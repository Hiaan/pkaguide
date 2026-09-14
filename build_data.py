# -*- coding: utf-8 -*-
"""Converte pka.xlsx (planilha PokeAlliance) em site/src/data/data.json"""
import json, re, unicodedata
import openpyxl

WB = openpyxl.load_workbook('pka.xlsx', data_only=True)
API = json.load(open('pokeapi_list.json', encoding='utf-8'))['results']
API_IDS = {r['name']: int(r['url'].rstrip('/').split('/')[-1]) for r in API}

TYPO = {
    'charmelion': 'charmeleon', 'chicorita': 'chikorita', 'feraligator': 'feraligatr',
    'salamalence': 'salamence', 'zangooze': 'zangoose', 'luvdisk': 'luvdisc',
    'hydreidon': 'hydreigon', 'foette': 'floette', 'ilumise': 'illumise',
    'mime': 'mr. mime', 'mr mime': 'mr. mime', 'wobuffet': 'wobbuffet',
    'infarnape': 'infernape', 'lopuny': 'lopunny', 'vespiqueen': 'vespiquen',
}
API_ALIAS = {'nidoran-female': 'nidoran-f', 'nidoran-male': 'nidoran-m', 'castform-fire': 'castform', 'castform-electric': 'castform',
             'castform-ice': 'castform', 'deoxys': 'deoxys-normal', 'mimikyu': 'mimikyu-disguised', 'wormadam': 'wormadam-plant',
             'giratina': 'giratina-altered', 'shaymin': 'shaymin-land', 'basculin': 'basculin-red-striped', 'darmanitan': 'darmanitan-standard',
             'tornadus': 'tornadus-incarnate', 'thundurus': 'thundurus-incarnate', 'landorus': 'landorus-incarnate', 'keldeo': 'keldeo-ordinary',
             'meloetta': 'meloetta-aria', 'meowstic': 'meowstic-male', 'aegislash': 'aegislash-shield', 'pumpkaboo': 'pumpkaboo-average',
             'gourgeist': 'gourgeist-average', 'zygarde': 'zygarde-50', 'oricorio': 'oricorio-baile', 'lycanroc': 'lycanroc-midday',
             'wishiwashi': 'wishiwashi-solo', 'minior': 'minior-red-meteor', 'toxtricity': 'toxtricity-amped', 'urshifu': 'urshifu-single-strike',
             'indeedee': 'indeedee-male', 'morpeko': 'morpeko-full-belly', 'eiscue': 'eiscue-ice', 'basculegion': 'basculegion-male',
             'enamorus': 'enamorus-incarnate', 'oinkologne': 'oinkologne-male', 'maushold': 'maushold-family-of-four', 'squawkabilly': 'squawkabilly-green-plumage',
             'palafin': 'palafin-zero', 'tatsugiri': 'tatsugiri-curly', 'dudunsparce': 'dudunsparce-two-segment'}

def rows(name):
    ws = WB[name]
    out = []
    for row in ws.iter_rows(values_only=True):
        r = ['' if c is None else c for c in row]
        r = [c.strip() if isinstance(c, str) else c for c in r]
        if any(c != '' for c in r):
            out.append(r)
    return out

def s(v):
    if v is None: return ''
    if isinstance(v, float): return str(int(v)) if v.is_integer() else str(v)
    return re.sub(r'\n{3,}', '\n\n', str(v)).strip()

def norm_name(raw):
    """'sh Raichu' / 'Shiny Raichu' / 'Mega X' -> (display, base, shiny, mega)"""
    n = s(raw).strip()
    shiny = mega = False
    m = re.match(r'^(sh|shiny|s)\s+(.*)$', n, re.I)
    if m:
        shiny = True; n = m.group(2)
    m = re.match(r'^mega\s+(.*)$', n, re.I)
    if m:
        mega = True; n = m.group(1)
    base = n.strip()
    key = base.lower()
    key = TYPO.get(key, key)
    base = ' '.join(w.capitalize() if w.islower() else w for w in key.split(' ')) if key != base.lower() else base
    if key == 'mr. mime': base = 'Mr. Mime'
    disp = ('Mega ' if mega else '') + ('Shiny ' if shiny else '') + base
    return disp, base, shiny, mega

