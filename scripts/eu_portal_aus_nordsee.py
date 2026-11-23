"""Baut aus dem Nordsee-Vermietungsportal das gemeinsame Vermietungsportal für alle Länder (myburano.com/vermieten)."""
import re,sys,json
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
def R(a,b,cnt=1):
    global s
    assert a in s,("FEHLT",a[:90]); s=s.replace(a,b) if cnt==0 else s.replace(a,b,cnt)

# --- Konfiguration
i=s.index('var PORTAL = {'); j=s.index('kontakt: {',i)
blk=s[i:j]
blk=blk.replace('name: "NordseeBnB"','name: "BnB Europa"').replace('vmName: "Nordsee Webdesign"','vmName: "BnB Webdesign"').replace('domain: "nordseebnb.de"','domain: "eu-bnb.com"')
blk=blk.replace('gastUrl: "https://nordseebnb.de/"','gastUrl: "https://eu-bnb.com/"').replace('vmUrl: "https://nordsee-webdesign.de/"','vmUrl: "https://eu-bnb.com/vermieten/"')
blk=blk.replace('vmHosts: /webdesign/i','vmHosts: /eu-bnb|webdesign|localhost|^$/i').replace('gastHosts: /nordseebnb/i','gastHosts: /^\\b$/').replace('region: "nordsee"','region: "europa"')
s=s[:i]+blk+s[j:]
R('kontakt: { name: "NordseeBnB",','kontakt: { name: "BnB Webdesign",')

# --- Länder statt Inseln
REG='var REGIONEN=[{k:"nord",n:"Skandinavien & Finnland"},{k:"sued",n:"Südeuropa"},{k:"west",n:"Westeuropa"},{k:"de",n:"Deutschland"}];'
L=[("Italien","https://it-bnb.com/","sued",42.8,12.0,"Ortstaxe (imposta di soggiorno) je nach Gemeinde, z. B. in Venedig, Florenz und Rom",["Venedig & Burano","Toskana","Amalfiküste"],["Venedig","Burano","Rom","Florenz","Gardasee","Cinque Terre","Amalfi"]),
 ("Frankreich","https://fr-bnb.com/","west",46.6,2.4,"Taxe de séjour je nach Gemeinde",["Paris","Provence","Bretagne"],["Paris","Nizza","Avignon","Bordeaux","Saint-Malo","Chamonix"]),
 ("Spanien","https://es-bnb.com/","sued",40.2,-3.7,"Tasa turística in einigen Regionen, z. B. Katalonien und Balearen",["Barcelona","Andalusien","Mallorca"],["Madrid","Barcelona","Valencia","Sevilla","Granada","Palma","Málaga"]),
 ("Dänemark","https://dk-bnb.dk/","nord",56.0,10.5,"in der Regel keine Ortstaxe",["Nordseeküste","Kopenhagen","Bornholm"],["Kopenhagen","Skagen","Aarhus","Ribe","Rømø","Bornholm"]),
 ("Schweden","https://se-bnb.com/","nord",61.5,16.0,"in der Regel keine Ortstaxe",["Schären","Seen","Lappland"],["Stockholm","Göteborg","Malmö","Visby","Smögen","Abisko"]),
 ("Norwegen","https://no-bnb.com/","nord",64.5,13.0,"in einigen Orten eine Touristenabgabe",["Fjorde","Lofoten","Nordlicht"],["Oslo","Bergen","Flåm","Geiranger","Tromsø","Lofoten"]),
 ("Finnland","https://fi-bnb.com/","nord",64.0,26.0,"in der Regel keine Ortstaxe",["Seenplatte","Lappland","Helsinki"],["Helsinki","Turku","Tampere","Savonlinna","Rovaniemi","Levi"]),
 ("Deutschland","https://debnb.de/","de",51.2,10.4,"Kurabgabe bzw. Gästetaxe nach Satzung der Gemeinde",["Nord- & Ostsee","Städte","Alpen"],["Hamburg","München","Sylt","Rügen","Usedom"])]
