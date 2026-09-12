import { SectionHead } from '../components/ui'

const URL = 'https://criticalcatch-pkatools.vercel.app/'

const TOOLS = [
  { ico: '🎯', title: 'Ferramentas de catch', desc: 'Acompanhe brokes, chance de catch e o quanto falta para a máxima do seu shiny.' },
  { ico: '📈', title: 'Médias', desc: 'Média de catches por tier e por Pokémon, com base nos dados da comunidade.' },
  { ico: '🧩', title: 'Times', desc: 'Monte e compare rotações de Pokémon para cada hunt.' },
  { ico: '💥', title: 'Calculadora de dano', desc: 'Simule o dano dos seus Pokémon considerando tier, star, boost e talentos.' },
]

export default function Ferramentas() {
  return (
    <>
      <SectionHead title="Ferramentas" sub="Ferramentas interativas para o dia a dia no PokeAlliance, no site Critical Catch." />
      <div className="sug">
        <div className="sug-hero">
          <h2><span>Critical Catch</span> · PKA Tools</h2>
          <p>Ferramentas de catch, médias, times e calculadora de dano em um só lugar. Abre em uma nova aba.</p>
          <a className="btn btn-primary" style={{ fontSize: 17, padding: '16px 30px' }} href={URL} target="_blank" rel="noreferrer">🚀 Abrir Critical Catch ↗</a>
          <div className="muted small" style={{ marginTop: 12 }}>{URL.replace('https://', '')}</div>
        </div>
        <div className="sug-steps" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {TOOLS.map((t) => (
            <a key={t.title} className="card" href={URL} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
              <div style={{ fontSize: 30, marginBottom: 8 }}>{t.ico}</div>
              <b>{t.title}</b>
              <p className="muted small" style={{ margin: '6px 0 0', lineHeight: 1.5 }}>{t.desc}</p>
            </a>
          ))}
        </div>
      </div>
    </>
  )
}
