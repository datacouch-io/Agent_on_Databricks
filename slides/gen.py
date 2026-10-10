# -*- coding: utf-8 -*-
"""Emit deck slides from a compact spec. Inline styles only (closed CSS subset)."""
import pathlib, json

SLIDES = pathlib.Path(__file__).parent / "project" / "slides"
MONO = "'JetBrains Mono', Courier New, monospace"
ACC, INK, PAPER, BODY = "#8B0000", "#14181F", "#FBFBF8", "#4A5568"

def mono(s):
    return '<span style="font-family:%s">%s</span>' % (MONO, s)

def h2(t, size=64):
    return '<h2 style="font-size:%dpx;font-weight:600;line-height:1.1">%s</h2>' % (size, t)

def eyebrow(t):
    return ('<p style="font-size:26px;font-weight:700;color:%s;letter-spacing:3px;'
            'text-transform:uppercase">%s</p>' % (ACC, t))

def lead(t, size=34):
    return '<p style="font-size:%dpx;color:%s;line-height:1.4;width:1620px">%s</p>' % (size, INK, t)

def para(t, size=30):
    return '<p style="font-size:%dpx;color:%s;line-height:1.45">%s</p>' % (size, INK, t)

def h3(t):
    return '<h3 style="font-size:32px;font-weight:600">%s</h3>' % t

def card(label, text, dark=False, strong=False, fs=27, bfs=25):
    if dark:
        box = "background:#14181F;padding:28px;border-radius:12px"
        lc, tc = "#FF9E64", "#E3E6EA"
    else:
        bd = "2px solid %s" % ACC if strong else "1px solid #E3E6EA"
        box = "background:#FFFFFF;padding:28px;border:%s;border-radius:12px" % bd
        lc, tc = ACC, BODY
    return ('<div style="flex:1;display:flex;flex-direction:column;gap:10px;%s">'
            '<p style="font-size:%dpx;font-weight:700;color:%s">%s</p>'
            '<p style="font-size:%dpx;color:%s;line-height:1.4">%s</p></div>'
            % (box, fs, lc, label, bfs, tc, text))

def cards(items, gap=24):
    return '<div style="display:flex;gap:%dpx">%s</div>' % (gap, "".join(items))

def row(label, text, w=300, dark=False, strong=False):
    if dark:
        box = "background:#14181F;padding:24px 30px;border-radius:12px"
        lc, tc = "#FF9E64", "#B8C1CC"
    else:
        bd = "2px solid %s" % ACC if strong else "1px solid #E3E6EA"
        box = "background:#FFFFFF;padding:24px 30px;border:%s;border-radius:12px" % bd
        lc, tc = ACC, BODY
    return ('<div style="display:flex;gap:26px;align-items:center;%s">'
            '<p style="width:%dpx;font-size:27px;font-weight:700;color:%s">%s</p>'
            '<p style="flex:1;font-size:26px;color:%s;line-height:1.35">%s</p></div>'
            % (box, w, lc, label, tc, text))

def rows(items, gap=14):
    return '<div style="display:flex;flex-direction:column;gap:%dpx">%s</div>' % (gap, "".join(items))

def callout(title, text, icon="Warning", tone="alert"):
    if tone == "alert":
        bg, bc, tc, ic = "#F6E9E9", ACC, INK, ACC
    elif tone == "dark":
        bg, bc, tc, ic = "#14181F", "#FF9E64", "#F2F4F7", "#FF9E64"
    else:
        bg, bc, tc, ic = "#EDF0F3", ACC, INK, ACC
    ib = ('<x-icon name="%s" style="color:%s;width:52px;height:52px"></x-icon>' % (icon, ic)) if icon else ""
    inner = ""
    if title:
        inner += '<p style="font-size:28px;font-weight:700;color:%s">%s</p>' % (bc, title)
    inner += '<p style="font-size:29px;color:%s;line-height:1.42">%s</p>' % (tc, text)
    return ('<div style="display:flex;gap:24px;align-items:center;background:%s;padding:30px 36px;'
            'border-radius:14px">%s<div style="flex:1;display:flex;flex-direction:column;gap:8px">'
            '%s</div></div>' % (bg, ib, inner))

def panel(title, text, tone="grey", flex=1):
    if tone == "dark":
        bg, tcl, tct = "#14181F", "#FF9E64", "#E3E6EA"
    elif tone == "alert":
        bg, tcl, tct = "#F6E9E9", ACC, INK
    elif tone == "white":
        bg, tcl, tct = "#FFFFFF", ACC, BODY
    else:
        bg, tcl, tct = "#EDF0F3", ACC, BODY
    bd = ";border:1px solid #E3E6EA" if tone == "white" else ""
    inner = ""
    if title:
        inner += '<p style="font-size:28px;font-weight:700;color:%s">%s</p>' % (tcl, title)
    inner += '<p style="font-size:27px;color:%s;line-height:1.45">%s</p>' % (tct, text)
    return ('<div style="flex:%s;display:flex;flex-direction:column;gap:12px;background:%s;'
            'padding:30px 34px;border-radius:12px%s">%s</div>' % (flex, bg, bd, inner))

