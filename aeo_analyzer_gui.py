#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║         AEO ANALYZER ERA  —  GUI Edition  by SA Era           ║
║     SEO · AEO · Crawl · Rank Prediction Engine                ║
║     Flet 0.85.1 — Rich CLI-style visual output                ║
╚═══════════════════════════════════════════════════════════════╝
"""

import re, json, sys, time, os, threading, urllib.parse
from collections import Counter
from datetime import datetime
import flet as ft

try:
    import requests
except ImportError:
    print("[!] pip install requests"); sys.exit(1)
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] pip install beautifulsoup4 lxml"); sys.exit(1)
try:
    import textstat; HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False
try:
    import spacy; nlp = spacy.load("en_core_web_sm"); HAS_SPACY = True
except Exception:
    HAS_SPACY = False

# ── Colors ────────────────────────────────────────────────────────
BG      = "#0d1117"; BG2 = "#161b22"; BG3 = "#1c2128"
CYAN    = "#00d4ff"; CDIM = "#0097b2"
GREEN   = "#39d353"; YELLOW = "#e3b341"; RED = "#f85149"
BLUE    = "#58a6ff"; MAG = "#c678dd"; ORG = "#ff7b2e"
TEXT    = "#e6edf3"; DIM = "#8b949e"; BORDER = "#30363d"
MONO    = "Courier New"

def sc(v): return GREEN if v>=75 else (YELLOW if v>=45 else RED)
def rc(p): return GREEN if "HIGH" in p else (YELLOW if "MEDIUM" in p else RED)

# ── Padding / Border helpers ──────────────────────────────────────
def pxy(v=0,h=0): return ft.padding.Padding.symmetric(vertical=v,horizontal=h)
def pon(top=0,right=0,bottom=0,left=0): return ft.padding.Padding.only(top=top,right=right,bottom=bottom,left=left)
def mon(top=0,right=0,bottom=0,left=0): return ft.margin.Margin.only(top=top,right=right,bottom=bottom,left=left)
def ba(w,c): return ft.border.Border.all(w,c)
def bb(w,c): return ft.border.Border.only(bottom=ft.border.BorderSide(w,c))
def bt(w,c): return ft.border.Border.only(top=ft.border.BorderSide(w,c))
def brl(tl=0,bl=0): return ft.border_radius.BorderRadius.only(top_left=tl,bottom_left=bl)
def brr(tr=0,br=0): return ft.border_radius.BorderRadius.only(top_right=tr,bottom_right=br)

# ── Score bar (matches CLI bar style) ────────────────────────────
def make_bar(value, width=160):
    filled = int((value/100)*width)
    color  = sc(value)
    return ft.Row([
        ft.Container(width=max(1,filled), height=12, bgcolor=color,   border_radius=brl(3,3)),
        ft.Container(width=max(0,width-filled), height=12, bgcolor="#21262d", border_radius=brr(3,3)),
    ], spacing=0)

# ── Section title like CLI ─────────────────────────────────────────
def sec(title, color=MAG):
    return ft.Container(
        content=ft.Row([
            ft.Container(expand=True, height=1, bgcolor=CDIM),
            ft.Text(f"  {title}  ", size=13, weight=ft.FontWeight.BOLD, color=color, font_family=MONO),
            ft.Container(expand=True, height=1, bgcolor=CDIM),
        ], spacing=0),
        margin=mon(top=18, bottom=10),
    )

# ── Table header row ───────────────────────────────────────────────
def tbl_header(*cols_widths):
    return ft.Container(
        content=ft.Row([
            ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=CYAN,
                    font_family=MONO, width=w if w else None,
                    expand=(w is None))
            for label, w in cols_widths
        ], spacing=0),
        padding=pxy(v=6, h=12),
        border=bb(1, CYAN),
        bgcolor=BG3,
    )

# ── Table row ──────────────────────────────────────────────────────
def tbl_row(cells, alt=False):
    return ft.Container(
        content=ft.Row(cells, spacing=0),
        padding=pxy(v=7, h=12),
        border=bb(1, BORDER),
        bgcolor="#1a1f27" if alt else BG2,
    )

# ── Kv row (label: value) ──────────────────────────────────────────
def kv(label, value, vcol=TEXT, lw=160):
    return ft.Container(
        content=ft.Row([
            ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=TEXT, width=lw, font_family=MONO),
            ft.Text(str(value), size=12, color=vcol, expand=True, max_lines=3, font_family=MONO),
        ], spacing=8),
        padding=pxy(v=5, h=12),
        border=bb(1, BORDER),
    )

def stat_box(label, value, color=CYAN):
    return ft.Container(
        content=ft.Column([
            ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=color, font_family=MONO),
            ft.Text(label, size=10, color=DIM, font_family=MONO),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BG3, border_radius=8, padding=pxy(v=10,h=14),
        border=ba(1,BORDER), expand=True,
    )

def chip(text, is_issue=True):
    return ft.Container(
        content=ft.Row([
            ft.Text("⚠" if is_issue else "→", color=RED if is_issue else YELLOW, size=12, width=16),
            ft.Text(text, size=12, color=DIM, expand=True, font_family=MONO),
        ], spacing=6),
        padding=pon(top=3, bottom=3, left=8),
    )

def logline(msg, kind="info"):
    colors={"info":CYAN,"good":GREEN,"warn":YELLOW,"error":RED,"dim":DIM}
    return ft.Text(msg, size=12, color=colors.get(kind,TEXT), font_family=MONO)

# ════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE (unchanged logic)
# ════════════════════════════════════════════════════════════════

def crawl_page(url):
    h={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}
    t0=time.time(); resp=requests.get(url,headers=h,timeout=(5,10),allow_redirects=True)
    lt=round(time.time()-t0,2); resp.raise_for_status()
    soup=BeautifulSoup(resp.text,"lxml"); base=urllib.parse.urlparse(url)
    tt=soup.find("title"); title=tt.get_text(strip=True) if tt else ""
    mt=soup.find("meta",attrs={"name":re.compile(r"^description$",re.I)})
    meta=mt.get("content","").strip() if mt else ""
    headings={lv:[h2.get_text(strip=True) for h2 in soup.find_all(lv)] for lv in ["h1","h2","h3","h4"]}
    paras=[p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True))>40]
    fre=re.compile(r"(frequently asked|faq|common questions|people also ask)",re.I)
    faqs=[]
    for sec2 in soup.find_all(["section","div","article"]):
        hh=sec2.find(re.compile(r"^h[1-6]$"))
        if hh and fre.search(hh.get_text()):
            for q in sec2.find_all(["dt","h3","h4","strong","b"]):
                t=q.get_text(strip=True)
                if t.endswith("?") or len(t.split())<20: faqs.append(t)
    il=[]; el=[]
    for a in soup.find_all("a",href=True):
        href=a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"): continue
        full=urllib.parse.urljoin(url,href); parsed=urllib.parse.urlparse(full)
        entry={"href":full,"text":a.get_text(strip=True)}
        if parsed.netloc==base.netloc: il.append(entry)
        else: el.append(entry)
    imgs=[{"src":i.get("src",""),"alt":i.get("alt",""),"w":i.get("width",""),"h":i.get("height","")} for i in soup.find_all("img")]
    schemas=[]
    for s in soup.find_all("script",type="application/ld+json"):
        try: schemas.append(json.loads(s.string or "{}"))
        except: pass
    body=soup.find("body"); ft2=body.get_text(separator=" ",strip=True) if body else ""
    return {"url":url,"status":resp.status_code,"load":lt,"title":title,"meta":meta,
            "headings":headings,"paras":paras,"faqs":faqs,"il":il,"el":el,"imgs":imgs,
            "schemas":schemas,"text":ft2,"wc":len(ft2.split())}

def analyze_seo(d, kw=""):
    title=d["title"]; meta=d["meta"]; text=d["text"]
    words=text.lower().split(); scores={}; issues=[]; recs=[]
    tl=len(title)
    if 50<=tl<=60: scores["title_length"]=100
    elif 40<=tl<=70: scores["title_length"]=70; issues.append(f"Title is {tl} chars (ideal 50-60)")
    else: scores["title_length"]=30; issues.append(f"Title {tl} chars — {'too short' if tl<40 else 'too long'}")
    ml=len(meta)
    if 140<=ml<=160: scores["meta_desc"]=100
    elif not meta: scores["meta_desc"]=0; issues.append("Missing meta description")
    elif ml<140: scores["meta_desc"]=50; issues.append(f"Meta too short ({ml} chars, ideal 140-160)")
    else: scores["meta_desc"]=60; issues.append(f"Meta too long ({ml} chars)")
    density=0.0
    if kw:
        kl=kw.lower(); kc=sum(1 for w in words if kl in w)
        density=round((kc/max(len(words),1))*100,2)
        if 1.0<=density<=2.5: scores["kw_density"]=100
        elif density<1.0: scores["kw_density"]=40; issues.append(f"KW density {density}% low (target 1-2.5%)")
        else: scores["kw_density"]=50; issues.append(f"KW density {density}% — possible stuffing")
    else: scores["kw_density"]=50
    ilc=len(d["il"])
    if ilc>=5: scores["int_links"]=100
    elif ilc>=3: scores["int_links"]=70
    elif ilc>=1: scores["int_links"]=40; recs.append("Add more internal links (aim for 5+)")
    else: scores["int_links"]=0; issues.append("No internal links found")
    imgs=d["imgs"]
    if imgs:
        wa=sum(1 for i in imgs if i["alt"].strip()); ratio=wa/len(imgs)
        scores["img_alt"]=round(ratio*100)
        if ratio<1.0: issues.append(f"{len(imgs)-wa} image(s) missing alt tags")
    else: scores["img_alt"]=100
    h1=d["headings"].get("h1",[]); h2=d["headings"].get("h2",[])
    if len(h1)==1: scores["headings"]=100 if h2 else 60
    elif not h1: scores["headings"]=0; issues.append("No H1 tag found")
    else: scores["headings"]=40; issues.append(f"Multiple H1 tags ({len(h1)})")
    flesch=None
    if HAS_TEXTSTAT and text:
        flesch=textstat.flesch_reading_ease(text)
        if flesch>=60: scores["readability"]=100
        elif flesch>=40: scores["readability"]=70
        else: scores["readability"]=40; issues.append(f"Low readability ({flesch:.0f})")
    else: scores["readability"]=60
    st=[s.get("@type","?") for s in d["schemas"]]
    if d["schemas"]:
        sv=40
        if any("FAQ" in str(t) for t in st): sv+=30
        if any("Article" in str(t) or "BlogPosting" in str(t) for t in st): sv+=30
        scores["schema"]=min(100,sv)
    else: scores["schema"]=0; recs.append("Add JSON-LD structured data")
    return {"scores":scores,"score":round(sum(scores.values())/len(scores)),"flesch":flesch,
            "density":density,"ilc":ilc,"imgs":len(imgs),"issues":issues,"recs":recs,"st":st}

def analyze_aeo(d):
    text=d["text"]; hall=[]
    for lv in ["h1","h2","h3"]: hall.extend(d["headings"].get(lv,[]))
    scores={}; sigs={}; issues=[]
    qh=[h for h in hall if "?" in h or re.match(r"^(what|how|why|when|where|who|which|can|is|are|does|do)\b",h,re.I)]
    qr=len(qh)/max(len(hall),1)
    scores["q_headings"]=min(100,round(qr*200)); sigs["q_headings"]=f"{len(qh)}/{len(hall)} are question-style"
    has_faq=len(d["faqs"])>0 or any(re.search(r"faq|frequently asked|people also ask",h,re.I) for h in hall)
    scores["faq"]=100 if has_faq else 0; sigs["faq"]=f"{'Found' if has_faq else 'Not found'} — {len(d['faqs'])} items"
    if not has_faq: issues.append("No FAQ section — add Q&A blocks to capture People Also Ask")
    sa=[p for p in d["paras"] if len(p.split())<=50]; sar=len(sa)/max(len(d["paras"]),1)
    scores["short_ans"]=min(100,round(sar*150)); sigs["short_ans"]=f"{len(sa)} short paragraphs (<=50 words)"
    top_ents=[]
    if HAS_SPACY and text:
        doc=nlp(text[:50000]); ents=Counter([(e.text,e.label_) for e in doc.ents])
        top_ents=ents.most_common(10); ec=len(set(e.text for e in doc.ents))
        scores["entities"]=min(100,ec*3); sigs["entities"]=f"{ec} unique named entities"
    else: scores["entities"]=50; sigs["entities"]="spaCy unavailable — install for NLP analysis"
    common=Counter(w.lower() for w in text.split() if len(w)>4 and w.isalpha()).most_common(20)
    scores["nlp"]=80 if len(common)>=10 else 40; sigs["nlp"]="Top terms: "+(", ".join([w for w,_ in common[:4]]))
    st=[s.get("@type","?") for s in d["schemas"]]; sv=0
    if d["schemas"]: sv+=40
    if any("FAQ" in str(t) for t in st): sv+=30
    if any("Article" in str(t) or "BlogPosting" in str(t) for t in st): sv+=30
    scores["struct_data"]=min(100,sv); sigs["struct_data"]=f"Types: {st if st else ['None']}"
    cit=[p for p in d["paras"] if 80<=len(p.split())<=300]
    scores["citable"]=min(100,len(cit)*15); sigs["citable"]=f"{len(cit)} paragraphs in 80-300 word range"
    eeat={"author byline":bool(re.search(r"by\s+[A-Z][a-z]+\s+[A-Z][a-z]+|written by|author:",text[:3000],re.I)),
          "publication date":bool(re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}",text[:3000],re.I)),
          "citations/references":bool(re.search(r"(according to|research shows|study|cited|reference|source)",text,re.I)),
          "expertise language":bool(re.search(r"(expert|professional|certified|licensed|specialist|years of experience)",text,re.I))}
    scores["eeat"]=sum(eeat.values())*25; sigs["eeat"]=f"{sum(eeat.values())}/4 signals: "+", ".join(k for k,v in eeat.items() if v)
    return {"scores":scores,"score":round(sum(scores.values())/len(scores)),
            "sigs":sigs,"top_ents":top_ents,"eeat":eeat,"issues":issues}

def rank_prob(seo,aeo,wc,il,bl=50.0):
    if wc>=2000: depth=100
    elif wc>=1000: depth=70
    elif wc>=500: depth=40
    else: depth=15
    depth=min(100,depth+min(20,il*2))
    rs=round(seo*0.35+aeo*0.35+bl*0.15+depth*0.15,1)
    if rs>=90: pred,conf="HIGH — Strong ranking potential","High"
    elif rs>=70: pred,conf="MEDIUM — Moderate ranking potential","Medium"
    else: pred,conf="LOW — Significant improvements needed","Low"
    return {"score":rs,"pred":pred,"conf":conf,"depth":depth,
            "comps":{"SEO Score":seo,"AEO Score":aeo,"Backlink Score":bl,"Content Depth":depth}}

def save_report(raw,seo,aeo,rank):
    os.makedirs("reports",exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S"); fname=f"reports/aeo_era_{ts}.json"
    with open(fname,"w") as f:
        json.dump({"url":raw["url"],"seo":seo,"aeo":aeo,"rank":rank},f,indent=2,default=str)
    return fname

# ════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title="AEO Analyzer ERA — by SA Era"
    page.bgcolor=BG; page.padding=0
    page.theme_mode=ft.ThemeMode.DARK
    page.fonts={"mono":MONO}
    store={}

    # ── HEADER ────────────────────────────────────────────────
    header=ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("AEO Analyzer",size=18,weight=ft.FontWeight.BOLD,color=CYAN,font_family=MONO),
                ft.Text("ERA",size=30,weight=ft.FontWeight.BOLD,color=CYAN,font_family=MONO),
            ],spacing=0),
            ft.Container(width=1,height=50,bgcolor=BORDER),
            ft.Column([
                ft.Text("SEO · AEO · Crawl · Rank Prediction",size=12,color=DIM),
                ft.Text("E-E-A-T · NLP · Structured Data · by SA Era",size=12,color=DIM),
                ft.Text(f"GUI Edition  |  Flet 0.85.1  |  {datetime.now().strftime('%d %b %Y')}",size=11,color=CDIM),
            ],spacing=3,expand=True),
        ],spacing=18,vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BG2,padding=pxy(v=12,h=22),border=bb(1,BORDER),
    )

    # ── INPUT ─────────────────────────────────────────────────
    url_f=ft.TextField(label="Target URL",hint_text="https://example.com",prefix_icon=ft.Icons.LINK,
        bgcolor=BG3,border_color=CDIM,focused_border_color=CYAN,color=TEXT,cursor_color=CYAN,
        label_style=ft.TextStyle(color=DIM),expand=True)
    kw_f=ft.TextField(label="Target Keyword (optional)",hint_text="e.g. seo tools",prefix_icon=ft.Icons.SEARCH,
        bgcolor=BG3,border_color=BORDER,focused_border_color=CYAN,color=TEXT,cursor_color=CYAN,
        label_style=ft.TextStyle(color=DIM),width=240)
    bl_f=ft.TextField(label="Backlink Score",value="50",prefix_icon=ft.Icons.LINK_OFF,
        bgcolor=BG3,border_color=BORDER,focused_border_color=CYAN,color=TEXT,cursor_color=CYAN,
        label_style=ft.TextStyle(color=DIM),width=145,input_filter=ft.NumbersOnlyInputFilter())
    btn=ft.Button(content=ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH,color=BG,size=15),
                  ft.Text("Analyze",color=BG,weight=ft.FontWeight.BOLD)],spacing=6,tight=True),
                  bgcolor=CYAN,height=50,width=135)
    pbar=ft.ProgressBar(value=None,color=CYAN,bgcolor=BG3,bar_height=3,visible=False)
    stxt=ft.Text("",size=11,color=DIM)
    input_panel=ft.Container(
        content=ft.Column([
            ft.Row([url_f,kw_f,bl_f,btn],spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER),
            pbar,stxt],spacing=6),
        bgcolor=BG2,padding=pxy(v=12,h=22),border=bb(1,BORDER))

    # ── LOG ───────────────────────────────────────────────────
    log_list=ft.ListView(expand=True,spacing=1,auto_scroll=True,padding=8)
    def clr(_=None): log_list.controls.clear(); page.update()
    log_panel=ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("Live Output",size=12,weight=ft.FontWeight.BOLD,color=DIM),
                    ft.Container(expand=True),
                    ft.TextButton(content=ft.Text("Clear",color=DIM,size=11),on_click=clr)]),
            ft.Container(content=log_list,bgcolor="#070b10",border_radius=8,border=ba(1,BORDER),expand=True),
        ],spacing=4,expand=True),padding=12,expand=True)

    # ── TAB CONTENT COLUMNS ──────────────────────────────────
    c_crawl=ft.Column(scroll=ft.ScrollMode.AUTO,spacing=0,expand=True)
    c_seo  =ft.Column(scroll=ft.ScrollMode.AUTO,spacing=0,expand=True)
    c_aeo  =ft.Column(scroll=ft.ScrollMode.AUTO,spacing=0,expand=True)
    c_rank =ft.Column(scroll=ft.ScrollMode.AUTO,spacing=0,expand=True)

    tabs=[
        ft.Container(content=c_crawl,padding=pxy(v=10,h=18),expand=True,visible=False),
        ft.Container(content=c_seo,  padding=pxy(v=10,h=18),expand=True,visible=False),
        ft.Container(content=c_aeo,  padding=pxy(v=10,h=18),expand=True,visible=False),
        ft.Container(content=c_rank, padding=pxy(v=10,h=18),expand=True,visible=False),
    ]
    tlabels=["📡 Crawl","🔍 SEO","🤖 AEO","🏆 Ranking"]
    tbtns=[]

    def mk_tbtn(i,label):
        b=ft.TextButton(content=ft.Text(label,size=12,
            color=CYAN if i==0 else DIM,
            weight=ft.FontWeight.BOLD if i==0 else ft.FontWeight.NORMAL))
        def oc(e,idx=i):
            for j,x in enumerate(tbtns):
                x.content.color =CYAN if j==idx else DIM
                x.content.weight=ft.FontWeight.BOLD if j==idx else ft.FontWeight.NORMAL
            for j,t in enumerate(tabs): t.visible=(j==idx)
            page.update()
        b.on_click=oc; return b

    for i,l in enumerate(tlabels): tbtns.append(mk_tbtn(i,l))

    tab_bar=ft.Container(content=ft.Row(tbtns,spacing=4),bgcolor=BG2,
                         padding=pxy(v=5,h=16),border=bb(1,BORDER),visible=False)
    results=ft.Container(
        content=ft.Column([tab_bar,ft.Stack(tabs,expand=True)],spacing=0,expand=True),
        expand=True,visible=False)

    content_row=ft.Row([
        ft.Container(content=log_panel,width=300),
        ft.Container(width=1,bgcolor=BORDER),
        results,
    ],spacing=0,expand=True)

    page.add(ft.Column([header,input_panel,content_row],spacing=0,expand=True))

    def log(msg,kind="info"):
        log_list.controls.append(logline(msg,kind)); page.update()

    def snack(msg,color=GREEN):
        sb=ft.SnackBar(content=ft.Text(msg,color=BG),bgcolor=color)
        page.overlay.append(sb); sb.open=True; page.update()

    def sw(idx):
        for j,b in enumerate(tbtns):
            b.content.color =CYAN if j==idx else DIM
            b.content.weight=ft.FontWeight.BOLD if j==idx else ft.FontWeight.NORMAL
        for j,t in enumerate(tabs): t.visible=(j==idx)

    # ─────────────────────────────────────────────────────────
    # BUILD CRAWL TAB
    # ─────────────────────────────────────────────────────────
    def bld_crawl(r):
        c_crawl.controls.clear()
        c_crawl.controls.append(sec("LAYER 1 — PAGE CRAWL"))

        # Status line
        st_color=GREEN if r["status"]==200 else YELLOW
        c_crawl.controls.append(ft.Container(
            content=ft.Row([
                ft.Text(f"  {r['status']} OK",size=12,color=st_color,font_family=MONO,weight=ft.FontWeight.BOLD),
                ft.Container(width=20),
                ft.Text(f"Load: {r['load']}s",size=12,color=CYAN,font_family=MONO),
                ft.Container(width=20),
                ft.Text(f"Words: {r['wc']:,}",size=12,color=CYAN,font_family=MONO),
                ft.Container(width=20),
                ft.Text(f"Internal Links: {len(r['il'])}",size=12,color=TEXT,font_family=MONO),
            ]),bgcolor=BG3,border_radius=8,padding=pxy(v=8,h=12),
            border=ba(1,st_color),margin=mon(bottom=10),
        ))

        # Crawl table
        c_crawl.controls.append(ft.Container(
            content=ft.Column([
                tbl_header(("Field",160),("Value",None)),
                kv("URL",           r["url"][:90],BLUE),
                kv("Title",         (r["title"] or "None")[:90],
                   GREEN if 50<=len(r["title"])<=60 else YELLOW),
                kv("Title Length",  f"{len(r['title'])} chars",
                   GREEN if 50<=len(r["title"])<=60 else YELLOW),
                kv("Meta Desc",     (r["meta"] or "— Missing —")[:100],
                   GREEN if r["meta"] else RED),
                kv("Meta Length",   f"{len(r['meta'])} chars",
                   GREEN if 140<=len(r["meta"])<=160 else YELLOW),
                kv("Word Count",    f"{r['wc']:,}",
                   GREEN if r["wc"]>=1500 else (YELLOW if r["wc"]>=800 else RED)),
                kv("H1 Tags",       ", ".join(r["headings"].get("h1",[])) or "None",
                   GREEN if len(r["headings"].get("h1",[]))==1 else RED),
                kv("H2 Tags",       f"{len(r['headings'].get('h2',[]))} found",CYAN),
                kv("H3 Tags",       f"{len(r['headings'].get('h3',[]))} found",CYAN),
                kv("Internal Links",str(len(r["il"])),GREEN if len(r["il"])>=5 else YELLOW),
                kv("External Links",str(len(r["el"])),TEXT),
                kv("Images",        f"{len(r['imgs'])} total",TEXT),
                kv("FAQs Found",    str(len(r["faqs"])),GREEN if r["faqs"] else YELLOW),
                kv("Paragraphs",    str(len(r["paras"])),TEXT),
                kv("Schema Types",  ", ".join([s.get("@type","?") for s in r["schemas"]]) or "None",
                   GREEN if r["schemas"] else RED),
            ],spacing=0),
            bgcolor=BG2,border_radius=10,border=ba(1,BORDER),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ))

        if r["faqs"]:
            c_crawl.controls.append(sec("FAQ ITEMS DETECTED",CYAN))
            for f in r["faqs"][:8]:
                c_crawl.controls.append(ft.Container(
                    content=ft.Text(f"  • {f[:100]}",size=12,color=DIM,font_family=MONO),
                    padding=pon(top=3,bottom=3,left=8)))

    # ─────────────────────────────────────────────────────────
    # BUILD SEO TAB  (matches CLI table style)
    # ─────────────────────────────────────────────────────────
    def bld_seo(seo,raw):
        c_seo.controls.clear()
        c_seo.controls.append(sec("LAYER 2 — SEO ANALYSIS"))

        # Score headline
        score_c=sc(seo["score"])
        c_seo.controls.append(ft.Container(
            content=ft.Row([
                ft.Text("SEO Score:",size=14,color=TEXT,font_family=MONO,weight=ft.FontWeight.BOLD),
                ft.Text(f" {seo['score']}/100",size=22,color=score_c,font_family=MONO,weight=ft.FontWeight.BOLD),
            ]),
            padding=pxy(v=8,h=14),bgcolor=BG3,border_radius=8,
            border=ba(2,score_c),margin=mon(bottom=12),
        ))

        # Stat boxes
        fl_v=f"{seo['flesch']:.0f}" if seo["flesch"] else "N/A"
        c_seo.controls.append(ft.Row([
            stat_box("SEO Score",    seo["score"],     CYAN),
            stat_box("Int. Links",   seo["ilc"],       BLUE),
            stat_box("Images",       seo["imgs"],      BLUE),
            stat_box("KW Density",   f"{seo['density']:.1f}%", TEXT),
            stat_box("Flesch Score", fl_v,             TEXT),
        ],spacing=6))
        c_seo.controls.append(ft.Container(height=12))

        # Signal table (matches CLI)
        names={
            "title_length": ("Title Length (50-60 chars)", "HIGH"),
            "meta_desc":    ("Meta Description (140-160)","HIGH"),
            "kw_density":   ("Keyword Density (1-2.5%)",  "HIGH"),
            "int_links":    ("Internal Links (5+ ideal)",  "HIGH"),
            "img_alt":      ("Image Alt Tags (100%)",      "MEDIUM"),
            "headings":     ("Heading Structure (H1>H2)",  "HIGH"),
            "readability":  ("Readability (Flesch)",       "MEDIUM"),
            "schema":       ("Schema / JSON-LD",           "HIGH"),
        }
        rows=[tbl_header(("Signal",None),("Score",60),("Bar",170),("Status",80))]
        for i,(k,(label,imp)) in enumerate(names.items()):
            v=seo["scores"].get(k,0); color=sc(v)
            status="✓ Good" if v>=75 else ("△ Fair" if v>=45 else "✗ Weak")
            sc_=GREEN if v>=75 else (YELLOW if v>=45 else RED)
            rows.append(tbl_row([
                ft.Text(label,size=12,color=TEXT,expand=True,font_family=MONO),
                ft.Text(str(v),size=12,color=color,width=60,weight=ft.FontWeight.BOLD,font_family=MONO),
                ft.Container(content=make_bar(v,160),width=170),
                ft.Text(status,size=12,color=sc_,width=80,font_family=MONO),
            ],alt=i%2==1))

        c_seo.controls.append(ft.Container(
            content=ft.Column(rows,spacing=0),bgcolor=BG2,
            border_radius=10,border=ba(1,BORDER),clip_behavior=ft.ClipBehavior.HARD_EDGE))

        if seo["issues"]:
            c_seo.controls.append(sec("ISSUES",RED))
            for i in seo["issues"]: c_seo.controls.append(chip(i,True))
        if seo["recs"]:
            c_seo.controls.append(sec("RECOMMENDATIONS",YELLOW))
            for r2 in seo["recs"]: c_seo.controls.append(chip(r2,False))

    # ─────────────────────────────────────────────────────────
    # BUILD AEO TAB
    # ─────────────────────────────────────────────────────────
    def bld_aeo(aeo):
        c_aeo.controls.clear()
        c_aeo.controls.append(sec("LAYER 3 — AEO ANALYSIS (AI-Answer Friendliness)"))

        score_c=sc(aeo["score"])
        c_aeo.controls.append(ft.Container(
            content=ft.Row([
                ft.Text("AEO Score:",size=14,color=TEXT,font_family=MONO,weight=ft.FontWeight.BOLD),
                ft.Text(f" {aeo['score']}/100",size=22,color=score_c,font_family=MONO,weight=ft.FontWeight.BOLD),
            ]),
            padding=pxy(v=8,h=14),bgcolor=BG3,border_radius=8,
            border=ba(2,score_c),margin=mon(bottom=12),
        ))

        c_aeo.controls.append(ft.Row([
            stat_box("AEO Score", aeo["score"],               CYAN),
            stat_box("E-E-A-T",  f"{sum(aeo['eeat'].values())}/4", BLUE),
            stat_box("FAQs",     "Yes" if aeo["scores"]["faq"]==100 else "No",
                     GREEN if aeo["scores"]["faq"]==100 else RED),
        ],spacing=6))
        c_aeo.controls.append(ft.Container(height=12))

        names={
            "q_headings": ("Question-Based Headings", "HIGH"),
            "faq":        ("FAQ Section Present",      "HIGH"),
            "short_ans":  ("Short Direct Answers",     "HIGH"),
            "entities":   ("Semantic Entities (NLP)",  "HIGH"),
            "nlp":        ("NLP Topic Relevance",      "HIGH"),
            "struct_data":("Structured Data (Schema)", "HIGH"),
            "citable":    ("Citable Paragraphs",       "HIGH"),
            "eeat":       ("E-E-A-T Signals",          "HIGH"),
        }
        rows=[tbl_header(("AEO Signal",None),("Score",60),("Bar",160),("Importance",90),("Detail",None))]
        for i,(k,(label,imp)) in enumerate(names.items()):
            v=aeo["scores"].get(k,0); color=sc(v)
            detail=str(aeo["sigs"].get(k,""))[:35]
            rows.append(tbl_row([
                ft.Text(label,size=12,color=TEXT,width=180,font_family=MONO),
                ft.Text(str(v),size=12,color=color,width=60,weight=ft.FontWeight.BOLD,font_family=MONO),
                ft.Container(content=make_bar(v,150),width=160),
                ft.Text("HIGH",size=11,color=RED,width=90,font_family=MONO,weight=ft.FontWeight.BOLD),
                ft.Text(detail,size=11,color=DIM,expand=True,font_family=MONO,max_lines=2),
            ],alt=i%2==1))

        c_aeo.controls.append(ft.Container(
            content=ft.Column(rows,spacing=0),bgcolor=BG2,
            border_radius=10,border=ba(1,BORDER),clip_behavior=ft.ClipBehavior.HARD_EDGE))

        # E-E-A-T detail
        c_aeo.controls.append(sec("E-E-A-T SIGNAL DETAIL",CYAN))
        eeat_rows=[ft.Container(
            content=ft.Row([
                ft.Text("✓" if v else "✗",color=GREEN if v else RED,size=14,width=24,
                        font_family=MONO,weight=ft.FontWeight.BOLD),
                ft.Text(k,size=12,color=CYAN if v else DIM,font_family=MONO),
            ],spacing=8),padding=pxy(v=4,h=12),border=bb(1,BORDER))
            for k,v in aeo["eeat"].items()]
        c_aeo.controls.append(ft.Container(content=ft.Column(eeat_rows,spacing=0),
            bgcolor=BG2,border_radius=10,border=ba(1,BORDER),clip_behavior=ft.ClipBehavior.HARD_EDGE))

        if aeo.get("top_ents"):
            c_aeo.controls.append(sec("TOP NAMED ENTITIES",CYAN))
            ent_rows=[tbl_header(("Entity",180),("Type",100),("Count",None))]
            for (ent,lbl),cnt in aeo["top_ents"][:8]:
                ent_rows.append(ft.Container(
                    content=ft.Row([
                        ft.Text(ent,size=12,color=CYAN,width=180,font_family=MONO),
                        ft.Text(lbl,size=11,color=DIM, width=100,font_family=MONO),
                        ft.Text(f"x{cnt}",size=11,color=TEXT,font_family=MONO),
                    ],spacing=0),padding=pxy(v=5,h=12),border=bb(1,BORDER)))
            c_aeo.controls.append(ft.Container(content=ft.Column(ent_rows,spacing=0),
                bgcolor=BG2,border_radius=10,border=ba(1,BORDER),clip_behavior=ft.ClipBehavior.HARD_EDGE))

        if aeo["issues"]:
            c_aeo.controls.append(sec("AEO ISSUES",RED))
            for i in aeo["issues"]: c_aeo.controls.append(chip(i))

    # ─────────────────────────────────────────────────────────
    # BUILD RANK TAB
    # ─────────────────────────────────────────────────────────
    def bld_rank(rank,seo,aeo,raw):
        c_rank.controls.clear()
        c_rank.controls.append(sec("LAYER 5 — RANKING PROBABILITY ENGINE"))

        pred=rank["pred"]; pc=rc(pred)
        icon="🟢" if "HIGH" in pred else ("🟡" if "MEDIUM" in pred else "🔴")

        # Big verdict
        c_rank.controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"{icon}  RANK PROBABILITY SCORE",size=13,color=DIM,font_family=MONO),
                ft.Container(height=4),
                ft.Text(f"{rank['score']}/100",size=42,weight=ft.FontWeight.BOLD,color=pc,font_family=MONO),
                ft.Container(height=4),
                ft.Text(pred,size=16,color=pc,weight=ft.FontWeight.BOLD,font_family=MONO),
                ft.Text(f"Confidence Level: {rank['conf']}",size=12,color=DIM,font_family=MONO),
                ft.Container(height=8),
                make_bar(int(rank["score"]),300),
                ft.Container(height=8),
                ft.Text(
                    f"rank_score = SEO({seo['score']})×0.35  +  AEO({aeo['score']})×0.35  +  "
                    f"Backlinks({rank['comps']['Backlink Score']:.0f})×0.15  +  "
                    f"Depth({rank['comps']['Content Depth']:.0f})×0.15",
                    size=11,color=DIM,font_family=MONO,
                ),
            ],spacing=4,horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG3,border_radius=12,border=ba(2,pc),
            padding=pxy(v=22,h=28),alignment=ft.alignment.Alignment(x=0,y=0),
            margin=mon(bottom=14),
        ))

        # Components table
        c_rank.controls.append(sec("SCORE COMPONENTS",MAG))
        weights={"SEO Score":0.35,"AEO Score":0.35,"Backlink Score":0.15,"Content Depth":0.15}
        comp_rows=[tbl_header(("Component",None),("Weight",70),("Score",70),("Contribution",110),("Bar",None))]
        for i,(name,val) in enumerate(rank["comps"].items()):
            w=weights.get(name,0); contrib=round(val*w,1)
            comp_rows.append(tbl_row([
                ft.Text(name,size=12,color=TEXT,width=160,font_family=MONO),
                ft.Text(f"{int(w*100)}%",size=12,color=DIM,width=70,font_family=MONO),
                ft.Text(f"{val:.0f}",size=12,color=sc(int(val)),width=70,weight=ft.FontWeight.BOLD,font_family=MONO),
                ft.Text(f"+{contrib}",size=12,color=CYAN,width=110,font_family=MONO),
                ft.Container(content=make_bar(int(val),120),expand=True),
            ],alt=i%2==1))
        c_rank.controls.append(ft.Container(content=ft.Column(comp_rows,spacing=0),
            bgcolor=BG2,border_radius=10,border=ba(1,BORDER),clip_behavior=ft.ClipBehavior.HARD_EDGE))

        # Priority actions
        acts=[]
        if seo["score"]<70: acts.append((True,f"SEO score {seo['score']}/100 — fix SEO issues first"))
        if aeo["score"]<70: acts.append((False,f"AEO score {aeo['score']}/100 — add FAQ + question headings"))
        if not raw["schemas"]: acts.append((False,"Add JSON-LD schema markup (Article, FAQ, BreadcrumbList)"))
        if raw["wc"]<1000: acts.append((False,f"Content only {raw['wc']} words — aim for 1500+"))
        if seo["ilc"]<3: acts.append((False,f"Only {seo['ilc']} internal links — add more"))
        if not acts: acts.append((False,"✓ All major signals look strong!"))

        c_rank.controls.append(sec("PRIORITY ACTIONS",YELLOW))
        for is_err,msg in acts: c_rank.controls.append(chip(msg,is_err))

        c_rank.controls.append(ft.Container(height=16))

        def do_save(_):
            try:
                fname=save_report(store["raw"],store["seo"],store["aeo"],store["rank"])
                log(f"Report saved: {fname}","good"); snack(f"Saved: {fname}",GREEN)
            except Exception as ex: log(f"Save error: {ex}","error")

        c_rank.controls.append(ft.Button(
            content=ft.Text("💾  Save JSON Report",color=BG,weight=ft.FontWeight.BOLD,font_family=MONO),
            bgcolor=CDIM,height=44,on_click=do_save))

    # ─────────────────────────────────────────────────────────
    # RUN ANALYSIS
    # ─────────────────────────────────────────────────────────
    def run(_=None):
        url=url_f.value.strip()
        if not url: snack("Please enter a URL first",RED); return
        if not url.startswith("http"): url="https://"+url
        kw=kw_f.value.strip()
        try: bl=max(0,min(100,float(bl_f.value or "50")))
        except: bl=50.0
        btn.disabled=True; pbar.visible=True
        results.visible=False; tab_bar.visible=False
        clr(); page.update()

        def task():
            try:
                stxt.value="Layer 1 — Crawling..."; page.update()
                log(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing: {url}","info")
                log("Crawling page and extracting signals...","dim"); page.update()
                raw=crawl_page(url)
                log(f"Crawled in {raw['load']}s  |  {raw['wc']:,} words  |  {len(raw['il'])} internal links","good")

                stxt.value="Layer 2 — SEO analysis..."; page.update()
                log("Running SEO analysis...","dim"); page.update()
                seo=analyze_seo(raw,kw=kw)
                log(f"SEO Score: {seo['score']}/100","good")

                stxt.value="Layer 3 — AEO analysis..."; page.update()
                log("Running AEO analysis...","dim"); page.update()
                aeo=analyze_aeo(raw)
                log(f"AEO Score: {aeo['score']}/100","good")

                stxt.value="Layer 5 — Ranking probability..."; page.update()
                log("Computing ranking probability...","dim"); page.update()
                rank=rank_prob(seo["score"],aeo["score"],raw["wc"],seo["ilc"],bl)
                pk="good" if "HIGH" in rank["pred"] else ("warn" if "MEDIUM" in rank["pred"] else "error")
                log(f"Rank Score: {rank['score']}/100 — {rank['pred']}",pk)

                store.update({"raw":raw,"seo":seo,"aeo":aeo,"rank":rank})

                if seo["issues"]:
                    log("SEO Issues:","dim")
                    for i in seo["issues"]: log(f"  ⚠ {i}","warn")
                if aeo["issues"]:
                    log("AEO Issues:","dim")
                    for i in aeo["issues"]: log(f"  ⚠ {i}","warn")
                log("Analysis complete! ✓","good")

                bld_crawl(raw); bld_seo(seo,raw); bld_aeo(aeo); bld_rank(rank,seo,aeo,raw)
                sw(0); tab_bar.visible=True; results.visible=True

            except requests.exceptions.Timeout:
                log("Timed out after 10s — site is too slow or blocking bots. Try a different URL.","error")
            except requests.exceptions.ConnectionError:
                log("Connection error — check URL and network","error")
            except requests.exceptions.HTTPError as ex:
                log(f"HTTP error: {ex}","error")
            except Exception as ex:
                import traceback
                log(f"Error: {ex}","error")
                log(traceback.format_exc(),"dim")
            finally:
                btn.disabled=False; pbar.visible=False; stxt.value=""; page.update()

        threading.Thread(target=task,daemon=True).start()

    btn.on_click=run; url_f.on_submit=run
    page.update()

if __name__=="__main__":
    ft.app(main)
