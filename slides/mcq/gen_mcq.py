# -*- coding: utf-8 -*-
import re, math, json, os, sys
from questions import QUIZ

SLIDES="/Users/hadez/Documents/Company/training content/Agent_on_Databricks/slides/project/slides"
DECK  ="/Users/hadez/Documents/Company/training content/Agent_on_Databricks/slides/project/deck.json"
LETTERS="ABCD"

def plain(s):  # visible length, markup stripped
    return re.sub(r"\s+"," ", re.sub(r"<[^>]+>","", re.sub(r"&[a-z]+;","x",s))).strip()

def lines(text, px, width):
    """approximate wrapped line count for IBM Plex Sans"""
    cpl = max(1, int(width / (px*0.497)))
    return max(1, math.ceil(len(plain(text))/cpl))

CARD_W = (1664-28)//2           # two cards per row
def card_h(stem, opts, sp, op):
    inner = CARD_W - 56
    h = 24                                        # padding top
    h += lines(stem, sp, inner-52) * (sp*1.35)    # stem
    h += 12                                       # gap
    for o in opts:
        h += lines(o, op, inner-52) * (op*1.30) + 7
    return h + 26                                 # padding bottom

def ans_h(ans, why, others, a,b,c):
    inner = CARD_W - 56
    h = 24 + lines(ans, a, inner-52)*(a*1.32) + 10
    h += lines(why, b, inner-52)*(b*1.32) + 8
    h += lines(others, c, inner-52)*(c*1.32)
    return h + 26

CHROME = ('<div style="position:absolute;right:0;top:0;width:12px;height:1080px;'
          'background:#8B0000;opacity:0.5"></div>')
FOOT = ('<hr style="position:absolute;left:128px;bottom:72px;width:1664px;border-top:1px solid #D9DCE1">\n'
        '<div style="position:absolute;left:128px;bottom:68px;width:56px;height:6px;background:#14181F"></div>')

# tunable defaults; the browser fit-pass overwrites these per slide
VARS = "--stem:22px;--opt:20px;--ans:22px;--why:20px;--oth:19px;--cpad:24px;--cgap:11px;--rgap:22px"

def badge(n, size=36, bg="#8B0000"):
    return (f'<p style="flex:none;width:{size}px;height:{size}px;border-radius:{size//2}px;background:{bg};'
            f'color:#FBFBF8;font-size:{int(size*0.55)}px;font-weight:700;text-align:center;'
            f'line-height:{size}px">{n}</p>')

def rows4(items):
    return ('<div style="display:flex;flex-direction:column;gap:var(--rgap);flex:1">'
            + "".join(items) + '</div>')

ROW = ('<div style="display:flex;gap:30px;align-items:flex-start;background:#FFFFFF;'
       'border:1px solid #E3E6EA;border-radius:12px;padding:var(--cpad) 28px">')

def shell(sid, title, tag, tagcol, lead, inner, notes):
    return (f'<section id="{sid}" data-transition="fade" style="background:#FBFBF8;color:#14181F;'
            "font-family:'IBM Plex Sans', Arial, sans-serif;padding:84px 128px 104px;display:flex;"
            f'flex-direction:column;gap:18px;{VARS}">\n'+CHROME+"\n"
            f'<div style="display:flex;align-items:baseline;gap:22px">'
            f'<h2 style="font-size:48px;font-weight:600;line-height:1.1">{title}</h2>'
            f'<p style="font-size:24px;color:{tagcol};font-weight:600">{tag}</p></div>\n'
            f'<p style="font-size:23px;color:#4A5568">{lead}</p>\n'
            +inner+"\n"+FOOT+"\n"
            f'<aside>{notes}</aside>\n</section>\n')

