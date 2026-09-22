# -*- coding: utf-8 -*-
"""
PKA GUIDE Overlay: passa o mouse (ou aperta a tecla) em um item do jogo e o painel mostra para que ele serve.
- Lê o tooltip por captura de TELA (pixel) + OCR. Não lê memória nem toca no processo do jogo.
- Painel arredondado, arrastável, fechado por padrão; abre quando reconhece um item.
- Modos: automático, tecla de atalho ou ambos (⚙ Configurações).
- Item fora da base abre como "NÃO CADASTRADO" com botão para cadastrar.
"""
import json, os, re, sys, threading, time, queue, difflib, unicodedata, subprocess, tempfile, traceback, webbrowser
import tkinter as tk
import numpy as np
import mss
from PIL import Image, ImageDraw, ImageTk
from pynput import mouse, keyboard
import ui_kit as ui

APP_NAME = 'PKA GUIDE'
VERSION = '2.5.0'
SITE = 'https://pkaguide.vercel.app'
DB_URL = SITE + '/overlay/items_db.json'
VERSION_URL = SITE + '/overlay/version.json'
TASKS_URL = SITE + '/overlay/tasks_db.json'
HUB_URL = SITE + '/overlay/hub_db.json'
VIDEOS_URL = SITE + '/overlay/videos_db.json'

if os.name == 'nt':  # sem isso, em telas com escala != 100% a área capturada sai deslocada
    try:
        import ctypes
        try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

FROZEN = getattr(sys, 'frozen', False)
BUNDLE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
EXE = sys.executable if FROZEN else None
INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
DATA_DIR = INSTALL_DIR if FROZEN else os.path.dirname(os.path.abspath(__file__))
os.makedirs(DATA_DIR, exist_ok=True)
CATALOG_DIR = os.path.join(DATA_DIR, 'catalog'); os.makedirs(CATALOG_DIR, exist_ok=True)
CATALOG_FILE = os.path.join(CATALOG_DIR, 'catalog.json')
CUSTOM_FILE = os.path.join(DATA_DIR, 'custom_items.json')
UNKNOWN_FILE = os.path.join(DATA_DIR, 'nao_reconhecidos.json')
LOG_FILE = os.path.join(DATA_DIR, 'overlay.log')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_db.json')

def log(*a):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')
    except Exception: pass

def jload(path, default):
    try: return json.load(open(path, encoding='utf-8'))
    except Exception: return default

catalog = jload(CATALOG_FILE, {})
custom = jload(CUSTOM_FILE, {})
unknown = jload(UNKNOWN_FILE, {})
DEFAULTS = {'mode': 'auto', 'hotkey': 'f4', 'show_s': 8, 'alpha': 97}   # alpha em % (30 a 100)
cfg = dict(DEFAULTS, **jload(CONFIG_FILE, {}))

