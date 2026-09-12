# -*- coding: utf-8 -*-
"""Resolve links imgur (albuns/imagens) da planilha em URLs diretas de imagem.
Usa cache em imgur_cache.json para nao refazer requests a cada execucao."""
import json, re, time, sys, urllib.request

DATA = 'site/src/data/data.json'
CACHE = 'imgur_cache.json'
OUT = 'site/src/data/imgur.json'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}

text = open(DATA, encoding='utf-8').read()
links = sorted(set(re.findall(r'https?://(?:www\.)?imgur\.com/(?:a/|gallery/)?[A-Za-z0-9]+', text)))
try:
    cache = json.load(open(CACHE, encoding='utf-8'))
except Exception:
    cache = {}

def resolve(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        return {'error': str(e)[:80]}
    ids = []
    for m in re.finditer(r'https://i\.imgur\.com/([A-Za-z0-9]{7})(?:[hlmts])?\.(?:png|jpe?g|gif|webp)', html):
        i = m.group(1)
        if i not in ids: ids.append(i)
    # imagem unica (imgur.com/xxxx): a propria pagina traz og:image
    return {'images': [f'https://i.imgur.com/{i}.png' for i in ids[:12]]}

todo = [l for l in links if l not in cache or 'error' in cache[l]]
print(f'{len(links)} links, {len(todo)} para buscar', flush=True)
for n, l in enumerate(todo, 1):
    cache[l] = resolve(l)
    if n % 25 == 0:
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'), indent=0)
        print(f'  {n}/{len(todo)}', flush=True)
    time.sleep(0.6)
json.dump(cache, open(CACHE, 'w', encoding='utf-8'), indent=0)

out = {l: v['images'] for l, v in cache.items() if v.get('images')}
json.dump(out, open(OUT, 'w', encoding='utf-8'), separators=(',', ':'))
errs = [l for l in links if 'error' in cache.get(l, {})]
print(f'ok: {len(out)}  erros: {len(errs)}', errs[:5])
