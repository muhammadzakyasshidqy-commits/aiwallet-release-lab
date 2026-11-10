"""Single-user local dashboard. No third-party calls, no telemetry, no publishing."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, Request, Body
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .report import render_html
from .markers import extract_markers, markers_csv
from .editorial import create_review
from fastapi.staticfiles import StaticFiles

from . import __version__
from .core import ALLOWED_EXTENSIONS, AuditError, MAX_FILE_BYTES, audit_video, make_poster


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = root / "reports.sqlite3"
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS reports(
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, name TEXT NOT NULL,
                status TEXT NOT NULL, payload TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS editorial_reviews(
                report_id TEXT NOT NULL, revision INTEGER NOT NULL,
                created_at TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(report_id, revision),
                FOREIGN KEY(report_id) REFERENCES reports(id) ON DELETE CASCADE)""")

    def connect(self):
        db = sqlite3.connect(self.db, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def add(self, id_: str, report: dict[str, Any]):
        with self.connect() as db:
            db.execute("INSERT INTO reports(id,created_at,name,status,payload) VALUES(?,?,?,?,?)",
                       (id_, report["created_at"], report["file"]["name"],
                        report["summary"]["status"], json.dumps(report, ensure_ascii=False)))

    def get(self, id_: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM reports WHERE id=?", (id_,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list(self, limit=40) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT id,created_at,name,status,payload FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": row["id"], "created_at": row["created_at"], "name": row["name"],
                 "status": row["status"], "summary": json.loads(row["payload"])["summary"]} for row in rows]

    def latest_review(self, report_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT revision,payload FROM editorial_reviews WHERE report_id=? "
                             "ORDER BY revision DESC LIMIT 1", (report_id,)).fetchone()
        return {"revision": row["revision"], "review": json.loads(row["payload"])} if row else None

    def add_review(self, report_id: str, review: dict[str, Any]) -> int:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT COALESCE(MAX(revision),0)+1 FROM editorial_reviews WHERE report_id=?",
                             (report_id,)).fetchone()
            rev = int(row[0])
            db.execute("INSERT INTO editorial_reviews(report_id,revision,created_at,payload) VALUES(?,?,?,?)",
                       (report_id, rev, review["created_at"], json.dumps(review,ensure_ascii=False)))
        return rev

    def delete(self, id_: str) -> bool:
        with self.connect() as db:
            cursor = db.execute("DELETE FROM reports WHERE id=?", (id_,))
        (self.root / "posters" / f"{id_}.jpg").unlink(missing_ok=True)
        return cursor.rowcount > 0


