"""TÜRMOB mevzuat sirkülerlerini ve İSMMMO duyurularını duyurular.json dosyasına yazar.

Kaynaklardan biri okunamazsa o kaynağın önceki kayıtları korunur.
Test için: python3 duyurular.py --yerel turmob.html ismmmo.html
"""
import html, json, re, sys, urllib.request
from datetime import datetime, timezone, timedelta

TURMOB = "https://www.turmob.org.tr/Sirkuler"
ISMMMO = "https://www.ismmmo.org.tr/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
ADET = 12


def indir(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")


def temiz(t):
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def baglantilar(s):
    return re.findall(r"<a[^>]+href=[\"']?([^\"' >]+)[^>]*>(.*?)</a>", s, re.S)


def turmob_oku(s):
    """'Vergi / 10.11.2026/123 Başlık' biçimindeki sirküler satırları."""
    sonuc, gorulen = [], set()
    for href, metin in baglantilar(s):
        if "/sirkuler/detailPdf/" not in href:
            continue
        t = temiz(metin)
        m = re.match(r"(.+?)\s*/\s*(\d{2}\.\d{2}\.\d{4})\s*/\s*(\d+)\s+(.+)", t)
        if not m or href in gorulen:
            continue
        gorulen.add(href)
        kategori, tarih, no, baslik = m.groups()
        url = href if href.startswith("http") else "https://www.turmob.org.tr" + href
        sonuc.append({"tarih": tarih, "no": no, "konu": kategori.strip(), "baslik": baslik.strip(), "url": url})
    return sonuc[:ADET]


def ismmmo_oku(s):
    """Ana sayfadaki duyuru ve mevzuat dosyaları; tarih dosya adındaki GGAAYYYY kısmından."""
    sonuc, gorulen = [], set()
    for href, metin in baglantilar(s):
        m = re.search(r"/dosya/\d+/(Mevzuat|Kurumsal)-Dosya/(\d{2})(\d{2})(\d{4})[-_]", href)
        if not m:
            continue
        baslik = temiz(metin)
        if len(baslik) < 15 or href in gorulen:
            continue
        gorulen.add(href)
        tur, g, a, y = m.groups()
        baslik = re.sub(r"^(DUYURU|Duyuru)\s*:\s*", "", baslik)
        url = href if href.startswith("http") else "https://www.ismmmo.org.tr" + href
        sonuc.append({"tarih": f"{g}.{a}.{y}", "konu": "Mevzuat" if tur == "Mevzuat" else "Duyuru", "baslik": baslik, "url": url})
    sonuc.sort(key=lambda x: datetime.strptime(x["tarih"], "%d.%m.%Y"), reverse=True)
    return sonuc[:ADET]


def main():
    try:
        eski = json.load(open("duyurular.json", encoding="utf-8"))
    except Exception:
        eski = {"turmob": [], "ismmmo": []}
    yerel = "--yerel" in sys.argv
    yeni = {}
    for anahtar, url, okuyucu, dosya_idx in (("turmob", TURMOB, turmob_oku, 2), ("ismmmo", ISMMMO, ismmmo_oku, 3)):
        try:
            s = open(sys.argv[dosya_idx], encoding="utf-8", errors="replace").read() if yerel else indir(url)
            kayitlar = okuyucu(s)
            if not kayitlar:
                raise ValueError("kayıt bulunamadı")
            yeni[anahtar] = kayitlar
            print(anahtar, len(kayitlar), "kayıt")
        except Exception as e:
            print(anahtar, "OKUNAMADI, önceki kayıtlar korunuyor:", e)
            yeni[anahtar] = eski.get(anahtar, [])
    if yeni["turmob"] == eski.get("turmob") and yeni["ismmmo"] == eski.get("ismmmo"):
        print("değişiklik yok")
        return
    yeni["guncelleme"] = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m.%Y %H:%M")
    json.dump(yeni, open("duyurular.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