orte=",\n".join("{n:%s,seite:%s,kur:%s,reg:%s,km:%s,lat:%s,lng:%s,tags:%s,t:%s,orte:%s}"%(json.dumps(n,ensure_ascii=False),json.dumps(u),json.dumps(k,ensure_ascii=False),json.dumps(r),json.dumps("Länderportal "+u.split('//')[1].strip('/'),ensure_ascii=False),la,lo,json.dumps(tg,ensure_ascii=False),json.dumps("Ferienunterkünfte in "+n+" – direkt bei privaten Gastgebern, ohne Provision.",ensure_ascii=False),json.dumps(o,ensure_ascii=False)) for n,u,r,la,lo,k,tg,o in L)
i=s.index('var REGIONEN='); j=s.index('];',s.index('var ORTE=',i))+2
s=s[:i]+REG+"\nvar ORTE=[\n"+orte+"\n];"+s[j:]

# --- Pakete
R('name:"Inselseite + Portal", provision:"0 %", grundgebuehr:"19 €", einheit:"pro Monat"','name:"Länderseite + Portal", provision:"0 %", grundgebuehr:"19 €", einheit:"pro Monat"')
R('"Ihre Unterseite auf syltbnb.de, amrumbnb.de, foehrbnb.de oder wangeroogebnb.de – alle anderen Orte unter nordseebnb.de"','"Ihre Unterseite auf dem Länderportal – z. B. it-bnb.com, fr-bnb.com, es-bnb.com, dk-bnb.dk, se-bnb.com, no-bnb.com, fi-bnb.com"')
s=s.replace("Alles aus Inselseite + Portal","Alles aus Länderseite + Portal")
s=s.replace("Kurkarten & Kurabgabe für Ihre Gäste – automatisch, wo Ihr Ort es zulässt","Kurtaxe bzw. Ortstaxe für Ihre Gäste – automatisch, wo Ihr Ort es zulässt")

# --- Länder-Abschnitt statt Inselseite
i=s.index('<section class="lsec" id="lInsel">'); j=s.index('</section>',i)+10
isles="".join('<a class="isle" href="%s" target="_blank" rel="noopener"><b>%s</b><span>%s/ihr-name</span></a>'%(u,n,u.split('//')[1].strip('/')) for n,u,*_ in L)
s=s[:i]+'''<section class="lsec" id="lInsel">
      <div class="wrap">
        <div class="eyebrow">Ihre Länderseite</div>
        <h2>Ihre Unterkunft als eigene Unterseite – auf dem Portal Ihres Landes</h2>
        <p class="lead">Gäste suchen nach dem Land, nicht nach dem Anbieter. Deshalb bekommen Sie Ihre Unterseite direkt auf dem passenden Länderportal – in der Landessprache, auf Englisch und Deutsch.</p>
        <div class="isles">'''+isles+'''</div>
        <div class="islprice"><div><b>0 %</b><small>Provision auf Ihre Buchungen</small></div><div><b>14 Tage</b><small>gratis testen</small></div><div><b>3</b><small>Sprachen je Seite</small></div></div>
        <div style="text-align:center;margin-top:18px"><button class="btn" onclick="pickPaket('website')">Jetzt Länderseite anlegen</button></div>
      </div>
    </section>'''+s[j:]

# --- Titel und Marke
R('<title>NordseeBnB – Ferienwohnungen auf den Nordseeinseln, direkt vom Vermieter</title>','<title>BnB Webdesign – Websites & Buchungsportal für Vermieter in Europa</title>')
s=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="Eigene Website, Portal-Eintrag und Buchungsservice für Ferienvermieter in Italien, Frankreich, Spanien, Skandinavien und Deutschland – ohne Provision.">',s,count=1)
R('document.title="Nordsee Webdesign – Websites & Buchungsportal für Vermieter an der Nordsee";$("brandLink").innerHTML="Nordsee <span>Webdesign</span><small>Websites &amp; Buchungsportal für Vermieter</small>";',
  'document.title="BnB Webdesign – Websites & Buchungsportal für Vermieter in Europa";$("brandLink").innerHTML="BnB <span>Webdesign</span><small>Websites &amp; Buchungsportal für Vermieter in Europa</small>";')

