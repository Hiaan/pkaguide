# -*- coding: utf-8 -*-
"""Converte doc.docx (Guia de times para iniciar Hoenn) em site/src/data/teams.json"""
import json, re, zipfile

DOC_URL = 'https://docs.google.com/document/d/1mVsLDJnSddFdjA3r_Gm66L9E5VVb1nAm/export?format=docx'

z = zipfile.ZipFile('doc.docx')
x = z.read('word/document.xml').decode('utf8')
lines = []
for p in re.findall(r'<w:p[ >].*?</w:p>', x, re.S):
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip()
    if t: lines.append(t)

ELEMENTS = {'DARK/GHOST': 'Dark/Ghost', 'ELECTRIC': 'Electric', 'FAIRY': 'Fairy', 'FIGHTING': 'Fighting', 'FIRE': 'Fire', 'FLYING': 'Flying',
            'GRASS': 'Grass', 'GROUND': 'Ground', 'ICE': 'Ice', 'POISON': 'Poison', 'PSYCH': 'Psychic', 'ROCK': 'Rock', 'STEEL': 'Steel',
            'WATER': 'Water', 'BUG': 'Bug', 'DRAGON': 'Dragon'}
FIX = {'Decalty': 'Delcatty', 'Victrebell': 'Victreebel', 'Exeguttor': 'Exeggutor', 'Swallot': 'Swalot', 'Lunatune': 'Lunatone', 'Hydregon': 'Hydreigon'}

def parse_poke(line):
    """'Shiny Rhydon 2 Stars (Offtank) - T2' -> dict"""
    m = re.match(r'^(.*?)\s*-\s*([A-Za-z0-9]+)\s*(.*)$', line)
    if not m: return None
    left, tier, rest = m.group(1), m.group(2).upper().replace('T', 'T'), m.group(3).strip()
    tier = {'SR': 'Super Rare'}.get(tier, tier)
    stars = re.search(r'(\d)\s*Stars?', left, re.I)
    off = bool(re.search(r'offtank', left, re.I))
    name = re.sub(r'\(?\s*offtank\s*\)?', '', left, flags=re.I)
    name = re.sub(r'\d\s*Stars?', '', name, flags=re.I).strip(' -')
    name = ' '.join(name.split())
    for k, v in FIX.items(): name = name.replace(k, v)
    note = rest.strip(' -')
    if 'tem que testar' in (line.lower()): note = 'Ainda não testado'
    return {'name': name, 'tier': tier, 'stars': int(stars.group(1)) if stars else 0, 'offtank': off, 'note': note}

notes, teams, incomplete = [], [], []
i = 0
# observações iniciais
while i < len(lines) and lines[i].upper() not in ELEMENTS:
    if not lines[i].lower().startswith('observa'): notes.append(lines[i])
    i += 1
section = 'teams'
cur = None
while i < len(lines):
    l = lines[i]; U = l.upper().rstrip(':')
    if U.startswith('ROTAÇÕES INCOMPLETAS'): section = 'incomplete'; cur = None
    elif U in ELEMENTS:
        cur = {'element': ELEMENTS[U], 'initial': [], 'upgrades': [], 'pros': '', 'cons': '', 'note': ''}
        (teams if section == 'teams' else incomplete).append(cur)
        mode = 'initial'
    elif cur is not None:
        if U.startswith('TIME INICIAL'): mode = 'initial'
        elif U.startswith('O QUE PODE MELHORAR'): mode = 'upgrades'
        elif U.startswith('PRÓS') or U.startswith('PROS'): cur['pros'] = l.split(':', 1)[1].strip() if ':' in l else ''
        elif U.startswith('CONTRAS'): cur['cons'] = l.split(':', 1)[1].strip() if ':' in l else ''
        else:
            p = parse_poke(l)
            if p: cur[mode].append(p)
            else: cur['note'] = (cur['note'] + ' ' + l).strip()
    i += 1

out = {'source': 'https://docs.google.com/document/d/1mVsLDJnSddFdjA3r_Gm66L9E5VVb1nAm/edit', 'notes': notes, 'teams': teams, 'incomplete': incomplete}
json.dump(out, open('site/src/data/teams.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('teams', [t['element'] for t in teams], 'incomplete', [t['element'] for t in incomplete])
print('notes', len(notes)); print(teams[0]['initial'][:2], teams[0]['pros'])
