import guiaRaw from '../data/rockets_guide.json'
import { useState } from 'react'
import { data, type Pokemon, type Team } from '../lib/data'
import { Imgur, Linkified, Note, PokeName, Search, SectionHead } from '../components/ui'
import { VideoRefs } from './Videos'
import GuildBoss from './GuildBoss'

type Props = { sub: string; onOpen: (p: Pokemon) => void }

export default function Desafios({ sub, onOpen }: Props) {
  if (sub === 'guildboss') return <GuildBoss onOpen={onOpen} />
  const topic = ({ rocket: 'rocket', police: 'policia', hazard: 'dens', linked: 'linked', bh: 'bh' } as Record<string, string>)[sub] ?? 'gym'
  return <><DesafiosInner sub={sub} onOpen={onOpen} /><VideoRefs topic={topic} /></>
}

const guia = guiaRaw as unknown as {
  source: string; author: string; title: string; intro: string[]
  ranks: { S: string[]; A: string[]; B: string[]; nota: string }
  mecanicas: { t: string; d: string }[]
  npcs: { name: string; andar: number; dificuldade: string; tips: string[]; recs: { npc: string; use: string }[] }[]
  police: { tips: string[] }
}
const nk = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim()
const guiaPorNpc = new Map(guia.npcs.map((n) => [nk(n.name), n]))

