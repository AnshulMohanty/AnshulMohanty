"""
Builds every figure in assets/ except the contribution plinth (scripts/contributions.py
redraws that one every day). Run from the repository root:  python3 scripts/build.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hairline import _runs as hl_runs
from hairline import (Doc, Track, EASE, fit, box_pts, rrect, circle, prism, solid, flat, path, hull, THEMES,
                      base_front, tr, n, wrap, measure)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
W = 840
STAGGER = 0.035  # rule 02: delay = |i - a| x step


def falloff(d):
    return [1.0, 0.42, 0.16, 0.07][d] if d < 4 else 0.0


def lit_track(doc, rest_on, choices, T, on_color, off_color):
    """Stroke for one part: bright when chosen, at rest only if it is the rest mark."""
    t = Track(on_color if rest_on else off_color)
    for when, on in choices:
        t.step(when, on_color if on else off_color)
    return doc.animate(t, T, lambda v: "stroke:%s" % v)


def readouts(doc, x, y, items, T, anchor="end", size=12):
    """items: list of (start, end, text); items[0] is the rest text, shown outside the others' windows.
    Hand-overs are sequential: the outgoing text fades first, the incoming one follows."""
    OUT, IN, GAP = 0.14, 0.18, 0.1
    out = []
    t = Track(1)
    for s_, e_, _ in items[1:]:
        t.step(s_, 0, fade=OUT)
        t.step(e_ + GAP, 1, fade=IN)
    cls = doc.animate(t, T, lambda v: "opacity:%s" % n(v))
    out.append(doc.text(x, y, items[0][2], "pm", size, "ink3", anchor, cls=cls))
    for s_, e_, txt in items[1:]:
        t = Track(0)
        t.step(s_ + GAP, 1, fade=IN)
        t.step(e_, 0, fade=OUT)
        cls = doc.animate(t, T, lambda v: "opacity:%s" % n(v))
        out.append(doc.text(x, y, txt, "pm", size, "ink3", anchor, cls=cls, opacity=0))
    return "".join(out)


def windows(doc, x, y, texts, T, static, anchor="end", size=12):
    """texts: list of (text, [(start, end), ...]) with visibility windows that may wrap the loop.
    `static` is the index shown when nothing animates."""
    OUT, IN, GAP = 0.14, 0.18, 0.1
    out = []
    for i, (txt, wins) in enumerate(texts):
        on0 = any(s_ <= 0 for s_, _ in wins)
        to_end = any(e_ >= T for _, e_ in wins)
        t = Track(1 if on0 else 0)
        for s_, e_ in sorted(wins):
            if s_ > 0:
                t.step(s_ + GAP, 1, fade=IN)
            if e_ < T:
                t.step(e_, 0, fade=OUT)
            elif not on0:                       # hand over to the text that opens the loop
                t.step(T - 0.4, 0, fade=OUT)
        if on0 and not to_end:                  # fade back in just before the loop restarts
            t.step(T - 0.2, 1, fade=IN)
        cls = doc.animate(t, T, lambda v: "opacity:%s" % n(v))
        out.append(doc.text(x, y, txt, "pm", size, "ink3", anchor, cls=cls, opacity=1 if i == static else 0))
    return "".join(out)


# ============================================================================ hero

GLYPHS = {
    # small hairline icons, drawn around (0, 0) in a radius of about 9
    "voice": lambda: "".join('<path class="mk" d="M%s %sV%s"/>' % (n(-8 + i * 2.7), n(-h / 2), n(h / 2))
                             for i, h in enumerate([3, 7, 12, 6, 10, 5, 2.5])),
    "layers": lambda: "".join('<path class="g-fill" d="M0 %sL9 %sL0 %sL-9 %sZ"/>' % (n(-8 + o), n(-3.5 + o), n(1 + o), n(-3.5 + o))
                              for o in (7, 3.5, 0)),
    "graph": lambda: ('<circle class="mk" r="8.5" stroke-dasharray="2 2"/><circle class="g-fill" r="2.2"/>' +
                      "".join('<path class="mk" d="M0 0L%s %s"/><circle class="g-fill" cx="%s" cy="%s" r="1.8"/>' % (
                          n(8.5 * math.cos(a)), n(8.5 * math.sin(a)), n(8.5 * math.cos(a)), n(8.5 * math.sin(a)))
                          for a in (-1.2, 0.9, 2.6))),
    "shuttle": lambda: ('<path class="mk" d="M-2.2 3.4L-6.5 -7M2.2 3.4L6.5 -7M0 3.4V-8.4M-3.4 -2H3.4"/>'
                        '<ellipse class="mk" cx="0" cy="-7.4" rx="6.5" ry="1.9"/><circle class="g-fill" cx="0" cy="5.6" r="2.6"/>'),
    "reel": lambda: ('<circle class="mk" r="8.8"/><circle class="mk" r="1.4"/>' +
                     "".join('<circle class="mk" cx="%s" cy="%s" r="2.1"/>' % (n(4.8 * math.cos(a)), n(4.8 * math.sin(a)))
                             for a in (0.4, 2.0, 3.6, 5.2))),
    "belt": lambda: ('<path class="mk" d="M-10 -2.5H10M-10 1.5H10"/><rect class="g-fill" x="-3.2" y="-4.2" width="6.4" height="7.4" rx="1.6"/>'
                     '<path class="mk" d="M-1.5 3.2L-5 10M1.5 3.2L5.5 9.6M3.6 5.6L6 4.7M4.4 7.4L6.8 6.5"/>'),
}


def hero(theme):
    """Name and a rotating line on the left. On the right, an orbit system: the builds circle a
    chip engraved AM on the inner ring, the rest of life on the outer ring, counter-rotating.
    Whatever swings to the front lights up, a beam fires from the core, and the caption names it."""
    H = 342
    lines = ["Builds retrieval that cites chapter and verse.",
             "Ships full-stack TypeScript, from crown to cellar.",
             "Second dan black belt. Breaks boards, never builds.",
             "Plays for the state. Every smash returned with interest.",
             "Watches every genre. Stays for the post-credits scene."]
    doc = Doc(W, H, theme, "Anshul Mohanty",
              "Anshul Mohanty. " + " ".join(lines) + " An orbit of his builds (Voice RAG, Saakshi, CodeFlow) and "
              "his pursuits (badminton, films, karate) around a chip engraved AM.", "h")
    th = doc.th
    doc.add(doc.text(-3, 80, "Anshul", "psb", 80, "ink", tracking=-0.035))
    doc.add(doc.text(-3, 164, "Mohanty", "psb", 80, "ink", tracking=-0.035))

    # ---- one line, many sides: each slides up and out, the next slides in
    LT = 2.8
    T = LT * len(lines)
    ly = 218
    cid = doc.uid()
    doc.defs.append('<clipPath id="%s"><rect x="0" y="%s" width="530" height="34"/></clipPath>' % (cid, ly - 25))
    doc.add('<rect x="1" y="%s" width="3" height="20" rx="1.5" fill="%s"/>' % (ly - 16, th["hi"]))
    out = []
    for i, txt in enumerate(lines):
        t0 = i * LT
        tk = Track((0, 30 if i else 0))
        if i:
            tk.to(t0 - 0.4, (0, 0), dur=0.45, ease="cubic-bezier(.25,1,.5,1)")
        tk.to(t0 + LT - 0.45, (0, -30), dur=0.45, ease="cubic-bezier(.5,0,.75,0)")
        if t0 + LT + 0.02 < T - 0.05:
            tk.step(t0 + LT + 0.02, (0, 30), fade=0)
        if i == 0:
            tk.to(T - 0.45, (0, 0), dur=0.45, ease="cubic-bezier(.25,1,.5,1)")
        cls = doc.animate(tk, T, tr, wrap=(i == len(lines) - 1))
        rest = "" if i == 0 else ' transform="translate(0 30)"'
        out.append('<g class="%s"%s>%s</g>' % (cls, rest, doc.text(14, ly, txt, "psm", 18.5, "ink", tracking=-0.01)))
    doc.add('<g clip-path="url(#%s)">%s</g>' % (cid, "".join(out)))
    body = ("I build software with impeccable manners: it shows its workings, cites its sources, "
            "and never invents a figure.")
    for i, line in enumerate(wrap("ps", 15.5, body, 470)):
        doc.add(doc.text(0, 258 + i * 24, line, "ps", 15.5, "ink2"))

    # ---- the orbit
    P = 12.0
    R1, R2, ZO = 2.05, 3.2, 0.32
    pts = [(R2 * math.cos(a), R2 * math.sin(a), ZO) for a in [i * math.pi / 18 for i in range(36)]]
    pts += box_pts(-1.1, -1.1, 1.1, 1.1, 0, 0.62) + [(R2 * math.cos(a), R2 * math.sin(a), ZO + 1.6) for a in (0, 1.6, 3.2, 4.7)]
    cam = fit(32, 42, pts, (526, 4, 314, 306), pad=16)
    af = math.atan2(cam.ct, cam.st)                         # the angle that faces the viewer

    def orbit_path(R, front):
        a0 = af - math.pi / 2 if front else af + math.pi / 2
        seg = [cam.P(R * math.cos(a0 + k * math.pi / 40), R * math.sin(a0 + k * math.pi / 40), ZO) for k in range(41)]
        return path(seg)

    doc.css.append("@keyframes ants{to{stroke-dashoffset:-20}}@keyframes antsr{to{stroke-dashoffset:20}}"
                   ".ants{animation:ants 2.4s linear infinite}.antsr{animation:antsr 2.4s linear infinite}"
                   ".g-fill{fill:%s}" % th["plate"])
    back_rings = "".join('<path class="gd dash %s" d="%s"/>' % (c, orbit_path(R, False)) for R, c in ((R1, "ants"), (R2, "antsr")))
    front_rings = "".join('<path class="gd dash %s" d="%s" style="stroke:%s"/>' % (c, orbit_path(R, True), th["mid"])
                          for R, c in ((R1, "ants"), (R2, "antsr")))

    items = [("voice", 1, 0.0, "Voice RAG: a 3.4 ms retrieval core"),
             ("shuttle", 2, 2.0, "Badminton: state level"),
             ("layers", 1, 4.0, "Saakshi: proof, not just photos"),
             ("reel", 2, 6.0, "Films: every genre, no skips"),
             ("graph", 1, 8.0, "CodeFlow: maps how code fits together"),
             ("belt", 2, 10.0, "Karate: 2nd dan, breaks boards not builds")]
    NS = 60
    back_items, front_items = [], []
    for idx, (glyph, ring, tf, _) in enumerate(items):
        R = R1 if ring == 1 else R2
        w = (2 * math.pi / P) * (1 if ring == 1 else -1)
        a0 = af - w * tf
        base = cam.P(R * math.cos(a0), R * math.sin(a0), ZO)
        frames = []
        for k in range(NS + 1):
            t = P * k / NS
            a = a0 + w * t
            p = cam.P(R * math.cos(a), R * math.sin(a), ZO)
            d = math.cos(a - af)
            sc = 0.8 + 0.3 * (d + 1) / 2
            frames.append((t, p[0] - base[0], p[1] - base[1], sc, d))
        name = doc.uid()
        for copy, front in (("b", False), ("f", True)):
            kf = []
            for t, dx, dy, sc, d in frames:
                vis = (d >= 0) if front else (d < 0)
                op = (0.45 + 0.55 * (d + 1) / 2) if vis else 0
                col = th["hi"] if d > 0.94 else th["edge"]
                kf.append("%s%%{transform:translate(%spx,%spx) scale(%s);opacity:%s;stroke:%s}" % (
                    n(t / P * 100), n(dx), n(dy), n(sc), n(op), col))
            doc.css.append("@keyframes %s%s{%s}.%s%s{animation:%s%s %ss linear infinite}" % (
                name, copy, "".join(kf), name, copy, name, copy, n(P)))
            _, _, _, sc0, d0 = frames[0]
            vis0 = (d0 >= 0) if front else (d0 < 0)
            badge = ('<g class="%s%s" style="transform-origin:%spx %spx;stroke:%s" opacity="%s" transform="scale(%s)">'
                     '<circle cx="%s" cy="%s" r="15" fill="%s"/><g transform="translate(%s %s)">%s</g></g>') % (
                name, copy, n(base[0]), n(base[1]), th["hi"] if d0 > 0.94 else th["edge"],
                n((0.45 + 0.55 * (d0 + 1) / 2) if vis0 else 0), n(sc0),
                n(base[0]), n(base[1]), th["plate"], n(base[0]), n(base[1]), GLYPHS[glyph]())
            (front_items if front else back_items).append(badge)

    # beams from the core to the front of each ring, as each item arrives
    top = cam.P(0, 0, 0.62)
    beams = []
    for ring, R in ((1, R1), (2, R2)):
        tip = cam.P(R * math.cos(af), R * math.sin(af), ZO)
        b = Track(0)
        for idx, (g_, r_, tf, _) in enumerate(items):
            if r_ != ring:
                continue
            if tf - 0.25 > b.pts[-1][0]:
                b.step(tf - 0.25, 0.9, fade=0.2)
                b.step(tf + 0.55, 0, fade=0.5)
        if ring == 1:       # its first pass is at t = 0: open on, close the loop on
            b = Track(0.9)
            b.step(0.55, 0, fade=0.5)
            for tf in (4.0, 8.0):
                b.step(tf - 0.25, 0.9, fade=0.2)
                b.step(tf + 0.55, 0, fade=0.5)
            b.step(P - 0.3, 0.9, fade=0.25)
        bcls = doc.animate(b, P, lambda v: "opacity:%s" % n(v))
        beams.append('<path class="%s" d="M%s %sL%s %s" stroke="%s" stroke-width="1.3" stroke-linecap="round" opacity="0"/>' % (
            bcls, n(top[0]), n(top[1]), n(tip[0]), n(tip[1] - 14), th["hi"]))

    # the core: a chip engraved AM, with pins on its two visible faces and a pulse every pass
    pins = []
    for y in (-0.55, -0.18, 0.18, 0.55):
        pins.append(path([cam.P(1.1, y, 0.24), cam.P(1.4, y, 0.24)]))
        pins.append(path([cam.P(y, 1.1, 0.24), cam.P(y, 1.4, 0.24)]))
    core = slab(doc, cam, -1.1, -1.1, 1.1, 1.1, 0, 0.42, r=0.22, inset=0.12)
    core += slab(doc, cam, -0.7, -0.7, 0.7, 0.7, 0.42, 0.62, r=0.14, inset=0.07)
    ax, ay = cam.d(dx=1)
    bx, by = cam.d(dy=1)
    ex, ey = cam.P(0, 0, 0.62)
    core += ('<text transform="matrix(%s %s %s %s %s %s)" x="0" y="0.2" text-anchor="middle" class="f-psb" '
             'font-size="0.62" fill="%s">AM</text>') % (n(ax), n(ay), n(bx), n(by), n(ex), n(ey), th["ink"])
    doc.fonts.add("psb")
    pulse = Track((1, 0))
    for k in range(6):
        t0 = 2.0 * k
        if k == 0:
            pulse = Track((1, 0.7))
            pulse.to(0, (2.4, 0), dur=0.9, ease="cubic-bezier(.2,.7,.3,1)")
            pulse.step(1.0, (1, 0), fade=0)
            continue
        pulse.step(t0, (1, 0.7), fade=0.03)
        pulse.to(t0 + 0.03, (2.4, 0), dur=0.9, ease="cubic-bezier(.2,.7,.3,1)")
        pulse.step(t0 + 1.0, (1, 0), fade=0)
    pulse.step(P - 0.02, (1, 0.7), fade=0.015)
    pcls = doc.animate(pulse, P, lambda v: "transform:scale(%s);opacity:%s" % (n(v[0]), n(v[1])))
    ring_pts = [cam.P(0.95 * math.cos(a), 0.95 * math.sin(a), 0.62) for a in [i * math.pi / 20 for i in range(40)]]
    core += '<path class="%s" d="%s" fill="none" stroke="%s" stroke-width="1.1" opacity="0" style="transform-origin:%spx %spx"/>' % (
        pcls, path(ring_pts, True), th["hi"], n(ex), n(ey))
    core += '<g class="mg">%s</g>' % "".join('<path class="mk" d="%s"/>' % p_ for p_ in pins)

    doc.add(back_rings + "".join(back_items) + core + "".join(beams) + front_rings + "".join(front_items))
    cx = 530 + 155
    doc.add(windows(doc, cx, H - 8, [
        (txt, [(tf - 1.0, tf + 1.0)] if tf else [(0, 1.0), (P - 1.0, P)]) for (_, _, tf, txt) in items
    ], P, static=0, anchor="middle", size=11.5))
    return doc.render()


# ============================================================================ shared pieces

def grower(doc, cam, ring, z0, zmax, inset=0.12):
    """A solid drawn at full height, clipped at its base, so a translate makes it grow."""
    sil, crease = prism(cam, ring, z0, zmax, inset)
    front = base_front(cam, ring, z0)
    R, L = front[0], front[-1]
    cid = doc.uid()
    clip = [(R[0] + 1.2, R[1])] + front + [(L[0] - 1.2, L[1]), (L[0] - 1.2, -4000), (R[0] + 1.2, -4000)]
    doc.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, path(clip, True)))
    return cid, sil, crease


def drop(cam, zmax, h):
    return cam.d(dz=h - zmax)


LANG = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6"}


def frame_box(doc, H):
    doc.add('<rect x=".5" y=".5" width="%s" height="%s" rx="6" fill="none" stroke="%s"/>' % (W - 1, H - 1, doc.th["border"]))


def plate(theme, key, title, meta, tagline, body, H, figure):
    """A project as a large pinned card: same border, radius and title row as GitHub's."""
    repo, lang = meta
    doc = Doc(W, H, theme, title, "%s (%s). %s %s" % (title, repo, tagline, body), key)
    th = doc.th
    frame_box(doc, H)
    P = 28
    doc.add(doc.text(P, 64, title, "psb", 34, "ink", tracking=-0.025))
    x = P
    doc.add(doc.text(x, 92, repo, "pm", 12, "accent"))
    x += measure("pm", 12, repo) + 12
    pw = measure("psm", 11, "Public") + 14
    doc.add('<rect x="%s" y="80" width="%s" height="18" rx="9" fill="none" stroke="%s"/>' % (n(x + .5), n(pw), th["border"]))
    doc.add(doc.text(x + 7.5, 93, "Public", "psm", 11, "ink2"))
    x += pw + 14
    doc.add('<circle cx="%s" cy="88.5" r="5.5" fill="%s"/>' % (n(x + 5.5), LANG[lang]))
    doc.add(doc.text(x + 16, 93, lang, "ps", 12.5, "ink2"))
    y = 140
    for line in wrap("psm", 18.5, tagline, 320):
        doc.add(doc.text(P, y, line, "psm", 18.5, "ink", tracking=-0.01))
        y += 26
    y += 8
    for line in wrap("ps", 14.5, body, 320):
        doc.add(doc.text(P, y, line, "ps", 14.5, "ink2"))
        y += 22
    figure(doc, (380, 16, W - 380 - 18, H - 16 - 34))
    return doc.render()


