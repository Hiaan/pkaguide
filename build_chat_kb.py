# -*- coding: utf-8 -*-
"""Gera a base de conhecimento do chat (api/_kb/kb.json) a partir dos dados do site.
Cada trecho tem: id, t (título), u (link da seção no site, em formato #/rota), k (tipo) e x (texto).
O chat só responde com o que estiver aqui, e só manda links que estejam aqui."""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, 'site', 'src', 'data')
OUT = os.path.join(ROOT, 'api', '_kb')
load = lambda n: json.load(open(os.path.join(D, n), encoding='utf-8'))

kb = []
def add(k, t, u, x, tags=''):
    x = re.sub(r'[ \t]+', ' ', x).strip()
    if x: kb.append({'id': len(kb), 'k': k, 't': t, 'u': u, 'x': x[:1800], 'g': tags})

data = load('data.json'); wiki = load('wiki.json'); tasks = load('tasks.json')
hunts = load('hunts.json'); teams2 = load('teams2.json')
items_db = json.load(open(os.path.join(ROOT, 'overlay', 'items_db.json'), encoding='utf-8'))
guia = json.load(open(os.path.join(ROOT, 'overlay', 'rockets_guide.json'), encoding='utf-8'))
q = lambda s: s.replace(' ', '%20')

# ---------- o próprio site ----------
SITE = [
    ('O que é o PKA GUIDE', '#/inicio', 'O PKA GUIDE é um guia da comunidade do PokeAlliance, atualizado todo dia a partir da Pokédex Pública (planilha do Mts Vitor), dos guias de times do Safnaw e do loxas, da wiki oficial e de vídeos. Tem Pokédex, tier list, onde caçar, drops de itens, dens, dungeons, ginásios, rockets, polícia, tasks, wiki, vídeos e ferramentas. Feito por @hianpoke.'),
    ('Calculadora "O que buscar agora"', '#/sistemas/progressao', 'Calculadora de progressão: mostra o que sai mais barato para ganhar dano num Pokémon (subir o Held X-Attack, o Boost, estrelar ou treinar). Você informa estrelas, held, boost, treino, talentos, runa de Attack, medalhas e guild, e coloca os preços do market. Considera a chance de falha das pedras de Boost (50% na primeira faixa, 5% na última, e +10 pontos de chance a cada falha). Mostra o custo por +1% de dano e um planejador "quanto custa ganhar +X%".'),
    ('Simulador de Medalhas', '#/pokedex/simulador', 'Simulador do Medal System: escolha até 10 medalhas de Kanto em um anel, o nível de cada uma (Bronze a Orichalcum) e veja o que sobe e o que cai no personagem. Tem montagem automática por objetivo (dano, tank, caçar shiny, loot, deslocamento, pesca), 5 presets e link para compartilhar.'),
    ('Overlay do PKA GUIDE', '#/ferramentas/overlay', 'O overlay é um programa para Windows: passe o mouse num item dentro do jogo e ele mostra para que serve (talento, boost, material ou só NPC). Lê a tela por OCR, sem mexer no jogo. Tem Consulta rápida com abas (Pokémon, timers, task, times, rockets, medalhas, tabelas, vídeos), ajuste de tamanho e opacidade, e só aparece com o jogo na frente. Atualiza sozinho.'),
    ('Seção Iniciantes', '#/iniciantes/lista', 'A seção Iniciantes tem o guia dos melhores Pokémon para quem está começando (do vídeo do Canal Do Loxas): Arcanine, Poliwrath, Steelix, Mimikyu, Shiny Persian, Omastar, Pachirisu e Shiny Magneton, com o que cada um caça, como conseguir e uma tabela de cobertura por elemento. Também ensina onde e como caçar (Pokédex do jogo, Hunt Finder, mapa) e talentos e boost.'),
    ('Onde e como caçar (Hunt Finder)', '#/iniciantes/hunts', 'Para descobrir onde caçar: use a Pokédex do jogo (Ctrl+K, action bar, Pokédex) e o Hunt Finder, que filtra por nível, Pokémon usado, elemento-alvo, tier do shiny, zona e continente. Dá para fazer o inverso: colocar o seu Pokémon e ver o que ele caça. Ctrl+Tab abre o mapa e marca a hunt escolhida.'),
    ('Talentos e boost para iniciantes', '#/iniciantes/dicas', 'Ao chegar no level 150: compre um held de boost, abra os talentos (Ctrl+T) e faça os mais simples de defesa e de ataque; Pokémon de dupla tipagem precisa dos dois talentos de defesa. Não precisa fazer todos os talentos, mas os iniciais ajudam em tudo.'),
    ('Vídeos e busca nos vídeos', '#/videos/perguntar', 'A aba Vídeos tem busca nas falas de centenas de vídeos de PokeAlliance (Pergunte aos vídeos), vídeos por tema e uma tabela de canais.'),
    ('Sugestões para o site', '#/sugestoes', 'Para sugerir melhorias ou avisar de erros, use a página Sugestões do site: ela abre uma issue no GitHub já preenchida ou copia o texto para você mandar no canal do hianpoke ou no Discord.'),
]
for t, u, x in SITE: add('site', t, u, x)

