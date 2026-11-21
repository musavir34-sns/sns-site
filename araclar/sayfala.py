"""kaynak/tek-sayfa.html dosyasından her bölüm için ayrı adresli sayfalar üretir.

Çalıştırma (depo kök klasöründe):  python3 araclar/sayfala.py
Üretilenler: index.html, <bolum>/index.html, sitemap.xml, robots.txt
Siteyi düzenlerken yalnızca kaynak/tek-sayfa.html değiştirilir, sonra bu betik çalıştırılır.
"""
import html, json, os, re

ALAN = "https://snsdanismanlik.com.tr"
KAYNAK = "kaynak/tek-sayfa.html"

SAYFALAR = {  # bölüm kimliği: (adres, başlık, açıklama)
    "ana": ("/", "SNS Danışmanlık · Serdar Saraç, SMMM · Serbest Muhasebeci Mali Müşavirlik Bürosu",
            "Serdar Saraç, Serbest Muhasebeci Mali Müşavir (İSMMMO sicil no 60446). Kağıthane / İstanbul. Muhasebe, vergi, bordro ve mali danışmanlık hizmetleri."),
    "hizmet-sayfa": ("/hizmetler/", "Hizmetler · SNS Danışmanlık",
            "Muhasebe ve defter tutma, vergi beyannameleri, bordro ve SGK, şirket işlemleri, vergi incelemesi ve uzlaşma, dış ticaret, finansal raporlama ve denetim."),
    "diger-sektorler": ("/diger-sektorler/", "Diğer faaliyet alanları · SNS Danışmanlık",
            "İnşaat ve taahhüt, e-ticaret, etkinlik ve organizasyon, yazılım, ses-ışık-LED ve holding yapılarında muhasebe ve vergi."),
    "sektorler": ("/medya-film-dizi/", "Medya, film ve dizi sektörü · SNS Danışmanlık",
            "Yapım şirketleri, stüdyolar ve sinema salonları için maliyet, proje bütçesi, Madde 18 istisnası ve vergi konuları."),
    "yat-tekne": ("/yat-tekne/", "Yat ve tekne işletmeleri · SNS Danışmanlık",
            "Tekne satın alma süreci, charter işletmesi, fizibilite çalışması ve vergi planlaması."),
    "uluslararasi": ("/uluslararasi-ticaret/", "Uluslararası ticaret ve yabancı sermayeli şirketler · SNS Danışmanlık",
            "İthalat-ihracat ve navlun planlaması, kârlılık analizi, yabancı sermayeli şirketlerin kuruluşu, muhasebesi ve ortaklara raporlama."),
    "gundem": ("/gundem/", "Gündem: TÜRMOB ve İSMMMO güncel mevzuat · SNS Danışmanlık",
            "TÜRMOB mevzuat sirkülerleri, İSMMMO duyuruları ve büro yazıları tek listede, günde üç kez güncellenir."),
    "yazilar-sayfa": ("/yazilar/", "Yazılar · SNS Danışmanlık",
            "Vergi, SGK, medya sektörü ve dış ticaret üzerine analizler: Madde 18 istisnası, prim günü, e-ticaret gümrük kuralları ve daha fazlası."),
    "pratik-sayfa": ("/pratik-bilgiler/", "Hesaplama araçları ve 2026 oranları · SNS Danışmanlık",
            "KDV, net-brüt maaş, kıdem ve ihbar tazminatı, gelir vergisi, gecikme zammı ve damga vergisi hesaplama; 2026 oranları, vergi takvimi ve dilekçe örnekleri."),
    "hakkimizda-sayfa": ("/hakkimizda/", "Serdar Saraç, SMMM · Hakkımızda · SNS Danışmanlık",
            "Serdar Saraç'ın özgeçmişi, görev aldığı kurumlar, eğitim ve deneyim alanları. İstanbul SMMM Odası sicil no 60446."),
    "iletisim-sayfa": ("/iletisim/", "İletişim · SNS Danışmanlık",
            "Adres, telefon, e-posta ve WhatsApp bilgileri. Hamidiye Mah., Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2, 34408 Kağıthane / İstanbul."),
    "yasal-sayfa": ("/kvkk-ve-cerezler/", "KVKK Aydınlatma Metni ve Çerez Politikası · SNS Danışmanlık",
            "Kişisel verilerin işlenmesine ilişkin aydınlatma metni ve çerez politikası."),
}

s = open(KAYNAK, encoding="utf-8").read()


def div_sonu(bas):
    d = 0
    for m in re.finditer(r"<(/?)div\b", s[bas:]):
        d += -1 if m.group(1) else 1
        if d == 0:
            return s.find(">", bas + m.end()) + 1
    raise ValueError("div kapanmadı")


baslar = [m.start() for m in re.finditer(r'<div class="sayfa"', s)]
bolumler = {}
for b in baslar:
    pid = re.search(r'id="([^"]+)"', s[b:b + 120]).group(1)
    bolumler[pid] = (b, div_sonu(b))
assert set(bolumler) == set(SAYFALAR), set(bolumler) ^ set(SAYFALAR)

ilk = min(v[0] for v in bolumler.values()); son = max(v[1] for v in bolumler.values())
govde_on = s[s.find("<body>") + len("<body>"):ilk]          # yazı tipi bağlantıları + stil
_k = govde_on.find("<style>")
FONT_BAS = govde_on[:_k].strip() + "\n"                       # yazı tipi bağlantıları <head> içine taşınır
govde_on = govde_on[_k:]
arka = s[son:s.rfind("</body>")]                            # ortak betikler
betikler = re.findall(r"<script>(.*?)</script>", arka, re.S)
assert len(betikler) == 5, len(betikler)
hesap_js, yonlendirme_js, canli_js, menu_js, gundem_js = betikler

# hangi kimlik hangi sayfada
kimlik_sayfa = {}
for pid, (a, b) in bolumler.items():
    for m in re.finditer(r'\sid="([^"]+)"', s[a:b]):
        kimlik_sayfa.setdefault(m.group(1), pid)


def adres(hedef):
    """'#x' biçimindeki eski bağlantının yeni adresi."""
    if hedef in SAYFALAR:
        return SAYFALAR[hedef][0]
    pid = kimlik_sayfa.get(hedef)
    if pid is None:
        return None
    return SAYFALAR[pid][0] + "#" + hedef


def baglanti_cevir(html, bu_sayfa):
    def f(m):
        hedef = m.group(1)
        yeni = adres(hedef)
        if yeni is None:
            return m.group(0)
        if bu_sayfa is not None and yeni.startswith(SAYFALAR[bu_sayfa][0] + "#") and kimlik_sayfa.get(hedef) == bu_sayfa:
            yeni = "#" + hedef  # aynı sayfadaki bölüme kaydırma
        return 'href="%s"' % yeni
    return re.sub(r'href="#([A-Za-z0-9_-]+)"', f, html)


# menü betiğindeki '#...' adreslerini çevir
menu_js = re.sub(r"'#([A-Za-z0-9_-]+)'", lambda m: "'%s'" % (adres(m.group(1)) or "#" + m.group(1)), menu_js)

# gündem betiği: yazı listesini sabit veriye çevir
a, b = bolumler["yazilar-sayfa"]
ol = re.search(r"<ol\b.*?</ol>", s[a:b], re.S).group(0)
yazilar = []
for href, ic in re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', ol, re.S):
    sp = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<span[^>]*>(.*?)</span>", ic, re.S)]
    yazilar.append({"tur": "yazi", "konu": sp[0] if sp else "", "baslik": sp[1] if len(sp) > 1 else "",
                    "url": adres(href[1:]) if href.startswith("#") else href})
eski = re.search(r"var ol=document\.querySelector\('#yazilar-sayfa ol'\);\n if\(ol\).*?\n", gundem_js).group(0)
gundem_js = gundem_js.replace(eski, "yazilar=" + json.dumps(yazilar, ensure_ascii=False) + ";\n")
gundem_js = gundem_js.replace("fetch('duyurular.json'", "fetch('/duyurular.json'")
canli_js = canli_js.replace("fetch('kurlar.json'", "fetch('/kurlar.json'")

