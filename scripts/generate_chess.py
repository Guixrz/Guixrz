#!/usr/bin/env python3
"""
Gera dist/chess.svg: suas contribuições recentes viram um tabuleiro de xadrez,
as peças fazem a combinação  1.Qa8+!! Kxa8  2.Nxb6+ Kb8  3.Nd7#,
o rei preto explode e tudo volta a ser quadradinhos. O ciclo se repete.

Uso:
  GITHUB_USER=seu_usuario GITHUB_TOKEN=xxx python scripts/generate_chess.py
  python scripts/generate_chess.py --frame 22.3 teste.svg   (imagem estática de um instante, p/ testes)
"""
import os, sys, json, math, random, urllib.request

# ---------------------------------------------------------------- layout
W, H = 840, 260
T = 36.0                      # duração do ciclo (segundos)
CELL, PITCH, COLS = 12, 15, 52
GX = (W - (COLS * PITCH - 3)) / 2
GY = (H - (7 * PITCH - 3)) / 2
SQ = 26
BX, BY = (W - 8 * SQ) / 2, (H - 8 * SQ) / 2
MID0 = 22                     # primeira coluna (de 0..51) que vira tabuleiro
S0 = CELL / SQ                # escala do quadrado quando ainda é "quadradinho"
LV = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']   # tema escuro do GitHub
LIGHT, DARK = '#a7d8a0', '#2e7d46'

# ---------------------------------------------------------------- dados
def fetch_levels(user, token):
    """Retorna matriz [semana][dia] com níveis 0..4 das últimas 52 semanas."""
    counts = None
    try:
        q = ('query($l:String!){user(login:$l){contributionsCollection{contributionCalendar'
             '{weeks{contributionDays{contributionCount weekday}}}}}}')
        req = urllib.request.Request(
            'https://api.github.com/graphql',
            data=json.dumps({'query': q, 'variables': {'l': user}}).encode(),
            headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json',
                     'User-Agent': 'chess-profile'})
        weeks = json.load(urllib.request.urlopen(req, timeout=30))['data']['user'][
            'contributionsCollection']['contributionCalendar']['weeks'][-COLS:]
        counts = [[0] * 7 for _ in range(COLS)]
        off = COLS - len(weeks)
        for wi, w in enumerate(weeks):
            for d in w['contributionDays']:
                counts[off + wi][d['weekday']] = d['contributionCount']
    except Exception as e:
        print('Aviso: não consegui ler as contribuições, usando dados de exemplo:', e)
        rnd = random.Random(3)
        counts = [[rnd.choice([0, 0, 0, 1, 2, 3, 5, 8]) for _ in range(7)] for _ in range(COLS)]
    mx = max(1, max(max(c) for c in counts))
    return [[0 if c == 0 else min(4, math.ceil(c / mx * 4)) for c in col] for col in counts]

# ---------------------------------------------------------------- peças
def glyph(kind, white):
    f, s = ('#f5f5f5', '#111') if white else ('#1a1a1a', '#e6e6e6')
    a = f'fill="{f}" stroke="{s}" stroke-width="1.1" stroke-linejoin="round" stroke-linecap="round"'
    g = {
     'P': f'<circle cx="13" cy="8" r="4.2" {a}/><path d="M8.5 21Q9 14 13 12.5Q17 14 17.5 21Z" {a}/><rect x="7" y="21" width="12" height="3" rx="1" {a}/>',
     'R': f'<path d="M7.5 10V5h2.8v2h1.5V5h2.4v2h1.5V5h2.8v5z" {a}/><path d="M8.5 21 9.5 10h7l1 11z" {a}/><rect x="6.5" y="21" width="13" height="3" rx="1" {a}/>',
     'N': f'<path d="M7.5 22C8 17 8.5 13.5 11.5 11C10 10.2 8.5 10.3 6.5 12.3L5.5 11C7 8 9.5 6 12 5L13 3.5L14.6 5C18.5 5.7 20.5 10 20 15.5L19.5 22Z" {a}/><circle cx="13.5" cy="8.3" r="1" fill="{s}"/><rect x="6.5" y="21" width="13.5" height="3" rx="1" {a}/>',
     'B': f'<path d="M13 3.5C16 6 17.2 8.6 17.2 11C17.2 13 15.5 14.4 15 15.5H17.5L18 21H8L8.5 15.5H11C10.5 14.4 8.8 13 8.8 11C8.8 8.6 10 6 13 3.5Z" {a}/><path d="M11.2 9.5h3.6M13 7.7v3.6" stroke="{s}" stroke-width="1" fill="none"/><rect x="6.5" y="21" width="13" height="3" rx="1" {a}/>',
     'Q': f'<path d="M5 9L8.5 17L10 8L13 16L16 8L17.5 17L21 9L19.5 21H6.5Z" {a}/><circle cx="5" cy="8" r="1.6" {a}/><circle cx="10" cy="6.6" r="1.6" {a}/><circle cx="13" cy="5.6" r="1.6" {a}/><circle cx="16" cy="6.6" r="1.6" {a}/><circle cx="21" cy="8" r="1.6" {a}/><rect x="6" y="21" width="14" height="3" rx="1" {a}/>',
     'K': f'<path d="M13 2.5V8M10.5 5H15.5" stroke="{s}" stroke-width="1.6" fill="none" stroke-linecap="round"/><path d="M7.5 14Q13 8.5 18.5 14Z" {a}/><path d="M8 21L9 13.5H17L18 21Z" {a}/><rect x="6.5" y="21" width="13" height="3" rx="1" {a}/>',
    }
    return g[kind]