# ---------- Pokémon (agrupados pela base) ----------
groups = {}
for p in data['pokemon']:
    groups.setdefault(p.get('base') or p['name'], []).append(p)
for base, ps in groups.items():
    linhas = []
    tipo = next((p['type'] for p in ps if p.get('type') and p['type'] != '?'), '')
    for p in ps:
        partes = [f"{p['name']} (tier {p['tier'] or '?'})"]
        if p.get('drops'): partes.append('dropa: ' + ', '.join(p['drops']))
        if p.get('tasks'): partes.append('task com: ' + ', '.join(sorted({t['npc'] for t in p['tasks']})))
        m = p.get('medal') or {}
        if m.get('buff') or m.get('debuff'): partes.append(f"medalha: bônus {m.get('buff') or '-'}, penalidade {m.get('debuff') or '-'}")
        if p.get('hunts'): partes.append('tem hunt cadastrada em Localizações')
        linhas.append('; '.join(partes))
    add('pokemon', f'{base} (Pokédex)', f'#/pokedex/grid?q={q(base)}', f"{base}, tipo {tipo or 'desconhecido'}. " + ' | '.join(linhas), tags=' '.join(p['name'] for p in ps))

# ---------- itens ----------
for name, it in items_db.items():
    cat = {'talento': 'usado em PokeTalent (dá para usar ou vender para player)', 'boost': 'item de boost',
           'material': 'material de boost (stone ou fragmento)', 'npc': 'sem uso conhecido, só vender para NPC'}.get(it.get('cat'), it.get('cat') or '')
    partes = [f'Item {name}: {cat}.']
    if it.get('drops'): partes.append('Dropa de: ' + ', '.join(it['drops'][:30]) + ('…' if len(it['drops']) > 30 else '') + '.')
    for t in (it.get('talents') or [])[:4]:
        partes.append(f"Talento {t['type']} #{t['n']} ({t['qty']} un.): {t['buff']}")
    if it.get('boost'): partes.append('Boost: ' + ', '.join(sorted(set(it['boost']))) + '.')
    if it.get('stone'): partes.append('Stone de boost: ' + ', '.join(it['stone']) + '.')
    if it.get('fragment'): partes.append('Fragmento de boost: ' + ', '.join(it['fragment']) + '.')
    if it.get('alias_de'): partes.append(f"Mesmo item que {it['alias_de']}.")
    if it.get('nota'): partes.append(it['nota'])
    add('item', f'Item: {name}', f'#/itens/drops?q={q(name)}', ' '.join(partes))

# ---------- wiki (por seção) ----------
SKIP = {'sistemas/linked-tasks', 'sistemas/tasks-do-mundo'}
for pg in wiki['pages']:
    if pg['path'] in SKIP: continue
    partes = re.split(r'\n(?=#{2,3} )', pg['md'])
    for parte in partes:
        parte = re.sub(r'<[^>]+>', ' ', parte)
        parte = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', parte)
        parte = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', parte)
        m = re.match(r'#{1,3} (.+)', parte)
        sec = m.group(1).strip() if m else pg['title']
        for i in range(0, len(parte), 1500):
            add('wiki', f"Wiki: {pg['title']}" + ('' if sec == pg['title'] else f' - {sec}'), f"#/wiki/{pg['path']}", parte[i:i + 1500])