# sayfa değiştirme yerine yalnız menü düğmesi
yeni_yonlendirme = yonlendirme_js[:yonlendirme_js.find("  function show(){")] + "})();\n"
yeni_yonlendirme = re.sub(r"  var pages=\[[^\]]*\];\n", "", yeni_yonlendirme)
assert "function show" not in yeni_yonlendirme and "insertBefore(b,nav)" in yeni_yonlendirme

# eski #bölüm bağlantılarıyla gelenleri yeni adrese gönder (yalnız ana sayfada)
eski_harita = {pid: v[0] for pid, v in SAYFALAR.items() if pid != "ana"}
for k, pid in kimlik_sayfa.items():
    if pid != "ana" and k not in eski_harita:
        eski_harita[k] = SAYFALAR[pid][0] + "#" + k
ESKI_YAZI = {"madde-18": "madde-18-mi-sirket-mi-2026", "prim-gunu": "emeklilik-prim-gunu-mu-kazanc-mi",
             "sinema-salon": "sinema-salon-isletmeciligi", "e-ticaret-gumruk": "e-ticaret-yeni-gumruk-kurallari",
             "kamera-arkasi": "kamera-arkasindaki-gizli-kahraman", "kooperatif-denetim": "kooperatif-dis-denetci-zorunlulugu",
             "dizi-ihracat": "turk-dizi-sektorunun-finansal-analizi"}
for k, v in ESKI_YAZI.items():
    eski_harita[k] = "/yazilar/%s/" % v
yazi_yonlendir_js = "(function(){var m=%s;var h=location.hash.slice(1);if(h&&m[h])location.replace('/yazilar/'+m[h]+'/');})();" % json.dumps(ESKI_YAZI, separators=(",", ":"))
eski_js = "(function(){var m=%s;var h=location.hash.slice(1);if(h&&m[h])location.replace(m[h]);})();" % json.dumps(eski_harita, ensure_ascii=False, separators=(",", ":"))

ikonlar = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">\n'
           '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n<meta name="theme-color" content="#2B2F33">\n')


def esc(t):
    return t.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def bas_yap(yol, baslik, aciklama, ek="", gorsel_ozel=None, tur="website"):
    if gorsel_ozel:
        gorsel, galt = gorsel_ozel
    elif yol.startswith("/hesaplama-merkezi/"):
        gorsel, galt = "/og-hesaplama.png", "SNS İş Dünyası Hesaplama Merkezi"
    else:
        gorsel, galt = "/og-sns.png", "SNS Danışmanlık · Serdar Saraç, SMMM"
    ek = ('<meta property="og:site_name" content="SNS Danışmanlık">\n<meta property="og:image" content="%s%s">\n'
          '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
          '<meta property="og:image:alt" content="%s">\n<meta name="twitter:card" content="summary_large_image">\n' % (ALAN, gorsel, esc(galt))) + ek
    ek = FONT_BAS + ek
    return ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s<link rel="canonical" href="%s%s">\n'
            '<meta property="og:type" content="%s">\n<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s%s">\n<meta property="og:locale" content="tr_TR">\n%s</head>\n<body>\n'
            % (esc(baslik), esc(aciklama), ikonlar, ALAN, yol, tur, esc(baslik), esc(aciklama), ALAN, yol, ek))


# Yapılandırılmış veri (schema.org): arama motorları ve yapay zekâ aramaları büroyu doğru tanısın.
# Bilgiler vergi levhası, faaliyet belgesi ve Google İşletme Profili ile aynı tutulmalı.
ISLETME_LD = {
    "@context": "https://schema.org", "@type": "AccountingService", "@id": ALAN + "/#buro",
    "name": "Serdar Saraç Serbest Muhasebeci Mali Müşavir Bürosu", "alternateName": "SNS Danışmanlık",
    "url": ALAN + "/", "logo": ALAN + "/og-sns.png", "image": ALAN + "/og-sns.png",
    "email": "info@snsdanismanlik.com.tr", "telephone": "+90 532 624 99 33",
    "address": {"@type": "PostalAddress", "streetAddress": "Hamidiye Mah. Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2",
                "addressLocality": "Kağıthane", "addressRegion": "İstanbul", "postalCode": "34408", "addressCountry": "TR"},
    "geo": {"@type": "GeoCoordinates", "latitude": 41.092933, "longitude": 28.975068},
    "areaServed": ["TR", "LY", "QA", "IQ", "EG", "IR"], "knowsLanguage": ["tr", "en"],
    "sameAs": ["https://share.google/wuSox0PQlExN3fpbv"],  # Google İşletme Profili
    "knowsAbout": ["Muhasebe ve defter tutma", "Vergi danışmanlığı", "Dış ticaret ve ihracat vergilendirmesi", "Akreditif ve ihracat bedelinin tahsili",
                   "KDV iadesi", "Libya, Katar, Irak, Mısır ve İran ile ticaret", "Yabancı sermayeli şirketler", "Şirket işlemleri ve genel kurul (TTK)"],
    # Büro sahibinin kimliği ve uzmanlık alanları (yapay zekâ aramalarının kişiyi uzmanlıkla eşleştirmesi için)
    "founder": {"@type": "Person", "@id": ALAN + "/#serdar-sarac", "name": "Serdar Saraç", "jobTitle": "Serbest Muhasebeci Mali Müşavir",
                "url": ALAN + "/hakkimizda/", "sameAs": ["https://www.linkedin.com/in/serdar-sara%C3%A7-3660466a/"],
                "alumniOf": {"@type": "CollegeOrUniversity", "name": "Anadolu Üniversitesi"},
                "memberOf": {"@type": "Organization", "name": "İstanbul Serbest Muhasebeci Mali Müşavirler Odası", "alternateName": "İSMMMO"},
                "hasCredential": [
                    {"@type": "EducationalOccupationalCredential", "credentialCategory": "Meslek ruhsatı", "name": "Serbest Muhasebeci Mali Müşavir",
                     "recognizedBy": {"@type": "Organization", "name": "TÜRMOB"}},
                    {"@type": "EducationalOccupationalCredential", "credentialCategory": "Sertifika", "name": "Kooperatif Dış Denetçisi",
                     "recognizedBy": {"@type": "Organization", "name": "TÜRMOB"}}],
                "knowsLanguage": ["tr", "en"],
                "knowsAbout": ["Dış ticaret", "İhracat ve ithalat vergilendirmesi", "Akreditif", "Libya'ya ihracat", "Yabancı sermayeli şirketler",
                               "Türk Ticaret Kanunu şirket işlemleri", "Kooperatif dış denetimi", "Medya ve film sektöründe finansal yönetim",
                               "Finansal raporlama ve bütçe", "Enflasyon muhasebesi"]},
}
ISLETME_LD_HTML = '<script type="application/ld+json">%s</script>\n' % json.dumps(ISLETME_LD, ensure_ascii=False)

uretilen = []
for pid, (yol, baslik, aciklama) in SAYFALAR.items():
    a, b = bolumler[pid]
    govde = s[a:b]
    govde = re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="%s">' % pid, govde, count=1)
    govde = baglanti_cevir(govde, pid)
    govde = govde.replace('href="#ana"', 'href="/"')
    bas = bas_yap(yol, baslik, aciklama, ("<script>%s</script>\n" % eski_js) if pid == "ana" else ("<script>%s</script>\n" % yazi_yonlendir_js) if pid == "yazilar-sayfa" else "")
    if pid in ("ana", "iletisim-sayfa", "hakkimizda-sayfa"):
        bas = bas.replace("</head>", ISLETME_LD_HTML + "</head>", 1)
    if pid == "ana":  # Bing Webmaster Tools site doğrulaması (kaldırılmamalı)
        bas = bas.replace("</head>", '<meta name="msvalidate.01" content="5EC5BDE2B80F13EED4DE461AB37B3F4F">\n</head>', 1)
    js = [yeni_yonlendirme, canli_js, menu_js, gundem_js]
    if pid == "pratik-sayfa":
        js.insert(0, hesap_js)
    sayfa = bas + govde_on + govde + "\n" + "".join("<script>%s</script>\n" % x for x in js) + "</body>\n</html>\n"
    hedef = "index.html" if yol == "/" else yol.strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef) or ".", exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, yol, len(sayfa)))

