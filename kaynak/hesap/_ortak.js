var HM=(function(){
 function sayi(v){if(v==null)return NaN;v=String(v).trim().replace(/\s/g,'');if(!v)return NaN;
  if(v.indexOf(',')>=0){v=v.replace(/\./g,'').replace(',','.')}else if(/^-?\d{1,3}(\.\d{3})+$/.test(v)){v=v.replace(/\./g,'')}return parseFloat(v)}
 function f(n,d){if(!isFinite(n))return '–';return n.toLocaleString('tr-TR',{minimumFractionDigits:d==null?2:d,maximumFractionDigits:d==null?2:d})}
 function bugun(){return new Date().toLocaleDateString('tr-TR',{day:'2-digit',month:'2-digit',year:'numeric'})}
 function pdf(baslik){var eski=document.title;document.title=baslik+' · '+bugun().replace(/\./g,'-');
  document.querySelectorAll('details.hm-acilir').forEach(function(d){d.open=true});
  document.querySelectorAll('.pdf-tarih').forEach(function(e){e.textContent=bugun()});
  window.print();setTimeout(function(){document.title=eski},500)}
 return {sayi:sayi,f:f,bugun:bugun,pdf:pdf};
})();
HM.kurlar=function(){if(!HM._k)HM._k=fetch('/kurlar.json',{cache:'no-store'}).then(function(r){return r.json()}).catch(function(){return {kurlar:{},satis:{}}});return HM._k};
HM.PB=[['USD','ABD doları'],['EUR','Euro'],['GBP','İngiliz sterlini'],['CNY','Çin yuanı'],['CHF','İsviçre frangı'],['JPY','Japon yeni'],['RUB','Rus rublesi'],['QAR','Katar riyali'],['AED','BAE dirhemi'],['SAR','Suudi riyali']];
HM.pbSecenek=function(sec){return HM.PB.map(function(p){return '<option value="'+p[0]+'"'+(p[0]===sec?' selected':'')+'>'+p[0]+' · '+p[1]+'</option>'}).join('')};