# ---------- tasks do mundo ----------
for t in tasks['tasks']:
    obj = '; '.join(o['text'] for o in t['objectives'])
    rew = ', '.join(f"{r['qty']} {r['label']}".strip() for r in t['rewards'])
    add('task', f"Task do mundo: {t['npc']} ({t['region']})", '#/tasks', f"Task do NPC {t['npc']} em {t['region']}. Objetivos: {obj}. Recompensas: {rew}.")

# ---------- rockets, polícia, ginásios ----------
gmap = {g['name'].upper(): g for g in guia['npcs']}
for key, rota, nome in (('rocket', '#/desafios/rocket', 'Rocket'), ('police', '#/desafios/police', 'Polícia')):
    nota = data[key].get('note', '').replace('\n', ' ')
    for t in data[key]['teams']:
        linhas = '; '.join(f"{f['npc']} -> leve {f['rec']}" for f in t['fights'])
        g = gmap.get(t['name'].upper())
        extra = ''
        if g:
            extra = f" Andar {g['andar']}, dificuldade: {g['dificuldade']}. " + ' '.join(g['tips']) + ' ' + ' '.join(f"{r['npc']}: {r['use']}." for r in g['recs'])
        add('npc', f"{nome}: {t['name']}", rota, f"{nome} {t['name']}: " + linhas + '.' + extra)
    if key == 'rocket':
        add('npc', 'Rocket: como funciona (guia do AlastraSz)', rota, ' '.join(guia['intro']) + ' Rank S: ' + ', '.join(guia['ranks']['S']) + '. Rank A: ' + ', '.join(guia['ranks']['A']) + '. Rank B: ' + ', '.join(guia['ranks']['B']) + '. ' + ' '.join(f"{m['t']}: {m['d']}" for m in guia['mecanicas']))
        add('npc', 'Polícia: como funciona (guia do AlastraSz)', '#/desafios/police', ' '.join(guia['police']['tips']))
for c in data['gym']['cities']:
    add('npc', f"Ginásio de {c['city']}", '#/desafios/gym', f"Ginásio de {c['city']}. Tasks: {', '.join(c['tasks'])}. Time do líder: {', '.join(c['leader'])}. " + data['gym']['note'][:600].replace('\n', ' '))

# ---------- dens, dungeons, hazard, linked, brotherhood ----------
for d in data['dens']:
    add('den', f"Den: {d['name']}", '#/dungeons/dens', f"Den {d['name']}: {d['players']} jogador(es), {d['mobsCount']} mobs, {d['xp']} de xp, tempo {d['time']}, ~{d['xph']} xp/hora. Mobs: {', '.join(d['mobs'])}. Itens: {', '.join(d['items'])}.")
for d in data['dungeons']:
    add('dungeon', f"Dungeon: {d['name']}", '#/dungeons/list', f"Dungeon {d['name']}. Pokémon: {', '.join(d['hunts'])}." + (f" Cidade: {d['city']}." if d.get('city') else ''))
for h in data['hazard']:
    add('hazard', f"Hazard Task: {h['npc']}", '#/desafios/hazard', f"Hazard Task do NPC {h['npc']} (Hoenn): {h['task']}.")
lk = data['linked']['tasks']
for i in range(0, len(lk), 15):
    add('linked', 'Linked Tasks', '#/desafios/linked', 'Linked Tasks: ' + '; '.join(f"{t['qty']}x {t['pokemon']} ({t['huntType']})" for t in lk[i:i + 15]))
add('bh', 'Brotherhood (BH)', '#/desafios/bh', str(data['bh']).replace('\n', ' '))

