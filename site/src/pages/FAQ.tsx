import { useState } from 'react'
import { data } from '../lib/data'
import { Linkified, Search, SectionHead } from '../components/ui'

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
              {isOpen && <div className="faq-a"><Linkified text={f.a} /></div>}
            </div>
          )
        })}
      </div>
      {!list.length && <div className="empty">Nenhuma resposta encontrada. Tenta outra palavra ou pergunta no Discord.</div>}
    </>
  )
}
