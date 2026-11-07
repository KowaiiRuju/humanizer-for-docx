const fs = require('node:fs');
const path = require('node:path');
const sharp = require('C:/Users/Acer/AppData/Local/OpenAI/Codex/runtimes/cua_node/cfb32733c877621e/bin/node_modules/sharp');
const out = path.join(__dirname, 'revised-diagrams');
const outMain = path.join(__dirname, '..', '..', 'output', 'diagrams');
fs.mkdirSync(out, {recursive: true});
fs.mkdirSync(outMain, {recursive: true});
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const figures = [], checks = [];
const FONT = 'Times New Roman', BODY = 26, HEADING = 29, LEADING = 34;

function figure(n, title, height, draw) {
  const parts = [];
  function text(x, y, lines, bold = false, available = 920) {
    if (typeof lines === 'string') lines = [lines];
    const size = bold ? HEADING : BODY;
    for (const line of lines) checks.push({line, size, available, bold});
    parts.push(`<text x="${x}" y="${y}" text-anchor="middle" font-family="${FONT}" font-size="${size}" font-weight="${bold ? 'bold' : 'normal'}" fill="#111111">${lines.map((s, i) => `<tspan x="${x}" dy="${i ? LEADING : 0}">${esc(s)}</tspan>`).join('')}</text>`);
  }
  function box(x, y, w, h, heading, lines = [], shaded = false) {
    if (typeof heading === 'string') heading = heading ? [heading] : [];
    if (typeof lines === 'string') lines = [lines];
    const count = heading.length + lines.length;
    if (count && (count - 1) * LEADING + 34 > h) throw Error(`Figure ${n}: insufficient box height (${(count - 1) * LEADING + 34} > ${h})`);
    parts.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="${shaded ? '#ededed' : '#ffffff'}" stroke="#222222" stroke-width="2.5"/>`);
    let baseline = y + (h - (count - 1) * LEADING) / 2 + 9;
    if (heading.length) text(x + w / 2, baseline, heading, true, w - 28);
    baseline += heading.length * LEADING;
    if (lines.length) text(x + w / 2, baseline, lines, false, w - 28);
  }
  function arrow(x1, y1, x2, y2) {
    parts.push(`<path d="M${x1} ${y1} L${x2} ${y2}" fill="none" stroke="#222222" stroke-width="2.5" marker-end="url(#arrow)"/>`);
  }
  function line(d) {
    parts.push(`<path d="${d}" fill="none" stroke="#222222" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`);
  }
  // Connected 1-to-2 split from bottom-center (500, yTop) to top-centers (xLeft, yBot) and (xRight, yBot)
  function fork2(yTop, yMid, yBot, xLeft = 252, xRight = 748) {
    line(`M500 ${yTop} L500 ${yMid} L${xLeft} ${yMid} M500 ${yMid} L${xRight} ${yMid}`);
    arrow(xLeft, yMid, xLeft, yBot);
    arrow(xRight, yMid, xRight, yBot);
  }
  // Connected 2-to-1 merge from bottom-centers (xLeft, yTop) and (xRight, yTop) to top-center (500, yBot)
  function merge2(yTop, yMid, yBot, xLeft = 252, xRight = 748) {
    line(`M${xLeft} ${yTop} L${xLeft} ${yMid} L500 ${yMid} M${xRight} ${yTop} L${xRight} ${yMid} L500 ${yMid}`);
    arrow(500, yMid, 500, yBot);
  }
  // Connected 1-to-3 split from (500, yTop) to (xLeft, yBot), (500, yBot), (xRight, yBot)
  function fork3(yTop, yMid, yBot, xLeft = 175, xRight = 825) {
    line(`M500 ${yTop} L500 ${yMid} L${xLeft} ${yMid} M500 ${yMid} L${xRight} ${yMid}`);
    arrow(xLeft, yMid, xLeft, yBot);
    arrow(500, yMid, 500, yBot);
    arrow(xRight, yMid, xRight, yBot);
  }
  // Connected 3-to-1 merge from (xLeft, yTop), (500, yTop), (xRight, yTop) to (500, yBot)
  function merge3(yTop, yMid, yBot, xLeft = 175, xRight = 825) {
    line(`M${xLeft} ${yTop} L${xLeft} ${yMid} L500 ${yMid} M500 ${yTop} L500 ${yMid} M${xRight} ${yTop} L${xRight} ${yMid} L500 ${yMid}`);
    arrow(500, yMid, 500, yBot);
  }

  draw({box, text, arrow, line, fork2, merge2, fork3, merge3});
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="${height}" viewBox="0 0 1000 ${height}"><title>${esc(title)}</title><desc>Consistent Times New Roman typography. Smartphone local flora generalization study.</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#222222"/></marker></defs><rect width="1000" height="${height}" fill="white"/>${parts.join('')}</svg>`;
  figures.push({n, title, height, svg, font: FONT, body_size: BODY, heading_size: HEADING, embedded_width_pt: 243.25});
}

// Figure 1: Research gap in smartphone local flora recognition (height: 540)
figure(1, 'Research gap in smartphone recognition of unseen physical plants', 540, ({box, fork2, merge2}) => {
  box(25, 15, 950, 120, 'In-situ smartphone plant capture (100 plants, 2,000 photos)', [
    '20 handheld photos per plant share leaf geometry, sunlight, and background clutter.'
  ]);
  fork2(135, 162, 190);
  box(25, 190, 455, 150, 'Protocol A (Random image split)', [
    'Same plant appears in train and test.',
    'Inflated by familiar plant & site cues.'
  ]);
  box(520, 190, 455, 150, 'Protocol B (Plant-disjoint CV)', [
    'All 20 views of test plants held out.',
    'Tests recognition of unseen plants.'
  ]);
  merge2(340, 368, 395);
  box(25, 395, 950, 130, 'Research gap: Quantifying the generalization drop (Protocol A vs. B)', [
    'How much Macro F1 do classical descriptors (GLCM/LBP/HOG/HSV)',
    'versus MobileNetV3-Large lose when tested on unseen physical plants?'
  ], true);
});

// Figure 2: Conceptual framework of the comparative experiment (height: 545)
figure(2, 'Conceptual framework for the smartphone local flora benchmark', 545, ({box, arrow, merge2}) => {
  box(25, 15, 455, 150, '1a. Field sampling & tagging', [
    '10 verified species (SP01–SP10).',
    '100 distinct physical plants in',
    'MSU-MCEST, Maigo, & Kolambugan.'
  ]);
  box(520, 15, 455, 150, '1b. Smartphone capture & QC', [
    '20 five-view photos per plant.',
    '2,000 QC-verified RGB images with',
    'specimen_id, view, & lighting logs.'
  ]);
  merge2(165, 190, 215);
  box(25, 215, 950, 145, '2. Controlled benchmark: 6 pipelines × 2 partitioning protocols', [
    '6 Pipelines: Handcrafted ML (3), Frozen MobileNetV3 (2), MobileNetV3-Large (1)',
    '2 Protocols: Protocol A (70/15/15 image split) vs. Protocol B (5-fold plant CV)'
  ]);
  arrow(500, 360, 500, 405);
  box(25, 405, 950, 125, '3. Output: Generalization gap & smartphone deployment guidance', [
    'Macro F1, Generalization Drop Rate (GDR), 2,000-resample plant bootstrap CI,',
    'exact McNemar specimen test, and single-image CPU/GPU inference latency'
  ], true);
});

// Figure 3: Planned smartphone sampling and image acquisition (height: 580)
figure(3, 'Smartphone sampling hierarchy across ten species and 100 physical plants', 580, ({box, text, arrow}) => {
  box(25, 15, 950, 240, '', []);
  text(500, 52, 'Level 1: Ten target local flora classes (SP01–SP10)', true, 920);
  const left = [
    'SP01  Santan (Ixora sp.)',
    'SP02  Lantana (L. camara)',
    'SP03  San Francisco (C. variegatum)',
    'SP04  Ruellia (Ruellia sp.)',
    'SP05  Gumamela (H. rosa-sinensis)'
  ];
  const right = [
    'SP06  Mayana (C. scutellarioides)',
    'SP07  Makahiya (M. pudica)',
    'SP08  Tsitsirika (C. roseus)',
    'SP09  Coatbuttons (T. procumbens)',
    'SP10  Tawa-tawa (E. hirta)'
  ];
  text(265, 92, left, false, 440);
  text(735, 92, right, false, 440);
  arrow(500, 255, 500, 295);
  box(25, 295, 950, 115, 'Level 2: 10 physical plants per species = 100 tagged plants', [
    'Botanical verification, permanent specimen IDs, and exclusion of clonal shoots'
  ]);
  arrow(500, 410, 500, 450);
  box(25, 450, 950, 115, 'Level 3: 20 smartphone photos per plant = 2,000 accepted images', [
    '5 views × 4 shots: habit, top leaf, angled foliage, venation, and node or flower'
  ], true);
});

// Figure 4: Shared evaluation workflow for the six pipelines (height: 530)
figure(4, 'Shared evaluation workflow for the six classification pipelines', 530, ({box, fork3, merge3}) => {
  box(25, 15, 950, 95, 'Locked 224 × 224 RGB smartphone images & split manifests', [
    'Fit feature scalers and model parameters strictly inside each training fold'
  ]);
  fork3(110, 134, 158);
  box(20, 158, 310, 205, 'Handcrafted ML', [
    '3 pipelines',
    'GLCM + LBP + HOG',
    '+ HSV (1,704-D)',
    'HC SVM / RF / XGB'
  ]);
  box(345, 158, 310, 205, 'Hybrid controls', [
    '2 pipelines',
    'Frozen MobileNetV3',
    'features (1,280-D)',
    'HY SVM / HY XGB'
  ]);
  box(670, 158, 310, 205, 'Lightweight DL', [
    '1 mobile CNN',
    'Fine-tuned',
    'MobileNetV3-Large',
    'End-to-end (DL MN3)'
  ]);
  merge3(363, 387, 411);
  box(25, 411, 950, 104, 'Protected outer-test evaluation (Protocol A vs. Protocol B)', [
    'Compare Macro F1, Generalization Drop Rate (GDR), and batch-1 runtime cost'
  ], true);
});

// Figure 5: Random-image and specimen-disjoint evaluation protocols (height: 515)
figure(5, 'Protocol A (random image split) versus Protocol B (specimen-disjoint 5-fold CV)', 515, ({box, text, fork2}) => {
  box(25, 15, 950, 90, 'Full smartphone dataset: 100 physical plants (2,000 images)', [
    '10 species × 10 tagged plants per species × 20 five-view photos per plant'
  ]);
  fork2(105, 128, 152, 252, 748);

  box(20, 152, 465, 348, '', []);
  text(252, 190, 'Protocol A: Random image split', true, 435);
  text(252, 226, 'Splits individual photos (70 / 15 / 15)', false, 435);
  box(45, 248, 415, 58, 'Train: 1,400 photos', []);
  box(45, 318, 200, 58, 'Val: 300', []);
  box(260, 318, 200, 58, 'Test: 300', []);
  text(252, 418, ['Same plant appears in Train & Test.', 'Baseline for familiar plants.'], false, 435);

  box(515, 152, 465, 348, '', [], true);
  text(748, 190, 'Protocol B: Plant-disjoint CV', true, 435);
  text(748, 226, 'Splits whole plants (5-fold CV)', false, 435);
  box(540, 248, 415, 58, 'Train: 60 plants (1,200)', []);
  box(540, 318, 200, 58, 'Val: 20 (400)', []);
  box(755, 318, 200, 58, 'Test: 20 (400)', []);
  text(748, 418, ['20 whole plants held out in Test.', 'Zero plant overlap across splits.'], false, 435);
});

// Figure 6: Analysis and interpretation of held-out predictions (height: 540)
figure(6, 'Statistical testing and practical smartphone deployment evaluation', 540, ({box, fork2, merge2}) => {
  box(25, 15, 950, 115, '1. Out-of-fold predictions & runtime logs (Protocol A & Protocol B)', [
    'Link held-out predictions to image_id, specimen_id, view angle, and lighting state'
  ]);
  fork2(130, 156, 182);
  box(25, 182, 455, 170, '2a. Generalization & significance', [
    'Macro F1, Gap, and Drop Rate (GDR).',
    '2,000-resample plant bootstrap CI.',
    'Exact McNemar test (100 plants).'
  ]);
  box(520, 182, 455, 170, '2b. Error audit & runtime cost', [
    'Per-species confusion matrices.',
    'Error breakdown by view & lighting.',
    'Batch-1 latency, VRAM, & model size.'
  ]);
  merge2(352, 378, 405);
  box(25, 405, 950, 120, '3. Practical smartphone deployment recommendation', [
    'Select pipeline balancing unseen-plant Macro F1 (Protocol B)',
    'and single-image runtime cost for field smartphone use'
  ], true);
});

async function main() {
  for (const {line, size, available, bold} of checks) {
    const sample = `<svg width="1800" height="90" xmlns="http://www.w3.org/2000/svg"><text x="5" y="65" font-family="${FONT}" font-size="${size}" font-weight="${bold ? 'bold' : 'normal'}">${esc(line)}</text></svg>`;
    const result = await sharp(Buffer.from(sample)).trim().toBuffer({resolveWithObject:true});
    if (result.info.width > available) throw Error(`Text exceeds available width (${result.info.width} > ${available}): ${line}`);
  }
  for (const f of figures) {
    fs.writeFileSync(path.join(out, `figure_${f.n}.svg`), f.svg);
    fs.writeFileSync(path.join(outMain, `figure_${f.n}.svg`), f.svg);
    await sharp(Buffer.from(f.svg), {density:216}).png().toFile(path.join(out, `figure_${f.n}.png`));
    await sharp(Buffer.from(f.svg), {density:216}).png().toFile(path.join(outMain, `figure_${f.n}.png`));
  }
  fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(figures.map(({svg,...f})=>f), null, 2));
  console.log('PASS: six logically connected top-to-bottom diagrams generated.');
}
main().catch(e => { console.error(e); process.exitCode = 1; });
