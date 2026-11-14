"""kaynak/tek-sayfa.html dosyasından her bölüm için ayrı adresli sayfalar üretir.

Çalıştırma (depo kök klasöründe):  python3 araclar/sayfala.py
Üretilenler: index.html, <bolum>/index.html, sitemap.xml, robots.txt
Siteyi düzenlerken yalnızca kaynak/tek-sayfa.html değiştirilir, sonra bu betik çalıştırılır.
"""
import json, os, re

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
            "Adres, telefon, e-posta ve WhatsApp bilgileri. Hamidiye Mah., Girne Cad. Çelik Özer İş Merkezi No: 49/2, 34408 Kağıthane / İstanbul."),
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
for href, ic in re.findall(r'<a href="#([^"]+)"[^>]*>(.*?)</a>', ol, re.S):
    sp = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<span[^>]*>(.*?)</span>", ic, re.S)]
    yazilar.append({"tur": "yazi", "konu": sp[0] if sp else "", "baslik": sp[1] if len(sp) > 1 else "", "url": adres(href)})
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
eski_js = "(function(){var m=%s;var h=location.hash.slice(1);if(h&&m[h])location.replace(m[h]);})();" % json.dumps(eski_harita, ensure_ascii=False, separators=(",", ":"))

ikonlar = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">\n'
           '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n<meta name="theme-color" content="#2B2F33">\n')


def esc(t):
    return t.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def bas_yap(yol, baslik, aciklama, ek=""):
    return ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s<link rel="canonical" href="%s%s">\n'
            '<meta property="og:type" content="website">\n<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s%s">\n<meta property="og:locale" content="tr_TR">\n%s</head>\n<body>\n'
            % (esc(baslik), esc(aciklama), ikonlar, ALAN, yol, esc(baslik), esc(aciklama), ALAN, yol, ek))


uretilen = []
for pid, (yol, baslik, aciklama) in SAYFALAR.items():
    a, b = bolumler[pid]
    govde = s[a:b]
    govde = re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="%s">' % pid, govde, count=1)
    govde = baglanti_cevir(govde, pid)
    govde = govde.replace('href="#ana"', 'href="/"')
    bas = bas_yap(yol, baslik, aciklama, ("<script>%s</script>\n" % eski_js) if pid == "ana" else "")
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
for dosya in sorted(glob.glob("kaynak/hesap/*.html")):
    metin = open(dosya, encoding="utf-8").read()
    m = re.match(r"<!--META (\{.*?\}) -->\n", metin, re.S)
    meta = json.loads(m.group(1)); icerik = metin[m.end():]
    pid = "hesap-" + os.path.basename(dosya)[:-5]
    govde = re.sub(r'<div class="sayfa"[^>]*>', '<div class="sayfa" id="%s">' % pid, ust, count=1) + "\n<script>%s</script>\n" % ortak_js + icerik + "\n" + alt
    sayfa = (bas_yap(meta["yol"], meta["baslik"], meta["aciklama"]) + govde_on + "<style>%s</style>\n" % ortak_css + govde + "\n"
             + "".join("<script>%s</script>\n" % x for x in [yeni_yonlendirme, canli_js, menu_js]) + "</body>\n</html>\n")
    hedef = meta["yol"].strip("/") + "/index.html"
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    open(hedef, "w", encoding="utf-8").write(sayfa)
    uretilen.append((hedef, meta["yol"], len(sayfa))); ek_adresler.append(meta["yol"])

open("sitemap.xml", "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join("  <url><loc>%s%s</loc></url>\n" % (ALAN, y) for y in [v[0] for v in SAYFALAR.values()] + ek_adresler)
    + "</urlset>\n")
open("robots.txt", "w", encoding="utf-8").write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % ALAN)
for h, y, n in uretilen:
    print("%-34s %-24s %7d bayt" % (h, y, n))