def sq(col, row): return (BX + col * SQ, BY + row * SQ)
def cell_xy(c, r): return (GX + c * PITCH, GY + r * PITCH)

# ---------------------------------------------------------------- roteiro
# (id, tipo, branca?, casa inicial (col,row), movimentos [(t0,t1,destino)], some_em)
T_IN = 8.7
END_SHRINK = (25.2, 25.8)
pieces_def = [
 # brancas
 ('wQ','Q',1,(2,2),[(12.0,13.0,(0,0))],(15.15,15.4)),     # Dc6 -> a8+!!  (capturada pelo rei)
 ('wK','K',1,(1,7),[],None),
 ('wN','N',1,(3,3),[(16.4,17.4,(1,2)),(20.4,21.4,(3,0))],None),  # Cxb6+ , Cd7#
 ('wB','B',1,(6,6),[],None),
 ('wR','R',1,(7,7),[],None),
 ('wp1','P',1,(0,6),[],None), ('wp2','P',1,(1,6),[],None),
 ('wp3','P',1,(2,6),[],None), ('wp4','P',1,(7,6),[],None),
 # pretas
 ('bK','K',0,(1,0),[(14.6,15.4,(0,0)),(18.5,19.3,(1,0))],(22.0,22.15)),  # explode
 ('bR1','R',0,(2,0),[],None), ('bR2','R',0,(4,0),[],None),
 ('bB','B',0,(5,2),[],None), ('bQ','Q',0,(4,6),[],None),
 ('bp1','P',0,(0,1),[],None), ('bp2','P',0,(2,1),[],None),
 ('bp3','P',0,(6,1),[],None), ('bp4','P',0,(7,1),[],None),
 ('bp5','P',0,(1,2),[],(17.25,17.5)),                    # peão b6 capturado
]
HL = [  # destaques vermelhos (xeque / xeque duplo / mate)
 ('h1',(1,0),13.0,14.5), ('h2',(0,0),17.4,18.4), ('h3',(1,0),21.4,22.1),
]
BADGE = (13.0, 14.6)
BOOM_T = 22.0
SHARDS = []
_r = random.Random(5)
for k in range(16):
    a = k / 16 * 2 * math.pi + _r.uniform(-.2, .2); d = _r.uniform(22, 46)
    SHARDS.append((math.cos(a) * d, math.sin(a) * d, _r.choice(['#ff9f1c', '#ffd166', '#ff4d4d', '#ffffff']), _r.uniform(1.6, 3.2)))
TA, TR = 6.5, 26.2          # início da transformação / início da volta