# ============================================================================ Voice RAG

def fig_voice(doc, frame):
    th = doc.th
    T = 9.2
    X_STT0, X_STT1 = 4.3, 14.3          # ~1,400 ms of speech to text
    X_CORE0 = 14.85                     # ragCore starts here
    X_BUD1 = X_CORE0 + 10.0 / 7.0       # the 200 ms budget, same scale
    X_CORE1 = X_CORE0 + 0.17            # 3.4 ms would be 0.024: drawn at the thinnest that reads
    QX0, QX1 = 16.9, 18.9
    WAVE = [0.55, 1.15, 1.95, 1.35, 2.45, 1.7, 0.95, 1.45, 0.6]
    WMAX = 2.9
    pts = box_pts(-0.7, -0.2, 19.6, 2.6, -0.35, 0) + box_pts(0, 0.8, 4, 1.6, 0, WMAX + 0.4) + \
        box_pts(QX0, 0.3, QX1, 2.1, 0, 1.6)
    cam = fit(41, 30, pts, frame, pad=4)

    # rail
    doc.add(solid(doc, cam, rrect(-0.7, -0.2, 19.6, 2.6, 0.7), -0.35, 0, inset=0.22))
    # budget footprint: a guide, painted behind what it belongs to
    doc.add('<path class="gd dash" d="%s"/>' % flat(cam, rrect(X_CORE0 - 0.12, 0.32, X_BUD1, 2.08, 0.25), 0, True))

    # waveform: the question, out loud
    rnd = random.Random(3)
    for i, h0 in enumerate(WAVE):
        x0 = 0.25 + i * 0.44
        ring = rrect(x0, 0.85, x0 + 0.26, 1.55, 0.1, 2)
        cid, sil, cr = grower(doc, cam, ring, 0, WMAX, 0.06)
        t = Track(drop(cam, WMAX, h0))
        tt = 0.8
        while tt < 2.2:
            t.to(tt, drop(cam, WMAX, rnd.uniform(0.25, WMAX)), dur=0.24)
            tt += 0.26
        t.to(2.35, drop(cam, WMAX, h0), dur=0.45)
        cls = doc.animate(t, T, tr)
        o = drop(cam, WMAX, h0)
        doc.add('<g clip-path="url(#%s)"><g class="%s" transform="translate(%s %s)">%s</g></g>' % (
            cid, cls, n(o[0]), n(o[1]), solid(doc, cam, ring, 0, WMAX, 0.06)))

    phases = [(2.4, "stt"), (4.3, "core"), (6.2, "quote"), (8.1, None)]
    REST = "core"

    def part(name, ring, z0, z1, lift, extra=""):
        on = [(w, (p == name) if p else (name == REST)) for w, p in phases]
        scls = lit_track(doc, name == REST, on, T, th["hi"], th["edge"])
        mcls = lit_track(doc, name == REST, on, T, th["hi"], th["mid"])
        t = Track((0, 0))
        for w, p in phases:
            t.to(w, cam.d(dz=lift) if p == name else (0, 0))
        lcls = doc.animate(t, T, tr)
        sil, cr = prism(cam, ring, z0, z1, 0.14)
        rs = th["hi"] if name == REST else th["edge"]
        rm = th["hi"] if name == REST else th["mid"]
        return ('<g class="%s"><g class="s %s" style="stroke:%s"><path class="sil" d="%s"/>%s</g>'
                '<g class="%s" style="stroke:%s">%s</g></g>') % (
            lcls, scls, rs, sil, ('<path class="cr" d="%s"/>' % cr) if cr else "", mcls, rm, extra)

    # speech to text: long, and not ours
    stt_marks = "".join('<path class="mk" d="%s"/>' % flat(cam, [(x, 0.75), (x, 1.65)], 0.7)
                        for x in [X_STT0 + 0.6 + k * 0.6 for k in range(16)])
    doc.add(part("stt", rrect(X_STT0, 0.55, X_STT1, 1.85, 0.3), 0, 0.7, 0.45, stt_marks))
    # ragCore: 3.4 ms, a sliver inside its budget
    doc.add(part("core", rrect(X_CORE0, 0.55, X_CORE1, 1.85, 0.06, 2), 0, 1.45, 0.35))
    # the answer: a quote with its passage id
    qlines = [flat(cam, [(QX0 + 0.35, y), (QX0 + 0.35 + L, y)], 0.75) for y, L in ((0.75, 1.2), (1.15, 1.25), (1.55, 0.8))]
    qlines.append(flat(cam, circle(QX1 - 0.4, 1.75, 0.12, 12), 0.75, True))
    doc.add(part("quote", rrect(QX0, 0.3, QX1, 2.1, 0.25), 0.5, 0.75, 0.5,
                 "".join('<path class="mk" d="%s"/>' % q for q in qlines)))

    x = W - 28
    y = doc.h - 18
    doc.add(readouts(doc, x, y, [
        (0, 0, "ragCore 3.4 ms of ~1.4 s"),
        (0.8, 2.4, "listening"),
        (2.4, 4.3, "speech to text ~1,400 ms, not ours"),
        (4.3, 6.2, "ragCore 3.4 ms p50, budget 200 ms"),
        (6.2, 8.1, "a verbatim span, with its passage id"),
    ], T))