# --- Hesaplama Merkezi sayfaları (kaynak/hesap/*.html) ---
import glob
a, b = bolumler["hizmet-sayfa"]
iskelet = baglanti_cevir(s[a:b], None).replace('href="#ana"', 'href="/"')
iskelet = iskelet.replace(" border-bottom: 1px solid #1FA86D; padding-bottom: 3px", "")
ust = iskelet[:iskelet.find("</header>") + len("</header>")]
k = iskelet.find("Büro sahibi"); alt = iskelet[iskelet.rfind("<section", 0, k):]
ortak_css = open("kaynak/hesap/_ortak.css", encoding="utf-8").read()
ortak_js = open("kaynak/hesap/_ortak.js", encoding="utf-8").read()
ek_adresler = []
PDF_BASLIK = ('<div class="pdf-baslik"><svg aria-hidden="true" height="34" viewBox="8 10 80 76" width="36"><rect fill="#1FA86D" height="10" width="80" x="8" y="10"></rect>'
              '<rect fill="#1FA86D" height="38" width="10" x="8" y="10"></rect><rect fill="#2B2F33" height="10" width="80" x="8" y="43"></rect>'
              '<rect fill="#1FA86D" height="38" width="10" x="78" y="48"></rect><rect fill="#1FA86D" height="10" width="80" x="8" y="76"></rect></svg>'
              '<div><b>SNS Danışmanlık</b> · Serdar Saraç, SMMM<br>snsdanismanlik.com.tr · Hesaplama tarihi: <span class="pdf-tarih"></span></div></div>')
PDF_ALT = ('<div class="pdf-alt">Bu belge snsdanismanlik.com.tr Hesaplama Merkezi ile oluşturulmuştur. Tahmini hesaptır; resmî kayıt ve beyanlarda ilgili belgeler esastır. '
           'SNS Danışmanlık · Serdar Saraç, Serbest Muhasebeci Mali Müşavir · İSMMMO sicil no 60446</div>')
for dosya in sorted(glob.glob("kaynak/hesap/*.html")):
    metin = open(dosya, encoding="utf-8").read()
    m = re.match(r"<!--META (\{.*?\}) -->\n", metin, re.S)
    meta = json.loads(m.group(1)); icerik = metin[m.end():]
    icerik = icerik.replace("<!--PDFBASLIK-->", PDF_BASLIK).replace("<!--PDFALT-->", PDF_ALT)
    pid = "hesap-" + os.path.basename(dosya)[:-5]
    govde = re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="%s">' % pid, ust, count=1) + "\n<script>%s</script>\n" % ortak_js + icerik + "\n" + alt
    sayfa = (bas_yap(meta["yol"], meta["baslik"], meta["aciklama"]) + govde_on + "<style>%s</style>\n" % ortak_css + govde + "\n"
             + "".join("<script>%s</script>\n" % x for x in [yeni_yonlendirme, canli_js, menu_js]) + "</body>\n</html>\n")
    hedef = meta["yol"].strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, meta["yol"], len(sayfa))); ek_adresler.append(meta["yol"])

# --- Yazı sayfaları (kaynak/yazilar/*.html) ---
YAZI_SIRASI = re.findall(r'href="/yazilar/([a-z0-9-]+)/"', re.search(r"<ol\b.*?</ol>", s[bolumler["yazilar-sayfa"][0]:bolumler["yazilar-sayfa"][1]], re.S).group(0))
a, b = bolumler["yazilar-sayfa"]
yz_iskelet = baglanti_cevir(s[a:b], None).replace('href="#ana"', 'href="/"')
yz_ust = yz_iskelet[:yz_iskelet.find("</header>") + len("</header>")]
k = yz_iskelet.find("Büro sahibi"); yz_alt = yz_iskelet[yz_iskelet.rfind("<section", 0, k):]
YZ_CSS = (".yz-tablo{overflow-x:auto;margin:10px 0 18px}.yz table{width:100%;min-width:480px;border-collapse:collapse;font-size:15px;line-height:1.55}.yz th,.yz td{border-top:1px solid #E1E4DE;padding:10px 12px;text-align:left;vertical-align:top}.yz thead th{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#5F656B;font-weight:600}.yz tbody th{font-weight:600}.yz h3.yz-alt{margin:22px 0 8px;font:500 19px/1.35 Fraunces,serif}"
          ".yz{max-width:760px;margin:0 auto;padding:64px 24px 0;color:#2B2F33;font-family:Manrope,sans-serif}"
          ".yz-yol{margin:0 0 22px;font-size:13px;color:#666C72}.yz-yol a{color:#666C72}"
          ".yz-ust{margin:0;font-size:13px;letter-spacing:.26em;text-transform:uppercase;border-left:3px solid #1FA86D;padding-left:10px}"
          ".yz h1{margin:14px 0 14px;font:300 clamp(32px,4.4vw,48px)/1.15 Fraunces,serif}"
          ".yz-meta{margin:0 0 34px;padding-bottom:18px;border-bottom:1px solid #E1E4DE;font-size:14px;color:#666C72}"
          ".yz p{margin:0 0 18px;font-size:17.5px;line-height:1.8;color:#2F3437}"
          ".yz h3,.yz h2.yz-ara{margin:34px 0 12px;font:500 24px/1.3 Fraunces,serif}"
          ".yz ul{margin:0 0 18px;padding-left:22px}.yz li{font-size:17px;line-height:1.7;color:#2F3437;margin:0 0 6px}"
          ".yz blockquote{margin:28px 0;padding:4px 0 4px 22px;border-left:2px solid #1FA86D;font:400 20px/1.6 Fraunces,serif}"
          ".yz-dayanak{margin:34px 0 0;padding:16px 18px;background:#FFF;border:1px solid #E1E4DE;border-radius:10px;font-size:14px;line-height:1.6;color:#4A5056}"
          ".yz-not{margin:14px 0 0;font-size:14px;line-height:1.7;color:#5F656B}"
          ".yz-diger{margin:44px 0 0;border-top:1px solid #2B2F33;padding-top:18px}.yz-diger h2{margin:0 0 6px;font:400 22px/1.3 Fraunces,serif}"
          ".yz-diger a{display:block;padding:12px 0;border-bottom:1px solid #E1E4DE;color:#2B2F33;text-decoration:none;font:400 18px/1.4 Fraunces,serif}.yz-diger a:hover{color:#157A4F}"
          ".yz-diger small{display:block;font:600 11.5px/1.3 Manrope,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#666C72;margin-bottom:3px}"
          ".yz-kisaca{margin:0 0 34px;padding:18px 22px 12px;background:#FFF;border:1px solid #E1E4DE;border-left:4px solid #1FA86D;border-radius:10px}"
          ".yz-kisaca h2{margin:0 0 10px;font:600 12px/1.3 Manrope,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#157A4F}"
          ".yz-kisaca ul{margin:0;padding-left:20px}.yz .yz-kisaca li{font-size:16px;line-height:1.65;margin:0 0 8px}"
          ".yz ol{margin:0 0 18px;padding-left:24px}.yz ol li{font-size:17px;line-height:1.7;color:#2F3437;margin:0 0 10px}"
          ".yz .yz-uyari{padding:16px 20px;background:#FFF;border:1px solid #E1E4DE;border-left:4px solid #2B2F33;border-radius:10px;font-size:15.5px;line-height:1.7}"
          ".yz .yz-gonder{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;margin:26px 0 8px}.yz-gonder span{flex:1 1 280px;font-size:14px;line-height:1.6;color:#5F656B}"
          ".yz-dugme{display:inline-block;background:#3DDC97;color:#14281E;text-decoration:none;font:600 15px/1 Manrope,sans-serif;padding:16px 26px;border-radius:999px}.yz-dugme:hover{background:#1FA86D;color:#FFF}"
          ".yz-sorular{list-style:none;margin:0 0 18px;padding:0;border-top:1px solid #E1E4DE}.yz .yz-sorular li{margin:0;border-bottom:1px solid #E1E4DE}"
          ".yz-sorular a{display:block;padding:14px 0 2px;color:#2B2F33;text-decoration:none;font:400 19px/1.4 Fraunces,serif}.yz-sorular a:hover{color:#157A4F}.yz-sorular small{display:block;padding-bottom:14px;font-size:13px;color:#666C72}"
          ".yz .yz-bos{color:#5F656B;font-style:italic}"
          "@media(max-width:700px){.yz{padding:40px 16px 0}.yz p{font-size:16.5px}}")
