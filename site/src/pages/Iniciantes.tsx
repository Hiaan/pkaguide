import { Note, PokeName, SectionHead, TierBadge, TypeIcon } from '../components/ui'
import type { Pokemon } from '../lib/data'

type Go = (sec: string, sub?: string) => void

const VIDEO = 'BH1X39oMYGQ'
const yt = (t = 0) => `https://www.youtube.com/watch?v=${VIDEO}${t ? `&t=${t}s` : ''}`
const fmt = (t: number) => `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`
const IMG = (n: string) => `/guides/iniciantes/${n}.jpg`

/* ---------- os 8 Pokémon do vídeo ---------- */
type Pick = {
  name: string          // nome na Pokédex do site
  types: string[]
  tier: string
  como: string          // como conseguir
  caca: string[]        // tipos de hunt que ele resolve
  nota: string
  t: number             // minuto do vídeo
  print?: string
}

const PICKS: Pick[] = [
  {
    name: 'Arcanine', types: ['Fire'], tier: 'T2', t: 303, print: 'pokedex-arcanine',
    como: 'Capture um Growlithe e evolua. Não capture o Arcanine direto: Pokémon normal tem pouco espaço de broke.',
    caca: ['Bug', 'Grass', 'Ice', 'Steel'],
    nota: 'Só com ele já dá para caçar quatro elementos diferentes. Na Pokédex do jogo dá para ver onde o Arcanine aparece abaixo e acima do level 150.',
  },
  {
    name: 'Poliwrath', types: ['Water', 'Fighting'], tier: 'T3', t: 337,
    como: 'Capture um Poliwag e evolua.',
    caca: ['Ground', 'Rock', 'Fire', 'Dark', 'Normal'],
    nota: 'Moveset misto: bate tudo o que Água e Lutador batem. Para Normal precisa de um talento de lutador e de um held de boost. Tem um pouco menos de força, mas traz skill defensiva, stun em área e um combo bom. Se sobrar vaga para Normal, a alternativa é o Machamp, que não tem stun nem silence.',
  },
  {
    name: 'Steelix', types: ['Ground', 'Steel'], tier: 'T2', t: 488,
    como: 'Compre um Onix e uma Metal Coat e evolua.',
    caca: ['Poison', 'Electric', 'Steel', 'Rock', 'Fire'],
    nota: 'Para o Loxas é um dos MVPs do jogo. Em level 150 Fogo ainda é difícil, mas de uns 200 em diante vale testar. Contra Pokémon que voam, como o Charizard, a terra não pega.',
  },
  {
    name: 'Mimikyu', types: ['Ghost', 'Fairy'], tier: 'T2', t: 580, print: 'pokedex-mimikyu',
    como: 'Não tem atalho: precisa ir atrás dele nas hunts.',
    caca: ['Dark', 'Fighting', 'Dragon'],
    nota: 'Outro MVP segundo o vídeo. Apanha de Ghost e de Metal, mas toma dano neutro de Dark, e por isso rende tanto nas hunts Dark.',
  },
  {
    name: 'Shiny Persian', types: ['Dark'], tier: 'T2', t: 650,
    como: 'É o mais trabalhoso: precisa caçar Persian até vir o shiny. Para um T2 o limite de broke fica perto de 900 balls, então não chega a ser difícil.',
    caca: ['Ghost', 'Psychic'],
    nota: 'Shiny de Normal serve de coringa no time: o Persian usa golpes Dark. Como as hunts de Ghost e Psychic não são as mais procuradas, é o de menor prioridade da lista.',
  },
  {
    name: 'Omastar', types: ['Rock', 'Water'], tier: 'T2', t: 720, print: 'pokedex-omastar',
    como: 'Capture um Omanyte e evolua, é fácil.',
    caca: ['Fire', 'Ice', 'Flying', 'Bug'],
    nota: 'Da categoria "Exploder" (o equivalente ao speedster da PXG): skill que acelera, skill defensiva, protect e combo em área. Foi pensado para Fogo, e bate também tudo o que Pedra e Água batem. Ajuda em quests em que se bate no protect e solta o combo.',
  },
  {
    name: 'Pachirisu', types: ['Electric'], tier: 'T2', t: 841,
    como: 'Não tem atalho: precisa ir atrás dele nas hunts.',
    caca: ['Water', 'Flying'],
    nota: 'Pouca coisa a explicar: Elétrico bate em Água e em Voador. O Loxas acha a tabela defensiva do jogo meio quebrada, então não vale se prender a ela.',
  },
  {
    name: 'Shiny Magneton', types: ['Electric', 'Steel'], tier: 'T2', t: 874,
    como: 'Quase todo mundo que sobe até o 150 já tem um. Se não tiver, o Magneton normal serve.',
    caca: ['Fairy', 'Rock', 'Ice'],
    nota: 'Resolve Fada e tudo o que Metal bate, como Pedra. É fácil de arrumar.',
  },
]