# --- allgemeine Textanpassungen (Reihenfolge wichtig)
for a,b in [("auf den Nordseeinseln","in ganz Europa"),("Alle Nordseeinseln","Alle Länder"),("allen Nordseeinseln","allen Ländern"),("den Nordseeinseln","ganz Europa"),("Nordseeinseln","Urlaubsländer"),
 ("einer Nordseeinsel","einem unserer Länder"),("Vermietern an der Nordsee","Vermietern in Europa"),("Vermieter an der Nordsee","Vermieter in Europa"),("an der Nordsee","in Europa"),("Nordseeurlaub","Europaurlaub"),
 ("Nordsee Webdesign","BnB Webdesign"),("nordsee-webdesign.de","eu-bnb.com/vermieten"),("NordseeBnB","BnB Europa"),("ihr-name.nordseebnb.de","ihr-name.eu-bnb.com"),("nordseebnb.de/ihr-name","eu-bnb.com/ihr-name"),("nordseebnb.de","eu-bnb.com"),
 ("Kennt die Nordsee","Kennt Ihre Region"),("Nordsee-Karte","Europa-Karte"),
 ("Inselseiten","Länderseiten"),("Inselseite","Länderseite"),("auf Ihrer Insel bzw. in Ihrem Ort","in Ihrem Ort"),("auf Ihrer Insel","in Ihrer Region"),("Ihre Insel","Ihre Region"),("der Insel","der Region"),("Alle Inseln","Alle Länder"),("Welche Inseln sind dabei?","Welche Länder sind dabei?"),
 ("für alle Inseln","für alle Regionen"),("Auf den Inseln arbeiten wir","In den Regionen arbeiten wir"),("nach der Satzung Ihrer Insel","nach den Regeln Ihres Ortes"),
 ("z. B. Ferienwohnung in Wyk auf Föhr, bisher nur bei einem Portal","z. B. Ferienwohnung in Florenz, bisher nur bei einem Portal"),
 ("ob auf Sylt, Föhr oder Norderney","ob in Italien, Schweden oder Spanien"),("Moin und herzlich willkommen","Herzlich willkommen"),("Moin","Guten Tag"),
 ("Was kostet meine Länderseite?","Was kostet meine Länderseite?")]:
    s=s.replace(a,b)
s=s.replace("Ihre Website als Unterseite einer Länderseite kostet 99 € im ersten Jahr, danach 20 € pro Jahr – und 0 % Provision auf Ihre Buchungen.","Ihre Website als Unterseite einer Länderseite kostet eine feste Gebühr pro Jahr (Preis auf Anfrage) – und 0 % Provision auf Ihre Buchungen.")
s=re.sub(r'\["Wo liegt meine Unterseite\?","[^"]*"\]','["Wo liegt meine Unterseite?","Auf dem Portal Ihres Landes, zum Beispiel it-bnb.com/ihr-name, fr-bnb.com/ihr-name oder se-bnb.com/ihr-name. Gäste sehen sie in der Landessprache, auf Englisch und Deutsch."]',s)
s=re.sub(r'\["Welche Länder sind dabei\?","[^"]*"\]','["Welche Länder sind dabei?","Italien, Frankreich, Spanien, Dänemark, Schweden, Norwegen, Finnland und Deutschland – jeweils mit eigenem Länderportal. Weitere Länder folgen."]',s)