def save_cfg():
    try: json.dump(cfg, open(CONFIG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    except Exception as e: log('save_cfg', e)

REGION = (-360, -170, 380, 170)
TRIES = (0.25, 0.55, 1.0, 1.6)  # tenta cedo e repete; o tooltip do jogo demora a aparecer
POLL = 0.12                     # intervalo entre olhadas na tela
ICON = 34

# ---------------- identidade visual ----------------
MAGIC = '#181819'            # vira transparente na janela (quase igual ao fundo, sem halo colorido)
BG, BG2, BG3 = '#18181b', '#232327', '#33333a'
TXT, MUTED, MUTED2, LINE = '#fafafa', '#a1a1aa', '#71717a', '#3f3f46'
ORANGE, YELLOW, SKY, INDIGO, GREEN, RED = '#f97316', '#eab308', '#0ea5e9', '#4f46e5', '#22c55e', '#ef4444'
FONT = 'Segoe UI'
RADIUS, PAD, CARD_W = 16, 10, 372

CATS = {
    'talento': (GREEN, 'sparkle', 'USAR · VENDER PARA PLAYER', 'Usado em PokeTalent'),
    'boost':   (YELLOW, 'flame', 'BOOST', 'Item de boost'),
    'material':(SKY, 'gem', 'MATERIAL', 'Stone / fragmento de boost'),
    'npc':     ('#8b8b94', 'coin', 'SÓ NPC', 'Sem uso conhecido: vender para NPC'),
    'desconhecido': ('#8b8b94', 'search', 'SEM REGISTRO', 'Não está na base do site'),
}
CAT_OPTS = [('talento', 'Usar / vender para player', GREEN), ('boost', 'Boost', YELLOW),
            ('material', 'Material (stone/fragmento)', SKY), ('npc', 'Só vender para NPC', '#8b8b94')]

# ---------------- base de itens ----------------
def load_db():
    for p in (os.path.join(DATA_DIR, 'items_db.json'), os.path.join(BUNDLE, 'items_db.json')):
        if os.path.exists(p):
            d = jload(p, None)
            if d: return d
    return {}

def merge_custom():
    for k, v in custom.items():
        if v.get('alias') and v['alias'] in DB:
            d = dict(DB[v['alias']]); d['name'] = k; d['alias_de'] = v['alias']; DB[k] = d
        else:
            DB[k] = {'name': k, 'cat': v.get('cat', 'npc'), 'talents': [], 'boost': [], 'drops': [],
                     'stone': [], 'fragment': [], 'nota': v.get('note', ''), 'custom': True}

DB = load_db(); merge_custom(); NAMES = list(DB.keys())

def refresh_db():
    global DB, NAMES
    try:
        import requests
        d = requests.get(DB_URL, timeout=8).json()
        if isinstance(d, dict) and len(d) > 100:
            json.dump(d, open(os.path.join(DATA_DIR, 'items_db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            DB = d; merge_custom(); NAMES = list(DB.keys())
            return f'{len(DB)} itens'
    except Exception as e:
        log('refresh_db', e); return f'{len(DB)} itens (offline)'
    return f'{len(DB)} itens'

TASKS = jload(TASKS_FILE, None) or jload(os.path.join(BUNDLE, 'tasks_db.json'), {'tasks': []})

def refresh_tasks():
    global TASKS
    try:
        import requests
        d = requests.get(TASKS_URL, timeout=10).json()
        if isinstance(d, dict) and d.get('tasks'):
            json.dump(d, open(TASKS_FILE, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            TASKS = d
    except Exception as e: log('refresh_tasks', e)

def _local_or_bundle(name, default):
    return jload(os.path.join(DATA_DIR, name), None) or jload(os.path.join(BUNDLE, name), default)

HUB = _local_or_bundle('hub_db.json', {})
VIDEOS = _local_or_bundle('videos_db.json', [])

def refresh_hub():
    global HUB, VIDEOS
    try:
        import requests
        for url, name in ((HUB_URL, 'hub_db.json'), (VIDEOS_URL, 'videos_db.json')):
            d = requests.get(url, timeout=30).json()
            if d:
                json.dump(d, open(os.path.join(DATA_DIR, name), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
                if name == 'hub_db.json': HUB = d
                else: VIDEOS = d
    except Exception as e: log('refresh_hub', e)

def search_tasks(q, limit=8):
    s = norm(q)
    if len(s) < 2: return []
    exact, partial = [], []
    for t in TASKS.get('tasks', []):
        alvos = [norm(o.get('target', '')) for o in t.get('objectives', [])]
        if s in alvos: exact.append(t)
        elif any(s in a for a in alvos) or s in norm(t.get('npc', ''))              or any(s in norm(r.get('label', '')) for r in t.get('rewards', [])):
            partial.append(t)
    return (exact + partial)[:limit]

def check_update():
    try:
        import requests
        v = requests.get(VERSION_URL, timeout=8).json()
        if tuple(map(int, v['version'].split('.'))) > tuple(map(int, VERSION.split('.'))):
            return v['version'], v['url']
    except Exception as e: log('check_update', e)
    return None, None

def apply_update(url):
    """baixa o instalador novo e roda em modo silencioso (ele troca a pasta do app e reabre)"""
    import requests
    setup = os.path.join(tempfile.gettempdir(), 'PKA_GUIDE_Setup.exe')
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(setup, 'wb') as f:
            for chunk in r.iter_content(1 << 16): f.write(chunk)
    subprocess.Popen([setup, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], creationflags=0x00000008)
    os._exit(0)

# ---------------- texto ----------------
IGNORE = ('price', 'segure', 'shift', 'coleta', 'depot', 'stash', 'trainer', 'ultra bag', 'great bag', 'pokemon', 'loot')

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r"[^a-z0-9' ]+", ' ', s).strip()

def clean_line(text):
    t = norm(text)
    t = re.sub(r'^\s*(x\s*)?\d+[\.,]?\d*\s*[kx]?\s+', '', t)
    t = re.sub(r'\s+x?\d+\s*$', '', t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    if len(t) < 4 or len(t) > 44: return ''
    if any(t.startswith(w) for w in IGNORE): return ''
    if not re.search(r'[a-z]{3}', t): return ''
    return t

def singulars(c):
    out = [c]
    if c.endswith('ies'): out.append(c[:-3] + 'y')
    if c.endswith('es') and not c.endswith('ss'): out.append(c[:-2])
    if c.endswith('s') and not c.endswith('ss'): out.append(c[:-1])
    return out

def looks_like_item(raw):
    """nome de item no jogo vem em Maiúsculas Iniciais e com 2+ palavras ('16 Wigglytuff Ears')"""
    s = re.sub(r'^\s*[x]?\d[\d.,k]*\s*[x]?\s*', '', raw.strip())
    s = s.strip(' .:-')
    words = [w for w in re.split(r'\s+', s) if w]
    if len(words) < 2 or len(words) > 6: return False
    small = {'of', 'the', 'de', 'do', 'da'}
    caps = [w for w in words if w[:1].isupper() or w.lower() in small]
    return len(caps) == len(words) and any(len(w) > 2 for w in words)

def match_name(text):
    t = clean_line(text)
    if not t: return None, 0, ''
    groups = [singulars(t)] + [singulars(t.rsplit(' ', i)[0]) for i in range(1, min(3, t.count(' ') + 1))]
    for g in groups:
        for c in g:
            if c in DB: return c, 1.0, t
    for g in groups:
        for c in g:
            m = difflib.get_close_matches(c, NAMES, n=1, cutoff=0.8)
            if m: return m[0], difflib.SequenceMatcher(None, c, m[0]).ratio(), t
    return None, 0, (singulars(t)[-1] if looks_like_item(text) else '')

# ---------------- teclas ----------------
MOD_NAMES = {'ctrl': ('ctrl', 'ctrl_l', 'ctrl_r'), 'alt': ('alt', 'alt_l', 'alt_r', 'alt_gr'), 'shift': ('shift', 'shift_l', 'shift_r')}

def base_key(key):
    try:
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else f'vk{key.vk}'
        n = str(key).replace('Key.', '')
        for m, alts in MOD_NAMES.items():
            if n in alts: return m
        return n
    except Exception: return ''

def combo_str(key, held):
    b = base_key(key)
    if not b or b in ('ctrl', 'alt', 'shift'): return ''
    return '+'.join([m for m in ('ctrl', 'alt', 'shift') if m in held] + [b])

def pretty_key(s):
    return ' + '.join(w.upper() for w in s.split('+')) if s else '—'

# ---------------- OCR ----------------
_ocr = None
def get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr

_sct = threading.local()
def grab(x, y):
    """captura a área ao redor do cursor + o ícone sob o cursor (rápido, sem OCR)"""
    if not hasattr(_sct, 'm'): _sct.m = mss.MSS()
    mon = _sct.m.monitors[0]
    box = {'left': max(mon['left'], x + REGION[0]), 'top': max(mon['top'], y + REGION[1]),
           'width': REGION[2] - REGION[0], 'height': REGION[3] - REGION[1]}
    g = _sct.m.grab(box)
    img = Image.frombytes('RGB', g.size, g.bgra, 'raw', 'BGRX')
    ish = _sct.m.grab({'left': x - ICON // 2, 'top': y - ICON // 2, 'width': ICON, 'height': ICON})
    icon = Image.frombytes('RGB', ish.size, ish.bgra, 'raw', 'BGRX')
    sig = hash(img.resize((48, 24), Image.BILINEAR).convert('L').tobytes())
    return img, icon, sig

def ocr_lines(img):
    res, _ = get_ocr()(np.array(img), use_cls=False)
    return [r[1] for r in (res or []) if float(r[2]) > 0.5]

def read_tooltip(x, y):
    img, icon, _ = grab(x, y)
    return ocr_lines(img), icon

# ---------------- janela arredondada ----------------
class Round:
    """janela sem borda com cartão arredondado; o conteúdo vai em self.body"""
    def __init__(self, master=None, width=CARD_W, border=LINE, alpha=None):
        if alpha is None: alpha = cfg['alpha'] / 100
        self.win = tk.Toplevel(master) if master else tk.Tk()
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.attributes('-alpha', alpha)
        self.win.configure(bg=MAGIC)
        try: self.win.attributes('-transparentcolor', MAGIC)
        except Exception: pass
        self.canvas = tk.Canvas(self.win, bg=MAGIC, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.bg_photo = None
        self.bg_id = self.canvas.create_image(0, 0, anchor='nw')
        self.body = tk.Frame(self.canvas, bg=BG)
        # espaçador invisível: garante a largura mínima sem travar a altura automática
        self.spacer = tk.Frame(self.body, bg=BG, height=1, width=1); self.spacer.pack(fill='x')
        self.spacer._nodrag = False
        self.canvas.create_window(PAD, PAD, anchor='nw', window=self.body)
        self.border = border
        self.width = width

    def relayout(self, keep_pos=True):
        self.spacer.config(width=max(1, self.width))
        self.body.update_idletasks()
        w = max(self.width, self.body.winfo_reqwidth()) + PAD * 2
        h = self.body.winfo_reqheight() + PAD * 2
        self.bg_photo = ImageTk.PhotoImage(ui.panel(w, h, RADIUS, BG, self.border, 2, MAGIC))
        self.canvas.itemconfig(self.bg_id, image=self.bg_photo)
        self.canvas.config(width=w, height=h)
        if keep_pos: self.win.geometry(f'{w}x{h}+{self.win.winfo_x()}+{self.win.winfo_y()}')
        else: self.win.geometry(f'{w}x{h}')

    def set_border(self, color): self.border = color

    def drag_with(self, *widgets):
        def start(e): self._d = (e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y())
        def move(e): self.win.geometry(f'+{e.x_root - self._d[0]}+{e.y_root - self._d[1]}')
        def bind(w):
            w.bind('<ButtonPress-1>', start, add='+'); w.bind('<B1-Motion>', move, add='+')
            for c in w.winfo_children():
                if getattr(c, '_nodrag', False): continue
                bind(c)
        for w in widgets: bind(w)

TYPE_ALIAS = {'metal': 'steel', 'fly': 'flying', 'aco': 'steel', 'aço': 'steel', 'eletric': 'electric'}
_type_cache = {}

def type_img(name, size=16):
    """ícone do elemento (mesmas artes do site); None se não for um tipo conhecido"""
    k = TYPE_ALIAS.get(norm(name), norm(name))
    key = (k, size)
    if key in _type_cache: return _type_cache[key]
    for base in (DATA_DIR, BUNDLE):
        f = os.path.join(base, 'types', k + '.png')
        if os.path.exists(f):
            try:
                _type_cache[key] = ImageTk.PhotoImage(Image.open(f).convert('RGBA').resize((size, size), Image.LANCZOS))
                return _type_cache[key]
            except Exception as e: log('type_img', e)
    _type_cache[key] = None
    return None

def type_chip(parent, name, bg=BG, size=16, fsize=9, color='#e4e4e7'):
    """ícone + nome do elemento, lado a lado"""
    f = tk.Frame(parent, bg=bg)
    im = type_img(name, size)
    if im:
        l = tk.Label(f, image=im, bg=bg, bd=0); l.image = im; l.pack(side='left', padx=(0, 4))
    tk.Label(f, text=name, font=(FONT, fsize), fg=color, bg=bg).pack(side='left')
    return f

def ico_label(parent, name, size, color, bg=BG):
    img = ImageTk.PhotoImage(ui.icon(name, size, color))
    l = tk.Label(parent, image=img, bg=bg, bd=0); l.image = img
    return l

def item_thumb(img, size=62, radius=12, bg='#0f0f13'):
    card = Image.new('RGBA', (size * 3, size * 3), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, size * 3 - 1, size * 3 - 1], radius=radius * 3, fill=ui._rgb(bg) + (255,))
    card = card.resize((size, size), Image.LANCZOS)
    inner = size - 12
    card.alpha_composite(img.convert('RGBA').resize((inner, inner), Image.NEAREST), (6, 6))
    return card

# ---------------- app ----------------
class App:
    def __init__(self):
        self.enabled = True
        self.pos = (0, 0); self.last_move = time.time()
        self.q = queue.Queue(); self.pending = None; self.modal = None
        self.update_url = None; self.held = set(); self.recording = None
        self.status_text = f'v{VERSION} · carregando…'

        self.w = Round(width=CARD_W)
        self.root = self.w.win
        self.root.title(APP_NAME)
        try: self.root.iconbitmap(os.path.join(BUNDLE, 'logo.ico'))
        except Exception: pass

        b = self.w.body
        head = tk.Frame(b, bg=BG); head.pack(fill='x', padx=4, pady=(2, 0))
        try:
            lg = ImageTk.PhotoImage(Image.open(os.path.join(BUNDLE, 'logo_small.png')).convert('RGBA').resize((30, 30), Image.LANCZOS))
            l = tk.Label(head, image=lg, bg=BG, bd=0); l.image = lg; l.pack(side='left', padx=(2, 8))
        except Exception: pass
        ttl = tk.Frame(head, bg=BG); ttl.pack(side='left')
        tk.Label(ttl, text='PKA ', font=(FONT, 11, 'bold'), fg=TXT, bg=BG).pack(side='left')
        tk.Label(ttl, text='GUIDE', font=(FONT, 11, 'bold'), fg=SKY, bg=BG).pack(side='left')

        self.b_close = tk.Label(head, text='✕', font=(FONT, 11), fg=MUTED2, bg=BG, padx=7, cursor='hand2')
        self.b_close.pack(side='right'); self.b_close._nodrag = True
        self.b_close.bind('<Button-1>', lambda e: self.q.put(('quit', None)))
        self.b_close.bind('<Enter>', lambda e: self.b_close.config(fg=RED))
        self.b_close.bind('<Leave>', lambda e: self.b_close.config(fg=MUTED2))

        self.b_toggle = tk.Label(head, bg=BG, bd=0, cursor='hand2'); self.b_toggle.pack(side='right', padx=6)
        self.b_toggle._nodrag = True
        self.b_toggle.bind('<Button-1>', lambda e: self.toggle())

        self.b_tasks = tk.Label(head, text='Consulta', font=(FONT, 9, 'bold'), fg=MUTED2, bg=BG, padx=5, cursor='hand2')
        self.b_tasks.pack(side='right'); self.b_tasks._nodrag = True
        self.b_tasks.bind('<Button-1>', lambda e: self.open_hub())
        self.b_tasks.bind('<Enter>', lambda e: self.b_tasks.config(fg=TXT))
        self.b_tasks.bind('<Leave>', lambda e: self.b_tasks.config(fg=MUTED2))
        self.b_cfg = tk.Label(head, text='⚙', font=(FONT, 12), fg=MUTED2, bg=BG, padx=6, cursor='hand2')
        self.b_cfg.pack(side='right'); self.b_cfg._nodrag = True
        self.b_cfg.bind('<Button-1>', lambda e: self.open_config())
        self.b_cfg.bind('<Enter>', lambda e: self.b_cfg.config(fg=TXT))
        self.b_cfg.bind('<Leave>', lambda e: self.b_cfg.config(fg=MUTED2))

        self.b_update = tk.Label(head, bg=BG, bd=0, cursor='hand2'); self.b_update._nodrag = True
        self.b_update.bind('<Button-1>', lambda e: self.do_update())

        self.sep = tk.Frame(b, bg=LINE, height=1)
        self.panel = tk.Frame(b, bg=BG)
        top = tk.Frame(self.panel, bg=BG); top.pack(fill='x', pady=(10, 2))
        self.thumb = tk.Label(top, bg=BG, bd=0); self.thumb.pack(side='left', padx=(4, 12))
        info = tk.Frame(top, bg=BG); info.pack(side='left', fill='x', expand=True)
        self.l_name = tk.Label(info, text='', font=(FONT, 13, 'bold'), fg=TXT, bg=BG, anchor='w', justify='left', wraplength=250)
        self.l_name.pack(fill='x')
        self.l_cat = tk.Label(info, bg=BG, bd=0); self.l_cat.pack(anchor='w', pady=(7, 0))
        self.rows = tk.Frame(self.panel, bg=BG); self.rows.pack(fill='x', pady=(10, 2))
        self.b_reg = tk.Label(self.panel, bg=BG, bd=0, cursor='hand2'); self.b_reg._nodrag = True
        self.b_reg.bind('<Button-1>', lambda e: self.open_modal())
        self.l_foot = tk.Label(self.panel, text='', font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w')
        self.l_foot.pack(fill='x', padx=4, pady=(8, 4))

        self.set_toggle()
        self.w.drag_with(b)
        self.w.width = 0
        self.w.relayout(keep_pos=False)
        self.root.geometry(f'+{self.root.winfo_screenwidth() - CARD_W - 40}+16')
        self.open_until = 0

        mouse.Listener(on_move=self.on_move).start()
        keyboard.Listener(on_press=self.on_key_down, on_release=self.on_key_up).start()
        threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=self.startup, daemon=True).start()
        self.root.after(80, self.tick)

    # ---------- início ----------
    def startup(self):
        msg = refresh_db()
        refresh_tasks()
        refresh_hub()
        self.status_text = f'v{VERSION} · {msg}'
        get_ocr()
        self.status_text = f'v{VERSION} · {msg} · pronto'
        newv, url = check_update()
        if newv:
            self.update_url = url; self.q.put(('update', newv))

    def do_update(self):
        if not self.update_url or not FROZEN: return
        img = ImageTk.PhotoImage(ui.pill('baixando…', None, BG3, h=22, fsize=10))
        self.b_update.config(image=img); self.b_update.image = img
        threading.Thread(target=lambda: apply_update(self.update_url), daemon=True).start()

    # ---------- UI ----------
    def set_toggle(self):
        on = self.enabled
        img = ImageTk.PhotoImage(ui.pill('LIGADO' if on else 'PAUSADO', 'shield' if on else None,
                                         ORANGE if on else BG3, h=22, fsize=10))
        self.b_toggle.config(image=img); self.b_toggle.image = img

    def toggle(self):
        self.enabled = not self.enabled; self.set_toggle()
        if not self.enabled: self.close_panel()
        else: self.w.relayout()

    def open_panel(self):
        self.w.width = CARD_W
        if not self.panel.winfo_manager():
            self.sep.pack(fill='x', pady=(8, 0)); self.panel.pack(fill='x')
        self.w.relayout(); self.open_until = time.time() + cfg['show_s']

    def close_panel(self):
        if self.modal: return
        if self.panel.winfo_manager(): self.panel.pack_forget(); self.sep.pack_forget()
        self.w.width = 0                      # fechado: encolhe para caber só o cabeçalho
        self.w.set_border(LINE); self.w.relayout()

    def add_row(self, icon_name, color, title, sub=None, types=None):
        r = tk.Frame(self.rows, bg=BG); r.pack(fill='x', pady=3)
        ico_label(r, icon_name, 17, color).pack(side='left', padx=(5, 9), anchor='n', pady=1)
        tx = tk.Frame(r, bg=BG); tx.pack(side='left', fill='x', expand=True)
        if types:
            line = tk.Frame(tx, bg=BG); line.pack(fill='x')
            tk.Label(line, text=title, font=(FONT, 9, 'bold'), fg='#e4e4e7', bg=BG).pack(side='left')
            for i, tp in enumerate(types):
                type_chip(line, tp, fsize=9).pack(side='left', padx=(6 if i else 4, 0))
            if sub: tk.Label(tx, text=sub, font=(FONT, 8), fg=MUTED, bg=BG, anchor='w', justify='left', wraplength=300).pack(fill='x')
            return
        tk.Label(tx, text=title, font=(FONT, 9, 'bold'), fg='#e4e4e7', bg=BG, anchor='w', justify='left', wraplength=300).pack(fill='x')
        if sub:
            tk.Label(tx, text=sub, font=(FONT, 8), fg=MUTED, bg=BG, anchor='w', justify='left', wraplength=300).pack(fill='x')

    def set_pill(self, label, text, icon_name, color, h=23, fsize=10):
        img = ImageTk.PhotoImage(ui.pill(text, icon_name, color, h=h, fsize=fsize))
        label.config(image=img); label.image = img

    def show_item(self, name, icon_img, score):
        d = DB[name]; color, ico, tag, desc = CATS.get(d.get('cat', 'desconhecido'), CATS['desconhecido'])
        self.pending = (name, icon_img)
        for w in self.rows.winfo_children(): w.destroy()
        th = ImageTk.PhotoImage(item_thumb(icon_img)); self.thumb.config(image=th); self.thumb.image = th
        self.l_name.config(text=name.title())
        self.set_pill(self.l_cat, tag, ico, color)
        if d.get('alias_de'): self.add_row('link', SKY, 'Mesmo item que ' + d['alias_de'].title())
        for t in d.get('talents', []):
            tp = t['type'] if type_img(t['type']) else None
            self.add_row('sparkle', GREEN, (f"Talento #{t['n']} · {t['qty']} un." if tp else f"{t['type']} · Talento #{t['n']} · {t['qty']} un."),
                         t['buff'][:95], types=[tp] if tp else None)
        if d.get('boost'): self.add_row('flame', YELLOW, 'Boost:', types=sorted(set(d['boost'])))
        if d.get('stone'): self.add_row('gem', SKY, 'Stone de boost:', types=d['stone'])
        if d.get('fragment'): self.add_row('hex', SKY, 'Fragmento de boost:', types=d['fragment'])
        if d.get('drops'):
            dr = d['drops']
            self.add_row('target', '#c084fc', 'Drop de ' + ', '.join(dr[:4]) + ('  +' + str(len(dr) - 4) if len(dr) > 4 else ''))
        if d.get('nota'): self.add_row('pencil', MUTED, d['nota'])
        if d.get('custom'): self.add_row('pencil', INDIGO, 'Cadastrado por você')
        if not self.rows.winfo_children(): self.add_row(ico, color, desc)
        self.b_reg.pack_forget()
        self.w.set_border(color)
        self.update_foot()
        self.open_panel()

    def show_novo(self, name, icon_img):
        self.pending = (name, icon_img)
        for w in self.rows.winfo_children(): w.destroy()
        th = ImageTk.PhotoImage(item_thumb(icon_img)); self.thumb.config(image=th); self.thumb.image = th
        self.l_name.config(text=name.title())
        self.set_pill(self.l_cat, 'NÃO CADASTRADO', 'search', INDIGO)
        self.add_row('search', INDIGO, 'Este item ainda não está na base do site.', 'Cadastre para que serve e ele passa a aparecer aqui.')
        self.set_pill(self.b_reg, '   Cadastrar este item   ', 'plus', INDIGO, h=30, fsize=11)
        self.b_reg.pack(pady=(6, 2))
        self.w.set_border(INDIGO)
        self.l_foot.config(text=f'{len(unknown)} aguardando cadastro  ·  {self.status_text}')
        self.open_panel()

    def update_foot(self):
        m = cfg['mode']; k = pretty_key(cfg['hotkey'])
        modo = 'automático' if m == 'auto' else (f'tecla {k}' if m == 'hotkey' else f'automático + {k}')
        self.l_foot.config(text=f'{modo}  ·  catálogo {len(catalog)}  ·  {self.status_text}')

    # ---------- entrada ----------
    def on_move(self, x, y): self.pos = (x, y); self.last_move = time.time()

    def on_key_down(self, key):
        b = base_key(key)
        if b in ('ctrl', 'alt', 'shift'): self.held.add(b); return
        combo = combo_str(key, self.held)
        if not combo: return
        if self.recording: self.q.put(('recorded', combo)); return
        if cfg['mode'] in ('hotkey', 'ambos') and self.enabled and combo == cfg['hotkey']:
            threading.Thread(target=self.capture_now, daemon=True).start()

    def on_key_up(self, key): self.held.discard(base_key(key))

    def capture_now(self):
        try:
            lines, icon = read_tooltip(*self.pos)
            best = None
            for line in lines:
                name, score, read = match_name(line)
                if name: best = ('ok', name, icon, score); break
                if read and not best: best = ('novo', read, icon, 0)
            if not best: self.q.put(('nada', None)); return
            if best[0] == 'ok':
                self.save_catalog(best[1], best[2], best[3]); self.q.put(('show', best[1:]))
            else:
                self.save_unknown(best[1], best[2]); self.q.put(('novo', best[1:]))
        except Exception as e: log('capture_now', e)

    def worker(self):
        last_pos, tries, done, last_sig, last_look = None, 0, False, None, 0
        while True:
            time.sleep(0.04)
            try:
                if not self.enabled or cfg['mode'] not in ('auto', 'ambos'): continue
                if self.pos != last_pos:
                    last_pos, tries, done, last_sig, last_look = self.pos, 0, False, None, 0
                if done or tries >= len(TRIES): continue
                now = time.time()
                if now - self.last_move < TRIES[tries] or now - last_look < POLL: continue
                last_look = now
                x, y = self.pos
                try:
                    rx, ry = self.root.winfo_x(), self.root.winfo_y()
                    if rx <= x <= rx + self.root.winfo_width() and ry <= y <= ry + self.root.winfo_height():
                        done = True; continue
                except Exception: pass
                img, icon, sig = grab(x, y)
                if sig == last_sig: continue      # tela igual: não gasta OCR nem tentativa
                last_sig = sig
                tries += 1
                lines = ocr_lines(img)
                best = None
                for line in lines:
                    name, score, read = match_name(line)
                    if name: best = ('ok', name, icon, score); break
                    if read and not best: best = ('novo', read, icon, 0)
                if best and best[0] == 'ok':
                    done = True; self.save_catalog(best[1], best[2], best[3]); self.q.put(('show', best[1:]))
                elif best and tries >= len(TRIES):
                    done = True; self.save_unknown(best[1], best[2]); self.q.put(('novo', best[1:]))
            except Exception as e:
                log('worker', e, traceback.format_exc()[:300])

    def save_catalog(self, name, icon, score):
        slug = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        if name not in catalog or score > catalog[name].get('score', 0):
            try: icon.save(os.path.join(CATALOG_DIR, slug + '.png'))
            except Exception: pass
            catalog[name] = {'file': slug + '.png', 'score': round(score, 3), 'ts': int(time.time())}
            json.dump(catalog, open(CATALOG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def save_unknown(self, name, icon):
        slug = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        if name not in unknown:
            try: icon.save(os.path.join(CATALOG_DIR, '_novo_' + slug + '.png'))
            except Exception: pass
            unknown[name] = {'file': '_novo_' + slug + '.png', 'vezes': 0, 'ts': int(time.time())}
        unknown[name]['vezes'] += 1
        json.dump(unknown, open(UNKNOWN_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------- janelas auxiliares ----------
    def _modal(self, title, icon_name, color, width=380):
        if self.modal: self.close_modal()
        self.open_until = time.time() + 9999
        m = Round(self.root, width=width, border=color, alpha=max(0.9, cfg['alpha'] / 100)); self.modal = m
        h = tk.Frame(m.body, bg=BG); h.pack(fill='x', pady=(2, 6), padx=4)
        ico_label(h, icon_name, 20, color).pack(side='left', padx=(2, 8))
        tk.Label(h, text=title, font=(FONT, 12, 'bold'), fg=TXT, bg=BG).pack(side='left')
        cl = tk.Label(h, text='✕', font=(FONT, 11), fg=MUTED2, bg=BG, padx=6, cursor='hand2')
        cl.pack(side='right'); cl._nodrag = True
        cl.bind('<Button-1>', lambda e: self.close_modal())
        cl.bind('<Enter>', lambda e: cl.config(fg=RED)); cl.bind('<Leave>', lambda e: cl.config(fg=MUTED2))
        tk.Frame(m.body, bg=LINE, height=1).pack(fill='x', padx=2)
        m.drag_with(m.body)
        return m

    def _place_modal(self, m):
        m.relayout(keep_pos=False)
        m.win.update_idletasks()
        x = self.root.winfo_x() - m.win.winfo_width() - 12
        if x < 10: x = self.root.winfo_x() + self.root.winfo_width() + 12
        m.win.geometry(f'+{max(10, x)}+{self.root.winfo_y() + 30}')

    def section(self, parent, text):
        tk.Label(parent, text=text, font=(FONT, 8, 'bold'), fg=MUTED2, bg=BG, anchor='w').pack(fill='x', padx=4, pady=(12, 5))

    def entry(self, parent, value=''):
        wrap = tk.Frame(parent, bg=BG2); wrap.pack(fill='x', padx=2)
        e = tk.Entry(wrap, font=(FONT, 10), bg=BG2, fg=TXT, insertbackground=ORANGE, relief='flat', bd=0, highlightthickness=0)
        e.insert(0, value); e.pack(fill='x', padx=10, pady=9)
        e._nodrag = True; wrap._nodrag = True
        return e

    def button(self, parent, text, color, cmd, icon_name=None, h=30, side=None, **kw):
        img = ImageTk.PhotoImage(ui.pill('  ' + text + '  ', icon_name, color, h=h, fsize=10))
        l = tk.Label(parent, image=img, bg=BG, bd=0, cursor='hand2'); l.image = img; l._nodrag = True
        l.bind('<Button-1>', lambda e: cmd())
        l.pack(side=side, **kw) if side else l.pack(**kw)
        return l

    # ---------- cadastro ----------
    def open_modal(self):
        if not self.pending: return
        name, icon_img = self.pending
        m = self._modal('Cadastrar item', 'plus', INDIGO)
        c = m.body
        self.section(c, 'NOME DO ITEM (COMO APARECE NO JOGO)')
        e_name = self.entry(c, name.title())
        self.section(c, 'PARA QUE SERVE?')
        var = tk.StringVar(value='npc')
        for key, label, color in CAT_OPTS:
            row = tk.Frame(c, bg=BG); row.pack(fill='x', padx=2, pady=1)
            r = tk.Radiobutton(row, value=key, variable=var, bg=BG, activebackground=BG, selectcolor=BG3,
                               bd=0, highlightthickness=0, cursor='hand2')
            r.pack(side='left'); r._nodrag = True
            ico_label(row, CATS[key][1], 15, color).pack(side='left', padx=(2, 7))
            tk.Label(row, text=label, font=(FONT, 10), fg=TXT, bg=BG).pack(side='left')
        self.section(c, 'OBSERVAÇÃO (OPCIONAL)')
        e_note = self.entry(c)
        self.section(c, 'OU É O MESMO QUE UM ITEM JÁ CADASTRADO')
        e_alias = self.entry(c)
        lb = tk.Listbox(c, height=4, font=(FONT, 9), bg=BG2, fg=TXT, relief='flat', bd=0,
                        highlightthickness=0, selectbackground=INDIGO, activestyle='none')
        lb._nodrag = True
        def filt(*_):
            q = norm(e_alias.get()); lb.delete(0, 'end')
            if len(q) >= 2:
                for n in [n for n in NAMES if q in n][:20]: lb.insert('end', n.title())
                lb.pack(fill='x', padx=2, pady=(4, 0))
            else:
                lb.pack_forget()
            m.relayout()
        e_alias.bind('<KeyRelease>', filt)
        def pick(_):
            if lb.curselection():
                e_alias.delete(0, 'end'); e_alias.insert(0, lb.get(lb.curselection()[0])); lb.pack_forget(); m.relayout()
        lb.bind('<<ListboxSelect>>', pick)
        bar = tk.Frame(c, bg=BG); bar.pack(fill='x', pady=(16, 4))
        self.button(bar, 'Salvar', GREEN, lambda: self.save_custom(e_name.get(), var.get(), e_note.get(), e_alias.get(), icon_img), 'plus', side='right')
        self.button(bar, 'Cancelar', BG3, self.close_modal, side='right', padx=(0, 8))
        tk.Label(bar, text=f'{len(custom)} cadastrados', font=(FONT, 8), fg=MUTED2, bg=BG).pack(side='left', padx=4)
        self._place_modal(m)

    def save_custom(self, name, cat, note, alias, icon_img):
        name = norm(name)
        if not name: return
        alias = norm(alias)
        custom[name] = {'cat': cat, 'note': note.strip(), 'alias': alias if alias in DB else None, 'ts': int(time.time())}
        json.dump(custom, open(CUSTOM_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        unknown.pop(name, None)
        json.dump(unknown, open(UNKNOWN_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        global NAMES
        merge_custom(); NAMES = list(DB.keys())
        self.save_catalog(name, icon_img, 1.0)
        self.close_modal()
        self.q.put(('show', (name, icon_img, 1.0)))

    # ---------- configurações ----------
    def open_config(self):
        m = self._modal('Configurações', 'shield', ORANGE, width=400)
        c = m.body
        self.section(c, 'QUANDO LER O ITEM')
        mode = tk.StringVar(value=cfg['mode']); self._mode_var = mode
        def apply_mode():
            cfg['mode'] = mode.get(); save_cfg(); self.update_foot()
        for key, title, sub in (('auto', 'Automático', 'lê sozinho quando você para o mouse sobre o item'),
                                ('hotkey', 'Só quando eu apertar a tecla', 'não fica lendo a tela o tempo todo'),
                                ('ambos', 'Ambos', 'lê sozinho e também quando você aperta a tecla')):
            row = tk.Frame(c, bg=BG); row.pack(fill='x', padx=2, pady=3)
            r = tk.Radiobutton(row, value=key, variable=mode, bg=BG, activebackground=BG, selectcolor=BG3,
                               bd=0, highlightthickness=0, cursor='hand2', command=apply_mode)
            r.pack(side='left', anchor='n'); r._nodrag = True
            tx = tk.Frame(row, bg=BG); tx.pack(side='left', fill='x', expand=True, padx=(4, 0))
            tk.Label(tx, text=title, font=(FONT, 10, 'bold'), fg=TXT, bg=BG, anchor='w').pack(fill='x')
            tk.Label(tx, text=sub, font=(FONT, 8), fg=MUTED, bg=BG, anchor='w').pack(fill='x')

        card = tk.Frame(c, bg=BG2); card.pack(fill='x', padx=2, pady=(14, 4))
        tk.Label(card, text='TECLA DE ATALHO', font=(FONT, 8, 'bold'), fg=MUTED2, bg=BG2, anchor='w').pack(fill='x', padx=12, pady=(10, 6))
        line = tk.Frame(card, bg=BG2); line.pack(fill='x', padx=12, pady=(0, 8))
        l_key = tk.Label(line, text=pretty_key(cfg['hotkey']), font=(FONT, 13, 'bold'), fg=SKY, bg=BG3, padx=20, pady=7)
        l_key.pack(side='left')
        img = ImageTk.PhotoImage(ui.pill('  Gravar tecla  ', 'pencil', INDIGO, h=32, fsize=10))
        b_rec = tk.Label(line, image=img, bg=BG2, bd=0, cursor='hand2'); b_rec.image = img; b_rec._nodrag = True
        b_rec.pack(side='left', padx=10)
        def start_rec(_=None):
            self.recording = True
            i2 = ImageTk.PhotoImage(ui.pill('  Aperte agora…  ', None, ORANGE, h=32, fsize=10))
            b_rec.config(image=i2); b_rec.image = i2; l_key.config(text='…', fg=ORANGE)
        b_rec.bind('<Button-1>', start_rec)
        tk.Label(card, text='Escolha uma tecla que o jogo não use (ex.: F4, Ctrl+Q).', font=(FONT, 8), fg=MUTED2,
                 bg=BG2, anchor='w', wraplength=340, justify='left').pack(fill='x', padx=12, pady=(0, 10))
        self._cfg_widgets = (l_key, b_rec)

        self.section(c, 'TRANSPARÊNCIA DO PAINEL')
        arow = tk.Frame(c, bg=BG); arow.pack(fill='x', padx=2)
        l_alpha = tk.Label(arow, text=f"{cfg['alpha']}%", font=(FONT, 10, 'bold'), fg=SKY, bg=BG, width=5, anchor='e')
        l_alpha.pack(side='right', padx=(8, 2))
        def set_alpha(v):
            a = int(float(v)); cfg['alpha'] = a; save_cfg()
            l_alpha.config(text=f'{a}%')
            try:
                self.root.attributes('-alpha', a / 100)
                if self.modal: self.modal.win.attributes('-alpha', max(0.9, a / 100))
            except Exception: pass
        av = tk.IntVar(value=cfg['alpha'])
        sa = tk.Scale(arow, from_=30, to=100, orient='horizontal', variable=av, bg=BG, fg=BG, troughcolor=BG3,
                      highlightthickness=0, bd=0, sliderrelief='flat', activebackground=SKY, showvalue=False,
                      command=set_alpha)
        sa.pack(fill='x'); sa._nodrag = True
        tk.Label(c, text='Quanto menor, mais o jogo aparece através do painel.', font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w').pack(fill='x', padx=4, pady=(4, 0))

        self.section(c, 'TEMPO QUE O PAINEL FICA ABERTO (SEGUNDOS)')
        sv = tk.IntVar(value=cfg['show_s'])
        sc = tk.Scale(c, from_=3, to=30, orient='horizontal', variable=sv, bg=BG, fg=MUTED, troughcolor=BG3,
                      highlightthickness=0, bd=0, sliderrelief='flat', activebackground=ORANGE, font=(FONT, 8),
                      command=lambda v: (cfg.__setitem__('show_s', int(float(v))), save_cfg()))
        sc.pack(fill='x', padx=2); sc._nodrag = True

        tk.Frame(c, bg=LINE, height=1).pack(fill='x', padx=2, pady=12)
        tk.Label(c, text=f'{len(DB)} itens na base  ·  {len(custom)} cadastrados  ·  {len(unknown)} aguardando',
                 font=(FONT, 8), fg=MUTED, bg=BG, anchor='w').pack(fill='x', padx=4)
        bar = tk.Frame(c, bg=BG); bar.pack(fill='x', pady=(14, 4))
        self.button(bar, 'Fechar', GREEN, self.close_modal, side='right')
        self.button(bar, 'Abrir pasta', BG3, lambda: subprocess.Popen(['explorer', DATA_DIR]), side='right', padx=(0, 8))
        self._place_modal(m)

    def open_tasks(self):
        m = self._modal('Consultar tasks', 'target', SKY, width=430)
        c = m.body
        self.section(c, 'NOME DO POKÉMON, NPC OU RECOMPENSA')
        e = self.entry(c)
        info = tk.Label(c, text=f"{len(TASKS.get('tasks', []))} tasks da wiki oficial", font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w')
        info.pack(fill='x', padx=4, pady=(6, 0))
        res = tk.Frame(c, bg=BG); res.pack(fill='x', pady=(6, 2))

        def draw(*_):
            for w in res.winfo_children(): w.destroy()
            found = search_tasks(e.get())
            if not found:
                if len(norm(e.get())) >= 2:
                    tk.Label(res, text='Nenhuma task encontrada.', font=(FONT, 9), fg=MUTED, bg=BG, anchor='w').pack(fill='x', padx=4, pady=6)
                    info.config(text='0 resultados')
                m.relayout(); return
            info.config(text=f'{len(found)} resultado(s)')
            for t in found:
                card = tk.Frame(res, bg=BG2); card.pack(fill='x', pady=4)
                top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(9, 2))
                tk.Label(top, text=t.get('npc', '?'), font=(FONT, 11, 'bold'), fg=TXT, bg=BG2).pack(side='left')
                tk.Label(top, text='  ' + t.get('region', ''), font=(FONT, 8), fg=MUTED, bg=BG2).pack(side='left')
                if t.get('loc'):
                    lk = tk.Label(top, text='onde fica', font=(FONT, 8, 'bold'), fg=SKY, bg=BG2, cursor='hand2')
                    lk.pack(side='right'); lk._nodrag = True
                    lk.bind('<Button-1>', lambda ev, u=t['loc']: webbrowser.open(u))
                for o in t.get('objectives', []):
                    txt = f"• {o['qty']}x {o['target']}" if o.get('qty') else '• ' + o.get('text', '')
                    tk.Label(card, text=txt, font=(FONT, 9), fg='#e4e4e7', bg=BG2, anchor='w',
                             wraplength=380, justify='left').pack(fill='x', padx=16)
                rw = ' · '.join(f"{r.get('qty','')} {r.get('label','')}".strip() for r in t.get('rewards', [])) or 'sem recompensa listada'
                tk.Label(card, text='🎁 ' + rw, font=(FONT, 8), fg=YELLOW, bg=BG2, anchor='w',
                         wraplength=380, justify='left').pack(fill='x', padx=16, pady=(4, 10))
            m.relayout()

        e.bind('<KeyRelease>', draw)
        bar = tk.Frame(c, bg=BG); bar.pack(fill='x', pady=(10, 4))
        self.button(bar, 'Fechar', GREEN, self.close_modal, side='right')
        if self.pending:
            nome = self.pending[0].title()
            self.button(bar, nome[:16], SKY, lambda: (e.delete(0, 'end'), e.insert(0, nome), draw()), 'search', side='left')
        self._place_modal(m)
        e.focus_set()

    # ---------- central de consultas rápidas (abas) ----------
    HUB_TABS = (('pokemon', '', 'Pokémon'), ('timers', '', 'Timers'), ('task', '', 'Task'),
                ('times', '', 'Times'), ('medalhas', '', 'Medalhas'), ('tabelas', '', 'Tabelas'),
                ('videos', '', 'Vídeos'))

    def open_hub(self, tab=None):
        tab = tab or cfg.get('hub_tab', 'pokemon')
        m = self._modal('Consulta rápida', 'search', SKY, width=470)
        c = m.body
        bar = tk.Frame(c, bg=BG); bar.pack(fill='x', pady=(8, 2))
        body = tk.Frame(c, bg=BG); body.pack(fill='x')
        self._hub = (m, body)
        labels = {}
        def select(key):
            cfg['hub_tab'] = key; save_cfg()
            for k, l in labels.items():
                l.config(bg=SKY if k == key else BG2, fg='#ffffff' if k == key else MUTED)
            for w in body.winfo_children(): w.destroy()
            getattr(self, 'hub_' + key)(body)
            m.relayout()
        for key, ico, name in self.HUB_TABS:
            l = tk.Label(bar, text=(f'{ico} {name}' if ico else name), font=(FONT, 8, 'bold'), bg=BG2, fg=MUTED, padx=6, pady=5, cursor='hand2')
            l.pack(side='left', padx=(0, 3)); l._nodrag = True
            l.bind('<Button-1>', lambda e, k=key: select(k))
            labels[key] = l
        self._hub_select = select
        select(tab if hasattr(self, 'hub_' + tab) else 'pokemon')
        self._place_modal(m)

    def _hub_relayout(self):
        try: self._hub[0].relayout()
        except Exception: pass

    def _card(self, parent):
        f = tk.Frame(parent, bg=BG2); f.pack(fill='x', pady=3)
        return f

    def _txt(self, parent, text, size=9, color=None, bold=False, bg=BG2, padx=12, pady=0):
        l = tk.Label(parent, text=text, font=(FONT, size, 'bold' if bold else 'normal'), fg=color or '#e4e4e7', bg=bg,
                     anchor='w', justify='left', wraplength=420)
        l.pack(fill='x', padx=padx, pady=pady)
        return l

    def _link(self, parent, text, url, bg=BG2):
        l = tk.Label(parent, text=text, font=(FONT, 8, 'bold'), fg=SKY, bg=bg, cursor='hand2')
        l._nodrag = True; l.bind('<Button-1>', lambda e: webbrowser.open(url))
        return l

    def _search_box(self, parent, hint, on_change, value=''):
        self.section(parent, hint)
        e = self.entry(parent, value)
        res = tk.Frame(parent, bg=BG); res.pack(fill='x', pady=(6, 2))
        def run(*_):
            for w in res.winfo_children(): w.destroy()
            on_change(e.get(), res)
            self._hub_relayout()
        e.bind('<KeyRelease>', run)
        e.focus_set()
        run()
        return e

    # --- 🔍 Pokémon ---
    def hub_pokemon(self, body):
        start = self.pending[0].title() if self.pending else ''
        def draw(q, res):
            s = norm(q)
            if len(s) < 2:
                self._txt(res, f"{len(HUB.get('pokemon', []))} Pokémon. Digite o nome (ex.: gengar, shiny onix).", 8, MUTED2, bg=BG, padx=4)
                return
            ps = HUB.get('pokemon', [])
            found = [p for p in ps if norm(p['n']) == s] + [p for p in ps if s in norm(p['n']) and norm(p['n']) != s]
            if not found:
                self._txt(res, 'Nenhum Pokémon encontrado.', 9, MUTED, bg=BG, padx=4); return
            if len(found) > 1 and norm(found[0]['n']) != s:
                row = tk.Frame(res, bg=BG); row.pack(fill='x')
                for p in found[:6]:
                    l = tk.Label(row, text=p['n'], font=(FONT, 8), bg=BG3, fg=TXT, padx=6, pady=3, cursor='hand2')
                    l.pack(side='left', padx=(0, 4), pady=2); l._nodrag = True
                    l.bind('<Button-1>', lambda e, n=p['n']: (self._poke_entry.delete(0, 'end'), self._poke_entry.insert(0, n), self._poke_entry.event_generate('<KeyRelease>')))
            p = found[0]
            card = self._card(res)
            top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(10, 4))
            tk.Label(top, text=p['n'], font=(FONT, 13, 'bold'), fg=TXT, bg=BG2).pack(side='left')
            for tp in re.split(r'[\\/,]| e ', p.get('t', '')):
                if tp.strip() and type_img(tp): type_chip(top, tp.strip(), bg=BG2, size=18, fsize=9, color=TXT).pack(side='left', padx=(8, 0))
            tk.Label(top, text=f"  ·  {p.get('tier', '')}", font=(FONT, 9, 'bold'), fg=YELLOW, bg=BG2).pack(side='left')
            links = tk.Frame(card, bg=BG2); links.pack(fill='x', padx=12)
            for k, u in (p.get('hunts') or {}).items():
                if str(u).startswith('http'):
                    self._link(links, f'hunt {k}', u).pack(side='left', padx=(0, 10))
            if p.get('drops'): self._txt(card, 'Drops: ' + ', '.join(p['drops'][:14]), pady=(6, 0))
            if p.get('dens'): self._txt(card, 'Dens: ' + ', '.join(p['dens']), pady=(4, 0))
            if p.get('dung'): self._txt(card, 'Dungeons: ' + ', '.join(p['dung']), pady=(4, 0))
            md = p.get('medal') or {}
            if md.get('buff') or md.get('debuff'):
                self._txt(card, f"Medalha:  ▲ {md.get('buff') or '—'}    ▼ {md.get('debuff') or 'nenhuma'}", pady=(4, 0))
            for t in p.get('tasks', [])[:4]:
                row = tk.Frame(card, bg=BG2); row.pack(fill='x', padx=12, pady=(4, 0))
                tk.Label(row, text=f"Task · {t['npc']}" + (f" ({t['region']})" if t.get('region') else '') + (f" — {t['obj']}" if t.get('obj') else ''),
                         font=(FONT, 9), fg='#e4e4e7', bg=BG2, anchor='w', wraplength=330, justify='left').pack(side='left')
                if t.get('loc'): self._link(row, 'onde', t['loc']).pack(side='right')
                if t.get('rew'): self._txt(card, '        Recompensa: ' + t['rew'], 8, YELLOW)
            tk.Frame(card, bg=BG2, height=10).pack()
        self._poke_entry = self._search_box(body, 'NOME DO POKÉMON', draw, start)

    # --- ⏱ Timers ---
    def hub_timers(self, body):
        self.section(body, 'NOVO TIMER')
        row = tk.Frame(body, bg=BG); row.pack(fill='x')
        name = tk.Entry(row, font=(FONT, 10), bg=BG2, fg=TXT, insertbackground=ORANGE, relief='flat', width=22)
        name.insert(0, 'Rocket'); name.pack(side='left', ipady=6, padx=(2, 6)); name._nodrag = True
        mins = tk.Entry(row, font=(FONT, 10), bg=BG2, fg=TXT, insertbackground=ORANGE, relief='flat', width=6, justify='center')
        mins.insert(0, '60'); mins.pack(side='left', ipady=6); mins._nodrag = True
        tk.Label(row, text='min', font=(FONT, 8), fg=MUTED, bg=BG).pack(side='left', padx=(4, 8))
        def add(n=None, mm=None):
            try: mm = float(mm if mm is not None else mins.get().replace(',', '.'))
            except ValueError: return
            cfg.setdefault('timers', []).append({'name': (n or name.get() or 'Timer').strip(), 'mins': mm, 'end': time.time() + mm * 60, 'done': False})
            save_cfg(); self._hub_select('timers')
        self.button(row, 'Iniciar', GREEN, add, 'plus', h=28, side='left')
        presets = cfg.get('timer_presets') or [['Rocket', 60], ['Polícia', 60], ['Boss de Guild', 120], ['Dungeon', 30]]
        pr = tk.Frame(body, bg=BG); pr.pack(fill='x', pady=(6, 0))
        for n, mm in presets:
            l = tk.Label(pr, text=f'{n} {int(mm)}m', font=(FONT, 8), bg=BG3, fg=TXT, padx=6, pady=3, cursor='hand2')
            l.pack(side='left', padx=(2, 4)); l._nodrag = True
            l.bind('<Button-1>', lambda e, n=n, mm=mm: add(n, mm))
        tk.Label(body, text='Os tempos são ajustáveis: digite o nome e os minutos que valem para você. O aviso toca mesmo com esta janela fechada.',
                 font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w', wraplength=440, justify='left').pack(fill='x', padx=4, pady=(6, 0))

        dens = HUB.get('dens', [])
        if dens:
            self.section(body, 'DENS (DURAÇÃO DA PLANILHA)')
            dv = tk.StringVar(value=dens[0]['n'])
            drow = tk.Frame(body, bg=BG); drow.pack(fill='x')
            om = tk.OptionMenu(drow, dv, *[d['n'] for d in dens])
            om.config(bg=BG2, fg=TXT, activebackground=BG3, activeforeground=TXT, relief='flat', highlightthickness=0, font=(FONT, 9), width=20)
            om['menu'].config(bg=BG2, fg=TXT, font=(FONT, 9))
            om.pack(side='left', padx=(2, 8)); om._nodrag = True
            def add_den():
                d = next((x for x in dens if x['n'] == dv.get()), None)
                if not d: return
                h, mi, s = (list(map(int, str(d['time']).split(':'))) + [0, 0, 0])[:3]
                add('Den ' + d['n'], h * 60 + mi + s / 60)
            self.button(drow, 'Iniciar den', SKY, add_den, 'plus', h=28, side='left')

        self.section(body, 'RODANDO')
        lst = tk.Frame(body, bg=BG); lst.pack(fill='x')
        ts = cfg.get('timers', [])
        if not ts: self._txt(lst, 'Nenhum timer rodando.', 9, MUTED, bg=BG, padx=4)
        self._timer_labels = []
        for i, t in enumerate(ts):
            card = self._card(lst)
            r = tk.Frame(card, bg=BG2); r.pack(fill='x', padx=12, pady=8)
            tk.Label(r, text=t['name'], font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left')
            x = tk.Label(r, text='✕', font=(FONT, 10), fg=MUTED2, bg=BG2, cursor='hand2'); x.pack(side='right'); x._nodrag = True
            x.bind('<Button-1>', lambda e, i=i: (cfg['timers'].pop(i), save_cfg(), self._hub_select('timers')))
            rs = tk.Label(r, text='↻', font=(FONT, 10, 'bold'), fg=SKY, bg=BG2, cursor='hand2'); rs.pack(side='right', padx=8); rs._nodrag = True
            rs.bind('<Button-1>', lambda e, t=t: (t.update(end=time.time() + t['mins'] * 60, done=False), save_cfg(), self._hub_select('timers')))
            lb = tk.Label(r, text='', font=(FONT, 11, 'bold'), fg=YELLOW, bg=BG2); lb.pack(side='right', padx=8)
            self._timer_labels.append((lb, t))
        self._timer_draw()

    def _timer_draw(self):
        for lb, t in getattr(self, '_timer_labels', []):
            try:
                left = t['end'] - time.time()
                if left <= 0: lb.config(text='LIBERADO', fg=GREEN)
                else:
                    h, r = divmod(int(left), 3600); mi, s = divmod(r, 60)
                    lb.config(text=(f'{h}:{mi:02d}:{s:02d}' if h else f'{mi:02d}:{s:02d}'), fg=YELLOW)
            except Exception: pass

    def _timer_check(self):
        for t in cfg.get('timers', []):
            if not t.get('done') and time.time() >= t['end']:
                t['done'] = True; save_cfg()
                try:
                    import winsound; winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception: pass
                for w in self.rows.winfo_children(): w.destroy()
                self.thumb.config(image=''); self.thumb.image = None
                self.l_name.config(text=f"{t['name']} liberou!")
                self.set_pill(self.l_cat, 'TIMER', 'target', GREEN)
                self.add_row('target', GREEN, f"Passaram {int(t['mins'])} minutos.", 'Abra ⏱ Timers para reiniciar.')
                self.b_reg.pack_forget(); self.w.set_border(GREEN); self.update_foot()
                self.open_panel(); self.open_until = time.time() + 15

    # --- 📋 Task acompanhada ---
    def hub_task(self, body):
        tr = cfg.get('track')
        if tr:
            card = self._card(body)
            top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(10, 4))
            tk.Label(top, text='Acompanhando: ' + tr['npc'], font=(FONT, 11, 'bold'), fg=TXT, bg=BG2).pack(side='left')
            if tr.get('loc'): self._link(top, '🗺 onde fica', tr['loc']).pack(side='right')
            for o in tr['objectives']:
                row = tk.Frame(card, bg=BG2); row.pack(fill='x', padx=12, pady=3)
                qty = int(o.get('qty') or 0)
                done = o.get('done', 0)
                ok = qty and done >= qty
                tk.Label(row, text=(o.get('target') or o.get('text', ''))[:26], font=(FONT, 10), fg=GREEN if ok else TXT, bg=BG2,
                         width=18, anchor='w').pack(side='left')
                tk.Label(row, text=f'{done}/{qty}' if qty else f'{done}', font=(FONT, 10, 'bold'), fg=GREEN if ok else YELLOW,
                         bg=BG2, width=9).pack(side='left')
                for d in (1, 5, 10, -1):
                    b = tk.Label(row, text=f'{d:+d}', font=(FONT, 8, 'bold'), bg=BG3 if d > 0 else BG, fg=TXT if d > 0 else MUTED,
                                 padx=6, pady=2, cursor='hand2')
                    b.pack(side='left', padx=2); b._nodrag = True
                    b.bind('<Button-1>', lambda e, o=o, d=d: (o.__setitem__('done', max(0, o.get('done', 0) + d)), save_cfg(), self._hub_select('task')))
            if tr.get('rew'): self._txt(card, 'Recompensa: ' + tr['rew'], 8, YELLOW, pady=(6, 0))
            b = tk.Frame(card, bg=BG2); b.pack(fill='x', padx=12, pady=10)
            self.button(b, 'Parar de acompanhar', BG3, lambda: (cfg.pop('track', None), save_cfg(), self._hub_select('task')), side='left')
        def draw(q, res):
            found = search_tasks(q, limit=5)
            if not found:
                if len(norm(q)) >= 2: self._txt(res, 'Nenhuma task encontrada.', 9, MUTED, bg=BG, padx=4)
                return
            for t in found:
                card = self._card(res)
                top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(8, 2))
                tk.Label(top, text=t.get('npc', '?'), font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left')
                tk.Label(top, text='  ' + t.get('region', ''), font=(FONT, 8), fg=MUTED, bg=BG2).pack(side='left')
                def follow(t=t):
                    cfg['track'] = {'npc': t.get('npc', ''), 'loc': t.get('loc', ''),
                                    'rew': ' · '.join(f"{r.get('qty', '')} {r.get('label', '')}".strip() for r in t.get('rewards', [])),
                                    'objectives': [dict(o, done=0) for o in t.get('objectives', [])]}
                    save_cfg(); self._hub_select('task')
                fl = tk.Label(top, text='+ acompanhar', font=(FONT, 8, 'bold'), fg=GREEN, bg=BG2, cursor='hand2')
                fl.pack(side='right'); fl._nodrag = True; fl.bind('<Button-1>', lambda e, f=follow: f())
                self._txt(card, '  ·  '.join(f"{o['qty']}x {o['target']}" if o.get('qty') else o.get('text', '') for o in t.get('objectives', [])), 9, pady=(0, 8))
        self._search_box(body, 'PROCURAR TASK PARA ACOMPANHAR (POKÉMON, NPC OU RECOMPENSA)', draw)

    # --- 🧭 Times ---
    def hub_times(self, body):
        def draw(q, res):
            s = norm(q)
            ts = HUB.get('teams', [])
            found = [t for t in ts if not s or s in norm(t['name'] + ' ' + t['sub'] + ' ' + ' '.join(sum((r[1] for r in t['rows']), [])))]
            if not s:
                row = tk.Frame(res, bg=BG); row.pack(fill='x')
                for i, t in enumerate(ts[:24]):
                    l = tk.Label(row, text=t['name'], font=(FONT, 8), bg=BG3, fg=TXT, padx=5, pady=3, cursor='hand2')
                    l.grid(row=i // 6, column=i % 6, padx=2, pady=2, sticky='we'); l._nodrag = True
                    l.bind('<Button-1>', lambda e, n=t['name']: (self._team_entry.delete(0, 'end'), self._team_entry.insert(0, n), self._team_entry.event_generate('<KeyRelease>')))
                return
            for t in found[:4]:
                card = self._card(res)
                top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(8, 2))
                tk.Label(top, text=t['name'], font=(FONT, 11, 'bold'), fg=TXT, bg=BG2).pack(side='left')
                tk.Label(top, text=f"  {t['sub']}  ·  guia {t['src']}", font=(FONT, 8), fg=MUTED, bg=BG2).pack(side='left')
                for label, names in t['rows']:
                    if names: self._txt(card, f'{label}: ' + ', '.join(names), 9)
                tk.Frame(card, bg=BG2, height=8).pack()
            if not found: self._txt(res, 'Nada encontrado.', 9, MUTED, bg=BG, padx=4)
        self._team_entry = self._search_box(body, 'ELEMENTO, HUNT OU POKÉMON', draw)

    # --- 🏅 Medalhas ---
    MEDAL_PT = {'Damage Boost': 'Dano', 'Critical Chance': 'Chance crítico', 'Critical Damage': 'Dano crítico',
                'Precision Percent': 'Precisão', 'Life Leech': 'Roubo de vida', 'Defense Boost': 'Defesa', 'HP Boost': 'Vida',
                'Evasion Percent': 'Evasão', 'Critical Resistance': 'Resist. crítico', 'Pokemon Speed': 'Veloc. Pokémon',
                'Character Speed': 'Veloc. personagem', 'Fly Speed': 'Fly', 'Ride Speed': 'Ride', 'Surf Speed': 'Surf',
                'Catch Rate': 'Catch', 'Shiny Catch Rate': 'Catch shiny', 'Shiny Charm Rate': 'Shiny Charm', 'Loot Boost': 'Loot',
                'Fishing Skill': 'Skill pesca', 'Extra Fishing': 'Pesca extra', 'Shiny Fishing Rate': 'Shiny pesca',
                'Headbutt Skill': 'Skill Headbutt', 'Shiny Headbutt Rate': 'Shiny Headbutt'}
    LEVELS = ('Bronze', 'Silver', 'Gold', 'Diamond', 'Emerald', 'Orichalcum')

    def hub_medalhas(self, body):
        import urllib.parse
        self.section(body, 'COLE O LINK DO SIMULADOR DO SITE (BOTÃO "COMPARTILHAR")')
        e = self.entry(body, cfg.get('medals', ''))
        res = tk.Frame(body, bg=BG); res.pack(fill='x', pady=(6, 2))
        by = {p['n']: p for p in HUB.get('pokemon', [])}
        fix = lambda s: {'critical change': 'Critical Chance', 'critital damage': 'Critical Damage', 'fly spped': 'Fly Speed',
                         'shing fishing rate': 'Shiny Fishing Rate'}.get((s or '').strip().lower(), (s or '').strip())
        def draw(*_):
            for w in res.winfo_children(): w.destroy()
            raw = e.get().strip()
            code = urllib.parse.unquote(raw.split('s=', 1)[1].split('&')[0]) if 's=' in raw else raw
            slots = []
            for x in code.split(','):
                if '.' in x:
                    n, l = x.rsplit('.', 1)
                    if n in by: slots.append((n, max(1, min(6, int(l) if l.isdigit() else 1))))
            if not slots:
                self._txt(res, 'Monte seus emblemas no site (Pokédex → Medalhas (simulador)), clique em "🔗 Compartilhar" e cole aqui. Fica salvo.', 8, MUTED2, bg=BG, padx=4)
                self._hub_relayout(); return
            cfg['medals'] = raw; save_cfg()
            up, down = {}, {}
            card = self._card(res)
            for n, l in slots:
                md = by[n].get('medal') or {}
                b, d = fix(md.get('buff')), fix(md.get('debuff'))
                if b: up[b] = up.get(b, 0) + l
                if d and d != '-' and l < 6: down[d] = down.get(d, 0) + (6 - l)
                self._txt(card, f"{n} ({self.LEVELS[l - 1]})  ▲ {self.MEDAL_PT.get(b, b or '—')}  ▼ {self.MEDAL_PT.get(d, d) if d and d != '-' else '—'}"
                          + ('  (zerada)' if l == 6 and d else ''), 9, pady=(2, 0))
            tk.Frame(card, bg=BG2, height=6).pack()
            tot = self._card(res)
            self._txt(tot, 'RESULTADO (quanto mais ▲/▼, mais forte)', 8, MUTED2, True, pady=(8, 2))
            for k in sorted(set(up) | set(down), key=lambda k: -(up.get(k, 0) - down.get(k, 0))):
                net = up.get(k, 0) - down.get(k, 0)
                sym = ('▲' * min(3, (net + 3) // 4)) if net > 0 else ('▼' * min(3, (-net + 3) // 4)) if net < 0 else '= se anulando'
                self._txt(tot, f"{self.MEDAL_PT.get(k, k)}: {sym}", 9, GREEN if net > 0 else RED if net < 0 else MUTED)
            tk.Frame(tot, bg=BG2, height=8).pack()
            self._hub_relayout()
        e.bind('<KeyRelease>', draw); e.bind('<<Paste>>', lambda ev: self.root.after(50, draw))
        draw()

    # --- 📊 Tabelas ---
    TIER_COLORS = {'T1': '#22c55e', 'T2': '#84cc16', 'T3': '#eab308', 'T4': '#f59e0b', 'T5': '#f97316', 'T6': '#fb7185',
                   'T7': '#a1a1aa', 'Super Rare': '#38bdf8', 'SR': '#38bdf8', 'Ultra Rare': '#a78bfa', 'UR': '#a78bfa',
                   'Legendary': '#f472b6', 'Mythic': '#facc15'}
    TIER_SHORT = {'Super Rare': 'SR', 'Ultra Rare': 'UR', 'Legendary': 'Lend.', 'Mythic': 'Mítico'}

    def _table(self, parent, headers, rows, widths=None, head_colors=None, first_colors=None, note=None, plain=False):
        """tabela de verdade: cabeçalho, linhas zebradas, primeira coluna destacada"""
        wrap = tk.Frame(parent, bg=LINE); wrap.pack(fill='x', pady=(4, 2), padx=2)
        g = tk.Frame(wrap, bg=BG); g.pack(fill='x', padx=1, pady=1)
        for c, h in enumerate(headers):
            col = (head_colors or {}).get(h, MUTED)
            tk.Label(g, text=self.TIER_SHORT.get(h, h), font=(FONT, 8, 'bold'), fg=col, bg=BG3, padx=6, pady=5,
                     anchor='w' if c == 0 and not plain else 'center').grid(row=0, column=c, sticky='nsew')
        for r, row in enumerate(rows, start=1):
            bg = BG2 if r % 2 else BG
            for c, v in enumerate(row):
                if c == 0 and not plain:
                    if type_img(v):
                        cell = tk.Frame(g, bg=bg); cell.grid(row=r, column=0, sticky='nsew')
                        type_chip(cell, v, bg=bg, size=18, fsize=9, color=TXT).pack(anchor='w', padx=8, pady=4)
                    else:
                        tk.Label(g, text=self.TIER_SHORT.get(v, v), font=(FONT, 9, 'bold'), fg=(first_colors or {}).get(v, TXT), bg=bg,
                                 padx=8, pady=4, anchor='w').grid(row=r, column=0, sticky='nsew')
                else:
                    empty = v in ('', None, '—')
                    tk.Label(g, text='—' if empty else v, font=(FONT, 9), fg=MUTED2 if empty else '#e4e4e7', bg=bg, padx=6, pady=4,
                             justify='center', wraplength=(widths or {}).get(c, 0)).grid(row=r, column=c, sticky='nsew')
        for c in range(len(headers)): g.grid_columnconfigure(c, weight=1)
        if note:
            tk.Label(parent, text=note, font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w', justify='left', wraplength=440).pack(fill='x', padx=4, pady=(4, 0))

    def hub_tabelas(self, body):
        bar = tk.Frame(body, bg=BG); bar.pack(fill='x', pady=(8, 4))
        out = tk.Frame(body, bg=BG); out.pack(fill='x')
        TC = self.TIER_COLORS
        def show(k):
            cfg['hub_table'] = k; save_cfg()
            for w in out.winfo_children(): w.destroy()
            if k == 'boost':
                rows = [[b['type'], b['stone'].replace(' stone', '').title(), ', '.join(i.split(' (')[0] for i in b['items'][:3])]
                        for b in HUB.get('boost', [])]
                self._table(out, ['Tipo', 'Stone', 'Itens de boost'], rows, widths={2: 230},
                            note='Fragmento = "<tipo> fragment". Veja a lista completa no site.')
            elif k == 'star':
                st = HUB.get('star', {})
                pct = dict(re.findall(r'-\s*(Tier \d|Super Rare|Ultra Rare|Legendary):\s*(\d+)%', st.get('note', '')))
                name = lambda t: {'T3': 'Tier 3', 'T2': 'Tier 2', 'T1': 'Tier 1'}.get(t, t)
                rows = [[t['tier'], (pct.get(name(t['tier'])) or '?') + '%'] +
                        [f"{c.get('dd', 0):g} DD\n{c.get('kk', 0):g}kk" for c in t['costs']] for t in st.get('tiers', [])]
                self._table(out, ['Tier', 'Dano/★', '1★', '2★', '3★', '4★', '5★'], rows, first_colors=TC,
                            note='Custo de cada estrela com 100% de sucesso. Dano/★ = quanto o ataque sobe por estrela.')
            elif k == 'runes':
                rows = []
                for r in HUB.get('runes', {}).get('stats', []):
                    rows.append([r['name']] + [(f"{x['bonus']}\n{x['points']} pts" if x.get('bonus') else (f"{x['points']} pts" if x.get('points') else ''))
                                               for x in r['levels']])
                self._table(out, ['Atributo', 'Nv 1', 'Nv 2', 'Nv 3', 'Nv 4', 'Nv 5'], rows)
            elif k == 'shiny':
                cols = HUB.get('shinyRate', {}).get('columns', [])
                tiers = [t['tier'] for t in (cols[0]['tiers'] if cols else [])]
                rows = [[f"{c['rate']}"] + [(f"{t['value']:g}%" if t.get('value') is not None else '') for t in c['tiers']] for c in cols]
                self._table(out, ['Rate'] + tiers, rows, head_colors=TC,
                            note='Chance de vir shiny por tier em cada Shiny Rate.')
                br = HUB.get('brokes', {}).get('max', [])
                if br:
                    tk.Label(out, text='MAX BROKE', font=(FONT, 8, 'bold'), fg=MUTED2, bg=BG, anchor='w').pack(fill='x', padx=4, pady=(10, 0))
                    half = (len(br) + 1) // 2
                    for part in (br[:half], br[half:]):
                        self._table(out, [b['tier'] for b in part], [[b['max'] for b in part]], head_colors=TC, plain=True)
            for kk, l in labels.items(): l.config(bg=ORANGE if kk == k else BG3)
            self._hub_relayout()
        labels = {}
        for k, name in (('boost', 'Boost'), ('star', 'Star'), ('runes', 'Runas'), ('shiny', 'Shiny Rate / Broke')):
            l = tk.Label(bar, text=name, font=(FONT, 8, 'bold'), bg=BG3, fg=TXT, padx=8, pady=4, cursor='hand2')
            l.pack(side='left', padx=(2, 4)); l._nodrag = True
            l.bind('<Button-1>', lambda e, k=k: show(k)); labels[k] = l
        show(cfg.get('hub_table', 'boost'))

    # --- 🎬 Vídeos ---
    def hub_videos(self, body):
        def draw(q, res):
            s = norm(q)
            if len(s) < 3:
                self._txt(res, f'{len(VIDEOS)} vídeos com as falas transcritas. Pergunte algo (ex.: como pegar shiny, melhor hunt 200).', 8, MUTED2, bg=BG, padx=4)
                return
            words = [w for w in s.split() if len(w) > 2 and w not in ('como', 'qual', 'para', 'que', 'melhor', 'onde', 'uma', 'com')] or s.split()
            scored = []
            for v in VIDEOS:
                tt = norm(v['title'])
                best, bt, bx = 0, 0, ''
                for t, txt in v.get('segs', []):
                    n = norm(txt); sc = sum(1 for w in words if w in n)
                    if sc > best: best, bt, bx = sc, t, txt
                sc = best + 2 * sum(1 for w in words if w in tt)
                if sc: scored.append((sc, v, bt, bx))
            scored.sort(key=lambda x: -x[0])
            if not scored: self._txt(res, 'Nada encontrado nas falas.', 9, MUTED, bg=BG, padx=4); return
            for sc, v, t, txt in scored[:5]:
                card = self._card(res)
                top = tk.Frame(card, bg=BG2); top.pack(fill='x', padx=12, pady=(8, 2))
                tk.Label(top, text=v['title'][:58], font=(FONT, 9, 'bold'), fg=TXT, bg=BG2, anchor='w').pack(side='left')
                self._link(top, f'{int(t) // 60}:{int(t) % 60:02d} ▸', f"https://www.youtube.com/watch?v={v['id']}&t={int(t)}s").pack(side='right')
                self._txt(card, f"{v['ch']} — “{txt[:160]}…”", 8, MUTED, pady=(0, 8))
        e = self._search_box(body, 'PERGUNTE AOS VÍDEOS', lambda q, r: None)
        e.bind('<KeyRelease>', lambda ev: None)
        res = e.master.master.winfo_children()[-1]
        def go(*_):
            for w in res.winfo_children(): w.destroy()
            draw(e.get(), res); self._hub_relayout()
        e.bind('<Return>', go)
        tk.Label(body, text='Aperte Enter para buscar.', font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w').pack(fill='x', padx=4)
        go()

    def close_modal(self):
        self.recording = None
        if self.modal:
            try: self.modal.win.destroy()
            except Exception: pass
            self.modal = None
        self.open_until = time.time() + 2

    # ---------- loop ----------
    def tick(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'show': self.show_item(*payload)
                elif kind == 'novo': self.show_novo(payload[0], payload[1])
                elif kind == 'nada':
                    for w in self.rows.winfo_children(): w.destroy()
                    self.thumb.config(image=''); self.thumb.image = None
                    self.l_name.config(text='Nada encontrado aqui')
                    self.set_pill(self.l_cat, 'TENTE DE NOVO', 'search', BG3)
                    self.add_row('search', MUTED, 'Deixe o tooltip do item aberto e aperte a tecla de novo.')
                    self.b_reg.pack_forget(); self.w.set_border(BG3); self.update_foot(); self.open_panel()
                elif kind == 'recorded':
                    self.recording = None
                    cfg['hotkey'] = payload
                    if cfg['mode'] == 'auto': cfg['mode'] = 'ambos'
                    save_cfg()
                    try: self._mode_var.set(cfg['mode'])
                    except Exception: pass
                    try:
                        l_key, b_rec = self._cfg_widgets
                        l_key.config(text=pretty_key(payload), fg=SKY)
                        i2 = ImageTk.PhotoImage(ui.pill('  Gravar tecla  ', 'pencil', INDIGO, h=32, fsize=10))
                        b_rec.config(image=i2); b_rec.image = i2
                    except Exception: pass
                    self.update_foot()
                elif kind == 'update':
                    self.set_pill(self.b_update, f'v{payload}', 'plus', INDIGO, h=22)
                    self.b_update.pack(side='right', padx=(0, 6)); self.w.relayout()
                elif kind == 'quit':
                    self.root.destroy(); return
        except queue.Empty: pass
        self._tk_n = getattr(self, '_tk_n', 0) + 1
        if self._tk_n % 6 == 0:
            self._timer_check()
            if self.modal: self._timer_draw()
        if self.panel.winfo_manager() and time.time() > self.open_until and not self.modal:
            self.close_panel()
        self.root.after(80, self.tick)

if __name__ == '__main__':
    log('início', VERSION, 'itens:', len(DB))
    App().root.mainloop()