def voice(theme):
    return plate(theme, "v", "Voice RAG", ("AnshulMohanty/HH_Goa", "JavaScript"),
                 "Ask out loud. Get a quote, not a vibe.",
                 "Voice-first retrieval with a 200 ms budget. The retrieval core runs in 3.4 ms, "
                 "and the README shows exactly where the other 1.4 seconds go.",
                 300, fig_voice)


# ============================================================================ Saakshi

def fig_layers(doc, frame):
    """As on Saakshi's own site: one photo lifts apart into five labelled evidence layers,
    each read in turn, then they seal back into one proof."""
    th = doc.th
    fx, fy, fw, fh = frame
    T = 10.0
    N, SZ, TH, GAP = 5, 8.0, 0.3, 2.0
    names = [("The photo", "the original, untouched"), ("Where and when", "GPS and time, checked"),
             ("Its fingerprint", "pHash, catches reuse"), ("What the AI sees", "objects, labelled"),
             ("What was measured", "mask area, counted")]
    sw = fw - 150
    pts = box_pts(0, 0, SZ, SZ, 0, (N - 1) * GAP + TH + 0.2)
    cam = fit(40, 31, pts, (fx, fy, sw, fh), pad=4)
    LIFT0 = 0.9                     # layers start rising
    RISE = [LIFT0 + (k - 1) * 0.28 if k else LIFT0 for k in range(N)]
    READ = [2.7 + k * 0.75 for k in range(N)]
    SEAL = 6.75                     # labels go, layers collapse
    SEALED = 7.6
    rnd = random.Random(11)
    bits = [rnd.random() < 0.45 for _ in range(64)]

    def marks(k, z):
        m = []
        if k == 0:      # the photo
            m.append(flat(cam, rrect(0.7, 0.7, SZ - 0.7, SZ - 0.7, 0.3), z, True))
            m.append(flat(cam, [(1.0, 5.9), (2.6, 4.1), (3.7, 5.0), (5.1, 3.2), (7.0, 5.6)], z))
            m.append(flat(cam, circle(5.6, 2.1, 0.55, 24), z, True))
        elif k == 1:    # where and when: the GPS ring, its centre, and a stamped tag
            m.append(flat(cam, circle(3.6, 4.2, 2.4, 48), z, True))
            m.append(flat(cam, circle(3.6, 4.2, 0.32, 16), z, True))
            m.append(flat(cam, rrect(4.6, 0.9, 7.4, 2.4, 0.15), z, True))
            m.append(flat(cam, [(4.95, 1.4), (6.9, 1.4)], z))
            m.append(flat(cam, [(4.95, 1.9), (6.3, 1.9)], z))
        elif k == 2:    # fingerprint: an 8 x 8 hash
            for i in range(8):
                for j in range(8):
                    if bits[i * 8 + j]:
                        cx, cy = 1.2 + i * 0.8, 1.2 + j * 0.8
                        m.append(flat(cam, rrect(cx - 0.24, cy - 0.24, cx + 0.24, cy + 0.24, 0.05, 1), z, True))
        elif k == 3:    # what the AI sees
            m.append(flat(cam, rrect(1.0, 1.3, 4.4, 4.5, 0.2), z, True))
            m.append(flat(cam, [(1.0, 1.0), (2.4, 1.0)], z))
            m.append(flat(cam, rrect(3.9, 3.7, 7.0, 6.8, 0.2), z, True))
            m.append(flat(cam, [(3.9, 3.4), (5.0, 3.4)], z))
        else:           # what was measured: a mask, hatched
            blob = [(4 + (2.6 + 0.5 * math.sin(3 * a) + 0.3 * math.cos(5 * a)) * math.cos(a),
                     4 + (2.4 + 0.4 * math.cos(2 * a)) * math.sin(a)) for a in [i * math.pi / 24 for i in range(48)]]
            m.append(flat(cam, blob, z, True))
            for yy in (2.6, 3.4, 4.2, 5.0, 5.8):
                m.append(flat(cam, [(2.2, yy), (5.8, yy)], z))
        return "".join('<path class="mk" d="%s"/>' % d for d in m)

    lx = fx + sw + 18
    for k in range(N):
        sil, cr = prism(cam, rrect(0, 0, SZ, SZ, 0.6), 0, TH, 0.16)
        flat_z, up_z = k * 0.07, k * GAP
        # position: flat -> rises -> holds -> collapses (top layers first) -> flat
        t = Track(cam.d(dz=flat_z))
        t.to(RISE[k], cam.d(dz=up_z), dur=0.6, ease="cubic-bezier(.3,.7,.2,1)")
        t.to(SEAL + (N - 1 - k) * 0.1, cam.d(dz=flat_z), dur=0.6, ease="cubic-bezier(.6,0,.4,1)")
        lcls = doc.animate(t, T, tr)
        lit = [(READ[k], True), (READ[k] + 0.75, False)]
        if k == 0:
            lit += [(SEALED, True), (T - 0.4, False)]
        scls = lit_track(doc, False, lit, T, th["hi"], th["edge"])
        mcls = lit_track(doc, False, lit, T, th["hi"], th["mid"])
        # leader line from the plate's right corner to its label, moving with the plate
        cxr, cyr = cam.P(SZ, 0, TH)
        lead_y = cyr
        op = Track(0)
        op.step(RISE[k] + 0.45, 1, fade=0.25)
        op.step(SEAL - 0.1, 0, fade=0.25)
        ocls = doc.animate(op, T, lambda v: "opacity:%s" % n(v))
        leader = '<g class="%s"><path d="M%s %sH%s" stroke="%s" stroke-dasharray="2 3"/><circle cx="%s" cy="%s" r="1.8" fill="%s"/></g>' % (
            ocls, n(cxr + 4), n(lead_y), n(lx - 6), th["edge"], n(lx - 6), n(lead_y), th["edge"])
        o = cam.d(dz=up_z)
        doc.add('<g class="%s" transform="translate(%s %s)"><g class="s %s"><path class="sil" d="%s"/><path class="cr" d="%s"/></g>'
                '<g class="%s mg">%s</g>%s</g>' % (lcls, n(o[0]), n(o[1]), scls, sil, cr, mcls, marks(k, TH), leader))
        # the label, fixed where the plate comes to rest
        ly = lead_y + o[1]
        lab = doc.text(lx, ly - 2, "%d  %s" % (k + 1, names[k][0]), "psm", 12, "ink")
        lab += doc.text(lx, ly + 13, names[k][1], "ps", 10.5, "ink3")
        doc.add('<g class="%s">%s</g>' % (ocls, lab))
    doc.add(windows(doc, W - 28, doc.h - 18, [
        ("one photo", [(0, LIFT0)]),
        ("what Saakshi reads from one photo", [(LIFT0, SEAL)]),
        ("sealed into one proof", [(SEAL, T)]),
    ], T, static=1))


def saakshi(theme):
    return plate(theme, "s", "Saakshi", ("AnshulMohanty/Saakshi", "TypeScript"),
                 "Proof, not just photos.",
                 "Turns field photos from NGOs and community groups into verified, measured, "
                 "traceable proof of impact. Every number in a report links to the photo behind it.",
                 330, fig_layers)


# ============================================================================ CodeFlow