# --- Nachbesserungen sichtbarer Vermieter-Texte, KI-Anweisungen und Wissen des Assistenten
LAND_LINKS=" · ".join('<a href="%s">%s</a>'%(u,n) for n,u,*_ in L)
s=re.sub(r'🏝️ Länderseiten: .*?(?= · 🌊)', '🌍 Länderportale: '+LAND_LINKS.replace('\\','\\\\'), s, count=1)
s=re.sub(r'Vermieter auf Sylt, Amrum, Föhr oder Wangerooge bekommen ihre Unterseite auf [^;]*; alle anderen Orte unter eu-bnb\.com\.', 'Vermieter bekommen ihre Unterseite auf dem Länderportal ihres Landes: it-bnb.com, fr-bnb.com, es-bnb.com, dk-bnb.dk, se-bnb.com, no-bnb.com, fi-bnb.com bzw. debnb.de.', s)
s=re.sub(r'INSELN: BnB Europa deckt .*?eigene Seiten:[^.]*\.', 'LÄNDER: BnB Europa umfasst Italien, Frankreich, Spanien, Dänemark, Schweden, Norwegen, Finnland und Deutschland, jeweils mit eigenem Länderportal (Gästeseite in Landessprache, Englisch und Deutsch).', s, count=1, flags=re.S)
s=re.sub(r'Orte liegen in Europa, meist auf einer Insel \(z\. B\. [^)]*\) – trage Ort und Insel ein, z\. B\. \\"Wyk auf Föhr\\"\.', 'Orte liegen irgendwo in Europa – trage Ort und Land ein, z. B. \\"Burano, Italien\\" oder \\"Visby, Schweden\\".', s)
for a,b in [('(u.ort?", ":"")+"Nordsee")','(u.ort?", ":"")+"Europa")'),('(u.ort||"Nordsee")','(u.ort||"Europa")'),('ort:u.ort||"Nordsee"','ort:u.ort||"Europa"'),('esc(D.region||"Nordsee")','esc(D.region||"Europa")'),
            ("An der Nordsee bauen wir ihn","In anderen Regionen bauen wir ihn"),
            ("kennt die Insel (Strand, Fähre, Anreise, Ausflüge)","kennt die Region (Strand, Anreise, Ausflüge)"),
            ("<span>🏝️</span><b>Ihre Länderseite</b><small>Unterseite auf syltbnb.de, amrumbnb.de, foehrbnb.de, wangeroogebnb.de oder eu-bnb.com</small>","<span>🌍</span><b>Ihre Länderseite</b><small>Unterseite auf it-bnb.com, fr-bnb.com, es-bnb.com, dk-bnb.dk, se-bnb.com, no-bnb.com oder fi-bnb.com</small>"),
            ("sowie SyltBnB, AmrumBnB, FöhrBnB und WangeroogeBnB sind Angebote","sowie die Länderportale it-bnb.com, fr-bnb.com, es-bnb.com, dk-bnb.dk, se-bnb.com, no-bnb.com und fi-bnb.com sind Angebote"),
            ("<small>Deutsch, Englisch, Dänisch, Niederländisch, Französisch</small>","<small>Landessprache, Englisch, Deutsch – auf Wunsch weitere</small>")]:
    s=s.replace(a,b)

