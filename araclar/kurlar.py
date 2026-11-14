"""TCMB gösterge niteliğindeki döviz alış kurlarını kurlar.json dosyasına yazar."""
import json, urllib.request, xml.etree.ElementTree as ET

KODLAR = ["USD", "EUR", "GBP", "QAR", "AED", "SAR", "CNY", "CHF", "JPY", "RUB"]
URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (snsdanismanlik.com.tr kur bandi)"})
kok = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
kurlar, satis, capraz = {}, {}, {}
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
        # TCMB çapraz kurları: EUR ve GBP için 1 birim = x USD, diğerleri için 1 USD = x birim
        cro = (c.findtext("CrossRateOther") or "").strip()
        cru = (c.findtext("CrossRateUSD") or "").strip()
        if kod in ("EUR", "GBP") and cro:
            capraz[kod + "/USD"] = float(cro)
        elif cru:
            capraz["USD/" + kod] = float(cru)
if "USD" not in kurlar:
    raise SystemExit("USD kuru bulunamadi, dosya degistirilmedi")
# çapraz kur yoksa ya da alış kurlarından hesaplanan değerden %3'ten fazla saparsa hesaplanan değer kullanılır
hesap = {}
if all(x in kurlar for x in ("USD", "EUR", "GBP", "QAR")):
    u = float(kurlar["USD"])
    hesap = {"EUR/USD": float(kurlar["EUR"]) / u, "GBP/USD": float(kurlar["GBP"]) / u, "USD/QAR": u / float(kurlar["QAR"])}
parite = {}
for ad in ("EUR/USD", "GBP/USD", "USD/QAR"):
    v = capraz.get(ad)
    if ad in hesap and (v is None or abs(v / hesap[ad] - 1) > 0.03):
        v = hesap[ad]
    if v:
        parite[ad] = round(v, 4)
capraz.update({x: parite[x] for x in parite})
if "EUR/USD" in capraz and "GBP/USD" in capraz:
    parite["EUR/GBP"] = round(capraz["EUR/USD"] / capraz["GBP/USD"], 4)
json.dump({"tarih": kok.get("Tarih"), "kurlar": kurlar, "satis": satis, "parite": parite}, open("kurlar.json", "w"), ensure_ascii=False)
print(kok.get("Tarih"), kurlar, satis, parite)