def api_id(base):
    k = base.lower()
    k = unicodedata.normalize('NFKD', k).encode('ascii', 'ignore').decode()
    k = k.replace('. ', '-').replace('.', '').replace("'", '').replace(' ', '-')
    k = API_ALIAS.get(k, k)
    return API_IDS.get(k) or API_IDS.get(re.sub(r'-[xy]$', '', k))

# ---------- Pokémon master ----------
poke = {}
def P(raw):
    disp, base, shiny, mega = norm_name(raw)
    if disp not in poke:
        poke[disp] = {'name': disp, 'base': base, 'shiny': shiny, 'mega': mega, 'id': api_id(base),
                      'drops': [], 'tier': '', 'type': '', 'hunts': {}, 'tasks': [], 'medal': {}}
    return poke[disp]

for r in rows('Drops')[1:]:
    if not s(r[0]): continue
    p = P(r[0])
    p['drops'] = [s(c) for c in r[1:] if s(c)]

for r in rows('Tier List')[1:]:
    if not s(r[0]): continue
    p = P(r[0]); p['tier'] = s(r[1]); p['type'] = s(r[2])

for r in rows('Localizações')[1:]:
    if not s(r[0]): continue
    p = P(r[0])
    h = {}
    for k, i in (('wildscape', 1), ('normal', 2), ('hoenn', 3)):
        v = s(r[i])
        if v and v != '-': h[k] = v
    p['hunts'] = h

for r in rows('Tasks')[1:]:
    if not s(r[0]): continue
    p = P(r[0])
    t = []
    for i in (1, 3, 5):
        if s(r[i]): t.append({'npc': s(r[i]), 'loc': s(r[i+1])})
    p['tasks'] = t

for r in rows('Medals')[1:]:
    if not s(r[0]): continue
    p = P(r[0])
    if s(r[1]) or s(r[2]): p['medal'] = {'buff': s(r[1]), 'debuff': s(r[2])}

# correções manuais de tier (tier_overrides.json): cria o Pokémon se não existir, herdando o tipo da forma base
try:
    _ovf = json.load(open('tier_overrides.json', encoding='utf-8'))
    _ov, _ovt = _ovf['tiers'], _ovf.get('types', {})
except FileNotFoundError:
    _ov, _ovt = {}, {}
for _name, _tier in _ov.items():
    _p = P(_name)
    _p['tier'] = _tier
    if _p['base'] in _ovt: _p['type'] = _ovt[_p['base']]
    if not _p['type']:
        for _cand in (_p['base'], f"Shiny {_p['base']}", _p['base'].replace(' X', '').replace(' Y', '')):
            _q = poke.get(_cand) or poke.get(f'Shiny {_cand}')
            if _q and _q['type']: _p['type'] = _q['type']; break

# item index (reverse drops)
items = {}
for p in poke.values():
    for it in p['drops']:
        items.setdefault(it, [])
        if p['name'] not in items[it]: items[it].append(p['name'])

# ---------- Rates ----------
sr = rows('Shiny Rate')
shiny_rate = {'columns': [], 'note': 'Ajude a tabela a ser mais precisa: mande os dados do seu analyzer pelo form.',
              'form': 'https://docs.google.com/forms/d/e/1FAIpQLSfDhUaqGeUK-6uLphsluOpr_FMMDLni0Q3uPvx69x19tYVfvg/viewform'}
for c in range(0, 14, 2):
    col = {'rate': sr[0][c], 'tiers': []}
    for r in sr[2:7]:
        v = r[c+1]
        col['tiers'].append({'tier': s(r[c]), 'value': round(v, 1) if isinstance(v, (int, float)) else None})
    shiny_rate['columns'].append(col)

br = rows('Brokes')
brokes = {'note': s(br[0][1]), 'max': [{'tier': s(r[0]), 'max': s(r[1])} for r in br[1:]]}

