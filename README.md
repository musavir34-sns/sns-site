# SNS Danışmanlık web sitesi

snsdanismanlik.com.tr adresinde yayınlanan sitenin dosyaları.

## Düzenleme
- Sitenin tek kaynağı `kaynak/tek-sayfa.html` dosyasıdır. Değişiklik orada yapılır.
- Sonra depo kök klasöründe `python3 araclar/sayfala.py` çalıştırılır; her bölüm kendi adresine yazılır
  (`/hizmetler/`, `/gundem/`, `/iletisim/` …) ve `sitemap.xml`, `robots.txt` yeniden üretilir.

## Otomatik güncellenen dosyalar
- `kurlar.json`: TCMB döviz alış kurları, hafta içi her gün 15:50
- `duyurular.json`: TÜRMOB mevzuat sirkülerleri ve İSMMMO duyuruları, her gün 08:10, 13:10, 18:10

## Diğer
- `404.html`: bulunamayan adresleri ana sayfaya yönlendirir
- `CNAME`: alan adı tanımı
