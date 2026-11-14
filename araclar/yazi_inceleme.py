#!/usr/bin/env python3
"""kaynak/yazilar/*.html taslaklarından değişiklikleri işaretli inceleme sayfası üretir.
Kullanım: python3 araclar/yazi_inceleme.py CIKTI.html [slug ...]"""
import glob, json, os, re, sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cikti = sys.argv[1]
secili = sys.argv[2:]
dosyalar = sorted(glob.glob(os.path.join(KOK, "kaynak/yazilar/*.html")))
yazilar = []
for d in dosyalar:
    s = open(d, encoding="utf-8").read()
    meta = json.loads(re.search(r"<!--META (.*?) -->", s, re.S).group(1))
    if secili and meta["slug"] not in secili:
        continue
    govde = re.sub(r"<!--META .*? -->", "", s, flags=re.S)
    kaynak = re.search(r"<!--KAYNAK (.*?) -->", govde, re.S)
    govde = re.sub(r"<!--KAYNAK .*? -->", "", govde, flags=re.S)
    yazilar.append((meta, govde.strip(), kaynak.group(1).strip() if kaynak else "", len(re.findall(r"<ins>", govde)), len(re.findall(r"<del>", govde))))

sira = {s: i for i, s in enumerate(secili)}
yazilar.sort(key=lambda y: sira.get(y[0]["slug"], 99))

icindekiler = "".join('<li><a href="#%s">%s</a> <span>%d ekleme · %d çıkarma</span></li>' % (m["slug"], m["baslik"], a, c) for m, _, _, a, c in yazilar)
bolumler = ""
for i, (m, g, k, a, c) in enumerate(yazilar, 1):
    eski = '<p class="eski">LinkedIn başlığı: <del>%s</del></p>' % m["eski_baslik"] if m.get("eski_baslik") else ""
    bolumler += ('<article id="%s"><p class="ust">%d · %s</p><h2>%s</h2>%s<p class="ozet">%s</p>%s'
                 '<p class="kaynak"><b>Dayanak:</b> %s</p></article>') % (m["slug"], i, m["kategori"], m["baslik"], eski, m["ozet"], g, k)

html = """<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Yazı düzeltmeleri</title><style>
:root{--z:#F4F4F2;--y:#1FA86D;--a:#2B2F33;--k:#C0392B}
*{box-sizing:border-box}body{margin:0;background:var(--z);color:var(--a);font:16px/1.7 Manrope,system-ui,sans-serif}
main{max-width:820px;margin:0 auto;padding:32px 16px 80px}
h1{font:400 36px/1.15 Fraunces,Georgia,serif;margin:0 0 8px}h2{font:400 27px/1.25 Fraunces,Georgia,serif;margin:4px 0 10px}
h3{font-size:17px;margin:22px 0 6px}
.lejant{display:flex;flex-wrap:wrap;gap:14px;font-size:14px;background:#fff;border:1px solid #E1E4DE;border-radius:12px;padding:12px 16px;margin:16px 0}
ins{background:#DDF7EA;color:#0F5A3A;text-decoration:none;border-bottom:2px solid var(--y);padding:0 2px}
del{background:#FBE3E0;color:#8E2A1F;text-decoration:line-through;text-decoration-color:var(--k);padding:0 2px}
nav ol{padding-left:20px}nav li{margin:4px 0}nav li span{font-size:12.5px;color:#666C72;margin-left:6px}nav a{color:var(--a)}
article{background:#fff;border:1px solid #E1E4DE;border-radius:14px;padding:24px 26px;margin:22px 0}
.ust{margin:0;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--y);font-weight:700}
.ozet{color:#4A5056;font-size:14.5px;border-left:3px solid #3DDC97;padding-left:12px}
.eski{font-size:13.5px;color:#666C72;margin:0}
.kaynak{font-size:13px;color:#666C72;border-top:1px solid #EEF0EC;padding-top:10px;margin-top:18px}
@media (prefers-color-scheme:dark){body{background:#1E2124;color:#ECEDEB}article,.lejant{background:#2B2F33;border-color:#3A3F44}nav a{color:#ECEDEB}
ins{background:#123D2B;color:#9EF0C6}del{background:#4A1F1A;color:#F5B5AC}.ozet,.eski,.kaynak,nav li span{color:#B9BEC2}}
</style></head><body><main>
<p class="ust">SNS Danışmanlık · Yazılar</p><h1>Yazı düzeltmeleri</h1>
<p>Üslup ve kurgu korunarak yalnızca yanlış veya eskimiş kısımlar düzeltildi. Onayınızdan sonra işaretler kaldırılıp yazılar siteye alınacak.</p>
<div class="lejant"><span><ins>Yeşil</ins> eklenen veya değiştirilen metin</span><span><del>Kırmızı</del> çıkarılan metin</span></div>
<nav><b>Bu partideki yazılar</b><ol>""" + icindekiler + "</ol></nav>" + bolumler + "</main></body></html>"
open(cikti, "w", encoding="utf-8").write(html)
print(len(yazilar), "yazı →", cikti)