# ---------- sistemas ----------
star = data['star']
add('sistema', 'Star Ascension (custo e dano)', '#/sistemas/star', star['note'].replace('\n', ' ') + ' Cada estrela dobra o número de cópias do Pokémon: 1ª = 1 cópia, 2ª = 2, 3ª = 4, 4ª = 8, 5ª = 16. Custo de máquina por tier: ' + '; '.join(f"{t['tier']}: " + ', '.join(f"{c['dd']:g} DD + {c['kk']:g}kk" for c in t['costs']) for t in star['tiers']))
r = data['runes']
add('sistema', 'Runas', '#/sistemas/runes', 'Runas (pontos por nível e bônus): ' + '; '.join(f"{s['name']}: " + ', '.join(f"{l['points']} pts{(' -> ' + l['bonus']) if l['bonus'] else ''}" for l in s['levels'] if l['points']) for s in r['stats']))
dm = data['damage']
add('sistema', 'Dano de referência', '#/sistemas/damage', 'Dano esperado no lvl 150 sem bônus de attack, por função e tier (' + ', '.join(dm['tiers']) + '): ' + '; '.join(f"{x['role']}: " + ', '.join(x['values']) for x in dm['roles']))
sr = data['shinyRate']
add('sistema', 'Shiny Rate (normais por shiny)', '#/sistemas/rates', 'Média de Pokémon normais por shiny por shiny rate: ' + '; '.join(f"rate {c['rate']}: " + ', '.join(f"{t['tier']} {t['value']}" for t in c['tiers'] if t['value'] is not None) for c in sr['columns']))
add('sistema', 'Máximo de brokes por tier', '#/sistemas/rates', 'Máximo de brokes: ' + ', '.join(f"{b['tier']} {b['max']}" for b in data['brokes']['max']))
for b in data['boost']:
    add('boost', f"Boost de {b['type']}", '#/itens/boost', f"Boost do elemento {b['type']}: stone {b['stone']}, fragmento {b['fragment']}. Itens de boost: {', '.join(b['items'])}.")
fr = data['fragments']
add('boost', 'Fragmentos por faixa de boost', '#/itens/boost', fr['note'] + ' ' + '; '.join(f"faixa {b}: mín {fr['min'][i]}, média {fr['avg'][i]}, máx {fr['max'][i]}" for i, b in enumerate(fr['brackets'])))
por_tipo = {}
for t in data['talents']:
    por_tipo.setdefault(t['type'], []).append(t)
for tipo, ts in por_tipo.items():
    for i in range(0, len(ts), 10):
        add('talento', f'Talentos ({tipo})', '#/itens/talents', f'Talentos do tipo {tipo}: ' + ' | '.join(f"#{t['n']} item {t['item']} x{t['qty']} (de {(str(t['pokemon']).splitlines() or ['?'])[0]}): {t['buff']}" for t in ts[i:i + 10]))

# ---------- times ----------
for e in hunts['elements'] + hunts['hunts']:
    add('time', f"Time por hunt: {e['name']}", '#/times/hunt', f"Time recomendado (Safnaw) para {e['name']}" + (f" ({e['hunt']})" if e.get('hunt') else '') + f": tanks {', '.join(e['tanks'] + e.get('otherTanks', []))}; dps {', '.join(e['dps'] + e.get('otherDps', []))}; Smeargle: {', '.join(e.get('smeargle', []))}.")
for t in teams2['teams']:
    add('time', f"Time sem T2/T3: {t['element']}", '#/times/sem-t2', f"Time sem T2/T3 (loxas) para {t['element']}: " + ', '.join(x['name'] for x in t.get('initial', [])) + ('. Prós: ' + str(t['pros']) if t.get('pros') else '') + ('. Contras: ' + str(t['cons']) if t.get('cons') else ''))

# ---------- FAQ ----------
for f in data['faq']:
    add('faq', f"FAQ: {f['q']}", '#/faq', f"{f['q']}: {f['a']}")

os.makedirs(OUT, exist_ok=True)
json.dump(kb, open(os.path.join(OUT, 'kb.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
tam = os.path.getsize(os.path.join(OUT, 'kb.json'))
por = {}
for c in kb: por[c['k']] = por.get(c['k'], 0) + 1
print(f'{len(kb)} trechos, {tam // 1024} KB:', por)
