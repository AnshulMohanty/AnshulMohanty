"""
Redraws assets/contributions-{light,dark}.svg from the public contribution calendar.

    python3 scripts/contributions.py AnshulMohanty

Runs daily from .github/workflows/contributions.yml. Standard library only. If the
calendar cannot be read, it exits with an error and leaves the existing figures alone.
"""
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hairline import Doc, Track, EASE, fit, box_pts, rrect, circle, prism, flat, path, base_front, tr, n, measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = 840
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ----------------------------------------------------------------------------- data

def _get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=dict({"User-Agent": "profile-figure (python urllib)"}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def from_page(user):
    s = _get("https://github.com/users/%s/contributions" % user, {"Accept": "text/html"})
    tips = {}
    for attrs, text in re.findall(r"<tool-tip([^>]*)>([^<]*)</tool-tip>", s):
        m = re.search(r'for="([^"]+)"', attrs)
        if m:
            tips[m.group(1)] = text.strip()
    days = {}
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", s):
        date = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        cid = re.search(r'id="([^"]+)"', tag)
        if not date:
            continue
        tip = tips.get(cid.group(1) if cid else "", "")
        m = re.match(r"([\d,]+) contributions?", tip)
        days[date.group(1)] = int(m.group(1).replace(",", "")) if m else 0
    return days


def from_api(user, token):
    q = ('query($u:String!){user(login:$u){contributionsCollection{contributionCalendar'
         '{weeks{contributionDays{date contributionCount}}}}}}')
    body = json.dumps({"query": q, "variables": {"u": user}}).encode()
    s = _get("https://api.github.com/graphql", {"Authorization": "bearer " + token,
                                                 "Content-Type": "application/json"}, body)
    weeks = json.loads(s)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def from_viewer(token):
    """The token owner's own calendar: works even when the profile is set to private."""
    q = "query{viewer{contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"
    s = _get("https://api.github.com/graphql", {"Authorization": "bearer " + token,
                                                 "Content-Type": "application/json"}, json.dumps({"query": q}).encode())
    weeks = json.loads(s)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def fetch(user):
    days = {}
    own = os.environ.get("CONTRIB_TOKEN")          # a personal token: needed if the profile is private
    if own:
        try:
            days = from_viewer(own)
        except Exception as e:  # noqa: BLE001
            print("viewer graphql failed:", e, file=sys.stderr)
    if len(days) < 300:
        try:
            days = from_page(user)
        except Exception as e:  # noqa: BLE001
            print("calendar page failed:", e, file=sys.stderr)
    if len(days) < 300 and os.environ.get("GITHUB_TOKEN"):
        try:
            days = from_api(user, os.environ["GITHUB_TOKEN"])
        except Exception as e:  # noqa: BLE001
            print("graphql failed:", e, file=sys.stderr)
    if len(days) < 300:
        raise SystemExit("could not read the contribution calendar for %s" % user)
    return sorted((dt.date.fromisoformat(k), v) for k, v in days.items())


def fetch_languages(user):
    """Primary language of each public, non-fork repo, and the public repo count. None on failure."""
    repos = []
    token = os.environ.get("GITHUB_TOKEN")
    try:
        page = 1
        while True:
            hdr = {"Accept": "application/vnd.github+json"}
            if token:
                hdr["Authorization"] = "bearer " + token
            batch = json.loads(_get("https://api.github.com/users/%s/repos?per_page=100&type=owner&page=%d" % (user, page), hdr))
            repos += [(r["name"], r.get("language"), r.get("fork")) for r in batch]
            if len(batch) < 100:
                break
            page += 1
    except Exception as e:  # noqa: BLE001
        print("repo api failed, reading the page instead:", e, file=sys.stderr)
        repos = []
        try:
            for page in range(1, 11):
                h = _get("https://github.com/%s?tab=repositories&page=%d" % (user, page), {"Accept": "text/html"})
                items = re.findall(r'<li[^>]*itemprop="owns"[^>]*>(.*?)</li>', h, re.S)
                for it in items:
                    nm = re.search(r'itemprop="name codeRepository"[^>]*>\s*([^<]+?)\s*<', it)
                    lg = re.search(r'itemprop="programmingLanguage">([^<]+)<', it)
                    repos.append((nm.group(1) if nm else "?", lg.group(1) if lg else None, "Forked from" in it))
                if not items or 'rel="next"' not in h:
                    break
        except Exception as e2:  # noqa: BLE001
            print("repo page failed:", e2, file=sys.stderr)
            return None
    if not repos:
        return None
    counts = {}
    for _, lang, fork in repos:
        if lang and not fork:
            counts[lang] = counts.get(lang, 0) + 1
    langs = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return langs, len(repos)


def stats(days):
    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c)
    best = max(days, key=lambda d: (d[1], d[0]))
    longest = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    top = sorted([d for d in days if d[1]], key=lambda d: (-d[1], -d[0].toordinal()))
    return dict(total=total, active=active, longest=longest, top=top[:4], today=days[-1][0], best=best)


