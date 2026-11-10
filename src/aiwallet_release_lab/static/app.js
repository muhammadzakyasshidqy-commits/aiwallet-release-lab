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
 const timeline=$('marker-list');timeline.replaceChildren();
 const measure=result.measurements||{}, raw=[];
 for(const [key,label] of [['black_segments','BLACK'],['freeze_segments','FREEZE'],['silence_segments','SILENCE']]){
  const entries=measure[key];if(!Array.isArray(entries))continue;
  for(const x of entries){const start=Number(x.start);if(!Number.isFinite(start)||start<0)continue;raw.push({start,label,end:x.end})}
 }
 raw.sort((a,b)=>a.start-b.start||a.label.localeCompare(b.label));
 for(const x of raw.slice(0,300)){const end=x.end===null?'END UNKNOWN':Number.isFinite(Number(x.end))?Number(x.end).toFixed(2)+'s':'END UNKNOWN';timeline.append(node('li','',x.label+'  '+x.start.toFixed(2)+'s → '+end))}
 if(!raw.length)timeline.append(node('li','','Tidak ada segmen terdeteksi. Ini bukan bukti bebas masalah jika scan tidak lengkap.'));
 setText('marker-coverage',(measure.analysis_seconds||0)+'s dianalisis dari '+result.metadata.duration_seconds+'s. '+(measure.limited_scan?'SCAN TERBATAS':'Scan hasil detektor tersedia; interpretasi tetap diperlukan.'));
 $('download-markers').href='/api/reports/'+id+'/markers.csv';
 loadEditorialReview(id);
 $('download-html').href='/api/reports/'+id+'/html';$('result-panel').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});
}
async function history(){try{const res=await fetch('/api/reports',{cache:'no-store'});if(!res.ok)throw new Error('History unavailable');const data=await res.json();const items=data.reports||[];setText('history-count',items.length+' REPORTS');const box=$('history');box.replaceChildren();if(!items.length){box.append(node('p','empty-history','Belum ada laporan di perangkat ini.'));return}
 for(const it of items){const row=node('div','history-item');row.append(node('strong','',it.name));const level=node('span','status '+it.status,fmtLevel(it.status));row.append(level);const when=node('time','',formatDate(it.created_at));row.append(when);const actions=node('div');const view=node('button','','Lihat');view.type='button';view.addEventListener('click',async()=>{const r=await fetch('/api/reports/'+it.id);if(r.ok)showReport(it.id,await r.json(),'/api/reports/'+it.id+'/poster')});const del=node('button','delete','Hapus');del.type='button';del.addEventListener('click',async()=>{if(!confirm('Hapus laporan '+it.name+' dan cuplikan terkait dari komputer ini?'))return;const r=await fetch('/api/reports/'+it.id,{method:'DELETE'});if(r.ok){if(current?.id===it.id){$('empty-results').hidden=false;$('full-results').hidden=true;current=null}await history()}});actions.append(view,del);row.append(actions);box.append(row)}
 }catch(e){setText('history-count','OFFLINE');$('history').textContent='Riwayat belum dapat dibaca.'}}
form.addEventListener('submit',async e=>{e.preventDefault();if(!chosen){notify('Pilih berkas video terlebih dahulu.',true);return}if(!$('consent-local').checked){notify('Centang persetujuan pemeriksaan lokal.',true);return}run.disabled=true;notify('Membaca frame, metadata, dan audio…');const fd=new FormData();fd.append('file',chosen,chosen.name);try{const res=await fetch('/api/audits',{method:'POST',body:fd});let data={};try{data=await res.json()}catch{}if(!res.ok)throw new Error(data.detail||'Analisis gagal.');showReport(data.id,data.report,data.poster_url);notify('QC selesai. Laporan dapat diunduh.');chosen=null;input.value='';setText('file-label','Taruh video di sini');setText('file-details','Atau klik untuk memilih file dari perangkat');await history()}catch(err){notify(err.message||'Analisis gagal.',true)}finally{run.disabled=false}});
history();

// Human creative approval is NOT inferred from technical QC. All content stays local.
const editorialForm=$('editorial-form'), editorialState=$('editorial-state'), editorialDownload=$('download-editorial');
const reviewFields=['story_hook','visual_clarity','pacing','sound_design','brand_accuracy'];
async function loadEditorialReview(id){
  editorialState.textContent='Memuat review manusia…';editorialDownload.hidden=true;
  editorialForm.reset();
  try{
    const r=await fetch('/api/reports/'+id+'/review',{cache:'no-store'});
    if(!r.ok)throw new Error('Review lokal tidak dapat dibaca');
    const data=await r.json();
    if(current?.id!==id)return;
    const info=data.latest;
    if(!info){editorialState.textContent='Belum dinilai manusia. PASS teknis ≠ kualitas kreatif.';return;}
    const review=info.review;
    editorialForm.elements.namedItem('reviewer').value=review.reviewer;
    editorialForm.elements.namedItem('notes').value=review.notes||'';
    for(const key of reviewFields){const item=editorialForm.elements.namedItem(key);if(item)item.value=review.criteria[key]||''}
    editorialState.textContent=(review.outcome==='approved'?'Review manual: disetujui':'Review manual: minta revisi')+' · rev. '+info.revision+' · reviewer tidak diautentikasi.';
    editorialDownload.hidden=false;editorialDownload.href='/api/reports/'+id+'/review.json';
  }catch(e){if(current?.id===id)editorialState.textContent=e.message||'Review lokal tidak tersedia.'}
}
editorialForm.addEventListener('submit',async ev=>{
  ev.preventDefault();if(!current?.id||!editorialForm.reportValidity())return;
  const btn=$('editorial-save');btn.disabled=true;
  editorialState.textContent='Menyimpan review lokal…';
  try{
    const data=new FormData(editorialForm);
    const criteria={};for(const field of reviewFields)criteria[field]=String(data.get(field)||'');
    const payload={reviewer:String(data.get('reviewer')||''),notes:String(data.get('notes')||''),criteria};
    const id=current.id;
    const r=await fetch('/api/reports/'+id+'/review',{
      method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)
    });
    let result={};try{result=await r.json()}catch{}
    if(!r.ok)throw new Error(result.detail||'Review tidak bisa disimpan.');
    if(current?.id===id)await loadEditorialReview(id);
  }catch(err){editorialState.textContent=err.message||'Gagal menyimpan review.';}
  finally{btn.disabled=false;}
});
