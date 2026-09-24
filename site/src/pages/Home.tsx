import { data } from '../lib/data'
import tasksRaw from '../data/tasks.json'
import wikiData from '../data/wiki.json'
import { videos, VideoCard } from './Videos'

type Go = (sec: string, sub?: string) => void

const FEATURED: { ico: string; t: string; d: string; sec: string; sub?: string; hot?: boolean }[] = [
  { ico: '⬇️', t: 'Overlay do PKA GUIDE', d: 'Passe o mouse no item dentro do jogo e veja na hora para que ele serve.', sec: 'ferramentas', sub: 'overlay', hot: true },
  { ico: '🏅', t: 'Simulador de Medalhas', d: 'Monte os 10 emblemas e veja o que sobe e o que cai no personagem.', sec: 'pokedex', sub: 'simulador', hot: true },
  { ico: '📋', t: 'Tasks do Mundo', d: 'Todos os NPCs de task, objetivos, recompensas e onde ficam.', sec: 'tasks' },
  { ico: '🧭', t: 'Times por hunt', d: 'Qual time levar em cada hunt, com e sem T2/T3.', sec: 'times' },
]

const QUICK: { ico: string; t: string; sec: string; sub?: string }[] = [
  { ico: '🔴', t: 'Pokédex', sec: 'pokedex', sub: 'grid' },
  { ico: '🏆', t: 'Tier List', sec: 'pokedex', sub: 'tierlist' },
  { ico: '📍', t: 'Localizações', sec: 'pokedex', sub: 'hunts' },
  { ico: '🎒', t: 'Buscar drop', sec: 'itens', sub: 'drops' },
  { ico: '🏰', t: 'Dungeons e Dens', sec: 'dungeons' },
  { ico: '⚔️', t: 'Ginásios', sec: 'desafios', sub: 'gym' },
  { ico: '🚀', t: 'Rockets', sec: 'desafios', sub: 'rocket' },
  { ico: '⭐', t: 'Sistema de Star', sec: 'sistemas', sub: 'star' },
  { ico: '💥', t: 'Cálculo de dano', sec: 'sistemas', sub: 'damage' },
  { ico: '✨', t: 'Shiny Rate', sec: 'sistemas', sub: 'rates' },
  { ico: '📚', t: 'Guias da Wiki', sec: 'wiki' },
  { ico: '🎬', t: 'Pergunte aos vídeos', sec: 'videos', sub: 'perguntar' },
]

const SOURCES: { t: string; by: string; what: string; url: string }[] = [
  { t: 'Pokédex Pública PokeAlliance', by: 'planilha do Mts Vitor', what: 'Pokémon, drops, tiers, itens, dens, dungeons, ginásios, rockets, star, runas e boost', url: 'https://docs.google.com/spreadsheets/d/1GCH3PmFKQrBj7AA51hgqfg6Q2SrvNgrNlxgIidVeTMU' },
  { t: 'Guia de times por hunt', by: 'planilha do Safnaw', what: 'tanks, DPS e Smeargle de cada elemento e hunt', url: 'https://docs.google.com/spreadsheets/d/1JcYTCkuKiYK6OcEx9CC-LxRLsPRAPvKaHza-cZuEh1s' },
  { t: 'Times sem T2/T3', by: 'documento do cabeça do loxas', what: 'times para quem está começando no 350', url: 'https://docs.google.com/document/d/1L1-sju28TVQMdjtD-xF-3jAK4reTX-RSuMCGAg-tHkg' },
  { t: 'Wiki oficial do PokeAlliance', by: 'equipe do jogo', what: '48 guias e as Tasks do Mundo', url: 'https://wiki.pokealliance.com' },
  { t: 'Vídeos da comunidade', by: 'canais do YouTube', what: 'transcrições usadas na busca e nos vídeos de referência', url: 'https://pkaguide.vercel.app/#/videos/canais' },
]

export default function Home({ go }: { go: Go }) {
  const tasks = (tasksRaw as unknown as { tasks: unknown[] }).tasks.length
  const wiki = (wikiData as { pages: unknown[] }).pages.length
  const pokes = data.pokemon.filter((p) => !p.shiny).length
  const items = Object.keys(data.items).length
  const stats: { n: number; l: string; sec: string; sub?: string }[] = [
    { n: pokes, l: 'Pokémon', sec: 'pokedex' }, { n: items, l: 'Itens com drop', sec: 'itens' },
    { n: tasks, l: 'Tasks', sec: 'tasks' }, { n: data.dens.length, l: 'Dens', sec: 'dungeons', sub: 'dens' },
    { n: wiki, l: 'Guias da wiki', sec: 'wiki' }, { n: videos.length, l: 'Vídeos indexados', sec: 'videos' },
  ]
  const top = [...videos].sort((a, b) => b.views - a.views).slice(0, 3)

  return (
    <div className="home">
      <section className="home-welcome">
        <h2>Bem-vindo ao <span>PKA GUIDE</span></h2>
        <p>O guia da comunidade do PokeAlliance: tudo da Pokédex Pública, da wiki oficial e dos melhores vídeos, organizado e atualizado todo dia. Use a busca lá em cima ou escolha um atalho abaixo.</p>
      </section>

      <div className="home-stats">
        {stats.map((s) => (
          <button key={s.l} className="home-stat" onClick={() => go(s.sec, s.sub)}>
            <b>{s.n.toLocaleString('pt-BR')}</b><span>{s.l}</span>
          </button>
        ))}
      </div>

      <h3 className="home-h">Destaques</h3>
      <div className="home-feat">
        {FEATURED.map((f) => (
          <button key={f.t} className={`home-card ${f.hot ? 'hot' : ''}`} onClick={() => go(f.sec, f.sub)}>
            <span className="home-ico">{f.ico}</span>
            <b>{f.t}</b>
            <span>{f.d}</span>
          </button>
        ))}
      </div>

      <h3 className="home-h">Atalhos</h3>
      <div className="home-quick">
        {QUICK.map((q) => (
          <button key={q.t} className="home-q" onClick={() => go(q.sec, q.sub)}><span>{q.ico}</span>{q.t}</button>
        ))}
      </div>

      <h3 className="home-h">Vídeos em destaque</h3>
      <div className="home-videos">{top.map((v) => <VideoCard key={v.id} v={v} compact />)}</div>

      <h3 className="home-h">De onde vêm os dados</h3>
      <div className="home-src">
        {SOURCES.map((s) => (
          <a key={s.t} className="home-srccard" href={s.url} target="_blank" rel="noreferrer">
            <b>{s.t}</b>
            <span>{s.by}</span>
            <small>{s.what}</small>
          </a>
        ))}
      </div>

      <div className="home-sug">
        <span>💡 Tem ideia para o site ou achou algo errado?</span>
        <button className="btn btn-primary" onClick={() => go('sugestoes')}>Mandar sugestão</button>
      </div>
    </div>
  )
}
