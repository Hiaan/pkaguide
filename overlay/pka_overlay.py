# -*- coding: utf-8 -*-
"""
PKA GUIDE Overlay: passa o mouse em um item no jogo e o painel mostra para que ele serve.
- Lê o tooltip por captura de TELA (pixel) + OCR. Não lê memória nem toca no processo do jogo.
- Tenta ler algumas vezes enquanto o mouse fica parado (o tooltip do jogo demora a aparecer).
- Item que não está na base abre o painel como "NÃO CADASTRADO" com botão para cadastrar.
- Cadastros ficam em custom_items.json e podem ser exportados para publicar no site.
"""
import json, os, re, sys, threading, time, queue, difflib, unicodedata, subprocess, shutil, tempfile, traceback
import tkinter as tk
import numpy as np
import mss
from PIL import Image, ImageTk
from pynput import mouse, keyboard

APP_NAME = 'PKA GUIDE'
VERSION = '1.2.0'
SITE = 'https://pkaguide.vercel.app'
DB_URL = SITE + '/overlay/items_db.json'
VERSION_URL = SITE + '/overlay/version.json'

# DPI: sem isso, em telas com escala != 100% a área capturada sai deslocada
if os.name == 'nt':
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

DEFAULTS = {'mode': 'auto', 'hotkey': 'f4', 'show_s': 8}
try:
    cfg = dict(DEFAULTS, **json.load(open(CONFIG_FILE, encoding='utf-8')))
except Exception:
    cfg = dict(DEFAULTS)

