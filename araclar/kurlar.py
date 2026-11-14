"""TCMB gösterge niteliğindeki döviz alış kurlarını kurlar.json dosyasına yazar."""
import json, urllib.request, xml.etree.ElementTree as ET

KODLAR = ["USD", "EUR", "GBP", "QAR", "AED", "SAR", "CNY", "CHF", "JPY", "RUB"]
URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (snsdanismanlik.com.tr kur bandi)"})
kok = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
kurlar, satis = {}, {}
for c in kok.findall("Currency"):
    kod = c.get("CurrencyCode")
    if kod in KODLAR:
        alis = (c.findtext("ForexBuying") or "").strip()
        birim = float((c.findtext("Unit") or "1").strip() or 1)
        sat = (c.findtext("ForexSelling") or "").strip()
        if alis:
            kurlar[kod] = f"{float(alis) / birim:.4f}"
        if sat:
            satis[kod] = f"{float(sat) / birim:.4f}"
if "USD" not in kurlar:
    raise SystemExit("USD kuru bulunamadi, dosya degistirilmedi")
json.dump({"tarih": kok.get("Tarih"), "kurlar": kurlar, "satis": satis}, open("kurlar.json", "w"), ensure_ascii=False)
print(kok.get("Tarih"), kurlar, satis)
