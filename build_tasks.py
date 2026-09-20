# -*- coding: utf-8 -*-
"""Extrai as Tasks do Mundo da wiki oficial + a localização dos NPCs da planilha
e gera site/src/data/tasks.json (e a cópia para o overlay em site/public/overlay/tasks_db.json)."""
import json, os, re, unicodedata

WIKI = 'https://wiki.pokealliance.com'
SRC_PAGE = 'sistemas/tasks-do-mundo'

def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()

def parse_npc(cell):
    name = re.search(r'world-task-npc__copy.*?<strong>(.*?)</strong>', cell, re.S)
    img = re.search(r'world-task-npcs/([^"\']+)', cell)
    return (strip_tags(name.group(1)) if name else strip_tags(cell)), (f'{WIKI}/api/assets/world-task-npcs/{img.group(1)}' if img else '')

def parse_objectives(cell):
    out = []
    for m in re.finditer(r'<span class="world-task-objective">(.*?)</span>\s*</span>', cell, re.S):
        txt = strip_tags(m.group(1))
        if not txt: continue
        q = re.match(r'(?:Derrotar|Entregar|Capturar)\s+([\d.]+)\s*x?\s+(.+)', txt, re.I)
        out.append({'text': txt,
                    'qty': q.group(1).replace('.', '') if q else '',
                    'target': q.group(2).strip(' .') if q else ''})
    if not out:
        txt = strip_tags(cell)
        if txt: out.append({'text': txt, 'qty': '', 'target': ''})
    return out

def parse_rewards(cell):
    out = []
    for m in re.finditer(r'<span class="linked-reward-item([^"]*)">(.*?)</span>\s*</span>', cell, re.S):
        kind_raw, body = m.group(1), m.group(2)
        img = re.search(r'src="([^"]+)"', body)
        strong = re.search(r'<strong>(.*?)</strong>', body, re.S)
        small = re.search(r'<small>(.*?)</small>', body, re.S)
        kind = 'xp' if 'xp' in kind_raw else ('pokemon' if 'pokemon' in kind_raw else 'item')
        out.append({'kind': kind,
                    'qty': strip_tags(strong.group(1)) if strong else '',
                    'label': strip_tags(small.group(1)) if small else '',
                    'img': (WIKI + img.group(1)) if img and img.group(1).startswith('/') else (img.group(1) if img else '')})
    return out

def main():
    wiki = json.load(open('site/src/data/wiki.json', encoding='utf-8'))
    page = next((p for p in wiki['pages'] if p['path'] == SRC_PAGE), None)
    if not page: raise SystemExit('página de tasks não encontrada em wiki.json')
    md = page['md']

    # localização dos NPCs vem da planilha (aba Tasks): NPC -> link do mapa
    data = json.load(open('site/src/data/data.json', encoding='utf-8'))
    npc_map, npc_pokes = {}, {}
    for p in data['pokemon']:
        for t in p.get('tasks', []):
            k = norm(t['npc'])
            if t.get('loc') and t['loc'].startswith('http'): npc_map.setdefault(k, t['loc'])
            npc_pokes.setdefault(k, [])
            if p['name'] not in npc_pokes[k]: npc_pokes[k].append(p['name'])

    tasks, region = [], ''
    for line in md.splitlines():
        h = re.match(r'^##\s+(.+)$', line)
        if h:
            region = h.group(1).strip()
            continue
        if not line.startswith('| <span class="world-task-npc"'): continue
        cells = [c.strip() for c in line.strip().strip('|').split(' | ')]
        if len(cells) < 3: continue
        npc, npc_img = parse_npc(cells[0])
        objs = parse_objectives(cells[1])
        rews = parse_rewards(cells[2])
        key = norm(npc)
        tasks.append({'npc': npc, 'npcImg': npc_img, 'region': region,
                      'loc': npc_map.get(key, ''), 'objectives': objs, 'rewards': rews,
                      'alsoFor': npc_pokes.get(key, [])})

    # índice por Pokémon-alvo
    by_poke = {}
    for i, t in enumerate(tasks):
        alvos = {o['target'] for o in t['objectives'] if o['target']}
        for a in alvos:
            by_poke.setdefault(norm(a), {'name': a, 'tasks': []})
            by_poke[norm(a)]['tasks'].append(i)

    out = {'source': f'{WIKI}/{SRC_PAGE}', 'updated': wiki.get('updated', ''),
           'regions': sorted({t['region'] for t in tasks}), 'tasks': tasks, 'byPokemon': by_poke}
    os.makedirs('site/public/overlay', exist_ok=True)
    json.dump(out, open('site/src/data/tasks.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(out, open('site/public/overlay/tasks_db.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    kb = os.path.getsize('site/src/data/tasks.json') // 1024
    com_loc = sum(1 for t in tasks if t['loc'])
    print(f'{len(tasks)} tasks · {len(by_poke)} Pokémon-alvo · {com_loc} com mapa · {kb} KB')
    print('regiões:', out['regions'])
    ex = tasks[0]
    print('exemplo:', ex['npc'], '|', ex['region'], '|', [o['text'] for o in ex['objectives']], '|',
          [f"{r['qty']} {r['label']}" for r in ex['rewards']])

if __name__ == '__main__':
    main()