def bar(title, text, flex=1):
    return ('<div style="flex:%s;display:flex;flex-direction:column;gap:12px;background:#F6E9E9;'
            'padding:30px 34px;border-left:8px solid %s;border-radius:0 12px 12px 0">'
            '<p style="font-size:28px;font-weight:700;color:%s">%s</p>'
            '<p style="font-size:27px;color:%s;line-height:1.45">%s</p></div>'
            % (flex, ACC, ACC, title, INK, text))

def cols(items, gap=36, align=""):
    a = ";align-items:%s" % align if align else ""
    return '<div style="display:flex;gap:%dpx%s">%s</div>' % (gap, a, "".join(items))

def code(lines, fs=24, flex=None, title=None):
    body = "<br>\n".join(lines)
    t = ('<p style="font-family:%s;font-size:%dpx;color:#8A94A3">%s</p>' % (MONO, fs, title)) if title else ""
    f = "flex:%s;" % flex if flex else ""
    return ('<div style="%sbackground:#1E242E;padding:30px;border-radius:14px;display:flex;'
            'flex-direction:column;gap:10px">%s<p style="font-family:%s;font-size:%dpx;color:#C5CFD9;'
            'line-height:1.55">%s</p></div>' % (f, t, MONO, fs, body))

def out(title, lines, fs=24, flex=None):
    f = "flex:%s;" % flex if flex else ""
    return ('<div style="%sdisplay:flex;flex-direction:column;gap:8px;background:#FFFFFF;padding:28px;'
            'border:1px solid #E3E6EA;border-radius:12px">'
            '<p style="font-size:26px;font-weight:700;color:%s">%s</p>'
            '<p style="font-family:%s;font-size:%dpx;color:%s;line-height:1.5">%s</p></div>'
            % (f, ACC, title, MONO, fs, BODY, "<br>\n".join(lines)))

def flow(steps):
    """steps: list of (label, sub). Last one rendered dark."""
    parts = []
    for i, (lbl, sub) in enumerate(steps):
        last = i == len(steps) - 1
        if last:
            box = "background:#14181F;padding:28px;border-radius:12px"
            lc, sc = "#F2F4F7", "#B8C1CC"
        else:
            box = "background:#FFFFFF;padding:28px;border:1px solid #E3E6EA;border-radius:12px"
            lc, sc = INK, BODY
        parts.append('<div style="flex:1;display:flex;flex-direction:column;gap:8px;%s">'
                     '<p style="font-size:26px;font-weight:700;color:%s">%s</p>'
                     '<p style="font-size:24px;color:%s;line-height:1.35">%s</p></div>'
                     % (box, lc, lbl, sc, sub))
        if not last:
            parts.append('<x-shape kind="arrow-right" style="background:%s;width:76px;'
                         'height:36px"></x-shape>' % ACC)
    return '<div style="display:flex;gap:22px;align-items:center">%s</div>' % "".join(parts)

def dodont(dos, donts):
    def lst(items, c):
        return "".join('<p style="font-size:27px;color:%s;line-height:1.4">%s</p>' % (c, i) for i in items)
    return ('<div style="display:flex;gap:40px">'
            '<div style="flex:1;display:flex;flex-direction:column;gap:14px;background:#FFFFFF;'
            'padding:34px;border:2px solid #1F6F43;border-radius:14px">'
            '<div style="display:flex;gap:16px;align-items:center">'
            '<x-icon name="Check" style="color:#1F6F43;width:44px;height:44px"></x-icon>'
            '<p style="font-size:32px;font-weight:700;color:#1F6F43">Do</p></div>%s</div>'
            '<div style="flex:1;display:flex;flex-direction:column;gap:14px;background:#FFFFFF;'
            'padding:34px;border:2px solid %s;border-radius:14px">'
            '<div style="display:flex;gap:16px;align-items:center">'
            '<x-icon name="Close" style="color:%s;width:44px;height:44px"></x-icon>'
            '<p style="font-size:32px;font-weight:700;color:%s">Don\'t</p></div>%s</div></div>'
            % (lst(dos, BODY), ACC, ACC, ACC, lst(donts, BODY)))

