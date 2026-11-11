export const W = 32;
export const H = 32;
export const PALETTE: Record<string, string> = {
  k: "#2a1b33", h: "#ff8ab8", d: "#d9578f", H: "#ffd0e4", s: "#ffe5d4",
  S: "#f4bfa6", e: "#3b2352", i: "#8b5cf6", I: "#c9b8ff", w: "#ffffff",
  b: "#ff9db3", m: "#a8324f", M: "#ff7f9c", r: "#ff4d6d", R: "#c9184a",
  y: "#ffd166", c: "#5b8def", C: "#3d63b8", o: "#5a3550", z: "#ffffff",
  B: "#8ecdf7", g: "#d4d6e2", G: "#6e7088", n: "#7fe0ff",
};
const BASE = [
  "................................", "............hhhhhhhh............", "..........hhhhHHhhhhhh..........",
  ".........hhhHHhhhhhhhhh.........", "....rr..hhHHhhhhhhhhhhhh..rr....", "...rRrr.hHhhhhhhhhhhhhhh.rrRr...",
  "...rrRrhhhhhhhhhhhhhhhhhhrRrr...", "....rrhhhhhhhhhhhhhhhhhhhhrr....", "..hhhdhhhhhhhhhhhhh hhhhyyhdhhh..".replace(" ", ""),
  "..hhhdhhhhdhhhhdhhhhdhhyyhdhhh..", "..hhhdhhdhhdssdhhdssdhhdhhdhhh..", "..hhhdhhsssssssssssssssshhdhhh..",
  "..hhhdhhsssssssssssssssshhdhhh..", "..hhhdhhsssssssssssssssshhdhhh..", "..hhhdhhsssssssssssssssshhdhhh..",
  ".hhhd.hhsssssssssssssssshh.dhhh.", ".hhhd.hhhsssssssssssssshhh.dhhh.", ".hhd..hhh.SssssssssssS.hhh..dhh.",
  ".hhd..hh......ssss......hh..dhh.", ".hhd......wwwwwrrwwwww......dhh.", ".hhd....cccwwwrRRrwwwccc....dhh.",
  ".hd.....cCccwwwrrwwwccCc.....dh.", "..h.....cCcccccrrcccccCc.....h..", "........ssCccccccccccCss........",
  ".........ccCcccCCcccCcc.........", "........ccCcccCccCcccCcc........", "........CCCCCCCCCCCCCCCC........",
  "............ss....ss............", "............ss....ss............", "............ww....ww............",
  "...........ooo....ooo...........", "................................",
];
type Grid = string[][];
type Options = { eyes?: string; mouth?: string; blush?: boolean; legs?: string; arms?: string; bob?: number; look?: number; sit?: boolean };
export const EYES: Record<string, { L: string[]; R?: string[] }> = {
  open: { L: ["eee", "wii", "iii", "iIi"] }, closed: { L: ["sss", "sss", "eee", "sss"] },
  happy: { L: ["sss", "ses", "ese", "sss"] }, wide: { L: ["eee", "ewe", "eie", "eee"] },
  sad: { L: ["see", "eii", "wii", "iIi"], R: ["ees", "iie", "iiw", "iIi"] },
  angry: { L: ["ess", "eee", "wii", "iIi"], R: ["sse", "eee", "iiw", "iIi"] },
  half: { L: ["sss", "eee", "wii", "iIi"] }, heart: { L: ["rsr", "rrr", "rrr", "srs"] },
  up: { L: ["eee", "iwi", "iii", "sss"] }, sleep: { L: ["sss", "sss", "ese", "ses"] },
  wink: { L: ["eee", "wii", "iii", "iIi"], R: ["sss", "ses", "ese", "sss"] },
};
export const MOUTHS: Record<string, string[]> = {
  smile: ["mssm", "smms"], small: ["ssss", "smms"], open: ["smms", "sMMs"],
  talk: ["smms", "smms"], o: ["smms", "smms"], frown: ["ssss", "mssm"],
  flat: ["ssss", "smms"], smirk: ["ssss", "ssmm"], wavy: ["ssss", "msms"], grin: ["mmmm", "sMMs"],
};
const LEGS: Record<string, string[]> = {
  stand: ["............ss....ss............", "............ss....ss............", "............ww....ww............", "...........ooo....ooo..........."],
  walkA: ["............ss....ss............", "............ww....ss............", "...........ooo....ww............", "..................ooo..........."],
  walkB: ["............ss....ss............", "............ss....ww............", "............ww....ooo............", "...........ooo.................."],
  dangle: ["............ss....ss............", "...........ss......ss...........", "...........ww......ww...........", "..........oo........oo.........."],
  sit: ["................................", "................................", "................................", "..........oooo....oooo.........."],
};
const ARMS: Record<string, [number, number, string][]> = {
  down: [], wave: [[22, 21, "."], [23, 21, "."], [22, 22, "."], [23, 22, "."], [22, 23, "."], [23, 23, "."],
    [24, 20, "c"], [24, 19, "c"], [25, 19, "C"], [25, 18, "c"], [25, 17, "s"], [26, 17, "s"], [25, 16, "s"], [26, 16, "s"]],
};
ARMS.up = ARMS.wave.concat(ARMS.wave.map(([x, y, ch]) => [W - 1 - x, y, ch] as [number, number, string]));
export const EFFECTS: Record<string, string[]> = {
  z: ["zzz", "..z", ".z.", "z..", "zzz"], heart: [".r.r.", "rrrrr", "rrrrr", ".rrr.", "..r.."],
  excl: ["r", "r", "r", ".", "r"], quest: [".zz.", "z..z", "..z.", "....", "..z."],
  anger: ["rr.rr", "r...r", ".....", "r...r", "rr.rr"], note: ["..zz", "..zz", "..z.", "zzz.", "zz.."],
  sweat: [".B.", "BBB", "BBB", ".B."], sparkle: [".y.", "yyy", ".y."], tear: ["B", "B"],
  laptop: [".GGGGGGGGGG.", ".GggggggggG.", ".GgggnngggG.", ".GggggggggG.", "GGGGGGGGGGGG", ".gggggggggg."],
  cloud: ["..zzzz...", ".zzzzzzz.", "zzzzzzzzz", ".zzzzzzz.", "...zz....", ".z......."],
  mag: [".GGG..", "GnnnG.", "GnwnG.", "GnnnG.", ".GGG..", "....o.", ".....o."],
  mail: ["wwwwwww", "wrwwwrw", "wwrwrww", "wwwrwww", "wwwwwww"],
  gear: [".G.G.", "GGGGG", ".GwG.", "GGGGG", ".G.G."],
  gear2: ["G.G.G", ".GGG.", "GGwGG", ".GGG.", "G.G.G"],
  book: ["rrrrrr", "rwwwwr", "rweewr", "rwwwwr", "rrrrrr"],
};
export const EXPRESSIONS: Record<string, { eyes: string; mouth: string; blush?: boolean; effect?: string }> = {
  neutral: { eyes: "open", mouth: "smile" }, happy: { eyes: "happy", mouth: "grin", blush: true, effect: "note" },
  sad: { eyes: "sad", mouth: "frown", effect: "tear" }, thinking: { eyes: "up", mouth: "flat", effect: "quest" },
  surprised: { eyes: "wide", mouth: "o", effect: "excl" }, angry: { eyes: "angry", mouth: "frown", effect: "anger" },
  shy: { eyes: "half", mouth: "wavy", blush: true, effect: "sweat" }, love: { eyes: "heart", mouth: "smile", blush: true, effect: "heart" },
  sleepy: { eyes: "half", mouth: "small", effect: "z" }, smug: { eyes: "half", mouth: "smirk", effect: "sparkle" },
};
function put(g: Grid, x: number, y: number, ch: string) { if (g[y]?.[x] !== undefined) g[y][x] = ch; }
function outline(g: Grid): Grid {
  const out = g.map((row) => [...row]);
  for (let y = 0; y < g.length; y++) for (let x = 0; x < g[0].length; x++) {
    if (g[y][x] !== ".") continue;
    if ([[-1, 0], [1, 0], [0, -1], [0, 1]].some(([dy, dx]) => g[y + dy]?.[x + dx] && g[y + dy][x + dx] !== "." && g[y + dy][x + dx] !== "k")) out[y][x] = "k";
  }
  return out;
}
function stamp(g: Grid, rows: string[], ox: number, oy: number) {
  rows.forEach((row, dy) => [...row].forEach((ch, dx) => { if (ch !== "_") put(g, ox + dx, oy + dy, ch); }));
}
function shiftDown(g: Grid, last: number, dy: number) {
  for (let y = last; y >= 0; y--) for (let x = 0; x < W; x++) g[y][x] = y - dy >= 0 ? g[y - dy][x] : ".";
}
export function compose(options: Options = {}): Grid {
  const o = { eyes: "open", mouth: "smile", blush: false, legs: "stand", arms: "down", bob: 0, look: 0, sit: false, ...options };
  const g = BASE.map((row) => [...row]); const eyes = EYES[o.eyes] || EYES.open; const look = Math.max(-1, Math.min(1, o.look || 0));
  stamp(g, eyes.L, 10 + look, 11); stamp(g, eyes.R || eyes.L, 19 + look, 11); stamp(g, MOUTHS[o.mouth] || MOUTHS.smile, 14, 15);
  if (o.blush) [[9, 15], [10, 15], [21, 15], [22, 15]].forEach(([x, y]) => put(g, x, y, "b"));
  stamp(g, LEGS[o.sit ? "sit" : o.legs] || LEGS.stand, 0, 27); ARMS[o.arms]?.forEach(([x, y, ch]) => put(g, x, y, ch));
  if (o.sit) shiftDown(g, 29, 3); if (o.bob) shiftDown(g, o.sit ? 29 : 26, o.bob); return outline(g);
}
export function effectGrid(name: string): Grid {
  const rows = EFFECTS[name] || []; const width = (rows[0]?.length || 0) + 2;
  return outline([Array(width).fill("."), ...rows.map((row) => [".", ...row, "."]), Array(width).fill(".")]);
}
export function draw(ctx: CanvasRenderingContext2D, g: Grid, ox: number, oy: number, scale: number) {
  g.forEach((row, y) => row.forEach((ch, x) => { if (ch !== ".") { ctx.fillStyle = PALETTE[ch] || "#ff00ff"; ctx.fillRect((ox + x) * scale, (oy + y) * scale, scale, scale); } }));
}