# ---------- Star ----------
sl = rows('Star Level')
star = {'note': s(rows('Star')[3][0]), 'steps': [s(c) for c in sl[0] if s(c)], 'tiers': []}
for r in sl[2:8]:
    if s(r[0]).startswith('#'): continue
    costs = []
    for i in range(1, 11, 2):
        costs.append({'dd': r[i], 'kk': r[i+1]})
    star['tiers'].append({'tier': s(r[0]), 'costs': costs})

# ---------- Runes ----------
ru = rows('Runes')
runes = {'stats': [], 'levels': []}
names = [s(c) for c in ru[0][1:17:2]]
levels = [s(r[0]) for r in ru[2:7]]
runes['levels'] = levels
for j, nm in enumerate(names):
    col = 1 + j*2
    vals = []
    for r in ru[2:7]:
        vals.append({'points': s(r[col]), 'bonus': s(r[col+1])})
    runes['stats'].append({'name': nm, 'levels': vals})
runes['shinyCharmTotal'] = 3200

# ---------- Damage ----------
dm = rows('Damage')
damage = {'tiers': [s(c) for c in dm[0] if s(c)], 'roles': [], 'note': s(dm[5][0])}
for r in dm[1:5]:
    damage['roles'].append({'role': s(r[0]), 'values': [s(c) for c in r[1:8]]})

# ---------- Dungeons ----------
dungeons = []
for r in rows('Dungeons')[1:]:
    if not s(r[0]): continue
    dungeons.append({'name': s(r[0]), 'loc': s(r[1]), 'hunts': [s(c) for c in r[2:] if s(c)]})
dg_city = {s(r[0]): s(r[1]) for r in rows('DGs')[1:] if s(r[0])}
for d in dungeons: d['city'] = dg_city.get(d['name'], '')

dens = {}
for r in rows('DgMobs')[1:]:
    if not s(r[0]): continue
    key = norm_name(r[0])[0]
    dens[key] = {'name': key, 'players': s(r[1]), 'mobsCount': s(r[2]), 'xp': r[3] if isinstance(r[3], (int, float)) else s(r[3]),
                 'time': s(r[4]), 'mobs': [norm_name(c)[0] for c in r[5:10] if s(c)],
                 'xph': r[10] if isinstance(r[10], (int, float)) else s(r[10]), 'items': []}
for r in rows('DgItems')[1:]:
    if not s(r[0]): continue
    key = norm_name(r[0])[0]
    dens.setdefault(key, {'name': key, 'players': s(r[1]), 'mobsCount': '', 'xp': '', 'time': '', 'mobs': [], 'xph': '', 'items': []})
    dens[key]['items'] = [s(c) for c in r[2:] if s(c)]

porygon = [{'title': s(r[0]).rstrip(':'), 'text': s(r[1])} for r in rows('Porygon')]

# ---------- GYM ----------
gy = rows('GYM')
gym = {'note': s(gy[0][4]), 'cities': []}
for r in gy[1:9]:
    gym['cities'].append({'city': s(r[0]), 'tasks': [s(r[1]), s(r[2])], 'dungeon': s(r[3]), 'leader': []})
cities = [s(c) for c in gy[10]]
for r in gy[11:]:
    for i, c in enumerate(cities):
        if i < len(r) and s(r[i]):
            for g in gym['cities']:
                if g['city'] == c: g['leader'].append(norm_name(r[i])[0])