def fig_codeflow(doc, frame):
    """CodeFlow's own picture: eight stages fill a rail while the dependency map resolves in rings
    (foundations at the centre). Then it answers: what breaks if auth/session changes?"""
    th = doc.th
    fx, fy, fw, fh = frame
    T = 12.0
    END = 10.9
    stages = ["ingest", "orient", "map", "inventory", "connect", "analyze", "synthesize", "index"]
    # ---- rail
    rx0, rw = fx, 150
    row0, rh = fy + 26, 26
    doc.add(doc.text(rx0, fy + 8, "PIPELINE", "pm", 9.5, "ink3", tracking=0.12))
    for i, name in enumerate(stages):
        y = row0 + i * rh
        t0 = 0.25 + i * 0.42
        doc.add(doc.text(rx0, y, "%02d" % (i + 1), "pm", 10, "ink3"))
        lt = Track(doc.c("ink3"))
        lt.step(t0 + 0.38, doc.c("ink"))
        lt.step(END, doc.c("ink3"), fade=0.4)
        lcls = doc.animate(lt, T, lambda v: "fill:%s" % v)
        doc.add(doc.text(rx0 + 22, y, name, "pm", 11, "ink", cls=lcls))
        if i >= 6:
            doc.add(doc.text(rx0 + rw, y, "key", "pm", 9, "ink3", "end"))
        by = y + 7
        doc.add('<rect x="%s" y="%s" width="%s" height="2.5" rx="1.25" fill="%s"/>' % (n(rx0 + 22), n(by), rw - 22, th["lo"]))
        bt = Track(0)
        bt.to(t0, 1, dur=0.38, ease="cubic-bezier(.4,0,.2,1)")
        bt.to(END, 0, dur=0.5)
        bcls = doc.animate(bt, T, lambda v: "transform:scaleX(%s)" % n(v))
        doc.add('<rect class="%s" x="%s" y="%s" width="%s" height="2.5" rx="1.25" fill="%s" style="transform-origin:%spx %spx"/>' % (
            bcls, n(rx0 + 22), n(by), rw - 22, th["hi"], n(rx0 + 22), n(by)))

    # ---- the map
    gx = fx + rw + (fw - rw) / 2 + 10
    gy = fy + fh / 2 + 4
    R = min((fw - rw) / 2 - 14, fh / 2 - 6)
    rings = [0, 0.36, 0.67, 0.97]
    for k in (1, 2, 3):
        doc.add('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" %s/>' % (
            n(gx), n(gy), n(R * rings[k]), th["lo"] if k < 3 else th["mid"], 'stroke-dasharray="2 3"' if k == 3 else ""))
    doc.add(doc.text(gx + R + 2, fy + 8, "RINGS = HOW FOUNDATIONAL", "pm", 9.5, "ink3", "end", tracking=0.12))
    rnd = random.Random(21)
    counts = [1, 4, 7, 10]
    nodes = []          # (ring, x, y, r)
    for k, cnt in enumerate(counts):
        off = rnd.uniform(0, 2 * math.pi)
        for j in range(cnt):
            a = off + 2 * math.pi * j / cnt + rnd.uniform(-0.18, 0.18)
            rr = R * rings[k] * (1 + rnd.uniform(-0.04, 0.04))
            nodes.append((k, gx + rr * math.cos(a), gy + rr * math.sin(a), [5.2, 4.2, 3.4, 2.8][k]))
    by_ring = {k: [i for i, nd in enumerate(nodes) if nd[0] == k] for k in range(4)}
    edges = []          # (child, parent): dependencies point inward
    for k in (1, 2, 3):
        for i in by_ring[k]:
            inner = sorted(by_ring[k - 1], key=lambda p: (nodes[p][1] - nodes[i][1]) ** 2 + (nodes[p][2] - nodes[i][2]) ** 2)
            edges.append((i, inner[0]))
            if k > 1 and rnd.random() < 0.45 and len(inner) > 1:
                edges.append((i, inner[1]))
    sel = by_ring[1][0]
    # blast radius: everything that depends on sel, by hops
    hop = {sel: 0}
    frontier = [sel]
    while frontier:
        nxt = []
        for p in frontier:
            for c, q in edges:
                if q == p and c not in hop:
                    hop[c] = hop[p] + 1
                    nxt.append(c)
        frontier = nxt
    ASK, PICK, SPREAD = 4.1, 4.7, 5.15
    for ei, (c, p) in enumerate(edges):
        x1, y1 = nodes[c][1], nodes[c][2]
        x2, y2 = nodes[p][1], nodes[p][2]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        bend = 0.18 * (1 if ei % 2 else -1)
        qx, qy = mx + (gx - mx) * 0.25 - (y2 - y1) * bend, my + (gy - my) * 0.25 + (x2 - x1) * bend
        d = "M%s %sQ%s %s %s %s" % (n(x1), n(y1), n(qx), n(qy), n(x2), n(y2))
        k = nodes[c][0]
        t0 = [0, 2.35, 2.7, 3.05][k] + ei * 0.012
        draw = Track(1)
        draw.to(t0, 0, dur=0.45, ease="cubic-bezier(.4,0,.2,1)")
        draw.step(END + 0.6, 1, fade=0)
        lit = c in hop and p in hop
        col = Track(th["mid"])
        if lit:
            col.step(SPREAD + 0.12 * hop[c], th["hi"], fade=0.25)
            col.step(END + 0.6, th["mid"], fade=0)
        dcls = doc.animate_many([(draw, lambda v: "stroke-dashoffset:%s" % n(v)), (col, lambda v: "stroke:%s" % v)], T)
        ccls = ""
        op = Track(1)
        op.step(END, 0, fade=0.45)
        op.step(T - 0.05, 1, fade=0)
        ocls = doc.animate(op, T, lambda v: "opacity:%s" % v)
        doc.add('<g class="%s"><path class="%s %s" d="%s" pathLength="1" fill="none" stroke="%s" stroke-width="%s" '
                'stroke-dasharray="1" style="vector-effect:none"/></g>' % (
                    ocls, dcls, ccls, d, th["hi"] if lit else th["mid"], "1.1" if lit else "0.8"))
    far = max(by_ring[1], key=lambda i: (nodes[i][1] - nodes[sel][1]) ** 2 + (nodes[i][2] - nodes[sel][2]) ** 2)
    labels = {0: "config/env", sel: "auth/session", far: "core/resolver"}
    for i, (k, x, y, r) in enumerate(nodes):
        t0 = [0.7, 1.1, 1.5, 1.9][k] + (i % 7) * 0.03
        op = Track(0)
        op.step(t0, 1, fade=0.25)
        op.step(END, 0, fade=0.45)
        ocls = doc.animate(op, T, lambda v: "opacity:%s" % v)
        lit = i in hop
        st = Track(th["edge"])
        fl = Track(th["plate"])
        if lit:
            when = PICK if i == sel else SPREAD + 0.12 * hop[i]
            st.step(when, th["hi"], fade=0.2)
            st.step(END + 0.6, th["edge"], fade=0)
            if i == sel:
                fl.step(when, th["hi"], fade=0.2)
                fl.step(END + 0.6, th["plate"], fade=0)
        scls = doc.animate_many([(st, lambda v: "stroke:%s" % v), (fl, lambda v: "fill:%s" % v)], T)
        fcls = ""
        body = '<circle class="%s %s" cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>' % (
            scls, fcls, n(x), n(y), n(r), th["hi"] if i == sel else th["plate"], th["hi"] if lit else th["edge"])
        if i in labels:
            col = "ink" if i == sel else "ink2"
            if k == 0:
                body += doc.text(x, y + r + 12, labels[i], "pm", 9.5, col, "middle")
            elif x < gx:
                body += doc.text(x - r - 4, y + 3.5, labels[i], "pm", 9.5, col, "end")
            else:
                body += doc.text(x + r + 4, y + 3.5, labels[i], "pm", 9.5, col)
        doc.add('<g class="%s">%s</g>' % (ocls, body))
    # a pulse when the question lands on auth/session
    _, sx, sy, sr = nodes[sel]
    pulse = Track((1, 0))
    pulse.step(PICK, (1, 0.9), fade=0.05)
    pulse.to(PICK + 0.05, (3.4, 0), dur=0.9, ease="cubic-bezier(.2,.7,.3,1)")
    pulse.step(PICK + 1.1, (1, 0), fade=0)
    pcls = doc.animate(pulse, T, lambda v: "transform:scale(%s);opacity:%s" % (n(v[0]), n(v[1])))
    doc.add('<circle class="%s" cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.2" opacity="0" style="transform-origin:%spx %spx"/>' % (
        pcls, n(sx), n(sy), n(sr + 2), th["hi"], n(sx), n(sy)))
    nb = len(hop) - 1
    doc.add(windows(doc, W - 28, doc.h - 18, [
        ("resolving the graph, deterministic pass first", [(0, ASK), (END + 0.3, T)]),
        ("ask // what breaks if I change auth/session?", [(ASK, SPREAD + 0.5)]),
        ("auth/session changes: %d modules break, each cited" % nb, [(SPREAD + 0.5, END + 0.3)]),
    ], T, static=2))


def codeflow(theme):
    return plate(theme, "c", "CodeFlow", ("AnshulMohanty/Code_Flow", "TypeScript"),
                 "Maps how a codebase fits together.",
                 "Eight stages from git clone to a map you can question. Answers cite real files "
                 "and lines, and a line that was never read cannot be cited.",
                 300, fig_codeflow)


# ============================================================================ stack

STACK = [
    ("Languages", "TypeScript, JavaScript on Node (ESM), Python, Java"),
    ("Frontend", "React, Next.js, Vite, Tailwind CSS, three.js, GSAP"),
    ("Backend", "Express, server-sent events, BullMQ, Inngest, MCP servers"),
    ("Data", "Postgres with pgvector, PGlite, Drizzle, MongoDB, Redis, Qdrant"),
    ("Retrieval and AI", "hnswlib, MiniLM on transformers.js, BM25 + vector hybrid, Gemini, Claude, Voyage"),
    ("Tooling", "pnpm workspaces, Docker Compose, Vitest, Playwright, Zod, GitHub Actions"),
]
MARQUEE = ["TypeScript", "React", "Next.js", "Node.js", "Express", "PostgreSQL", "pgvector", "Redis",
           "BullMQ", "MongoDB", "Docker", "tree-sitter", "three.js", "Playwright"]
LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "Java": "#b07219",
               "HTML": "#e34c26", "CSS": "#663399", "Go": "#00ADD8", "Rust": "#dea584", "C++": "#f34b7d"}
# snapshot of primary languages across public, non-fork repos (scripts/contributions.py refreshes it daily)
LANG_SNAPSHOT = ([("TypeScript", 9), ("JavaScript", 6), ("Python", 4), ("Java", 2), ("HTML", 1)], 24)


FOCUS = [
    ("AI retrieval and RAG", "Search that answers with a quote and its source.",
     ["RAG", "pgvector", "hnswlib", "BM25 + vectors", "MiniLM", "Gemini", "Claude", "Voyage", "Qdrant"]),
    ("Full-stack TypeScript", "Products end to end, from the UI to the job queue.",
     ["TypeScript", "React", "Next.js", "Node.js", "Express", "Tailwind CSS", "three.js", "GSAP"]),
    ("Systems and data", "Pipelines, caches and code graphs behind the apps.",
     ["PostgreSQL", "MongoDB", "Redis", "BullMQ", "Docker", "tree-sitter", "Playwright", "Vitest"]),
]


def chips(doc, x, y, width, names, delay0):
    """Flow-wrapped pills, like GitHub topic labels. Returns the svg and the height used."""
    th = doc.th
    out, cx, cy, hgt, gap = [], x, y, 26, 7
    for i, nm in enumerate(names):
        w = measure("ps", 13, nm) + 22
        if cx + w > x + width and cx > x:
            cx, cy = x, cy + hgt + gap
        fill = th["subtle"]
        pill = ('<rect x="%s" y="%s" width="%s" height="%s" rx="13" fill="%s" stroke="%s"/>' % (
            n(cx + .5), n(cy + .5), n(w), hgt, fill, th["border"]) +
            doc.text(cx + 11.5, cy + 17.5, nm, "ps", 13, "ink"))
        out.append('<g class="cp" style="animation-delay:%ss">%s</g>' % (n(delay0 + i * 0.04), pill))
        cx += w + gap
    return "".join(out), cy + hgt - y


