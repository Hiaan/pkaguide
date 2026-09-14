# -*- coding: utf-8 -*-
"""Cruza videos_raw.json + transcripts/*.json com os temas do site.
Saídas:
  site/src/data/videos.json       -> metadados dos vídeos com transcrição + pontuação por tema
  site/src/data/video_refs.json   -> tema -> vídeos de referência (com minuto e trecho)
  site/src/data/transcripts.json  -> id -> segmentos [[seg, texto]] (carregado sob demanda na aba Vídeos)
"""
import json, math, os, re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9 ]+', ' ', s)

# tema -> (rótulo, termos, rota no site)
TOPICS = {
    'iniciante': ('Começando no jogo', ['iniciante', 'comecar', 'comecando', 'primeiros passos', 'tutorial', 'como jogar', 'level 1', 'nivel 1'], 'faq'),
    'up': ('Upar rápido', ['upar', 'xp', 'experiencia', 'level 150', 'lvl 150', 'level 250', 'level 350', 'up rapido'], 'faq'),
    'dinheiro': ('Fazer dinheiro', ['dinheiro', 'farmar', 'farm', 'kk', 'vender', 'market', 'lucro', 'rico'], 'faq'),
    'shiny': ('Shiny & brokes', ['shiny', 'broke', 'brokes', 'maxima', 'catch', 'pokeball', 'ultra ball', 'alliance ball'], 'sistemas/rates'),
    'star': ('Star Ascension', ['star', 'estrela', 'estrelar', 'ascension', 'estrelado'], 'sistemas/star'),
    'boost': ('Boost', ['boost', 'boostar', 'boost stone', 'fragmento', 'fragmentos'], 'itens/boost'),
    'helds': ('Helds', ['held', 'helds', 'fundir', 'fusao'], 'faq'),
    'talentos': ('PokeTalents', ['talento', 'talentos', 'poketalent', 'orb', 'orbs'], 'itens/talents'),
    'runas': ('Runas', ['runa', 'runas'], 'sistemas/runes'),
    'medalhas': ('Medalhas', ['medalha', 'medalhas', 'medal'], 'pokedex/medals'),
    'dungeon': ('Dungeons & shards', ['dungeon', 'dungeons', 'shard', 'shards', 'arcane'], 'dungeons/list'),
    'dens': ('Dens (hazard / mega)', ['den', 'dens', 'mega den', 'hazard'], 'dungeons/dens'),
    'porygon': ('Quest do Porygon', ['porygon', 'vektor'], 'dungeons/porygon'),
    'gym': ('Ginásios', ['ginasio', 'ginasios', 'gym', 'gyms', 'lider'], 'desafios/gym'),
    'rocket': ('Rockets', ['rocket', 'rockets', 'giovanni', 'equipe rocket'], 'desafios/rocket'),
    'policia': ('Polícia', ['policia', 'oficial', 'officer'], 'desafios/police'),
    'hoenn': ('Hoenn', ['hoenn'], 'faq'),
    'linked': ('Linked tasks', ['linked', 'linked task', 'task', 'tasks'], 'desafios/linked'),
    'bh': ('Brotherhood', ['brotherhood', 'bh', 'contrato', 'contratos'], 'desafios/bh'),
    'times': ('Times & rotação', ['rotacao', 'time', 'times', 'offtank', 'tanque', 'dps', 'lurar'], 'times/hunt'),
    'tier': ('Tier list', ['tier', 'tier list', 'super rare', 'ultra rare', 'legendary', 'lendario', 'mythic'], 'pokedex/tierlist'),
    'hunt': ('Hunts & localizações', ['hunt', 'hunts', 'wildscape', 'onde cacar', 'localizacao', 'spawn', 'respawn'], 'pokedex/hunts'),
    'drops': ('Drops & itens', ['drop', 'drops', 'loot', 'item', 'itens', 'stone'], 'itens/drops'),
    'vip': ('VIP & loja', ['vip', 'premium', 'loja', 'store', 'game pass', 'cupom'], 'faq'),
    'prey': ('Prey', ['prey', 'preys'], 'faq'),
    'pesca': ('Pesca', ['pesca', 'pescar', 'fishing'], 'faq'),
    'dano': ('Dano & builds', ['dano', 'damage', 'dps', 'critico', 'build'], 'sistemas/damage'),
}