# --- Mehrsprachigkeit (Übersetzung der Oberfläche, Ergebnis wird im Browser gespeichert)
I18N=r"""<script>
function bwI18n(o){
var ALL={it:"Italiano",en:"English",de:"Deutsch",fr:"Français",es:"Español",nl:"Nederlands",da:"Dansk",sv:"Svenska",nb:"Norsk",fi:"Suomi"};
var NAMEN={it:"Italian",en:"English",fr:"French",es:"Spanish",nl:"Dutch",da:"Danish",sv:"Swedish",nb:"Norwegian (Bokmål)",fi:"Finnish",de:"German"};
var LANGS={};(o.langs||Object.keys(ALL)).forEach(function(k){if(ALL[k])LANGS[k]=ALL[k]});
var q=new URLSearchParams(location.search),L=q.get("lang"),KP=o.key||"bw";
try{if(!L)L=localStorage.getItem(KP+"_lang")}catch(e){}
if(!L)L=(navigator.language||"en").slice(0,2).replace("no","nb");
if(!LANGS[L])L=LANGS[o.def]?o.def:Object.keys(LANGS)[0];
try{localStorage.setItem(KP+"_lang",L)}catch(e){}
window.BW_LANG=L;window.BW_SPRACHE=NAMEN[L]||"German";
var C={},OUT={},PEND={},busy=false,timer=null,dot=null;
window.BW_T=function(t){var k=String(t||"").trim();return C[k]||t};
window.BW_PENDING=function(){return Object.keys(PEND).length+(busy?1:0)};
function sel(){if(document.getElementById("bwLang")||Object.keys(LANGS).length<2)return;var n=o.mount&&document.querySelector(o.mount);
  var s=document.createElement("select");s.id="bwLang";s.setAttribute("data-noi18n","1");s.setAttribute("aria-label","Language");
  if(n){s.className="icbtn";s.style.cssText="width:64px;padding:0 4px;font-weight:600"}else s.style.cssText="position:fixed;top:10px;right:10px;z-index:3000;padding:6px;border-radius:10px;border:1px solid #ccc;background:#fff;font:600 13px sans-serif";
  Object.keys(LANGS).forEach(function(k){var op=document.createElement("option");op.value=k;op.textContent=(k==="nb"?"NO":k.toUpperCase())+" · "+LANGS[k];if(k===L)op.selected=true;s.appendChild(op)});
  s.onchange=function(){try{localStorage.setItem(KP+"_lang",s.value)}catch(e){}var u=new URL(location.href);u.searchParams.set("lang",s.value);location.href=u.toString()};
  if(n)n.insertBefore(s,n.firstChild);else document.body.appendChild(s)}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",sel);else sel();setTimeout(sel,1500);
if(L==="de")return;
document.documentElement.lang=L;
var KEY=KP+"_i18n_"+L;try{C=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
Object.keys(C).forEach(function(k){OUT[C[k]]=1});
var SKIP={SCRIPT:1,STYLE:1,TEXTAREA:1,CODE:1,NOSCRIPT:1,IFRAME:1,SVG:1};
function brauchts(t){t=t.trim();return t.length>1&&/[A-Za-zÄÖÜäöüß]{2}/.test(t)&&!/^(https?:|www\.|[\w.+-]+@)/.test(t)&&!OUT[t]}
function skipEl(e){for(;e&&e!==document.body;e=e.parentNode){if(e.nodeType===1&&(SKIP[e.tagName]||e.hasAttribute("data-noi18n")||e.isContentEditable||e.classList.contains("preview")||e.classList.contains("bub")))return true}return false}
function anwenden(){
  var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null),n,neu=0;
  while(n=w.nextNode()){var t=n.nodeValue,k=t.trim();if(!brauchts(k)||skipEl(n.parentNode))continue;
    if(C[k]){n.nodeValue=t.replace(k,C[k])}else{PEND[k]=1;neu++}}
  document.body.querySelectorAll("[placeholder],[title],[aria-label]").forEach(function(e){if(skipEl(e))return;
    ["placeholder","title","aria-label"].forEach(function(a){var v=e.getAttribute(a);if(!v)return;var k=v.trim();if(!brauchts(k))return;if(C[k])e.setAttribute(a,C[k]);else{PEND[k]=1;neu++}})});
  if(neu)planen()}
function planen(){clearTimeout(timer);timer=setTimeout(senden,400)}
function zeigen(an){if(!dot){dot=document.createElement("div");dot.setAttribute("data-noi18n","1");dot.style.cssText="position:fixed;left:12px;bottom:12px;z-index:3000;background:#1d4f73;color:#fff;border-radius:99px;padding:6px 12px;font:600 12px sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.25)";dot.textContent="⏳ "+LANGS[L]+" …";document.body.appendChild(dot)}dot.style.display=an?"block":"none"}
function senden(){if(busy)return;var keys=Object.keys(PEND).filter(function(k){return!C[k]});if(!keys.length){PEND={};zeigen(false);return}
  var batch=[],len=0;for(var i=0;i<keys.length&&batch.length<80&&len<7000;i++){batch.push(keys[i]);len+=keys[i].length}
  busy=true;zeigen(true);
  var prompt="Translate these German user-interface texts of a holiday-rental website into "+NAMEN[L]+". Polite, natural, short. Keep emojis, numbers, prices, %, € amounts, punctuation style, and brand/product names (BnB Webdesign, BnB Europa, EU-BnB, WhatsApp, Booking.com, Airbnb, iCal, Dünenvilla, Strandvilla, Thiessow, Rügen) unchanged. Return ONLY a JSON array of strings, same order and same length.\n\n"+JSON.stringify(batch);
  fetch(o.api,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:"claude-haiku-5-5",max_tokens:8000,messages:[{role:"user",content:prompt}]})})
  .then(function(r){return r.json()}).then(function(j){var txt=(j.content||[]).map(function(c){return c.text||""}).join("");var a=JSON.parse(txt.slice(txt.indexOf("["),txt.lastIndexOf("]")+1));
    batch.forEach(function(k,i){if(typeof a[i]==="string"&&a[i].trim()){C[k]=a[i].trim();OUT[C[k]]=1}delete PEND[k]});
    try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){}})
  .catch(function(){batch.forEach(function(k){delete PEND[k]})})
  .then(function(){busy=false;anwenden();if(Object.keys(PEND).length)planen();else zeigen(false)})}
function start(){fetch(o.dict+L+".json").then(function(r){return r.ok?r.json():{}}).catch(function(){return{}}).then(function(j){Object.keys(j||{}).forEach(function(k){if(!C[k]){C[k]=j[k];OUT[j[k]]=1}});
  anwenden();new MutationObserver(function(ms){var z=false;ms.forEach(function(m){if(m.addedNodes.length||m.type==="characterData")z=true});if(z){clearTimeout(window.__bwT);window.__bwT=setTimeout(anwenden,150)}}).observe(document.body,{childList:true,subtree:true,characterData:true})})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",function(){setTimeout(start,600)});else setTimeout(start,600);
}
bwI18n({mount:".navicons",dict:"https://eu-bnb.com/vermieten/i18n/",api:PORTAL.claude,key:"bw"});
</script>
</body>"""
s=s.replace('</style>','@media (max-width:480px){#navGast{display:none}.navicons .lbl{display:none}.brand small{display:none}.brand{min-width:0}}\n</style>',1)
k=s.rindex('</body>'); s=s[:k]+'<div hidden id="bwExtra"><p>Herzlich willkommen bei BnB Europa! Ich helfe Ihnen gern bei der Wahl der Region und der passenden Unterkunft. Wonach suchen Sie?</p><p>Herzlich willkommen bei BnB Webdesign! Schön, dass Sie da sind. Ich beantworte gern Ihre Fragen rund um Ihre eigene Website und unser neues Buchungsportal. Was möchten Sie wissen?</p></div>\n'+I18N+s[k+7:]
R('form:false,lang:"de",','form:false,lang:(window.BW_LANG||"de"),')
R('kb:gast?kbGast():kbVermieter(),','kb:(gast?kbGast():kbVermieter())+((window.BW_LANG&&window.BW_LANG!=="de")?"\\nSPRACHE: Sprich mit dem Nutzer auf "+window.BW_SPRACHE+" (Sprachcode "+window.BW_LANG+"). Wechsle sofort in eine andere Sprache, wenn der Nutzer sie spricht.":""),')
R('greeting:gast?"','greeting:(window.BW_T||function(x){return x})(gast?"')
s=s.replace('Was möchten Sie wissen?"})})})','Was möchten Sie wissen?")})})})',1)
# Websites der Vermieter: Landessprache + Englisch + Deutsch, gleiche Übersetzungsdatei
R('function buildSite(D){','''function buildSite(D){var h=buildSite0(D),L0=window.BW_LANG||"de",langs=[L0,"en","de"].filter(function(x,i,a){return a.indexOf(x)===i});
  var js="<script>("+bwI18n.toString()+")({langs:"+JSON.stringify(langs)+",def:"+JSON.stringify(L0)+",dict:\\"https://eu-bnb.com/vermieten/i18n/\\",api:"+JSON.stringify(PORTAL.claude)+",key:\\"site\\"})<\\/script>";
  var k=h.lastIndexOf("</body>");return k>=0?h.slice(0,k)+js+h.slice(k):h+js}
function buildSite0(D){''')
open(dst,'w',encoding='utf-8').write(s)
rest=re.sub(r'data:[^"\')]{200,}','',s)
print("fertig", len(s), "| Rest Nordsee:", len(re.findall(r'Nordsee',rest)), "| Insel:", len(re.findall(r'Insel',rest)))
