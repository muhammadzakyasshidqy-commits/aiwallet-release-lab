'use strict';
const $=id=>document.getElementById(id);
$('menu-button').addEventListener('click',()=>{const open=$('navigation').classList.toggle('open');$('menu-button').setAttribute('aria-expanded',String(open))});
document.querySelectorAll('#navigation a').forEach(a=>a.addEventListener('click',()=>{$('navigation').classList.remove('open');$('menu-button').setAttribute('aria-expanded','false')}));
const d=$('waitlist-dialog'),f=$('waitlist-form'),message=$('waitlist-status');
document.querySelectorAll('.waitlist-open').forEach(b=>b.addEventListener('click',()=>{$('waitlist-plan').value=b.dataset.plan;message.textContent='';d.showModal()}));
$('close-waitlist').addEventListener('click',()=>d.close());
f.addEventListener('submit',async ev=>{ev.preventDefault();if(!f.reportValidity())return;const btn=$('send-waitlist');btn.disabled=true;message.textContent='Mencatat minat…';const data=Object.fromEntries(new FormData(f).entries());try{const r=await fetch('https://jwdxpigxgasybqaovsma.supabase.co/functions/v1/aiwallet-release-interest',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name:data.name,email:data.email,plan:data.plan,consent:!!data.consent,website:data.website})});const body=await r.json();if(!r.ok||!body.ok)throw Error(body.message||'Pencatatan belum berhasil');message.textContent='Minat tercatat. Belum ada tagihan atau langganan aktif.';f.reset()}catch(e){message.textContent=e.message||'Gagal mengirim; coba lagi atau hubungi email kontak.'}finally{btn.disabled=false}});