def fx_rag(doc, x, y, w, h):
    """A query finds the line that answers it, and comes back as a quote with its citation."""
    th = doc.th
    T = 5.0
    qx, qy = x, y + h / 2 - 11
    doc.add('<rect x="%s" y="%s" width="58" height="22" rx="11" fill="%s" stroke="%s"/>' % (n(qx + .5), n(qy + .5), th["subtle"], th["border"]))
    doc.add(doc.text(qx + 29, qy + 15, "query", "pm", 10.5, "ink2", "middle"))
    dx, dy, dw, dh = x + 84, y + 6, 72, h - 12
    for i in (2, 1):                                   # the pile behind
        doc.add('<rect x="%s" y="%s" width="%s" height="%s" rx="4" fill="%s" stroke="%s"/>' % (
            n(dx + i * 6), n(dy - i * 5), dw, dh, th["plate"], th["mid"]))
    doc.add('<rect x="%s" y="%s" width="%s" height="%s" rx="4" fill="%s" stroke="%s"/>' % (n(dx), n(dy), dw, dh, th["plate"], th["edge"]))
    rows = [dy + 14 + k * 13 for k in range(6)]
    lens = [52, 44, 50, 36, 48, 30]
    HIT = 3
    for k, (ry, L) in enumerate(zip(rows, lens)):
        if k == HIT:
            col = Track(th["mid"])
            col.step(2.0, th["hi"], fade=0.2)
            col.step(4.5, th["mid"], fade=0.3)
            c = doc.animate(col, T, lambda v: "stroke:%s" % v)
            doc.add('<path class="%s" d="M%s %sH%s" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (
                c, n(dx + 10), n(ry), n(dx + 10 + L), th["hi"]))
        else:
            doc.add('<path d="M%s %sH%s" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (n(dx + 10), n(ry), n(dx + 10 + L), th["mid"]))
    # the beam from the query to the page, then a reading bar that runs down to the hit
    beam = Track(1)
    beam.to(0.2, 0, dur=0.5, ease="cubic-bezier(.4,0,.2,1)")
    beam.step(4.4, 1, fade=0.3)
    bcls = doc.animate(beam, T, lambda v: "stroke-dashoffset:%s" % n(v))
    doc.add('<path class="%s" d="M%s %sH%s" pathLength="1" stroke-dasharray="1" stroke="%s" stroke-width="1.2" style="vector-effect:none"/>' % (
        bcls, n(qx + 60), n(qy + 11), n(dx - 2), th["hi"]))
    scan = Track((0, 0))
    scan.to(0.75, (0, rows[HIT] - rows[0]), dur=1.15, ease="cubic-bezier(.45,0,.55,1)")
    scan.step(4.4, (0, 0), fade=0)
    sop = Track(0)
    sop.step(0.7, 0.9, fade=0.15)
    sop.step(2.05, 0, fade=0.25)
    scls = doc.animate_many([(scan, tr), (sop, lambda v: "opacity:%s" % n(v))], T)
    doc.add('<rect class="%s" x="%s" y="%s" width="%s" height="9" rx="2" fill="%s" opacity="0"/>' % (
        scls, n(dx + 5), n(rows[0] - 4.5), dw - 10, th["hi"]))
    # the quote slides out with its citation
    cx0 = dx + dw + 12
    q = Track((-24, 0))
    q.to(2.2, (0, 0), dur=0.55, ease="cubic-bezier(.2,.8,.2,1)")
    q.to(4.3, (-24, 0), dur=0.4)
    qo = Track(0)
    qo.step(2.2, 1, fade=0.3)
    qo.step(4.3, 0, fade=0.35)
    qcls = doc.animate_many([(q, tr), (qo, lambda v: "opacity:%s" % n(v))], T)
    qw = min(x + w - cx0, 74)
    doc.add('<g class="%s"><rect x="%s" y="%s" width="%s" height="40" rx="5" fill="%s" stroke="%s"/>'
            '<path d="M%s %sH%s" stroke="%s" stroke-width="2" stroke-linecap="round"/>%s</g>' % (
                qcls, n(cx0), n(rows[HIT] - 20), n(qw), th["plate"], th["hi"],
                n(cx0 + 9), n(rows[HIT] - 6), n(cx0 + qw - 12), th["hi"],
                doc.text(cx0 + 9, rows[HIT] + 12, "p.3, l.42", "pm", 9.5, "ink2")))


def fx_stack(doc, x, y, w, h):
    """A request travels down UI, API, queue and DB, and the answer comes back up."""
    th = doc.th
    T = 3.6
    names = ["UI", "API", "queue", "DB"]
    bw, bh, gap = min(w - 70, 150), 17, 8
    bx = x + 34
    tops = [y + 4 + k * (bh + gap) for k in range(4)]
    cx = bx + bw - 22
    # the packet's path: down, a pause at each layer, then up
    stops = [tops[k] + bh / 2 for k in range(4)]
    times_down = [0.3 + k * 0.42 for k in range(4)]
    times_up = [times_down[-1] + 0.5 + k * 0.32 for k in range(1, 4)]
    for k, nm in enumerate(names):
        col = Track(th["edge"])
        col.step(times_down[k], th["hi"], fade=0.12)
        up_t = times_up[2 - k] if k < 3 else times_down[3] + 0.3
        col.step(up_t + 0.25, th["edge"], fade=0.3)
        c = doc.animate(col, T, lambda v: "stroke:%s" % v)
        doc.add('<rect class="%s" x="%s" y="%s" width="%s" height="%s" rx="4" fill="%s" stroke="%s"/>' % (
            c, n(bx + .5), n(tops[k] + .5), bw, bh, th["plate"], th["edge"]))
        doc.add(doc.text(bx + 9, tops[k] + 12.5, nm, "pm", 10.5, "ink2"))
    doc.add('<path d="M%s %sV%s" stroke="%s" stroke-dasharray="2 3"/>' % (n(cx), n(tops[0] - 2), n(tops[-1] + bh + 2), th["mid"]))
    p = Track((0, 0))
    for t_, yy in zip(times_down, stops):
        p.to(max(t_ - 0.3, p.pts[-1][0]), (0, yy - stops[0]), dur=0.3, ease="cubic-bezier(.45,0,.55,1)")
    for t_, yy in zip(times_up, reversed(stops[:-1])):
        p.to(max(t_ - 0.26, p.pts[-1][0]), (0, yy - stops[0]), dur=0.26, ease="cubic-bezier(.45,0,.55,1)")
    pcls = doc.animate(p, T, tr)
    doc.add('<circle class="%s" cx="%s" cy="%s" r="4.2" fill="%s"/>' % (pcls, n(cx), n(stops[0]), th["hi"]))
    doc.add(doc.text(x, tops[0] + 12, "req", "pm", 9.5, "ink3"))
    doc.add(doc.text(x, tops[-1] + 12, "ok", "pm", 9.5, "ink3"))


def fx_ring(doc, x, y, w, h):
    """Keys land on a consistent-hashing ring and slide round to the node that owns them."""
    th = doc.th
    T = 5.0
    r = min(h / 2 - 6, 44)
    cx, cy = x + w / 2 + 18, y + h / 2
    doc.add('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-dasharray="2 3"/>' % (n(cx), n(cy), n(r), th["mid"]))
    nodes = [-80, -15, 50, 115, 180, 245]
    keys = [(-50, 0.2, 1), (85, 1.5, 3), (205, 2.8, 5)]       # angle it lands at, when, node that owns it
    for k, a in enumerate(nodes):
        ar = math.radians(a)
        nx, ny = cx + r * math.cos(ar), cy + r * math.sin(ar)
        col = Track(th["edge"])
        fl = Track(th["plate"])
        for ka, t0, owner in keys:
            if owner == k:
                col.step(t0 + 1.0, th["hi"], fade=0.12)
                col.step(t0 + 1.6, th["edge"], fade=0.3)
                fl.step(t0 + 1.0, th["hi"], fade=0.12)
                fl.step(t0 + 1.6, th["plate"], fade=0.3)
        c = doc.animate_many([(col, lambda v: "stroke:%s" % v), (fl, lambda v: "fill:%s" % v)], T)
        doc.add('<circle class="%s" cx="%s" cy="%s" r="5" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
            c, n(nx), n(ny), th["plate"], th["edge"]))
    for ka, t0, owner in keys:
        ar = math.radians(ka)
        kx, ky = cx + r * math.cos(ar), cy + r * math.sin(ar)
        # fly in from the left edge, then ride the ring to its node
        fly = Track((x - kx, 0))
        fly.to(t0, (0, 0), dur=0.45, ease="cubic-bezier(.2,.8,.2,1)")
        fly.step(t0 + 1.8, (x - kx, 0), fade=0)
        ride = Track(0)
        ride.to(t0 + 0.5, nodes[owner] - ka if nodes[owner] > ka else nodes[owner] + 360 - ka, dur=0.5, ease="cubic-bezier(.45,0,.2,1)")
        ride.step(t0 + 1.8, 0, fade=0)
        op = Track(0)
        op.step(t0, 1, fade=0.15)
        op.step(t0 + 1.1, 0, fade=0.3)
        fcls = doc.animate_many([(fly, tr), (op, lambda v: "opacity:%s" % n(v))], T)
        rcls = doc.animate(ride, T, lambda v: "transform:rotate(%sdeg)" % n(v))
        doc.add('<g class="%s" opacity="0"><g class="%s" style="transform-origin:%spx %spx">'
                '<rect x="%s" y="%s" width="8" height="8" rx="1.5" fill="%s"/></g></g>' % (
                    fcls, rcls, n(cx), n(cy), n(kx - 4), n(ky - 4), th["hi"]))
    doc.add(doc.text(x, y + h - 4, "keys", "pm", 9.5, "ink3"))


FX = [fx_rag, fx_stack, fx_ring]


