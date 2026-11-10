'use strict';
// All imported media receipts are parsed in browser memory. No upload.
(function(){
const byId=id=>document.getElementById(id);
const kindLabels={black_segments:'BLACK',freeze_segments:'FREEZE',silence_segments:'SILENCE'};
const maxBytes=2*1024*1024;
const headings=['kind','start_seconds','end_seconds','duration_seconds','start_timestamp','end_timestamp','approx_frame_start','approx_frame_end','source_video','note'];
let model=null;
function finite(value,min=0){return typeof value==='number'&&Number.isFinite(value)&&value>=min;}
function timestamp(n){const ms=Math.round(n*1000);const h=Math.floor(ms/3600000),m=Math.floor(ms%3600000/60000),s=Math.floor(ms%60000/1000),rest=ms%1000;return [h,m,s].map(x=>String(x).padStart(2,'0')).join(':')+'.'+String(rest).padStart(3,'0')}
function csvCell(value){let s=value===null||value===undefined?'':String(value);if(/^\s*[=+\-@\t\r\n]/.test(s))s="'"+s;return /[,"\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function analyze(report){
 if(!report||typeof report!=='object'||Array.isArray(report)||report.schema_version!=='1.0')throw Error('Receipt harus JSON Release Lab versi skema 1.0.');
 const m=report.metadata, v=report.measurements, source=report.file;
 if(!m||!v||!source||typeof source.name!=='string'||source.name.length>300)throw Error('Struktur receipt tidak lengkap.');
 if(!finite(m.duration_seconds,.01)||!finite(m.fps,.01)||m.fps>240||m.duration_seconds>86400)throw Error('Durasi atau FPS receipt tidak valid.');
 if(!finite(v.analysis_seconds||0)||v.analysis_seconds>m.duration_seconds+1.5)throw Error('Cakupan scan receipt tidak valid.');
 const coverage=v.analysis_seconds||0, rows=[];
 for(const [field,label] of Object.entries(kindLabels)){
  const segments=v[field]||[];
  if(!Array.isArray(segments)||segments.length>1500)throw Error('Daftar segmen rusak atau terlalu besar.');
  for(const entry of segments){
    if(!entry||!finite(entry.start)||entry.start>m.duration_seconds+.2)throw Error('Waktu segmen tidak valid.');
    const end=entry.end===null||entry.end===undefined?(coverage>entry.start?Math.min(m.duration_seconds,coverage):null):entry.end;
    if(end!==null&&(!finite(end)||end<entry.start||end>m.duration_seconds+.2))throw Error('Waktu akhir tidak valid.');
    if(rows.length>=1500)throw Error('Jumlah segmen melebihi batas.');
    rows.push({kind:label.toLowerCase(),start_seconds:entry.start,end_seconds:end,duration_seconds:end===null?null:Math.round((end-entry.start)*1000000)/1000000,start_timestamp:timestamp(entry.start),end_timestamp:end===null?'':timestamp(end),approx_frame_start:Math.round(entry.start*m.fps),approx_frame_end:end===null?null:Math.round(end*m.fps),source_video:source.name,note:'Technical interval; editorial review required'+(entry.end===null||entry.end===undefined?'; end estimated from scan coverage':'')});
  }
 }
 rows.sort((a,b)=>a.start_seconds-b.start_seconds||a.kind.localeCompare(b.kind));
 const complete=coverage>0&&coverage+.15>=m.duration_seconds&&!v.limited_scan&&!(v.scan_errors||[]).length&&!(v.truncated_sections||[]).length;
 return {rows,complete,name:source.name,duration:m.duration_seconds,coverage,fps:m.fps,summary:report.summary||{},id:source.sha256||'',truncated:v.truncated_sections||[],errors:v.scan_errors||[]}
}
function clear(){byId('filename').textContent='Belum ada media';byId('read-state').textContent='NO RECEIPT';byId('duration').textContent='—';byId('fps').textContent='—';byId('count').textContent='—';byId('coverage').textContent='Belum dianalisis.';byId('quality-status').textContent='BELUM DIUJI';byId('quality-status').className='stamp';byId('download-csv').disabled=true;byId('timeline-scale').replaceChildren();byId('markers').replaceChildren();model=null}
function show(data){model=data;byId('read-state').textContent='LOCAL JSON LOADED';byId('filename').textContent=data.name;byId('duration').textContent=data.duration.toFixed(2)+'s';byId('fps').textContent=String(data.fps);byId('count').textContent=String(data.rows.length);byId('coverage').textContent=`${data.coverage.toFixed(2)}s diinspeksi dari ${data.duration.toFixed(2)}s. `+(data.complete?'Cakupan tersedia; hasil tetap perlu review.':'CAKUPAN TERBATAS: daftar kosong bukan bukti bebas masalah.');byId('quality-status').textContent=data.complete?'SCAN REPORTED':'INSUFFICIENT COVERAGE';byId('quality-status').className='stamp'+(data.complete?'':' warning');byId('download-csv').disabled=false;
 byId('limitation').textContent=data.rows.length?`${data.rows.length} segmen terdeteksi. Ini adalah interval teknis, bukan rekomendasi pemotongan otomatis.`:'Tidak ada segmen tercatat. '+(data.complete?'Tetap periksa kualitas secara manual.':'Scan tidak lengkap; jangan menganggap file lulus QC.');
 const tbody=byId('markers');tbody.replaceChildren();const scale=byId('timeline-scale');scale.replaceChildren();
 if(!data.rows.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='Tidak ada segmen dalam receipt.';tr.append(td);tbody.append(tr)}
 for(const e of data.rows){const tr=document.createElement('tr');for(const val of [e.kind.toUpperCase(),e.start_timestamp,e.end_timestamp||'UNKNOWN',e.approx_frame_start,e.note]){const td=document.createElement('td');td.textContent=String(val);tr.append(td)}tbody.append(tr);const bar=document.createElement('div');bar.className='event-segment '+e.kind;const start=100*e.start_seconds/data.duration;const width=100*Math.max(.02,(e.end_seconds??data.coverage)-e.start_seconds)/data.duration;bar.style.left=Math.min(100,start)+'%';bar.style.width=Math.min(100-start,width)+'%';bar.title=e.kind+' '+e.start_timestamp;scale.append(bar)}
}
async function readFile(file){if(!file)return;if(file.size>maxBytes||file.size<5){throw Error('Maksimum 2 MiB untuk receipt JSON.')}if(!file.name.toLowerCase().endsWith('.json'))throw Error('Pilih file .json, bukan video.');const raw=await file.text();return analyze(JSON.parse(raw))}
async function openLocal(file){clear();byId('open-status').textContent='Memeriksa receipt…';byId('open-status').classList.remove('error');try{const data=await readFile(file);show(data);byId('open-status').textContent='Berhasil dimuat: '+file.name}catch(e){byId('open-status').textContent=e instanceof Error?e.message:'JSON tidak terbaca';byId('open-status').classList.add('error')}}
byId('receipt-file').addEventListener('change',e=>openLocal(e.target.files?.[0]));const drop=byId('dropzone');for(const n of ['dragenter','dragover'])drop.addEventListener(n,e=>{e.preventDefault();drop.classList.add('dragging')});for(const n of ['dragleave','drop'])drop.addEventListener(n,e=>{e.preventDefault();drop.classList.remove('dragging')});drop.addEventListener('drop',e=>openLocal(e.dataTransfer.files?.[0]));drop.addEventListener('keydown',e=>{if(e.target===drop&&(e.key==='Enter'||e.key===' ')){e.preventDefault();byId('receipt-file').click()}});
byId('open-sample').addEventListener('click',async()=>{clear();byId('open-status').textContent='Membaca receipt contoh…';try{const response=await fetch('../demo/audit.json',{cache:'no-store'});if(!response.ok)throw Error('Contoh belum bisa diambil.');const body=await response.text();if(body.length>maxBytes)throw Error('Contoh terlalu besar.');show(analyze(JSON.parse(body)));byId('open-status').textContent='Contoh sintetis, bukan video pelanggan.'}catch(e){byId('open-status').textContent=e instanceof Error?e.message:'Contoh gagal dibuka';byId('open-status').classList.add('error')} });
byId('download-csv').addEventListener('click',()=>{if(!model)return;const lines=[headings.join(','),...model.rows.map(e=>headings.map(k=>csvCell(e[k])).join(','))].join('\r\n')+'\r\n';const blob=new Blob(['\uFEFF',lines],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='release-markers.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
})();
