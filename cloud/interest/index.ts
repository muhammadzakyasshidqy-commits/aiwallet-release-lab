// Optional customer managed-hosting interest. Free Apache-2.0 self-hosted core is unaffected.
// NOT a payment/checkout endpoint. A registration does not authorize a charge.
const headers={
 "access-control-allow-origin":"*",
 "access-control-allow-methods":"GET,POST,OPTIONS",
 "access-control-allow-headers":"Content-Type",
 "content-type":"application/json; charset=utf-8",
 "cache-control":"no-store",
 "x-content-type-options":"nosniff",
 "referrer-policy":"no-referrer"
};
const respond=(status:number,data:Record<string,unknown>)=>new Response(JSON.stringify(data),{status,headers});
const plans=new Set(["creator_cloud","studio_workspace"]);
function clean(x:unknown,max:number){return typeof x==="string"?x.trim().slice(0,max):"";}
Deno.serve(async(req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers});
 if(req.method==="GET")return respond(200,{
  product:"AIWallet Release Lab",version:"0.9-beta",
  model:"Free Apache-2.0 self-hosted core + future optional managed subscriptions for customers",
  owner_paid_subscription_required:false,
  pricing_idr_per_month:{creator_cloud:149000,studio_workspace:499000},
  billing_live:false,managed_cloud_available:false,interest_registration_live:true,
  message:"Managed plans are proposals only. No purchase, trial, recurring charge or entitlement is created."
 });
 if(req.method!=="POST")return respond(405,{error:"method_not_allowed"});
 if(!(req.headers.get("content-type")||"").toLowerCase().includes("application/json"))return respond(415,{error:"json_required"});
 if(Number(req.headers.get("content-length")||0)>2048)return respond(413,{error:"request_too_large"});
 try{
  const raw=await req.text();if(raw.length>2048)return respond(413,{error:"request_too_large"});
  const v=JSON.parse(raw);
  if(!v||typeof v!=="object"||Array.isArray(v))return respond(400,{error:"invalid_payload"});
  if(clean(v.website,250))return respond(202,{ok:true,message:"Permintaan diterima."});
  const email=clean(v.email,254).toLowerCase(),name=clean(v.name,100),plan=clean(v.plan,35);
  if(name.length<2||name.length>100||email.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||!plans.has(plan)||v.consent!==true)
   return respond(400,{error:"invalid_form",message:"Periksa nama, email, paket, dan persetujuan."});
  const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!key)return respond(503,{error:"service_not_ready"});
  const target=url.replace(/\/$/,"")+"/rest/v1/aiwallet_release_interest?on_conflict=email";
  const saved=await fetch(target,{method:"POST",headers:{Authorization:"Bearer "+key,apikey:key,"Content-Type":"application/json",Prefer:"resolution=ignore-duplicates,return=minimal"},
   body:JSON.stringify({email,name,plan,consent:true,source:"release_lab_v09_managed_interest"})});
  if(!saved.ok)return respond(503,{error:"save_unavailable"});
  return respond(202,{ok:true,charged:false,managed_service_active:false,message:"Minat tercatat. Belum ada tagihan atau langganan aktif."});
 }catch{return respond(400,{error:"invalid_json"});}
});