def stack(theme, langs=None):
    langs, nrepos = langs or LANG_SNAPSHOT
    total = sum(c for _, c in langs) or 1
    P, G = 28, 26
    cw = (W - 2 * P - 2 * G) / 3
    FY, FH = 76, 112
    TY = FY + FH + 34
    probe = Doc(W, 10, theme, "", "", "z")
    body_h = max(22 + 21 * len(wrap("ps", 13.5, d, cw)) + 14 + chips(probe, 0, 0, cw, c, 0)[1] for _, d, c in FOCUS)
    H = int(TY + body_h + 34 + 74)
    doc = Doc(W, H, theme, "What I work on",
              "What I work on. " + " ".join("%s: %s %s." % (t, d, ", ".join(c)) for t, d, c in FOCUS) +
              " Written in " + ", ".join("%s %d%%" % (l, round(100 * c / total)) for l, c in langs) + ".", "k")
    th = doc.th
    frame_box(doc, H)
    doc.css.append("@keyframes cp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
                   ".cp{animation:cp .5s cubic-bezier(.2,.7,.2,1) both}")
    doc.add(doc.text(P, 50, "What I work on", "psb", 22, "ink", tracking=-0.02))
    for i, (title, desc, names) in enumerate(FOCUS):
        x = P + i * (cw + G)
        if i:
            doc.add('<path d="M%s %sV%s" stroke="%s"/>' % (n(x - G / 2), FY, n(TY + body_h - 20), th["border"]))
        FX[i](doc, x, FY, cw, FH)
        doc.add('<rect x="%s" y="%s" width="18" height="3" rx="1.5" fill="%s"/>' % (n(x), TY - 26, th["hi"]))
        doc.add(doc.text(x, TY, title, "psb", 18, "ink", tracking=-0.015))
        y = TY + 22
        for line in wrap("ps", 13.5, desc, cw):
            doc.add(doc.text(x, y, line, "ps", 13.5, "ink2"))
            y += 21
        svg, _ = chips(doc, x, y - 4, cw, names, 0.2 + i * 0.25)
        doc.add(svg)
    y0 = int(TY + body_h)
    doc.add('<path d="M%d %dH%d" stroke="%s"/>' % (P, y0, W - P, th["border"]))
    doc.add(doc.text(P, y0 + 30, "Written in", "psm", 13.5, "ink"))
    doc.add(doc.text(W - P, y0 + 30, "primary language of %d repos" % total, "pm", 11.5, "ink3", "end"))
    bx, by, bw, bh = P + 96, y0 + 21, W - 2 * P - 96 - 210, 10
    cid = doc.uid()
    doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s" rx="5"/></clipPath>' % (cid, bx, by, bw, bh))
    segs, x = [], bx
    for lang, c in langs:
        wd = bw * c / total
        segs.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (n(x), by, n(max(wd - 2, 1)), bh, LANG_COLORS.get(lang, "#8b949e")))
        x += wd
    grow = Track(0)
    grow.to(0, 1, dur=1.1, ease="cubic-bezier(.2,.7,.2,1)")
    gcls = doc.animate(grow, 1.1, lambda v: "transform:scaleX(%s)" % n(v), once=True, delay=0.6)
    doc.add('<g clip-path="url(#%s)"><g class="%s" style="transform-origin:%spx %spx">%s</g></g>' % (cid, gcls, bx, by, "".join(segs)))
    x = P
    for lang, c in langs:
        doc.add('<circle cx="%s" cy="%s" r="4.5" fill="%s"/>' % (n(x + 4.5), y0 + 54, LANG_COLORS.get(lang, "#8b949e")))
        doc.add(doc.text(x + 15, y0 + 58.5, lang, "psm", 13, "ink"))
        x += 15 + measure("psm", 13, lang) + 6
        pct = "%d%%" % round(100 * c / total)
        doc.add(doc.text(x, y0 + 58.5, pct, "ps", 13, "ink3"))
        x += measure("ps", 13, pct) + 22
    return doc.render()


# ============================================================================ index of work

INDEX = [
    ("HH_Goa", "Voice RAG: a 3.4 ms retrieval core inside a 200 ms budget, answering with verbatim quotes.", "JavaScript"),
    ("Saakshi", "Turns NGO field photos into verified, measured, traceable proof of impact.", "TypeScript"),
    ("Code_Flow", "Maps how a codebase fits together; every answer cites a real file and line.", "TypeScript"),
    ("GradeSense", "Explainable exam grading: every mark arrives with the evidence behind it.", "TypeScript"),
    ("TypeAhead", "Autocomplete over ~428k phrases, cached on a consistent-hashing Redis ring.", "JavaScript"),
    ("RISC-V-Instruction-Set-Explorer", "Cross-checks the RISC-V instruction dictionary against the ISA manual.", "TypeScript"),
]


def index_head(theme):
    H = 62
    doc = Doc(W, H, theme, "Index of work", "Index of work: the pinned repositories.", "ih")
    th = doc.th
    doc.add(doc.text(0, 40, "Index of work", "psb", 22, "ink", tracking=-0.02))
    doc.add(doc.text(W, 40, "%d pinned repositories" % len(INDEX), "pm", 11.5, "ink3", "end"))
    return doc.render()


def index_row(theme, i):
    name, desc, lang = INDEX[i]
    H = 66
    doc = Doc(W, H, theme, name, "%02d. %s, %s. %s" % (i + 1, name, lang, desc), "ir%d" % i)
    th = doc.th
    doc.add('<path d="M0 .5H%d" stroke="%s"/>' % (W, th["border"]))
    if i == len(INDEX) - 1:
        doc.add('<path d="M0 %sH%d" stroke="%s"/>' % (n(H - .5), W, th["border"]))
    doc.add(doc.text(0, 30, "%02d" % (i + 1), "pm", 12, "ink3"))
    doc.add(doc.text(40, 31, name, "psb", 17, "ink", tracking=-0.015))
    doc.add(doc.text(40, 52, desc, "ps", 13.5, "ink2"))
    lx = W - 130
    doc.add('<circle cx="%s" cy="27" r="5" fill="%s"/>' % (n(lx), LANG_COLORS.get(lang, "#8b949e")))
    doc.add(doc.text(lx + 12, 31.5, lang, "ps", 12.5, "ink2"))
    # the arrow nudges, each row a beat after the last
    nudge = Track((0, 0))
    nudge.to(0.2 + i * 0.12, (3, -3), dur=0.35, ease="cubic-bezier(.3,.7,.2,1)")
    nudge.to(0.75 + i * 0.12, (0, 0), dur=0.45)
    ncls = doc.animate(nudge, 4.0, tr)
    ax = W - 14
    doc.add('<g class="%s"><path d="M%s 32L%s 23M%s 23H%sV%s" fill="none" stroke="%s" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round"/></g>' % (ncls, n(ax - 9), n(ax), n(ax - 6), n(ax), n(29), th["ink2"]))
    return doc.render()


# ============================================================================ social buttons

def button(theme, label):
    th = THEMES[theme]
    tw = measure("psm", 14, label)
    w, h = int(tw + 14 + 12 + 10 + 14), 34
    doc = Doc(w, h, theme, label, label, "b" + label[:2].lower())
    bg = "#f6f8fa" if theme == "light" else "#212830"
    doc.add('<rect x=".5" y=".5" width="%s" height="%s" rx="6" fill="%s" stroke="%s"/>' % (w - 1, h - 1, bg, th["border"]))
    doc.add(doc.text(14, 22, label, "psm", 14, "ink"))
    ax = 14 + tw + 10
    doc.add('<path d="M%s 22L%s 13M%s 13H%sV%s" fill="none" stroke="%s" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>' % (
        n(ax), n(ax + 9), n(ax + 3), n(ax + 9), n(19), th["ink2"]))
    return doc.render()


# ============================================================================ off the keyboard

def shuttle(doc, cam, cx, cy, z0, s, stroke=None, mark=None):
    """A shuttlecock standing on its cork: cork, skirt, rim, feathers and the thread band."""
    th = doc.th
    rc, rb, rt = 0.32 * s, 0.3 * s, 0.95 * s
    zc, zb, zt = z0 + rc, z0 + rc * 1.55, z0 + 2.05 * s
    sb = [cam.P(x, y, zb) for x, y in circle(cx, cy, rb, 24)]
    stp = [cam.P(x, y, zt) for x, y in circle(cx, cy, rt, 36)]
    k = cam.P(cx, cy, zc)
    marks = [path(stp, True)]
    for i in range(16):
        a = 2 * math.pi * i / 16
        ux, uy = math.cos(a), math.sin(a)
        if ux * cam.st + uy * cam.ct > -0.05:
            marks.append(path([cam.P(cx + rb * ux, cy + rb * uy, zb), cam.P(cx + rt * ux, cy + rt * uy, zt)]))
    zm, rm = zb + 0.38 * (zt - zb), rb + 0.38 * (rt - rb)
    band = [(cx + rm * math.cos(a), cy + rm * math.sin(a)) for a in [j * math.pi / 30 for j in range(61)]]
    band = [p for p in band if (p[0] - cx) * cam.st + (p[1] - cy) * cam.ct > 0]
    if band:
        marks.append(path([cam.P(x, y, zm) for x, y in band]))
    st = stroke or th["edge"]
    mk = mark or th["mid"]
    return ('<g class="s" style="stroke:%s"><circle class="sil" cx="%s" cy="%s" r="%s"/><path class="sil" d="%s"/></g>'
            '<g style="stroke:%s">%s</g>') % (st, n(k[0]), n(k[1]), n(rc * cam.S), path(hull(sb + stp), True),
                                             mk, "".join('<path class="mk" d="%s"/>' % m for m in marks))


def slab(doc, cam, x0, y0, x1, y1, z0, z1, r=0.25, inset=0.14, marks="", stroke=None, mark=None, cls="", mcls=""):
    sil, cr = prism(cam, rrect(x0, y0, x1, y1, r), z0, z1, inset)
    st = ' style="stroke:%s"' % stroke if stroke else ""
    mk = ' style="stroke:%s"' % (mark or doc.th["mid"])
    return ('<g class="s %s"%s><path class="sil" d="%s"/>%s</g><g class="%s"%s>%s</g>' % (
        cls, st, sil, ('<path class="cr" d="%s"/>' % cr) if cr else "", mcls, mk, marks))


