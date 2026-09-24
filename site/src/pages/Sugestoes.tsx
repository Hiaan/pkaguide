import { useState } from 'react'
import { SectionHead } from '../components/ui'

const REPO = 'https://github.com/Hiaan/pkaguide/issues/new'
const TIPOS: { id: string; label: string; ico: string }[] = [
  { id: 'Ideia', label: 'Ideia nova', ico: '💡' },
  { id: 'Erro', label: 'Achei um erro', ico: '🐞' },
  { id: 'Dado', label: 'Dado desatualizado', ico: '📊' },
  { id: 'Overlay', label: 'Sobre o overlay', ico: '🖥️' },
]

export default function Sugestoes() {
  const [tipo, setTipo] = useState('Ideia')
  const [titulo, setTitulo] = useState('')
  const [texto, setTexto] = useState('')
  const [copiado, setCopiado] = useState(false)

  const corpo = `${texto}\n\n---\nEnviado pela página de Sugestões do PKA GUIDE (${location.href})`
  const url = `${REPO}?title=${encodeURIComponent(`[${tipo}] ${titulo}`)}&body=${encodeURIComponent(corpo)}`
  const pronto = titulo.trim().length > 3 && texto.trim().length > 10

  const copiar = () => {
    navigator.clipboard?.writeText(`[${tipo}] ${titulo}\n\n${texto}`).then(() => {
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2500)
    }).catch(() => { /* sem clipboard */ })
  }

  return (
    <>
      <SectionHead title="Sugestões" sub="Este site é feito pela comunidade e melhora com a sua ajuda. Mande sua ideia por aqui mesmo." />

      <div className="sug-form card">
        <div className="field">
          <label>O que você quer mandar?</label>
          <div className="tags">
            {TIPOS.map((t) => (
              <button key={t.id} className={`chip orange ${tipo === t.id ? 'active' : ''}`} onClick={() => setTipo(t.id)}>{t.ico} {t.label}</button>
            ))}
          </div>
        </div>
        <div className="field">
          <label>Resumo em uma linha</label>
          <input className="sug-input" value={titulo} maxLength={90} placeholder="ex.: falta a função de cada Pokémon nos times"
                 onChange={(e) => setTitulo(e.target.value)} />
        </div>
        <div className="field">
          <label>Explique com suas palavras</label>
          <textarea className="sug-input" rows={5} value={texto} maxLength={1500}
                    placeholder="Conte o que falta, onde está errado ou como ficaria melhor. Se for um erro, diga em qual aba aconteceu."
                    onChange={(e) => setTexto(e.target.value)} />
        </div>
        <div className="sug-actions">
          <a className={`btn btn-primary ${pronto ? '' : 'disabled'}`} href={pronto ? url : undefined} target="_blank" rel="noreferrer"
             onClick={(e) => { if (!pronto) e.preventDefault() }}>
            📨 Enviar sugestão
          </a>
          <button className="btn" onClick={copiar} disabled={!pronto}>{copiado ? '✓ Copiado' : '📋 Copiar texto'}</button>
          {!pronto && <span className="muted small">Preencha o resumo e a explicação para liberar o envio.</span>}
        </div>
        <p className="muted tiny" style={{ margin: '12px 2px 0' }}>
          O envio abre a página do GitHub do projeto já preenchida com o que você escreveu. É preciso ter conta no GitHub (é grátis) e clicar em "Submit".
          Se preferir não criar conta, use o botão "Copiar texto" e cole num comentário do canal ou no Discord.
        </p>
      </div>

      <div className="sug">
        <div className="sug-hero">
          <h2>Feito por <span>@hianpoke</span></h2>
          <p>
            O PKA GUIDE é produzido e mantido pelo canal <b>hianpoke</b> no YouTube. Também dá para mandar sua sugestão
            nos comentários de qualquer vídeo ou no Discord do jogo.
          </p>
          <div className="sug-links">
            <a className="yt" href="https://www.youtube.com/@hianpoke" target="_blank" rel="noreferrer">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.3 3.6-6.3 3.6z" /></svg>
              youtube.com/@hianpoke
            </a>
            <a className="btn" href="https://discord.gg/pokealliance" target="_blank" rel="noreferrer">Discord do PokeAlliance</a>
            <a className="btn" href="https://github.com/Hiaan/pkaguide/issues" target="_blank" rel="noreferrer">Ver sugestões já enviadas</a>
          </div>
        </div>
      </div>
    </>
  )
}
