# -*- coding: utf-8 -*-
"""Converte doc2.docx (Times sem T2-T3, lvl 350, por cabeça do loxas) em site/src/data/teams2.json"""
import json, re, zipfile

z = zipfile.ZipFile('doc2.docx')
x = z.read('word/document.xml').decode('utf8')
lines = []
for p in re.findall(r'<w:p[ >].*?</w:p>', x, re.S):
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip()
    if t: lines.append(t)

KEYS = [('dark', 'Dark/Ghost'), ('eletric', 'Electric'), ('fada', 'Fairy'), ('lutador', 'Fighting'), ('fire', 'Fire'), ('fogo', 'Fire'),
        ('voador', 'Flying'), ('grama', 'Grass'), ('terra', 'Ground'), ('gelo', 'Ice'), ('veneno', 'Poison'), ('psiquico', 'Psychic'),
        ('psíquico', 'Psychic'), ('rock', 'Rock'), ('pedra', 'Rock'), ('metal', 'Steel'), ('agua', 'Water'), ('água', 'Water'),
        ('johto', 'Johto'), ('inseto', 'Bug'), ('dragao', 'Dragon'), ('dragão', 'Dragon')]
FIX = {'Decalty': 'Delcatty', 'Lunatune': 'Lunatone', 'Hydregon': 'Hydreigon', 'Xedinja': 'Shedinja', 'Garbordor': 'Garbodor', 'Marquerain': 'Masquerain'}

def header(line):
    l = line.lower()
    if re.search(r'\s-\s*(t\d|sr)\b', l): return None
    words = len(l.split())
    if not l.startswith('time inicial') and words > 4: return None
    for k, v in KEYS:
        if k in l:
            note = line if (not l.startswith('time inicial') and words > 2) else ''
            return v, note
    return None

def parse_poke(line):
    l = line.strip()
    m = re.match(r'^(.*?)\s*-\s*(T\d|SR|t\d|sr)\b\s*(.*)$', l)
    if m:
        left, tier, rest = m.group(1), m.group(2).upper(), m.group(3)
    else:
        m = re.match(r'^(SHINY [A-Z\' ]+?)\s+(?:GOST\s+)?(T\d|SR)$', l.upper())
        if not m: return None
        left, tier, rest = m.group(1).title(), m.group(2), ''
    tier = {'SR': 'Super Rare'}.get(tier, tier)
    stars = re.search(r'(\d)\s*Stars?', left, re.I)
    off = bool(re.search(r'off\s*tank', left + ' ' + rest, re.I))
    name = re.sub(r'\(?\s*off\s*tank\s*\)?', '', left, flags=re.I)
    name = re.sub(r'\d\s*Stars?', '', name, flags=re.I).strip(' -')
    name = ' '.join(w.capitalize() if w.isupper() else w for w in name.split())
    for k, v in FIX.items(): name = name.replace(k, v)
    note = re.sub(r'\(?\s*off\s*tank\s*\)?', '', rest, flags=re.I).strip(' -()')
    if 'testar' in l.lower(): note = 'Ainda não testado'
    return {'name': name, 'tier': tier, 'stars': int(stars.group(1)) if stars else 0, 'offtank': off, 'note': note}

notes, teams = [], []
cur = None
for i, l in enumerate(lines):
    if i < 2: continue  # titulo + "feito por"
    h = header(l)
    if h:
        cur = {'element': h[0], 'initial': [], 'upgrades': [], 'pros': '', 'cons': '', 'note': h[1]}
        teams.append(cur); continue
    if cur is None:
        notes.append(l); continue
    p = parse_poke(l)
    if p: cur['initial'].append(p)
    else: cur['note'] = (cur['note'] + ' · ' + l).strip(' ·')

incomplete = [t for t in teams if not t['initial']]
teams = [t for t in teams if t['initial']]
out = {'source': 'https://docs.google.com/document/d/1L1-sju28TVQMdjtD-xF-3jAK4reTX-RSuMCGAg-tHkg/edit', 'title': lines[0],
       'notes': notes, 'teams': teams, 'incomplete': incomplete}
json.dump(out, open('site/src/data/teams2.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('teams2', [(t['element'], len(t['initial'])) for t in teams])
print('notes', notes)
for t in teams:
    if t['note']: print(' note', t['element'], '->', t['note'])