CHROME = ('<hr style="position:absolute;left:128px;bottom:96px;width:1664px;border-top:1px solid #D9DCE1">'
          '<div style="position:absolute;left:128px;bottom:92px;width:56px;height:6px;background:#14181F"></div>'
          '<p style="position:absolute;left:1716px;bottom:68px;width:76px;font-size:24px;font-weight:600;'
          'color:#FBFBF8;background:%s;padding:6px 0;text-align:center">%%s</p>' % ACC)

def slide(sid, num, blocks, notes, gap=34):
    html = ('<section id="%s" data-transition="fade" style="background:%s;color:%s;'
            "font-family:'IBM Plex Sans', Arial, sans-serif;"
            'padding:128px 128px 160px;display:flex;flex-direction:column;gap:%dpx">\n'
            '<div style="position:absolute;right:0;top:0;width:12px;height:1080px;background:%s;'
            'opacity:0.5"></div>\n' % (sid, PAPER, INK, gap, ACC))
    html += "\n".join(blocks) + "\n"
    html += (CHROME % ("%02d" % num)) + "\n"
    html += "<aside>%s</aside>\n</section>\n" % notes.strip()
    (SLIDES / (sid + ".html")).write_text(html, encoding="utf-8")
    return sid

def divider(sid, num_label, title, goal, meta, section_desc, notes):
    html = ('<section id="%s" data-section="%s" data-transition="push" style="background:#14181F;'
            "color:#F2F4F7;font-family:'IBM Plex Sans', Arial, sans-serif;"
            'padding:128px;display:flex;flex-direction:column;justify-content:center;gap:32px">\n'
            '<div style="position:absolute;right:0;top:0;width:12px;height:1080px;background:%s"></div>\n'
            '<p style="font-size:260px;font-weight:700;line-height:1;color:#2A3340">%s</p>\n'
            '<h2 style="font-size:84px;font-weight:600;line-height:1.1;width:1400px">%s</h2>\n'
            '<hr style="width:240px;border-top:4px solid %s">\n'
            '<p style="font-size:36px;font-style:italic;color:#B8C1CC;width:1300px">%s</p>\n'
            '<p style="position:absolute;left:128px;bottom:80px;font-size:26px;color:#8A94A3">%s</p>\n'
            '<aside>%s</aside>\n</section>\n'
            % (sid, section_desc, ACC, num_label, title, ACC, goal, meta, notes.strip()))
    (SLIDES / (sid + ".html")).write_text(html, encoding="utf-8")
    return sid

def numbers():
    d = json.loads((pathlib.Path(__file__).parent / "project" / "deck.json").read_text())
    return {s: i + 1 for i, s in enumerate(d["order"])}

# ---- Databricks documentation images (uploaded as artifact assets) ----
ASSET = {
 "aisearch-managed":   "/_blob/1754c963e5308aa1d656c4fad57447d5",
 "aisearch-selfmgd":   "/_blob/0f6e343091ee93eefa6fdd879a3fbf3d",
 "aisearch-create":    "/_blob/d4b0d98da16cf5dfb97fcb5b59068182",
 "aisearch-sync":      "/_blob/bd91abfd663ae5cacff8fef9bd412dcf",
 "traces-tab":         "/_blob/ab65b202ac2e720bf5532f85311e9100",
 "trace-detail":       "/_blob/367dbe09519e5edd640d24fdbacdba99",
 "run-scorer":         "/_blob/f7415c8d68121b8272300b754986388a",
 "genie-create":       "/_blob/796fc5674dfcb365ab2be9f8c3da7586",
 "genie-context":      "/_blob/c9d3248d96bcd00b2845e0b9974c6707",
 "genie-one-home":     "/_blob/70656e2b196758bcd0013d9e42b344eb",
 "metric-views":       "/_blob/6f9a226577439b77e4063cf3e96f512f",
 "unity-gateway":      "/_blob/ab2457681acb78652771f8bf3230c7b9",
 "data-intelligence":  "/_blob/02425cf2883f53126627b9d11c27e718",
 "playground-tools":   "/_blob/793741d303b5a5e7aea8387d6efac9fe",
}

def img(key, caption, source, h=None, flex=1, bg="#EDF0F3"):
    """A framed documentation screenshot with its source credited underneath."""
    hh = "height:%dpx;object-fit:contain;" % h if h else ""
    return ('<div style="flex:%s;display:flex;flex-direction:column;gap:12px">'
            '<div style="background:%s;border:1px solid #E3E6EA;border-radius:12px;padding:16px;'
            'display:flex;justify-content:center">'
            '<img src="%s" alt="%s" style="max-width:100%%;object-fit:contain;%sborder-radius:6px;background:#FFFFFF">'
            '</div>'
            '<p style="font-size:22px;color:#4A5568;line-height:1.35">%s<br>'
            '<span style="font-size:19px;color:#8A94A3">Source: %s</span></p></div>'
            % (flex, bg, ASSET[key], caption.replace('"', "'"), hh, caption, source))

