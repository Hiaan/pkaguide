import { useMemo, useState } from 'react'
import { data, typeColor, type Pokemon } from '../lib/data'
import { Note, PokeName, Search, SectionHead } from '../components/ui'
import { VideoRefs } from './Videos'

type Props = { sub: string; onOpen: (p: Pokemon) => void; item: string; setItem: (i: string) => void }

export default function Itens({ sub, onOpen, item, setItem }: Props) {
  const [q, setQ] = useState('')

  if (sub === 'talents') return <><Talents onOpen={onOpen} /><VideoRefs topic="talentos" /></>
  if (sub === 'boost') return <><Boost /><VideoRefs topic="boost" /></>

  // ---- Buscar drop ----
  const items = Object.keys(data.items).sort()
  const s = q.trim().toLowerCase()
  const matches = s ? items.filter((i) => i.includes(s)) : []
  const sel = item && data.items[item] ? item : matches.length === 1 ? matches[0] : ''
  return (
    <>
      <SectionHead title="Buscar item (drops)" sub="Digite o nome de um item e veja todos os Pokémon que dropam ele. Substitui a aba 'Search' da planilha, sem limite de pessoas usando." />
      <div className="toolbar">
        <Search value={q} onChange={(v) => { setQ(v); setItem('') }} placeholder="Ex: moon topknot, fire stone, straw…" />
        <span className="count">{items.length} itens catalogados</span>
      </div>
      {!s && !sel && (
        <Note>Comece a digitar o nome do item. Dica: os itens também são clicáveis dentro da ficha de cada Pokémon na Pokédex.</Note>
      )}
      {s && !sel && (
        <div className="tags" style={{ marginBottom: 18 }}>
          {matches.slice(0, 80).map((i) => <span key={i} className="badge item" onClick={() => { setQ(i); setItem(i) }}>{i}</span>)}
          {!matches.length && <span className="muted">Nenhum item com esse nome</span>}
        </div>
      )}
      {sel && (
        <div className="card">
          <div className="card-title"><h3>Pokémon que dropam <span style={{ color: 'var(--orange)' }}>{sel}</span></h3><span className="muted small">{data.items[sel].length}</span></div>
          <div className="grid grid-4">
            {data.items[sel].map((n) => (
              <div className="link-row" key={n}><PokeName name={n} onOpen={onOpen} /></div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function Talents({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const types = [...new Set(data.talents.map((t) => t.type))]
  const s = q.trim().toLowerCase()
  const list = data.talents.filter((t) => (!type || t.type === type) && (!s || t.item.toLowerCase().includes(s) || t.pokemon.toLowerCase().includes(s) || t.buff.toLowerCase().includes(s)))
  const grouped = useMemo(() => {
    const m = new Map<string, typeof list>()
    for (const t of list) { const k = `${t.type} #${t.n}`; m.set(k, [...(m.get(k) ?? []), t]) }
    return [...m.entries()]
  }, [list])
  return (
    <>
      <SectionHead title="PokeTalents" sub="Quais itens (e quantos) cada talento pede, com o buff que ele dá. Busque pelo item, pelo Pokémon que dropa ou pelo efeito." />
      <div className="toolbar">
        <Search value={q} onChange={setQ} placeholder="Item, Pokémon ou buff…" />
        <select className="select" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">Todos os tipos</option>
          {types.map((t) => <option key={t}>{t}</option>)}
        </select>
        <span className="count">{list.length} itens</span>
      </div>
      <div className="grid grid-2">
        {grouped.map(([k, l]) => (
          <div className="card" key={k}>
            <div className="card-title">
              <span className="badge type" style={{ background: typeColor(l[0].type) }}>{l[0].type}</span>
              <h3>Talento #{l[0].n}</h3>
            </div>
            <p className="small" style={{ margin: '0 0 12px', color: '#d4d4d8', lineHeight: 1.5 }}>{l[0].buff}</p>
            <div className="table-wrap" style={{ boxShadow: 'none' }}>
              <table>
                <thead><tr><th>Item</th><th>Vem de</th><th className="num">Qtd</th></tr></thead>
                <tbody>
                  {l.map((t, i) => (
                    <tr key={i}>
                      <td>{t.item}</td>
                      <td>{t.pokemon ? <PokeName name={t.pokemon} onOpen={onOpen} /> : <span className="muted">—</span>}</td>
                      <td className="num"><b>{t.qty}</b></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
      {!list.length && <div className="empty">Nada encontrado</div>}
    </>
  )
}

function Boost() {
  const [sel, setSel] = useState(data.boost[0]?.type ?? '')
  const b = data.boost.find((x) => x.type === sel)
  const f = data.fragments
  return (
    <>
      <SectionHead title="Boost por tipo" sub="Itens que já apareceram na máquina de boost para cada tipo (não são os itens do dia). Abaixo, quanto fragmento cada faixa de nível pede." />
      <div className="tags" style={{ marginBottom: 18 }}>
        {data.boost.map((x) => (
          <button key={x.type} className={`chip ${sel === x.type ? 'active' : ''}`} style={sel === x.type ? { background: typeColor(x.type) } : {}} onClick={() => setSel(x.type)}>{x.type}</button>
        ))}
      </div>
      {b && (
        <div className="grid grid-2" style={{ marginBottom: 20 }}>
          <div className="card">
            <div className="card-title"><span className="badge type" style={{ background: typeColor(b.type) }}>{b.type}</span><h3>Itens de boost</h3></div>
            <div className="tags" style={{ marginBottom: 12 }}>
              <span className="badge shiny">{b.fragment}</span>
              <span className="badge mega">{b.stone}</span>
            </div>
            <div className="tags">{b.items.map((i) => <span key={i} className="badge item" style={{ cursor: 'default' }}>{i}</span>)}</div>
          </div>
          <div className="card">
            <h3>Fragmentos por nível de boost</h3>
            <p className="muted small" style={{ marginTop: 0 }}>{f.note}</p>
            <div className="table-wrap" style={{ boxShadow: 'none' }}>
              <table>
                <thead><tr><th>Nível</th><th className="num">Mín</th><th className="num">Média</th><th className="num">Máx</th></tr></thead>
                <tbody>
                  {f.brackets.map((br, i) => (
                    <tr key={br}><td><b>{br}</b></td><td className="num">{f.min[i]}</td><td className="num">{f.avg[i]}</td><td className="num">{f.max[i]}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
