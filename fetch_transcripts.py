# -*- coding: utf-8 -*-
"""Seleciona os vídeos mais relevantes de videos_raw.json e baixa as transcrições (legendas automáticas pt)
em transcripts/<id>.json como segmentos [[segundos, texto], ...]. Cache: não rebaixa o que já existe."""
import json, os, re, subprocess, sys, time, glob

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 320
PRIORITY = ('Empregolista', 'Canal Do Loxas')
os.makedirs('transcripts', exist_ok=True)

vids = json.load(open('videos_raw.json', encoding='utf-8'))
for v in vids:  # listagens de canal vêm sem nome do canal: recupera da origem
    if not v['channel']:
        src = next((s for s in v['sources'] if s.startswith('channel:')), None)
        if src: v['channel'] = src.split(':', 1)[1]
json.dump(vids, open('videos_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
def relevant(v):
    t = v['title'].lower()
    return any(k in t for k in ('poke alliance', 'pokealliance', 'pka', 'pokéalliance', 'poke aliance'))
# entre 2 e 90 min: fora lives de várias horas
pool = [v for v in vids if relevant(v) and 120 <= (v['duration'] or 0) <= 5400]
prio = sorted([v for v in pool if v['channel'] in PRIORITY], key=lambda v: -v['views'])
others = sorted([v for v in pool if v['channel'] not in PRIORITY], key=lambda v: -v['views'])
# prioridade: todos os relevantes do Empregolista/Loxas (até 2/3 do limite), resto completa por views
sel = prio[: min(len(prio), 120)]
sel += others[: LIMIT - len(sel)]
json.dump([v['id'] for v in pool], open('videos_pool.json', 'w'), indent=0)
print(f'pool {len(pool)} | prioritários {len(prio)} | selecionados {len(sel)}', flush=True)
json.dump([v['id'] for v in sel], open('videos_selected.json', 'w'), indent=0)

def parse_vtt(path):
    segs, last = [], ''
    t = 0
    for l in open(path, encoding='utf-8').read().splitlines():
        m = re.match(r'(\d+):(\d+):(\d+)\.(\d+) --> ', l)
        if m:
            t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)); continue
        if l.startswith(('WEBVTT', 'Kind:', 'Language:')) or not l.strip(): continue
        txt = re.sub(r'<[^>]+>', '', l).strip()
        if txt and txt != last:
            segs.append([t, txt]); last = txt
    return segs

tmp = 'transcripts/_tmp'
os.makedirs(tmp, exist_ok=True)
done = fail = 0
for i, v in enumerate(sel, 1):
    out = f"transcripts/{v['id']}.json"
    if os.path.exists(out): continue
    for f in glob.glob(f'{tmp}/*'): os.remove(f)
    subprocess.run(['yt-dlp', '--skip-download', '--write-auto-subs', '--write-subs', '--sub-langs', 'pt-orig,pt,pt-BR,en',
                    '--sub-format', 'vtt', '-o', f'{tmp}/%(id)s.%(ext)s', '--quiet', '--no-warnings', f"https://www.youtube.com/watch?v={v['id']}"],
                   capture_output=True, text=True)
    files = sorted(glob.glob(f'{tmp}/*.vtt'), key=lambda f: (0 if '.pt' in f else 1, len(f)))
    if files:
        segs = parse_vtt(files[0])
        json.dump({'id': v['id'], 'lang': files[0].split('.')[-2], 'segments': segs}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        done += 1
    else:
        json.dump({'id': v['id'], 'lang': None, 'segments': []}, open(out, 'w', encoding='utf-8'))
        fail += 1
    if i % 10 == 0: print(f'  {i}/{len(sel)} ok={done} sem legenda={fail}', flush=True)
    time.sleep(1.0)
print(f'FIM ok={done} sem legenda={fail}')
