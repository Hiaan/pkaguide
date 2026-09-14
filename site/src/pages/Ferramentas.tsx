import { SectionHead } from '../components/ui'

type Tool = { url: string; name: string; tag: string; title: string; sub: string; lead: string; features: { ico: string; title: string; desc: string }[]; note?: string }

const TOOLS: Record<string, Tool> = {
  criticalcatch: {
    url: 'https://criticalcatch-pkatools.vercel.app/',
    name: 'Critical Catch', tag: 'PKA Tools',
    title: 'Ferramentas de catch',
    sub: 'Ferramentas interativas para o dia a dia no PokeAlliance, no site Critical Catch.',
    lead: 'Ferramentas de catch, médias, times e calculadora de dano em um só lugar.',
    features: [
      { ico: '🎯', title: 'Ferramentas de catch', desc: 'Acompanhe brokes, chance de catch e o quanto falta para a máxima do seu shiny.' },
      { ico: '📈', title: 'Médias', desc: 'Média de catches por tier e por Pokémon, com base nos dados da comunidade.' },
      { ico: '🧩', title: 'Times', desc: 'Monte e compare rotações de Pokémon para cada hunt.' },
      { ico: '💥', title: 'Calculadora de dano', desc: 'Simule o dano dos seus Pokémon considerando tier, star, boost e talentos.' },
    ],
  },
  pokeforge: {
    url: 'https://pokeforge-pka.netlify.app/',
    name: 'PokéForge', tag: 'Calculadora de builds',
    title: 'Calculadora de builds',
    sub: 'Planeje o custo total do seu próximo Pokémon: cópias, estrelas, treino e boost em um único orçamento.',
    lead: 'Do primeiro treino à build completa. Informe o preço do diamante no seu servidor, escolha tier e metas, e veja o orçamento em tempo real.',
    features: [
      { ico: '⭐', title: 'Fusões de STAR', desc: 'Quantas cópias 0★ e quantas taxas de fusão para chegar da estrela atual à desejada, com a árvore de fusões.' },
      { ico: '🏋️', title: 'Treinamento', desc: 'Oito atributos (Attack, Critical, Defense, HP, Precision, Evasion…) com cargas e diamantes por pacote de 20.000.' },
      { ico: '🔥', title: 'Boost probabilístico', desc: 'Stones esperadas em média, reserva com 95% de segurança e pior caso, considerando as falhas acumuladas.' },
      { ico: '💎', title: 'Orçamento ao vivo', desc: 'Converte tudo para Cash pelo preço do diamante, salva no navegador e exporta ou imprime a build.' },
    ],
    note: 'Treino é estimado e boost depende de tentativas. Os preços e taxas são os que você informa, então mantenha-os atualizados com o mercado.',
  },
}

export default function Ferramentas({ sub }: { sub: string }) {
  const t = TOOLS[sub] ?? TOOLS.criticalcatch
  return (
    <>
      <SectionHead title={t.title} sub={t.sub} />
      <div className="sug">
        <div className="sug-hero">
          <h2><span>{t.name}</span> · {t.tag}</h2>
          <p>{t.lead} Abre em uma nova aba.</p>
          <a className="btn btn-primary" style={{ fontSize: 17, padding: '16px 30px' }} href={t.url} target="_blank" rel="noreferrer">🚀 Abrir {t.name} ↗</a>
          <div className="muted small" style={{ marginTop: 12 }}>{t.url.replace('https://', '').replace(/\/$/, '')}</div>
        </div>
        <div className="sug-steps" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {t.features.map((f) => (
            <a key={f.title} className="card" href={t.url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
              <div style={{ fontSize: 30, marginBottom: 8 }}>{f.ico}</div>
              <b>{f.title}</b>
              <p className="muted small" style={{ margin: '6px 0 0', lineHeight: 1.5 }}>{f.desc}</p>
            </a>
          ))}
        </div>
        {t.note && <p className="muted small" style={{ marginTop: 18 }}>{t.note}</p>}
      </div>
    </>
  )
}
