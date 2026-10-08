"""
Hairline-style isometric line figures, written as static SVG files that GitHub can show.

The look follows Hairline by Lucas Marques (MIT, hairline.lucasmarkes.com): rounded solids
drawn as one silhouette and one dim crease, opaque plates in the page colour, and a single
bright stroke for whatever is chosen. GitHub renders README images with no JavaScript and
no pointer, so a "ghost pointer" timeline drives each figure with CSS keyframes instead.

Standard library only, so the GitHub Action can run it without installing anything.
"""
import base64
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
EASE = "cubic-bezier(.45,.05,.25,1)"  # soft in, soft out

# Plates take GitHub's own page colour, so a figure sits on the profile with no box.
THEMES = {
    "light": dict(plate="#ffffff", hi="#1a7f37", edge="#a3acb6", mid="#d1d9e0", lo="#e9ecef",
                  ink="#1f2328", ink2="#59636e", ink3="#818b98", accent="#0969da", border="#d1d9e0",
                  subtle="#f6f8fa", sel="#1f2328",
                  g=["#eff2f5", "#4ac26b", "#2da44e", "#1a7f37", "#116329"]),
    "dark": dict(plate="#0d1117", hi="#3fb950", edge="#5b6470", mid="#343b45", lo="#1f252d",
                 ink="#f0f6fc", ink2="#9198a1", ink3="#6b737d", accent="#4493f8", border="#3d444d",
                 subtle="#151b23", sel="#f0f6fc",
                 g=["#151b23", "#196c2e", "#2ea043", "#3fb950", "#56d364"]),
}