def kisaca_yap(meta):
    if not meta.get("kisaca"):
        return ""
    return ('<section class="yz-kisaca" aria-labelledby="yz-kisaca-b"><h2 id="yz-kisaca-b">Kısaca</h2><ul>'
            + "".join("<li>%s</li>" % esc(x).replace("&quot;", '"') for x in meta["kisaca"]) + "</ul></section>\n")
yz_meta = {}
for dosya in glob.glob("kaynak/yazilar/*.html"):
    metin = open(dosya, encoding="utf-8").read()
    m = re.match(r"<!--META (\{.*?\}) -->\n", metin, re.S)
    yz_meta[json.loads(m.group(1))["slug"]] = (json.loads(m.group(1)), metin[m.end():])
assert set(YAZI_SIRASI) == set(yz_meta), set(YAZI_SIRASI) ^ set(yz_meta)
for i, slug in enumerate(YAZI_SIRASI):
    meta, icerik = yz_meta[slug]
    kaynak = re.search(r"<!--KAYNAK (.*?) -->", icerik, re.S)
    icerik = re.sub(r"<!--KAYNAK .*? -->", "", icerik, flags=re.S).strip()
    if "<ins>" in icerik or "<del>" in icerik:
        raise SystemExit("İşaretli taslak yayımlanamaz: " + slug)
    yol = "/yazilar/%s/" % slug
    tarih_iso = "-".join(reversed(meta["guncelleme"].split(".")))
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": meta["baslik"], "description": meta["ozet"],
          "dateModified": tarih_iso, "inLanguage": "tr", "mainEntityOfPage": ALAN + yol, "image": ALAN + "/og/yazilar/%s.png" % slug,
          "author": {"@type": "Person", "name": "Serdar Saraç", "jobTitle": "Serbest Muhasebeci Mali Müşavir"},
          "publisher": {"@type": "Organization", "name": "SNS Danışmanlık", "url": ALAN}}
    diger = [YAZI_SIRASI[(i + j) % len(YAZI_SIRASI)] for j in (1, 2, 3)]
    govde = (re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="yazi-%s">' % slug, yz_ust, count=1)
             + '\n<article class="yz"><p class="yz-yol"><a href="/yazilar/">Yazılar</a> › %s</p><p class="yz-ust">%s</p><h1>%s</h1>'
               '<p class="yz-meta">Serdar Saraç, Serbest Muhasebeci Mali Müşavir · Son güncelleme: %s</p>\n%s%s\n'
             % (meta["kategori"], meta["kategori"].split(" · ")[0], meta["baslik"], meta["guncelleme"], kisaca_yap(meta), icerik)
             + ('<p class="yz-dayanak"><b>Dayanak:</b> %s</p>' % kaynak.group(1).strip() if kaynak else "")
             + '<p class="yz-not">Bu yazı genel bilgilendirme amaçlıdır; mevzuat değişebileceğinden somut durumlar için güncel mevzuat ayrıca değerlendirilmelidir.</p>'
             + '<nav class="yz-diger" aria-label="Diğer yazılar"><h2>Diğer yazılar</h2>'
             + "".join('<a href="/yazilar/%s/"><small>%s</small>%s</a>' % (d, yz_meta[d][0]["kategori"].split(" · ")[0], yz_meta[d][0]["baslik"]) for d in diger)
             + '<a href="/yazilar/" style="font:600 13px/1 Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#157A4F;border:0">Tüm yazılar →</a></nav></article>\n' + yz_alt)
    gorsel = ("/og/yazilar/%s.png" % slug, meta["baslik"]) if os.path.exists("og/yazilar/%s.png" % slug) else None
    sayfa = (bas_yap(yol, meta["baslik"] + " · SNS Danışmanlık", meta["ozet"],
                     '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False), gorsel, "article")
             + govde_on + "<style>%s</style>\n" % YZ_CSS + govde + "\n"
             + "".join("<script>%s</script>\n" % x for x in [yeni_yonlendirme, canli_js, menu_js]) + "</body>\n</html>\n")
    hedef = yol.strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, yol, len(sayfa))); ek_adresler.append(yol)

# --- Özel sayfalar (kaynak/sayfalar/*.html): yazı iskeletiyle, "Diğer yazılar" olmadan ---
for dosya in sorted(glob.glob("kaynak/sayfalar/*.html")):
    metin = open(dosya, encoding="utf-8").read()
    m = re.match(r"<!--META (\{.*?\}) -->\n", metin, re.S)
    meta = json.loads(m.group(1)); icerik = metin[m.end():]
    if "<!--SORULAR-->" in icerik:
        sorular = [d for d in YAZI_SIRASI if yz_meta[d][0]["kategori"].startswith("Okuyucu sorusu")]
        liste = ('<ul class="yz-sorular">' + "".join('<li><a href="/yazilar/%s/">%s</a><small>%s · %s</small></li>' % (d, yz_meta[d][0]["baslik"], yz_meta[d][0]["kategori"].split(" · ")[-1], yz_meta[d][0]["guncelleme"]) for d in sorular) + '</ul>'
                 if sorular else '<p class="yz-bos">Henüz yayımlanmış yanıt yok. Gelen sorular arasından seçilenler yanıtlandıkça bu listede yer alacak.</p>')
        icerik = icerik.replace("<!--SORULAR-->", liste)
        # Sayfanın "Son güncelleme" tarihi, en son yayımlanan yanıtın tarihinden eski kalmasın
        gun = lambda t: tuple(reversed([int(x) for x in t.split(".")]))
        meta["guncelleme"] = max([meta["guncelleme"]] + [yz_meta[d][0]["guncelleme"] for d in sorular], key=gun)
    kaynak = re.search(r"<!--KAYNAK (.*?) -->", icerik, re.S)
    icerik = re.sub(r"<!--KAYNAK .*? -->", "", icerik, flags=re.S).strip()
    govde = (re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="ozel-%s">' % os.path.basename(dosya)[:-5], yz_ust, count=1)
             + '\n<article class="yz"><p class="yz-ust">%s</p><h1>%s</h1><p class="yz-meta">Son güncelleme: %s</p>\n%s\n' % (meta["kategori"], meta["baslik"], meta["guncelleme"], icerik)
             + ('<p class="yz-dayanak"><b>Dayanak:</b> %s</p>' % kaynak.group(1).strip() if kaynak else "") + '</article>\n' + yz_alt)
    sayfa = (bas_yap(meta["yol"], meta["baslik"] + " · SNS Danışmanlık", meta["aciklama"]) + govde_on + "<style>%s</style>\n" % YZ_CSS + govde + "\n"
             + "".join("<script>%s</script>\n" % x for x in [yeni_yonlendirme, canli_js, menu_js]) + "</body>\n</html>\n")
    hedef = meta["yol"].strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, meta["yol"], len(sayfa))); ek_adresler.append(meta["yol"])

