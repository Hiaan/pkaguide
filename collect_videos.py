# -*- coding: utf-8 -*-
"""Coleta metadados de vídeos de PokeAlliance no YouTube (buscas + canais prioritários) -> videos_raw.json"""
import json, subprocess, sys

QUERIES = ['pokealliance', 'poke alliance', 'pka pokemon', 'pokealliance guia', 'pokealliance dicas', 'pokealliance iniciante',
           'pokealliance hunt', 'pokealliance shiny', 'pokealliance star', 'pokealliance boost', 'pokealliance dungeon',
           'pokealliance rocket', 'pokealliance gym', 'pokealliance hoenn', 'pokealliance dinheiro', 'pokealliance up rapido',
           'pokealliance tier list', 'pokealliance helds', 'pokealliance medalhas', 'pokealliance talentos']
CHANNELS = {'Empregolista': 'https://www.youtube.com/channel/UC7o5NHDen-zGFW52tHe1E7g/videos',
            'Canal Do Loxas': 'https://www.youtube.com/channel/UCkUhW2J42LM1XiIbZsd16HQ/videos'}

def run(url, n=None):
    cmd = ['yt-dlp', '--flat-playlist', '-j', '--extractor-args', 'youtube:lang=pt', '--ignore-errors']
    if n: cmd += ['--playlist-end', str(n)]
    cmd.append(url)
    out = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore').stdout
    res = []
    for l in out.splitlines():
        try: res.append(json.loads(l))
        except Exception: pass
    return res

videos = {}
def add(d, src):
    vid = d.get('id')
    if not vid or d.get('ie_key') not in (None, 'Youtube') or len(vid) != 11: return
    v = videos.setdefault(vid, {'id': vid, 'title': d.get('title') or '', 'channel': d.get('channel') or d.get('uploader') or '',
                                'channel_id': d.get('channel_id') or '', 'views': d.get('view_count') or 0,
                                'duration': d.get('duration') or 0, 'sources': []})
    if (d.get('view_count') or 0) > v['views']: v['views'] = d['view_count']
    if not v['title'] and d.get('title'): v['title'] = d['title']
    v['sources'].append(src)

for name, url in CHANNELS.items():
    r = run(url)
    for d in r: add(d, f'channel:{name}')
    print(name, len(r), flush=True)
for q in QUERIES:
    r = run(f'ytsearch80:{q}')
    for d in r: add(d, f'search:{q}')
    print(q, len(r), 'total', len(videos), flush=True)

json.dump(list(videos.values()), open('videos_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('TOTAL', len(videos))
