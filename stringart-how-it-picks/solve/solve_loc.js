// Re-solves the Short's portrait with the PUBLIC String Art Maker core.js at commit
// 209877cbecb0a351b38da0a4d9dd42d4c57df96d (core-209877c.js, md5 74f36669305ffdaa8c5aa86195f55b6a,
// downloaded from raw.githubusercontent.com) on the exact worker input the Maker page sent for the
// Library of Congress Einstein scan (einsteinloc-input.json; page status in einsteinloc-page.json).
// 1) pristine run: unmodified core, same options as worker.js joint() -> order, line count.
// 2) instrumented run: the same core with READ-ONLY hooks injected in memory (candidate scores, the
//    error arrays, and a scan at the stop). Asserts its order is identical to the pristine one.
// Writes trace-loc.json for extract.py. Run: node solve_loc.js
const fs = require('fs'), crypto = require('crypto'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'core-209877c.js'), 'utf8');
const md5 = crypto.createHash('md5').update(src).digest('hex');
if (md5 !== '74f36669305ffdaa8c5aa86195f55b6a') throw new Error('core.js is not the pinned commit: ' + md5);
const load = (code) => { const m = { exports: {} }; new Function('module', 'self', 'globalThis', code)(m, undefined, {}); return m.exports; };
const SA0 = load(src);
// read-only hooks (each insertion must match exactly once)
const ins = (s, find, add, before) => { const k = s.split(find).length - 1; if (k !== 1) throw new Error('hook anchor x' + k + ': ' + find); return s.replace(find, before ? add + find : find + add); };
let isrc = src;
isrc = ins(isrc, 'if (dlt < bd) { bd = dlt; bj = j; bp = pr; }\n      }\n      return [bd, bj, bp, c];', 'if (o.__cand) o.__cand(c, j, dlt);\n        ', true);
isrc = ins(isrc, '    while (total < maxLines) {', '    if (o.__expose) o.__expose({ e, TL, C, inside, labOf, tau, covP, offs, pix, used, rowStart, lineD, cur, prev, n, w });\n', true);
isrc = ins(isrc, '      if (!pick) break;   // no line lowers the error', '      if (!pick && o.__dead) o.__dead();\n', true);
const SA1 = load(isrc);

const m = JSON.parse(fs.readFileSync(path.join(__dirname, 'einsteinloc-input.json')));
const page = JSON.parse(fs.readFileSync(path.join(__dirname, 'einsteinloc-page.json')));
const opts = (extra) => Object.assign({ frameMM: m.frameMM, wmap: null, maxLines: m.maxLines, minBlock: m.minBlock, switchPenalty: m.switchPenalty, detailW: m.detailW,
  detailEvery: m.detailEvery, hueW: m.hueW, toneK: m.toneK, hiW: m.hiW, centerW: m.centerW, fineW: m.fineW, fineS1: m.fineS1, fineS2: m.fineS2, fineEvery: m.fineEvery,
  detailCap: m.detailCap, refresh: m.refresh, reuseW: m.reuseW, reuseCell: m.reuseCell, edgeW: m.edgeW, stop: () => false }, extra || {});