def build(sid, title, items):
    key=", ".join(f"{n}{LETTERS[items[n-1][2]]}" for n in range(1,5))
    qr=[]
    for n,(stem,opts,_,_,_) in enumerate(items,1):
        ol="".join(
          f'<p style="font-size:var(--opt);color:#4A5568;line-height:1.3">'
          f'<b style="color:#14181F">{LETTERS[i]}</b>&nbsp;&nbsp;{o}</p>' for i,o in enumerate(opts))
        qr.append(ROW+
          '<div style="flex:0 0 600px;display:flex;gap:13px;align-items:flex-start">'+badge(n)+
          '<p style="font-size:var(--stem);font-weight:600;line-height:1.3">'+stem+'</p></div>'
          f'<div style="flex:1;display:flex;flex-direction:column;gap:var(--cgap)">{ol}</div></div>')
    qnotes=(f"Answer key: {key}.\n\n"
        "Run this as a poll, not a lecture. Read each stem aloud, take a show of hands on every option, "
        "and only then move to the answer slide. The wrong answers are not filler \u2014 each one is a "
        "misconception this session exists to correct, so a room that splits is more useful to you than a "
        "room that is unanimous.\n\n"
        "If most of the room picks the same wrong option, stop and re-teach that point before moving on. "
        "That is the signal this slide is for.\n\n"
        "Timing: 5 minutes for the four questions, plus 4 minutes on the answer slide.")
    q=shell(sid+"-quiz", title, "Knowledge check", "#8A94A3",
            "Four questions. One correct answer each &mdash; answers on the next slide.", rows4(qr), qnotes)

    ar=[]
    for n,(stem,opts,ci,why,others) in enumerate(items,1):
        ar.append(ROW+
          '<div style="flex:0 0 600px;display:flex;gap:13px;align-items:flex-start">'+badge(n)+
          f'<p style="font-size:var(--ans);font-weight:700;line-height:1.3;color:#14181F">'
          f'{LETTERS[ci]}&nbsp;&mdash;&nbsp;{opts[ci]}</p></div>'
          f'<div style="flex:1;display:flex;flex-direction:column;gap:7px">'
          f'<p style="font-size:var(--why);color:#4A5568;line-height:1.3">{why}</p>'
          f'<p style="font-size:var(--oth);color:#8A94A3;line-height:1.3">{others}</p></div></div>')
    anotes=("Do not read these out verbatim. Take the one the room got wrong and talk through the grey "
        "line \u2014 the distractors carry the teaching.\n\n"
        "Every correct answer here is defended somewhere earlier in this session; if someone disputes one, "
        "go back to that slide rather than arguing from the answer key.\n\n"
        "Timing: 4 minutes.")
    a=shell(sid+"-quiz-answers", title, "Answers", "#8B0000",
            key+"&nbsp; &mdash; and why the others fail.", rows4(ar), anotes)
    return q, a, key

# --- rebalance the answer key: each letter correct exactly 7 times ---
TARGET={"s1":[0,1,2,3],"s2":[1,2,3,0],"s3":[2,3,0,1],"s4":[3,0,1,2],
        "s5":[0,2,1,3],"s6":[1,3,0,2],"s7":[2,0,3,1]}
for _sid,(_t,_items) in QUIZ.items():
    new=[]
    for _i,(stem,opts,ci,why,oth) in enumerate(_items):
        tgt=TARGET[_sid][_i]
        rest=[o for j,o in enumerate(opts) if j!=ci]
        out=[None]*4; out[tgt]=opts[ci]
        it=iter(rest)
        for j in range(4):
            if out[j] is None: out[j]=next(it)
        new.append((stem,out,tgt,why,oth))
    QUIZ[_sid]=(_t,new)

LAST={"s1":"s1-t5-best","s2":"s2-t5-why","s3":"s3-t6-why","s4":"s4-bench",
      "s5":"s5-t5-best","s6":"s6-t4-action","s7":"s7-t6-pitfalls"}

deck=json.load(open(DECK)); order=deck["order"][:]
for sid,(title,items) in QUIZ.items():
    assert len(items)==4, sid
    q,ans,key=build(sid,title,items)
    open(f"{SLIDES}/{sid}-quiz.html","w").write(q)
    open(f"{SLIDES}/{sid}-quiz-answers.html","w").write(ans)
    i=order.index(LAST[sid])
    order[i+1:i+1]=[f"{sid}-quiz", f"{sid}-quiz-answers"]
    print(f"  {sid}: inserted after {LAST[sid]:16} key {key}")
deck["order"]=order
json.dump(deck, open(DECK,"w"), indent=2)
print(f"\norder: {len(deck['order'])} slides")