vids = {v['id']: v for v in json.load(open('videos_raw.json', encoding='utf-8'))}
videos, refs, transcripts = [], {k: [] for k in TOPICS}, {}
seen = set()
for f in sorted(os.listdir('transcripts')):
    if not f.endswith('.json'): continue
    d = json.load(open(f'transcripts/{f}', encoding='utf-8'))
    v = vids.get(d['id'])
    if not v or not d['segments']: continue
    segs = d['segments']
    # compacta em blocos de ~12s para o site
    chunks, cur_t, cur = [], None, []
    for t, txt in segs:
        if cur_t is None: cur_t = t
        cur.append(txt)
        if t - cur_t >= 12:
            chunks.append([cur_t, ' '.join(cur)]); cur_t, cur = None, []
    if cur: chunks.append([cur_t, ' '.join(cur)])
    transcripts[v['id']] = chunks
    full = norm(' '.join(txt for _, txt in segs))
    words = len(full.split()) or 1
    topics, first = {}, {}
    for key, (label, terms, route) in TOPICS.items():
        n = 0; ft = None; best = None
        for t, txt in chunks:
            nt = norm(txt)
            c = sum(len(re.findall(r'\b' + re.escape(term) + r'\b', nt)) for term in terms)
            if c:
                n += c
                if ft is None: ft = t
                if best is None or c > best[0]: best = (c, t, txt)
        title_hit = sum(1 for term in terms if re.search(r'\b' + re.escape(term) + r'\b', norm(v['title'])))
        if n >= 5 or title_hit:
            score = (n / words) * 1000 + title_hit * 5
            topics[key] = round(score, 2)
            first[key] = {'t': best[1], 'snippet': best[2][:220]} if best else {'t': 0, 'snippet': chunks[0][1][:220] if chunks else ''}
    videos.append({'id': v['id'], 'title': v['title'], 'channel': v['channel'], 'views': v['views'], 'duration': v['duration'],
                   'topics': topics, 'lang': d['lang']})
    seen.add(v['id'])
    for key, sc in topics.items():
        refs[key].append({'id': v['id'], 'score': sc * math.log10(max(v['views'], 10)), 't': first[key]['t'], 'snippet': first[key]['snippet']})

for key in refs:
    refs[key] = [{k: r[k] for k in ('id', 't', 'snippet')} for r in sorted(refs[key], key=lambda r: -r['score'])[:5]]

# vídeos relevantes sem transcrição entram só no ranking
try:
    for vid in json.load(open('videos_pool.json')):
        if vid not in seen and vid in vids:
            v = vids[vid]
            videos.append({'id': v['id'], 'title': v['title'], 'channel': v['channel'], 'views': v['views'], 'duration': v['duration'], 'topics': {}, 'lang': None})
except FileNotFoundError:
    pass
videos.sort(key=lambda v: -v['views'])
os.makedirs('site/src/data', exist_ok=True)
json.dump(videos, open('site/src/data/videos.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'topics': {k: {'label': v[0], 'route': v[2]} for k, v in TOPICS.items()}, 'refs': refs},
          open('site/src/data/video_refs.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(transcripts, open('site/src/data/transcripts.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('videos', len(videos), 'transcripts bytes', os.path.getsize('site/src/data/transcripts.json'))
for k in TOPICS: print(f"  {k:10} {len([1 for v in videos if k in v['topics']]):3} vídeos | top: {[vids[r['id']]['title'][:40] for r in refs[k][:2]]}")