# ---------------------------------------------------------------- animação
def smooth(u): return u * u * (3 - 2 * u)
def val(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else smooth((t - t0) / (t1 - t0))
            return {k: a[k] + (b[k] - a[k]) * u for k in a}
    return keys[-1][1]

def pct(t): return f'{t / T * 100:.3f}%'
def keyframes(name, keys, css):
    out, last = [], -1
    for t, p in keys:
        t = max(0, min(T, t))
        if out and t <= last: t = last + 0.004
        last = t
        out.append(f'{pct(t)}{{{css(p)}}}')
    return f'@keyframes {name}{{{"".join(out)}}}'

def op_keys(spans, fade=0.15):
    """spans: lista de (inicio, fim, opacidade); fora delas = 0."""
    k = [(0, {'o': 0})]
    for a, b, o in spans:
        k += [(a, {'o': 0}), (a + fade, {'o': o}), (b - fade, {'o': o}), (b, {'o': 0})]
    return k + [(T, {'o': 0})]

# ---------------------------------------------------------------- construção
def build(levels, frame=None):
    static = frame is not None
    css, body = [], []
    A = lambda name, keys, cssfn, extra='': css.append(keyframes(name, keys, cssfn) + f'.{name}{{animation:{name} {T}s infinite ease-in-out;{extra}}}')

    body.append(f'<rect width="{W}" height="{H}" rx="14" fill="#0d1117"/>')

    # --- quadradinhos
    for c in range(COLS):
        for r in range(7):
            x, y = cell_xy(c, r)
            mid = MID0 <= c < MID0 + 8
            cls, op = '', ''
            if mid:
                i = c - MID0; d = i * 0.06
                keys = [(0, {'o': 1}), (TA + d - .02, {'o': 1}), (TA + d, {'o': 0}), (TR + 1.6 + d, {'o': 0}), (TR + 1.62 + d, {'o': 1}), (T, {'o': 1})]
                if static: op = f' opacity="{val(keys, frame)["o"]:.2f}"'
                elif (r == 0) and f'ch{i}' not in ''.join(css): A(f'ch{i}', keys, lambda p: f'opacity:{p["o"]:.2f}')
                if not static: cls = f' class="ch{i}"'
            body.append(f'<rect{cls} x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{LV[levels[c][r]]}"{op}/>')

    # --- tabuleiro (cada quadrado nasce de um quadradinho do meio)
    for j in range(8):
        for i in range(8):
            x, y = sq(i, j); cr = min(j, 6)
            cx0, cy0 = cell_xy(MID0 + i, cr); cx0 += CELL / 2; cy0 += CELL / 2
            dx, dy = cx0 - (x + SQ / 2), cy0 - (y + SQ / 2)
            c0 = LV[levels[MID0 + i][cr]]; c1 = LIGHT if (i + j) % 2 == 0 else DARK
            d = i * 0.06
            keys = [(0, {'p': 0, 'o': 0}), (TA + d - .05, {'p': 0, 'o': 0}), (TA + d, {'p': 0, 'o': 1}),
                    (TA + d + 1.7, {'p': 1, 'o': 1}), (TR + d, {'p': 1, 'o': 1}),
                    (TR + d + 1.6, {'p': 0, 'o': 1}), (TR + d + 1.65, {'p': 0, 'o': 0}), (T, {'p': 0, 'o': 0})]
            if static:
                v = val(keys, frame)
                if v['o'] < .02: continue
                s = S0 + (1 - S0) * v['p']
                px, py = dx * (1 - v['p']), dy * (1 - v['p'])
                col = c1 if v['p'] > .5 else c0
                body.append(f'<rect transform="translate({x + SQ/2 + px:.2f} {y + SQ/2 + py:.2f}) scale({s:.3f}) translate({-SQ/2} {-SQ/2})" width="{SQ}" height="{SQ}" rx="4" fill="{col}"/>')
            else:
                if j == 0 and f'bq{i}' not in ''.join(css):
                    def f(p, _=0):
                        if p['p'] == 1: return f'opacity:{p["o"]};transform:translate(0,0) scale(1);fill:var(--c1)'
                        return f'opacity:{p["o"]};transform:translate(var(--dx),var(--dy)) scale({S0:.4f});fill:var(--c0)'
                    A(f'bq{i}', keys, f, 'transform-box:fill-box;transform-origin:50% 50%;')
                body.append(f'<rect class="bq{i}" x="{x:.1f}" y="{y:.1f}" width="{SQ}" height="{SQ}" rx="4" style="--dx:{dx:.2f}px;--dy:{dy:.2f}px;--c0:{c0};--c1:{c1}" fill="{c1}" opacity="0"/>')

    # --- destaques de xeque
    for hid, (c, r), a, b in HL:
        x, y = sq(c, r); keys = op_keys([(a, b, .6)])
        if static: o = val(keys, frame)['o']; o > .01 and body.append(f'<rect x="{x}" y="{y}" width="{SQ}" height="{SQ}" fill="#ff3b3b" opacity="{o:.2f}"/>')
        else:
            A(hid, keys, lambda p: f'opacity:{p["o"]}'); body.append(f'<rect class="{hid}" x="{x}" y="{y}" width="{SQ}" height="{SQ}" fill="#ff3b3b" opacity="0"/>')

    # --- peças
    for pid, kind, white, start, moves, gone in pieces_def:
        pos = [(0, {'x': sq(*start)[0], 'y': sq(*start)[1]})]; cur = start
        for t0, t1, dest in moves:
            pos += [(t0, {'x': sq(*cur)[0], 'y': sq(*cur)[1]}), (t1, {'x': sq(*dest)[0], 'y': sq(*dest)[1]})]; cur = dest
        pos.append((T, pos[-1][1]))
        idx = [p[0] for p in pieces_def].index(pid); tin = T_IN + idx * 0.12
        ge = gone or END_SHRINK
        scl = [(0, {'s': 0}), (tin, {'s': 0}), (tin + .35, {'s': 1.15}), (tin + .5, {'s': 1}),
               (ge[0], {'s': 1}), (ge[1], {'s': 0}), (T, {'s': 0})]
        g = glyph(kind, white)
        if static:
            p = val(pos, frame); s = val(scl, frame)['s']
            if s < .01: continue
            body.append(f'<g transform="translate({p["x"]:.2f} {p["y"]:.2f})"><g transform="translate(13 13) scale({s:.3f}) translate(-13 -13)">{g}</g></g>')
        else:
            A(pid + 'o', pos, lambda p: f'transform:translate({p["x"]:.1f}px,{p["y"]:.1f}px)')
            A(pid + 'i', scl, lambda p: f'transform:scale({p["s"]:.3f})', 'transform-box:fill-box;transform-origin:50% 50%;')
            body.append(f'<g class="{pid}o"><g class="{pid}i"><rect width="{SQ}" height="{SQ}" fill="none"/>{g}</g></g>')

    # --- selo "!!" (lance brilhante)
    bx, by = BX + SQ - 3, BY + 3
    keys = op_keys([BADGE + (1,)])
    badge = (f'<circle cx="{bx}" cy="{by}" r="7.5" fill="#26c6b0"/>'
             f'<text x="{bx}" y="{by + 3.2}" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="10" fill="#fff" text-anchor="middle">!!</text>')
    if static:
        o = val(keys, frame)['o']; o > .01 and body.append(f'<g opacity="{o:.2f}">{badge}</g>')
    else:
        A('badge', keys, lambda p: f'opacity:{p["o"]}'); body.append(f'<g class="badge" opacity="0">{badge}</g>')

    # --- explosão do rei
    ex, ey = sq(1, 0); ex += SQ / 2; ey += SQ / 2
    if static:
        u = (frame - BOOM_T) / 1.0
        if 0 <= u <= 1:
            body.append(f'<circle cx="{ex}" cy="{ey}" r="{8 + 26*u:.1f}" fill="#fff" opacity="{max(0, .9 - u*1.4):.2f}"/>')
            for dx, dy, col, r in SHARDS:
                body.append(f'<circle cx="{ex + dx*u:.1f}" cy="{ey + dy*u:.1f}" r="{r*(1.2-u*.7):.1f}" fill="{col}" opacity="{1-u:.2f}"/>')
    else:
        a, b = BOOM_T, BOOM_T + 1.0
        css.append(f'@keyframes flash{{0%,{pct(a-.01)}{{opacity:0;transform:scale(.3)}}{pct(a+.05)}{{opacity:.95;transform:scale(.8)}}{pct(a+.4)}{{opacity:0;transform:scale(3)}}100%{{opacity:0;transform:scale(3)}}}}'
                   f'.flash{{animation:flash {T}s infinite ease-out;transform-box:fill-box;transform-origin:50% 50%}}'
                   f'@keyframes shard{{0%,{pct(a-.01)}{{opacity:0;transform:translate(0,0) scale(.4)}}{pct(a+.03)}{{opacity:1;transform:translate(0,0) scale(1.2)}}{pct(b)}{{opacity:0;transform:translate(var(--ex),var(--ey)) scale(.5)}}100%{{opacity:0;transform:translate(var(--ex),var(--ey)) scale(.5)}}}}'
                   f'.shard{{animation:shard {T}s infinite ease-out;transform-box:fill-box;transform-origin:50% 50%}}')
        body.append(f'<circle class="flash" cx="{ex}" cy="{ey}" r="9" fill="#fff" opacity="0"/>')
        for dx, dy, col, r in SHARDS:
            body.append(f'<circle class="shard" cx="{ex}" cy="{ey}" r="{r:.1f}" fill="{col}" opacity="0" style="--ex:{dx:.1f}px;--ey:{dy:.1f}px"/>')

    style = f'<style>{"".join(css)}</style>' if not static else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
            f'aria-label="Xadrez feito com as contribuições recentes">{style}{"".join(body)}</svg>')

# ---------------------------------------------------------------- main
if __name__ == '__main__':
    args = sys.argv[1:]
    frame = None
    if args[:1] == ['--frame']: frame, args = float(args[1]), args[2:]
    out = args[0] if args else 'dist/chess.svg'
    levels = fetch_levels(os.environ.get('GITHUB_USER', ''), os.environ.get('GITHUB_TOKEN', ''))
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'w', encoding='utf-8').write(build(levels, frame))
    print('gerado:', out)