# --- Yabancı dil sayfaları (kaynak/en/*.html, kaynak/ar/*.html) ---
# Her kaynak dosya: <!--META {"yol": "/en/...", "tr": "/turkce-karsiligi/", "baslik": ..., "aciklama": ..., "tur": "sayfa"|"yazi"} --> + gövde
DILLER = {
    "en": {"ad": "English", "kisa": "EN", "dir": "ltr", "locale": "en_US",
           "unvan": "Certified Public Accountant",
           "menu": [("Services", "/en/services/"), ("International", "/en/international/"), ("About", "/en/about/")],
           "iletisim": ("Contact", "/en/contact/"), "menu_ad": "Main menu", "atla": "Skip to content",
           "yaz_meta": "Serdar Saraç, Certified Public Accountant · Last updated: %s", "kisaca": "In brief",
           "dayanak": "Legal basis", "yazi_not": "This article is for general information only. Legislation may change; specific cases should be assessed under the legislation in force at the time.",
           "alt": [("Office holder", "Serdar Saraç<br/>Certified Public Accountant (<span lang=\"tr\">Serbest Muhasebeci Mali Müşavir</span>)"),
                   ("Registered office", "<span lang=\"tr\">Serdar Saraç Serbest Muhasebeci Mali Müşavir Bürosu</span><br/>Office reg. no 27853 · Trade name used: <span lang=\"tr\">SNS Danışmanlık</span>"),
                   ("Professional chamber", "Istanbul Chamber of Certified Public Accountants (<span lang=\"tr\">İSMMMO</span>)<br/>Reg. no 60446 · Licence no 342135321<br/>Registered: 05.03.2024"),
                   ("Languages", "Turkish · English"),
                   ("Address", "<span lang=\"tr\">Hamidiye Mah., Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2, 34408 Kağıthane / İstanbul</span>, Türkiye"),
                   ("Contact", "+90 532 624 99 33 (also WhatsApp)<br/>info@snsdanismanlik.com.tr")],
           "alt_link": [("Privacy &amp; cookies", "/en/privacy/"), ("Accessibility (in Turkish)", "/erisilebilirlik/"),
                        ("LinkedIn", "https://www.linkedin.com/in/serdar-sara%C3%A7-3660466a/")]},
    "ar": {"ad": "العربية", "kisa": "AR", "dir": "rtl", "locale": "ar_AR",
           "unvan": "محاسب قانوني معتمد",
           "menu": [("الخدمات", "/ar/services/"), ("التجارة الدولية", "/ar/international/"), ("من نحن", "/ar/about/")],
           "iletisim": ("اتصل بنا", "/ar/contact/"), "menu_ad": "القائمة الرئيسية", "atla": "انتقل إلى المحتوى",
           "yaz_meta": "سردار سراج، محاسب قانوني معتمد · آخر تحديث: %s", "kisaca": "باختصار",
           "dayanak": "السند القانوني", "yazi_not": "هذا المقال لأغراض المعلومات العامة فقط. قد تتغير التشريعات، لذا يجب تقييم كل حالة بعينها وفق التشريعات السارية وقت التقييم.",
           "alt": [("صاحب المكتب", "سردار سراج (<span lang=\"tr\">Serdar Saraç</span>)<br/>محاسب قانوني معتمد (<span lang=\"tr\">Serbest Muhasebeci Mali Müşavir</span>)"),
                   ("الاسم الرسمي للمكتب", "<span lang=\"tr\" dir=\"ltr\">Serdar Saraç Serbest Muhasebeci Mali Müşavir Bürosu</span><br/>رقم تسجيل المكتب 27853 · الاسم المستخدم: <span lang=\"tr\" dir=\"ltr\">SNS Danışmanlık</span>"),
                   ("الغرفة المهنية", "غرفة المحاسبين القانونيين المعتمدين في إسطنبول (<span lang=\"tr\">İSMMMO</span>)<br/>رقم التسجيل 60446 · رقم الترخيص 342135321<br/>تاريخ التسجيل: 05.03.2024"),
                   ("لغات العمل", "التركية · الإنجليزية"),
                   ("العنوان", "<span lang=\"tr\" dir=\"ltr\">Hamidiye Mah., Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2, 34408 Kağıthane / İstanbul</span>، تركيا"),
                   ("التواصل", "<span dir=\"ltr\">+90 532 624 99 33</span> (واتساب أيضاً)<br/><span dir=\"ltr\">info@snsdanismanlik.com.tr</span>")],
           "alt_link": [("الخصوصية وملفات تعريف الارتباط", "/ar/privacy/"), ("إمكانية الوصول (بالتركية)", "/erisilebilirlik/"),
                        ("LinkedIn", "https://www.linkedin.com/in/serdar-sara%C3%A7-3660466a/")]},
    "fa": {"ad": "فارسی", "kisa": "FA", "dir": "rtl", "locale": "fa_IR",
           "unvan": "حسابدار رسمی و مشاور مالی",
           "menu": [("خدمات", "/fa/services/"), ("تجارت بین‌المللی", "/fa/international/"), ("درباره ما", "/fa/about/")],
           "iletisim": ("تماس با ما", "/fa/contact/"), "menu_ad": "منوی اصلی", "atla": "رفتن به محتوا",
           "yaz_meta": "سردار ساراچ، حسابدار رسمی و مشاور مالی · آخرین به‌روزرسانی: %s", "kisaca": "به طور خلاصه",
           "dayanak": "مبنای قانونی", "yazi_not": "این مطلب صرفاً جنبه اطلاع‌رسانی عمومی دارد. مقررات ممکن است تغییر کند؛ بنابراین هر مورد مشخص باید بر اساس مقررات جاری بررسی شود.",
           "alt": [("مدیر دفتر", "سردار ساراچ (<span lang=\"tr\">Serdar Saraç</span>)<br/>حسابدار رسمی و مشاور مالی (<span lang=\"tr\">Serbest Muhasebeci Mali Müşavir</span>)"),
                   ("نام رسمی دفتر", "<span lang=\"tr\" dir=\"ltr\">Serdar Saraç Serbest Muhasebeci Mali Müşavir Bürosu</span><br/>شماره ثبت دفتر 27853 · نام مورد استفاده: <span lang=\"tr\" dir=\"ltr\">SNS Danışmanlık</span>"),
                   ("کانون حرفه‌ای", "کانون حسابداران رسمی و مشاوران مالی استانبول (<span lang=\"tr\">İSMMMO</span>)<br/>شماره عضویت 60446 · شماره پروانه 342135321<br/>تاریخ ثبت: 05.03.2024"),
                   ("زبان‌های کاری", "ترکی · انگلیسی"),
                   ("نشانی", "<span lang=\"tr\" dir=\"ltr\">Hamidiye Mah., Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2, 34408 Kağıthane / İstanbul</span>، ترکیه"),
                   ("تماس", "<span dir=\"ltr\">+90 532 624 99 33</span> (واتس‌اپ)<br/><span dir=\"ltr\">info@snsdanismanlik.com.tr</span>")],
           "alt_link": [("حریم خصوصی و کوکی‌ها", "/fa/privacy/"), ("دسترس‌پذیری (به ترکی)", "/erisilebilirlik/"),
                        ("LinkedIn", "https://www.linkedin.com/in/serdar-sara%C3%A7-3660466a/")]},
}
DIL_CSS = (".dl{background:#F4F4F2;color:#2B2F33;font-family:Manrope,sans-serif;min-height:100vh}"
           ".dl-ust{max-width:1248px;margin:0 auto;padding:28px 24px;display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:space-between}"
           ".dl-logo{display:flex;align-items:center;gap:16px;text-decoration:none;color:#2B2F33}"
           ".dl-logo b{display:block;font:400 22px/1.2 Fraunces,serif}.dl-logo small{display:block;margin-top:4px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#4A5056}"
           ".dl-menu{display:flex;flex-wrap:wrap;align-items:center;gap:12px 30px;font-size:14px;letter-spacing:.08em;text-transform:uppercase}"
           ".dl-menu a{color:#2F3437;text-decoration:none}.dl-menu a[aria-current]{color:#2B2F33;border-bottom:1px solid #1FA86D;padding-bottom:3px}"
           ".dl-menu a.dl-ilet{border:1px solid #1FA86D;padding:12px 22px;color:#2B2F33}"
           ".dl-dil{display:flex;gap:10px;color:#666C72}.dl-dil a{color:#666C72}.dl-dil b{color:#2B2F33;font-weight:600}"
           ".dl-w{max-width:1248px;margin:0 auto;padding:0 24px}"
           ".dl-hero{border-top:1px solid #E1E4DE;padding:72px 0 56px;background:radial-gradient(circle 300px at 76% 40%,rgba(61,220,151,.30),rgba(61,220,151,0) 100%),radial-gradient(circle 220px at 58% 85%,rgba(31,168,109,.12),rgba(31,168,109,0) 100%)}"
           ".dl-ey{margin:0;font-size:13px;letter-spacing:.26em;text-transform:uppercase;color:#2B2F33;border-left:3px solid #1FA86D;padding-left:10px}"
           ".dl h1{margin:22px 0 0;max-width:22ch;font:300 clamp(40px,5.2vw,72px)/1.08 Fraunces,serif;letter-spacing:-.015em;text-wrap:balance}"
           ".dl h2,.dl h3,.yz h1{text-wrap:balance}"
           ".dl-lead{margin:28px 0 0;max-width:680px;font-size:19px;line-height:1.7;color:#4A5056}"
           ".dl-cta{margin-top:36px;display:flex;flex-wrap:wrap;gap:18px;align-items:center;font-size:16px;color:#4A5056}"
           ".dl-btn{background:#3DDC97;color:#14281E;border-radius:999px;padding:18px 30px;text-decoration:none;font-weight:600;letter-spacing:.03em}.dl-btn:hover{background:#1FA86D;color:#FFF}"
           ".dl-sec{padding-top:96px}.dl-sec>.dl-ey{margin-bottom:0}"
           ".dl h2{margin:16px 0 0;font:400 clamp(30px,3.6vw,44px)/1.15 Fraunces,serif}"
           ".dl-p{margin:18px 0 0;max-width:760px;font-size:17px;line-height:1.75;color:#3A3F44}"
           ".dl-grid{margin-top:40px;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));border-top:1px solid #E1E4DE;border-left:1px solid #E1E4DE}"
           ".dl-grid.dl-g3{grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr))}"
           ".dl-card{background:#FFF;padding:30px 28px;border-right:1px solid #E1E4DE;border-bottom:1px solid #E1E4DE}.dl-card h3{margin:0 0 12px;font:500 22px/1.3 Fraunces,serif}"
           ".dl-no{margin:0 0 10px;font:13px 'JetBrains Mono',monospace;color:#2B2F33}"
           ".dl-card ul{margin:0;padding-left:18px;font-size:15.5px;line-height:1.85;color:#3A3F44}.dl-card p{margin:0;font-size:15.5px;line-height:1.7;color:#3A3F44}"
           ".dl-card a{color:#157A4F}.dl-kucuk{margin:20px 0 0;font-size:14px;line-height:1.6;color:#5F656B}"
           ".dl-tl{margin:24px 0 0;padding:0;list-style:none;border-top:1px solid #E1E4DE}.dl-tl li{display:flex;flex-wrap:wrap;gap:4px 24px;padding:14px 0;border-bottom:1px solid #E1E4DE;font-size:16px}"
           ".dl-tl b{flex:0 0 120px;font:600 14px 'JetBrains Mono',monospace;color:#157A4F}.dl-tl span{flex:1 1 280px}"
           ".dl-bilgi{margin-top:48px;border:1px solid #E1E4DE;border-radius:14px;padding:28px 32px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px 32px;font-size:15px;line-height:1.6;color:#2F3437}"
           ".dl-bilgi p{margin:0}.dl-bilgi p:first-child{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#666C72}.dl-bilgi p+p{margin-top:4px}"
           ".dl-alt{max-width:1248px;margin:0 auto;padding:40px 24px 48px;display:flex;flex-wrap:wrap;gap:16px 32px;justify-content:space-between;font-size:14px;color:#666C72}"
           ".dl-alt a{color:#666C72}.dl-alt span{display:flex;flex-wrap:wrap;gap:24px}"
           ".dl table{border-collapse:collapse;width:100%;font-size:15.5px}.dl td,.dl th{text-align:start;padding:10px 12px;border-bottom:1px solid #E1E4DE}"
           "@media(max-width:700px){.dl-hero{padding:48px 0 40px}.dl-sec{padding-top:64px}.dl-card{padding:24px 20px}}"
           # Arapça: sağdan sola, Noto Naskh Arabic; büyük harf ve harf aralığı Arapçada kullanılmaz
           "[dir=rtl] .dl,[dir=rtl].dl{font-family:'Noto Naskh Arabic',Manrope,serif}"
           "[dir=rtl] .dl-menu,[dir=rtl] .dl-ey,[dir=rtl] .dl-logo small,[dir=rtl] .dl-bilgi p:first-child{letter-spacing:0;text-transform:none}"
           "[dir=rtl] .dl-menu{font-size:16px}[dir=rtl] .dl-ey{font-size:15px;border-left:0;padding-left:0;border-right:3px solid #1FA86D;padding-right:10px}"
           "[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3{font-family:'Noto Naskh Arabic',serif!important;font-weight:600!important;letter-spacing:0}"
           "[dir=rtl] .dl h1{line-height:1.35}[dir=rtl] .dl h2{line-height:1.4}[dir=rtl] .dl-lead,[dir=rtl] .dl-p{line-height:1.9}"
           "[dir=rtl] .dl-card ul{padding-left:0;padding-right:18px}[dir=rtl] .dl-logo b,[dir=rtl] [lang=tr],[dir=rtl] [lang=en]{font-family:Manrope,sans-serif}"
           "[dir=rtl] .dl-logo b{font-family:Fraunces,serif}"
           "[dir=rtl] .yz{font-family:'Noto Naskh Arabic',serif}[dir=rtl] .yz p{line-height:1.95}[dir=rtl] .yz ul,[dir=rtl] .yz ol{padding-left:0;padding-right:22px}"
           "[dir=rtl] .yz blockquote{border-left:0;padding:4px 22px 4px 0;border-right:2px solid #1FA86D;font-family:'Noto Naskh Arabic',serif}"
           "[dir=rtl] .yz-ust{letter-spacing:0;text-transform:none;font-size:15px;border-left:0;padding-left:0;border-right:3px solid #1FA86D;padding-right:10px}"
           "[dir=rtl] .yz-kisaca{border-left:1px solid #E1E4DE;border-right:4px solid #1FA86D}[dir=rtl] .yz-kisaca h2{letter-spacing:0;text-transform:none;font-size:15px}"
           "[dir=rtl] .yz-kisaca ul{padding-left:0;padding-right:20px}[dir=rtl] .dl-tl b[dir=ltr]{text-align:right}")
