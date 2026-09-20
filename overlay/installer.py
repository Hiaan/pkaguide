# -*- coding: utf-8 -*-
"""
Instalador do PKA GUIDE Overlay.
Extrai o app (pasta completa, sem descompactar em Temp na hora de usar) para
%LOCALAPPDATA%\\PKA GUIDE\\app, cria atalhos e abre o programa.
  /S  → instala em silêncio (usado pela atualização automática dentro do app)
"""
import os, sys, time, shutil, zipfile, subprocess, threading, tempfile

APP_NAME = 'PKA GUIDE'
EXE_NAME = APP_NAME + '.exe'
BUNDLE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
APP_DIR = os.path.join(INSTALL_DIR, 'app')
TARGET = os.path.join(APP_DIR, EXE_NAME)
SILENT = any(a.lower() in ('/s', '-s', '--silent') for a in sys.argv[1:])

BG, BG2, TXT, MUTED, ORANGE, SKY, GREEN = '#18181b', '#27272a', '#fafafa', '#a1a1aa', '#f97316', '#0ea5e9', '#22c55e'


def kill_running():
    subprocess.run(['taskkill', '/F', '/IM', EXE_NAME], capture_output=True,
                   creationflags=0x08000000)
    time.sleep(1.2)


def extract(progress=None):
    os.makedirs(INSTALL_DIR, exist_ok=True)
    tmp = APP_DIR + '.new'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    with zipfile.ZipFile(os.path.join(BUNDLE, 'app.zip')) as z:
        names = z.namelist()
        for i, n in enumerate(names):
            z.extract(n, tmp)
            if progress and i % 12 == 0:
                progress(i / len(names))
    if progress: progress(1.0)
    shutil.rmtree(APP_DIR, ignore_errors=True)
    os.replace(tmp, APP_DIR)


def shortcuts():
    ps = f'''
$W = New-Object -ComObject WScript.Shell
foreach ($d in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs'))) {{
  $s = $W.CreateShortcut((Join-Path $d '{APP_NAME}.lnk'))
  $s.TargetPath = '{TARGET}'; $s.WorkingDirectory = '{APP_DIR}'; $s.IconLocation = '{TARGET}'
  $s.Description = 'PKA GUIDE Overlay - guia de itens do PokeAlliance'; $s.Save()
}}'''
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, creationflags=0x08000000)
    # remove instalações antigas (versões 1.x ficavam soltas na raiz)
    for old in (os.path.join(INSTALL_DIR, EXE_NAME),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'PKA Guide Overlay')):
        try:
            if os.path.isdir(old): shutil.rmtree(old, ignore_errors=True)
            elif os.path.isfile(old): os.remove(old)
        except Exception: pass
    for d in (os.path.join(os.path.expanduser('~'), 'Desktop'),
              os.path.join(os.environ.get('APPDATA', ''), 'Microsoft/Windows/Start Menu/Programs')):
        p = os.path.join(d, 'PKA Guide Overlay.lnk')
        try:
            if os.path.exists(p): os.remove(p)
        except Exception: pass


def run_app():
    subprocess.Popen([TARGET], cwd=APP_DIR, creationflags=0x00000008)


def install_silent():
    kill_running(); extract(); shortcuts(); run_app()


def install_gui():
    import tkinter as tk
    from PIL import Image, ImageTk

    root = tk.Tk()
    root.title(APP_NAME)
    root.configure(bg=BG)
    root.resizable(False, False)
    try: root.iconbitmap(os.path.join(BUNDLE, 'logo.ico'))
    except Exception: pass
    W, H = 460, 290
    root.geometry(f'{W}x{H}+{(root.winfo_screenwidth() - W) // 2}+{(root.winfo_screenheight() - H) // 3}')

    try:
        img = Image.open(os.path.join(BUNDLE, 'logo_small.png')).convert('RGBA').resize((84, 84), Image.LANCZOS)
        ph = ImageTk.PhotoImage(img)
        l = tk.Label(root, image=ph, bg=BG, bd=0); l.image = ph; l.pack(pady=(26, 10))
    except Exception:
        pass
    t = tk.Frame(root, bg=BG); t.pack()
    tk.Label(t, text='PKA ', font=('Segoe UI', 19, 'bold'), fg=TXT, bg=BG).pack(side='left')
    tk.Label(t, text='GUIDE', font=('Segoe UI', 19, 'bold'), fg=SKY, bg=BG).pack(side='left')
    tk.Label(root, text='Overlay de itens do PokeAlliance', font=('Segoe UI', 10), fg=MUTED, bg=BG).pack(pady=(2, 0))

    status = tk.Label(root, text='Pronto para instalar', font=('Segoe UI', 9), fg=MUTED, bg=BG)
    status.pack(pady=(18, 6))
    bar_bg = tk.Frame(root, bg=BG2, height=6, width=320); bar_bg.pack(); bar_bg.pack_propagate(False)
    bar = tk.Frame(bar_bg, bg=ORANGE, height=6, width=0); bar.place(x=0, y=0)

    btn = tk.Label(root, text='  Instalar agora  ', font=('Segoe UI', 11, 'bold'), fg='white', bg=ORANGE,
                   padx=18, pady=9, cursor='hand2')
    btn.pack(pady=18)

    def set_progress(p):
        bar.config(width=int(320 * p)); root.update_idletasks()

    def go(_=None):
        btn.pack_forget()
        def work():
            try:
                status.config(text='Fechando versões antigas…'); kill_running()
                status.config(text='Instalando arquivos…')
                extract(set_progress)
                status.config(text='Criando atalhos…'); shortcuts()
                status.config(text='Pronto! Abrindo o PKA GUIDE…', fg=GREEN)
                bar.config(bg=GREEN); set_progress(1.0)
                time.sleep(1.0); run_app(); root.after(300, root.destroy)
            except Exception as e:
                status.config(text=f'Erro: {e}', fg='#ef4444')
        threading.Thread(target=work, daemon=True).start()

    btn.bind('<Button-1>', go)
    tk.Label(root, text=f'Instala em {INSTALL_DIR}', font=('Segoe UI', 8), fg='#52525b', bg=BG).pack(side='bottom', pady=8)
    root.mainloop()


if __name__ == '__main__':
    if SILENT: install_silent()
    else: install_gui()