const TYPES = ['Normal', 'Fighting', 'Flying', 'Poison', 'Ground', 'Rock', 'Bug', 'Ghost', 'Steel', 'Fire', 'Water', 'Grass', 'Electric', 'Psychic', 'Ice', 'Dragon', 'Dark', 'Fairy']

const CHAPTERS: [number, string][] = [
  [0, 'Introdução'], [123, 'A lista dos 8'], [217, 'Pokédex do jogo'], [303, 'Arcanine'], [337, 'Poliwrath'],
  [488, 'Steelix'], [580, 'Mimikyu'], [650, 'Shiny Persian'], [720, 'Omastar'], [841, 'Pachirisu'],
  [874, 'Shiny Magneton'], [903, 'E os outros elementos?'], [956, 'Sites de apoio'], [1140, 'Hunt Finder'],
  [1235, 'Mapa e instâncias'], [1364, 'Itens de boost do dia'], [1405, 'Fazer o inverso'], [1514, 'Shiny Ditto e talentos'],
]

const Credit = () => (
  <div className="ini-credit">
    <span>🎬 Baseado no vídeo <b>MELHORES POKEMONS PARA INICIANTES NO PKA</b>, do <b>Canal Do Loxas</b>. Os textos aqui são um resumo; os prints vêm do próprio vídeo.</span>
    <a className="chip" href={yt()} target="_blank" rel="noreferrer">▶ Assistir no YouTube</a>
  </div>
)

const Shot = ({ img, title, children, t }: { img: string; title: string; children: React.ReactNode; t?: number }) => (
  <figure className="ini-shot">
    <a href={IMG(img)} target="_blank" rel="noreferrer"><img src={IMG(img)} alt={title} loading="lazy" /></a>
    <figcaption>
      <b>{title}</b>
      <span>{children}</span>
      {t != null && <a href={yt(t)} target="_blank" rel="noreferrer">▶ ver no vídeo ({fmt(t)})</a>}
    </figcaption>
  </figure>
)