const run = (SA, extra) => {
  const tb = SA.tableBytes(m.nails, m.nx, m.ny, m.edge, m.skip), lazy = tb > (m.tableMB || 256) * 1048576;
  const P = SA.prepare(m.nails, Int32Array.from(m.nx), Int32Array.from(m.ny), Uint8Array.from(m.edge), m.w, m.skip, null, lazy);
  const inside = SA.insideMask(m.shape, m.w, m.h);
  const t0 = process.hrtime.bigint();
  const r = SA.solveJoint(P, new Uint8ClampedArray(m.d), inside, m.threads, m.board, opts(extra));
  return { r, ms: Number(process.hrtime.bigint() - t0) / 1e6 };
};
// 1) pristine
const A = run(SA0); const order = Array.from(A.r.orders[0]);
const pageHash = page.info.hash, hashMatch = order.join(',') === pageHash;
console.log('pristine core md5', md5, '| lines', A.r.total, '| last nail', order[order.length - 1], '| order matches Maker page:', hashMatch, '| solver ms', Math.round(A.ms));
// 2) instrumented
let X = null, total = 0; const rms = [], cand = {}; let dead = null;
const stat = () => { let s = 0, c = 0; for (let i = 0; i < X.inside.length; i++) if (X.inside[i]) { s += X.e[0][i] ** 2; c++; } rms.push(Math.sqrt(s / c)); };
// plain lightness change if line (a,b) were added now: blend exactly as place() does, compare (L - L_target)^2 inside the circle
const q = [0, 0, 0];
const plainDelta = (a, b) => {
  const i0 = Math.min(a, b), j0 = Math.max(a, b), pr = X.rowStart[i0] + (j0 - i0 - 1);
  const s = X.offs[pr], t = X.offs[pr + 1]; if (s === t) return 0;
  const wv = X.covP[pr], tc = X.tau[0]; let d = 0;
  for (let k = s; k < t; k++) { const i = X.pix[k]; if (!X.inside[i]) continue;
    const C0 = X.C[0][i], C1 = X.C[1][i], C2 = X.C[2][i];
    X.labOf(C0 + wv * (tc[0] - C0), C1 + wv * (tc[1] - C1), C2 + wv * (tc[2] - C2), q);
    const eNew = q[0] - X.TL[0][i], eOld = X.e[0][i]; d += eNew * eNew - eOld * eOld; }
  return d;
};
const B = run(SA1, {
  __expose: (x) => { X = x; stat(); },
  __cand: (c, j, d) => { (cand[total] = cand[total] || { from: c, d: {} }).d[j] = d; },
  __dead: () => {
    const c = X.cur[0], n = X.n; let fromCur = 0, fromCurPlain = 0, fromCurN = 0, unused = 0, helpAny = 0, helpAnyPlain = 0, best = 0;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      const pr = X.rowStart[i] + (j - i - 1); if (X.offs[pr] === X.offs[pr + 1] || X.used[0][pr]) continue;
      unused++; const d = X.lineD(0, i, j, pr), dp = plainDelta(i, j);
      if (d < 0) helpAny++; if (dp < 0) helpAnyPlain++; if (d < best) best = d;
      if ((i === c || j === c) && (i !== X.prev[0] && j !== X.prev[0])) { fromCurN++; if (d < 0) fromCur++; if (dp < 0) fromCurPlain++; }
    }
    dead = { cur: c, prev: X.prev[0], linesFromCur: fromCurN, helpFromCurByScore: fromCur, helpFromCurByPlainLightness: fromCurPlain, unused, helpElsewhereByScore: helpAny - fromCur, helpAnywhereByPlainLightness: helpAnyPlain, bestScoreAnywhere: best };
  },
  stop: (tot) => { total = tot; stat(); return false; } });
const order2 = Array.from(B.r.orders[0]);
if (order2.join(',') !== order.join(',')) throw new Error('instrumented order differs from pristine');
console.log('instrumented order identical to pristine: true | dead end', JSON.stringify(dead));
fs.writeFileSync(path.join(__dirname, 'trace-loc.json'), JSON.stringify({ commit: '209877cbecb0a351b38da0a4d9dd42d4c57df96d', coreMd5: md5, photo: 'Albert_Einstein_1947.jpg (LoC LC-USZ62-60242, cph.3b46036)',
  pageStatus: page.status, hashMatch, solverMs: A.ms, n: m.nails, skip: m.skip, w: m.w, h: m.h, maxLines: m.maxLines, frameMM: m.frameMM, A: m.A, nx: m.nx, ny: m.ny, layout: (() => { const L = SA0.nailLayout(m.shape, m.nails, m.A); return { u: Array.from(L.u || L.U || []), v: Array.from(L.v || L.V || []), keys: Object.keys(L) }; })(), order, rms, cand, dead }));
console.log('wrote trace-loc.json');
