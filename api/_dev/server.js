// Servidor local do chat (o Vite aponta /api para cá). Use CHAT_MOCK=1 para testar sem chave.
import http from 'node:http'
import handler from '../chat.js'

http.createServer((req, res) => {
  let b = ''
  req.on('data', (c) => (b += c))
  req.on('end', () => {
    try { req.body = b ? JSON.parse(b) : undefined } catch { req.body = null }
    res.status = (n) => { res.statusCode = n; return res }
    res.json = (o) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)) }
    handler(req, res)
  })
}).listen(8787, () => console.log('chat dev em http://localhost:8787/api/chat', process.env.CHAT_MOCK === '1' ? '(mock)' : ''))
