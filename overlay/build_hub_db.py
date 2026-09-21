# -*- coding: utf-8 -*-
"""Gera as bases das abas rápidas do overlay a partir dos dados do site:
- site/public/overlay/hub_db.json    (Pokémon, times, tabelas, dens, medalhas)
- site/public/overlay/videos_db.json (títulos + falas dos vídeos, para a busca)
Cópias locais em overlay/ entram no instalador."""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'site', 'src', 'data')
OUT = os.path.join(ROOT, 'site', 'public', 'overlay')
load = lambda n: json.load(open(os.path.join(D, n), encoding='utf-8'))

data = load('data.json'); tasks = load('tasks.json'); hunts = load('hunts.json'); teams2 = load('teams2.json')

def norm(s): return ''.join(ch for ch in s.lower() if ch.isalnum() or ch == ' ').strip()

dens_by = {}
for d in data['dens']:
    for m in d['mobs']: dens_by.setdefault(norm(m), []).append(d['name'])
dung_by = {}
for d in data['dungeons']:
    for m in d['hunts']: dung_by.setdefault(norm(m), []).append(d['name'])

pokemon = []
for p in data['pokemon']:
    k = norm(p['name'])
    tk = []
    for i in tasks['byPokemon'].get(k, {}).get('tasks', []):
        t = tasks['tasks'][i]
        o = next((o for o in t['objectives'] if norm(o.get('target', '')) == k), None)
        tk.append({'npc': t['npc'], 'region': t['region'], 'loc': t.get('loc', ''),
                   'obj': o['text'] if o else '', 'rew': ' · '.join(f"{r['qty']} {r['label']}".strip() for r in t['rewards'])})
    if not tk:
        tk = [{'npc': x['npc'], 'region': '', 'loc': x.get('loc', ''), 'obj': '', 'rew': ''} for x in p.get('tasks', [])]
    pokemon.append({'n': p['name'], 'id': p.get('id'), 't': p.get('type', ''), 'tier': p.get('tier', ''),
                    'drops': p.get('drops', []), 'hunts': p.get('hunts', {}), 'medal': p.get('medal', {}),
                    'tasks': tk, 'dens': dens_by.get(k, []), 'dung': dung_by.get(k, [])})

teams = []
for e in hunts['elements'] + hunts['hunts']:
    teams.append({'name': e['name'], 'sub': e.get('hunt', ''), 'src': 'Safnaw',
                  'rows': [['Tanks', e['tanks'] + e.get('otherTanks', [])], ['DPS', e['dps'] + e.get('otherDps', [])],
                           ['Smeargle', e.get('smeargle', [])]]})
for t in teams2['teams']:
    teams.append({'name': t['element'], 'sub': 'sem T2/T3', 'src': 'loxas',
                  'rows': [['Inicial', [x['name'] + (' (offtank)' if x.get('offtank') else '') for x in t.get('initial', [])]],
                           ['Upgrades', [x['name'] if isinstance(x, dict) else str(x) for x in t.get('upgrades', [])]]]})

hub = {'pokemon': pokemon, 'teams': teams,
       'dens': [{'n': d['name'], 'time': d['time'], 'players': d['players'], 'xph': d['xph']} for d in data['dens']],
       'boost': data['boost'], 'star': data['star'], 'runes': data['runes'], 'shinyRate': data['shinyRate'], 'brokes': data['brokes']}

videos = load('videos.json'); tr = load('transcripts.json')
vdb = [{'id': v['id'], 'title': v['title'], 'ch': v['channel'], 'segs': tr.get(v['id'], [])} for v in videos]

os.makedirs(OUT, exist_ok=True)
for name, obj in (('hub_db.json', hub), ('videos_db.json', vdb)):
    p = os.path.join(OUT, name)
    json.dump(obj, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    shutil.copy(p, os.path.join(ROOT, 'overlay', name))
    print(name, os.path.getsize(p) // 1024, 'KB')
