# -*- coding: utf-8 -*-
"""Gera items_db.json (base do overlay) a partir de site/src/data/data.json"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, '..', 'site', 'src', 'data', 'data.json'), encoding='utf-8'))

items = {}
def it(name):
    k = name.strip().lower()
    return items.setdefault(k, {'name': k, 'talents': [], 'boost': [], 'drops': [], 'stone': [], 'fragment': []})

for t in d['talents']:
    it(t['item'])['talents'].append({'type': t['type'], 'n': t['n'], 'qty': t['qty'], 'buff': t['buff'], 'from': t['pokemon']})
for b in d['boost']:
    for x in b['items']:
        it(re.sub(r'\s*\([^)]*\)\s*$', '', x))['boost'].append(b['type'])
    it(b['stone'])['stone'].append(b['type'])
    it(b['fragment'])['fragment'].append(b['type'])
for name, pokes in d['items'].items():
    it(name)['drops'] = pokes

for v in items.values():
    if v['talents']: v['cat'] = 'talento'
    elif v['boost']: v['cat'] = 'boost'
    elif v['stone'] or v['fragment']: v['cat'] = 'material'
    elif v['drops']: v['cat'] = 'npc'
    else: v['cat'] = 'desconhecido'

json.dump(items, open(os.path.join(HERE, 'items_db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print(len(items), 'itens', Counter(v['cat'] for v in items.values()))