def save_cfg():
    try: json.dump(cfg, open(CONFIG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    except Exception as e: log('save_cfg', e)

def log(*a):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')
    except Exception: pass

catalog = json.load(open(CATALOG_FILE, encoding='utf-8')) if os.path.exists(CATALOG_FILE) else {}
custom = json.load(open(CUSTOM_FILE, encoding='utf-8')) if os.path.exists(CUSTOM_FILE) else {}
unknown = json.load(open(UNKNOWN_FILE, encoding='utf-8')) if os.path.exists(UNKNOWN_FILE) else {}

REGION = (-360, -170, 380, 170)   # área lida ao redor do cursor
TRIES = (0.35, 0.9, 1.7)          # o tooltip do jogo demora: tenta 3 vezes com o mouse parado
ICON = 34
SHOW_S = 8

# ---------- identidade visual (mesma do site) ----------
BG, BG2, BG3, LINE, TXT, MUTED, MUTED2 = '#18181b', '#27272a', '#3f3f46', '#3f3f46', '#fafafa', '#a1a1aa', '#71717a'
ORANGE, YELLOW, SKY, INDIGO, GREEN, RED = '#f97316', '#eab308', '#0ea5e9', '#4f46e5', '#22c55e', '#ef4444'
FONT = 'Inter' if os.name == 'nt' else 'Segoe UI'
CATS = {
    'talento': (GREEN, '#052e16', 'USAR  ·  VENDER PARA PLAYER', 'Usado em PokeTalent'),
    'boost': (YELLOW, '#422006', 'BOOST', 'Item de boost'),
    'material': (SKY, '#082f49', 'MATERIAL', 'Stone / fragmento de boost'),
    'npc': ('#a1a1aa', BG2, 'SÓ NPC', 'Sem uso conhecido: vender para NPC'),
    'desconhecido': ('#a1a1aa', BG2, 'SEM REGISTRO', 'Não está na base do site'),
}
CAT_OPTS = [('talento', 'Usar / vender para player', GREEN), ('boost', 'Boost', YELLOW),
            ('material', 'Material (stone/fragmento)', SKY), ('npc', 'Só vender para NPC', '#a1a1aa')]

# ---------- base de itens ----------
def load_db():
    for p in (os.path.join(DATA_DIR, 'items_db.json'), os.path.join(BUNDLE, 'items_db.json')):
        if os.path.exists(p):
            try: return json.load(open(p, encoding='utf-8'))
            except Exception: pass
    return {}

def merge_custom():
    """junta os cadastros do usuário na base (aliases viram cópia do item original)"""
    for k, v in custom.items():
        if v.get('alias') and v['alias'] in DB:
            d = dict(DB[v['alias']]); d['name'] = k; d['alias_de'] = v['alias']
            DB[k] = d
        else:
            DB[k] = {'name': k, 'cat': v.get('cat', 'npc'), 'talents': [], 'boost': [], 'drops': [],
                     'stone': [], 'fragment': [], 'nota': v.get('note', ''), 'custom': True}

DB = load_db()
merge_custom()
NAMES = list(DB.keys())

def refresh_db():
    global DB, NAMES
    try:
        import requests
        r = requests.get(DB_URL, timeout=8); r.raise_for_status()
        d = r.json()
        if isinstance(d, dict) and len(d) > 100:
            json.dump(d, open(os.path.join(DATA_DIR, 'items_db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            DB = d; merge_custom(); NAMES = list(DB.keys())
            return True, f'{len(DB)} itens'
    except Exception as e:
        log('refresh_db', e)
        return False, f'{len(DB)} itens (offline)'
    return False, f'{len(DB)} itens'

def check_update():
    try:
        import requests
        v = requests.get(VERSION_URL, timeout=8).json()
        if tuple(map(int, v['version'].split('.'))) > tuple(map(int, VERSION.split('.'))):
            return v['version'], v['url']
    except Exception as e: log('check_update', e)
    return None, None

def apply_update(url):
    import requests
    new = os.path.join(tempfile.gettempdir(), 'PKA_GUIDE_new.exe')
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(new, 'wb') as f:
            for chunk in r.iter_content(1 << 16): f.write(chunk)
    bat = os.path.join(tempfile.gettempdir(), 'pka_update.bat')
    open(bat, 'w').write(f'@echo off\r\ntimeout /t 2 /nobreak >nul\r\ncopy /y "{new}" "{EXE}" >nul\r\nstart "" "{EXE}"\r\ndel "%~f0"\r\n')
    subprocess.Popen(['cmd', '/c', bat], creationflags=0x08000000)
    os._exit(0)

# ---------- instalação ----------
def ensure_installed():
    if not FROZEN: return
    target = os.path.join(INSTALL_DIR, APP_NAME + '.exe')
    if os.path.normcase(EXE) == os.path.normcase(target): return
    try:
        shutil.copy2(EXE, target)
        ps = f'''
$W = New-Object -ComObject WScript.Shell
foreach ($d in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs'))) {{
  $s = $W.CreateShortcut((Join-Path $d '{APP_NAME}.lnk')); $s.TargetPath = '{target}'; $s.WorkingDirectory = '{INSTALL_DIR}'; $s.IconLocation = '{target}'; $s.Save()
}}'''
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, creationflags=0x08000000)
        subprocess.Popen([target], creationflags=0x00000008)
        os._exit(0)
    except Exception as e:
        log('instalação', e)

# ---------- texto ----------
IGNORE = ('price', 'segure', 'shift', 'coleta', 'depot', 'stash', 'trainer', 'ultra bag', 'great bag', 'pokemon', 'loot')

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r"[^a-z0-9' ]+", ' ', s).strip()

def clean_line(text):
    """tira quantidade e lixo do começo/fim; devolve '' se não parecer nome de item"""
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
    return None, 0, singulars(t)[-1]   # não achou: devolve o nome lido (singular) para cadastro

# ---------- teclas ----------
MOD_NAMES = {'ctrl': ('ctrl', 'ctrl_l', 'ctrl_r'), 'alt': ('alt', 'alt_l', 'alt_r', 'alt_gr'), 'shift': ('shift', 'shift_l', 'shift_r')}

def base_key(key):
    """nome simples da tecla: 'f4', 'a', 'space'…"""
    try:
        if isinstance(key, keyboard.KeyCode):
            if key.char: return key.char.lower()
            return f'vk{key.vk}'
        n = str(key).replace('Key.', '')
        for m, alts in MOD_NAMES.items():
            if n in alts: return m
        return n
    except Exception:
        return ''

def combo_str(key, held):
    parts = [m for m in ('ctrl', 'alt', 'shift') if m in held]
    b = base_key(key)
    if b in ('ctrl', 'alt', 'shift'): return ''
    return '+'.join(parts + [b]) if b else ''

def pretty_key(s):
    return ' + '.join(w.upper() for w in s.split('+')) if s else '—'

# ---------- OCR ----------
_ocr = None
def get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr

def read_tooltip(x, y):
    with mss.MSS() as sct:
        mon = sct.monitors[0]
        box = {'left': max(mon['left'], x + REGION[0]), 'top': max(mon['top'], y + REGION[1]),
               'width': REGION[2] - REGION[0], 'height': REGION[3] - REGION[1]}
        shot = sct.grab(box)
        img = Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')
        ish = sct.grab({'left': x - ICON // 2, 'top': y - ICON // 2, 'width': ICON, 'height': ICON})
        icon = Image.frombytes('RGB', ish.size, ish.bgra, 'raw', 'BGRX')
    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    res, _ = get_ocr()(np.array(big))
    return [r[1] for r in (res or []) if float(r[2]) > 0.5], icon

# ---------- app ----------
class App:
    def __init__(self):
        self.enabled = True
        self.pos = (0, 0); self.last_move = time.time()
        self.q = queue.Queue(); self.photo = None; self.logo = None
        self.update_url = None; self.pending = None; self.modal = None

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.97)
        self.root.configure(bg=ORANGE)
        try: self.root.iconbitmap(os.path.join(BUNDLE, 'logo.ico'))
        except Exception: pass
        outer = tk.Frame(self.root, bg=BG); outer.pack(padx=1, pady=1)

        head = tk.Frame(outer, bg=BG2, cursor='fleur'); head.pack(fill='x')
        try:
            self.logo = ImageTk.PhotoImage(Image.open(os.path.join(BUNDLE, 'logo_small.png')).convert('RGBA').resize((28, 28), Image.LANCZOS))
            tk.Label(head, image=self.logo, bg=BG2).pack(side='left', padx=(10, 6), pady=5)
        except Exception:
            tk.Label(head, text='◉', font=(FONT, 12, 'bold'), fg=ORANGE, bg=BG2).pack(side='left', padx=(10, 4), pady=6)
        ttl = tk.Frame(head, bg=BG2); ttl.pack(side='left', pady=4)
        tk.Label(ttl, text='PKA ', font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left')
        tk.Label(ttl, text='GUIDE', font=(FONT, 10, 'bold'), fg=SKY, bg=BG2).pack(side='left')
        self.b_close = tk.Label(head, text='✕', font=(FONT, 10, 'bold'), fg=MUTED, bg=BG2, padx=10, cursor='hand2')
        self.b_close.pack(side='right', pady=6)
        self.b_close.bind('<Button-1>', lambda e: self.q.put(('quit', None)))
        self.b_close.bind('<Enter>', lambda e: self.b_close.config(fg=RED))
        self.b_close.bind('<Leave>', lambda e: self.b_close.config(fg=MUTED))
        self.b_toggle = tk.Label(head, text='', font=(FONT, 9, 'bold'), fg='white', bg=ORANGE, padx=10, pady=2, cursor='hand2')
        self.b_toggle.pack(side='right', padx=(0, 6), pady=6)
        self.b_toggle.bind('<Button-1>', lambda e: self.toggle())
        self.b_cfg = tk.Label(head, text='⚙', font=(FONT, 11), fg=MUTED, bg=BG2, padx=8, cursor='hand2')
        self.b_cfg.pack(side='right', pady=6)
        self.b_cfg.bind('<Button-1>', lambda e: self.open_config())
        self.b_cfg.bind('<Enter>', lambda e: self.b_cfg.config(fg=TXT))
        self.b_cfg.bind('<Leave>', lambda e: self.b_cfg.config(fg=MUTED))
        self.b_update = tk.Label(head, text='', font=(FONT, 9, 'bold'), fg='white', bg=INDIGO, padx=10, pady=2, cursor='hand2')
        self.b_update.bind('<Button-1>', lambda e: self.do_update())
        self.buttons = (self.b_close, self.b_toggle, self.b_update, self.b_cfg)
        self.bind_drag(head)

        body = tk.Frame(outer, bg=BG, width=380); body.pack_propagate(False)
        self.body = body; self.open_until = 0
        top = tk.Frame(body, bg=BG); top.pack(fill='x', padx=12, pady=(10, 4))
        self.icon_box = tk.Label(top, bg=BG2, width=68, height=68, bd=0); self.icon_box.pack(side='left')
        right = tk.Frame(top, bg=BG); right.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.l_name = tk.Label(right, text='', font=(FONT, 12, 'bold'), fg=TXT, bg=BG, anchor='w', justify='left', wraplength=265); self.l_name.pack(fill='x')
        self.l_cat = tk.Label(right, text='', font=(FONT, 8, 'bold'), fg='white', bg=BG2, anchor='w', padx=8, pady=3); self.l_cat.pack(anchor='w', pady=(6, 0))
        tk.Frame(body, bg=LINE, height=1).pack(fill='x', padx=12, pady=(8, 6))
        self.l_info = tk.Label(body, text='', font=(FONT, 9), fg='#e4e4e7', bg=BG, justify='left', anchor='nw', wraplength=356); self.l_info.pack(fill='x', padx=12, pady=(0, 8))
        self.b_reg = tk.Label(body, text='➕  Cadastrar este item', font=(FONT, 9, 'bold'), fg='white', bg=INDIGO, pady=6, cursor='hand2')
        self.b_reg.bind('<Button-1>', lambda e: self.open_modal())
        self.l_foot = tk.Label(body, text='', font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w'); self.l_foot.pack(fill='x', padx=12, pady=(4, 8))
        self.status_text = f'v{VERSION} · carregando…'

        self.set_toggle()
        self.root.geometry(f'+{self.root.winfo_screenwidth() - 420}+12')
        self.held = set(); self.recording = None
        mouse.Listener(on_move=self.on_move).start()
        keyboard.Listener(on_press=self.on_key_down, on_release=self.on_key_up).start()
        threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=self.startup, daemon=True).start()
        self.root.after(80, self.tick)

    def bind_drag(self, w):
        if w in self.buttons: return
        w.bind('<ButtonPress-1>', self.drag_start); w.bind('<B1-Motion>', self.drag)
        for c in w.winfo_children(): self.bind_drag(c)

    # ----- inicialização -----
    def startup(self):
        ok, msg = refresh_db()
        self.status_text = f'v{VERSION} · {msg}'
        get_ocr()
        self.status_text = f'v{VERSION} · {msg} · pronto'
        newv, url = check_update()
        if newv:
            self.update_url = url; self.q.put(('update', newv))

    def do_update(self):
        if not self.update_url: return
        if not FROZEN: self.b_update.config(text='rode o build novo'); return
        self.b_update.config(text='baixando…', bg=BG3)
        threading.Thread(target=lambda: apply_update(self.update_url), daemon=True).start()

    # ----- UI -----
    def fit(self):
        self.root.update_idletasks()
        self.body.config(height=max(150, sum(w.winfo_reqheight() for w in self.body.winfo_children() if w.winfo_manager()) + 26))

    def open_panel(self):
        if not self.body.winfo_manager(): self.body.pack(fill='both')
        self.fit(); self.open_until = time.time() + cfg['show_s']

    def close_panel(self):
        if self.modal: return
        if self.body.winfo_manager(): self.body.pack_forget()
        self.root.update_idletasks()

    def set_toggle(self):
        self.b_toggle.config(text='●  LIGADO' if self.enabled else '○  DESLIGADO', bg=ORANGE if self.enabled else BG3)

    def toggle(self):
        self.enabled = not self.enabled; self.set_toggle()
        if not self.enabled: self.close_panel()

    def on_key_down(self, key):
        b = base_key(key)
        if b in ('ctrl', 'alt', 'shift'): self.held.add(b); return
        combo = combo_str(key, self.held)
        if not combo: return
        if self.recording:                       # gravando nova tecla na tela de config
            self.q.put(('recorded', combo)); return
        if cfg['mode'] == 'hotkey' and self.enabled and combo == cfg['hotkey']:
            threading.Thread(target=self.capture_now, daemon=True).start()

    def on_key_up(self, key):
        self.held.discard(base_key(key))

    def capture_now(self):
        """leitura imediata na posição atual do mouse (modo tecla de atalho)"""
        try:
            x, y = self.pos
            lines, icon = read_tooltip(x, y)
            best = None
            for line in lines:
                name, score, read = match_name(line)
                if name: best = ('ok', name, icon, score); break
                if read and not best: best = ('novo', read, icon, 0)
            if not best:
                self.q.put(('nada', None)); return
            if best[0] == 'ok':
                self.save_catalog(best[1], best[2], best[3]); self.q.put(('show', best[1:]))
            else:
                self.save_unknown(best[1], best[2]); self.q.put(('novo', best[1:]))
        except Exception as e:
            log('capture_now', e)

    def drag_start(self, e): self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()
    def drag(self, e): self.root.geometry(f'+{e.x_root - self._dx}+{e.y_root - self._dy}')
    def on_move(self, x, y): self.pos = (x, y); self.last_move = time.time()

    # ----- leitura -----
    def worker(self):
        last_pos, tries, done = None, 0, False
        while True:
            time.sleep(0.05)
            try:
                if not self.enabled or cfg['mode'] != 'auto': continue
                if self.pos != last_pos:
                    last_pos, tries, done = self.pos, 0, False
                if done or tries >= len(TRIES): continue
                if time.time() - self.last_move < TRIES[tries]: continue
                tries += 1
                x, y = self.pos
                try:
                    rx, ry = self.root.winfo_x(), self.root.winfo_y()
                    rw, rh = self.root.winfo_width(), self.root.winfo_height()
                    if rx <= x <= rx + rw and ry <= y <= ry + rh: done = True; continue
                except Exception: pass
                lines, icon = read_tooltip(x, y)
                best = None
                for line in lines:
                    name, score, read = match_name(line)
                    if name:
                        best = ('ok', name, icon, score); break
                    if read and not best: best = ('novo', read, icon, 0)
                if best and best[0] == 'ok':
                    done = True
                    self.save_catalog(best[1], best[2], best[3])
                    self.q.put(('show', best[1:]))
                elif best and tries >= len(TRIES):
                    done = True
                    self.save_unknown(best[1], icon)
                    self.q.put(('novo', best[1:]))
            except Exception as e:
                log('worker', e, traceback.format_exc()[:400])

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

    def describe(self, name):
        d = DB[name]; color, dark, tag, desc = CATS.get(d.get('cat', 'desconhecido'), CATS['desconhecido'])
        info = []
        if d.get('alias_de'): info.append(f"🔗  Mesmo item que: {d['alias_de'].title()}")
        for t in d.get('talents', []): info.append(f"🧠  {t['type']} · Talento #{t['n']} · {t['qty']} un.\n      {t['buff'][:90]}")
        if d.get('boost'): info.append('🔥  Boost: ' + ', '.join(sorted(set(d['boost']))))
        if d.get('stone'): info.append('💎  Stone de boost: ' + ', '.join(d['stone']))
        if d.get('fragment'): info.append('🧩  Fragmento de boost: ' + ', '.join(d['fragment']))
        if d.get('drops'):
            dr = d['drops']; info.append(f"🎯  Drop de: {', '.join(dr[:4])}{'  +' + str(len(dr) - 4) if len(dr) > 4 else ''}")
        if d.get('nota'): info.append('📝  ' + d['nota'])
        if d.get('custom'): info.append('✏️  Cadastrado por você')
        if not info: info.append(desc)
        return color, dark, tag, '\n'.join(info)

    # ----- cadastro -----
    def open_modal(self):
        if self.modal or not self.pending: return
        name, icon = self.pending
        self.open_until = time.time() + 999
        m = tk.Toplevel(self.root); self.modal = m
        m.title('Cadastrar item'); m.configure(bg=ORANGE); m.attributes('-topmost', True); m.overrideredirect(True)
        f = tk.Frame(m, bg=BG); f.pack(padx=1, pady=1)
        h = tk.Frame(f, bg=BG2, cursor='fleur'); h.pack(fill='x')
        tk.Label(h, text='➕  Cadastrar item', font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left', padx=12, pady=8)
        cl = tk.Label(h, text='✕', font=(FONT, 10, 'bold'), fg=MUTED, bg=BG2, padx=10, cursor='hand2'); cl.pack(side='right')
        cl.bind('<Button-1>', lambda e: self.close_modal())
        h.bind('<ButtonPress-1>', lambda e: setattr(m, '_d', (e.x_root - m.winfo_x(), e.y_root - m.winfo_y())))
        h.bind('<B1-Motion>', lambda e: m.geometry(f'+{e.x_root - m._d[0]}+{e.y_root - m._d[1]}'))

        c = tk.Frame(f, bg=BG); c.pack(fill='both', padx=16, pady=12)
        tk.Label(c, text='NOME DO ITEM (como aparece no jogo)', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        e_name = tk.Entry(c, font=(FONT, 11), bg=BG2, fg=TXT, insertbackground=TXT, relief='flat', bd=8)
        e_name.insert(0, name.title()); e_name.pack(fill='x', pady=(4, 12))

        tk.Label(c, text='PARA QUE SERVE?', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        var = tk.StringVar(value='npc')
        opts = tk.Frame(c, bg=BG); opts.pack(fill='x', pady=(6, 12))
        for key, label, color in CAT_OPTS:
            r = tk.Radiobutton(opts, text='  ' + label, value=key, variable=var, font=(FONT, 9), fg=TXT, bg=BG,
                               selectcolor=BG3, activebackground=BG, activeforeground=color, anchor='w', bd=0, highlightthickness=0)
            r.pack(fill='x')

        tk.Label(c, text='OBSERVAÇÃO (opcional)', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        e_note = tk.Entry(c, font=(FONT, 10), bg=BG2, fg=TXT, insertbackground=TXT, relief='flat', bd=7)
        e_note.pack(fill='x', pady=(4, 12))

        tk.Label(c, text='OU É O MESMO QUE UM ITEM JÁ CADASTRADO', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        e_alias = tk.Entry(c, font=(FONT, 10), bg=BG2, fg=TXT, insertbackground=TXT, relief='flat', bd=7)
        e_alias.pack(fill='x', pady=(4, 2))
        lb = tk.Listbox(c, height=4, font=(FONT, 9), bg=BG2, fg=TXT, relief='flat', bd=0, highlightthickness=0, selectbackground=INDIGO)
        def filt(*_):
            q = norm(e_alias.get())
            lb.delete(0, 'end')
            if len(q) >= 2:
                for n in [n for n in NAMES if q in n][:20]: lb.insert('end', n)
                lb.pack(fill='x', pady=(0, 10))
            else:
                lb.pack_forget()
        e_alias.bind('<KeyRelease>', filt)
        lb.bind('<<ListboxSelect>>', lambda e: (e_alias.delete(0, 'end'), e_alias.insert(0, lb.get(lb.curselection()[0])), lb.pack_forget()) if lb.curselection() else None)

        btns = tk.Frame(c, bg=BG); btns.pack(fill='x', pady=(8, 0))
        b_ok = tk.Label(btns, text='Salvar', font=(FONT, 10, 'bold'), fg='white', bg=GREEN, padx=22, pady=7, cursor='hand2')
        b_ok.pack(side='right'); b_ok.bind('<Button-1>', lambda e: self.save_custom(e_name.get(), var.get(), e_note.get(), e_alias.get(), icon))
        b_no = tk.Label(btns, text='Cancelar', font=(FONT, 10), fg=MUTED, bg=BG3, padx=18, pady=7, cursor='hand2')
        b_no.pack(side='right', padx=(0, 8)); b_no.bind('<Button-1>', lambda e: self.close_modal())
        tk.Label(btns, text=f'{len(custom)} cadastrados', font=(FONT, 8), fg=MUTED2, bg=BG).pack(side='left')

        m.update_idletasks()
        m.geometry(f'+{max(20, self.root.winfo_x() - m.winfo_width() - 14)}+{self.root.winfo_y() + 40}')
        e_name.focus_set()

    def open_config(self):
        if self.modal: self.close_modal()
        self.open_until = time.time() + 999
        m = tk.Toplevel(self.root); self.modal = m
        m.configure(bg=ORANGE); m.attributes('-topmost', True); m.overrideredirect(True)
        f = tk.Frame(m, bg=BG); f.pack(padx=1, pady=1)
        h = tk.Frame(f, bg=BG2, cursor='fleur'); h.pack(fill='x')
        tk.Label(h, text='⚙  Configurações', font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left', padx=12, pady=8)
        cl = tk.Label(h, text='✕', font=(FONT, 10, 'bold'), fg=MUTED, bg=BG2, padx=10, cursor='hand2'); cl.pack(side='right')
        cl.bind('<Button-1>', lambda e: self.close_modal())
        h.bind('<ButtonPress-1>', lambda e: setattr(m, '_d', (e.x_root - m.winfo_x(), e.y_root - m.winfo_y())))
        h.bind('<B1-Motion>', lambda e: m.geometry(f'+{e.x_root - m._d[0]}+{e.y_root - m._d[1]}'))

        c = tk.Frame(f, bg=BG, width=400); c.pack(fill='both', padx=16, pady=14)
        tk.Label(c, text='QUANDO LER O ITEM', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        mode = tk.StringVar(value=cfg['mode'])
        box = tk.Frame(c, bg=BG); box.pack(fill='x', pady=(6, 4))
        for key, title, sub in (('auto', 'Automático', 'lê sozinho quando você para o mouse sobre o item'),
                                ('hotkey', 'Só quando eu apertar a tecla', 'não fica lendo a tela o tempo todo')):
            row = tk.Frame(box, bg=BG); row.pack(fill='x', pady=2)
            tk.Radiobutton(row, text='  ' + title, value=key, variable=mode, font=(FONT, 10, 'bold'), fg=TXT, bg=BG,
                           selectcolor=BG3, activebackground=BG, activeforeground=ORANGE, anchor='w', bd=0,
                           highlightthickness=0, command=lambda: apply_mode()).pack(fill='x')
            tk.Label(row, text='      ' + sub, font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w').pack(fill='x')

        hk = tk.Frame(c, bg=BG2); hk.pack(fill='x', pady=(10, 4))
        tk.Label(hk, text='TECLA DE ATALHO', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG2, anchor='w').pack(fill='x', padx=12, pady=(10, 2))
        line = tk.Frame(hk, bg=BG2); line.pack(fill='x', padx=12, pady=(0, 12))
        l_key = tk.Label(line, text=pretty_key(cfg['hotkey']), font=(FONT, 13, 'bold'), fg=SKY, bg=BG3, padx=18, pady=6)
        l_key.pack(side='left')
        b_rec = tk.Label(line, text='Gravar tecla', font=(FONT, 9, 'bold'), fg='white', bg=INDIGO, padx=14, pady=7, cursor='hand2')
        b_rec.pack(side='left', padx=8)
        hint = tk.Label(hk, text='Aperte a tecla que quiser (ex.: F4, Ctrl+Q). Escolha uma que o jogo não use.',
                        font=(FONT, 8), fg=MUTED2, bg=BG2, anchor='w', wraplength=360, justify='left')
        hint.pack(fill='x', padx=12, pady=(0, 10))

        def start_rec(_=None):
            self.recording = True
            b_rec.config(text='Aperte agora…', bg=ORANGE)
            l_key.config(text='…', fg=ORANGE)
        b_rec.bind('<Button-1>', start_rec)
        self._cfg_widgets = (l_key, b_rec)

        def apply_mode():
            cfg['mode'] = mode.get(); save_cfg(); self.update_foot()
            hk.pack_configure() if cfg['mode'] == 'hotkey' else None
        tk.Frame(c, bg=LINE, height=1).pack(fill='x', pady=10)
        tk.Label(c, text='TEMPO QUE O PAINEL FICA ABERTO', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        srow = tk.Frame(c, bg=BG); srow.pack(fill='x', pady=(6, 2))
        sv = tk.IntVar(value=cfg['show_s'])
        def set_s(v):
            cfg['show_s'] = int(float(v)); save_cfg()
        tk.Scale(srow, from_=3, to=30, orient='horizontal', variable=sv, command=set_s, bg=BG, fg=TXT, troughcolor=BG3,
                 highlightthickness=0, bd=0, sliderrelief='flat', activebackground=ORANGE, font=(FONT, 8)).pack(fill='x')

        tk.Frame(c, bg=LINE, height=1).pack(fill='x', pady=10)
        info = tk.Frame(c, bg=BG); info.pack(fill='x')
        tk.Label(info, text=f'{len(DB)} itens na base  ·  {len(custom)} cadastrados por você  ·  {len(unknown)} aguardando',
                 font=(FONT, 8), fg=MUTED, bg=BG, anchor='w').pack(fill='x')
        b_open = tk.Label(info, text='📂  Abrir pasta de dados', font=(FONT, 9), fg=SKY, bg=BG, anchor='w', cursor='hand2')
        b_open.pack(fill='x', pady=(6, 0))
        b_open.bind('<Button-1>', lambda e: subprocess.Popen(['explorer', DATA_DIR]))
        b_ok = tk.Label(c, text='Fechar', font=(FONT, 10, 'bold'), fg='white', bg=GREEN, padx=22, pady=7, cursor='hand2')
        b_ok.pack(anchor='e', pady=(12, 0)); b_ok.bind('<Button-1>', lambda e: self.close_modal())

        m.update_idletasks()
        m.geometry(f'+{max(20, self.root.winfo_x() - m.winfo_width() - 14)}+{self.root.winfo_y() + 40}')

    def update_foot(self):
        extra = f"tecla {pretty_key(cfg['hotkey'])}" if cfg['mode'] == 'hotkey' else 'automático'
        self.l_foot.config(text=f'{extra}  ·  catálogo: {len(catalog)}  ·  {self.status_text}')

    def close_modal(self):
        self.recording = None
        if self.modal: self.modal.destroy(); self.modal = None
        self.open_until = time.time() + 2

    def save_custom(self, name, cat, note, alias, icon):
        name = norm(name)
        if not name: return
        alias = norm(alias)
        custom[name] = {'cat': cat, 'note': note.strip(), 'alias': alias if alias in DB else None, 'ts': int(time.time())}
        json.dump(custom, open(CUSTOM_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        unknown.pop(name, None)
        json.dump(unknown, open(UNKNOWN_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        global NAMES
        merge_custom(); NAMES = list(DB.keys())
        self.save_catalog(name, icon, 1.0)
        self.close_modal()
        self.q.put(('show', (name, icon, 1.0)))

    # ----- loop -----
    def tick(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'show':
                    name, icon, score = payload
                    color, dark, tag, info = self.describe(name)
                    self.pending = (name, icon)
                    self.photo = ImageTk.PhotoImage(icon.resize((68, 68), Image.NEAREST))
                    self.icon_box.config(image=self.photo, width=68, height=68, bg=dark)
                    self.l_name.config(text=name.title()); self.l_cat.config(text=tag, bg=color)
                    self.l_info.config(text=info); self.root.configure(bg=color)
                    self.b_reg.pack_forget()
                    self.update_foot()
                    self.open_panel()
                elif kind == 'novo':
                    name, icon, _ = payload
                    self.pending = (name, icon)
                    self.photo = ImageTk.PhotoImage(icon.resize((68, 68), Image.NEAREST))
                    self.icon_box.config(image=self.photo, width=68, height=68, bg=BG2)
                    self.l_name.config(text=name.title()); self.l_cat.config(text='NÃO CADASTRADO', bg=INDIGO)
                    self.l_info.config(text='Este item ainda não está na base do site.\nClique abaixo para dizer para que ele serve.')
                    self.root.configure(bg=INDIGO)
                    self.b_reg.pack(fill='x', padx=12, pady=(2, 6), before=self.l_foot)
                    self.l_foot.config(text=f'{len(unknown)} itens aguardando cadastro  ·  {self.status_text}')
                    self.open_panel()
                elif kind == 'recorded':
                    self.recording = None
                    cfg['hotkey'] = payload; cfg['mode'] = 'hotkey'; save_cfg()
                    try:
                        l_key, b_rec = self._cfg_widgets
                        l_key.config(text=pretty_key(payload), fg=SKY)
                        b_rec.config(text='Gravar tecla', bg=INDIGO)
                    except Exception: pass
                    self.update_foot()
                elif kind == 'nada':
                    self.l_name.config(text='Nada encontrado aqui')
                    self.l_cat.config(text='TENTE DE NOVO', bg=BG3)
                    self.icon_box.config(image='', bg=BG2)
                    self.l_info.config(text='Deixe o tooltip do item aberto na tela e aperte a tecla de novo.')
                    self.root.configure(bg=BG3); self.b_reg.pack_forget(); self.open_panel()
                elif kind == 'update':
                    self.b_update.config(text=f'⬇ Atualizar para v{payload}')
                    self.b_update.pack(side='right', padx=(0, 6), pady=6)
                elif kind == 'quit':
                    self.root.destroy(); return
        except queue.Empty: pass
        if self.body.winfo_manager() and time.time() > self.open_until: self.close_panel()
        self.root.after(80, self.tick)

if __name__ == '__main__':
    ensure_installed()
    log('início', VERSION, 'itens:', len(DB))
    App().root.mainloop()
