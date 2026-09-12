import { useEffect, useState, type ReactNode } from 'react'
import { findPokemon, linkify, spriteUrl, tierRank, TIER_COLORS, typeColor, type Pokemon } from '../lib/data'

/* ---------- basics ---------- */
export const Sprite = ({ p, size = '' }: { p: { id: number | null; shiny: boolean; name: string }; size?: '' | 'sm' | 'lg' }) => {
  const [err, setErr] = useState(false)
  const url = spriteUrl(p)
  if (!url || err) return <div className={`sprite-fallback ${size}`}>?</div>
  return <img className={`sprite ${size}`} src={url} alt={p.name} loading="lazy" onError={() => setErr(true)} />
}

export const TypeBadge = ({ t }: { t: string }) => (t ? <span className="badge type" style={{ background: typeColor(t) }}>{t}</span> : null)
export const TierBadge = ({ t }: { t: string }) =>
  t ? <span className="badge tier" style={{ background: TIER_COLORS[t] ?? '#3f3f46', color: '#fff' }}>{t}</span> : null

export const Search = ({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) => (
  <label className="search">
    <span className="ico">⌕</span>
    <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder ?? 'Buscar…'} />
    {value && <button className="chip" style={{ padding: '2px 8px' }} onClick={() => onChange('')}>✕</button>}
  </label>
)

export const Note = ({ children, warn }: { children: ReactNode; warn?: boolean }) => <div className={`note ${warn ? 'warn' : ''}`}>{children}</div>

export const Linkified = ({ text }: { text: string }) => (
  <>
    {linkify(text).map((part, i) =>
      i % 2 === 1 ? (
        <a key={i} href={part.startsWith('http') ? part : `https://${part}`} target="_blank" rel="noreferrer">{part}</a>
      ) : (
        <span key={i}>{part}</span>
      ),
    )}
  </>
)

export const Imgur = ({ href, label = 'Ver mapa' }: { href: string; label?: string }) =>
  href && href.startsWith('http') ? (
    <a className="btn" style={{ padding: '5px 10px', fontSize: 12 }} href={href} target="_blank" rel="noreferrer">🗺 {label}</a>
  ) : (
    <span className="muted small">{href || '—'}</span>
  )

export const SectionHead = ({ title, sub, right }: { title: string; sub?: string; right?: ReactNode }) => (
  <div className="section-head">
    <div>
      <h2>{title}</h2>
      {sub && <p>{sub}</p>}
    </div>
    {right}
  </div>
)

/* ---------- Pokémon name (clickable, with mini sprite) ---------- */
export const PokeName = ({ name, onOpen }: { name: string; onOpen?: (p: Pokemon) => void }) => {
  const p = findPokemon(name)
  if (!p) return <span>{name}</span>
  return (
    <span className="who" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: onOpen ? 'pointer' : 'default' }} onClick={() => onOpen?.(p)}>
      <Sprite p={p} size="sm" />
      <span style={{ fontWeight: 600 }}>{p.name}</span>
    </span>
  )
}

/* ---------- Pokémon card + modal ---------- */
export const PokeCard = ({ p, onOpen }: { p: Pokemon; onOpen: (p: Pokemon) => void }) => (
  <div className={`poke-card ${p.shiny ? 'shiny' : ''}`} onClick={() => onOpen(p)}>
    <Sprite p={p} />
    <div className="name">{p.name}</div>
    <div className="meta">
      <TierBadge t={p.tier} />
      <TypeBadge t={p.type} />
    </div>
  </div>
)

export const PokeModal = ({ p, onClose, onOpen, onItem }: { p: Pokemon; onClose: () => void; onOpen: (p: Pokemon) => void; onItem?: (item: string) => void }) => {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [onClose])
  const twin = findPokemon(p.shiny ? p.base : `Shiny ${p.base}`)
  // shiny/mega herdam hunt, task e medalha da versão normal (a planilha só registra lá)
  const base = (p.shiny || p.mega) && twin && !twin.shiny ? twin : undefined
  const huntsSrc = Object.keys(p.hunts).length ? p.hunts : base?.hunts ?? {}
  const tasksSrc = p.tasks.length ? p.tasks : base?.tasks ?? []
  const medalSrc = p.medal.buff || p.medal.debuff ? p.medal : base?.medal ?? {}
  const inherited = !!base && !Object.keys(p.hunts).length
  const hunts: [string, string | undefined][] = [
    ['Hunt normal', huntsSrc.normal],
    ['Wildscape (lvl 150+)', huntsSrc.wildscape],
    ['Hoenn (lvl 250+)', huntsSrc.hoenn],
  ]
  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div className="sprite-wrap"><Sprite p={p} size="lg" /></div>
          <div>
            <h2>{p.name}</h2>
            <div className="tags">
              <TierBadge t={p.tier} />
              <TypeBadge t={p.type} />
              {p.shiny && <span className="badge shiny">✦ Shiny</span>}
              {p.mega && <span className="badge mega">Mega</span>}
              {p.id && <span className="badge">#{p.id}</span>}
            </div>
            {twin && (
              <button className="chip" style={{ marginTop: 10 }} onClick={() => onOpen(twin)}>
                Ver {twin.shiny ? '✦ Shiny' : 'versão normal'} →
              </button>
            )}
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">✕</button>
        </div>
        <div className="modal-body">
          <div>
            <h4>Drops</h4>
            {p.drops.length ? (
              <div className="tags">{p.drops.map((d, i) => <span key={i} className="badge item" onClick={() => onItem?.(d)} title="Ver quem mais dropa">{d}</span>)}</div>
            ) : <span className="muted small">Sem registro</span>}
          </div>
          <div>
            <h4>Onde caçar {inherited && <span className="tiny" style={{ textTransform: 'none', letterSpacing: 0 }}>(mesma hunt da versão normal)</span>}</h4>
            <div className="link-list">
              {hunts.some(([, v]) => v) ? hunts.filter(([, v]) => v).map(([l, v]) => (
                <div className="link-row" key={l}><b>{l}</b><Imgur href={v!} /></div>
              )) : <span className="muted small">Sem registro</span>}
            </div>
          </div>
          <div>
            <h4>Task (NPC)</h4>
            <div className="link-list">
              {tasksSrc.length ? tasksSrc.map((t, i) => (
                <div className="link-row" key={i}><b>{t.npc}</b><Imgur href={t.loc} label="Localização" /></div>
              )) : <span className="muted small">Sem task registrada</span>}
            </div>
          </div>
          <div>
            <h4>Medalha</h4>
            {medalSrc.buff || medalSrc.debuff ? (
              <div className="tags">
                {medalSrc.buff && <span className="badge ok">▲ {medalSrc.buff}</span>}
                {medalSrc.debuff && <span className="badge bad">▼ {medalSrc.debuff}</span>}
              </div>
            ) : <span className="muted small">Sem registro</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

export const sortPoke = (a: Pokemon, b: Pokemon) => (a.id ?? 9999) - (b.id ?? 9999) || Number(a.shiny) - Number(b.shiny) || tierRank(a.tier) - tierRank(b.tier)
