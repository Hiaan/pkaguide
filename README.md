# PKA GUIDE

Guia da comunidade do PokeAlliance: site em https://pkaguide.vercel.app e um overlay para Windows.
Tudo é gerado a partir de fontes públicas (planilha da Pokédex Pública, wiki oficial, guias de times e transcrições de vídeos) e atualizado todo dia por um workflow do GitHub Actions.

## Estrutura

| Pasta / arquivo | O que é |
| --- | --- |
| `site/` | App Vite + React + TypeScript (o site). Dados prontos em `site/src/data/*.json`. |
| `overlay/` | Overlay para Windows (Python + tkinter) e o que é preciso para gerar o instalador. |
| `site/public/overlay/` | O que o overlay baixa: `items_db.json`, `tasks_db.json`, `hub_db.json`, `videos_db.json` e `version.json`. |
| `build_*.py`, `fetch_*.py` | Scripts que transformam as fontes nos JSONs do site. |
| `.github/workflows/update-data.yml` | Roda os scripts todo dia às 06:00 (Brasília) e commita o que mudou. |

## Scripts de dados

| Script | Fonte | Gera |
| --- | --- | --- |
| `build_data.py` | `pka.xlsx` (Pokédex Pública) | `site/src/data/data.json` (Pokémon, itens, dens, dungeons, ginásios, rockets, star, runas, boost, FAQ…) |
| `build_hunts.py` | `times.xlsx` (guia do Safnaw) | `hunts.json` |
| `build_teams2.py` | `doc2.docx` (guia do loxas) | `teams2.json` |
| `build_wiki.py` | wiki.pokealliance.com | `wiki.json` (48 guias) |
| `build_tasks.py` | página "Tasks do Mundo" da wiki + planilha | `tasks.json` e `site/public/overlay/tasks_db.json` |
| `fetch_imgur.py` | links do Imgur da planilha | `imgur.json` (imagens embutidas no site) |
| `collect_videos.py`, `fetch_transcripts.py`, `build_videos.py` | YouTube | `videos.json`, `transcripts.json`, `video_refs.json` |
| `overlay/build_items_db.py` | `data.json` | `items_db.json` (base do overlay) |
| `overlay/build_hub_db.py` | `data.json`, `tasks.json`, `hunts.json`, `teams2.json`, vídeos | `hub_db.json` e `videos_db.json` (abas da Consulta rápida) |

## Rodar local

```bash
# atualizar os dados da planilha
curl -L -o pka.xlsx "https://docs.google.com/spreadsheets/d/1GCH3PmFKQrBj7AA51hgqfg6Q2SrvNgrNlxgIidVeTMU/export?format=xlsx"
python build_data.py

# rodar o site
cd site && npm install && npm run dev
```

Deploy: a Vercel usa o `vercel.json` da raiz (build em `site/`, saída em `site/dist`) e publica a cada push na `master`.

## Seções do site

Menu fixo à esquerda, no estilo de wiki, com a página inicial no topo.

- **Início** — números do site, destaques, atalhos e vídeos em destaque.
- **Pokédex** — Pokémon, Tier List, Localizações, Tasks (da wiki), Medalhas (lista) e Medalhas (simulador).
- **Itens** — buscar drop, PokeTalents e Boost.
- **Sistemas** — Star, Runas, Dano, Shiny Rate & Brokes.
- **Dungeons** — dungeons, dens e Porygon.
- **Desafios** — ginásios, bosses de guild, rockets, polícia, hazard tasks, linked tasks e Brotherhood.
- **Times** — por hunt (guia do Safnaw) e sem T2/T3 (guia do loxas).
- **Tasks**, **Wiki**, **Vídeos** (busca nas falas, temas e canais), **Ferramentas** (overlay, Critical Catch, PokéForge), **FAQ** e **Sugestões**.

O simulador de medalhas fica em `site/src/pages/Medals.tsx`: 10 espaços, 5 presets salvos no navegador, link para compartilhar e valores de referência do nível Bronze vindos do vídeo do Empregolista (os demais são estimativa, marcados com `~`).

Veja `CHANGELOG.md` para o que mudou em cada versão e `overlay/README.md` para o overlay.
