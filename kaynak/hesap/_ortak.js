var HM=(function(){
 function sayi(v){if(v==null)return NaN;v=String(v).trim().replace(/\s/g,'');if(!v)return NaN;
  if(v.indexOf(',')>=0){v=v.replace(/\./g,'').replace(',','.')}return parseFloat(v)}
 function f(n,d){if(!isFinite(n))return '–';return n.toLocaleString('tr-TR',{minimumFractionDigits:d==null?2:d,maximumFractionDigits:d==null?2:d})}
 function bugun(){return new Date().toLocaleDateString('tr-TR',{day:'2-digit',month:'2-digit',year:'numeric'})}
 function pdf(baslik){var eski=document.title;document.title=baslik+' · '+bugun().replace(/\./g,'-');
  document.querySelectorAll('details.hm-acilir').forEach(function(d){d.open=true});
  document.querySelectorAll('.pdf-tarih').forEach(function(e){e.textContent=bugun()});
  window.print();setTimeout(function(){document.title=eski},500)}
 return {sayi:sayi,f:f,bugun:bugun,pdf:pdf};
})();