def label(d, now=None):
    s = "%d %s" % (d.day, MONTHS[d.month - 1])
    return s + (" %d" % d.year if now and d.year != now.year else "")


# ----------------------------------------------------------------------------- figure

def odometer(doc, x, y, value, size, delay):
    """Digits that roll up into place: each digit column scrolls through 0-9 twice and stops."""
    th = doc.th
    m = measure_digits(size)
    lh = size * 1.12
    out = []
    for i, ch in enumerate(value):
        cx = x + i * m
        if not ch.isdigit():
            out.append(doc.text(cx + m / 2, y, ch, "psb", size, "ink", "middle"))
            continue
        d = int(ch)
        cid = doc.uid()
        doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s"/></clipPath>' % (
            cid, n(cx - 2), n(y - size * 0.86), n(m + 4), n(size * 1.08)))
        final = -(10 + d) * lh
        t = Track(0)
        t.to(0, final, dur=1.5, ease="cubic-bezier(.16,.84,.24,1)")
        cls = doc.animate(t, 1.5, lambda v: "transform:translateY(%spx)" % n(v), once=True, delay=delay + i * 0.09)
        col = "".join(doc.text(cx + m / 2, y + k * lh, str(k % 10), "psb", size, "ink", "middle") for k in range(20))
        out.append('<g clip-path="url(#%s)"><g class="%s" transform="translate(0 %s)">%s</g></g>' % (cid, cls, n(final), col))
    return "".join(out)


def measure_digits(size):
    from hairline import measure as ms
    return max(ms("psb", size, str(k)) for k in range(10)) + size * 0.02