def create_app(data_dir: Path | None = None, *, max_bytes: int = MAX_FILE_BYTES) -> FastAPI:
    root = data_dir or Path(os.getenv("AIWALLET_DATA_DIR", str(Path.home() / ".aiwallet-release-lab")))
    store = Store(Path(root))
    semaphore = asyncio.Semaphore(2)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    api = FastAPI(title="AIWallet Release Lab", version=__version__, lifespan=lifespan,
                  description="Local-first technical video QC API. Not a social network publishing API.")
    # Loopback bind alone does not prevent DNS rebinding through a hostile Host header.
    # Only names used by the local CLI are allowed (testserver is for TestClient).
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])

    static = Path(__file__).with_name("static")

    @api.middleware("http")
    async def security_headers(request: Request, call_next):
        if request.method in ("POST", "DELETE", "PUT", "PATCH"):
            origin = request.headers.get("origin")
            expected = str(request.base_url).rstrip("/")
            if origin and origin != expected:
                raise_origin = True
            else:
                raise_origin = request.headers.get("sec-fetch-site") == "cross-site"
            if raise_origin:
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Cross-origin writes are disabled"}, status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @api.get("/api/health")
    def health():
        return {"ok": True, "version": __version__, "local_first": True, "publishes_media": False}

    @api.get("/api/reports")
    def list_reports():
        return {"reports": store.list()}

    @api.get("/api/reports/{id_}")
    def get_report(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_):
            raise HTTPException(404, "Report not found")
        data = store.get(id_)
        if data is None:
            raise HTTPException(404, "Report not found")
        return data

    @api.get("/api/reports/{id_}/review")
    def get_editorial_review(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_) or store.get(id_) is None:
            raise HTTPException(404, "Report not found")
        return {"latest": store.latest_review(id_)}

    @api.get("/api/reports/{id_}/review.json")
    def export_editorial_review(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_) or store.get(id_) is None:
            raise HTTPException(404, "Report not found")
        latest = store.latest_review(id_)
        if latest is None:
            raise HTTPException(404, "Editorial review not found")
        return Response(json.dumps(latest["review"],indent=2,ensure_ascii=False)+"\n",
                        media_type="application/json; charset=utf-8",
                        headers={"Content-Disposition":"attachment; filename=editorial-review.json",
                                 "Cache-Control":"private, no-store"})

    @api.post("/api/reports/{id_}/review", status_code=201)
    def submit_editorial_review(id_: str, payload: dict[str, Any] = Body(...)):
        if not re.fullmatch(r"[0-9a-f]{32}", id_):
            raise HTTPException(404, "Report not found")
        report = store.get(id_)
        if report is None:
            raise HTTPException(404, "Report not found")
        try:
            review = create_review(report, reviewer=payload.get("reviewer"),
                                   criteria=payload.get("criteria"),notes=payload.get("notes", ""))
        except AuditError as exc:
            raise HTTPException(422, str(exc)) from exc
        revision = store.add_review(id_,review)
        return {"revision":revision,"review":review,
                "notice":"Unverified human self-attestation. Technical PASS alone is not creative approval."}

    @api.get("/api/reports/{id_}/poster")
    def get_poster(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_) or store.get(id_) is None:
            raise HTTPException(404, "Poster not found")
        p = store.root / "posters" / f"{id_}.jpg"
        if not p.is_file():
            raise HTTPException(404, "Poster not found")
        return FileResponse(p, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=60"})

    @api.get("/api/reports/{id_}/html")
    def download_html(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_):
            raise HTTPException(404, "Report not found")
        data = store.get(id_)
        if not data:
            raise HTTPException(404, "Report not found")
        poster = store.root / "posters" / f"{id_}.jpg"
        html = render_html(data, poster if poster.is_file() else None)
        return HTMLResponse(html, headers={"Content-Disposition": "attachment; filename=release-report.html",
                                           "Cache-Control": "private, no-store"})

    @api.get("/api/reports/{id_}/markers.csv")
    def download_markers(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_):
            raise HTTPException(404, "Report not found")
        report = store.get(id_)
        if report is None:
            raise HTTPException(404, "Report not found")
        result = extract_markers(report)
        return Response(markers_csv(result), media_type="text/csv; charset=utf-8", headers={
            "Content-Disposition": "attachment; filename=release-markers.csv",
            "Cache-Control": "private, no-store",
        })

    @api.delete("/api/reports/{id_}")
    def delete_report(id_: str):
        if not re.fullmatch(r"[0-9a-f]{32}", id_) or not store.delete(id_):
            raise HTTPException(404, "Report not found")
        return {"deleted": True}

    @api.post("/api/audits", status_code=201)
    async def upload_and_audit(file: UploadFile = File(...)):
        name = (file.filename or "video.mp4").replace("\\", "/").split("/")[-1][:130]
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(415, "Gunakan file MP4, MOV, M4V, WebM, atau MKV.")
        if file.content_type and file.content_type not in ("video/mp4", "video/quicktime", "video/webm", "video/x-matroska", "video/x-m4v", "application/octet-stream"):
            raise HTTPException(415, "MIME video tidak didukung.")
        if file.size is not None and file.size > max_bytes:
            raise HTTPException(413, "Video melebihi batas ukuran.")
        # The source video stays in a private tempfile; we delete it after QC.
        path = None
        id_ = uuid.uuid4().hex
        try:
            with tempfile.NamedTemporaryFile(prefix="aiwallet_qc_", suffix=ext, dir=store.root,
                                             delete=False) as tmp:
                path = Path(tmp.name)
                total = 0
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(413, "Batas ukuran unggahan terlampaui.")
                    tmp.write(chunk)
            async with semaphore:
                try:
                    result = await asyncio.to_thread(audit_video, path)
                except AuditError as exc:
                    raise HTTPException(422, str(exc)) from exc
                result["file"]["name"] = name
                poster = store.root / "posters" / f"{id_}.jpg"
                try:
                    await asyncio.to_thread(make_poster, path, poster, result["metadata"]["duration_seconds"])
                except AuditError:
                    pass
                store.add(id_, result)
            return {"id": id_, "report": result, "poster_url": f"/api/reports/{id_}/poster" if poster.is_file() else None}
        finally:
            await file.close()
            if path:
                path.unlink(missing_ok=True)

    @api.get("/", include_in_schema=False)
    def index():
        return FileResponse(static / "index.html", media_type="text/html", headers={"Cache-Control": "no-store"})

    api.mount("/static", StaticFiles(directory=static), name="static")
    return api


app = create_app()
