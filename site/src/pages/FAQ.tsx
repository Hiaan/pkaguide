import { useState } from 'react'
import { data } from '../lib/data'
import { Linkified, Search, SectionHead } from '../components/ui'
import { VideoRefs, videoRefs } from './Videos'

const FAQ_TOPIC: Record<string, string> = { star: 'star', boost: 'boost', up: 'up', 'ilhas laranja': 'hunt', ditto: 'shiny', pesca: 'pesca', fundir: 'helds', held: 'helds', medalha: 'medalhas', hunt: 'hunt', 'maxima media': 'shiny', linked: 'linked', mega: 'dens', vip: 'vip', legendary: 'tier', caveira: 'hunt', bh: 'bh', balls: 'shiny', hoenn: 'hoenn', hazard: 'dens', orb: 'talentos', tierlist: 'tier', talents: 'talentos', rockets: 'rocket', 'ginasios gyms': 'gym', brokes: 'shiny', porygon: 'porygon', 'shard dg': 'dungeon', prey: 'prey', expedition: 'dungeon', passe: 'vip', cupom: 'vip', 'treino treinar punching': 'up', share: 'up', vender: 'dinheiro', carteira: 'dinheiro' }
const topicFor = (q: string) => FAQ_TOPIC[q] ?? Object.keys(videoRefs.topics).find((k) => q.split(' ').includes(k))

export default function FAQ() {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState<string | null>(null)
  const s = q.trim().toLowerCase()
  const list = data.faq.filter((f) => !s || f.q.toLowerCase().includes(s) || f.a.toLowerCase().includes(s))
  return (
    <>
      <SectionHead title="FAQ" sub="Respostas rápidas do Discord. Busque por palavra-chave: star, boost, fly, vip, hoenn…" />
      <div className="toolbar">
        <Search value={q} onChange={setQ} placeholder="O que você quer saber?" />
        <span className="count">{list.length} respostas</span>
      </div>
      <div style={{ display: 'grid', gap: 8 }}>
        {list.map((f) => {
          const isOpen = open === f.q || (!!s && list.length <= 6)
          return (
            <div className={`faq-item ${isOpen ? 'open' : ''}`} key={f.q}>
              <button className="faq-q" onClick={() => setOpen(isOpen ? null : f.q)}>
                <span className="kw">{f.q}</span>
                <span className="arrow">›</span>
              </button>
              {isOpen && <div className="faq-a"><Linkified text={f.a} />{topicFor(f.q) && <VideoRefs topic={topicFor(f.q)!} max={2} />}</div>}
            </div>
          )
        })}
      </div>
      {!list.length && <div className="empty">Nenhuma resposta encontrada. Tenta outra palavra ou pergunta no Discord.</div>}
    </>
  )
}
