import { useEffect, useRef, useState } from 'react'
import { Anchor, Send, X, Loader2, Sparkles, Eraser } from 'lucide-react'
import { api } from '../services/api'

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  sources?: { codigo: string; titulo?: string; fonte_url?: string }[]
}

function sessionId(): string {
  const k = 'capita_solara_session'
  let id = sessionStorage.getItem(k)
  if (!id) {
    id = crypto?.randomUUID?.() || `s_${Date.now()}_${Math.floor(Math.random() * 1e6)}`
    sessionStorage.setItem(k, id)
  }
  return id
}

const SAUDACAO: ChatMsg = {
  role: 'assistant',
  content:
    'Olá, sou a Capitã Solara ⚓ — sua assistente de normas náuticas do Yachts Atlas. ' +
    'Pergunte sobre NORMAM, ABNT ou ISO e eu respondo na hora, sempre citando a fonte. ' +
    'Trabalho só com normas verificadas — nada de achismo.',
}

export default function CapitaSolara() {
  const [aberto, setAberto] = useState(false)
  const [msgs, setMsgs] = useState<ChatMsg[]>([SAUDACAO])
  const [input, setInput] = useState('')
  const [enviando, setEnviando] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (aberto) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [msgs, enviando, aberto])

  /**
   * Limpa a conversa e começa uma sessão nova.
   *
   * Troca o session_id junto: o backend usa esse id para manter o contexto do
   * diálogo, então limpar só a tela deixaria a Solara ainda respondendo com
   * base no que foi dito antes.
   */
  const limpar = () => {
    sessionStorage.removeItem('capita_solara_session')
    setMsgs([SAUDACAO])
    setInput('')
  }

  const enviar = async () => {
    const texto = input.trim()
    if (!texto || enviando) return
    setInput('')
    setMsgs((m) => [...m, { role: 'user', content: texto }])
    setEnviando(true)
    try {
      const r = await api.chatbot.ask(texto, sessionId())
      setMsgs((m) => [...m, { role: 'assistant', content: r?.answer || '—', sources: r?.sources }])
    } catch (err) {
      // Registra a causa: engolir o erro deixava a falha indistinguível de
      // backend fora do ar, rede caída ou resposta inválida.
      console.error('[Capitã Solara] falha ao consultar:', err)
      setMsgs((m) => [
        ...m,
        { role: 'assistant', content: 'Não consegui responder agora. Tente novamente em instantes.' },
      ])
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      {/* Botão flutuante */}
      {!aberto && (
        <button
          onClick={() => setAberto(true)}
          aria-label="Abrir Capitã Solara"
          className="fixed bottom-6 right-6 z-[60] group flex items-center gap-3 pl-4 pr-5 py-3 rounded-full bg-gradient-to-br from-[#c5a059] to-[#b38f4d] text-[#010c20] shadow-2xl shadow-[#c5a059]/30 hover:scale-105 transition-all duration-300"
        >
          <span className="relative flex items-center justify-center w-9 h-9 rounded-full bg-[#010c20]/15 border border-[#010c20]/20 overflow-hidden">
            <img
              src="/capita-solara.png"
              alt="Capitã Solara"
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
                e.currentTarget.nextElementSibling?.classList.remove('hidden')
              }}
            />
            <Anchor size={18} className="hidden absolute" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#c5a059] animate-pulse"></span>
          </span>
          <span className="text-left">
            <span className="block text-[11px] font-black uppercase tracking-[0.15em] leading-none">Capitã Solara</span>
            <span className="block text-[8px] font-bold uppercase tracking-[0.2em] opacity-70 mt-0.5">Normas · IA</span>
          </span>
        </button>
      )}

      {/* Popup de chat */}
      {aberto && (
        <div className="fixed bottom-6 right-6 z-[60] w-[92vw] max-w-[400px] h-[600px] max-h-[80vh] flex flex-col bg-[#021431] border border-[#c5a059]/30 rounded-lg overflow-hidden shadow-2xl shadow-black/50 animate-in slide-in-from-bottom-4 fade-in duration-300">
          {/* Cabeçalho */}
          <div className="px-5 py-4 flex items-center justify-between bg-gradient-to-r from-[#c5a059]/10 to-transparent border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="relative w-10 h-10 rounded-full bg-gradient-to-br from-[#c5a059] to-[#b38f4d] flex items-center justify-center text-[#010c20] overflow-hidden">
                <img
                  src="/capita-solara.png"
                  alt="Capitã Solara"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                    e.currentTarget.nextElementSibling?.classList.remove('hidden')
                  }}
                />
                <Anchor size={18} className="hidden absolute" />
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#021431]"></span>
              </div>
              <div>
                <p className="text-white text-sm font-bold tracking-wide flex items-center gap-1.5">
                  Capitã Solara <Sparkles size={12} className="text-[#c5a059]" />
                </p>
                <p className="text-[8px] text-[#c5a059] uppercase tracking-[0.25em] font-black">Assistente de Normas · Online</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={limpar}
                disabled={msgs.length <= 1 || enviando}
                aria-label="Limpar conversa"
                title="Limpar conversa"
                className="p-1.5 text-white/40 hover:text-[#c5a059] transition-all
                           disabled:opacity-25 disabled:cursor-not-allowed disabled:hover:text-white/40"
              >
                <Eraser size={17} />
              </button>
              <button
                onClick={() => setAberto(false)}
                aria-label="Fechar"
                className="p-1.5 text-white/40 hover:text-white transition-all"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-lg text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-[#c5a059] text-[#010c20] font-medium rounded-br-sm'
                      : 'bg-white/[0.04] border border-white/5 text-white/80 font-light rounded-bl-sm'
                  }`}
                >
                  {m.content}
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-1.5">
                      {m.sources.map((s) => (
                        <span
                          key={s.codigo}
                          title={s.titulo}
                          className="text-[8px] font-black tracking-wide uppercase px-2 py-0.5 rounded-full bg-[#c5a059]/15 text-[#c5a059] border border-[#c5a059]/20"
                        >
                          {s.codigo}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {enviando && (
              <div className="flex justify-start">
                <div className="px-4 py-3 rounded-lg bg-white/[0.04] border border-white/5">
                  <Loader2 size={14} className="animate-spin text-[#c5a059]" />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Entrada */}
          <div className="p-3 border-t border-white/5 bg-[#010c20]/40">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && enviar()}
                placeholder="Pergunte à Capitã sobre uma norma…"
                className="flex-1 bg-white/[0.03] border border-white/10 rounded-full px-4 py-3 text-sm text-white placeholder:text-white/25 focus:outline-none focus:border-[#c5a059]/40 transition-all"
              />
              <button
                onClick={enviar}
                disabled={enviando || !input.trim()}
                aria-label="Enviar"
                className="w-11 h-11 flex-shrink-0 flex items-center justify-center bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-40 text-[#010c20] rounded-full transition-all"
              >
                <Send size={16} />
              </button>
            </div>
            <p className="text-[8px] text-white/20 uppercase tracking-[0.2em] font-black mt-2 text-center">
              Só normas · não trata dados pessoais
            </p>
          </div>
        </div>
      )}
    </>
  )
}