# ---------- Rocket / Police ----------
def parse_blocks(sheet, mode):
    rs = rows(sheet)
    note = s(rs[0][-1])
    teams = []
    i = 0
    while i < len(rs):
        r = rs[i]
        # header row: names in caps in cols 0,3,6,9 (rocket) or 0,2,4,6 (police)
        step = 3
        heads = [(c, s(r[c])) for c in range(0, 12, step) if c < len(r) and s(r[c]) and s(r[c]).isupper()]
        if heads:
            block = [{'name': h, 'col': c, 'fights': []} for c, h in heads]
            j = i + 1
            while j < len(rs) and not any(s(rs[j][c]).isupper() and len(s(rs[j][c])) > 2 for c in range(0, 12, step) if c < len(rs[j])):
                rr = rs[j]
                if s(rr[0]) == ',.' or s(rr[1]) == ',.':
                    j += 1; continue
                for b in block:
                    c = b['col']
                    if c < len(rr) and s(rr[c]):
                        b['fights'].append({'npc': norm_name(rr[c])[0], 'rec': norm_name(rr[c+1])[0] if mode == 'rocket' else s(rr[c+1])})
                j += 1
            teams.extend(block)
            i = j
        else:
            i += 1
    for t in teams: del t['col']
    return {'note': note, 'teams': teams}

rocket = parse_blocks('Rocket', 'rocket')
rocket['giovanniNote'] = 'Para batalhar com o Giovanni, é necessário ter ganhado 130 batalhas contra os demais membros da equipe Rocket'
police = parse_blocks('Police', 'police')

# ---------- Tasks ----------
lt = rows('Linked Tasks')
linked = {'note': s(lt[1][4]), 'tasks': []}
for r in lt[1:]:
    if not s(r[1]): continue
    linked['tasks'].append({'qty': int(r[0]) if isinstance(r[0], (int, float)) else s(r[0]), 'pokemon': norm_name(r[1])[0],
                            'huntType': s(r[2]), 'hunt': s(r[3]), 'killsPerHour': int(r[4]) if isinstance(r[4], (int, float)) else ''})
hazard = [{'npc': s(r[0]), 'loc': s(r[1]), 'task': s(r[2])} for r in rows('Hazard Tasks')[1:] if s(r[0])]
bh = s(rows('BH')[0][0])

# ---------- Talents ----------
talents = []
for r in rows('PokeTalents')[1:]:
    if not s(r[0]): continue
    talents.append({'item': s(r[0]), 'pokemon': s(r[1]), 'qty': int(r[3]) if isinstance(r[3], (int, float)) else s(r[3]),
                    'type': s(r[4]), 'n': int(r[5]) if isinstance(r[5], (int, float)) else s(r[5]), 'buff': s(r[7])})

# ---------- Boost ----------
boost = []
for r in rows('Boost'):
    if not s(r[0]): continue
    boost.append({'type': s(r[0]), 'fragment': s(r[1]), 'stone': s(r[2]), 'items': [s(c) for c in r[3:] if s(c)]})
sb = rows('Search Boost Items')
brackets = ['0-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40', '41-45', '46-50']
frag = {'brackets': brackets, 'min': [sb[3][4+i] for i in range(10)], 'avg': [sb[3][15+i] for i in range(10)], 'max': [sb[3][26+i] for i in range(10)],
        'note': 'Quantidade de fragmentos por faixa de nível de boost (igual para todos os tipos). Mín / média / máx observados em 477 dias.'}

# ---------- FAQ ----------
faq = [{'q': s(r[0]), 'a': s(r[1])} for r in rows('FAQ') if s(r[0]) and s(r[1])]

data = {
    'pokemon': sorted(poke.values(), key=lambda p: ((p['id'] or 9999), p['mega'], p['shiny'])),
    'items': items, 'shinyRate': shiny_rate, 'brokes': brokes, 'star': star, 'runes': runes, 'damage': damage,
    'dungeons': dungeons, 'dens': sorted(dens.values(), key=lambda d: d['name']), 'porygon': porygon, 'gym': gym,
    'rocket': rocket, 'police': police, 'linked': linked, 'hazard': hazard, 'bh': bh, 'talents': talents,
    'boost': boost, 'fragments': frag, 'faq': faq,
}
import os
os.makedirs('site/src/data', exist_ok=True)
json.dump(data, open('site/src/data/data.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('pokemon', len(poke), 'sem id:', [p['name'] for p in poke.values() if not p['id']][:30])
print('items', len(items), 'faq', len(faq), 'talents', len(talents), 'dens', len(dens), 'rocket teams', [t['name'] for t in rocket['teams']], 'police', [t['name'] for t in police['teams']])
