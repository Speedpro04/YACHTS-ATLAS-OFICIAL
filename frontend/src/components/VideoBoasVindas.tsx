import { useEffect, useState } from 'react'
import { PlayCircle, X, Clock } from 'lucide-react'
import { api } from '../services/api'

const JA_VISTO = 'atlas.boas-vindas.dispensado'

/**
 * Faixa de boas-vindas no topo do painel, com o vídeo que explica o sistema.
 *
 * Fica AQUI, e não só na tela de sucesso do pagamento, por duas razões: a tela
 * de sucesso empurra a Marina para o painel em 15 segundos (ninguém assiste 4
 * minutos ali), e a dúvida não aparece no dia da compra — aparece no primeiro
 * cadastro, uma semana depois. Aqui o vídeo continua ao alcance.
 *
 * O vídeo só BAIXA quando a pessoa dá play: são 16 MB, e carregar sozinho
 * pesaria em toda abertura do painel, inclusive de quem já assistiu.
 */
export default function VideoBoasVindas({ aberturaForcada = false }: { aberturaForcada?: boolean }) {
  const [dispensado, setDispensado] = useState(() => {
    try {
      return localStorage.getItem(JA_VISTO) === '1'
    } catch {
      return false   // aba anônima ou storage bloqueado: mostra, que é o certo
    }
  })
  const [url, setUrl] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(false)

  const tocar = async () => {
    if (url || carregando) return
    setCarregando(true)
    setErro(false)
    try {
      const r: any = await api.institucional.boasVindas()
      if (r?.url) setUrl(r.url)
      else setErro(true)
    } catch {
      setErro(true)
    } finally {
      setCarregando(false)
    }
  }

  // Chegou pela tela de sucesso do pagamento: o play já vem dado.
  useEffect(() => {
    if (aberturaForcada) tocar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberturaForcada])

  const dispensar = () => {
    setDispensado(true)
    try {
      localStorage.setItem(JA_VISTO, '1')
    } catch {
      /* sem storage, volta a aparecer no próximo acesso — não é perda */
    }
  }

  if (dispensado && !aberturaForcada) return null

  return (
    <div className="relative border border-[#c5a059]/20 rounded-sm overflow-hidden bg-[#010c20]">
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#c5a059]/5 blur-[100px] rounded-full pointer-events-none" />

      {url ? (
        <video
          src={url}
          controls
          autoPlay
          playsInline
          className="w-full aspect-video bg-black"
        />
      ) : (
        <div className="relative flex flex-col md:flex-row items-center gap-8 p-8 md:p-10">
          <button
            onClick={tocar}
            disabled={carregando}
            className="group relative w-full md:w-[320px] aspect-video rounded-sm overflow-hidden border border-[#c5a059]/30 shrink-0"
            aria-label="Assistir ao vídeo de boas-vindas"
          >
            <img
              src="/boas-vindas-poster.jpg"
              alt=""
              className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
            />
            <span className="absolute inset-0 flex items-center justify-center">
              {carregando ? (
                <span className="w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full animate-spin" />
              ) : (
                <PlayCircle size={52} className="text-[#c5a059] drop-shadow-lg" />
              )}
            </span>
          </button>

          <div className="relative z-10 text-center md:text-left">
            <div className="flex items-center gap-3 mb-4 justify-center md:justify-start">
              <div className="w-8 h-px bg-[#c5a059]" />
              <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#c5a059]">
                Comece por aqui
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-serif font-bold text-white mb-3 tracking-tight">
              O sistema por dentro, em quatro partes.
            </h2>
            <p className="text-white/40 font-light leading-relaxed max-w-lg">
              Painel Técnico, Pré-Data, Portal do Proprietário e o Dossiê Atlas — o caminho
              completo, do cadastro do primeiro barco ao documento que o dono recebe.
            </p>
            <p className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] font-black text-white/25 mt-5 justify-center md:justify-start">
              <Clock size={12} /> 4 minutos
            </p>
            {erro && (
              <p className="text-rose-400/80 text-xs mt-4">
                Não consegui carregar o vídeo agora. Tente de novo em instantes.
              </p>
            )}
          </div>
        </div>
      )}

      {!aberturaForcada && (
        <button
          onClick={dispensar}
          className="absolute top-3 right-3 z-20 text-white/30 hover:text-white/70 transition-colors"
          aria-label="Não mostrar mais"
          title="Não mostrar mais"
        >
          <X size={18} />
        </button>
      )}
    </div>
  )
}