def fig_karate(doc, frame, rx, ry):
    """An articulated action figure in a gi and black belt (two green dan stripes) on a mat.
    Guard, chamber, a high roundhouse kick (mawashi geri) with its arc and impact, recoil, guard."""
    th = doc.th
    fx, fy, fw, fh = frame
    T = 3.8
    K = 1.14
    LEN = {k: v * K for k, v in dict(thigh=27, shin=26, foot=9, torso=33, neck=4, head=8.5, upper=18, fore=16).items()}
    WID = {k: v * K for k, v in dict(thigh=8.5, shin=7, foot=4.6, torso=14.5, upper=6.2, fore=5.6).items()}
    pts = box_pts(-2.5, -0.9, 2.5, 0.9, -0.2, 0)
    cam = fit(26, 31, pts, (fx + 6, fy + fh - 44, fw - 12, 44), pad=1)
    seams = "".join('<path class="mk" d="%s"/>' % flat(cam, [(x, -0.75), (x, 0.75)], 0) for x in (-0.85, 0.85))
    doc.add(slab(doc, cam, -2.5, -0.9, 2.5, 0.9, -0.2, 0, r=0.25, inset=0.12, marks=seams))
    gx, gy = cam.P(-0.25, 0, 0)

    REST = dict(torso=174, lthigh=19, lshin=6, rthigh=-21, rshin=-8, lupper=36, lfore=150, rupper=10, rfore=162)
    CHAMBER = dict(torso=188, lthigh=19, lshin=6, rthigh=94, rshin=-40, lupper=56, lfore=134, rupper=-18, rfore=150)
    EXTEND = dict(torso=212, lthigh=19, lshin=6, rthigh=128, rshin=124, lupper=74, lfore=124, rupper=-64, rfore=-32)
    KEYS = [(0.0, REST), (0.55, REST), (0.8, CHAMBER), (0.97, EXTEND), (1.22, EXTEND), (1.44, CHAMBER), (1.8, REST)]

    def dirv(a):
        r = math.radians(a)
        return math.sin(r), math.cos(r)

    def add(p, a, L):
        d = dirv(a)
        return p[0] + d[0] * L, p[1] + d[1] * L

    def fk(P):
        hip = (gx, gy - LEN["thigh"] - LEN["shin"] + 1.5)
        j = {"hip": hip}
        for side in "lr":
            j[side + "knee"] = add(hip, P[side + "thigh"], LEN["thigh"])
            j[side + "ankle"] = add(j[side + "knee"], P[side + "shin"], LEN["shin"])
            j[side + "toe"] = add(j[side + "ankle"], 90 + (P[side + "shin"] - REST[side + "shin"]), LEN["foot"])
        j["shoulder"] = add(hip, P["torso"], LEN["torso"])
        j["head"] = add(j["shoulder"], P["torso"], LEN["neck"] + LEN["head"])
        for side in "lr":
            j[side + "elbow"] = add(j["shoulder"], P[side + "upper"], LEN["upper"])
            j[side + "fist"] = add(j[side + "elbow"], P[side + "fore"], LEN["fore"])
        return j

    J = fk(REST)

    def capsule(p, q, w, cls="sil"):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        r = w / 2
        return ('<path class="%s" d="M%s %sL%s %sA%s %s 0 0 1 %s %sL%s %sA%s %s 0 0 1 %s %sZ"/>' % (
            cls, n(p[0] + nx), n(p[1] + ny), n(q[0] + nx), n(q[1] + ny), n(r), n(r), n(q[0] - nx), n(q[1] - ny),
            n(p[0] - nx), n(p[1] - ny), n(r), n(r), n(p[0] + nx), n(p[1] + ny)))

    def ball(p, r):
        return '<circle class="jt" cx="%s" cy="%s" r="%s"/>' % (n(p[0]), n(p[1]), n(r))

    def rot_track(get):
        """CSS rotation (degrees, clockwise) for one joint, as a delta from the rest pose."""
        t = Track(0)
        prev = 0.0
        for when, P in KEYS[1:]:
            v = -(get(P) - get(REST))
            t.to(prev, round(v, 2), dur=when - prev, ease="cubic-bezier(.45,0,.2,1)")
            prev = when
        return doc.animate(t, T, lambda v: "transform:rotate(%sdeg)" % n(v))

    def joint(cls, at, inner):
        return '<g class="%s" style="transform-origin:%spx %spx">%s</g>' % (cls, n(at[0]), n(at[1]), inner)

    doc.css.append(".jt{fill:%s;stroke:%s;stroke-width:.9}" % (th["plate"], th["mid"]))

    def leg(side, lit_cls=""):
        thigh = capsule(J["hip"], J[side + "knee"], WID["thigh"])
        shin = capsule(J[side + "knee"], J[side + "ankle"], WID["shin"]) + capsule(J[side + "ankle"], J[side + "toe"], WID["foot"])
        knee = joint(rot_track(lambda P: P[side + "shin"] - P[side + "thigh"]), J[side + "knee"], shin + ball(J[side + "knee"], 2.8))
        return joint(rot_track(lambda P: P[side + "thigh"]), J["hip"],
                     '<g class="s %s">%s%s</g>' % (lit_cls, thigh, knee))

    def arm(side):
        upper = capsule(J["shoulder"], J[side + "elbow"], WID["upper"])
        fore = capsule(J[side + "elbow"], J[side + "fist"], WID["fore"]) + '<circle class="sil" cx="%s" cy="%s" r="3.6"/>' % (
            n(J[side + "fist"][0]), n(J[side + "fist"][1]))
        elbow = joint(rot_track(lambda P: (P[side + "fore"] - P[side + "upper"])), J[side + "elbow"], fore + ball(J[side + "elbow"], 2.4))
        return joint(rot_track(lambda P: (P[side + "upper"] - P["torso"])), J["shoulder"],
                     '<g class="s">%s%s</g>' % (upper, elbow))

    # torso, head, gi lapel and the belt
    hip, sh = J["hip"], J["shoulder"]
    tv = dirv(REST["torso"])
    perp = (-tv[1], tv[0])
    lapel = path([(sh[0] + perp[0] * -5, sh[1] + perp[1] * -5), (hip[0] + tv[0] * 9 + perp[0] * 4, hip[1] + tv[1] * 9 + perp[1] * 4)])
    belt_c = (hip[0] + tv[0] * 4, hip[1] + tv[1] * 4)
    bp = (belt_c[0] + perp[0] * 8.5, belt_c[1] + perp[1] * 8.5)
    bq = (belt_c[0] - perp[0] * 8.5, belt_c[1] - perp[1] * 8.5)
    knot = bq if bq[0] > bp[0] else bp
    belt_fill = "#010409" if doc.theme == "dark" else "#1f2328"
    t1 = (knot[0] + 3, knot[1] + 12)
    t2 = (knot[0] + 7.5, knot[1] + 10)
    stripes = "".join('<path d="M%s %sL%s %s" stroke="%s" stroke-width="1.6" stroke-linecap="round"/>' % (
        n(knot[0] + (t2[0] - knot[0]) * f - 2.4), n(knot[1] + (t2[1] - knot[1]) * f + 1.2),
        n(knot[0] + (t2[0] - knot[0]) * f + 2.4), n(knot[1] + (t2[1] - knot[1]) * f - 1.2), th["hi"]) for f in (0.62, 0.8))
    flick = Track(0)
    for when, v in ((0.8, 0), (0.97, -16), (1.22, -10), (1.5, 6), (1.8, -2), (2.1, 0)):
        flick.to(flick.pts[-1][0], v, dur=max(when - flick.pts[-1][0], 0.001), ease="cubic-bezier(.45,0,.55,1)")
    fcls = doc.animate(flick, T, lambda v: "transform:rotate(%sdeg)" % n(v))
    belt = ('<g class="s">%s</g>' % capsule(bp, bq, 4.6).replace('class="sil"', 'class="sil" style="fill:%s"' % belt_fill) +
            joint(fcls, knot, '<g class="s">%s%s</g>%s' % (
                capsule(knot, t1, 3.2).replace('class="sil"', 'class="sil" style="fill:%s"' % belt_fill),
                capsule(knot, t2, 3.2).replace('class="sil"', 'class="sil" style="fill:%s"' % belt_fill), stripes)))
    torso = ('<g class="s">%s<circle class="sil" cx="%s" cy="%s" r="%s"/></g>' % (
        capsule(hip, sh, WID["torso"]), n(J["head"][0]), n(J["head"][1]), LEN["head"]) +
        '<g class="mg"><path class="mk" d="%s"/></g>' % lapel)
    upper_body = joint(rot_track(lambda P: P["torso"]), J["hip"], arm("r") + torso + belt + ball(sh, 3) + arm("l"))

    # the kick's arc and its impact, computed from the same skeleton
    def lerp(P, Q, u):
        return {k: P[k] + (Q[k] - P[k]) * u for k in P}
    arc = [fk(lerp(CHAMBER, EXTEND, u / 12.0))["rtoe"] for u in range(13)]
    trail = Track(0)
    trail.step(0.82, 0.85, fade=0.12)
    trail.step(1.3, 0, fade=0.35)
    tcls = doc.animate(trail, T, lambda v: "opacity:%s" % n(v))
    doc.add('<path class="%s" d="%s" fill="none" stroke="%s" stroke-width="1.2" stroke-dasharray="2.5 3" opacity="0" style="vector-effect:none"/>' % (
        tcls, path(arc), th["hi"]))
    hit = fk(EXTEND)["rtoe"]
    rip = Track((0.4, 0))
    rip.step(0.97, (0.4, 0.9), fade=0.04)
    rip.to(1.01, (2.0, 0), dur=0.55, ease="cubic-bezier(.2,.7,.3,1)")
    rip.step(1.7, (0.4, 0), fade=0)
    rcls = doc.animate(rip, T, lambda v: "transform:scale(%s);opacity:%s" % (n(v[0]), n(v[1])))

    kick_lit = lit_track(doc, False, [(0.95, True), (1.4, False)], T, th["hi"], th["edge"])
    doc.add(leg("l") + upper_body + leg("r", kick_lit))
    for r0 in (7, 12):
        doc.add('<circle class="%s" cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.2" opacity="0" '
                'style="transform-origin:%spx %spx"/>' % (rcls, n(hit[0]), n(hit[1]), r0, th["hi"], n(hit[0]), n(hit[1])))
    doc.add(readouts(doc, rx, ry, [(0, 0, "dan 2"), (0.8, 1.9, "mawashi geri")], T, size=11.5))


