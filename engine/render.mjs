// Renders engine.html with a timeline injected as window.TL.
//   node render.mjs <timeline.json> frames <dir>          -> <dir>/00001.jpg ...
//   node render.mjs <timeline.json> preview <dir> <t>...  -> <dir>/t<t>.png
//   node render.mjs <timeline.json> cover <t> <out.jpg>   -> the hook line as a cover
//   node render.mjs <timeline.json> sounds <out.json>     -> sound cues for reel.py
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const [tlPath, mode, ...rest] = process.argv.slice(2);
const TL = JSON.parse(fs.readFileSync(tlPath, "utf8"));
const url = pathToFileURL(path.join(here, "engine.html")).href;

const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript((tl) => { window.TL = tl; }, TL);
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true || window.readyError, null, { timeout: 60000 });
  const err = await page.evaluate(() => window.readyError || null);
  if (err || errors.length) throw new Error(err || errors.join("\n"));
  return page;
}
const shoot = async (page, t, file, type = "jpeg") => {
  await page.evaluate((t) => window.render(t), t);
  await page.screenshot({ path: file, type, ...(type === "jpeg" ? { quality: 93 } : {}) });
};

try {
  if (mode === "sounds") {
    const page = await openPage();
    fs.writeFileSync(rest[0], JSON.stringify(await page.evaluate(() => window.soundEvents())));
  } else if (mode === "cover") {
    const page = await openPage();
    await page.evaluate(() => { window.COVER = true; });
    await shoot(page, Number(rest[0]), rest[1]);
  } else if (mode === "preview") {
    const [dir, ...times] = rest;
    fs.mkdirSync(dir, { recursive: true });
    const page = await openPage();
    for (const t of times.map(Number)) await shoot(page, t, path.join(dir, `t${t}.png`), "png");
    console.log(times.map((t) => path.join(dir, `t${t}.png`)).join("\n"));
  } else if (mode === "frames") {
    const dir = rest[0];
    fs.mkdirSync(dir, { recursive: true });
    const n = Math.round(TL.total * TL.fps);
    const W = Math.max(2, Math.min(6, os.cpus().length - 2));
    const pages = await Promise.all(Array.from({ length: W }, openPage));
    await Promise.all(pages.map(async (page, w) => {
      for (let f = w; f < n; f += W) await shoot(page, f / TL.fps, path.join(dir, `${String(f + 1).padStart(5, "0")}.jpg`));
    }));
    console.log(`${n} frames`);
  } else {
    throw new Error(`unknown mode ${mode}`);
  }
} finally {
  await browser.close();
}