LOGO_SVG = ('<svg aria-hidden="true" height="40" style="flex:none" viewBox="8 10 80 76" width="40"><rect fill="#1FA86D" height="10" width="80" x="8" y="10"></rect>'
            '<rect fill="#1FA86D" height="38" width="10" x="8" y="10"></rect><rect fill="#2B2F33" height="10" width="80" x="8" y="43"></rect>'
            '<rect fill="#1FA86D" height="38" width="10" x="78" y="48"></rect><rect fill="#1FA86D" height="10" width="80" x="8" y="76"></rect></svg>')
DIL_ESLES = {}   # Türkçe adres -> {dil: adres}; hreflang ve dil seçici için
dil_sayfalar = []
for dil, D in DILLER.items():
    for dosya in sorted(glob.glob("kaynak/%s/*.html" % dil) + glob.glob("kaynak/%s/yazilar/*.html" % dil)):
        metin = open(dosya, encoding="utf-8").read()
        m = re.match(r"<!--META (\{.*?\}) -->\n", metin, re.S)
        meta = json.loads(m.group(1)); meta["icerik"] = metin[m.end():]; meta["dil"] = dil
        dil_sayfalar.append(meta)
        if meta.get("tr"):
            DIL_ESLES.setdefault(meta["tr"], {})[dil] = meta["yol"]
