# -*- coding: utf-8 -*-
"""
PKA Overlay: passa o mouse em um item no jogo e mostra para que ele serve.
  F8  liga / desliga
  F9  fecha o app
Lê o tooltip do jogo por OCR (nada é injetado no cliente), cruza com a base do site (items_db.json)
e guarda o ícone + nome em catalog/ para montar o catálogo de itens.
"""
import json, os, re, sys, threading, time, queue, difflib, unicodedata
import tkinter as tk
import numpy as np
import mss
from PIL import Image
from pynput import mouse, keyboard

HERE = os.path.dirname(os.path.abspath(__file__))
DB = json.load(open(os.path.join(HERE, 'items_db.json'), encoding='utf-8'))
NAMES = list(DB.keys())
CATALOG_DIR = os.path.join(HERE, 'catalog')
os.makedirs(CATALOG_DIR, exist_ok=True)
CATALOG_FILE = os.path.join(CATALOG_DIR, 'catalog.json')
catalog = json.load(open(CATALOG_FILE, encoding='utf-8')) if os.path.exists(CATALOG_FILE) else {}

# região capturada ao redor do cursor (o tooltip do jogo aparece abaixo/à direita)
REGION = (-60, -30, 360, 110)   # dx0, dy0, dx1, dy1
STILL_MS = 300                  # mouse parado por este tempo dispara a leitura
ICON = 34                       # tamanho do ícone capturado para o catálogo

COLORS = {
    'talento': ('#16a34a', 'USAR / VENDER PARA PLAYER', 'Usado em PokeTalent'),
    'boost': ('#ca8a04', 'BOOST', 'Item de boost'),
    'material': ('#0ea5e9', 'MATERIAL', 'Stone / fragmento de boost'),
    'npc': ('#6b7280', 'SÓ NPC', 'Sem uso conhecido: vender para NPC'),
    'desconhecido': ('#6b7280', '?', 'Sem registro na base'),
}

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9\' ]+', ' ', s).strip()

def match_name(text):
    """acha o item da base mais parecido com o texto lido pelo OCR"""
    t = norm(text)
    if len(t) < 3: return None, 0
    # tenta a linha inteira e também prefixos (o OCR pode grudar 'x12' ou pontuação)
    cands = [t] + [t.rsplit(' ', i)[0] for i in range(1, min(3, t.count(' ') + 1))]
    best, score = None, 0
    for c in cands:
        if c in DB: return c, 1.0
        m = difflib.get_close_matches(c, NAMES, n=1, cutoff=0.78)
        if m:
            sc = difflib.SequenceMatcher(None, c, m[0]).ratio()
            if sc > score: best, score = m[0], sc
    return best, score

# ---------- OCR (carregado em thread para não travar a janela) ----------
_ocr = None
def get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr

def read_tooltip(x, y):
    with mss.mss() as sct:
        mon = sct.monitors[0]
        box = {'left': max(mon['left'], x + REGION[0]), 'top': max(mon['top'], y + REGION[1]),
               'width': REGION[2] - REGION[0], 'height': REGION[3] - REGION[1]}
        shot = sct.grab(box)
        img = Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')
        icon_box = {'left': x - ICON // 2, 'top': y - ICON // 2, 'width': ICON, 'height': ICON}
        ish = sct.grab(icon_box)
        icon = Image.frombytes('RGB', ish.size, ish.bgra, 'raw', 'BGRX')
    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    res, _ = get_ocr()(np.array(big))
    lines = [r[1] for r in (res or []) if float(r[2]) > 0.5]
    return lines, icon

# ---------- app ----------
class App:
    def __init__(self):
        self.enabled = True
        self.pos = (0, 0)
        self.last_move = time.time()
        self.last_read_pos = None
        self.q = queue.Queue()
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.96)
        self.root.withdraw()
        self.frame = tk.Frame(self.root, bg='#18181b', bd=0, highlightthickness=2, highlightbackground='#f97316')
        self.frame.pack()
        self.l_name = tk.Label(self.frame, text='', font=('Segoe UI', 11, 'bold'), fg='white', bg='#18181b', anchor='w')
        self.l_name.pack(fill='x', padx=10, pady=(6, 0))
        self.l_cat = tk.Label(self.frame, text='', font=('Segoe UI', 9, 'bold'), fg='white', bg='#3f3f46', anchor='w', padx=6)
        self.l_cat.pack(fill='x', padx=10, pady=(4, 0))
        self.l_info = tk.Label(self.frame, text='', font=('Segoe UI', 9), fg='#d4d4d8', bg='#18181b', justify='left', anchor='w', wraplength=340)
        self.l_info.pack(fill='x', padx=10, pady=(4, 8))
        # status pill (canto superior direito)
        self.status = tk.Toplevel(self.root)
        self.status.overrideredirect(True); self.status.attributes('-topmost', True); self.status.attributes('-alpha', 0.85)
        self.s_label = tk.Label(self.status, text='', font=('Segoe UI', 9, 'bold'), fg='white', bg='#16a34a', padx=10, pady=3)
        self.s_label.pack()
        sw = self.root.winfo_screenwidth()
        self.status.geometry(f'+{sw - 230}+8')
        self.set_status()
        self.hide_at = 0
        mouse.Listener(on_move=self.on_move).start()
        keyboard.Listener(on_press=self.on_key).start()
        threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=get_ocr, daemon=True).start()  # pré-carrega o OCR
        self.root.after(100, self.tick)

    def set_status(self):
        self.s_label.config(text=f'PKA Overlay {"LIGADO  (F8 desliga)" if self.enabled else "DESLIGADO  (F8 liga)"}',
                            bg='#16a34a' if self.enabled else '#7f1d1d')

    def on_move(self, x, y):
        self.pos = (x, y); self.last_move = time.time()

    def on_key(self, key):
        if key == keyboard.Key.f8:
            self.enabled = not self.enabled
            self.q.put(('status', None))
            if not self.enabled: self.q.put(('hide', None))
        elif key == keyboard.Key.f9:
            self.q.put(('quit', None))

    def worker(self):
        while True:
            time.sleep(0.05)
            if not self.enabled: continue
            if time.time() - self.last_move < STILL_MS / 1000: continue
            if self.pos == self.last_read_pos: continue
            self.last_read_pos = self.pos
            x, y = self.pos
            try:
                lines, icon = read_tooltip(x, y)
            except Exception as e:
                print('erro captura:', e); continue
            found = None
            for line in lines:
                name, score = match_name(line)
                if name: found = (name, score, line); break
            if found:
                name, score, raw = found
                self.save_catalog(name, icon, raw, score)
                self.q.put(('show', (name, x, y)))
            else:
                self.q.put(('hide', None))

    def save_catalog(self, name, icon, raw, score):
        slug = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        path = os.path.join(CATALOG_DIR, slug + '.png')
        if name not in catalog or score > catalog[name].get('score', 0):
            icon.save(path)
            catalog[name] = {'file': slug + '.png', 'ocr': raw, 'score': round(score, 3), 'ts': int(time.time())}
            json.dump(catalog, open(CATALOG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def describe(self, name):
        d = DB[name]; cat = d['cat']
        color, tag, desc = COLORS[cat]
        info = []
        for t in d['talents']:
            info.append(f"🧠 {t['type']} talento #{t['n']}: {t['qty']} un.  ·  {t['buff'][:70]}")
        if d['boost']: info.append('🔥 Boost: ' + ', '.join(sorted(set(d['boost']))))
        if d['stone']: info.append('💎 Stone de boost: ' + ', '.join(d['stone']))
        if d['fragment']: info.append('🧩 Fragmento de boost: ' + ', '.join(d['fragment']))
        if d['drops']:
            dr = d['drops']; info.append(f"🎯 Drop de: {', '.join(dr[:4])}{' +' + str(len(dr) - 4) if len(dr) > 4 else ''}")
        if not info: info.append(desc)
        return color, tag, '\n'.join(info)

    def tick(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'show':
                    name, x, y = payload
                    color, tag, info = self.describe(name)
                    self.l_name.config(text=name.title())
                    self.l_cat.config(text=tag, bg=color)
                    self.frame.config(highlightbackground=color)
                    self.l_info.config(text=info)
                    self.root.update_idletasks()
                    w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
                    sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                    px = min(x + 24, sw - w - 8); py = y - h - 16 if y - h - 16 > 0 else y + 60
                    self.root.geometry(f'+{px}+{py}')
                    self.root.deiconify()
                    self.hide_at = time.time() + 6
                elif kind == 'hide':
                    self.root.withdraw()
                elif kind == 'status':
                    self.set_status()
                elif kind == 'quit':
                    self.root.destroy(); return
        except queue.Empty:
            pass
        # esconde se o mouse andou muito ou passou o tempo
        if self.root.state() != 'withdrawn' and self.last_read_pos:
            dx = abs(self.pos[0] - self.last_read_pos[0]); dy = abs(self.pos[1] - self.last_read_pos[1])
            if dx > 70 or dy > 70 or time.time() > self.hide_at:
                self.root.withdraw()
        self.root.after(60, self.tick)

if __name__ == '__main__':
    print('PKA Overlay iniciado. F8 liga/desliga, F9 fecha. Itens na base:', len(DB))
    App().root.mainloop()
