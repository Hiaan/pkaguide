# -*- coding: utf-8 -*-
"""
PKA Guide Overlay: passa o mouse em um item no jogo e o painel mostra para que ele serve.
- Lê o tooltip por captura de TELA (pixel) + OCR. Não lê memória nem toca no processo do jogo.
- Painel flutuante arrastável, fechado por padrão; abre só quando reconhece um item.
- Base de itens vem do site pkaguide.vercel.app (atualizada todo dia); cai para a cópia local se estiver offline.
- Verifica se existe versão nova do app no GitHub e oferece atualizar com um clique.
- Na primeira execução do .exe, instala em %LOCALAPPDATA%\\PKA Guide Overlay e cria atalhos.
"""
import json, os, re, sys, threading, time, queue, difflib, unicodedata, subprocess, shutil, tempfile
import tkinter as tk
import numpy as np
import mss
from PIL import Image, ImageTk
from pynput import mouse

APP_NAME = 'PKA GUIDE'
VERSION = '1.0.1'
SITE = 'https://pkaguide.vercel.app'
DB_URL = SITE + '/overlay/items_db.json'
VERSION_URL = SITE + '/overlay/version.json'

FROZEN = getattr(sys, 'frozen', False)
BUNDLE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
EXE = sys.executable if FROZEN else None
INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
DATA_DIR = INSTALL_DIR if FROZEN else os.path.dirname(os.path.abspath(__file__))
os.makedirs(DATA_DIR, exist_ok=True)
CATALOG_DIR = os.path.join(DATA_DIR, 'catalog'); os.makedirs(CATALOG_DIR, exist_ok=True)
CATALOG_FILE = os.path.join(CATALOG_DIR, 'catalog.json')
catalog = json.load(open(CATALOG_FILE, encoding='utf-8')) if os.path.exists(CATALOG_FILE) else {}

REGION = (-330, -150, 360, 140)  # área lida ao redor do cursor (depot: tooltip abaixo/direita; bag: card à esquerda)
STILL_MS = 300
ICON = 34
SHOW_S = 7

# ---------- identidade visual (mesma do site) ----------
BG, BG2, BG3, LINE, TXT, MUTED, MUTED2 = '#18181b', '#27272a', '#3f3f46', '#3f3f46', '#fafafa', '#a1a1aa', '#71717a'
ORANGE, YELLOW, SKY, INDIGO = '#f97316', '#eab308', '#0ea5e9', '#4f46e5'
FONT = 'Inter' if os.name == 'nt' else 'Segoe UI'
CATS = {
    'talento': ('#22c55e', '#052e16', 'USAR  ·  VENDER PARA PLAYER', 'Usado em PokeTalent'),
    'boost': (YELLOW, '#422006', 'BOOST', 'Item de boost'),
    'material': (SKY, '#082f49', 'MATERIAL', 'Stone / fragmento de boost'),
    'npc': ('#a1a1aa', BG2, 'SÓ NPC', 'Sem uso conhecido: vender para NPC'),
    'desconhecido': ('#a1a1aa', BG2, 'SEM REGISTRO', 'Não está na base do site'),
}

# ---------- base de itens ----------
def load_db():
    """cópia local (instalada) > cópia embutida no exe"""
    for p in (os.path.join(DATA_DIR, 'items_db.json'), os.path.join(BUNDLE, 'items_db.json')):
        if os.path.exists(p):
            try: return json.load(open(p, encoding='utf-8'))
            except Exception: pass
    return {}

DB = load_db()
NAMES = list(DB.keys())

