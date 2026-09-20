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
VERSION = '2.2.0'
SITE = 'https://pkaguide.vercel.app'
DB_URL = SITE + '/overlay/items_db.json'
VERSION_URL = SITE + '/overlay/version.json'
TASKS_URL = SITE + '/overlay/tasks_db.json'

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
DEFAULTS = {'mode': 'auto', 'hotkey': 'f4', 'show_s': 8}
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
    def __init__(self, master=None, width=CARD_W, border=LINE, alpha=0.97):
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

        self.b_tasks = tk.Label(head, text='📋', font=(FONT, 11), fg=MUTED2, bg=BG, padx=5, cursor='hand2')
        self.b_tasks.pack(side='right'); self.b_tasks._nodrag = True
        self.b_tasks.bind('<Button-1>', lambda e: self.open_tasks())
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

    def add_row(self, icon_name, color, title, sub=None):
        r = tk.Frame(self.rows, bg=BG); r.pack(fill='x', pady=3)
        ico_label(r, icon_name, 17, color).pack(side='left', padx=(5, 9), anchor='n', pady=1)
        tx = tk.Frame(r, bg=BG); tx.pack(side='left', fill='x', expand=True)
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
            self.add_row('sparkle', GREEN, f"{t['type']} · Talento #{t['n']} · {t['qty']} un.", t['buff'][:95])
        if d.get('boost'): self.add_row('flame', YELLOW, 'Boost: ' + ', '.join(sorted(set(d['boost']))))
        if d.get('stone'): self.add_row('gem', SKY, 'Stone de boost: ' + ', '.join(d['stone']))
        if d.get('fragment'): self.add_row('hex', SKY, 'Fragmento de boost: ' + ', '.join(d['fragment']))
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
        m = Round(self.root, width=width, border=color, alpha=0.99); self.modal = m
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
                    lk = tk.Label(top, text='🗺 onde fica', font=(FONT, 8, 'bold'), fg=SKY, bg=BG2, cursor='hand2')
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
        if self.panel.winfo_manager() and time.time() > self.open_until and not self.modal:
            self.close_panel()
        self.root.after(80, self.tick)

if __name__ == '__main__':
    log('início', VERSION, 'itens:', len(DB))
    App().root.mainloop()