def hreflang(tr_yol, diller):
    h = '<link rel="alternate" hreflang="tr" href="%s%s">\n' % (ALAN, tr_yol)
    h += "".join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (d, ALAN, y) for d, y in sorted(diller.items()))
    return h + '<link rel="alternate" hreflang="x-default" href="%s%s">\n' % (ALAN, tr_yol)
for meta in dil_sayfalar:
    dil, D, yol = meta["dil"], DILLER[meta["dil"]], meta["yol"]
    tr_yol = meta.get("tr") or "/"
    menu = "".join('<a href="%s"%s>%s</a>' % (y, ' aria-current="page"' if yol.startswith(y) else "", ad) for ad, y in D["menu"])
    karsilik = DIL_ESLES.get(tr_yol, {}) if meta.get("tr") else {}
    secici = '<a href="%s" lang="tr" hreflang="tr" aria-label="TR – Türkçe">TR</a>' % tr_yol + "".join(
        ('<b aria-current="true" lang="%s">%s</b>' % (d, DILLER[d]["kisa"])) if d == dil else
        ('<a href="%s" lang="%s" hreflang="%s" aria-label="%s – %s">%s</a>' % (karsilik.get(d, "/%s/" % d), d, d, DILLER[d]["kisa"], DILLER[d]["ad"], DILLER[d]["kisa"]))
        for d in DILLER)
    ust = ('<div class="sayfa" id="%s"><div class="dl" dir="%s">\n<header class="dl-ust">\n<a class="dl-logo" href="/%s/">%s<span><b lang="tr">SNS Danışmanlık</b><small>Serdar Saraç · %s</small></span></a>\n'
           '<nav class="dl-menu" aria-label="%s">%s<span class="dl-dil">%s</span>'
           '<a class="dl-ilet" href="%s"%s>%s</a></nav>\n</header>\n'
           % ("%s-%s" % (dil, yol.strip("/").replace("/", "-") or "ana"), D["dir"], dil, LOGO_SVG, D["unvan"], D["menu_ad"], menu, secici,
              D["iletisim"][1], ' aria-current="page"' if yol == D["iletisim"][1] else "", D["iletisim"][0]))
    alt = ('<section class="dl-w"><div class="dl-bilgi">' + "".join('<div><p>%s</p><p>%s</p></div>' % x for x in D["alt"]) + '</div></section>\n'
           '<footer class="dl-alt"><span>© 2026 <span lang="tr">SNS Danışmanlık</span></span><span>'
           + "".join('<a href="%s">%s</a>' % (y, ad) for ad, y in D["alt_link"]) + '</span></footer>\n</div></div>')
    icerik = meta["icerik"]
    ek_bas = hreflang(tr_yol, DIL_ESLES.get(tr_yol, {dil: yol})) if meta.get("tr") else ""
    if meta.get("tur") == "yazi":
        kaynak = re.search(r"<!--KAYNAK (.*?) -->", icerik, re.S)
        icerik = re.sub(r"<!--KAYNAK .*? -->", "", icerik, flags=re.S).strip()
        kis = ('<section class="yz-kisaca" aria-labelledby="yz-kisaca-b"><h2 id="yz-kisaca-b">%s</h2><ul>' % D["kisaca"]
               + "".join("<li>%s</li>" % x for x in meta["kisaca"]) + "</ul></section>\n") if meta.get("kisaca") else ""
        icerik = ('<article class="yz"><p class="yz-ust">%s</p><h1>%s</h1><p class="yz-meta">%s</p>\n%s%s\n'
                  % (meta["kategori"], meta["baslik"], D["yaz_meta"] % meta["guncelleme"], kis, icerik)
                  + ('<p class="yz-dayanak"><b>%s:</b> %s</p>' % (D["dayanak"], kaynak.group(1).strip()) if kaynak else "")
                  + '<p class="yz-not">%s</p></article>\n' % D["yazi_not"])
        tarih_iso = "-".join(reversed(meta["guncelleme"].split(".")))
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": meta["baslik"], "description": meta["aciklama"],
              "dateModified": tarih_iso, "inLanguage": dil, "mainEntityOfPage": ALAN + yol,
              "author": {"@type": "Person", "name": "Serdar Saraç", "jobTitle": D["unvan"]},
              "publisher": {"@type": "Organization", "name": "SNS Danışmanlık", "url": ALAN}}
        ek_bas += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False)
    elif meta.get("buro_kaydi"):
        ek_bas += ISLETME_LD_HTML
    bas = bas_yap(yol, meta["baslik"] + " · SNS Danışmanlık", meta["aciklama"], ek_bas, None, "article" if meta.get("tur") == "yazi" else "website")
    bas = bas.replace('<html lang="tr">', '<html lang="%s" dir="%s">' % (dil, D["dir"]), 1).replace('content="tr_TR"', 'content="%s"' % D["locale"], 1)
    sayfa = (bas + '<a class="atla" href="#icerik">%s</a>\n' % D["atla"] + govde_on + "<style>%s%s</style>\n" % (DIL_CSS, YZ_CSS)
             + ust + icerik + "\n" + alt + "\n</body>\n</html>\n")
    hedef = yol.strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, yol, len(sayfa))); ek_adresler.append(yol)

# --- Son işlem: menü etiketleri ve kur bandı sunucu tarafında hazır gelsin (sayfa yüklenirken kayma olmasın) ---
MENU_ETIKET = dict(re.findall(r"'([^']+)':\{t:'([^']+)'", menu_js))
try:
    KUR = json.load(open("kurlar.json", encoding="utf-8"))
except Exception:
    KUR = {}
def tr4(x):
    return ("%.4f" % float(x)).replace(".", ",")
def kur_bandi(html):
    K = KUR.get("kurlar") or {}
    if not K.get("USD"):
        return html
    html = re.sub(r'(<span data-kod="([A-Z]{3})">\2 <strong[^>]*>)–(</strong>)',
                  lambda m: m.group(1) + (tr4(K[m.group(2)]) if m.group(2) in K else "–") + m.group(3), html)
    P = KUR.get("parite") or {}
    try:
        eu = P.get("EUR/USD") or float(K["EUR"]) / float(K["USD"]); gu = P.get("GBP/USD") or float(K["GBP"]) / float(K["USD"])
        L = [("EUR/USD", eu), ("GBP/USD", gu), ("EUR/GBP", P.get("EUR/GBP") or eu / gu), ("USD/QAR", P.get("USD/QAR") or float(K["USD"]) / float(K["QAR"]))]
    except Exception:
        return html
    par = ('<span class="kur-parite" style="margin-left:auto;display:flex;gap:18px;flex-wrap:nowrap;white-space:nowrap;color:#C9CDD0" title="Çapraz kurlar (TCMB)">'
           '<span style="color:#3DDC97;font-weight:600;letter-spacing:.04em">Parite</span>'
           + "".join('<span>%s <strong style="color:#FFFFFF;font-weight:600">%s</strong></span>' % (a, tr4(v)) for a, v in L) + '</span>\n')
    return re.sub(r'<span style="margin-left: auto; color: #B9BEC2" class="kur-tarih">TCMB</span>',
                  par + '<span style="margin-left: 0; color: #B9BEC2" class="kur-tarih">TCMB · %s</span>' % KUR.get("tarih", ""), html)
def menu_etiket(html):
    def nav(m):
        return re.sub(r'<a href="([^"]+)" style="([^"]*)">([^<]*)</a>',
                      lambda a: '<a class="mm-on" href="%s" style="%s">%s</a>' % (a.group(1), a.group(2), MENU_ETIKET[a.group(1)]) if a.group(1) in MENU_ETIKET else a.group(0), m.group(0))
    return re.sub(r'<nav aria-label="Ana menü".*?</nav>', nav, html, flags=re.S)