def refresh_db():
    """baixa a base atualizada do site; devolve (ok, msg)"""
    global DB, NAMES
    try:
        import requests
        r = requests.get(DB_URL, timeout=8); r.raise_for_status()
        d = r.json()
        if isinstance(d, dict) and len(d) > 100:
            json.dump(d, open(os.path.join(DATA_DIR, 'items_db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            DB, NAMES = d, list(d.keys())
            return True, f'{len(DB)} itens (base atualizada do site)'
    except Exception as e:
        return False, f'{len(DB)} itens (offline: {type(e).__name__})'
    return False, f'{len(DB)} itens'

def check_update():
    """devolve (nova_versao, url_exe) ou (None, None)"""
    try:
        import requests
        v = requests.get(VERSION_URL, timeout=8).json()
        if tuple(map(int, v['version'].split('.'))) > tuple(map(int, VERSION.split('.'))):
            return v['version'], v['url']
    except Exception:
        pass
    return None, None

def apply_update(url):
    """baixa o exe novo e troca o atual por um .bat (só quando rodando como exe)"""
    import requests
    new = os.path.join(tempfile.gettempdir(), 'PKA_Guide_Overlay_new.exe')
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(new, 'wb') as f:
            for chunk in r.iter_content(1 << 16): f.write(chunk)
    target = EXE
    bat = os.path.join(tempfile.gettempdir(), 'pka_update.bat')
    open(bat, 'w').write(f'@echo off\r\ntimeout /t 2 /nobreak >nul\r\ncopy /y "{new}" "{target}" >nul\r\nstart "" "{target}"\r\ndel "%~f0"\r\n')
    subprocess.Popen(['cmd', '/c', bat], creationflags=0x08000000)
    os._exit(0)

# ---------- instalação (primeira execução do exe) ----------
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
        print('instalação falhou, rodando daqui mesmo:', e)

# ---------- texto ----------
def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r"[^a-z0-9' ]+", ' ', s).strip()

def singulars(c):
    out = [c]
    if c.endswith('ies'): out.append(c[:-3] + 'y')
    if c.endswith('es') and not c.endswith('ss'): out.append(c[:-2])
    if c.endswith('s') and not c.endswith('ss'): out.append(c[:-1])
    return out

def match_name(text):
    t = norm(text)
    t = re.sub(r'^\s*(x\s*)?\d+\s*x?\s+', '', t)
    t = re.sub(r'\s+x?\d+\s*$', '', t)
    if len(t) < 3 or t.startswith(('price', 'segure')): return None, 0
    groups = [singulars(t)] + [singulars(t.rsplit(' ', i)[0]) for i in range(1, min(3, t.count(' ') + 1))]
    for g in groups:
        for c in g:
            if c in DB: return c, 1.0
    for g in groups:
        for c in g:
            m = difflib.get_close_matches(c, NAMES, n=1, cutoff=0.8)
            if m: return m[0], difflib.SequenceMatcher(None, c, m[0]).ratio()
    return None, 0

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

# ---------- painel ----------
class App:
    def __init__(self):
        self.enabled = True
        self.pos = (0, 0); self.last_move = time.time(); self.last_read_pos = None
        self.q = queue.Queue(); self.photo = None; self.logo = None
        self.update_url = None

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.97)
        self.root.configure(bg=ORANGE)
        try: self.root.iconbitmap(os.path.join(BUNDLE, 'logo.ico'))
        except Exception: pass
        outer = tk.Frame(self.root, bg=BG); outer.pack(padx=1, pady=1)

        # cabeçalho (arrastável) com a identidade do site
        head = tk.Frame(outer, bg=BG2, cursor='fleur'); head.pack(fill='x')
        try:
            self.logo = ImageTk.PhotoImage(Image.open(os.path.join(BUNDLE, 'logo_small.png')).convert('RGBA').resize((28, 28), Image.LANCZOS))
            tk.Label(head, image=self.logo, bg=BG2).pack(side='left', padx=(10, 6), pady=5)
        except Exception:
            tk.Label(head, text='◉', font=(FONT, 12, 'bold'), fg=ORANGE, bg=BG2).pack(side='left', padx=(10, 4), pady=6)
        t = tk.Frame(head, bg=BG2); t.pack(side='left', pady=4)
        tk.Label(t, text='PKA ', font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left')
        tk.Label(t, text='GUIDE', font=(FONT, 10, 'bold'), fg=SKY, bg=BG2).pack(side='left')
        self.b_close = tk.Label(head, text='✕', font=(FONT, 10, 'bold'), fg=MUTED, bg=BG2, padx=10, cursor='hand2')
        self.b_close.pack(side='right', pady=6)
        self.b_close.bind('<Button-1>', lambda e: self.q.put(('quit', None)))
        self.b_close.bind('<Enter>', lambda e: self.b_close.config(fg='#ef4444'))
        self.b_close.bind('<Leave>', lambda e: self.b_close.config(fg=MUTED))
        self.b_toggle = tk.Label(head, text='', font=(FONT, 9, 'bold'), fg='white', bg=ORANGE, padx=10, pady=2, cursor='hand2')
        self.b_toggle.pack(side='right', padx=(0, 6), pady=6)
        self.b_toggle.bind('<Button-1>', lambda e: self.toggle())
        self.b_update = tk.Label(head, text='', font=(FONT, 9, 'bold'), fg='white', bg=INDIGO, padx=10, pady=2, cursor='hand2')
        self.b_update.bind('<Button-1>', lambda e: self.do_update())
        # arrastar segurando em qualquer ponto do cabeçalho (menos nos botões)
        def bind_drag(w):
            if w in (self.b_close, self.b_toggle, self.b_update): return
            w.bind('<ButtonPress-1>', self.drag_start); w.bind('<B1-Motion>', self.drag)
            for c in w.winfo_children(): bind_drag(c)
        bind_drag(head)

        # corpo (fechado por padrão)
        body = tk.Frame(outer, bg=BG, width=360); body.pack_propagate(False)
        self.body = body; self.open_until = 0
        top = tk.Frame(body, bg=BG); top.pack(fill='x', padx=12, pady=(10, 4))
        self.icon_box = tk.Label(top, bg=BG2, width=68, height=68, bd=0); self.icon_box.pack(side='left')
        right = tk.Frame(body if False else top, bg=BG); right.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.l_name = tk.Label(right, text='', font=(FONT, 12, 'bold'), fg=TXT, bg=BG, anchor='w', justify='left', wraplength=250); self.l_name.pack(fill='x')
        self.l_cat = tk.Label(right, text='', font=(FONT, 8, 'bold'), fg='white', bg=BG2, anchor='w', padx=8, pady=3); self.l_cat.pack(anchor='w', pady=(6, 0))
        tk.Frame(body, bg=LINE, height=1).pack(fill='x', padx=12, pady=(8, 6))
        self.l_info = tk.Label(body, text='', font=(FONT, 9), fg='#e4e4e7', bg=BG, justify='left', anchor='nw', wraplength=336); self.l_info.pack(fill='x', padx=12, pady=(0, 10))
        self.l_foot = tk.Label(body, text='', font=(FONT, 8), fg=MUTED2, bg=BG, anchor='w'); self.l_foot.pack(fill='x', padx=12, pady=(0, 8))
        self.status_text = f'v{VERSION} · carregando…'

        self.set_toggle()
        self.root.geometry(f'+{self.root.winfo_screenwidth() - 400}+12')
        mouse.Listener(on_move=self.on_move).start()
        threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=self.startup, daemon=True).start()
        self.root.after(80, self.tick)

    # ----- inicialização em segundo plano -----
    def startup(self):
        ok, msg = refresh_db()
        self.status_text = f'v{VERSION} · {msg}'
        get_ocr()
        self.status_text = f'v{VERSION} · {msg} · OCR pronto'
        newv, url = check_update()
        if newv:
            self.update_url = url
            self.q.put(('update', newv))

    def do_update(self):
        if not self.update_url: return
        if not FROZEN:
            self.b_update.config(text='atualize com git pull'); return
        self.b_update.config(text='baixando…', bg=BG3)
        threading.Thread(target=lambda: apply_update(self.update_url), daemon=True).start()

    # ----- UI -----
    def fit(self):
        self.root.update_idletasks()
        self.body.config(height=max(150, sum(w.winfo_reqheight() for w in self.body.winfo_children()) + 30))

    def open_panel(self):
        if not self.body.winfo_manager(): self.body.pack(fill='both')
        self.fit(); self.open_until = time.time() + SHOW_S

    def close_panel(self):
        if self.body.winfo_manager(): self.body.pack_forget()
        self.root.update_idletasks()

    def set_toggle(self):
        self.b_toggle.config(text='●  LIGADO' if self.enabled else '○  DESLIGADO', bg=ORANGE if self.enabled else BG3)

    def toggle(self):
        self.enabled = not self.enabled; self.set_toggle()
        if not self.enabled: self.close_panel()

    def drag_start(self, e): self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()
    def drag(self, e): self.root.geometry(f'+{e.x_root - self._dx}+{e.y_root - self._dy}')
    def on_move(self, x, y): self.pos = (x, y); self.last_move = time.time()

    # ----- leitura -----
    def worker(self):
        while True:
            time.sleep(0.05)
            if not self.enabled or time.time() - self.last_move < STILL_MS / 1000 or self.pos == self.last_read_pos: continue
            self.last_read_pos = self.pos
            x, y = self.pos
            try:
                rx, ry, rw, rh = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()
                if rx <= x <= rx + rw and ry <= y <= ry + rh: continue
            except Exception: pass
            try: lines, icon = read_tooltip(x, y)
            except Exception as e: print('erro captura:', e); continue
            for line in lines:
                name, score = match_name(line)
                if name:
                    self.save_catalog(name, icon, line, score)
                    self.q.put(('show', (name, icon, score))); break

    def save_catalog(self, name, icon, raw, score):
        slug = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        if name not in catalog or score > catalog[name].get('score', 0):
            icon.save(os.path.join(CATALOG_DIR, slug + '.png'))
            catalog[name] = {'file': slug + '.png', 'ocr': raw, 'score': round(score, 3), 'ts': int(time.time())}
            json.dump(catalog, open(CATALOG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def describe(self, name):
        d = DB[name]; color, dark, tag, desc = CATS.get(d.get('cat', 'desconhecido'), CATS['desconhecido'])
        info = []
        for t in d.get('talents', []): info.append(f"🧠  {t['type']} · Talento #{t['n']} · {t['qty']} un.\n      {t['buff'][:90]}")
        if d.get('boost'): info.append('🔥  Boost: ' + ', '.join(sorted(set(d['boost']))))
        if d.get('stone'): info.append('💎  Stone de boost: ' + ', '.join(d['stone']))
        if d.get('fragment'): info.append('🧩  Fragmento de boost: ' + ', '.join(d['fragment']))
        if d.get('drops'):
            dr = d['drops']; info.append(f"🎯  Drop de: {', '.join(dr[:4])}{'  +' + str(len(dr) - 4) if len(dr) > 4 else ''}")
        if not info: info.append(desc)
        return color, dark, tag, '\n'.join(info)

    def tick(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'show':
                    name, icon, score = payload
                    color, dark, tag, info = self.describe(name)
                    self.photo = ImageTk.PhotoImage(icon.resize((68, 68), Image.NEAREST))
                    self.icon_box.config(image=self.photo, width=68, height=68, bg=dark)
                    self.l_name.config(text=name.title()); self.l_cat.config(text=tag, bg=color)
                    self.l_info.config(text=info); self.root.configure(bg=color)
                    self.l_foot.config(text=('leitura exata' if score >= 0.999 else f'leitura aproximada ({int(score * 100)}%)') + f'  ·  catálogo: {len(catalog)}  ·  {self.status_text}')
                    self.open_panel()
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
    App().root.mainloop()