def fig_badminton(doc, frame, rx, ry):
    """A shuttle rallying over the net."""
    th = doc.th
    L, R, Y0, Y1, APEX, LOW, NX = 1.1, 6.1, 1.95, 1.25, 2.7, 0.3, 3.6
    s = 0.62
    pts = box_pts(0, 0, 7.2, 3.2, -0.2, APEX + 2.05 * s + 0.1)
    cam = fit(30, 31, pts, frame, pad=2)
    court = [flat(cam, rrect(0.3, 0.3, 6.9, 2.9, 0.05, 1), 0, True)] + [flat(cam, seg, 0) for seg in (
        [(2.55, 0.3), (2.55, 2.9)], [(4.65, 0.3), (4.65, 2.9)], [(0.3, 1.6), (2.55, 1.6)], [(4.65, 1.6), (6.9, 1.6)])]
    doc.add(slab(doc, cam, 0, 0, 7.2, 3.2, -0.2, 0, r=0.3, inset=0.16,
                 marks="".join('<path class="mk" d="%s"/>' % c for c in court)))
    for py in (-0.05, 3.25):
        doc.add(slab(doc, cam, NX - 0.06, py - 0.06, NX + 0.06, py + 0.06, 0, 1.55, r=0.03, inset=0))
    mesh = [path([cam.P(NX, y, 0.78), cam.P(NX, y, 1.5)]) for y in [0.05 + i * 0.3 for i in range(11)]]
    mesh += [path([cam.P(NX, -0.05, z), cam.P(NX, 3.25, z)]) for z in (0.78, 1.02, 1.26)]
    doc.add('<g class="mg">%s</g>' % "".join('<path class="mk" d="%s"/>' % m for m in mesh))
    doc.add('<path class="sil" fill="none" stroke="%s" d="%s"/>' % (th["edge"], path([cam.P(NX, -0.05, 1.5), cam.P(NX, 3.25, 1.5)])))

    def at(u, x0, y0, x1, y1):
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        return x, y, LOW + (APEX - LOW) * (1 - (2 * u - 1) ** 2)

    base = (NX, (Y0 + Y1) / 2, APEX)

    def off(p):
        return cam.d(p[0] - base[0], p[1] - base[1], p[2] - base[2])

    t = Track(off(base))
    seq, clock, step, K = [], 0.0, 0.052, 24
    for u in [0.5 + i / K for i in range(1, K // 2 + 1)]:              # apex -> right, low
        clock += step; seq.append((clock, at(u, L, Y0, R, Y1)))
    clock += 0.18
    for u in [i / K for i in range(1, K + 1)]:                         # right -> left
        clock += step; seq.append((clock, at(u, R, Y1, L, Y0)))
    clock += 0.18
    for u in [i / K for i in range(1, K // 2 + 1)]:                    # left -> apex
        clock += step; seq.append((clock, at(u, L, Y0, R, Y1)))
    prev = 0.0
    for when, p in seq:
        t.to(prev, off(p), dur=when - prev, ease="linear")
        prev = when
    T = round(prev + 0.001, 3)
    cls = doc.animate(t, T, tr)
    doc.add('<g class="%s">%s</g>' % (cls, shuttle(doc, cam, base[0], base[1], base[2], s, th["hi"], th["hi"])))
    half = (K // 2) * step
    doc.add(readouts(doc, rx, ry, [(0, 0, "rally"), (0.01, half + 0.1, "smash"),
                                   (half + 0.18, half + 0.18 + K * step, "clear")], T, size=11.5))


def fig_films(doc, frame, rx, ry):
    """A reel turning, and a strip of film running under a lit gate."""
    th = doc.th
    pts = box_pts(-0.2, -0.2, 7.4, 3.4, -0.2, 3.3)
    cam = fit(30, 31, pts, frame, pad=2)
    doc.add(slab(doc, cam, -0.2, -0.2, 7.4, 3.4, -0.2, 0, r=0.3, inset=0.16))
    doc.add(slab(doc, cam, 1.15, 0.25, 1.95, 0.85, 0, 0.32, r=0.1, inset=0.06))
    cx, cz, R = 1.55, 1.78, 1.42
    ax, ay = cam.d(dx=1)
    bx, by = cam.d(dz=1)
    for yy, spin in ((0.3, False), (0.62, True)):
        ex, ey = cam.P(cx, yy, cz)
        inner = ""
        if spin:
            parts = ['<circle class="mk" r="1.24"/>', '<circle class="mk" r=".2"/>']
            parts += ['<circle class="mk" cx="%s" cy="%s" r=".3"/>' % (n(0.74 * math.cos(a)), n(0.74 * math.sin(a)))
                      for a in [i * 2 * math.pi / 5 for i in range(5)]]
            inner = '<g class="spin" style="stroke:%s">%s</g>' % (th["mid"], "".join(parts))
        doc.add('<g transform="matrix(%s %s %s %s %s %s)"><circle class="sil" r="%s" style="fill:%s;stroke:%s"/>%s</g>' % (
            n(ax), n(ay), n(bx), n(by), n(ex), n(ey), n(R), th["plate"], th["edge"], inner))
    doc.css.append("@keyframes reel{to{transform:rotate(360deg)}}.spin{animation:reel 4.5s linear infinite}")
    Y0, Y1, Z = 1.5, 2.8, 0.06
    doc.add(slab(doc, cam, 0.2, Y0, 7.0, Y1, 0, Z, r=0.04, inset=0))
    clip = doc.uid()
    doc.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (clip, flat(cam, [(0.25, Y0), (6.95, Y0), (6.95, Y1), (0.25, Y1)], Z, True)))
    P = 1.1
    run = []
    for k in range(-1, 8):
        x = k * P
        run.append(flat(cam, rrect(x + 0.18, Y0 + 0.24, x + 0.92, Y1 - 0.24, 0.05, 1), Z, True))
        for h in range(4):
            hx = x + 0.08 + h * 0.275
            for hy in (Y0 + 0.06, Y1 - 0.16):
                run.append(flat(cam, rrect(hx, hy, hx + 0.12, hy + 0.1, 0.02, 1), Z, True))
    t = Track((0, 0))
    t.to(0, cam.d(dx=P), dur=0.7, ease="linear")
    cls = doc.animate(t, 0.7, tr, wrap=True)
    doc.add('<g clip-path="url(#%s)"><g class="%s mg">%s</g></g>' % (clip, cls, "".join('<path class="mk" d="%s"/>' % r for r in run)))
    doc.add('<path class="mk" style="stroke:%s" d="%s"/>' % (th["hi"], flat(cam, rrect(3.4, Y0 + 0.14, 4.32, Y1 - 0.14, 0.06, 2), Z + 0.01, True)))
    genres = ["thriller", "anime", "rom-com", "documentary", "horror", "sci-fi", "all of it"]
    T = 1.2 * len(genres)
    items = [(0, 0, genres[-1])] + [(i * 1.2 + 0.01, (i + 1) * 1.2, g) for i, g in enumerate(genres[:-1])]
    doc.add(readouts(doc, rx, ry, items, T, size=11.5))


OFF = [
    ("Badminton", "Plays for the state. Smashes returned with interest.", fig_badminton),
    ("Films", "Every genre. Always stays for the post-credits scene.", fig_films),
]


def offkeys(theme):
    H = 300
    doc = Doc(W, H, theme, "Off the keyboard",
              "Off the keyboard: badminton, played for the state; films, every genre.", "o")
    frame_box(doc, H)
    doc.add(doc.text(28, 50, "Off the keyboard", "psb", 22, "ink", tracking=-0.02))
    gap, x0 = 40, 28
    cw = (W - 2 * x0 - gap * (len(OFF) - 1)) / len(OFF)
    for i, (title, sub, fig) in enumerate(OFF):
        x = x0 + i * (cw + gap)
        fig(doc, (x, 64, cw, 168), x + cw, 254)
        doc.add(doc.text(x, 254, title, "psm", 15, "ink"))
        doc.add(doc.text(x, 276, sub, "ps", 13.5, "ink2"))
    return doc.render()


# ============================================================================ karate: the motion study

def karate(theme):
    """Adapted from Anshul's own motion study (scripts/media/karate-src.svg): a flying side kick,
    ghosted frames, three boards. Name and rank filled in, unverifiable figures replaced, recoloured
    to the profile's palette, and a light version made from the same drawing."""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "karate-src.svg")).read()
    src = src.replace(' xmlns:c2pa="http://c2pa.org/manifest"', "")
    src = src.replace('width="900" height="300"', 'width="840" height="280"', 1)
    swaps = [
        ("<title id=\"t\">Your Name, karate black belt</title>", "<title id=\"t\">Anshul Mohanty, 2nd dan black belt</title>"),
        ("and the contact height is measured at 1.47 metres.", "and lands. Breaks boards, not builds."),
        (">Your Name<", ">Anshul Mohanty<"),
        (">Black belt<", ">Black belt, 2nd dan<"),
        (">Style<", ">Kick<"),
        (">Shotokan<", ">Yoko tobi geri<"),
        (">Contact height<", ">Contact<"),
        ('text-anchor="end">1.47 m<', 'text-anchor="end">Head height<'),
        (">1.47 m<", ">contact<"),
    ]
    for a, b in swaps:
        if a not in src:
            raise ValueError("karate source changed: %r not found" % a)
        src = src.replace(a, b)
    th = THEMES[theme]
    colours = {"#d29922": th["hi"]}
    if theme == "light":
        colours.update({"#0d1117": "#ffffff", "#30363d": "#d1d9e0", "#7d8590": "#59636e", "#e6edf3": "#1f2328"})
    for a, b in colours.items():
        src = src.replace(a, b).replace(a.upper(), b)
    return src


# ============================================================================ avatar

THEMES_AVATAR = dict(plate="#0d1117", hi="#3fb950", edge="#aab3bd", mid="#58616c", lo="#262c36",
                     ink="#f0f6fc", ink2="#9198a1", ink3="#6b737d", accent="#4493f8", border="#3d444d",
                     subtle="#151b23", sel="#f0f6fc", g=[])


def avatar_svg():
    """The profile picture: a black belt with its two stripes, a film reel, a shuttlecock."""
    th = dict(THEMES_AVATAR)
    doc = Doc(460, 460, "dark", "Avatar", "Avatar", "a")
    doc.th = th
    doc.add('<rect width="460" height="460" fill="%s"/>' % th["plate"])
    pts = box_pts(0, 0, 8, 8, -0.45, 3.6)
    cam = fit(40, 31, pts, (44, 58, 372, 352), pad=0)
    doc.add(slab(doc, cam, 0, 0, 8, 8, -0.45, 0, r=0.75, inset=0.25))
    doc.add(shuttle(doc, cam, 2.0, 2.3, 0, 1.55))
    doc.add(slab(doc, cam, 5.25, 1.15, 6.25, 1.85, 0, 0.35, r=0.1, inset=0.06))
    ax, ay = cam.d(dx=1)
    bx, by = cam.d(dz=1)
    for yy, front in ((1.2, False), (1.62, True)):
        ex, ey = cam.P(5.75, yy, 2.05)
        inner = ""
        if front:
            inner = '<g style="stroke:%s">%s</g>' % (th["mid"], '<circle class="mk" r="1.45"/><circle class="mk" r=".24"/>' + "".join(
                '<circle class="mk" cx="%s" cy="%s" r=".36"/>' % (n(0.86 * math.cos(a)), n(0.86 * math.sin(a))) for a in [i * 2 * math.pi / 5 + 0.3 for i in range(5)]))
        doc.add('<g transform="matrix(%s %s %s %s %s %s)"><circle class="sil" r="1.66" style="fill:%s;stroke:%s"/>%s</g>' % (
            n(ax), n(ay), n(bx), n(by), n(ex), n(ey), th["plate"], th["edge"], inner))
    doc.add(slab(doc, cam, 0.9, 4.9, 7.0, 6.2, 0, 0.22, r=0.18, inset=0.08))
    stripes = "".join('<path class="mk" d="%s"/>' % flat(cam, [(x, 5.0), (x, 6.1)], 0.44) for x in (5.85, 6.25))
    doc.add(slab(doc, cam, 1.4, 4.9, 7.0, 6.2, 0.22, 0.44, r=0.18, inset=0.08, marks=stripes, mark=th["hi"]))
    svg = doc.render()
    return svg.replace("stroke-width:.95", "stroke-width:2.6").replace("stroke-width:.9", "stroke-width:2")


def write(name, fn):
    os.makedirs(ASSETS, exist_ok=True)
    for theme in ("light", "dark"):
        p = os.path.join(ASSETS, "%s-%s.svg" % (name, theme))
        with open(p, "w") as fh:
            fh.write(fn(theme))
        print("wrote", os.path.relpath(p, ROOT), os.path.getsize(p), "bytes")


FIGURES = {"hero": hero, "voice-rag": voice, "saakshi": saakshi, "codeflow": codeflow, "stack": stack,
           "off-the-keyboard": offkeys,
           "btn-linkedin": lambda t: button(t, "LinkedIn"), "btn-x": lambda t: button(t, "Follow on X"),
           "btn-repos": lambda t: button(t, "All repositories"), "karate": karate, "index": index_head}
for _i in range(len(INDEX)):
    FIGURES["index-%02d" % (_i + 1)] = (lambda k: (lambda t: index_row(t, k)))(_i)

if __name__ == "__main__":
    only = sys.argv[1:] or list(FIGURES)
    for name in only:
        write(name, FIGURES[name])
