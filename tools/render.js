// Render each <section class="slide"> in an HTML file to a 1080x1350 JPEG.
// Usage: node tools/render.js <slides.html> <outDir>
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const [html, outDir] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(html), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const slides = await page.$$('section.slide');
  for (let i = 0; i < slides.length; i++) {
    const file = path.join(outDir, String(i + 1).padStart(2, '0') + '.jpg');
    await slides[i].screenshot({ path: file, type: 'jpeg', quality: 92 });
    console.log(file);
  }
  await browser.close();
})();
