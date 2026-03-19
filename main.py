#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       🎬  CINEFLUX  —  Movies Downloader  v7.0              ║
║  Desktop GUI + Web Server  |  Auto Lang  |  Custom Links   ║
╚══════════════════════════════════════════════════════════════╝
Desktop: python main.py
Web:     python main.py --web
Web:     python main.py --web 8080
"""

# ─── Auto-install ─────────────────────────────────────────────────────────────
import subprocess, sys
for _i,_n in [("yt_dlp","yt-dlp"),("requests","requests"),
              ("bs4","beautifulsoup4"),("langdetect","langdetect"),
              ("PIL","Pillow"),("flask","flask")]:
    try: __import__(_i)
    except ImportError:
        print(f"Installing {_n}...")
        subprocess.check_call([sys.executable,"-m","pip","install",_n,"-q"])

import os, json, threading, time
import yt_dlp, requests
from bs4 import BeautifulSoup

# Tkinter — sirf desktop mode mein load hoga
_WEB_MODE = "--web" in sys.argv or os.environ.get("RENDER") or os.environ.get("WEB_MODE")
if not _WEB_MODE:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog
    try:
        from PIL import Image, ImageTk
        import io as _io
        PIL_OK = True
    except ImportError:
        PIL_OK = False
else:
    PIL_OK = False

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Movies")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ✅ 1080p HARD CAP — Yahan change karo agar kabhi badhana ho
MAX_QUALITY_HEIGHT = 1080

C = {
    "bg":"#030a10","bg2":"#071420","bg3":"#0a1f30","panel":"#071825",
    "neon":"#00ffe7","neon2":"#ff3cac","neon3":"#f7c948",
    "dim":"#4a7a9b","text":"#c8f0ff","border":"#0a2a3a",
    "sel":"#021a14","sel2":"#1a1400",
}

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM LINKS — Memory only (restart pe reset)
# ══════════════════════════════════════════════════════════════════════════════

CUSTOM_LINKS: list = []   # sab memory mein — koi file nahi

def save_custom_links(links: list):
    pass   # memory only — kuch save nahi hota

def load_custom_links() -> list:
    return CUSTOM_LINKS

# ══════════════════════════════════════════════════════════════════════════════
#  AUTO LANGUAGE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════

def detect_industry(text: str) -> str | None:
    if not text or len(text.strip()) < 2:
        return None
    t = text.strip()

    def smatch(s, pairs):
        return any(lo <= ord(c) <= hi for c in s for lo,hi in pairs)

    if smatch(t,[(0x0C00,0x0C7F)]): return "3"
    if smatch(t,[(0x0B80,0x0BFF)]): return "4"
    if smatch(t,[(0x0D00,0x0D7F)]): return "6"
    if smatch(t,[(0x0C80,0x0CFF)]): return "7"
    if smatch(t,[(0x0A00,0x0A7F)]): return "8"
    if smatch(t,[(0x0600,0x06FF)]): return "5"
    if smatch(t,[(0x0900,0x097F)]):
        bh = ["bhojpuri","bhoji","pawan","khesari","dinesh","nirahua"]
        return "13" if any(k in t.lower() for k in bh) else "2"

    tl = t.lower()
    kw_map = [
        ("1",  ["hollywood","marvel","pixar","disney","warner","netflix original","amazon original"]),
        ("2",  ["bollywood","salman","shahrukh","aamir","hrithik","akshay kumar","hindi movie"]),
        ("3",  ["tollywood","telugu","ram charan","jr ntr","prabhas","allu arjun","mahesh babu"]),
        ("4",  ["kollywood","tamil","vijay","ajith","dhanush","rajinikanth","suriya"]),
        ("5",  ["lollywood","pakistani","lahore","fawad","mahira","urdu film"]),
        ("6",  ["mollywood","malayalam","mohanlal","mammootty","dulquer","fahadh"]),
        ("7",  ["sandalwood","kannada","yash","puneeth","darshan","kgf"]),
        ("8",  ["pollywood","punjabi movie","ammy virk","diljit","sonam bajwa"]),
        ("10", ["nollywood","nigerian","yoruba","igbo","genevieve","omotola"]),
        ("11", ["chhattisgarhi","chhollywood","cg movie"]),
        ("12", ["dollywood","nashville","country film"]),
        ("13", ["bhojpuri","bhojiwood","pawan singh","khesari lal","dinesh lal"]),
        ("14", ["ghollywood","ghanaian","akan","twi film","kumasi"]),
    ]
    for key, words in kw_map:
        if any(w in tl for w in words):
            return key

    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
        lang = detect(t)
        m = {"hi":"2","te":"3","ta":"4","ml":"6","kn":"7","pa":"8",
             "ur":"5","yo":"10","ig":"10","en":"1"}
        return m.get(lang, "1")
    except: pass

    return "1"

# ══════════════════════════════════════════════════════════════════════════════
#  FILM INDUSTRIES
# ══════════════════════════════════════════════════════════════════════════════
INDUSTRIES = {
    "1":  {"name":"Hollywood",   "icon":"🎪","lang":"English",       "region":"USA","keyword":"full movie english",             "sites":["yt_general","yt_fullmovie","tubi","pluto","plex","archive","dailymotion"]},
    "2":  {"name":"Bollywood",   "icon":"🇮🇳","lang":"Hindi",         "region":"Mumbai","keyword":"bollywood hindi full movie",      "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "3":  {"name":"Tollywood",   "icon":"🌺","lang":"Telugu",        "region":"AP/TG","keyword":"tollywood telugu full movie",     "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "4":  {"name":"Kollywood",   "icon":"🌴","lang":"Tamil",         "region":"Chennai","keyword":"kollywood tamil full movie",      "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "5":  {"name":"Lollywood",   "icon":"🇵🇰","lang":"Urdu","region":"Lahore","keyword":"lollywood pakistani full movie",  "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "6":  {"name":"Mollywood",   "icon":"🌿","lang":"Malayalam",     "region":"Kerala","keyword":"mollywood malayalam full movie",  "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "7":  {"name":"Sandalwood",  "icon":"🏯","lang":"Kannada",       "region":"Karnataka","keyword":"sandalwood kannada full movie",   "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "8":  {"name":"Pollywood",   "icon":"🌾","lang":"Punjabi",       "region":"Punjab","keyword":"pollywood punjabi full movie",    "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "9":  {"name":"Ollywood",    "icon":"🔶","lang":"Odia",          "region":"Odisha","keyword":"ollywood odia full movie",        "sites":["odia_yt","sidharth","tarang","sarthak","dailymotion","odia_archive"]},
    "10": {"name":"Nollywood",   "icon":"🌍","lang":"Yoruba/Igbo",   "region":"Nigeria","keyword":"nollywood nigerian full movie",   "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "11": {"name":"Chhollywood", "icon":"🌄","lang":"Chhattisgarhi", "region":"CG","keyword":"chhollywood chhattisgarhi full movie","sites":["yt_general","yt_fullmovie","dailymotion"]},
    "12": {"name":"Dollywood",   "icon":"🎸","lang":"English",       "region":"Nashville","keyword":"dollywood southern full movie",   "sites":["yt_general","yt_fullmovie","tubi","pluto","archive"]},
    "13": {"name":"Bhojiwood",   "icon":"🎺","lang":"Bhojpuri",      "region":"Bihar/UP","keyword":"bhojiwood bhojpuri full movie",   "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
    "14": {"name":"Ghollywood",  "icon":"🇬🇭","lang":"Akan/Twi",     "region":"Ghana","keyword":"ghollywood ghanaian full movie",  "sites":["yt_general","yt_fullmovie","dailymotion","archive"]},
}

# ══════════════════════════════════════════════════════════════════════════════
#  SEARCH BACKEND
# ══════════════════════════════════════════════════════════════════════════════
def fmt_views(n):
    try:
        n=int(n)
        if n>=1_000_000: return f"{n/1_000_000:.1f}M views"
        if n>=1_000: return f"{n/1_000:.0f}K views"
        return f"{n} views"
    except: return ""

def make_result(title,url,duration="",channel="",views="",thumb=""):
    return {"title":title,"url":url,"duration":str(duration),"channel":channel,"views":views,"thumb":thumb}

def yt_search(query):
    opts={"quiet":True,"no_warnings":True,"extract_flat":True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data=ydl.extract_info(f"ytsearch8:{query}",download=False)
    results=[]
    for e in (data.get("entries") or []):
        if not e: continue
        dur=e.get("duration",0) or 0; m,s=divmod(int(dur),60)
        vid=e.get("id","")
        url=e.get("url") or e.get("webpage_url") or (f"https://youtu.be/{vid}" if vid else "")
        if not url: continue
        vid_id = e.get("id","")
        thumb  = f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg" if vid_id else ""
        results.append(make_result(e.get("title","N/A"),url,f"{m}:{s:02d}",
                                   e.get("channel") or e.get("uploader",""),
                                   fmt_views(e.get("view_count",0)), thumb))
    return results

def archive_search(query,subject_filter=""):
    q=f"({query}) AND mediatype:movies"
    if subject_filter: q+=f" AND ({subject_filter})"
    params={"q":q,"fl[]":["identifier","title","creator","year"],"rows":8,"page":1,"output":"json"}
    try:
        docs=requests.get("https://archive.org/advancedsearch.php",params=params,
                          headers=HEADERS,timeout=10).json()["response"]["docs"]
    except: return []
    return [make_result(d.get("title",d.get("identifier","")),
                        f"https://archive.org/details/{d.get('identifier','')}",
                        str(d.get("year","?")),d.get("creator","Internet Archive"),"Public Domain ✅")
            for d in docs]

def dailymotion_search(query):
    params={"search":query,"fields":"id,title,duration,owner.screenname,views_total","limit":8,"sort":"relevance"}
    try: data=requests.get("https://api.dailymotion.com/videos",params=params,headers=HEADERS,timeout=10).json()
    except: return []
    results=[]
    for v in data.get("list",[]):
        dur=v.get("duration",0) or 0; m,s=divmod(dur,60)
        results.append(make_result(v.get("title","N/A"),f"https://www.dailymotion.com/video/{v['id']}",
                                   f"{m}:{s:02d}",v.get("owner.screenname","Dailymotion"),
                                   fmt_views(v.get("views_total",0))))
    return results

def is_direct_video_site(url: str) -> bool:
    """
    Check karo ki URL yt-dlp supported video site hai ya nahi.
    Normal websites (hdhub4u, filmyzilla, etc.) → False
    Video platforms (youtube, dailymotion, vimeo, etc.) → True
    """
    VIDEO_PLATFORMS = [
        "youtube.com","youtu.be","dailymotion.com","vimeo.com",
        "twitch.tv","facebook.com/watch","fb.watch","instagram.com/reel",
        "twitter.com","x.com","reddit.com","bilibili.com",
        "ok.ru","rutube.ru","rumble.com","odysee.com","bitchute.com",
    ]
    url_lower = url.lower()
    return any(p in url_lower for p in VIDEO_PLATFORMS)

def url_to_domain(url: str) -> str:
    """URL se clean domain nikalo — site: search ke liye."""
    return url.split("//")[-1].split("/")[0].replace("www.","").strip()

def normalize_url(url: str) -> str:
    """
    URL normalize karo:
    - mp4loop.xyz        → https://mp4loop.xyz
    - https://mp4loop.xyz/ → https://mp4loop.xyz
    - http://...         → as-is (http rakho)
    """
    url = url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url

def custom_link_search(link: dict, query: str, keyword: str) -> list:
    ltype = link.get("type","yt_search")
    name  = link.get("name","Custom")
    tmpl  = normalize_url(link.get("url_template",""))  # ✅ always normalize

    # ✅ AUTO-FIX: agar "direct" set hai lekin URL normal website hai
    # toh automatically yt_search use karo — error nahi aayega
    if ltype == "direct" and not is_direct_video_site(tmpl):
        print(f"[AUTO-FIX] '{name}' direct→yt_search (not a video platform): {tmpl}")
        ltype = "yt_search"

    if ltype == "yt_search":
        # URL se domain nikalo → site: search
        domain = url_to_domain(tmpl)
        return yt_search(f"{query} {keyword} site:{domain}" if domain else f"{query} {keyword}")

    elif ltype == "direct":
        try:
            url = tmpl.replace("{query}", query.replace(" ","+"))
            opts={"quiet":True,"no_warnings":True,"extract_flat":True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info=ydl.extract_info(url,download=False)
            results=[]
            entries = info.get("entries") or ([info] if info.get("title") else [])
            for e in entries[:8]:
                if not e: continue
                dur=e.get("duration",0) or 0; m,s=divmod(int(dur),60)
                u=e.get("webpage_url") or e.get("url","")
                if not u: continue
                results.append(make_result(e.get("title","N/A"),u,f"{m}:{s:02d}",
                                           e.get("channel") or e.get("uploader",name),
                                           fmt_views(e.get("view_count",0))))
            return results
        except Exception as ex:
            # ✅ Fallback: direct fail hua toh yt_search try karo
            print(f"[FALLBACK] direct failed for '{name}', trying yt_search: {ex}")
            domain = url_to_domain(tmpl)
            try:
                return yt_search(f"{query} {keyword} site:{domain}")
            except:
                return []
    return []

SITES = {
    "yt_general":   {"name":"YouTube",              "icon":"▶", "fn":lambda q,kw:yt_search(f"{q} {kw}")},
    "yt_fullmovie": {"name":"YouTube Full Movie",   "icon":"🎞","fn":lambda q,kw:yt_search(f"{q} {kw} free")},
    "archive":      {"name":"Internet Archive",     "icon":"🏛","fn":lambda q,kw:archive_search(q)},
    "dailymotion":  {"name":"Dailymotion",          "icon":"📹","fn":lambda q,kw:dailymotion_search(f"{q} {kw}")},
    "tubi":         {"name":"Tubi (via YouTube)",   "icon":"📺","fn":lambda q,kw:yt_search(f"{q} tubi full movie")},
    "pluto":        {"name":"Pluto TV",             "icon":"🪐","fn":lambda q,kw:yt_search(f"{q} pluto tv full movie")},
    "plex":         {"name":"Plex (via YouTube)",   "icon":"🟡","fn":lambda q,kw:yt_search(f"{q} plex free movie")},
    "odia_yt":      {"name":"Odia YouTube",         "icon":"🔶","fn":lambda q,kw:yt_search(f"{q} odia full movie")},
    "sidharth":     {"name":"Sidharth TV",          "icon":"📡","fn":lambda q,kw:yt_search(f"{q} odia sidharth tv")},
    "tarang":       {"name":"Tarang Cine",          "icon":"🌊","fn":lambda q,kw:yt_search(f"{q} odia tarang")},
    "sarthak":      {"name":"Sarthak Music",        "icon":"🎵","fn":lambda q,kw:yt_search(f"{q} odia sarthak music")},
    "odia_archive": {"name":"Archive (Odia)",       "icon":"🏛","fn":lambda q,kw:archive_search(q,"subject:odia OR subject:oriya")},
}

def get_all_site_keys_for_industry(ind_key: str) -> list:
    built_in = INDUSTRIES[ind_key]["sites"]
    custom = [f"__custom_{i}" for i,l in enumerate(CUSTOM_LINKS)
              if l.get("industry","all") in ("all", ind_key)]
    return built_in + custom

def get_site(key: str):
    if key.startswith("__custom_"):
        idx = int(key.split("_")[-1])
        if idx < len(CUSTOM_LINKS):
            lnk = CUSTOM_LINKS[idx]
            return {"name": lnk["name"], "icon":"🔗",
                    "fn": lambda q,kw,l=lnk: custom_link_search(l,q,kw)}
    return SITES.get(key)

def auto_pick_site(ind_key: str) -> str:
    sites = get_all_site_keys_for_industry(ind_key)
    custom = [s for s in sites if s.startswith("__custom_")]
    if len(custom) > 1:
        return "__all_custom__"   # parallel mode — sab ek saath
    if len(custom) == 1:
        return custom[0]
    return sites[0] if sites else "yt_general"

def get_qualities(url):
    """
    ✅ 1080p HARD CAP
    - MAX_QUALITY_HEIGHT (1080) se upar koi bhi format list mein nahi aayega
    - 4K (2160p), 1440p — completely filtered out
    - Download format string bhi capped rahega
    """
    opts={"quiet":True,"no_warnings":True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info(url,download=False)
    seen, ql = [], []
    for f in info.get("formats",[]):
        h = f.get("height")
        if not h or f.get("vcodec","none") == "none": continue
        if h > MAX_QUALITY_HEIGHT: continue   # ← 4K / 1440p BLOCK
        label = f"{h}p [{f.get('ext','?')}]"
        if label in seen: continue
        seen.append(label)
        ql.append({"label":label,"height":h})
    ql.sort(key=lambda x:x["height"], reverse=True)
    return ql, info.get("title","video")

# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════
class CineFluxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CINEFLUX v7.0 — Max 1080p | Auto Site | Custom Links")
        self.root.geometry("1200x800")
        self.root.minsize(980,680)
        self.root.configure(bg=C["bg"])

        self.movie_var       = tk.StringVar()
        self.sel_industry    = None
        self.sel_site_key    = None
        self.search_results  = []
        self.sel_result      = None
        self.qualities       = []
        self.sel_quality_idx = tk.IntVar(value=0)
        self.dl_folder       = tk.StringVar(value=DOWNLOAD_FOLDER)
        self._dl_cancel      = False
        self._detect_job     = None
        self._det_key        = None

        self._build_ui()
        self._clock_tick()
        self._log("CINEFLUX v7.0 — system online.", "ok")
        self._log("Auto lang detect + Auto site select active.", "warn")
        self._log("Odia/Ollywood = manual only.", "dim")
        self._log(f"Quality cap: MAX {MAX_QUALITY_HEIGHT}p  (4K blocked)", "warn")
        self._log(f"{len(CUSTOM_LINKS)} custom link(s) loaded.", "ok" if CUSTOM_LINKS else "dim")

    def _build_ui(self):
        self._build_header()
        self._build_step_bar()
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.nb = ttk.Notebook(body)
        self.nb.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        self._style_nb()
        self._build_tab1()
        self._build_tab2()
        self._build_tab3()
        self._build_tab4()
        self._build_tab5()

        right = tk.Frame(body, bg=C["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        self._build_lang_panel(right)
        self._build_links_panel(right)
        self._build_console(right)

    def _build_header(self):
        h = tk.Frame(self.root, bg=C["bg"], pady=8); h.pack(fill=tk.X, padx=12)
        tk.Label(h, text="CINE",  font=("Courier",22,"bold"), bg=C["bg"], fg=C["neon"]).pack(side=tk.LEFT)
        tk.Label(h, text="FLUX",  font=("Courier",22,"bold"), bg=C["bg"], fg=C["neon2"]).pack(side=tk.LEFT)
        tk.Label(h, text="  v7.0",font=("Courier",11),        bg=C["bg"], fg=C["dim"]).pack(side=tk.LEFT, pady=6)
        r = tk.Frame(h, bg=C["bg"]); r.pack(side=tk.RIGHT)
        self.clock_lbl = tk.Label(r, text="00:00:00", font=("Courier",13,"bold"), bg=C["bg"], fg=C["neon3"])
        self.clock_lbl.pack(side=tk.RIGHT, padx=10)
        # ✅ MAX 1080p badge header mein
        tk.Label(r, text="● MAX 1080p", font=("Courier",9), bg=C["bg"], fg=C["neon2"]).pack(side=tk.RIGHT, padx=6)
        tk.Label(r, text="● AUTO SITE", font=("Courier",9), bg=C["bg"], fg=C["neon2"]).pack(side=tk.RIGHT, padx=6)
        tk.Label(r, text="● AUTO LANG", font=("Courier",9), bg=C["bg"], fg=C["neon"]).pack(side=tk.RIGHT, padx=6)
        tk.Frame(self.root, bg=C["neon"], height=1).pack(fill=tk.X, padx=12, pady=(0,6))

    def _build_step_bar(self):
        bar = tk.Frame(self.root, bg=C["bg"]); bar.pack(fill=tk.X, padx=12, pady=(0,8))
        self.step_lbls = []
        for s in ["01·TITLE","02·INDUSTRY","03·RESULTS","04·QUALITY","05·DOWNLOAD"]:
            l = tk.Label(bar, text=s, font=("Courier",9,"bold"), bg=C["bg"], fg=C["dim"], padx=12, pady=4)
            l.pack(side=tk.LEFT); self.step_lbls.append(l)

    def _set_step(self, idx):
        for i,l in enumerate(self.step_lbls):
            l.config(fg=C["neon3"] if i<idx else (C["neon"] if i==idx else C["dim"]))
        self.nb.select(idx)

    def _style_nb(self):
        s=ttk.Style(); s.theme_use("default")
        s.configure("TNotebook",     background=C["bg"],   borderwidth=0)
        s.configure("TNotebook.Tab", background=C["bg2"],  foreground=C["dim"],
                    font=("Courier",9), padding=[10,4], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected",C["panel"])],
              foreground=[("selected",C["neon"])])

    def _build_lang_panel(self, parent):
        lp = tk.Frame(parent, bg=C["panel"],
                      highlightthickness=1, highlightbackground=C["border"])
        lp.grid(row=0, column=0, sticky="ew", pady=(0,6))
        tk.Label(lp, text="// LIVE DETECT", font=("Courier",8),
                 bg=C["panel"], fg=C["dim"]).pack(anchor="w", padx=10, pady=(8,2))
        self.det_icon_lbl = tk.Label(lp, text="?", font=("Segoe UI Emoji",24),
                                      bg=C["panel"], fg=C["text"])
        self.det_icon_lbl.pack(pady=(2,0))
        self.det_name_lbl = tk.Label(lp, text="——", font=("Courier",12,"bold"),
                                      bg=C["panel"], fg=C["neon"])
        self.det_name_lbl.pack()
        self.det_lang_lbl = tk.Label(lp, text="Type movie name...",
                                      font=("Courier",8), bg=C["panel"], fg=C["dim"],
                                      wraplength=175, justify="center")
        self.det_lang_lbl.pack(pady=(0,4))
        cf = tk.Frame(lp, bg=C["panel"], padx=10); cf.pack(fill=tk.X, pady=(0,2))
        tk.Label(cf, text="CONFIDENCE", font=("Courier",7), bg=C["panel"], fg=C["dim"]).pack(anchor="w")
        bbg = tk.Frame(cf, bg=C["bg3"], height=4); bbg.pack(fill=tk.X)
        self.conf_bar = tk.Frame(bbg, bg=C["neon"], height=4); self.conf_bar.place(x=0,y=0,relheight=1,relwidth=0)
        self.det_conf_lbl = tk.Label(lp, text="0%", font=("Courier",8),
                                      bg=C["panel"], fg=C["neon3"])
        self.det_conf_lbl.pack(pady=(0,2))
        self.det_site_lbl = tk.Label(lp, text="", font=("Courier",8),
                                      bg=C["panel"], fg=C["neon3"], wraplength=175, justify="center")
        self.det_site_lbl.pack(pady=(0,2))
        self.odia_notice = tk.Label(lp, text="🔶 Odia? → Manual chunno",
                                     font=("Courier",8), bg=C["panel"], fg=C["neon3"], justify="center")
        self.use_det_btn = self._neon_btn(lp, "USE DETECTED  →", self._use_detected, C["neon"])
        self.use_det_btn.pack(pady=(2,10), padx=10, fill=tk.X)
        self.use_det_btn.config(state="disabled")

    def _build_links_panel(self, parent):
        lf = tk.Frame(parent, bg=C["panel"],
                      highlightthickness=1, highlightbackground=C["border"])
        lf.grid(row=1, column=0, sticky="ew", pady=(0,6))
        hdr = tk.Frame(lf, bg=C["panel"]); hdr.pack(fill=tk.X, padx=10, pady=(8,4))
        tk.Label(hdr, text="// CUSTOM LINKS", font=("Courier",8),
                 bg=C["panel"], fg=C["dim"]).pack(side=tk.LEFT)
        self._neon_btn(hdr, "+ ADD", self._add_link_dialog, C["neon3"], small=True).pack(side=tk.RIGHT)
        lf2 = tk.Frame(lf, bg=C["panel"]); lf2.pack(fill=tk.X, padx=10, pady=(0,6))
        lf2.columnconfigure(0, weight=1)
        self.links_frame = tk.Frame(lf2, bg=C["panel"]); self.links_frame.pack(fill=tk.X)
        self._refresh_links_ui()

    def _refresh_links_ui(self):
        for w in self.links_frame.winfo_children(): w.destroy()
        if not CUSTOM_LINKS:
            tk.Label(self.links_frame, text="No custom links yet.\nClick + ADD to add one.",
                     font=("Courier",8), bg=C["panel"], fg=C["dim"], justify="left").pack(anchor="w")
            return
        for i,lnk in enumerate(CUSTOM_LINKS):
            row = tk.Frame(self.links_frame, bg=C["panel"]); row.pack(fill=tk.X, pady=1)
            ind_name = INDUSTRIES.get(lnk.get("industry","all"),{}).get("name","All") \
                       if lnk.get("industry","all") != "all" else "All"
            tk.Label(row, text=f"🔗 {lnk['name'][:18]}",
                     font=("Courier",9), bg=C["panel"], fg=C["neon3"]).pack(side=tk.LEFT)
            tk.Label(row, text=f"[{ind_name}]",
                     font=("Courier",7), bg=C["panel"], fg=C["dim"]).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="✕", font=("Courier",8,"bold"),
                      bg=C["panel"], fg=C["neon2"], relief="flat", bd=0, cursor="hand2",
                      command=lambda idx=i: self._remove_link(idx)).pack(side=tk.RIGHT)

    def _add_link_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Custom Link")
        dlg.geometry("440x210")
        dlg.configure(bg=C["bg"])
        dlg.grab_set()

        tk.Label(dlg, text="// ADD CUSTOM LINK", font=("Courier",12,"bold"),
                 bg=C["bg"], fg=C["neon"]).pack(anchor="w", padx=16, pady=(16,12))

        url_var = tk.StringVar()
        ind_var = tk.StringVar(value="all")

        # ── URL only ───────────────────────────────────────────────
        tk.Label(dlg, text="Site URL:", font=("Courier",9),
                 bg=C["bg"], fg=C["dim"]).pack(anchor="w", padx=16)
        tk.Entry(dlg, textvariable=url_var, font=("Courier",11),
                 bg=C["bg2"], fg=C["neon"], insertbackground=C["neon"],
                 relief="flat", bd=6).pack(fill=tk.X, padx=16, pady=(2,10))

        # ── Industry ───────────────────────────────────────────────
        tk.Label(dlg, text="Industry:", font=("Courier",9),
                 bg=C["bg"], fg=C["dim"]).pack(anchor="w", padx=16)
        ind_opts = ["all"] + [f"{k} - {v['name']}" for k,v in INDUSTRIES.items()]
        ttk.Combobox(dlg, textvariable=ind_var, values=ind_opts,
                     font=("Courier",9), state="readonly").pack(fill=tk.X, padx=16, pady=(2,14))

        # ── Save ───────────────────────────────────────────────────
        def save():
            url = url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "URL required!", parent=dlg); return
            url     = normalize_url(url)
            name    = url_to_domain(url)
            ind_val = ind_var.get().split(" - ")[0] if " - " in ind_var.get() else "all"
            CUSTOM_LINKS.append({"name":name, "url_template":url,
                                 "type":"yt_search", "industry":ind_val})
            save_custom_links(CUSTOM_LINKS)
            self._refresh_links_ui()
            self._log(f"Custom link added: {name}", "ok")
            dlg.destroy()

        self._neon_btn(dlg, "SAVE LINK", save, C["neon"]).pack(padx=16, fill=tk.X)

    def _remove_link(self, idx):
        if 0 <= idx < len(CUSTOM_LINKS):
            name = CUSTOM_LINKS[idx]["name"]
            del CUSTOM_LINKS[idx]
            save_custom_links(CUSTOM_LINKS)
            self._refresh_links_ui()
            self._log(f"Removed: {name}", "warn")

    def _build_console(self, parent):
        cw = tk.Frame(parent, bg=C["bg"]); cw.grid(row=2, column=0, sticky="nsew")
        cw.rowconfigure(1, weight=1); cw.columnconfigure(0, weight=1)
        tk.Label(cw, text="// SYSTEM LOG", font=("Courier",9), bg=C["bg"], fg=C["dim"]).grid(row=0, column=0, sticky="w", pady=(0,4))
        self.console = tk.Text(cw, bg=C["bg2"], fg=C["dim"], font=("Courier",10),
                               relief="flat", highlightthickness=1, highlightbackground=C["border"],
                               state="disabled", wrap="word", width=28)
        self.console.grid(row=1, column=0, sticky="nsew")
        sb = tk.Scrollbar(cw, command=self.console.yview, bg=C["bg2"], troughcolor=C["bg2"])
        sb.grid(row=1, column=1, sticky="ns")
        self.console["yscrollcommand"] = sb.set
        self.console.tag_config("ok",  foreground=C["neon"])
        self.console.tag_config("warn",foreground=C["neon3"])
        self.console.tag_config("err", foreground=C["neon2"])
        self.console.tag_config("dim", foreground=C["dim"])

    def _build_tab1(self):
        f = tk.Frame(self.nb, bg=C["panel"], padx=20, pady=20)
        self.nb.add(f, text=" 01 · TITLE ")
        tk.Label(f, text="// TARGET ACQUISITION", font=("Courier",10),
                 bg=C["panel"], fg=C["dim"]).pack(anchor="w", pady=(0,16))
        ef = tk.Frame(f, bg=C["neon"], padx=1, pady=1); ef.pack(fill=tk.X, pady=(0,4))
        self.movie_entry = tk.Entry(ef, textvariable=self.movie_var,
                                    font=("Courier",16,"bold"), bg=C["bg2"], fg=C["neon"],
                                    insertbackground=C["neon"], relief="flat", bd=8)
        self.movie_entry.pack(fill=tk.X)
        self.movie_entry.bind("<Return>", lambda e: self._go_next())
        self.movie_var.trace_add("write", self._on_movie_type)
        tk.Label(f, text="Type → language auto-detected  |  ENTER to proceed",
                 font=("Courier",9), bg=C["panel"], fg=C["dim"]).pack(anchor="w", pady=(2,12))
        self._neon_btn(f, "SCAN  →", self._go_next, C["neon"]).pack(anchor="w", pady=(0,20))
        self.auto_badge = tk.Label(f, text="", font=("Courier",10,"bold"),
                                    bg=C["panel"], fg=C["neon3"])
        self.auto_badge.pack(anchor="w", pady=(0,6))
        # ✅ Quality cap badge — Tab 1 mein visible
        tk.Label(f, text=f"⚡ Quality Cap: MAX {MAX_QUALITY_HEIGHT}p  |  4K / 1440p blocked",
                 font=("Courier",9), bg=C["panel"], fg=C["neon2"]).pack(anchor="w", pady=(0,4))
        tk.Label(f, text="DOWNLOAD FOLDER", font=("Courier",9),
                 bg=C["panel"], fg=C["dim"]).pack(anchor="w", pady=(16,4))
        fr = tk.Frame(f, bg=C["panel"]); fr.pack(fill=tk.X)
        tk.Entry(fr, textvariable=self.dl_folder, font=("Courier",10),
                 bg=C["bg2"], fg=C["neon3"], insertbackground=C["neon3"],
                 relief="flat", bd=6).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._neon_btn(fr, "BROWSE", self._browse_folder, C["neon3"], small=True).pack(side=tk.LEFT, padx=(6,0))

    def _build_tab2(self):
        f = tk.Frame(self.nb, bg=C["panel"], padx=16, pady=16)
        self.nb.add(f, text=" 02 · INDUSTRY ")
        tk.Label(f, text="// SELECT FILM INDUSTRY  (Odia = manual, others auto-skip)",
                 font=("Courier",10), bg=C["panel"], fg=C["dim"]).pack(anchor="w", pady=(0,12))
        grid = tk.Frame(f, bg=C["panel"]); grid.pack(fill=tk.BOTH, expand=True)
        self.ind_btns = {}
        for i,(k,ind) in enumerate(INDUSTRIES.items()):
            row,col = divmod(i,4)
            card = tk.Frame(grid, bg=C["bg2"], highlightthickness=1,
                            highlightbackground=C["border"], cursor="hand2")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            grid.columnconfigure(col, weight=1)
            tk.Label(card, text=ind["icon"], font=("Segoe UI Emoji",16),
                     bg=C["bg2"], fg=C["text"]).pack(pady=(10,2))
            tk.Label(card, text=ind["name"].upper(), font=("Courier",10,"bold"),
                     bg=C["bg2"], fg=C["text"]).pack()
            tk.Label(card, text=ind["lang"], font=("Courier",8),
                     bg=C["bg2"], fg=C["dim"]).pack(pady=(0,10))
            card.bind("<Button-1>", lambda e,key=k,c=card: self._select_industry(key,c))
            for ch in card.winfo_children():
                ch.bind("<Button-1>", lambda e,key=k,c=card: self._select_industry(key,c))
            self.ind_btns[k] = card

    def _build_tab3(self):
        f = tk.Frame(self.nb, bg=C["panel"], padx=16, pady=16)
        self.nb.add(f, text=" 03 · RESULTS ")
        f.rowconfigure(1, weight=1); f.columnconfigure(0, weight=1)

        self.results_hdr = tk.Label(f, text="// SEARCH RESULTS",
                                     font=("Courier",10), bg=C["panel"], fg=C["dim"])
        self.results_hdr.grid(row=0, column=0, sticky="w", pady=(0,6))

        # ── Scrollable Canvas frame ──────────────────────────────
        outer = tk.Frame(f, bg=C["bg2"], highlightthickness=1,
                         highlightbackground=C["border"])
        outer.grid(row=1, column=0, sticky="nsew")
        outer.rowconfigure(0, weight=1); outer.columnconfigure(0, weight=1)

        self.res_canvas = tk.Canvas(outer, bg=C["bg2"], highlightthickness=0)
        self.res_canvas.grid(row=0, column=0, sticky="nsew")
        vsb = tk.Scrollbar(outer, orient="vertical",
                           command=self.res_canvas.yview,
                           bg=C["bg2"], troughcolor=C["bg2"])
        vsb.grid(row=0, column=1, sticky="ns")
        self.res_canvas.configure(yscrollcommand=vsb.set)

        self.res_inner = tk.Frame(self.res_canvas, bg=C["bg2"])
        self._res_win  = self.res_canvas.create_window(
            (0,0), window=self.res_inner, anchor="nw")

        def _on_resize(e):
            self.res_canvas.itemconfig(self._res_win, width=e.width)
        self.res_canvas.bind("<Configure>", _on_resize)

        def _on_frame_resize(e):
            self.res_canvas.configure(scrollregion=self.res_canvas.bbox("all"))
        self.res_inner.bind("<Configure>", _on_frame_resize)

        # mousewheel scroll
        def _mw(e):
            self.res_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        self.res_canvas.bind_all("<MouseWheel>", _mw)

        self._thumb_refs  = []   # keep PIL refs alive
        self._sel_card    = None
        self._card_frames = []

        self._neon_btn(f, "SELECT  →", self._select_result, C["neon"]).grid(
            row=2, column=0, sticky="w", pady=(10,0))

    def _build_tab4(self):
        f = tk.Frame(self.nb, bg=C["panel"], padx=16, pady=16)
        self.nb.add(f, text=" 04 · QUALITY ")
        f.rowconfigure(2, weight=1); f.columnconfigure(0, weight=1)
        self.qual_hdr = tk.Label(f, text="// RESOLUTION MATRIX",
                                  font=("Courier",10), bg=C["panel"], fg=C["dim"])
        self.qual_hdr.grid(row=0, column=0, sticky="w", pady=(0,2))
        # ✅ Cap notice Tab 4
        tk.Label(f, text=f"⚡ Max quality: {MAX_QUALITY_HEIGHT}p  |  4K / 1440p filtered",
                 font=("Courier",8), bg=C["panel"], fg=C["neon2"]).grid(
                 row=1, column=0, sticky="w", pady=(0,10))
        self.qual_frame = tk.Frame(f, bg=C["panel"])
        self.qual_frame.grid(row=2, column=0, sticky="nsew")
        self._neon_btn(f, "CONFIRM  →", self._confirm_quality, C["neon2"]).grid(
            row=3, column=0, sticky="w", pady=(12,0))

    def _populate_qualities(self):
        for w in self.qual_frame.winfo_children(): w.destroy()
        self.sel_quality_idx.set(0)
        tk.Radiobutton(self.qual_frame,
                       text=f"  🏆  AUTO BEST  (max {MAX_QUALITY_HEIGHT}p)",
                       variable=self.sel_quality_idx, value=0,
                       font=("Courier",11,"bold"), bg=C["panel"], fg=C["neon"],
                       selectcolor=C["sel"], activebackground=C["panel"],
                       activeforeground=C["neon"]).pack(anchor="w", fill=tk.X, pady=3)
        for i,q in enumerate(self.qualities,1):
            h=q["height"]
            tag=" ← FULL HD" if h>=1080 else " ← HD" if h>=720 else " ← SD" if h<480 else ""
            col=C["neon"] if h>=1080 else C["neon3"] if h>=720 else C["dim"]
            tk.Radiobutton(self.qual_frame, text=f"  {q['label']}{tag}",
                           variable=self.sel_quality_idx, value=i,
                           font=("Courier",11), bg=C["panel"], fg=col,
                           selectcolor=C["sel"], activebackground=C["panel"],
                           activeforeground=col).pack(anchor="w", fill=tk.X, pady=2)

    def _build_tab5(self):
        f = tk.Frame(self.nb, bg=C["panel"], padx=20, pady=20)
        self.nb.add(f, text=" 05 · DOWNLOAD ")
        f.columnconfigure(0, weight=1)
        self.dl_title_lbl = tk.Label(f, text="AWAITING TARGET...",
                                      font=("Courier",13,"bold"), wraplength=700,
                                      bg=C["panel"], fg=C["neon"])
        self.dl_title_lbl.grid(row=0, column=0, sticky="w", pady=(0,4))
        self.dl_sub_lbl = tk.Label(f, text="", font=("Courier",9), bg=C["panel"], fg=C["dim"])
        self.dl_sub_lbl.grid(row=1, column=0, sticky="w", pady=(0,16))
        self.dl_pct_lbl = tk.Label(f, text="0%", font=("Courier",36,"bold"), bg=C["panel"], fg=C["neon"])
        self.dl_pct_lbl.grid(row=2, column=0, sticky="w", pady=(0,8))
        pb = tk.Frame(f, bg=C["neon"], height=2, pady=1); pb.grid(row=3, column=0, sticky="ew", pady=(0,8))
        pb.columnconfigure(0, weight=1)
        inner = tk.Frame(pb, bg=C["bg3"], height=8); inner.grid(row=0, column=0, sticky="ew"); inner.columnconfigure(0, weight=1)
        self.dl_bar_var = tk.DoubleVar(value=0)
        self.dl_bar = ttk.Progressbar(inner, variable=self.dl_bar_var, maximum=100, mode="determinate")
        self.dl_bar.grid(row=0, column=0, sticky="ew")
        style=ttk.Style(); style.configure("neon.Horizontal.TProgressbar",
                            troughcolor=C["bg3"],background=C["neon"],darkcolor=C["neon"],lightcolor=C["neon"],borderwidth=0)
        self.dl_bar.configure(style="neon.Horizontal.TProgressbar")
        stats=tk.Frame(f, bg=C["panel"]); stats.grid(row=4, column=0, sticky="w", pady=(4,16))
        self.dl_speed_lbl  = self._stat_block(stats,"SPEED",  "0.0 MB/s",0)
        self.dl_eta_lbl    = self._stat_block(stats,"ETA",    "--:--",   1)
        self.dl_size_lbl   = self._stat_block(stats,"RECEIVED","0 MB",   2)
        self.dl_status_lbl = self._stat_block(stats,"STATUS", "IDLE",    3)
        self.dl_misc_lbl   = tk.Label(f, text="", font=("Courier",9), bg=C["panel"], fg=C["dim"])
        self.dl_misc_lbl.grid(row=5, column=0, sticky="w", pady=(0,8))
        br=tk.Frame(f, bg=C["panel"]); br.grid(row=6, column=0, sticky="w", pady=(0,16))
        self.cancel_btn = self._neon_btn(br,"CANCEL",self._cancel_dl,C["neon2"])
        self.cancel_btn.pack(side=tk.LEFT, padx=(0,10)); self.cancel_btn.config(state="disabled")
        self._neon_btn(br,"NEW DOWNLOAD",self._reset,C["neon"]).pack(side=tk.LEFT)

    def _stat_block(self, parent, label, value, col):
        f=tk.Frame(parent, bg=C["panel"], padx=16, pady=8,
                   highlightthickness=1, highlightbackground=C["border"])
        f.grid(row=0, column=col, padx=(0,8))
        v=tk.Label(f, text=value, font=("Courier",13,"bold"), bg=C["panel"], fg=C["neon3"]); v.pack()
        tk.Label(f, text=label, font=("Courier",8), bg=C["panel"], fg=C["dim"]).pack()
        return v

    def _neon_btn(self, parent, text, cmd, color, small=False):
        font=("Courier",9,"bold") if small else ("Courier",11,"bold")
        return tk.Button(parent, text=text, command=cmd, font=font,
                         bg=C["bg2"], fg=color, activebackground=color, activeforeground=C["bg"],
                         relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                         highlightthickness=1, highlightbackground=color)

    def _clock_tick(self):
        self.clock_lbl.config(text=time.strftime("%H:%M:%S"))
        self.root.after(1000, self._clock_tick)

    def _log(self, msg, tag="dim"):
        ts=time.strftime("%H:%M:%S")
        self.console.config(state="normal")
        self.console.insert(tk.END, f"[{ts}] {msg}\n", tag)
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def _on_movie_type(self, *args):
        if self._detect_job: self.root.after_cancel(self._detect_job)
        self._detect_job = self.root.after(300, self._run_detect)

    def _run_detect(self):
        text = self.movie_var.get().strip()
        if not text or len(text) < 2:
            self._clear_detect(); return
        key = detect_industry(text)
        self._det_key = key
        if key is None:
            self.det_icon_lbl.config(text="?")
            self.det_name_lbl.config(text="UNKNOWN", fg=C["dim"])
            self.det_lang_lbl.config(text="Unknown — select manually", fg=C["dim"])
            self.det_conf_lbl.config(text="—")
            self.conf_bar.place(relwidth=0)
            self.odia_notice.pack(pady=(2,4))
            self.use_det_btn.config(state="disabled")
            self.auto_badge.config(text="")
            self.det_site_lbl.config(text="")
        else:
            ind  = INDUSTRIES[key]
            conf = 95 if any(ord(c)>127 for c in text) else (80 if len(text)>5 else 55)
            site_key  = auto_pick_site(key)
            all_keys  = get_all_site_keys_for_industry(key)
            cust_keys = [k for k in all_keys if k.startswith("__custom_")]
            if len(cust_keys) > 1:
                site_name = f"ALL {len(cust_keys)} CUSTOM SITES"
            elif site_key == "__all_custom__" or cust_keys:
                site_obj  = get_site(cust_keys[0]) if cust_keys else None
                site_name = site_obj["name"] if site_obj else "Custom"
            else:
                site_obj  = get_site(site_key)
                site_name = site_obj["name"] if site_obj else "YouTube"
            self.det_icon_lbl.config(text=ind["icon"])
            self.det_name_lbl.config(text=ind["name"].upper(), fg=C["neon"])
            self.det_lang_lbl.config(text=f"{ind['lang']} — {ind['region']}", fg=C["text"])
            self.det_conf_lbl.config(text=f"{conf}%")
            self.conf_bar.place(relwidth=conf/100)
            self.odia_notice.pack_forget()
            self.use_det_btn.config(state="normal")
            self.auto_badge.config(
                text=f"✓ Auto: {ind['name']}  |  Site: {site_name}")
            self.det_site_lbl.config(text=f"Auto site: {site_name}")
            self._log(f"Detect: {ind['name']} [{conf}%] → {site_name}", "ok")

    def _clear_detect(self):
        self.det_icon_lbl.config(text="?")
        self.det_name_lbl.config(text="——", fg=C["neon"])
        self.det_lang_lbl.config(text="Type movie name...", fg=C["dim"])
        self.det_conf_lbl.config(text="0%")
        self.conf_bar.place(relwidth=0)
        self.odia_notice.pack_forget()
        self.use_det_btn.config(state="disabled")
        self.auto_badge.config(text="")
        self.det_site_lbl.config(text="")
        self._det_key = None

    def _use_detected(self):
        if not self._det_key: return
        movie = self.movie_var.get().strip()
        if not movie: self._log("Movie title empty.", "err"); return
        card = self.ind_btns.get(self._det_key)
        if card: self._select_industry(self._det_key, card)

    def _go_next(self):
        movie = self.movie_var.get().strip()
        if not movie:
            self.movie_entry.config(highlightbackground=C["neon2"])
            self._log("ERROR: Movie title empty.", "err"); return
        self.movie_entry.config(highlightbackground=C["neon"])
        if self._det_key:
            ind  = INDUSTRIES[self._det_key]
            self._log(f"AUTO: {ind['name']} → searching...", "ok")
            self.sel_industry = self._det_key
            card = self.ind_btns.get(self._det_key)
            if card:
                for c in self.ind_btns.values():
                    c.config(highlightbackground=C["border"], bg=C["bg2"])
                    for ch in c.winfo_children(): ch.config(bg=C["bg2"])
                card.config(highlightbackground=C["neon"], bg=C["sel"])
                for ch in card.winfo_children(): ch.config(bg=C["sel"])
            site_key = auto_pick_site(self._det_key)
            self.sel_site_key = site_key
            all_keys  = get_all_site_keys_for_industry(self._det_key)
            cust_keys = [k for k in all_keys if k.startswith("__custom_")]
            if len(cust_keys) > 1:
                self._log(f"Parallel: {len(cust_keys)} custom sites ek saath", "ok")
            elif cust_keys:
                site_obj = get_site(cust_keys[0])
                self._log(f"Auto site: {site_obj['name'] if site_obj else site_key}", "ok")
            else:
                site_obj = get_site(site_key)
                self._log(f"Auto site: {site_obj['name'] if site_obj else site_key}", "ok")
            self._do_search()
        else:
            self._log("Unknown script → choose industry manually.", "warn")
            self._set_step(1)

    def _select_industry(self, key, card):
        for c in self.ind_btns.values():
            c.config(highlightbackground=C["border"], bg=C["bg2"])
            for ch in c.winfo_children(): ch.config(bg=C["bg2"])
        card.config(highlightbackground=C["neon"], bg=C["sel"])
        for ch in card.winfo_children(): ch.config(bg=C["sel"])
        self.sel_industry = key
        ind = INDUSTRIES[key]
        self._log(f"Industry: {ind['name']}", "ok")
        site_key  = auto_pick_site(key)
        self.sel_site_key = site_key
        all_keys  = get_all_site_keys_for_industry(key)
        cust_keys = [k for k in all_keys if k.startswith("__custom_")]
        if len(cust_keys) > 1:
            self._log(f"Parallel: {len(cust_keys)} custom sites ek saath", "ok")
        elif cust_keys:
            site_obj = get_site(cust_keys[0])
            self._log(f"Auto site: {site_obj['name'] if site_obj else site_key}", "ok")
        else:
            site_obj = get_site(site_key)
            self._log(f"Auto site: {site_obj['name'] if site_obj else site_key}", "ok")
        self._do_search()

    def _do_search(self):
        movie   = self.movie_var.get().strip()
        ind     = INDUSTRIES[self.sel_industry]
        keyword = ind["keyword"]

        # ✅ Sabhi custom links collect karo jo is industry ke liye hain
        all_keys    = get_all_site_keys_for_industry(self.sel_industry)
        custom_keys = [k for k in all_keys if k.startswith("__custom_")]

        if custom_keys:
            # ── PARALLEL MODE — sab custom links ek saath ──────────
            names = [get_site(k)["name"] for k in custom_keys if get_site(k)]
            self.results_hdr.config(
                text=f"// SEARCHING: {movie.upper()} on {len(custom_keys)} SITES PARALLEL...")
            self._log(f"Parallel search: {', '.join(names)}", "ok")
            self._set_step(2)

            def run_parallel():
                from concurrent.futures import ThreadPoolExecutor, as_completed
                all_results = []
                seen_urls   = set()

                def search_one(key):
                    site = get_site(key)
                    if not site: return []
                    try:
                        res = site["fn"](movie, keyword)
                        self.root.after(0, lambda n=site["name"], c=len(res):
                                        self._log(f"  {n}: {c} results", "ok"))
                        return res
                    except Exception as ex:
                        self.root.after(0, lambda n=site["name"], e=str(ex):
                                        self._log(f"  {n}: error — {e[:40]}", "err"))
                        return []

                with ThreadPoolExecutor(max_workers=len(custom_keys)) as ex:
                    futures = {ex.submit(search_one, k): k for k in custom_keys}
                    for f in as_completed(futures):
                        for r in f.result():
                            if r["url"] not in seen_urls:
                                seen_urls.add(r["url"])
                                all_results.append(r)

                # fallback agar koi result nahi mila
                if not all_results:
                    try:
                        all_results = yt_search(f"{movie} {keyword}")
                        self.root.after(0, lambda: self._log("Fallback: YouTube used.", "warn"))
                    except: pass

                self.root.after(0, lambda: self._show_results_final(
                    all_results, label=f"{len(custom_keys)} CUSTOM SITES"))

            threading.Thread(target=run_parallel, daemon=True).start()

        else:
            # ── SINGLE MODE — original flow ─────────────────────────
            site = get_site(self.sel_site_key)
            self.results_hdr.config(
                text=f"// SEARCHING: {movie.upper()} on {site['name'].upper() if site else '?'}...")
            self._set_step(2)
            def run():
                try:
                    results = site["fn"](movie, keyword) if site else []
                    if not results:
                        self._log("No results. Trying fallback...", "warn")
                        results = yt_search(f"{movie} {keyword}")
                    self.root.after(0, lambda: self._show_results_final(results))
                except Exception as e:
                    self.root.after(0, lambda: self._log(f"Search error: {e}", "err"))
            threading.Thread(target=run, daemon=True).start()

    def _show_results(self, results):
        self._show_results_final(results)

    def _show_results_final(self, results, label=None):
        self.search_results = results
        if not label:
            site = get_site(self.sel_site_key)
            label = site["name"].upper() if site else "RESULTS"
        self.results_hdr.config(text=f"// {label} — {len(results)} FOUND")

        # clear old cards
        for w in self.res_inner.winfo_children(): w.destroy()
        self._thumb_refs.clear()
        self._card_frames.clear()
        self._sel_card = None

        for i, r in enumerate(results):
            self._build_result_card(i, r)

        self.res_canvas.yview_moveto(0)
        self._log(f"{len(results)} results found.", "ok")

        # load thumbnails in background
        threading.Thread(target=self._load_thumbs, args=(results,), daemon=True).start()

    def _build_result_card(self, idx, r):
        """Ek result card banao — thumbnail + title + info."""
        card = tk.Frame(self.res_inner, bg=C["bg3"],
                        highlightthickness=1, highlightbackground=C["border"],
                        cursor="hand2")
        card.pack(fill=tk.X, padx=6, pady=3)
        self._card_frames.append(card)

        # thumbnail placeholder
        thumb_lbl = tk.Label(card, bg=C["bg3"], width=14, height=4,
                             text="🎬", font=("Segoe UI Emoji",18),
                             fg=C["dim"])
        thumb_lbl.pack(side=tk.LEFT, padx=(8,10), pady=8)
        card._thumb_lbl = thumb_lbl

        # info
        info = tk.Frame(card, bg=C["bg3"]); info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)
        num_lbl = tk.Label(info, text=f"{idx+1:02d}.", font=("Courier",9),
                           bg=C["bg3"], fg=C["dim"])
        num_lbl.pack(anchor="w")
        title_lbl = tk.Label(info, text=r["title"], font=("Courier",10,"bold"),
                             bg=C["bg3"], fg=C["text"], wraplength=500, justify="left")
        title_lbl.pack(anchor="w")
        meta = f"⏱ {r['duration']}  {r.get('channel','')[:30]}  {r.get('views','')}"
        tk.Label(info, text=meta, font=("Courier",8),
                 bg=C["bg3"], fg=C["dim"]).pack(anchor="w", pady=(2,0))

        # click to select
        def on_click(e, i=idx):
            # deselect old
            if self._sel_card is not None and self._sel_card < len(self._card_frames):
                old = self._card_frames[self._sel_card]
                old.config(highlightbackground=C["border"], bg=C["bg3"])
                for w in old.winfo_children():
                    w.config(bg=C["bg3"])
                    for ww in w.winfo_children():
                        try: ww.config(bg=C["bg3"])
                        except: pass
            # select new
            card.config(highlightbackground=C["neon"], bg=C["sel"])
            for w in card.winfo_children():
                w.config(bg=C["sel"])
                for ww in w.winfo_children():
                    try: ww.config(bg=C["sel"])
                    except: pass
            self._sel_card = i
            self._log(f"Selected: {self.search_results[i]['title'][:40]}", "ok")

        def on_dbl(e, i=idx):
            on_click(e, i)
            self._select_result()

        for widget in [card, thumb_lbl, info, title_lbl, num_lbl]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Double-Button-1>", on_dbl)

    def _load_thumbs(self, results):
        """Background mein thumbnails fetch karo aur cards mein set karo."""
        if not PIL_OK:
            return
        THUMB_W, THUMB_H = 120, 68
        for i, r in enumerate(results):
            thumb_url = r.get("thumb","")
            if not thumb_url:
                continue
            try:
                resp = requests.get(thumb_url, timeout=6, headers=HEADERS)
                img  = Image.open(_io.BytesIO(resp.content)).resize(
                    (THUMB_W, THUMB_H), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                def _set(ph=photo, idx=i):
                    if idx < len(self._card_frames):
                        card = self._card_frames[idx]
                        lbl  = card._thumb_lbl
                        lbl.config(image=ph, text="", width=THUMB_W, height=THUMB_H)
                        self._thumb_refs.append(ph)
                self.root.after(0, _set)
            except:
                pass

    def _select_result(self):
        idx = self._sel_card
        if idx is None: self._log("Pehle ek result click karo.", "warn"); return
        if idx >= len(self.search_results): return
        self.sel_result = self.search_results[idx]
        self._log(f"Selected: {self.sel_result['title'][:40]}...", "ok")
        self._log("Fetching quality formats...", "warn")
        self.qual_hdr.config(text="// FETCHING QUALITY OPTIONS...")
        self._set_step(3)
        def run():
            try:
                ql,title = get_qualities(self.sel_result["url"])
                self.qualities = ql
                self.root.after(0, lambda: self._ready_quality(title))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Quality error: {e}", "err"))
        threading.Thread(target=run, daemon=True).start()

    def _ready_quality(self, title):
        self.qual_hdr.config(text=f"// {title[:55]}{'...' if len(title)>55 else ''}")
        self._populate_qualities()
        self._log(f"{len(self.qualities)} options found (max {MAX_QUALITY_HEIGHT}p).", "ok")
        self._set_step(3)

    def _confirm_quality(self):
        idx = self.sel_quality_idx.get()
        if idx == 0:
            # ✅ Auto Best — lekin 1080p se upar NAHI jayega
            fmt   = f"bestvideo[height<={MAX_QUALITY_HEIGHT}]+bestaudio/best[height<={MAX_QUALITY_HEIGHT}]"
            label = f"AUTO BEST (max {MAX_QUALITY_HEIGHT}p)"
        elif 1 <= idx <= len(self.qualities):
            h     = self.qualities[idx-1]["height"]
            fmt   = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
            label = self.qualities[idx-1]["label"]
        else:
            fmt   = f"bestvideo[height<={MAX_QUALITY_HEIGHT}]+bestaudio/best[height<={MAX_QUALITY_HEIGHT}]"
            label = f"AUTO BEST (max {MAX_QUALITY_HEIGHT}p)"
        self._log(f"Quality: {label}", "ok")
        self._start_download(fmt, label)

    def _start_download(self, fmt_choice, quality_label):
        self._set_step(4)
        title = self.sel_result["title"]
        ind   = INDUSTRIES[self.sel_industry]
        site  = get_site(self.sel_site_key)
        self.dl_title_lbl.config(text=title[:80]+("..." if len(title)>80 else ""))
        self.dl_sub_lbl.config(text=f"{ind['name']}  /  {site['name'] if site else '?'}  /  {quality_label}")
        self.dl_bar_var.set(0); self.dl_pct_lbl.config(text="0%")
        self.dl_status_lbl.config(text="CONNECTING", fg=C["neon3"])
        self.cancel_btn.config(state="normal"); self._dl_cancel = False
        folder = self.dl_folder.get() or DOWNLOAD_FOLDER
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, "%(title)s.%(ext)s")

        def progress_hook(d):
            if self._dl_cancel: raise Exception("Cancelled")
            if d["status"] == "downloading":
                total=d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done=d.get("downloaded_bytes",0); speed=d.get("speed") or 0; eta=d.get("eta") or 0
                if total:
                    pct=done/total*100; spd=f"{speed/1_048_576:.1f} MB/s"
                    rec=f"{done/1_048_576:.1f} MB"; mm,ss=divmod(int(eta),60)
                    seg=f"WRITING {done/1_048_576:.1f}MB / {total/1_048_576:.1f}MB"
                    self.root.after(0,lambda p=pct,s=spd,r=rec,e=f"{mm}:{ss:02d}",g=seg:
                                    self._update_dl_ui(p,s,r,e,g))
            elif d["status"]=="finished":
                self.root.after(0,lambda:self._update_dl_ui(100,"—","—","00:00","MERGING..."))

        def run():
            opts={"format":fmt_choice,"outtmpl":out,"merge_output_format":"mp4",
                  "progress_hooks":[progress_hook],"quiet":True,"no_warnings":True}
            try:
                self._log("Download started...", "ok")
                with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([self.sel_result["url"]])
                if not self._dl_cancel: self.root.after(0, self._download_complete)
            except Exception as e:
                self.root.after(0, lambda: self._download_error(str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _update_dl_ui(self, pct, speed, received, eta, misc):
        self.dl_bar_var.set(pct); self.dl_pct_lbl.config(text=f"{pct:.1f}%")
        self.dl_speed_lbl.config(text=speed); self.dl_eta_lbl.config(text=eta)
        self.dl_size_lbl.config(text=received); self.dl_misc_lbl.config(text=misc)
        self.dl_status_lbl.config(text="DOWNLOADING", fg=C["neon3"])

    def _download_complete(self):
        self.dl_bar_var.set(100); self.dl_pct_lbl.config(text="100%", fg=C["neon"])
        self.dl_status_lbl.config(text="COMPLETE", fg=C["neon"])
        self.dl_misc_lbl.config(text=f"SAVED → {self.dl_folder.get()}")
        self.cancel_btn.config(state="disabled")
        self._log("Download complete!", "ok")
        messagebox.showinfo("CINEFLUX", f"Done!\nSaved to:\n{self.dl_folder.get()}")

    def _download_error(self, msg):
        self.dl_status_lbl.config(text="FAILED", fg=C["neon2"])
        self.dl_misc_lbl.config(text=f"ERROR: {msg[:80]}")
        self.cancel_btn.config(state="disabled")
        self._log(f"Failed: {msg[:60]}", "err")

    def _cancel_dl(self):
        self._dl_cancel = True
        self.dl_status_lbl.config(text="CANCELLED", fg=C["neon2"])
        self.cancel_btn.config(state="disabled")
        self._log("Cancelled.", "warn")

    def _reset(self):
        self.movie_var.set("")
        self.sel_industry=None; self.sel_site_key=None
        self.search_results=[]; self.sel_result=None; self.qualities=[]
        self.sel_quality_idx.set(0); self.dl_bar_var.set(0)
        self.dl_pct_lbl.config(text="0%", fg=C["neon"])
        self.dl_status_lbl.config(text="IDLE", fg=C["neon3"]); self.dl_misc_lbl.config(text="")
        for c in self.ind_btns.values():
            c.config(highlightbackground=C["border"], bg=C["bg2"])
            for ch in c.winfo_children(): ch.config(bg=C["bg2"])
        for w in self.res_inner.winfo_children(): w.destroy()
        self._thumb_refs.clear(); self._card_frames.clear(); self._sel_card = None
        self._clear_detect(); self._set_step(0)
        self._log("Reset. Ready.", "ok")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder: self.dl_folder.set(folder)

# ══════════════════════════════════════════════════════════════════════════════
#  WEB SERVER — Flask (mobile/browser access)
#  Run: python main.py --web        → web server on port 5000
#  Run: python main.py --web 8080   → custom port
# ══════════════════════════════════════════════════════════════════════════════

HTML_PAGE = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">\n<title>CineFlux</title>\n<style>\n  :root {\n    --bg:#030a10; --bg2:#071420; --bg3:#0a1f30; --panel:#071825;\n    --neon:#00ffe7; --neon2:#ff3cac; --neon3:#f7c948;\n    --dim:#4a7a9b; --text:#c8f0ff; --border:#0a2a3a;\n  }\n  * { box-sizing:border-box; margin:0; padding:0; }\n  body { background:var(--bg); color:var(--text); font-family:\'Courier New\',monospace;\n         min-height:100vh; padding-bottom:40px; }\n\n  /* ── HEADER ── */\n  .header { display:flex; align-items:center; justify-content:space-between;\n            padding:14px 16px; border-bottom:1px solid var(--neon); }\n  .logo { font-size:22px; font-weight:bold; }\n  .logo span:first-child { color:var(--neon); }\n  .logo span:last-child  { color:var(--neon2); }\n  .badges { display:flex; gap:6px; flex-wrap:wrap; }\n  .badge  { font-size:9px; color:var(--neon2); border:1px solid var(--neon2);\n            padding:2px 6px; border-radius:3px; }\n\n  /* ── STEPS ── */\n  .steps { display:flex; padding:10px 16px; gap:4px; overflow-x:auto; }\n  .step  { font-size:9px; padding:4px 10px; border-radius:3px; white-space:nowrap;\n           color:var(--dim); border:1px solid var(--border); cursor:pointer; }\n  .step.active  { color:var(--neon);  border-color:var(--neon); }\n  .step.done    { color:var(--neon3); border-color:var(--neon3); }\n\n  /* ── SECTIONS ── */\n  .section { display:none; padding:16px; }\n  .section.active { display:block; }\n\n  /* ── INPUTS ── */\n  .field-label { font-size:10px; color:var(--dim); margin-bottom:4px; }\n  input, select {\n    width:100%; background:var(--bg2); color:var(--neon);\n    border:1px solid var(--neon); border-radius:4px;\n    padding:12px 14px; font-size:16px; font-family:\'Courier New\',monospace;\n    outline:none; margin-bottom:12px;\n  }\n  select { color:var(--text); border-color:var(--border); }\n\n  /* ── BUTTONS ── */\n  .btn {\n    display:block; width:100%; padding:13px;\n    background:var(--bg2); color:var(--neon);\n    border:1px solid var(--neon); border-radius:4px;\n    font-size:13px; font-family:\'Courier New\',monospace; font-weight:bold;\n    cursor:pointer; text-align:center; margin-bottom:10px;\n    transition:background .15s;\n  }\n  .btn:active { background:var(--neon); color:var(--bg); }\n  .btn.pink   { color:var(--neon2); border-color:var(--neon2); }\n  .btn.pink:active { background:var(--neon2); color:var(--bg); }\n  .btn.gold   { color:var(--neon3); border-color:var(--neon3); }\n  .btn.gold:active { background:var(--neon3); color:var(--bg); }\n  .btn:disabled { opacity:.4; cursor:not-allowed; }\n\n  /* ── DETECT BOX ── */\n  .detect-box { background:var(--panel); border:1px solid var(--border);\n                border-radius:6px; padding:12px; margin-bottom:14px;\n                display:flex; align-items:center; gap:12px; }\n  .detect-icon { font-size:28px; }\n  .detect-info { flex:1; }\n  .detect-name { font-size:14px; font-weight:bold; color:var(--neon); }\n  .detect-lang { font-size:10px; color:var(--dim); }\n  .conf-bar-bg { background:var(--bg3); height:3px; border-radius:2px; margin-top:4px; }\n  .conf-bar    { background:var(--neon); height:3px; border-radius:2px;\n                 width:0; transition:width .4s; }\n\n  /* ── INDUSTRY GRID ── */\n  .ind-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:14px; }\n  .ind-card { background:var(--bg2); border:1px solid var(--border);\n              border-radius:6px; padding:10px 6px; text-align:center; cursor:pointer; }\n  .ind-card.sel { border-color:var(--neon); background:var(--panel); }\n  .ind-card .ic { font-size:20px; }\n  .ind-card .nm { font-size:9px; font-weight:bold; margin-top:3px; }\n  .ind-card .lg { font-size:8px; color:var(--dim); }\n\n  /* ── RESULT CARDS ── */\n  .result-card { background:var(--bg2); border:1px solid var(--border);\n                 border-radius:6px; padding:10px; margin-bottom:8px;\n                 display:flex; gap:10px; cursor:pointer; }\n  .result-card.sel { border-color:var(--neon); background:var(--panel); }\n  .result-thumb { width:90px; height:52px; object-fit:cover;\n                  border-radius:3px; background:var(--bg3);\n                  flex-shrink:0; display:flex; align-items:center;\n                  justify-content:center; font-size:20px; }\n  .result-thumb img { width:100%; height:100%; object-fit:cover; border-radius:3px; }\n  .result-info { flex:1; min-width:0; }\n  .result-num  { font-size:9px; color:var(--dim); }\n  .result-title{ font-size:12px; font-weight:bold; color:var(--text);\n                 white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }\n  .result-meta { font-size:10px; color:var(--dim); margin-top:3px; }\n\n  /* ── QUALITY ── */\n  .qual-item { background:var(--bg2); border:1px solid var(--border);\n               border-radius:4px; padding:11px 14px; margin-bottom:8px;\n               cursor:pointer; display:flex; align-items:center; gap:10px; }\n  .qual-item.sel { border-color:var(--neon2); background:var(--panel); }\n  .qual-item input[type=radio] { accent-color:var(--neon2); width:16px; height:16px; }\n  .qual-label { font-size:13px; }\n  .qual-tag   { font-size:10px; color:var(--neon3); margin-left:4px; }\n\n  /* ── PROGRESS ── */\n  .pct-big  { font-size:48px; font-weight:bold; color:var(--neon); margin:10px 0; }\n  .prog-bar-bg { background:var(--bg3); height:8px; border-radius:4px; margin:8px 0; }\n  .prog-bar    { background:var(--neon); height:8px; border-radius:4px;\n                 width:0; transition:width .4s; }\n  .stats-row { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin:10px 0; }\n  .stat-box  { background:var(--bg2); border:1px solid var(--border);\n               border-radius:4px; padding:10px; text-align:center; }\n  .stat-val  { font-size:14px; font-weight:bold; color:var(--neon3); }\n  .stat-lbl  { font-size:9px; color:var(--dim); }\n\n  /* ── LINKS PANEL ── */\n  .link-item { background:var(--bg2); border:1px solid var(--border);\n               border-radius:4px; padding:8px 12px; margin-bottom:6px;\n               display:flex; align-items:center; justify-content:space-between; }\n  .link-name { font-size:11px; color:var(--neon3); }\n  .link-ind  { font-size:9px; color:var(--dim); }\n  .del-btn   { background:none; border:none; color:var(--neon2);\n               font-size:16px; cursor:pointer; padding:0 4px; }\n\n  /* ── SPINNER ── */\n  .spinner { text-align:center; padding:30px; color:var(--dim); font-size:13px; }\n  .spin    { display:inline-block; animation:spin 1s linear infinite; }\n  @keyframes spin { to { transform:rotate(360deg); } }\n\n  /* ── TOAST ── */\n  .toast { position:fixed; bottom:20px; left:50%; transform:translateX(-50%);\n           background:var(--neon); color:var(--bg); padding:10px 20px;\n           border-radius:6px; font-size:12px; font-weight:bold;\n           opacity:0; transition:opacity .3s; pointer-events:none; z-index:999; }\n  .toast.show { opacity:1; }\n\n  .section-title { font-size:11px; color:var(--dim); margin-bottom:14px;\n                   padding-bottom:6px; border-bottom:1px solid var(--border); }\n  .info-text { font-size:10px; color:var(--neon3); margin-bottom:10px; }\n</style>\n</head>\n<body>\n\n<!-- HEADER -->\n<div class="header">\n  <div class="logo"><span>CINE</span><span>FLUX</span></div>\n  <div class="badges">\n    <span class="badge">MAX 1080p</span>\n    <span class="badge">AUTO LANG</span>\n  </div>\n</div>\n\n<!-- STEP BAR -->\n<div class="steps">\n  <div class="step active" id="stp0" onclick="goStep(0)">01·TITLE</div>\n  <div class="step"        id="stp1" onclick="goStep(1)">02·INDUSTRY</div>\n  <div class="step"        id="stp2" onclick="goStep(2)">03·RESULTS</div>\n  <div class="step"        id="stp3" onclick="goStep(3)">04·QUALITY</div>\n  <div class="step"        id="stp4" onclick="goStep(4)">05·DOWNLOAD</div>\n</div>\n\n<!-- ══ STEP 0 — TITLE ══ -->\n<div class="section active" id="sec0">\n  <div class="section-title">// TARGET ACQUISITION</div>\n\n  <div class="field-label">MOVIE NAME</div>\n  <input type="text" id="movieInput" placeholder="Type movie name..."\n         oninput="onMovieType()" onkeydown="if(event.key===\'Enter\') scanGo()">\n\n  <!-- detect box -->\n  <div class="detect-box" id="detectBox" style="display:none">\n    <div class="detect-icon" id="detIcon">?</div>\n    <div class="detect-info">\n      <div class="detect-name" id="detName">——</div>\n      <div class="detect-lang" id="detLang"></div>\n      <div class="conf-bar-bg"><div class="conf-bar" id="confBar"></div></div>\n    </div>\n  </div>\n\n  <button class="btn" onclick="scanGo()">⚡ SCAN &amp; SEARCH →</button>\n  <button class="btn gold" onclick="goStep(1)">SELECT INDUSTRY MANUALLY →</button>\n</div>\n\n<!-- ══ STEP 1 — INDUSTRY ══ -->\n<div class="section" id="sec1">\n  <div class="section-title">// SELECT FILM INDUSTRY</div>\n  <div class="ind-grid" id="indGrid"></div>\n  <button class="btn" onclick="industrySelected()">SEARCH →</button>\n</div>\n\n<!-- ══ STEP 2 — RESULTS ══ -->\n<div class="section" id="sec2">\n  <div class="section-title" id="resultsHdr">// SEARCH RESULTS</div>\n  <div id="resultsList"></div>\n  <button class="btn" id="selectBtn" onclick="selectResult()" disabled>SELECT →</button>\n</div>\n\n<!-- ══ STEP 3 — QUALITY ══ -->\n<div class="section" id="sec3">\n  <div class="section-title" id="qualHdr">// RESOLUTION MATRIX</div>\n  <div class="info-text">⚡ Max: 1080p — 4K filtered</div>\n  <div id="qualList"></div>\n  <button class="btn pink" onclick="confirmQuality()">CONFIRM &amp; DOWNLOAD →</button>\n</div>\n\n<!-- ══ STEP 4 — DOWNLOAD ══ -->\n<div class="section" id="sec4">\n  <div class="section-title">// DOWNLOAD</div>\n  <div id="dlTitle" style="font-size:13px;font-weight:bold;margin-bottom:6px;color:var(--neon)"></div>\n  <div class="pct-big" id="dlPct">0%</div>\n  <div class="prog-bar-bg"><div class="prog-bar" id="dlBar"></div></div>\n  <div class="stats-row">\n    <div class="stat-box"><div class="stat-val" id="dlSpeed">—</div><div class="stat-lbl">SPEED</div></div>\n    <div class="stat-box"><div class="stat-val" id="dlEta">—</div><div class="stat-lbl">ETA</div></div>\n    <div class="stat-box"><div class="stat-val" id="dlSize">—</div><div class="stat-lbl">SIZE</div></div>\n    <div class="stat-box"><div class="stat-val" id="dlState">IDLE</div><div class="stat-lbl">STATUS</div></div>\n  </div>\n  <div id="dlActionArea"></div>\n  <button class="btn" onclick="resetAll()" style="margin-top:10px">🔄 NEW DOWNLOAD</button>\n\n  <!-- Custom Links Manager -->\n  <div class="section-title" style="margin-top:24px">// CUSTOM LINKS</div>\n  <input type="text" id="newLinkUrl" placeholder="https://mp4loop.xyz">\n  <select id="newLinkInd">\n    <option value="all">All Industries</option>\n  </select>\n  <button class="btn gold" onclick="addLink()">+ ADD LINK</button>\n  <div id="linksList"></div>\n</div>\n\n<!-- TOAST -->\n<div class="toast" id="toast"></div>\n\n<script>\n// ══════════════════════════════════════════════════════════\n//  STATE\n// ══════════════════════════════════════════════════════════\nlet industries = {};\nlet curStep    = 0;\nlet selInd     = null;\nlet results    = [];\nlet selResult  = null;\nlet qualities  = [];\nlet selQual    = null;  // {height, label}\nlet detectJob  = null;\n\n// ══════════════════════════════════════════════════════════\n//  INIT\n// ══════════════════════════════════════════════════════════\nasync function init() {\n  const r = await fetch("/api/industries");\n  industries = await r.json();\n  buildIndGrid();\n  buildIndSelect();\n  loadLinks();\n}\n\nfunction buildIndGrid() {\n  const g = document.getElementById("indGrid");\n  g.innerHTML = "";\n  for (const [k, v] of Object.entries(industries)) {\n    const d = document.createElement("div");\n    d.className = "ind-card";\n    d.dataset.key = k;\n    d.innerHTML = `<div class="ic">${v.icon}</div>\n                   <div class="nm">${v.name.toUpperCase()}</div>\n                   <div class="lg">${v.lang}</div>`;\n    d.onclick = () => {\n      document.querySelectorAll(".ind-card").forEach(c => c.classList.remove("sel"));\n      d.classList.add("sel");\n      selInd = k;\n    };\n    g.appendChild(d);\n  }\n}\n\nfunction buildIndSelect() {\n  const s = document.getElementById("newLinkInd");\n  for (const [k, v] of Object.entries(industries)) {\n    const o = document.createElement("option");\n    o.value = k; o.textContent = `${v.name}`;\n    s.appendChild(o);\n  }\n}\n\n// ══════════════════════════════════════════════════════════\n//  STEPS\n// ══════════════════════════════════════════════════════════\nfunction goStep(n) {\n  document.querySelectorAll(".section").forEach((s,i) => {\n    s.classList.toggle("active", i === n);\n  });\n  document.querySelectorAll(".step").forEach((s,i) => {\n    s.classList.remove("active","done");\n    if (i < n)  s.classList.add("done");\n    if (i === n) s.classList.add("active");\n  });\n  curStep = n;\n}\n\n// ══════════════════════════════════════════════════════════\n//  DETECT\n// ══════════════════════════════════════════════════════════\nconst SCRIPT_RANGES = {\n  "3": [[0x0C00,0x0C7F]], "4": [[0x0B80,0x0BFF]],\n  "6": [[0x0D00,0x0D7F]], "7": [[0x0C80,0x0CFF]],\n  "8": [[0x0A00,0x0A7F]], "5": [[0x0600,0x06FF]],\n  "2": [[0x0900,0x097F]],\n};\nconst KW_MAP = [\n  ["1",  ["hollywood","marvel","disney","warner","netflix original"]],\n  ["2",  ["bollywood","salman","shahrukh","hrithik","akshay","hindi movie"]],\n  ["3",  ["tollywood","telugu","prabhas","allu arjun","mahesh babu"]],\n  ["4",  ["kollywood","tamil","vijay","ajith","dhanush","rajinikanth"]],\n  ["5",  ["lollywood","pakistani","urdu film"]],\n  ["6",  ["mollywood","malayalam","mohanlal","mammootty"]],\n  ["7",  ["sandalwood","kannada","yash","kgf"]],\n  ["8",  ["pollywood","punjabi movie","diljit"]],\n  ["13", ["bhojpuri","bhojiwood","pawan singh"]],\n];\n\nfunction detectIndustry(text) {\n  if (!text || text.length < 2) return null;\n  for (const [key, ranges] of Object.entries(SCRIPT_RANGES)) {\n    for (const c of text) {\n      const cp = c.codePointAt(0);\n      if (ranges.some(([lo,hi]) => cp >= lo && cp <= hi)) return key;\n    }\n  }\n  const tl = text.toLowerCase();\n  for (const [key, words] of KW_MAP) {\n    if (words.some(w => tl.includes(w))) return key;\n  }\n  return "1";\n}\n\nfunction onMovieType() {\n  clearTimeout(detectJob);\n  detectJob = setTimeout(() => {\n    const text = document.getElementById("movieInput").value.trim();\n    const key  = detectIndustry(text);\n    const box  = document.getElementById("detectBox");\n    if (!text || !key) { box.style.display = "none"; return; }\n    const ind  = industries[key];\n    if (!ind)  { box.style.display = "none"; return; }\n    const conf = [...text].some(c => c.codePointAt(0) > 127) ? 95 : (text.length > 5 ? 80 : 55);\n    document.getElementById("detIcon").textContent = ind.icon;\n    document.getElementById("detName").textContent = ind.name.toUpperCase();\n    document.getElementById("detLang").textContent = ind.lang;\n    document.getElementById("confBar").style.width  = conf + "%";\n    box.style.display = "flex";\n    selInd = key;\n    // highlight card\n    document.querySelectorAll(".ind-card").forEach(c => {\n      c.classList.toggle("sel", c.dataset.key === key);\n    });\n  }, 300);\n}\n\n// ══════════════════════════════════════════════════════════\n//  SEARCH\n// ══════════════════════════════════════════════════════════\nasync function scanGo() {\n  const movie = document.getElementById("movieInput").value.trim();\n  if (!movie) { toast("Movie name daalo!"); return; }\n  if (!selInd) selInd = "1";\n  goStep(2);\n  document.getElementById("resultsHdr").textContent = `// SEARCHING: ${movie.toUpperCase()}...`;\n  document.getElementById("resultsList").innerHTML = `<div class="spinner"><span class="spin">⟳</span> Searching...</div>`;\n  document.getElementById("selectBtn").disabled = true;\n  selResult = null;\n\n  try {\n    const r = await fetch(`/api/search?q=${encodeURIComponent(movie)}&ind=${selInd}`);\n    const d = await r.json();\n    if (d.error) throw new Error(d.error);\n    results = d.results || [];\n    renderResults(results, d.count);\n  } catch(e) {\n    document.getElementById("resultsList").innerHTML = `<div class="spinner">❌ Error: ${e.message}</div>`;\n  }\n}\n\nfunction industrySelected() {\n  if (!selInd) { toast("Industry chuniye!"); return; }\n  scanGo();\n}\n\nfunction renderResults(results, count) {\n  const hdr = document.getElementById("resultsHdr");\n  hdr.textContent = `// ${count} RESULTS FOUND`;\n  const list = document.getElementById("resultsList");\n  if (!results.length) {\n    list.innerHTML = `<div class="spinner">No results found.</div>`;\n    return;\n  }\n  list.innerHTML = "";\n  results.forEach((r, i) => {\n    const card = document.createElement("div");\n    card.className = "result-card";\n    card.innerHTML = `\n      <div class="result-thumb" id="thumb${i}">🎬</div>\n      <div class="result-info">\n        <div class="result-num">${String(i+1).padStart(2,"0")}.</div>\n        <div class="result-title">${escHtml(r.title)}</div>\n        <div class="result-meta">⏱ ${r.duration} &nbsp; ${escHtml(r.channel||"")} &nbsp; ${r.views||""}</div>\n      </div>`;\n    card.onclick = () => {\n      document.querySelectorAll(".result-card").forEach(c => c.classList.remove("sel"));\n      card.classList.add("sel");\n      selResult = r;\n      document.getElementById("selectBtn").disabled = false;\n    };\n    card.ondblclick = () => { card.click(); selectResult(); };\n    list.appendChild(card);\n\n    // lazy load thumb\n    if (r.thumb) {\n      const img = new Image();\n      img.onload = () => {\n        const td = document.getElementById(`thumb${i}`);\n        if (td) { td.innerHTML = ""; td.appendChild(img); }\n      };\n      img.src = r.thumb;\n    }\n  });\n}\n\n// ══════════════════════════════════════════════════════════\n//  QUALITY\n// ══════════════════════════════════════════════════════════\nasync function selectResult() {\n  if (!selResult) { toast("Pehle result select karo!"); return; }\n  goStep(3);\n  document.getElementById("qualHdr").textContent = "// FETCHING QUALITIES...";\n  document.getElementById("qualList").innerHTML = `<div class="spinner"><span class="spin">⟳</span> Loading...</div>`;\n\n  try {\n    const r = await fetch(`/api/qualities?url=${encodeURIComponent(selResult.url)}`);\n    const d = await r.json();\n    if (d.error) throw new Error(d.error);\n    qualities = d.qualities || [];\n    renderQualities(d.title, qualities);\n  } catch(e) {\n    document.getElementById("qualList").innerHTML = `<div class="spinner">❌ ${e.message}</div>`;\n  }\n}\n\nfunction renderQualities(title, ql) {\n  document.getElementById("qualHdr").textContent = `// ${title.substring(0,50)}`;\n  const list = document.getElementById("qualList");\n  list.innerHTML = "";\n  selQual = {height: 0, label: "AUTO BEST"};\n\n  // AUTO BEST option\n  const auto = document.createElement("div");\n  auto.className = "qual-item sel";\n  auto.innerHTML = `<input type="radio" name="qual" value="0" checked>\n                    <span class="qual-label">🏆 AUTO BEST (max 1080p)</span>`;\n  auto.onclick = () => {\n    document.querySelectorAll(".qual-item").forEach(q=>q.classList.remove("sel"));\n    auto.classList.add("sel");\n    selQual = {height: 0, label: "AUTO BEST"};\n  };\n  list.appendChild(auto);\n\n  ql.forEach((q, i) => {\n    const tag = q.height >= 1080 ? "FULL HD" : q.height >= 720 ? "HD" : q.height < 480 ? "SD" : "";\n    const item = document.createElement("div");\n    item.className = "qual-item";\n    item.innerHTML = `<input type="radio" name="qual" value="${i+1}">\n                      <span class="qual-label">${q.label}</span>\n                      ${tag ? `<span class="qual-tag">← ${tag}</span>` : ""}`;\n    item.onclick = () => {\n      document.querySelectorAll(".qual-item").forEach(x=>x.classList.remove("sel"));\n      item.classList.add("sel");\n      selQual = {height: q.height, label: q.label};\n    };\n    list.appendChild(item);\n  });\n}\n\n// ══════════════════════════════════════════════════════════\n//  DOWNLOAD\n// ══════════════════════════════════════════════════════════\nasync function confirmQuality() {\n  if (!selResult) { toast("Koi video select nahi!"); return; }\n  goStep(4);\n  document.getElementById("dlTitle").textContent = selResult.title;\n  document.getElementById("dlPct").textContent   = "0%";\n  document.getElementById("dlBar").style.width   = "0";\n  document.getElementById("dlState").textContent = "STARTING";\n  document.getElementById("dlActionArea").innerHTML = "";\n\n  try {\n    const r = await fetch("/api/download/start", {\n      method: "POST",\n      headers: {"Content-Type":"application/json"},\n      body: JSON.stringify({\n        url:    selResult.url,\n        height: selQual ? selQual.height : 0,\n        title:  selResult.title,\n      })\n    });\n    const d = await r.json();\n    if (d.error) throw new Error(d.error);\n    listenProgress(d.job_id);\n  } catch(e) {\n    document.getElementById("dlState").textContent = "ERROR: " + e.message;\n  }\n}\n\nfunction listenProgress(jobId) {\n  const es = new EventSource(`/api/download/progress/${jobId}`);\n  es.onmessage = (e) => {\n    const d = JSON.parse(e.data);\n    document.getElementById("dlPct").textContent   = d.pct + "%";\n    document.getElementById("dlBar").style.width   = d.pct + "%";\n    document.getElementById("dlSpeed").textContent = d.speed || "—";\n    document.getElementById("dlEta").textContent   = d.eta   || "—";\n    document.getElementById("dlSize").textContent  = d.size  || "—";\n    document.getElementById("dlState").textContent = (d.state||"").toUpperCase();\n\n    if (d.state === "done") {\n      es.close();\n      document.getElementById("dlPct").textContent = "100%";\n      document.getElementById("dlBar").style.width = "100%";\n      document.getElementById("dlActionArea").innerHTML =\n        `<a href="/api/download/file/${jobId}" class="btn" download>\n           ⬇️ DOWNLOAD FILE\n         </a>`;\n      toast("Download complete!");\n    }\n    if (d.state === "error") {\n      es.close();\n      document.getElementById("dlActionArea").innerHTML =\n        `<div style="color:var(--neon2);font-size:12px;padding:10px">❌ ${d.error||"Unknown error"}</div>`;\n    }\n  };\n}\n\n// ══════════════════════════════════════════════════════════\n//  CUSTOM LINKS\n// ══════════════════════════════════════════════════════════\nasync function loadLinks() {\n  const r = await fetch("/api/links");\n  const links = await r.json();\n  const list = document.getElementById("linksList");\n  if (!links.length) {\n    list.innerHTML = `<div style="font-size:10px;color:var(--dim)">No custom links yet.</div>`;\n    return;\n  }\n  list.innerHTML = "";\n  links.forEach((lnk, i) => {\n    const d = document.createElement("div");\n    d.className = "link-item";\n    d.innerHTML = `<div>\n        <div class="link-name">🔗 ${escHtml(lnk.name)}</div>\n        <div class="link-ind">[${lnk.industry === "all" ? "All" : (industries[lnk.industry]?.name || lnk.industry)}]</div>\n      </div>\n      <button class="del-btn" onclick="deleteLink(${i})">✕</button>`;\n    list.appendChild(d);\n  });\n}\n\nasync function addLink() {\n  const url = document.getElementById("newLinkUrl").value.trim();\n  const ind = document.getElementById("newLinkInd").value;\n  if (!url) { toast("URL daalo!"); return; }\n  const r = await fetch("/api/links", {\n    method:"POST",\n    headers:{"Content-Type":"application/json"},\n    body: JSON.stringify({url, industry: ind})\n  });\n  const d = await r.json();\n  if (d.ok) {\n    document.getElementById("newLinkUrl").value = "";\n    toast(`Added: ${d.name}`);\n    loadLinks();\n  } else {\n    toast("Error: " + d.error);\n  }\n}\n\nasync function deleteLink(idx) {\n  await fetch(`/api/links/${idx}`, {method:"DELETE"});\n  loadLinks();\n}\n\n// ══════════════════════════════════════════════════════════\n//  UTILS\n// ══════════════════════════════════════════════════════════\nfunction resetAll() {\n  selInd=null; selResult=null; selQual=null; results=[]; qualities=[];\n  document.getElementById("movieInput").value = "";\n  document.getElementById("detectBox").style.display = "none";\n  document.querySelectorAll(".ind-card").forEach(c=>c.classList.remove("sel"));\n  goStep(0);\n}\n\nfunction escHtml(s) {\n  return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");\n}\n\nlet toastTimer;\nfunction toast(msg) {\n  const t = document.getElementById("toast");\n  t.textContent = msg;\n  t.classList.add("show");\n  clearTimeout(toastTimer);\n  toastTimer = setTimeout(() => t.classList.remove("show"), 2500);\n}\n\ninit();\n</script>\n</body>\n</html>\n'

def start_web_server(port=5000):
    try: import flask
    except ImportError:
        print("Installing flask...")
        subprocess.check_call([sys.executable,"-m","pip","install","flask","-q"])
        import flask

    from flask import Flask, request, jsonify, Response, stream_with_context
    import tempfile, time as _time, json as _json

    web_app = Flask(__name__)

    @web_app.route("/")
    def _index():
        return HTML_PAGE, 200, {"Content-Type":"text/html; charset=utf-8"}

    @web_app.route("/api/industries")
    def _api_industries():
        return jsonify(INDUSTRIES)

    @web_app.route("/api/search")
    def _api_search():
        movie   = request.args.get("q","").strip()
        ind_key = request.args.get("ind","1")
        if not movie: return jsonify({"error":"query required"}), 400
        try:
            ind     = INDUSTRIES.get(ind_key, INDUSTRIES["1"])
            keyword = ind["keyword"]
            custom  = [l for l in CUSTOM_LINKS if l.get("industry","all") in ("all",ind_key)]
            all_res, seen = [], set()
            from concurrent.futures import ThreadPoolExecutor, as_completed
            tasks = [("c",l) for l in custom] + [("y",None)]
            def _run(task):
                k,lnk = task
                try:
                    if k=="c":
                        dom = url_to_domain(normalize_url(lnk.get("url_template","")))
                        return yt_search(f"{movie} {keyword} site:{dom}")
                    return yt_search(f"{movie} {keyword}")
                except: return []
            with ThreadPoolExecutor(max_workers=max(len(tasks),1)) as ex:
                for f in as_completed([ex.submit(_run,t) for t in tasks]):
                    for r in f.result():
                        if r["url"] not in seen:
                            seen.add(r["url"]); all_res.append(r)
            return jsonify({"results":all_res,"count":len(all_res)})
        except Exception as e:
            return jsonify({"error":str(e)}), 500

    @web_app.route("/api/qualities")
    def _api_qualities():
        url = request.args.get("url","")
        if not url: return jsonify({"error":"url required"}), 400
        try:
            ql,title = get_qualities(url)
            return jsonify({"qualities":ql,"title":title})
        except Exception as e:
            return jsonify({"error":str(e)}), 500

    _dl_jobs = {}

    @web_app.route("/api/download/start", methods=["POST"])
    def _api_dl_start():
        data   = request.json or {}
        url    = data.get("url","")
        height = data.get("height",0)
        if not url: return jsonify({"error":"url required"}), 400
        fmt = (f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
               if height else
               f"bestvideo[height<={MAX_QUALITY_HEIGHT}]+bestaudio/best[height<={MAX_QUALITY_HEIGHT}]")
        jid = f"job_{int(_time.time()*1000)}"
        st  = {"pct":0,"speed":"","eta":"","size":"","state":"starting","file":""}
        _dl_jobs[jid] = st
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp,"%(title)s.%(ext)s")
        def hook(d):
            if d["status"]=="downloading":
                total=d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done=d.get("downloaded_bytes",0); spd=d.get("speed") or 0; eta=d.get("eta") or 0
                if total:
                    st["pct"]=round(done/total*100,1)
                    st["speed"]=f"{spd/1_048_576:.1f} MB/s"
                    st["size"]=f"{done/1_048_576:.1f}/{total/1_048_576:.1f} MB"
                    mm,ss=divmod(int(eta),60); st["eta"]=f"{mm}:{ss:02d}"
                st["state"]="downloading"
            elif d["status"]=="finished":
                st["state"]="merging"; st["pct"]=99
        def run():
            try:
                with yt_dlp.YoutubeDL({"format":fmt,"outtmpl":out,"merge_output_format":"mp4",
                                        "progress_hooks":[hook],"quiet":True,"no_warnings":True}) as ydl:
                    ydl.download([url])
                for fn in os.listdir(tmp):
                    st["file"]=os.path.join(tmp,fn); break
                st["state"]="done"; st["pct"]=100
            except Exception as ex:
                st["state"]="error"; st["error"]=str(ex)
        threading.Thread(target=run,daemon=True).start()
        return jsonify({"job_id":jid})

    @web_app.route("/api/download/progress/<jid>")
    def _api_dl_progress(jid):
        def gen():
            while True:
                st = _dl_jobs.get(jid)
                if not st:
                    yield f"data: {_json.dumps({'state':'not_found'})}\n\n"; break
                yield f"data: {_json.dumps(st)}\n\n"
                if st["state"] in ("done","error"): break
                _time.sleep(0.8)
        return Response(stream_with_context(gen()), mimetype="text/event-stream",
                        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

    @web_app.route("/api/download/file/<jid>")
    def _api_dl_file(jid):
        from flask import send_file
        st = _dl_jobs.get(jid)
        if not st or not st.get("file"):
            return jsonify({"error":"file not ready"}), 404
        return send_file(st["file"], as_attachment=True)

    @web_app.route("/api/links", methods=["GET"])
    def _api_links_get():
        return jsonify(CUSTOM_LINKS)

    @web_app.route("/api/links", methods=["POST"])
    def _api_links_add():
        data = request.json or {}
        url  = normalize_url(data.get("url","").strip())
        ind  = data.get("industry","all")
        if not url: return jsonify({"error":"url required"}), 400
        name = url_to_domain(url)
        CUSTOM_LINKS.append({"name":name,"url_template":url,"type":"yt_search","industry":ind})
        save_custom_links(CUSTOM_LINKS)
        return jsonify({"ok":True,"name":name})

    @web_app.route("/api/links/<int:idx>", methods=["DELETE"])
    def _api_links_del(idx):
        if 0 <= idx < len(CUSTOM_LINKS):
            CUSTOM_LINKS.pop(idx)
            save_custom_links(CUSTOM_LINKS)
            return jsonify({"ok":True})
        return jsonify({"error":"not found"}), 404

    print(f"\n{'='*52}")
    print(f"  CINEFLUX WEB SERVER STARTED")
    print(f"  Browser mein kholo: http://localhost:{port}")
    print(f"  Mobile (same WiFi): http://<your-ip>:{port}")
    print(f"{'='*52}\n")
    web_app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GUNICORN ENTRY POINT — Render pe ye use hoga
# ══════════════════════════════════════════════════════════════════════════════
def create_app():
    """Gunicorn ke liye Flask app return karo."""
    try: import flask
    except ImportError:
        subprocess.check_call([sys.executable,"-m","pip","install","flask","-q"])
        import flask
    from flask import Flask, request, jsonify, Response, stream_with_context
    import tempfile, time as _time, json as _json

    web_app = Flask(__name__)

    @web_app.route("/")
    def _index():
        return HTML_PAGE, 200, {"Content-Type":"text/html; charset=utf-8"}

    @web_app.route("/api/industries")
    def _api_industries():
        return jsonify(INDUSTRIES)

    @web_app.route("/api/search")
    def _api_search():
        movie   = request.args.get("q","").strip()
        ind_key = request.args.get("ind","1")
        if not movie: return jsonify({"error":"query required"}), 400
        try:
            ind     = INDUSTRIES.get(ind_key, INDUSTRIES["1"])
            keyword = ind["keyword"]
            custom  = [l for l in CUSTOM_LINKS if l.get("industry","all") in ("all",ind_key)]
            all_res, seen = [], set()
            from concurrent.futures import ThreadPoolExecutor, as_completed
            tasks = [("c",l) for l in custom] + [("y",None)]
            def _run(task):
                k,lnk = task
                try:
                    if k=="c":
                        dom = url_to_domain(normalize_url(lnk.get("url_template","")))
                        return yt_search(f"{movie} {keyword} site:{dom}")
                    return yt_search(f"{movie} {keyword}")
                except: return []
            with ThreadPoolExecutor(max_workers=max(len(tasks),1)) as ex:
                for f in as_completed([ex.submit(_run,t) for t in tasks]):
                    for r in f.result():
                        if r["url"] not in seen:
                            seen.add(r["url"]); all_res.append(r)
            return jsonify({"results":all_res,"count":len(all_res)})
        except Exception as e:
            return jsonify({"error":str(e)}), 500

    @web_app.route("/api/qualities")
    def _api_qualities():
        url = request.args.get("url","")
        if not url: return jsonify({"error":"url required"}), 400
        try:
            ql,title = get_qualities(url)
            return jsonify({"qualities":ql,"title":title})
        except Exception as e:
            return jsonify({"error":str(e)}), 500

    _dl_jobs = {}

    @web_app.route("/api/download/start", methods=["POST"])
    def _api_dl_start2():
        data   = request.json or {}
        url    = data.get("url","")
        height = data.get("height",0)
        if not url: return jsonify({"error":"url required"}), 400
        fmt = (f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
               if height else
               f"bestvideo[height<={MAX_QUALITY_HEIGHT}]+bestaudio/best[height<={MAX_QUALITY_HEIGHT}]")
        jid = f"job_{int(_time.time()*1000)}"
        st  = {"pct":0,"speed":"","eta":"","size":"","state":"starting","file":""}
        _dl_jobs[jid] = st
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp,"%(title)s.%(ext)s")
        def hook(d):
            if d["status"]=="downloading":
                total=d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done=d.get("downloaded_bytes",0); spd=d.get("speed") or 0; eta=d.get("eta") or 0
                if total:
                    st["pct"]=round(done/total*100,1)
                    st["speed"]=f"{spd/1_048_576:.1f} MB/s"
                    st["size"]=f"{done/1_048_576:.1f}/{total/1_048_576:.1f} MB"
                    mm,ss=divmod(int(eta),60); st["eta"]=f"{mm}:{ss:02d}"
                st["state"]="downloading"
            elif d["status"]=="finished":
                st["state"]="merging"; st["pct"]=99
        def run():
            try:
                with yt_dlp.YoutubeDL({"format":fmt,"outtmpl":out,"merge_output_format":"mp4",
                                        "progress_hooks":[hook],"quiet":True,"no_warnings":True}) as ydl:
                    ydl.download([url])
                for fn in os.listdir(tmp):
                    st["file"]=os.path.join(tmp,fn); break
                st["state"]="done"; st["pct"]=100
            except Exception as ex:
                st["state"]="error"; st["error"]=str(ex)
        threading.Thread(target=run,daemon=True).start()
        return jsonify({"job_id":jid})

    @web_app.route("/api/download/progress/<jid>")
    def _api_dl_progress2(jid):
        def gen():
            while True:
                st = _dl_jobs.get(jid)
                if not st:
                    yield f"data: {_json.dumps({'state':'not_found'})}\n\n"; break
                yield f"data: {_json.dumps(st)}\n\n"
                if st["state"] in ("done","error"): break
                _time.sleep(0.8)
        return Response(stream_with_context(gen()), mimetype="text/event-stream",
                        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

    @web_app.route("/api/download/file/<jid>")
    def _api_dl_file2(jid):
        from flask import send_file
        st = _dl_jobs.get(jid)
        if not st or not st.get("file"):
            return jsonify({"error":"file not ready"}), 404
        return send_file(st["file"], as_attachment=True)

    @web_app.route("/api/links", methods=["GET"])
    def _api_links_get2():
        return jsonify(CUSTOM_LINKS)

    @web_app.route("/api/links", methods=["POST"])
    def _api_links_add2():
        data = request.json or {}
        url  = normalize_url(data.get("url","").strip())
        ind  = data.get("industry","all")
        if not url: return jsonify({"error":"url required"}), 400
        name = url_to_domain(url)
        CUSTOM_LINKS.append({"name":name,"url_template":url,"type":"yt_search","industry":ind})
        save_custom_links(CUSTOM_LINKS)
        return jsonify({"ok":True,"name":name})

    @web_app.route("/api/links/<int:idx>", methods=["DELETE"])
    def _api_links_del2(idx):
        if 0 <= idx < len(CUSTOM_LINKS):
            CUSTOM_LINKS.pop(idx)
            save_custom_links(CUSTOM_LINKS)
            return jsonify({"ok":True})
        return jsonify({"error":"not found"}), 404

    return web_app

# Gunicorn direct access
application = create_app()

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if "--web" in sys.argv:
        port = 5000
        for arg in sys.argv[1:]:
            if arg.isdigit(): port = int(arg)
        start_web_server(port)
    else:
        root = tk.Tk()
        CineFluxApp(root)
        root.mainloop()