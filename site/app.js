"use strict";
const menu=document.getElementById('menu-button');
const nav=document.getElementById('navigation');
menu?.addEventListener('click',()=>{const active=nav?.classList.toggle('open')||false;menu.setAttribute('aria-expanded',String(active));});
nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menu?.setAttribute('aria-expanded','false');}));
const managedForm=document.getElementById('managed-interest-form');
const managedPlan=document.getElementById('managed-plan');
const feedback=document.getElementById('managed-feedback');
const submit=document.getElementById('managed-submit');
document.querySelectorAll('[data-plan]').forEach(btn=>btn.addEventListener('click',()=>{
 managedPlan.value=btn.dataset.plan||'creator_cloud';
 managedForm.scrollIntoView({behavior:'smooth',block:'start'});managedPlan.focus();
}));
managedForm?.addEventListener('submit',async e=>{
 e.preventDefault();if(!managedForm.reportValidity())return;
 const fd=new FormData(managedForm);
 submit.disabled=true;feedback.textContent='Mencatat minat Anda…';
 try{
  const res=await fetch('https://jwdxpigxgasybqaovsma.supabase.co/functions/v1/aiwallet-release-interest',{
   method:'POST',headers:{'content-type':'application/json'},
   body:JSON.stringify({name:String(fd.get('name')||'').trim(),email:String(fd.get('email')||'').trim(),
    plan:String(fd.get('plan')||'creator_cloud'),consent:fd.has('consent'),website:String(fd.get('website')||'')})
  });
  const out=await res.json();if(!res.ok||!out.ok)throw Error(out.message||out.error||'Belum bisa mengirim');
  feedback.textContent='Minat tercatat. Tidak ada tagihan atau langganan yang diaktifkan.';
  feedback.dataset.result='success';managedForm.reset();
 }catch(err){feedback.textContent=(err.message||'Koneksi gagal')+'. Coba lagi atau hubungi email pada footer.';feedback.dataset.result='error';}
 finally{submit.disabled=false;}
});
