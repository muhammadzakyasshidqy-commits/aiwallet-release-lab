// AIWallet Creator Cloud early-access interest collection.
// This is NOT a subscription checkout. It must never grant paid entitlements.
const ORIGIN = "*"; // Explicit user-submitted, public prospect form only. No credentials/cookies.
const HEADERS = {
  "access-control-allow-origin": ORIGIN,
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "Content-Type",
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
  "cache-control": "no-store",
};
function reply(code: number, payload: Record<string,unknown>) {
  return new Response(JSON.stringify(payload), {status: code, headers:{...HEADERS,"content-type":"application/json; charset=utf-8"}});
}
const plans = new Set(["creator_cloud", "studio_workspace"]);
function clean(v: unknown, max: number): string {
  if (typeof v !== "string") return "";
  return v.trim().slice(0,max);
}
Deno.serve(async (request) => {
  if (request.method === "OPTIONS") return new Response(null,{status:204,headers:HEADERS});
  const url = new URL(request.url);
  if (request.method === "GET") return reply(200,{
    product:"AIWallet Release Lab",version:"0.1.0",status:"early_access_waitlist",
    recurring_charges_live:false,paid_features_live:false,
    prices_proposed_idr:{creator_cloud:149000,studio_workspace:499000},
    data_policy:"Email and selected tier are used only to contact you about the service. For deletion requests contact the project maintainer."
  });
  if (request.method !== "POST" || url.pathname.endsWith("/health")) return reply(405,{error:"method_not_allowed"});
  const length = Number(request.headers.get("content-length")||0);
  if (length > 2048) return reply(413,{error:"request_too_large"});
  try {
    const body = await request.text();
    if (body.length > 2048) return reply(413,{error:"request_too_large"});
    const obj = JSON.parse(body);
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return reply(400,{error:"invalid_payload"});
    if (clean(obj.website,250)) return reply(200,{ok:true}); // honeypot: do not save.
    const name = clean(obj.name,100);
    const email = clean(obj.email,254).toLowerCase();
    const plan = clean(obj.plan,30);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254 ||
        name.length < 2 || !plans.has(plan) || obj.consent !== true) {
      return reply(400,{error:"invalid_form",message:"Periksa email, nama, paket, dan persetujuan."});
    }
    const root = Deno.env.get("SUPABASE_URL");
    const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!root || !key) return reply(503,{error:"service_not_ready"});
    const endpoint = root.replace(/\/$/,"") + "/rest/v1/aiwallet_release_interest?on_conflict=email";
    const save = await fetch(endpoint, {
      method:"POST",
      headers:{Authorization:"Bearer "+key, apikey:key,"content-type":"application/json",
               Prefer:"resolution=merge-duplicates,return=minimal"},
      body:JSON.stringify({name,email,plan,consent:true,source:"release_lab_v0_1",updated_at:new Date().toISOString()})
    });
    if (!save.ok) return reply(503,{error:"save_unavailable"});
    return reply(201,{ok:true,message:"Minat akses awal tercatat. Ini bukan pembayaran atau aktivasi langganan."});
  } catch {
    return reply(400,{error:"invalid_json"});
  }
});
