# PKA GUIDE Overlay

Overlay para Windows: passe o mouse (ou aperte a tecla) em um item dentro do PokeAlliance e o painel mostra para que ele serve. Tem também uma **Consulta rápida** com abas, para não precisar sair do jogo.

- Lê o tooltip por **captura de tela + OCR**. Não lê memória, não injeta nada no cliente, não aperta tecla nem clica por você.
- Instalação por instalador nativo (Inno Setup) em `%LOCALAPPDATA%\PKA GUIDE\app`, com atalhos na área de trabalho e no menu Iniciar.
- Ao abrir, baixa as bases de https://pkaguide.vercel.app/overlay/ (usa a cópia local se estiver offline) e confere se há versão nova em `version.json`.

## Painel do item

- Categoria (PokeTalent, boost, material ou só NPC), talentos, boost, stone, fragmento e de quais Pokémon o item dropa.
- Elementos aparecem com o **ícone do tipo** (as mesmas artes do site, em `overlay/types/`).
- Item fora da base abre como "NÃO CADASTRADO", com botão para cadastrar. Cadastros vão para `custom_items.json` e os não reconhecidos para `nao_reconhecidos.json`.

## Consulta rápida (botão no topo)

| Aba | O que faz |
| --- | --- |
| Pokémon | Tipo, tier, drops, links de hunt, dens, dungeons, medalha e as tasks da wiki. |
| Timers | Rocket, Polícia, Boss, Dungeon, dens ou um timer seu. Avisa com som quando acaba, mesmo com a janela fechada. |
| Task | Procura uma task e acompanha o progresso de cada objetivo com contador. |
| Times | Times por elemento ou hunt (guias do Safnaw e do loxas). |
| Medalhas | Cole o link do simulador do site para ver sua montagem e o que sobe e cai. |
| Tabelas | Boost, Star, Runas, Shiny Rate e Max Broke. |
| Vídeos | Busca nas falas dos vídeos e abre no minuto certo. |

## Só com o jogo na frente

Por padrão o painel some quando outra janela ganha o foco (checa a janela da frente a cada ~0,5s pela API do Windows) e volta quando o jogo volta. Em ⚙ dá para desligar ou apontar outro executável com "Usar a janela da frente" (`only_game` e `game` no `config.json`).

## Ajuste rápido (topo do painel)

Barra sempre visível com **Tamanho** (60% a 150%, o app reabre para aplicar) e **Opacidade** (30% a 100%, muda na hora).

## Configurações (⚙)

Modo de leitura (automático, só na tecla, ou ambos), tecla de atalho gravável, tamanho e transparência do painel e por quanto tempo ele fica aberto. Tudo em `config.json`, junto com timers, task acompanhada e a montagem de medalhas.

## Rodar do código

```
pip install -r requirements.txt
python build_items_db.py
python build_hub_db.py
python pka_overlay.py
```

## Gerar o instalador

`build.bat` gera as bases, compila o app com PyInstaller (`--onedir`) e monta `dist\PKA GUIDE Setup.exe` com o Inno Setup (`tools\inno\ISCC.exe setup.iss`).

## Publicar uma versão nova

1. Suba `VERSION` em `pka_overlay.py` e `AppVersion` em `setup.iss`.
2. Rode `build.bat` e publique `dist\PKA GUIDE Setup.exe` como asset de uma release `v<versão>` no GitHub.
3. Atualize `site/public/overlay/version.json` com a versão, a URL do asset e uma nota curta. Os apps abertos passam a oferecer a atualização.