# erişilebilirlik: İngilizce terimler ekran okuyucuda İngilizce telaffuzla okunsun (yalnız görünen metin düğümleri)
EN_TERIM = ["Commercial Invoice", "Proforma Invoice", "Packing List", "packing list", "Origin Declaration", "Incoterms", "Cash Flow", "Notify"]
_EN_RE = re.compile(r"\b(" + "|".join(re.escape(x) for x in sorted(EN_TERIM, key=len, reverse=True)) + r")\b")
_ATLA = ("script", "style", "title", "option", "textarea", "head", "svg")
CF_ANALIZ = """<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "270111e077c64b8d85784514fc8d95d6"}'></script>\n"""
def ingilizce_isaretle(html):
    parca = re.split(r"(<[^>]+>)", html); ic = []; out = []
    for p in parca:
        if p.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", p)
            if m and m.group(2).lower() in _ATLA and not p.endswith("/>"):
                if m.group(1): 
                    if ic and ic[-1] == m.group(2).lower(): ic.pop()
                else: ic.append(m.group(2).lower())
            out.append(p)
        elif ic or not p.strip():
            out.append(p)
        else:
            out.append(_EN_RE.sub(r'<span lang="en">\1</span>', p))
    return "".join(out)
for h, y, n in uretilen:
    t = open(h, encoding="utf-8").read()
    t2 = menu_etiket(kur_bandi(t))
    t2 = ingilizce_isaretle(t2)
    # ziyaret sayacı: Cloudflare Web Analytics (çerezsiz, kişiyi tanımlamaz)
    if "cloudflareinsights" not in t2:
        t2 = t2.replace("</body>", CF_ANALIZ + "</body>", 1)
    # erişilebilirlik: içeriğe geç bağlantısı, kur bandı etiketi, hesap sonuçlarının ekran okuyucuya bildirilmesi
    if 'class="atla"' not in t2:
        t2 = t2.replace("<body>\n", '<body>\n<a class="atla" href="#icerik">İçeriğe geç</a>\n', 1)
    # dil seçici ve hreflang: Türkçe sayfalarda menüdeki boş alana diğer dil bağlantıları
    if not any(h.startswith(d + "/") for d in DILLER):
        karsilik = DIL_ESLES.get(y, {})
        secici = "".join('<a href="%s" lang="%s" hreflang="%s" style="color: #666C72; text-decoration: none" aria-label="%s – %s">%s</a>'
                         % (karsilik.get(d, "/%s/" % d), d, d, DILLER[d]["kisa"], DILLER[d]["ad"], DILLER[d]["kisa"]) for d in DILLER)
        t2 = t2.replace('<span style="display: flex; gap: 12px; color: #666C72"></span>',
                        '<span style="display: flex; gap: 12px; color: #666C72"><b style="color: #2B2F33; font-weight: 600" aria-current="true">TR</b>%s</span>' % secici, 1)
        if karsilik and 'hreflang="x-default"' not in t2:
            t2 = t2.replace("</head>", hreflang(y, karsilik) + "</head>", 1)
    k = t2.find("</header>")
    if k > 0 and 'id="icerik"' not in t2:
        t2 = t2[:k + 9] + '\n<span id="icerik" tabindex="-1"></span>' + t2[k + 9:]
    t2 = t2.replace('<div class="kurdis" style=', '<div class="kurdis" role="region" aria-label="TCMB döviz kurları ve pariteler" style=')
    if h.startswith("hesaplama-merkezi/"):
        t2 = re.sub(r'class="hm-izgara"(?![^>]*aria-live)', 'class="hm-izgara" aria-live="polite"', t2, count=1)
    if h.startswith("yazilar/") and h != "yazilar/index.html":
        a = t2.find('<article class="yz">'); b = t2.find('</article>', a)
        t2 = t2[:a] + t2[a:b].replace("<h3>", '<h2 class="yz-ara">').replace("</h3>", "</h2>") + t2[b:]
    # erişilebilirlik: kaydırılabilir tablolar klavyeyle odaklanabilsin (axe: scrollable-region-focusable)
    if '<div class="yz-tablo">' in t2:
        m_dil = re.search(r'<html lang="([a-z]+)"', t2)
        etiket = {"en": "Table", "ar": "جدول", "fa": "جدول"}.get(m_dil.group(1) if m_dil else "tr", "Tablo")
        t2 = t2.replace('<div class="yz-tablo">', '<div class="yz-tablo" tabindex="0" role="region" aria-label="%s">' % etiket)
    # SSS: data-sss işaretli bölümdeki soru-cevaplardan FAQPage yapılandırılmış verisi
    m = re.search(r"<section[^>]*data-sss[^>]*>(.*?)</section>", t2, re.S)
    if m and '"FAQPage"' not in t2:
        temiz = lambda x: html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
        ciftler = re.findall(r"<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>", m.group(1), re.S)
        ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": temiz(q), "acceptedAnswer": {"@type": "Answer", "text": temiz(a)}} for q, a in ciftler]}
        t2 = t2.replace("</head>", '<script type="application/ld+json">%s</script>\n</head>' % json.dumps(ld, ensure_ascii=False), 1)
    if t2 != t:
        open(h, "w", encoding="utf-8").write(t2)

open("sitemap.xml", "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join("  <url><loc>%s%s</loc></url>\n" % (ALAN, y) for y in [v[0] for v in SAYFALAR.values()] + ek_adresler)
    + "</urlset>\n")
open("robots.txt", "w", encoding="utf-8").write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % ALAN)

# llms.txt: yapay zekâ arama araçlarının siteyi hızlı tanıması için sade özet (llmstxt.org biçimi)
import html
def _baslik_aciklama(y):
    t = open((y.strip("/") + "/index.html") if y != "/" else "index.html", encoding="utf-8").read()
    b = re.search(r"<title>(.*?)</title>", t, re.S).group(1)
    a = re.search(r'<meta name="description" content="(.*?)">', t, re.S).group(1)
    return html.unescape(b).split(" · SNS")[0], html.unescape(a)
_gruplar = [("Ana sayfalar", lambda y: not y.startswith(("/yazilar/", "/hesaplama-merkezi/", "/en/", "/ar/")) or y == "/yazilar/"),
            ("English pages", lambda y: y.startswith("/en/")),
            ("صفحات باللغة العربية (Arabic pages)", lambda y: y.startswith("/ar/")),
            ("صفحات به زبان فارسی (Persian pages)", lambda y: y.startswith("/fa/")),
            ("Yazılar ve okuyucu soruları", lambda y: y.startswith("/yazilar/") and y != "/yazilar/"),
            ("Hesaplama Merkezi", lambda y: y.startswith("/hesaplama-merkezi/"))]
_tum = [v[0] for v in SAYFALAR.values()] + ek_adresler
_llms = ("# SNS Danışmanlık · Serdar Saraç, Serbest Muhasebeci Mali Müşavir\n\n"
         "> Serdar Saraç Serbest Muhasebeci Mali Müşavir Bürosu (İSMMMO sicil no 60446), Kağıthane / İstanbul. "
         "Muhasebe, vergi, SGK ve bordro, dış ticaret ve şirket işlemleri konularında hizmet verir. "
         "Sitedeki yazılar ve okuyucu soruları genel bilgilendirme amaçlıdır; somut bir olaya ilişkin mesleki görüş yerine geçmez.\n\n"
         "Adres: Hamidiye Mah. Girne Cad. Çelik Özer İş Merkezi No: 49/1 İç Kapı No: 2, 34408 Kağıthane / İstanbul · "
         "E-posta: info@snsdanismanlik.com.tr · Telefon: +90 532 624 99 33\n")
for _ad, _f in _gruplar:
    _llms += "\n## %s\n\n" % _ad + "".join("- [%s](%s%s): %s\n" % (*_baslik_aciklama(y)[:1], ALAN, y, _baslik_aciklama(y)[1]) for y in _tum if _f(y))
open("llms.txt", "w", encoding="utf-8").write(_llms)

for h, y, n in uretilen:
    print("%-34s %-24s %7d bayt" % (h, y, n))
