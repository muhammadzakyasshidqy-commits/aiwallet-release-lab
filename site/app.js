'use strict';
const menu=document.getElementById('menu-button');
const nav=document.getElementById('navigation');
menu?.addEventListener('click',()=>{const active=nav?.classList.toggle('open')||false;menu.setAttribute('aria-expanded',String(active));});
nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menu?.setAttribute('aria-expanded','false');}));
