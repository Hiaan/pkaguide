# site — PKA GUIDE

App Vite + React + TypeScript publicado em https://pkaguide.vercel.app. A documentação do projeto está no [README da raiz](../README.md) e o que mudou em cada versão no [CHANGELOG](../CHANGELOG.md).

```bash
npm install
npm run dev     # http://localhost:5173
npm run build   # gera site/dist (o que a Vercel publica)
```

## Como está organizado

- `src/App.tsx` — seções do menu lateral, rotas por hash (`#/secao/subpagina`) e busca rápida.
- `src/pages/` — uma página por seção (`Home`, `Pokedex`, `Medals`, `Tasks`, `Wiki`, `Videos`…).
- `src/components/ui.tsx` — peças reutilizadas (cards, badges de tipo e tier, busca, modal de Pokémon).
- `src/lib/data.ts` — carrega os JSONs e expõe tipos, cores e helpers.
- `src/data/*.json` — dados gerados pelos scripts da raiz; não edite à mão.
- `public/overlay/` — bases e `version.json` que o overlay baixa.
- `public/types/` — ícones dos elementos, usados no site e copiados para o overlay.

Rotas aceitam subpáginas com barra (a wiki usa `#/wiki/sistemas/linked-tasks`) e parâmetros (`#/pokedex/simulador?s=...` abre uma montagem de medalhas).