/* ---------- página 1: os Pokémon ---------- */
function Lista({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  return (
    <>
      <SectionHead title="Melhores Pokémon para iniciantes" sub="Oito Pokémon fáceis de conseguir que, juntos, deixam você caçar quase todos os respawns do jogo a partir do level 150, sem precisar de um aporte grande." />
      <Credit />

      <div className="ini-intro card">
        <p>
          A ideia do vídeo é simples: você não precisa gastar muito nem quebrar a cabeça para descobrir o que usar. Com um time pequeno e barato,
          dá para jogar quase tudo da região com level de caveira 150 ou mais. O mais importante, segundo o Loxas, é aprender <b>como descobrir onde usar cada um</b>,
          e isso está na aba <b>Onde e como caçar</b>.
        </p>
        <p className="muted small" style={{ marginBottom: 0 }}>
          Como ganhar dinheiro fica de fora: o vídeo trata só de o que usar para caçar um shiny ou montar o time que você quer.
        </p>
      </div>

      <div className="ini-slides">
        <Shot img="lista" title="A lista">Os oito escolhidos, ao lado da tabela de tipos do jogo.</Shot>
        <Shot img="relacoes" title="Quem caça o quê" t={830}>As linhas ligam cada Pokémon aos tipos que ele resolve, com o tier anotado ao lado.</Shot>
      </div>

      <div className="grid grid-2 ini-cards">
        {PICKS.map((p, i) => (
          <article className="card ini-card" key={p.name}>
            <div className="ini-card-head">
              <span className="ini-n">{i + 1}</span>
              <div className="ini-name"><PokeName name={p.name} onOpen={onOpen} /></div>
              <TierBadge t={p.tier} />
              <span className="ini-types">{p.types.map((t) => <TypeIcon key={t} t={t} size={20} />)}</span>
            </div>
            <div className="ini-row"><span>Como conseguir</span><p>{p.como}</p></div>
            <div className="ini-row">
              <span>Caça</span>
              <div className="ini-chips">
                {p.caca.map((t) => <span key={t} className="ini-chip"><TypeIcon t={t} size={16} />{t}</span>)}
              </div>
            </div>
            <p className="ini-nota">{p.nota}</p>
            {p.print && <a href={IMG(p.print)} target="_blank" rel="noreferrer"><img className="ini-print" src={IMG(p.print)} alt={`Pokédex: ${p.name}`} loading="lazy" /></a>}
            <a className="ini-yt" href={yt(p.t)} target="_blank" rel="noreferrer">▶ trecho no vídeo ({fmt(p.t)})</a>
          </article>
        ))}
      </div>

      <h3 className="ini-h">Cobertura por elemento</h3>
      <p className="muted small" style={{ marginTop: 0 }}>Montada a partir do que o vídeo diz que cada um caça.</p>
      <div className="ini-cover">
        {TYPES.map((t) => {
          const who = PICKS.filter((p) => p.caca.includes(t))
          return (
            <div key={t} className={`ini-cov ${who.length ? '' : 'none'}`}>
              <span className="ini-cov-t"><TypeIcon t={t} size={18} />{t}</span>
              <span className="ini-cov-w">{who.length ? who.map((p) => p.name).join(', ') : 'sem opção na lista'}</span>
            </div>
          )
        })}
      </div>
      <Note>
        O Loxas lembra os buracos da lista: <b>Voador puro</b> e <b>Inseto</b> não têm um escolhido (o Arcanine e o Omastar ainda batem em Inseto).
        Para Veneno o vídeo cita o <b>Muk</b>, que é fácil de montar. Para qualquer outro caso, procure por tier e elemento na Pokédex, como mostra a aba Onde e como caçar.
      </Note>

      <h3 className="ini-h">Capítulos do vídeo</h3>
      <div className="ini-chapters">
        {CHAPTERS.map(([t, l]) => (
          <a key={t} href={yt(t)} target="_blank" rel="noreferrer"><b>{fmt(t)}</b> {l}</a>
        ))}
      </div>
    </>
  )
}

/* ---------- página 2: onde e como caçar ---------- */
function Hunts({ go }: { go: Go }) {
  return (
    <>
      <SectionHead title="Onde e como caçar" sub="Como descobrir quais hunts o seu Pokémon resolve e como chegar até elas, sem decorar nada." />
      <Credit />

      <ol className="ini-steps">
        <li>
          <Shot img="pokedex-arcanine" title="1. Pokédex do jogo" t={217}>
            Configure o atalho em <b>Ctrl+K → action bar → Pokédex</b>. Pesquise o Pokémon e tire as marcações de instância e de dungeon para ver só os respawns normais.
            Dá para separar o que fica abaixo e acima do level 150 e ver se ele aparece em rotação ou em instância.
          </Shot>
        </li>
        <li>
          <Shot img="hunt-finder" title="2. Hunt Finder" t={1140}>
            Fica na barra de cima do jogo e filtra por nível, Pokémon usado, elemento-alvo, tier do shiny, zona (normal, wildcard, primal) e continente.
            Exemplo do vídeo: escolher o elemento Grass e ver todas as hunts de planta de Wildscape. No dia da gravação o filtro por tier ainda estava com defeito.
          </Shot>
        </li>
        <li>
          <Shot img="hunt-reverso" title="3. Fazer o inverso: o que o meu Pokémon caça?" t={1405}>
            Coloque o seu Pokémon no campo <b>Pokémon usado</b> e o Hunt Finder lista tudo o que ele consegue caçar (no exemplo, o Poliwrath).
            Ele não leva em conta a tabela de fraquezas, então use o bom senso: um Pokémon de Água e Lutador não se dá bem com tipos duplos de Pedra ou Voador, por exemplo.
          </Shot>
        </li>
        <li>
          <Shot img="mapa" title="4. Achar o lugar no mapa" t={1235}>
            <b>Ctrl+Tab</b> abre o mapa. Escolha a hunt no Hunt Finder, clique em <b>Show enter place</b> e aperte Ctrl+Tab: o ponto fica marcado, inclusive a entrada das instâncias.
            Se o seu minimapa estiver incompleto, baixe o arquivo no Discord do PKA (menu da esquerda) e coloque na pasta do minimapa.
          </Shot>
        </li>
        <li>
          <Shot img="sites" title="5. Chegar lá e conferir os dados" t={956}>
            O vídeo deixa três sites de apoio: a wiki do jogo, o Critical Catch e o PKA GUIDE. Para o caminho até a hunt, use a Pokédex Pública do Mts Vitor ou o guia daqui.
            Procurando por <b>tier e elemento</b> (ex.: T2 de Inseto) você encontra opções que não conhecia.
          </Shot>
        </li>
      </ol>

      <div className="ini-links">
        <button className="btn" onClick={() => go('pokedex', 'hunts')}>📍 Localizações no PKA GUIDE</button>
        <button className="btn" onClick={() => go('pokedex', 'tierlist')}>🏆 Tier List</button>
        <button className="btn" onClick={() => go('ferramentas', 'criticalcatch')}>🧰 Critical Catch</button>
      </div>
    </>
  )
}

/* ---------- página 3: talentos e boost ---------- */
function Dicas({ go }: { go: Go }) {
  return (
    <>
      <SectionHead title="Talentos, boost e Shiny Ditto" sub="O que fazer logo depois de pegar o level 150 para que esses Pokémon aguentem as hunts." />
      <Credit />

      <div className="ini-tips">
        <div className="card">
          <h3>Assim que chegar no 150</h3>
          <ul>
            <li>Compre um <b>held de boost</b> (T1, T2 ou T3) e coloque no Pokémon.</li>
            <li>Abra os talentos com <b>Ctrl+T</b> e faça os mais simples de <b>defesa</b> e de <b>ataque</b>. Segundo o vídeo, a vida do Pokémon melhora muito.</li>
            <li>Pokémon de <b>dupla tipagem</b> precisa dos dois talentos de defesa. Exemplo: o Poliwrath pede o de Lutador e o de Água.</li>
          </ul>
        </div>
        <div className="card">
          <h3>Vale a pena fazer os talentos?</h3>
          <ul>
            <li>Os primeiros de cada elemento são baratos. O de Água começa matando Poliwag (defesa), depois Horsea, e matar Poliwag shiny dá ataque; o de Lutador começa no Mankey.</li>
            <li>Não precisa fazer todos: alguns são caros demais. Mas até os iniciais ajudam em tudo, inclusive em ginásio (ex.: talento de Terra para o ginásio de Terra).</li>
          </ul>
        </div>
        <div className="card">
          <h3>Shiny Ditto</h3>
          <p>O vídeo fala que o Shiny Ditto resolve cerca de 99% dos problemas. Defensivamente você usa o talento de <b>Normal</b>; no ataque vale o talento do elemento em que ele se transformou.</p>
        </div>
      </div>

      <div className="ini-slides">
        <Shot img="boost" title="Itens de boost do dia" t={1364}>
          No TC você vê quais itens de boost estão valendo no dia, separados por elemento (o de Água, por exemplo, muda todo dia). Ótimo para escolher o que caçar hoje.
        </Shot>
        <Shot img="talentos" title="Talentos do jogador" t={1550}>
          A tela de Player Talents, aqui na aba de Água: cada degrau dá defesa ou ataque contra o tipo.
        </Shot>
      </div>

      <div className="ini-links">
        <button className="btn" onClick={() => go('itens', 'talents')}>✨ PokeTalents no PKA GUIDE</button>
        <button className="btn" onClick={() => go('itens', 'boost')}>🎒 Boost</button>
        <button className="btn" onClick={() => go('ferramentas', 'criticalcatch')}>🧰 Critical Catch</button>
      </div>
    </>
  )
}

export default function Iniciantes({ sub, onOpen, go }: { sub: string; onOpen: (p: Pokemon) => void; go: Go }) {
  if (sub === 'hunts') return <Hunts go={go} />
  if (sub === 'dicas') return <Dicas go={go} />
  return <Lista onOpen={onOpen} />
}
