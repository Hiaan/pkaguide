# PKA Guia — site interativo da planilha PokeAlliance

- `pka.xlsx` — export da planilha pública (Google Sheets).
- `build_data.py` — converte a planilha em `site/src/data/data.json` (rode `python build_data.py` após baixar uma nova versão da planilha).
- `site/` — app Vite + React + TypeScript.

```bash
# atualizar dados
curl -L -o pka.xlsx "https://docs.google.com/spreadsheets/d/1GCH3PmFKQrBj7AA51hgqfg6Q2SrvNgrNlxgIidVeTMU/export?format=xlsx"
python build_data.py

# rodar local
cd site && npm install && npm run dev
```

Deploy: Vercel usa o `vercel.json` da raiz (build em `site/`, output `site/dist`).
