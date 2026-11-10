'use strict';
const $=(id)=>document.getElementById(id);
const form=$('audit-form'), input=$('video-file'), drop=$('dropzone'), status=$('upload-status'), run=$('run-audit');
const maxBytes=256*1024*1024;
let chosen=null, current=null;
$('menu-button').addEventListener('click',()=>{const open=$('navigation').classList.toggle('open');$('menu-button').setAttribute('aria-expanded',String(open))});
document.querySelectorAll('#navigation a').forEach(a=>a.addEventListener('click',()=>{$('navigation').classList.remove('open');$('menu-button').setAttribute('aria-expanded','false')}));
function selected(file){if(!file)return;const ext=(file.name.split('.').pop()||'').toLowerCase();if(!['mp4','mov','m4v','webm','mkv'].includes(ext)){notify('Gunakan MP4, MOV, M4V, WebM, atau MKV.',true);chosen=null;return}if(file.size>maxBytes){notify('Berkas melebihi 256 MiB.',true);chosen=null;return}chosen=file;$('file-label').textContent=file.name;$('file-details').textContent=(file.size/1048576).toFixed(2)+' MiB · siap dianalisis';status.textContent='';status.classList.remove('error')}
function notify(message,error=false){status.textContent=message;status.classList.toggle('error',error)}
input.addEventListener('change',()=>selected(input.files?.[0]));
for(const name of ['dragenter','dragover'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.add('dragover')});
for(const name of ['dragleave','drop'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.remove('dragover')});
drop.addEventListener('drop',e=>selected(e.dataTransfer.files?.[0]));
drop.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target===drop){e.preventDefault();input.click()}});
function setText(id,text){$(id).textContent=text}
function node(tag,className,text){const item=document.createElement(tag);if(className)item.className=className;if(text!==undefined)item.textContent=text;return item}
function formatDate(s){try{return new Date(s).toLocaleString('id-ID',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}catch{return s}}
function fmtLevel(s){return s==='pass'?'PASS':s==='warn'?'CHECK':'BLOCK'}
function showReport(id,result,poster){current={id,result};$('empty-results').hidden=true;$('full-results').hidden=false;
 setText('result-badge',fmtLevel(result.summary.status));setText('result-filename',result.file.name);
 setText('result-meta',result.metadata.width+' × '+result.metadata.height+' · '+result.metadata.duration_seconds+' detik · '+(result.metadata.fps||'?')+' fps');
 setText('result-score',result.summary.passed+' LULUS / '+result.summary.warnings+' PERLU DICEK');
 const posterBox=$('result-poster');posterBox.replaceChildren();if(poster){const img=node('img');img.alt='Cuplikan pertama video terperiksa';img.src=poster;posterBox.appendChild(img)}else posterBox.textContent='NO PREVIEW';
 const checks=$('result-checks');checks.replaceChildren();for(const check of result.checks){const item=node('div','result-check '+check.level);item.append(node('span','',fmtLevel(check.level)));const content=node('div');content.append(node('h4','',check.title));content.append(node('p','',check.observation));content.append(node('p','',check.advice));item.append(content);checks.appendChild(item)}
 const jsonBlob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const link=$('download-json');if(link.dataset.objectUrl)URL.revokeObjectURL(link.dataset.objectUrl);link.href=URL.createObjectURL(jsonBlob);link.dataset.objectUrl=link.href;
 $('download-html').href='/api/reports/'+id+'/html';$('result-panel').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});
}
async function history(){try{const res=await fetch('/api/reports',{cache:'no-store'});if(!res.ok)throw new Error('History unavailable');const data=await res.json();const items=data.reports||[];setText('history-count',items.length+' REPORTS');const box=$('history');box.replaceChildren();if(!items.length){box.append(node('p','empty-history','Belum ada laporan di perangkat ini.'));return}
 for(const it of items){const row=node('div','history-item');row.append(node('strong','',it.name));const level=node('span','status '+it.status,fmtLevel(it.status));row.append(level);const when=node('time','',formatDate(it.created_at));row.append(when);const actions=node('div');const view=node('button','','Lihat');view.type='button';view.addEventListener('click',async()=>{const r=await fetch('/api/reports/'+it.id);if(r.ok)showReport(it.id,await r.json(),'/api/reports/'+it.id+'/poster')});const del=node('button','delete','Hapus');del.type='button';del.addEventListener('click',async()=>{if(!confirm('Hapus laporan '+it.name+' dan cuplikan terkait dari komputer ini?'))return;const r=await fetch('/api/reports/'+it.id,{method:'DELETE'});if(r.ok){if(current?.id===it.id){$('empty-results').hidden=false;$('full-results').hidden=true;current=null}await history()}});actions.append(view,del);row.append(actions);box.append(row)}
 }catch(e){setText('history-count','OFFLINE');$('history').textContent='Riwayat belum dapat dibaca.'}}
form.addEventListener('submit',async e=>{e.preventDefault();if(!chosen){notify('Pilih berkas video terlebih dahulu.',true);return}if(!$('consent-local').checked){notify('Centang persetujuan pemeriksaan lokal.',true);return}run.disabled=true;notify('Membaca frame, metadata, dan audio…');const fd=new FormData();fd.append('file',chosen,chosen.name);try{const res=await fetch('/api/audits',{method:'POST',body:fd});let data={};try{data=await res.json()}catch{}if(!res.ok)throw new Error(data.detail||'Analisis gagal.');showReport(data.id,data.report,data.poster_url);notify('QC selesai. Laporan dapat diunduh.');chosen=null;input.value='';setText('file-label','Taruh video di sini');setText('file-details','Atau klik untuk memilih file dari perangkat');await history()}catch(err){notify(err.message||'Analisis gagal.',true)}finally{run.disabled=false}});
history();

// Explicit opt-in only. Core audits never contact the hosted interest endpoint.
const waitDialog=$('waitlist-dialog'), waitForm=$('waitlist-form'), waitStatus=$('waitlist-status');
document.querySelectorAll('.waitlist-open').forEach(button=>button.addEventListener('click',()=>{
  $('waitlist-plan').value=button.dataset.plan;waitStatus.textContent='';waitDialog.showModal();
}));
$('close-waitlist').addEventListener('click',()=>waitDialog.close());
waitForm.addEventListener('submit',async event=>{
 event.preventDefault();if(!waitForm.reportValidity())return;
 const send=$('send-waitlist');send.disabled=true;waitStatus.textContent='Mencatat minat…';
 const data=Object.fromEntries(new FormData(waitForm).entries());
 try{const res=await fetch('https://jwdxpigxgasybqaovsma.supabase.co/functions/v1/aiwallet-release-interest',{
    method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({name:data.name,email:data.email,plan:data.plan,consent:!!data.consent,website:data.website})
  });let out={};try{out=await res.json()}catch{}
  if(!res.ok||!out.ok)throw new Error(out.message||'Layanan pencatatan minat belum tersedia.');
  waitStatus.textContent='Minatmu tercatat. Tidak ada penagihan atau langganan aktif.';waitForm.reset();
 }catch(err){waitStatus.textContent=err.message||'Pengiriman gagal. Hubungi kontak AIWallet.';}finally{send.disabled=false}
});
