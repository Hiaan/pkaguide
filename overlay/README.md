# PKA Guide Overlay

Passe o mouse em um item no PokeAlliance e o painel mostra para que ele serve (PokeTalent, boost, material ou só NPC).

- Lê o tooltip por **captura de tela + OCR**. Não lê memória, não injeta nada no cliente.
- Base de itens baixada de https://pkaguide.vercel.app/overlay/items_db.json a cada abertura (cópia local se estiver offline).
- Verifica versão nova em https://pkaguide.vercel.app/overlay/version.json e oferece o botão "Atualizar".
- Dois modos (botão ⚙): **automático** (lê quando o mouse para sobre o item) ou **tecla de atalho** configurável (só lê quando você aperta).
- Item fora da base abre o painel como "NÃO CADASTRADO" com botão para cadastrar; os cadastros ficam em `custom_items.json` e os não reconhecidos em `nao_reconhecidos.json`.
- Na primeira execução, o `.exe` se copia para `%LOCALAPPDATA%\PKA Guide Overlay` e cria atalhos na área de trabalho e no menu Iniciar.

## Rodar do código
```
pip install -r requirements.txt
python build_items_db.py
python pka_overlay.py
```

## Gerar o executável
`build.bat` (precisa de `pip install pyinstaller`). Saída em `dist\PKA Guide Overlay.exe`.

## Publicar uma versão nova
1. Suba `VERSION` em `pka_overlay.py`.
2. Rode `build.bat` e publique o exe como asset de uma release no GitHub (`v<versão>`).
3. Atualize `site/public/overlay/version.json` com a versão e a URL do asset. O site publica e os apps abertos passam a oferecer a atualização.