/** guia em vídeo do AlastraSz, mostrado acima dos times */
function GuiaRockets({ police }: { police?: boolean }) {
  return (
    <div className="card guia" style={{ marginBottom: 18 }}>
      <div className="card-title">
        <h3>Guia do {guia.author}</h3>
        <a className="chip" style={{ marginLeft: 'auto' }} href={guia.source} target="_blank" rel="noreferrer">▶ ver o vídeo</a>
      </div>
      <ul className="guia-list">
        {(police ? guia.police.tips : guia.intro).map((x) => <li key={x}>{x}</li>)}
      </ul>
      {!police && (
        <>
          <div className="guia-ranks">
            {([['S', guia.ranks.S], ['A', guia.ranks.A], ['B', guia.ranks.B]] as const).map(([r, list]) => (
              <div key={r} className={`guia-rank r${r}`}>
                <b>Rank {r}</b>
                <span>{list.join(', ')}</span>
              </div>
            ))}
          </div>
          <p className="muted tiny" style={{ margin: '4px 2px 12px' }}>{guia.ranks.nota}</p>
          <div className="guia-mec">
            {guia.mecanicas.map((m) => (
              <div key={m.t}><b>{m.t}</b><span>{m.d}</span></div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function DesafiosInner({ sub, onOpen }: Props) {
  if (sub === 'rocket') return <Teams title="Rockets" sub="Pokémon de cada membro da equipe Rocket, o counter da planilha e o que o guia do AlastraSz recomenda." data={data.rocket.teams} note={data.rocket.note} extra={data.rocket.giovanniNote} onOpen={onOpen} guia />
  if (sub === 'police') return <Teams title="Polícia" sub="Pokémon de cada oficial e os tipos recomendados pra enfrentar." data={data.police.teams} note={data.police.note} onOpen={onOpen} recIsType guiaPolice />
  if (sub === 'hazard') return <Hazard />
  if (sub === 'linked') return <Linked onOpen={onOpen} />
  if (sub === 'bh') return <BH />
  return <Gyms onOpen={onOpen} />
}

function Gyms({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  return (
    <>
      <SectionHead title="Ginásios (Kanto)" sub="Tasks pra liberar cada ginásio, dungeon e o time do líder." />
      <div className="grid grid-2">
        {data.gym.cities.map((g) => (
          <div className="card" key={g.city}>
            <div className="card-title"><h3>{g.city}</h3><span style={{ marginLeft: 'auto' }}><Imgur href={g.dungeon} label="Dungeon" /></span></div>
            <div className="tags" style={{ marginBottom: 12 }}>
              {g.tasks.map((t) => <span key={t} className="badge shiny">Task: {t}</span>)}
            </div>
            <h4 className="muted tiny" style={{ margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Time do líder</h4>
            <div className="tags">{g.leader.map((l, i) => <span key={i} className="badge" style={{ padding: '2px 8px 2px 2px' }}><PokeName name={l} onOpen={onOpen} /></span>)}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 18 }}><Note><Linkified text={data.gym.note} /></Note></div>
    </>
  )
}

function Teams({ title, sub, data: teams, note, extra, onOpen, recIsType, guia: comGuia, guiaPolice }: { title: string; sub: string; data: Team[]; note: string; extra?: string; onOpen: (p: Pokemon) => void; recIsType?: boolean; guia?: boolean; guiaPolice?: boolean }) {
  const [q, setQ] = useState('')
  const s = q.trim().toLowerCase()
  const list = teams.filter((t) => !s || t.name.toLowerCase().includes(s) || t.fights.some((f) => f.npc.toLowerCase().includes(s) || f.rec.toLowerCase().includes(s)))
  return (
    <>
      <SectionHead title={title} sub={sub} />
      <div className="toolbar"><Search value={q} onChange={setQ} placeholder="Nome do NPC ou Pokémon…" /></div>
      {(comGuia || guiaPolice) && <GuiaRockets police={guiaPolice} />}
      <Note><Linkified text={note} /></Note>
      <div className="grid grid-3">
        {list.map((t) => (
          <div className="card" key={t.name} style={t.name === 'GIOVANNI' ? { borderColor: 'rgba(249,115,22,0.5)' } : {}}>
            <div className="card-title">
              <h3 style={{ letterSpacing: '0.04em' }}>{t.name}</h3>
              {comGuia && guiaPorNpc.get(nk(t.name)) && (
                <span className="badge" style={{ marginLeft: 'auto' }}>
                  {guiaPorNpc.get(nk(t.name))!.andar}º andar · {guiaPorNpc.get(nk(t.name))!.dificuldade}
                </span>
              )}
            </div>
            {t.name === 'GIOVANNI' && extra && <p className="muted small" style={{ marginTop: 0 }}>{extra}</p>}
            <div className="vs-row" style={{ borderBottom: '1px solid var(--line)', paddingBottom: 6 }}>
              <span className="tiny muted">NPC</span><span className="vs"></span><span className="tiny muted" style={{ textAlign: 'right' }}>Recomendado</span>
            </div>
            {t.fights.map((f, i) => (
              <div className="vs-row" key={i}>
                <span className="who"><PokeName name={f.npc} onOpen={onOpen} /></span>
                <span className="vs">VS</span>
                <span className="who right">{recIsType ? <span className="badge ok">{f.rec}</span> : <PokeName name={f.rec} onOpen={onOpen} />}</span>
              </div>
            ))}
            {comGuia && guiaPorNpc.get(nk(t.name)) && (
              <div className="guia-npc">
                {guiaPorNpc.get(nk(t.name))!.recs.map((r) => (
                  <p key={r.npc}><b>{r.npc}:</b> {r.use}</p>
                ))}
                {guiaPorNpc.get(nk(t.name))!.tips.map((x) => <p key={x} className="muted">• {x}</p>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  )
}

function Hazard() {
  return (
    <>
      <SectionHead title="Hazard Tasks (Hoenn)" sub="NPC, localização e o que cada task pede." />
      <div className="table-wrap">
        <table>
          <thead><tr><th>NPC</th><th>Local</th><th>Task</th></tr></thead>
          <tbody>
            {data.hazard.map((h) => (
              <tr key={h.npc}>
                <td><b>{h.npc}</b></td>
                <td><Imgur href={h.loc} label="Mapa" /></td>
                <td style={{ whiteSpace: 'normal' }}><div className="tags">{h.task.split(',').map((t) => <span key={t} className="badge shiny">{t.trim()}</span>)}</div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Linked({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [type, setType] = useState('')
  const list = data.linked.tasks.filter((t) => !type || t.huntType === type)
  return (
    <>
      <SectionHead title="Linked Tasks" sub="Sequência de tasks encadeadas. Completar uma libera a próxima. Aperte Ctrl+L no jogo pra ver as suas." />
      <div className="toolbar">
        {['', 'Normal', 'Wild'].map((t) => <button key={t} className={`chip orange ${type === t ? 'active' : ''}`} onClick={() => setType(t)}>{t || 'Todas'}</button>)}
        <span className="count">{list.length} tasks</span>
      </div>
      <Note><Linkified text={data.linked.note} /></Note>
      <div className="table-wrap">
        <table>
          <thead><tr><th>#</th><th className="num">Qtd</th><th>Pokémon</th><th>Hunt</th><th>Mapa</th><th className="num">Kills/h</th></tr></thead>
          <tbody>
            {list.map((t, i) => (
              <tr key={i}>
                <td className="muted">{i + 1}</td>
                <td className="num"><b>{t.qty.toLocaleString('pt-BR')}</b></td>
                <td><PokeName name={t.pokemon} onOpen={onOpen} /></td>
                <td><span className={`badge ${t.huntType === 'Wild' ? 'mega' : ''}`}>{t.huntType}</span></td>
                <td><Imgur href={t.hunt} /></td>
                <td className="num">{t.killsPerHour ? t.killsPerHour.toLocaleString('pt-BR') : <span className="muted">—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function BH() {
  return (
    <>
      <SectionHead title="Brotherhood (BH)" sub="Como iniciar e como pegar os contratos." />
      <div className="card"><p style={{ margin: 0, whiteSpace: 'pre-line', lineHeight: 1.7 }}><Linkified text={data.bh} /></p></div>
    </>
  )
}
