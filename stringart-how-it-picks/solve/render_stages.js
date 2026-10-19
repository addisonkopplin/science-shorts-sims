// Renders the LoC-scan order with the Maker's own SA.render (pinned core) at several line counts,
// for judging by eye when the face appears and for the first-10-lines check. Writes stages.raw + stages.json.
// Run: node render_stages.js   (then python3 ../extract.py makes build_stages.png / first10.png)
const fs = require('fs'), path = require('path');
const m0 = { exports: {} }; new Function('module', 'self', 'globalThis', fs.readFileSync(path.join(__dirname, 'core-209877c.js'), 'utf8'))(m0, undefined, {});
const SA = m0.exports, T = JSON.parse(fs.readFileSync(path.join(__dirname, 'trace-loc.json')));
const inp = JSON.parse(fs.readFileSync(path.join(__dirname, 'einsteinloc-input.json')));
const S = 560, at = [10, 100, 300, 500, 800, 1200, T.order.length - 1];
const lay = SA.nailLayout(inp.shape, inp.nails, inp.A);
const fd = fs.openSync(path.join(__dirname, 'stages.raw'), 'w');
SA.render(S, S, lay, [Uint16Array.from(T.order)], [T.order.length - 1], inp.threads, inp.board, 0, inp.frameMM, [[0, 0, T.order.length - 1]], null,
  { at, fn: (i, [R]) => fs.writeSync(fd, Buffer.from(Uint8Array.from(R))) });
fs.closeSync(fd); fs.writeFileSync(path.join(__dirname, 'stages.json'), JSON.stringify({ S, at }));
console.log('rendered', at.join(','));