def draw(days, theme, updated, nrepos=None):
    st = stats(days)
    start = days[0][0] - dt.timedelta(days=(days[0][0].weekday() + 1) % 7)   # the Sunday on or before
    cells = []
    for d, c in days:
        cells.append(((d - start).days // 7, (d.weekday() + 1) % 7, d, c))   # col, row (Sunday = 0)
    ncol = max(c[0] for c in cells) + 1
    mx = max(c for *_, c in cells) or 1

    def lvl(c):
        if not c:
            return 0
        q = c / mx
        return 1 if q <= .25 else 2 if q <= .5 else 3 if q <= .75 else 4

    H = 360
    summary = "%d contributions on %d days in the last year; busiest day %d on %s." % (
        st["total"], st["active"], st["best"][1], label(st["best"][0], updated))
    doc = Doc(W, H, theme, "Contribution activity", "Contribution activity. " + summary, "g")
    th = doc.th
    P = 28
    doc.add('<rect x=".5" y=".5" width="%d" height="%d" rx="6" fill="none" stroke="%s"/>' % (W - 1, H - 1, th["border"]))
    doc.add(doc.text(P, 50, "Contribution activity", "psb", 22, "ink", tracking=-0.02))
    doc.add(doc.text(W - P, 50, "updated %s %d" % (label(updated), updated.year), "pm", 11.5, "ink3", "end"))

    # ---- the numbers, in a ruled row
    figs = [(str(st["total"]), "contributions in the last year"),
            (str(st["active"]), "days with contributions"),
            (str(nrepos) if nrepos else str(len(days) // 7), "public repositories" if nrepos else "weeks"),
            (str(st["best"][1]), "on the busiest day, %s" % label(st["best"][0], updated))]
    top, bot = 70, 156
    doc.add('<path d="M%d %dH%dM%d %dH%d" stroke="%s"/>' % (P, top, W - P, P, bot, W - P, th["border"]))
    cw = (W - 2 * P) / 4
    for i, (val, lab) in enumerate(figs):
        x = P + i * cw
        if i:
            doc.add('<path d="M%s %dV%d" stroke="%s"/>' % (n(x), top, bot, th["border"]))
        doc.add(odometer(doc, x + (16 if i else 0), 120, val, 40, 0.15 + i * 0.12))
        doc.add(doc.text(x + (16 if i else 0), 142, lab, "ps", 12.5, "ink2"))

    # ---- the calendar
    gx0, gy0 = P + 30, 206
    pitch = (W - P - gx0) / ncol
    cs = pitch - 3.2
    for col, row, d, c in cells:
        if d.day <= 7 and row == 0 and col > 0:
            doc.add(doc.text(gx0 + col * pitch, gy0 - 9, MONTHS[d.month - 1], "ps", 11.5, "ink2"))
    for r, nm in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        doc.add(doc.text(P, gy0 + r * pitch + cs - 1.5, nm, "ps", 11, "ink3"))
    doc.css.append("@keyframes rv{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}"
                   ".rv{animation:rv .55s cubic-bezier(.2,.7,.2,1) both}")
    by_col = {}
    rnd = __import__("random").Random(5)
    for col, row, d, c in cells:
        tw = ' class="tw" style="animation-duration:%ss;animation-delay:-%ss"' % (n(rnd.uniform(2.4, 4.6)), n(rnd.uniform(0, 4))) if c else ""
        by_col.setdefault(col, []).append(
            '<rect%s x="%s" y="%s" width="%s" height="%s" rx="2.4" fill="%s"/>' % (
                tw, n(gx0 + col * pitch), n(gy0 + row * pitch), n(cs), n(cs), th["g"][lvl(c)]))
    for col in sorted(by_col):
        doc.add('<g class="rv" style="animation-delay:%ss">%s</g>' % (n(0.25 + col * 0.016), "".join(by_col[col])))

    # ---- a constellation: one line joins every active day in date order, drawn like a trace,
    #      each day flares as the line reaches it, and active cells twinkle faintly between passes
    T = 9.0
    yb = H - 22
    act = [(gx0 + col * pitch + cs / 2, gy0 + row * pitch + cs / 2) for col, row, d, c in sorted(cells, key=lambda z: z[2]) if c]
    if len(act) >= 2:
        seg = [0.0]
        for p, q in zip(act, act[1:]):
            seg.append(seg[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
        total = seg[-1] or 1
        D0, DUR, FADE = 0.6, 4.6, 7.4
        draw = Track(1)
        draw.to(D0, 0, dur=DUR, ease="cubic-bezier(.45,.05,.55,.95)")
        draw.step(FADE + 0.8, 1, fade=0)
        op = Track(0.9)
        op.step(FADE, 0, fade=0.7)
        op.step(T - 0.25, 0.9, fade=0.2)
        lcls = doc.animate_many([(draw, lambda v: "stroke-dashoffset:%s" % n(v)), (op, lambda v: "opacity:%s" % n(v))], T)
        doc.add('<path class="%s" d="%s" pathLength="1" stroke-dasharray="1" fill="none" stroke="%s" stroke-width="1.1" '
                'stroke-linejoin="round" opacity=".9" style="vector-effect:none"/>' % (lcls, path(act), th["hi"]))
        doc.css.append("@keyframes fl{0%{transform:scale(.5);opacity:.95}100%{transform:scale(2.2);opacity:0}}")
        flares = []
        for (x, y), L in zip(act, seg):
            t_ = D0 + DUR * (L / total)
            fl = Track((0.5, 0))
            fl.step(t_, (0.5, 0.95), fade=0.04)
            fl.to(t_ + 0.04, (2.2, 0), dur=0.7, ease="cubic-bezier(.2,.7,.3,1)")
            fl.step(t_ + 0.8, (0.5, 0), fade=0)
            fcls = doc.animate(fl, T, lambda v: "transform:scale(%s);opacity:%s" % (n(v[0]), n(v[1])))
            flares.append('<circle class="%s" cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1" opacity="0" '
                          'style="transform-origin:%spx %spx"/>' % (fcls, n(x), n(y), n(cs * 0.7), th["hi"], n(x), n(y)))
        doc.add("".join(flares))
        doc.add(doc.text(P, yb, "%d active days, joined in the order they happened" % len(act), "pm", 11.5, "ink3"))
    doc.css.append("@keyframes tw{0%,100%{opacity:1}50%{opacity:.55}}.tw{animation:tw 3s ease-in-out infinite}")
    # legend
    lx = W - P - 5 * (cs + 3) - measure("ps", 11.5, "More") - 8
    doc.add(doc.text(lx - 8, yb, "Less", "ps", 11.5, "ink3", "end"))
    for i in range(5):
        doc.add('<rect x="%s" y="%s" width="%s" height="%s" rx="2.4" fill="%s"/>' % (
            n(lx + i * (cs + 3)), n(yb - cs + 1), n(cs), n(cs), th["g"][i]))
    doc.add(doc.text(lx + 5 * (cs + 3) + 5, yb, "More", "ps", 11.5, "ink3"))
    return doc.render()


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "AnshulMohanty")
    days = fetch(user)
    langs = fetch_languages(user)
    updated = dt.date.today()
    out = os.path.join(ROOT, "assets")
    os.makedirs(out, exist_ok=True)
    import build
    for theme in ("light", "dark"):
        for name, svg in (("contributions", draw(days, theme, updated, langs[1] if langs else None)),
                          ("stack", build.stack(theme, langs))):
            p = os.path.join(out, "%s-%s.svg" % (name, theme))
            with open(p, "w") as fh:
                fh.write(svg)
            print("wrote", os.path.relpath(p, ROOT), os.path.getsize(p), "bytes")
    st = stats(days)
    print("%d contributions, %d active days, longest streak %d; languages: %s" % (
        st["total"], st["active"], st["longest"], langs))


if __name__ == "__main__":
    main()
