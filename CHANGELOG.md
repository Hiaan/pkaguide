# Alterações recentes

Datas em 2026. O overlay segue a numeração das releases em https://github.com/Hiaan/pkaguide/releases.

## Overlay

### v2.9.2 — 24/09
- Só abre um painel por vez: depois de atualizar não ficam dois overlays na tela.

### v2.9.1 — 24/09
- Busca da aba Rockets: procurar "rocket", "policia" ou "ginasio" não dá mais "Nada encontrado", e quando o nome existe em outra lista (ex.: "blaze" na Polícia) ele mostra de lá.

### v2.9.0 — 24/09
- Aba **Rockets** na Consulta rápida: Rocket, Polícia e Ginásios, cada NPC com o Pokémon dele e o recomendado para levar.
- Busca por NPC ou por Pokémon ("gengar" mostra quem usa Gengar); sem busca, aparece só a lista de nomes para clicar.
- Depois de atualizar sozinho, o app reabre sozinho.

### v2.8.0 — 24/09
- **Atualiza sozinho**: ao abrir, baixa e instala a versão nova sem precisar clicar (dá para desligar em ⚙).
- Aviso e botão **"Reabrir como administrador"** quando o jogo está aberto como administrador — é o motivo de a tecla de atalho não funcionar dentro do jogo.
- Tabela de Star: campo "1 DD custa X kk" mostra o custo total em kk e uma linha com quantos Pokémon cada estrela consome (2, 4, 8, 16, 32).

### v2.7.0 — 23/09
- O painel **só aparece com o jogo na frente**: ao trocar para o navegador ou outro programa ele some sozinho e volta quando o jogo volta.
- Dá para desligar em ⚙ → "Só aparecer com o jogo na frente", e o botão "Usar a janela da frente" aponta outro cliente se o executável tiver outro nome.

### v2.6.0 — 23/09
- Barra de ajuste rápido sempre à vista no topo: **Tamanho** (60% a 150%) e **Opacidade** (30% a 100%), com botões − e +.
- O tamanho vale para tudo (fontes, ícones, largura do painel e das janelas de consulta). Ao trocar, o app reabre sozinho.
- Também dá para usar o slider de tamanho nas Configurações (⚙).

### v2.5.0 — 22/09
- Elementos com o ícone do tipo (as artes do site) nas linhas de Boost, Stone e Fragmento, no talento, no Pokémon da Consulta rápida e na tabela de Boost.
- Emojis que a fonte não desenhava viraram texto limpo.

### v2.4.1 — 21/09
- Tabelas de Boost, Star, Runas, Shiny Rate e Max Broke refeitas em formato de tabela: cabeçalho, linhas zebradas e cores por tier.

### v2.4.0 — 21/09
- **Consulta rápida** com 7 abas: Pokémon, Timers, Task, Times, Medalhas, Tabelas e Vídeos.
- Timers com aviso sonoro (Rocket, Polícia, Boss, Dungeon, dens ou personalizado) que funcionam com a janela fechada.
- Contador de progresso por objetivo na task acompanhada.
- Novas bases `hub_db.json` e `videos_db.json`, geradas por `overlay/build_hub_db.py` e atualizadas todo dia.

### v2.3.0 — 20/09
- Transparência do painel configurável no ⚙.

### v2.2.0 — 20/09
- Consulta de tasks no overlay, a partir das Tasks do Mundo da wiki.

### v2.1.0 e v2.0.0 — 20/09
- Instalador nativo (Inno Setup), que resolveu o erro de DLL.
- Visual arredondado com ícones e leitura mais rápida do tooltip.

## Site

### 24/09
- **Star**: "Pokés necessários" estava contando as etapas (3 para 0→3★). Agora conta certo — cada estrela consome o dobro da anterior, então 0→3★ são 14 Pokémon. Também dá para informar quanto custa 1 DD em kk e ver o custo todo em kk.
- **Sugestões**: página com formulário próprio, que abre uma issue no GitHub do projeto já preenchida (ou copia o texto).
- **Créditos**: bloco "De onde vêm os dados" na página inicial e rodapé citando a Pokédex Pública (Mts Vitor), o guia do Safnaw, o do cabeça do loxas e a wiki oficial.

### 22/09
- **Ícones de tipo** também no overlay (acima).

### 21/09
- **Página inicial**: números do site, destaques, atalhos e vídeos em destaque. O site passa a abrir nela.
- **Menu lateral fixo** na borda esquerda, no estilo da wiki do PXG, com a logo no topo, título da página e botão "☰ Menu" no celular. Correção: a barra agora tem a altura da tela e rola sozinha.
- **Pokédex → Tasks** passou a usar as Tasks do Mundo da wiki (NPC, região, objetivo, recompensa e local).
- Lista e simulador de medalhas ficaram lado a lado na Pokédex.

### 20/09
- **Simulador de medalhas** no estilo do painel do jogo: 10 espaços, 5 presets, link para compartilhar e montagem automática por objetivo. Mostra a porcentagem somada por atributo, com os valores de Bronze do vídeo do Empregolista; o resto é estimativa, marcada com `~`.
- **Tasks do Mundo** como aba própria do site.
- **Wiki** com os 48 guias da wiki oficial e busca; ícones de tipo nos badges.

### Antes disso
- Vídeos: índice com transcrições, busca nas falas, temas e canais.
- Desafios: Bosses de Guild a partir do vídeo do AlastraSz.
- Ferramentas: PokéForge, Critical Catch e download do overlay.
- Correções na tabela de raridade (tiers UR/Legendary/Mythic e Super Rare faltantes).