# ---- native diagram primitives (no raster images, deck fonts, exports to PPTX) ----

def node(label, sub="", tone="white", w=None, fs=24, sfs=20):
    if tone == "dark":
        box, lc, sc = "background:#14181F", "#F2F4F7", "#B8C1CC"
    elif tone == "accent":
        box, lc, sc = "background:#FFFFFF;border:2px solid %s" % ACC, ACC, BODY
    elif tone == "ghost":
        box, lc, sc = "background:transparent;border:1px dashed #AEB6C0", BODY, "#8A94A3"
    else:
        box, lc, sc = "background:#FFFFFF;border:1px solid #D9DCE1", INK, BODY
    width = "width:%dpx;" % w if w else "flex:1;"
    s = ('<p style="font-size:%dpx;font-weight:700;color:%s;line-height:1.25">%s</p>' % (fs, lc, label))
    if sub:
        s += '<p style="font-size:%dpx;color:%s;line-height:1.3">%s</p>' % (sfs, sc, sub)
    return ('<div style="%sdisplay:flex;flex-direction:column;gap:6px;%s;padding:18px 20px;'
            'border-radius:10px">%s</div>' % (width, box, s))

def arrow(label=None, w=56):
    a = '<x-shape kind="arrow-right" style="background:%s;width:%dpx;height:26px"></x-shape>' % (ACC, w)
    if not label:
        return '<div style="display:flex;align-items:center">%s</div>' % a
    return ('<div style="display:flex;flex-direction:column;align-items:center;gap:6px">'
            '<p style="font-size:18px;font-weight:700;color:%s;letter-spacing:1px;'
            'text-transform:uppercase;white-space:nowrap">%s</p>%s</div>' % (ACC, label, a))

def chain(items, gap=16, align="stretch"):
    return ('<div style="display:flex;gap:%dpx;align-items:%s">%s</div>'
            % (gap, align, "".join(items)))

def stack(items, gap=14, flex=None):
    f = "flex:%s;" % flex if flex else ""
    return '<div style="%sdisplay:flex;flex-direction:column;gap:%dpx">%s</div>' % (f, gap, "".join(items))

def band(text, tone="grey"):
    bg, c = ("#DDE2E8", BODY) if tone == "grey" else ("#F6E9E9", ACC)
    return ('<p style="background:%s;color:%s;font-size:19px;font-weight:700;letter-spacing:2px;'
            'text-transform:uppercase;padding:7px 14px;border-radius:6px;align-self:flex-start">%s</p>'
            % (bg, c, text))

def figure(inner, caption, source=None, flex=1, pad=26):
    cap = caption
    if source:
        cap += ('<br><span style="font-size:19px;color:#8A94A3">Redrawn from: %s</span>' % source)
    return ('<div style="flex:%s;display:flex;flex-direction:column;gap:12px">'
            '<div style="background:#EDF0F3;border:1px solid #E3E6EA;border-radius:12px;padding:%dpx;'
            'display:flex;flex-direction:column;gap:16px">%s</div>'
            '<p style="font-size:22px;color:%s;line-height:1.35">%s</p></div>'
            % (flex, pad, inner, BODY, cap))


# ---- icon/shape guard ----
# The Slides canvas renders an unknown name as the literal text "[icon: Name]".
# These are the only names it knows; anything else silently ships as a placeholder.
ICONS = {"Ant","Activity","Book","Chart","Chat","Check","CheckCircle","Clock","Cloud","Code",
         "Database","Globe","GraduationCap","Home","Key","Lightbulb","Lightning","Link","Lock",
         "Owl","PaperPlane","Play","Search","Settings","Star","ThumbsUp","Tool","Trust","Users",
         "Verified","Warning","Wrench"}
SHAPES = {"rect","rounded","ellipse","diamond","arrow-right"}

def check_icons(slides_dir="project/slides"):
    """Fail loudly on any icon or shape the canvas cannot draw."""
    import pathlib as _p, re as _re
    bad=[]
    for f in sorted(_p.Path(slides_dir).glob("*.html")):
        s=f.read_text()
        bad += [(f.stem,"icon",n)  for n in _re.findall(r'<x-icon[^>]*name="([^"]*)"', s)  if n not in ICONS]
        bad += [(f.stem,"shape",k) for k in _re.findall(r'<x-shape[^>]*kind="([^"]*)"', s) if k not in SHAPES]
    if bad:
        raise SystemExit("INVALID NAMES:\n" + "\n".join(f"  {a} {b} {c!r}" for a,b,c in bad))
    return "icons and shapes: all valid"
