# -*- coding: utf-8 -*-
"""
PKA Overlay: passa o mouse em um item no jogo e o painel mostra para que ele serve.
Painel flutuante (arrastável) com botão liga/desliga e ✕ para fechar. Sem teclas de atalho.
Lê o tooltip do jogo por OCR (nada é injetado no cliente), cruza com a base do site (items_db.json)
e guarda o ícone + nome em catalog/ para montar o catálogo de itens.
"""
import json, os, re, threading, time, queue, difflib, unicodedata
import tkinter as tk
import numpy as np
import mss
from PIL import Image, ImageTk
from pynput import mouse

HERE = os.path.dirname(os.path.abspath(__file__))
DB = json.load(open(os.path.join(HERE, 'items_db.json'), encoding='utf-8'))
NAMES = list(DB.keys())
CATALOG_DIR = os.path.join(HERE, 'catalog')
os.makedirs(CATALOG_DIR, exist_ok=True)
CATALOG_FILE = os.path.join(CATALOG_DIR, 'catalog.json')
catalog = json.load(open(CATALOG_FILE, encoding='utf-8')) if os.path.exists(CATALOG_FILE) else {}

REGION = (-330, -150, 360, 140)  # área lida ao redor do cursor (depot: tooltip abaixo/direita; bag: card à esquerda)
STILL_MS = 300                   # mouse parado por este tempo dispara a leitura
ICON = 34                        # tamanho do ícone capturado para o catálogo
SHOW_S = 7                       # segundos que o painel fica aberto após reconhecer um item

# cores / rótulos por categoria
CATS = {
    'talento': ('#22c55e', '#052e16', 'USAR  ·  VENDER PARA PLAYER', 'Usado em PokeTalent'),
    'boost': ('#eab308', '#422006', 'BOOST', 'Item de boost'),
    'material': ('#38bdf8', '#082f49', 'MATERIAL', 'Stone / fragmento de boost'),
    'npc': ('#a1a1aa', '#27272a', 'SÓ NPC', 'Sem uso conhecido: vender para NPC'),
    'desconhecido': ('#a1a1aa', '#27272a', 'SEM REGISTRO', 'Não está na base do site'),
}
BG, BG2, LINE, TXT, MUTED, ORANGE = '#18181b', '#27272a', '#3f3f46', '#fafafa', '#a1a1aa', '#f97316'
FONT = 'Segoe UI'

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
    """acha o item da base mais parecido com o texto lido pelo OCR"""
    t = norm(text)
    t = re.sub(r'^\s*(x\s*)?\d+\s*x?\s+', '', t)   # "16 wigglytuff ears" -> "wigglytuff ears"
    t = re.sub(r'\s+x?\d+\s*$', '', t)              # "... x12" no fim
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
    lines = [r[1] for r in (res or []) if float(r[2]) > 0.5]
    return lines, icon