FONTS = {
    "serif": ("Instrument Serif", "normal", 400, "instrumentserif-400"),
    "serifi": ("Instrument Serif", "italic", 400, "instrumentserif-italic"),
    "sans": ("Geist", "normal", 400, "geist-400"),
    "sansm": ("Geist", "normal", 500, "geist-500"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400"),
    "ps": ("Profile Sans", "normal", 400, "monasans-400"),
    "psm": ("Profile Sans", "normal", 500, "monasans-500"),
    "psb": ("Profile Sans", "normal", 650, "monasans-650"),
    "pm": ("Profile Mono", "normal", 400, "monaspace-400"),
}
SYS = {"sans": "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif",
       "serif": "Georgia,'Times New Roman',serif",
       "mono": "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"}
_METRICS = None


def metrics():
    global _METRICS
    if _METRICS is None:
        with open(os.path.join(FONT_DIR, "metrics.json")) as fh:
            _METRICS = json.load(fh)
    return _METRICS


def measure(font, size, text, tracking=0.0):
    m = metrics()[FONTS[font][3]]
    w = sum(m["w"].get(c, m["w"].get(" ", 250)) for c in text)
    return w / m["upm"] * size + tracking * size * max(len(text) - 1, 0)


def wrap(font, size, text, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and measure(font, size, trial) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(v):
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ----------------------------------------------------------------------------- geometry

class Cam:
    """Orthographic camera. World x and y lie on the ground, z points up."""

    def __init__(self, theta=36.0, phi=31.0, S=20.0, ox=0.0, oy=0.0):
        t, p = math.radians(theta), math.radians(phi)
        self.ct, self.st = math.cos(t), math.sin(t)
        self.sp, self.cp = math.sin(p), math.cos(p)
        self.S, self.ox, self.oy = S, ox, oy

    def P(self, x, y, z=0.0):
        return (self.ox + self.S * (x * self.ct - y * self.st),
                self.oy + self.S * ((x * self.st + y * self.ct) * self.sp - z * self.cp))

    def d(self, dx=0.0, dy=0.0, dz=0.0):
        """Screen offset of a world move, for CSS translate."""
        return (self.S * (dx * self.ct - dy * self.st),
                self.S * ((dx * self.st + dy * self.ct) * self.sp - dz * self.cp))

    def depth(self, x, y):
        return x * self.st + y * self.ct


def rrect(x0, y0, x1, y1, r, steps=4):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = []
    for cx, cy, a0, a1 in ((x1 - r, y0 + r, -90, 0), (x1 - r, y1 - r, 0, 90),
                           (x0 + r, y1 - r, 90, 180), (x0 + r, y0 + r, 180, 270)):
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def hull(pts):
    """Convex hull (monotone chain) of screen points, counter-clockwise."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def circle(cx, cy, r, steps=40):
    return [(cx + r * math.cos(2 * math.pi * i / steps), cy + r * math.sin(2 * math.pi * i / steps))
            for i in range(steps)]


def _runs(cam, ring):
    sp = [cam.P(x, y) for x, y in ring]
    k = len(sp)
    L = min(range(k), key=lambda i: (round(sp[i][0], 6), sp[i][1]))
    R = max(range(k), key=lambda i: (round(sp[i][0], 6), -sp[i][1]))
    a = [(L + j) % k for j in range((R - L) % k + 1)]
    b = [(R + j) % k for j in range((L - R) % k + 1)]
    ya = sum(sp[i][1] for i in a) / len(a)
    yb = sum(sp[i][1] for i in b) / len(b)
    if ya <= yb:
        return a, b                      # back L->R, front R->L
    return list(reversed(b)), list(reversed(a))


def path(pts, closed=False):
    if not pts:
        return ""
    out = "M%s %s" % (n(pts[0][0]), n(pts[0][1]))
    out += "".join("L%s %s" % (n(x), n(y)) for x, y in pts[1:])
    return out + ("Z" if closed else "")


def prism(cam, ring, z0, z1, inset=0.0):
    """Silhouette (top ring's back run + base ring's front run) and the one dim crease."""
    back, front = _runs(cam, ring)
    top = [cam.P(x, y, z1) for x, y in ring]
    bot = [cam.P(x, y, z0) for x, y in ring]
    sil = path([top[i] for i in back] + [bot[i] for i in front], True)
    crease = ""
    if inset > 0 and z1 > z0:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        inner = []
        for x, y in ring:  # pull each point toward the centre along the box axes
            inner.append((x - math.copysign(min(inset, abs(x - cx)), x - cx),
                          y - math.copysign(min(inset, abs(y - cy)), y - cy)))
        ib, ifr = _runs(cam, inner)
        it = [cam.P(x, y, z1) for x, y in inner]
        crease = path([it[i] for i in ifr])
    return sil, crease


def base_front(cam, ring, z0):
    """The base ring's front run, for clipping things that grow out of the floor."""
    _, front = _runs(cam, ring)
    return [cam.P(ring[i][0], ring[i][1], z0) for i in front]


def flat(cam, pts, z=0.0, closed=False):
    return path([cam.P(x, y, z) for x, y in pts], closed)


# ----------------------------------------------------------------------------- animation

class Track:
    """Keyframes for one CSS property, built from choices on a timeline (seconds)."""

    def __init__(self, v0):
        self.v0 = v0
        self.pts = [[0.0, v0, "linear"]]

    @property
    def v(self):
        return self.pts[-1][1]

    def to(self, t, v, dur=0.55, ease=EASE):
        tl, vl, _ = self.pts[-1]
        t = max(t, tl)
        if t > tl + 1e-6:
            self.pts[-1][2] = "linear"
            self.pts.append([t, vl, ease])
        else:
            self.pts[-1][2] = ease
        self.pts.append([t + dur, v, "linear"])
        return self

    def step(self, t, v, fade=0.2):
        """Hold, then change to v; colours and opacity crossfade over `fade` seconds."""
        tl, vl, _ = self.pts[-1]
        if v == vl:
            return self
        t = max(t, tl + 0.001)
        if fade <= 0:
            self.pts[-1][2] = "steps(1,end)"
            self.pts.append([t, v, "linear"])
            return self
        if t > tl + 1e-6:
            self.pts[-1][2] = "linear"
            self.pts.append([t, vl, "ease-in-out"])
        else:
            self.pts[-1][2] = "ease-in-out"
        self.pts.append([t + fade, v, "linear"])
        return self

    def moving(self):
        return any(p[1] != self.v0 for p in self.pts)

    def css(self, name, T, fmt):
        pts = [p[:] for p in self.pts]
        if pts[-1][0] > T + 1e-6:
            raise ValueError("track runs past the loop: %s > %s" % (pts[-1][0], T))
        if pts[-1][0] < T - 1e-6:
            pts.append([T, pts[-1][1], "linear"])
        frames, last = [], -1.0
        for t, v, timing in pts:
            pct = round(t / T * 100, 3)
            if pct <= last:
                pct = round(last + 0.001, 3)
            last = pct
            frames.append("%s%%{%s;animation-timing-function:%s}" % (n(pct) if pct != int(pct) else int(pct), fmt(v), timing))
        return "@keyframes %s{%s}" % (name, "".join(frames))


def tr(v):
    return "transform:translate(%spx,%spx)" % (n(v[0]), n(v[1]))


# ----------------------------------------------------------------------------- document

class Doc:
    def __init__(self, w, h, theme, title, desc, prefix):
        self.w, self.h, self.th = w, h, THEMES[theme]
        self.theme = theme
        self.title, self.desc, self.prefix = title, desc, prefix
        self.css, self.defs, self.body = [], [], []
        self.fonts = set()
        self.k = 0

    def uid(self):
        self.k += 1
        return "%s%d" % (self.prefix, self.k)

    def c(self, key):
        return self.th[key]

    def add(self, s):
        self.body.append(s)

    def animate(self, track, T, fmt, once=False, delay=0.0, wrap=False):
        """Return a class name that plays this track (or '' if it never changes)."""
        if not track.moving():
            return ""
        if not once and not wrap:  # wrap: a pattern that repeats exactly one period on
            a, b = track.pts[-1][1], track.v0
            same = (abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01) if isinstance(a, tuple) else a == b
            if not same:
                raise ValueError("loop does not return to rest: %r -> %r" % (b, a))
        name = self.uid()
        self.css.append(track.css(name, T, fmt))
        if once:
            self.css.append(".%s{animation:%s %ss linear %ss both}" % (name, name, n(T), n(delay)))
        else:
            self.css.append(".%s{animation:%s %ss linear infinite}" % (name, name, n(T)))
        return name

    def animate_many(self, specs, T):
        """Several tracks on one element: one class, one comma-joined animation list."""
        names = []
        for track, fmt in specs:
            if not track.moving():
                continue
            nm = self.uid()
            self.css.append(track.css(nm, T, fmt))
            names.append(nm)
        if not names:
            return ""
        cls = self.uid()
        self.css.append(".%s{animation:%s}" % (cls, ",".join("%s %ss linear infinite" % (nm, n(T)) for nm in names)))
        return cls

    def text(self, x, y, s, font="sans", size=16, fill="ink", anchor="start", tracking=0.0, cls="", opacity=None):
        self.fonts.add(font)
        fam, style, weight, _ = FONTS[font]
        attrs = ['x="%s"' % n(x), 'y="%s"' % n(y), 'class="f-%s%s"' % (font, (" " + cls) if cls else ""),
                 'font-size="%s"' % n(size), 'fill="%s"' % self.c(fill)]
        if anchor != "start":
            attrs.append('text-anchor="%s"' % anchor)
        if tracking:
            attrs.append('letter-spacing="%sem"' % n(tracking))
        if opacity is not None:
            attrs.append('opacity="%s"' % n(opacity))
        return "<text %s>%s</text>" % (" ".join(attrs), esc(s))

    def render(self):
        th = self.th
        faces = []
        for f in sorted(self.fonts):
            fam, style, weight, key = FONTS[f]
            with open(os.path.join(FONT_DIR, key + ".woff2"), "rb") as fh:
                data = base64.b64encode(fh.read()).decode()
            faces.append("@font-face{font-family:'%s';font-style:%s;font-weight:%d;"
                         "src:url(data:font/woff2;base64,%s) format('woff2')}" % (fam, style, weight, data))
            fb = SYS["mono"] if f in ("mono", "pm") else SYS["serif"] if f.startswith("serif") else SYS["sans"]
            faces.append(".f-%s{font-family:'%s',%s;font-style:%s;font-weight:%d}" % (f, fam, fb, style, weight))
        base = (
            "path,line,ellipse,circle,polyline{vector-effect:non-scaling-stroke}"
            ".s{stroke:%(edge)s}.s>.sil{fill:%(plate)s}"
            ".sil{stroke-width:.95;stroke-linejoin:round}"
            ".cr{fill:none;stroke:%(mid)s;stroke-width:.9;stroke-linecap:round}"
            ".mk{fill:none;stroke-width:.9;stroke-linecap:round;stroke-linejoin:round}.mg{stroke:%(mid)s}.dot{stroke:none}"
            ".gd{fill:none;stroke:%(lo)s;stroke-width:.9;stroke-linecap:round}"
            ".dash{stroke-dasharray:2.5 3}"
            "text{font-kerning:normal;font-feature-settings:'kern','calt'}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        ) % th
        css = "".join(faces) + base + "".join(self.css)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'role="img" aria-labelledby="%st %sd">'
            '<title id="%st">%s</title><desc id="%sd">%s</desc>'
            "<style>%s</style><defs>%s</defs>%s</svg>"
        ) % (self.w, self.h, self.w, self.h, self.prefix, self.prefix, self.prefix, esc(self.title),
             self.prefix, esc(self.desc), css, "".join(self.defs), "".join(self.body))


def fit(theta, phi, pts, frame, pad=6.0):
    """Camera that fits every world point (rest and most extreme poses) inside frame=(x,y,w,h)."""
    c = Cam(theta, phi, 1.0, 0.0, 0.0)
    sp = [c.P(*p) for p in pts]
    x0, x1 = min(p[0] for p in sp), max(p[0] for p in sp)
    y0, y1 = min(p[1] for p in sp), max(p[1] for p in sp)
    fx, fy, fw, fh = frame
    S = min((fw - 2 * pad) / (x1 - x0), (fh - 2 * pad) / (y1 - y0))
    ox = fx + (fw - S * (x1 - x0)) / 2 - S * x0
    oy = fy + (fh - S * (y1 - y0)) / 2 - S * y0
    return Cam(theta, phi, S, ox, oy)


def box_pts(x0, y0, x1, y1, z0, z1):
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


# ----------------------------------------------------------------------------- solids

def solid(doc, cam, ring, z0, z1, inset=0.18, sil_cls="", extra="", stroke=None):
    """One opaque rounded solid. `stroke` overrides the silhouette colour (e.g. hi at rest)."""
    sil, crease = prism(cam, ring, z0, z1, inset)
    style = ' style="stroke:%s"' % stroke if stroke else ""
    out = '<g class="s %s"%s>' % (sil_cls, style)
    out += '<path class="sil" d="%s"/>' % sil
    if crease:
        out += '<path class="cr" d="%s"/>' % crease
    out += extra + "</g>"
    return out
