// Sitedeki tüm sayfaları axe-core ile WCAG 2.2 AA kurallarına göre tarar.
// GitHub Actions'ta çalışır (.github/workflows/erisilebilirlik.yml).
// Ciddi (serious) veya kritik (critical) bir hata bulunursa iş kırmızı biter; orta ve düşük bulgular raporda listelenir.
const fs = require('fs');
const { chromium } = require('playwright');
const axeModul = require('@axe-core/playwright');
const AxeBuilder = axeModul.AxeBuilder || axeModul.default || axeModul;

const KOK = process.env.KOK || 'http://localhost:8080';
const adresler = [...fs.readFileSync('sitemap.xml', 'utf8').matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map(m => m[1]);
const GORUNUM = [['masaüstü', { width: 1366, height: 900 }], ['mobil', { width: 390, height: 844 }]];

(async () => {
  const tarayici = await chromium.launch();
  const bulgular = [];
  for (const [ad, boyut] of GORUNUM) {
    const sayfa = await tarayici.newPage({ viewport: boyut });
    for (const yol of adresler) {
      await sayfa.goto(KOK + yol, { waitUntil: 'networkidle' });
      await sayfa.waitForTimeout(300);
      const s = await new AxeBuilder({ page: sayfa })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      for (const v of s.violations) {
        bulgular.push({ gorunum: ad, yol, kural: v.id, etki: v.impact, aciklama: v.help, adet: v.nodes.length,
                        ornek: v.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | ') });
      }
    }
    await sayfa.close();
  }
  await tarayici.close();

  const ciddi = bulgular.filter(b => b.etki === 'serious' || b.etki === 'critical');
  let rapor = `## Erişilebilirlik testi (axe-core, WCAG 2.2 AA)\n\n${adresler.length} sayfa × ${GORUNUM.length} görünüm tarandı.\n\n`;
  rapor += bulgular.length
    ? '| Görünüm | Sayfa | Kural | Etki | Adet | Örnek |\n|---|---|---|---|---|---|\n' +
      bulgular.map(b => `| ${b.gorunum} | ${b.yol} | ${b.kural} — ${b.aciklama} | ${b.etki} | ${b.adet} | \`${b.ornek.replace(/\|/g, '/')}\` |`).join('\n') + '\n'
    : 'Hiç bulgu yok. ✓\n';
  console.log(rapor);
  if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, rapor);
  if (ciddi.length) { console.error(`${ciddi.length} ciddi/kritik bulgu var.`); process.exit(1); }
})();
