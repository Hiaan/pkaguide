# -*- coding: utf-8 -*-
"""Baixa os guias da wiki oficial (wiki.pokealliance.com) e gera site/src/data/wiki.json.
Só as páginas de sistemas/guias/itens/quests; as fichas de Pokémon já vêm da planilha."""
import json, os, re, time, urllib.request

BASE = 'https://wiki.pokealliance.com'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; PKA-GUIDE/1.0; +https://pkaguide.vercel.app)'}
CACHE = 'wiki_cache.json'

SECTIONS = {
    'guias': ('Comece por aqui', '🚀'),
    'sistemas': ('Sistemas', '⚙️'),
    'itens': ('Itens', '🎒'),
    'quests': ('Quests', '📜'),
    'tutoriais': ('Tutoriais', '🎓'),
    'roadmap': ('Roadmap', '🗺️'),
}
SKIP = {'guias/teste'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')

def title_of(md, path):
    m = re.search(r'^#\s+(.+)$', md, re.M)
    if m: return m.group(1).strip()
    return path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()

def summary_of(md):
    m = re.search(r'^>\s*\*\*Resumo[^:]*:\*\*\s*(.+)$', md, re.M)
    if not m: m = re.search(r'^>\s*(.+)$', md, re.M)
    if m: return re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(1)).strip()[:220]
    for line in md.splitlines():
        line = line.strip()
        if line and not line.startswith(('#', '>', '|', '-', '*', '!')):
            return line[:220]
    return ''

def headings(md):
    return [re.sub(r'[#*`]', '', h).strip() for h in re.findall(r'^##\s+(.+)$', md, re.M)][:12]

def clean(md):
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()

def main():
    pages = json.loads(get(BASE + '/api/pages'))['pages']
    wanted = [p for p in pages if p.split('/')[0] in SECTIONS and p not in SKIP]
    cache = {}
    if os.path.exists(CACHE):
        try: cache = json.load(open(CACHE, encoding='utf-8'))
        except Exception: pass
    out = []
    for i, path in enumerate(sorted(wanted), 1):
        try:
            d = json.loads(get(f'{BASE}/api/page/{path}'))
            if d.get('draft'): continue
            md = clean(d.get('content', ''))
            if len(md) < 40: continue
            sec = path.split('/')[0]
            out.append({'path': path, 'url': f'{BASE}/{path}', 'section': sec,
                        'sectionLabel': SECTIONS[sec][0], 'icon': SECTIONS[sec][1],
                        'title': title_of(md, path), 'summary': summary_of(md),
                        'headings': headings(md), 'md': md})
            cache[path] = md
        except Exception as e:
            print('  erro', path, e)
        if i % 10 == 0: print(f'  {i}/{len(wanted)}', flush=True)
        time.sleep(0.25)
    order = list(SECTIONS)
    out.sort(key=lambda p: (order.index(p['section']), p['title']))
    os.makedirs('site/src/data', exist_ok=True)
    json.dump({'source': BASE, 'updated': time.strftime('%Y-%m-%d'), 'pages': out},
              open('site/src/data/wiki.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    kb = os.path.getsize('site/src/data/wiki.json') // 1024
    print(f'{len(out)} páginas · {kb} KB')
    for p in out: print(f"  [{p['section']:9}] {p['title']}")

if __name__ == '__main__':
    main()
