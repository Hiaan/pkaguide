import { SectionHead } from '../components/ui'

export default function Sugestoes() {
  return (
    <>
      <SectionHead title="Sugestões" sub="Este site é feito pela comunidade e melhora com a sua ajuda." />
      <div className="sug">
        <div className="sug-hero">
          <h2>Feito por <span>@hianpoke</span></h2>
          <p>
            O Guia PokeAlliance é produzido e mantido pelo canal <b>hianpoke</b> no YouTube.
            Tem uma ideia, achou um erro ou quer uma aba nova? Deixe sua sugestão nos comentários de <b>qualquer vídeo</b> do canal.
          </p>
          <a className="yt" href="https://www.youtube.com/@hianpoke" target="_blank" rel="noreferrer">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.3 3.6-6.3 3.6z" /></svg>
            youtube.com/@hianpoke
          </a>
        </div>
        <div className="sug-steps">
          <div className="card"><div className="n">1</div><b>Abra o canal</b><p className="muted small" style={{ margin: '6px 0 0' }}>Clique no botão acima e escolha qualquer vídeo.</p></div>
          <div className="card"><div className="n">2</div><b>Comente sua sugestão</b><p className="muted small" style={{ margin: '6px 0 0' }}>Diga o que falta, o que está errado ou o que ficaria melhor no site.</p></div>
          <div className="card"><div className="n">3</div><b>Acompanhe</b><p className="muted small" style={{ margin: '6px 0 0' }}>As melhorias entram no site, que se atualiza todo dia com a planilha.</p></div>
        </div>
      </div>
    </>
  )
}