# ---------- painel ----------
class App:
    def __init__(self):
        self.enabled = True
        self.pos = (0, 0)
        self.last_move = time.time()
        self.last_read_pos = None
        self.q = queue.Queue()
        self.photo = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.97)
        self.root.configure(bg=ORANGE)
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(padx=1, pady=1)

        # cabeçalho (arrastável)
        head = tk.Frame(outer, bg=BG2, cursor='fleur')
        head.pack(fill='x')
        tk.Label(head, text='◉', font=(FONT, 12, 'bold'), fg=ORANGE, bg=BG2).pack(side='left', padx=(10, 4), pady=6)
        tk.Label(head, text='PKA Overlay', font=(FONT, 10, 'bold'), fg=TXT, bg=BG2).pack(side='left', pady=6)
        self.b_close = tk.Label(head, text='✕', font=(FONT, 10, 'bold'), fg=MUTED, bg=BG2, padx=10, cursor='hand2')
        self.b_close.pack(side='right', pady=6)
        self.b_close.bind('<Button-1>', lambda e: self.q.put(('quit', None)))
        self.b_close.bind('<Enter>', lambda e: self.b_close.config(fg='#ef4444'))
        self.b_close.bind('<Leave>', lambda e: self.b_close.config(fg=MUTED))
        self.b_toggle = tk.Label(head, text='', font=(FONT, 9, 'bold'), fg='white', bg='#16a34a', padx=10, pady=2, cursor='hand2')
        self.b_toggle.pack(side='right', padx=(0, 6), pady=6)
        self.b_toggle.bind('<Button-1>', lambda e: self.toggle())
        head.bind('<ButtonPress-1>', self.drag_start); head.bind('<B1-Motion>', self.drag)

        # corpo
        body = tk.Frame(outer, bg=BG, width=360)
        body.pack_propagate(False)
        self.body = body          # começa fechado: só o cabeçalho aparece
        self.open_until = 0
        top = tk.Frame(body, bg=BG)
        top.pack(fill='x', padx=12, pady=(10, 4))
        self.icon_box = tk.Label(top, bg=BG2, width=68, height=68, bd=0)
        self.icon_box.pack(side='left')
        right = tk.Frame(top, bg=BG)
        right.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.l_name = tk.Label(right, text='Passe o mouse em um item', font=(FONT, 12, 'bold'), fg=TXT, bg=BG, anchor='w', justify='left', wraplength=250)
        self.l_name.pack(fill='x')
        self.l_cat = tk.Label(right, text='DEPOT, BAG OU LOOT', font=(FONT, 8, 'bold'), fg=MUTED, bg=BG2, anchor='w', padx=8, pady=3)
        self.l_cat.pack(anchor='w', pady=(6, 0))
        tk.Frame(body, bg=LINE, height=1).pack(fill='x', padx=12, pady=(8, 6))
        self.l_info = tk.Label(body, text='Segure o mouse parado no item até o tooltip do jogo aparecer.\nO painel lê o nome e mostra para que ele serve.', font=(FONT, 9), fg=MUTED, bg=BG, justify='left', anchor='nw', wraplength=336)
        self.l_info.pack(fill='x', padx=12, pady=(0, 10))
        self.l_foot = tk.Label(body, text='carregando OCR…', font=(FONT, 8), fg='#71717a', bg=BG, anchor='w')
        self.l_foot.pack(fill='x', padx=12, pady=(0, 8))

        self.set_toggle()
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f'+{sw - 380}+12')

        mouse.Listener(on_move=self.on_move).start()
        threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=self.preload, daemon=True).start()
        self.root.after(80, self.tick)

    # ----- UI helpers -----
    def preload(self):
        get_ocr(); self.q.put(('foot', 'OCR pronto · %d itens na base · %d no catálogo' % (len(DB), len(catalog))))

    def fit(self):
        self.root.update_idletasks()
        h = sum(w.winfo_reqheight() for w in self.body.winfo_children()) + 30
        self.body.config(height=max(150, h))

    def open_panel(self):
        if not self.body.winfo_manager(): self.body.pack(fill='both')
        self.fit(); self.open_until = time.time() + SHOW_S

    def close_panel(self):
        if self.body.winfo_manager(): self.body.pack_forget()
        self.root.update_idletasks()

    def set_toggle(self):
        self.b_toggle.config(text='● LIGADO' if self.enabled else '○ DESLIGADO', bg='#16a34a' if self.enabled else '#7f1d1d')

    def toggle(self):
        self.enabled = not self.enabled
        self.set_toggle()
        if not self.enabled: self.close_panel()

    def drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def drag(self, e):
        self.root.geometry(f'+{e.x_root - self._dx}+{e.y_root - self._dy}')

    def on_move(self, x, y):
        self.pos = (x, y); self.last_move = time.time()

    # ----- leitura -----
    def worker(self):
        while True:
            time.sleep(0.05)
            if not self.enabled or time.time() - self.last_move < STILL_MS / 1000 or self.pos == self.last_read_pos:
                continue
            self.last_read_pos = self.pos
            x, y = self.pos
            try:  # ignora quando o mouse está sobre o próprio painel
                rx, ry, rw, rh = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()
                if rx <= x <= rx + rw and ry <= y <= ry + rh: continue
            except Exception:
                pass
            try:
                lines, icon = read_tooltip(x, y)
            except Exception as e:
                print('erro captura:', e); continue
            for line in lines:
                name, score = match_name(line)
                if name:
                    self.save_catalog(name, icon, line, score)
                    self.q.put(('show', (name, icon, score)))
                    break

    def save_catalog(self, name, icon, raw, score):
        slug = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        if name not in catalog or score > catalog[name].get('score', 0):
            icon.save(os.path.join(CATALOG_DIR, slug + '.png'))
            catalog[name] = {'file': slug + '.png', 'ocr': raw, 'score': round(score, 3), 'ts': int(time.time())}
            json.dump(catalog, open(CATALOG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def describe(self, name):
        d = DB[name]; color, dark, tag, desc = CATS[d['cat']]
        info = []
        for t in d['talents']:
            info.append(f"🧠  {t['type']} · Talento #{t['n']} · {t['qty']} un.\n      {t['buff'][:90]}")
        if d['boost']: info.append('🔥  Boost: ' + ', '.join(sorted(set(d['boost']))))
        if d['stone']: info.append('💎  Stone de boost: ' + ', '.join(d['stone']))
        if d['fragment']: info.append('🧩  Fragmento de boost: ' + ', '.join(d['fragment']))
        if d['drops']:
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
                    self.l_name.config(text=name.title(), fg=TXT)
                    self.l_cat.config(text=tag, fg='white', bg=color)
                    self.l_info.config(text=info, fg='#e4e4e7')
                    self.root.configure(bg=color)
                    self.l_foot.config(text=('leitura exata' if score >= 0.999 else f'leitura aproximada ({int(score * 100)}%)') + f'  ·  catálogo: {len(catalog)} itens')
                    self.open_panel()
                elif kind == 'foot':
                    self.l_foot.config(text=payload)
                elif kind == 'quit':
                    self.root.destroy(); return
        except queue.Empty:
            pass
        if self.body.winfo_manager() and time.time() > self.open_until:
            self.close_panel()
        self.root.after(80, self.tick)

if __name__ == '__main__':
    print('PKA Overlay iniciado. Itens na base:', len(DB))
    App().root.mainloop()
