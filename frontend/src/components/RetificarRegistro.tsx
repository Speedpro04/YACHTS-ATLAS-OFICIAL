import { useState } from 'react'
import { AlertTriangle, Loader2, PenLine, X } from 'lucide-react'
import { api } from '../services/api'

/**
 * Retificação de um registro já selado.
 *
 * O original NUNCA é alterado nem excluído — isso é impossível por construção,
 * o banco recusa UPDATE e DELETE. Retificar cria um registro novo apontando
 * para o antigo. No dossiê e no painel os dois aparecem: o original tarjado
 * como retificado, a correção logo abaixo, com o motivo à vista.
 *
 * O motivo é obrigatório (o banco exige mín. 10 caracteres). Sem justificativa,
 * correção é indistinguível de maquiagem — é o motivo que dá credibilidade ao
 * mecanismo.
 */

const MOTIVO_MIN = 10

export default function RetificarRegistro({
  registro,
  ativoId,
  onPronto,
  onCancelar,
}: {
  registro: any
  ativoId: string
  onPronto: () => void
  onCancelar: () => void
}) {
  const dadosOriginais = registro?.dados || {}

  const [titulo, setTitulo] = useState(
    `${registro?.titulo || 'Registro'} — retificação`
  )
  const [observacao, setObservacao] = useState(registro?.observacao || '')
  const [motivo, setMotivo] = useState('')
  const [campos, setCampos] = useState<Record<string, string>>(() => {
    const base: Record<string, string> = {}
    for (const [k, v] of Object.entries(dadosOriginais)) {
      if (k === 'evidencias' || k === 'arquivos') continue
      if (v !== null && v !== undefined && typeof v !== 'object') base[k] = String(v)
    }
    return base
  })
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const motivoCurto = motivo.trim().length < MOTIVO_MIN

  const enviar = async () => {
    if (motivoCurto) return
    setEnviando(true)
    setErro(null)
    try {
      await api.registros.retificar({
        ativo_id: ativoId,
        categoria: registro.categoria,
        titulo: titulo.slice(0, 120),
        observacao: observacao || undefined,
        // Evidências do original não são reaproveitadas: cada registro sela as
        // suas. O original continua acessível com as dele.
        dados: { ...campos, enviado_em: new Date().toISOString() },
        status: registro.status || 'registrado',
        retifica_id: registro.id,
        motivo_retificacao: motivo.trim(),
      })
      onPronto()
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível registrar a retificação.')
    } finally {
      setEnviando(false)
    }
  }

  const inputCls =
    'w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20'

  const rotulo = (k: string) =>
    k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-[#010c20]/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="w-full max-w-2xl my-8 bg-[#021a3d] border border-blue-500/30 rounded-sm shadow-2xl">
        <div className="flex items-start justify-between gap-4 p-6 border-b border-white/10">
          <div className="flex items-start gap-4">
            <div className="mt-0.5 text-blue-400">
              <PenLine size={22} strokeWidth={1.8} />
            </div>
            <div>
              <h3 className="text-white text-sm font-bold">Retificar registro selado</h3>
              <p className="text-[10px] text-white/40 uppercase tracking-[0.2em] mt-1">
                O registro original permanece no histórico
              </p>
            </div>
          </div>
          <button
            onClick={onCancelar}
            aria-label="Fechar"
            className="text-white/30 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="bg-amber-500/[0.07] border-l-2 border-amber-500 rounded-sm px-4 py-3">
            <p className="text-amber-200/90 text-[12px] leading-relaxed">
              O registro <strong className="text-white">{registro?.titulo}</strong> não
              será alterado nem excluído — isso é impossível na plataforma. Esta
              correção entra como um registro novo vinculado a ele. No dossiê os
              dois aparecem lado a lado, com o motivo visível.
            </p>
          </div>

          <div>
            <label className="block text-[9px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-2">
              Título da retificação
            </label>
            <input
              className={inputCls}
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
          </div>

          {Object.keys(campos).length > 0 && (
            <div>
              <label className="block text-[9px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-2">
                Dados corrigidos
              </label>
              <p className="text-white/35 text-[11px] mb-3">
                Os campos vêm preenchidos com os valores do registro original.
                Ajuste o que estiver errado.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(campos).map(([k, v]) => (
                  <div key={k}>
                    <label className="block text-[8px] font-bold uppercase tracking-[0.15em] text-white/35 mb-1">
                      {rotulo(k)}
                    </label>
                    <input
                      className={inputCls}
                      value={v}
                      onChange={(e) =>
                        setCampos((p) => ({ ...p, [k]: e.target.value }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-[9px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-2">
              Observação
            </label>
            <textarea
              className={`${inputCls} min-h-[80px]`}
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-[9px] font-black uppercase tracking-[0.2em] text-blue-300 mb-2">
              Motivo da retificação · obrigatório
            </label>
            <textarea
              className={`${inputCls} min-h-[80px] ${
                motivo && motivoCurto ? 'border-rose-500/40' : ''
              }`}
              placeholder="Ex.: Horímetro digitado errado no lançamento original (688 h). O valor correto, conforme o laudo, é 694 h."
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
            />
            <p
              className={`text-[11px] mt-2 ${
                motivo && motivoCurto ? 'text-rose-300/80' : 'text-white/35'
              }`}
            >
              {motivo && motivoCurto
                ? `Faltam ${MOTIVO_MIN - motivo.trim().length} caracteres — o motivo fica visível no dossiê.`
                : 'Este texto aparece no dossiê, ao lado do registro corrigido. Escreva o que um comprador ou perito precisaria ler.'}
            </p>
          </div>

          {erro && (
            <div className="flex items-start gap-3 bg-rose-500/[0.07] border border-rose-500/30 rounded-sm p-4">
              <AlertTriangle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              <p className="text-rose-300/90 text-[12px]">{erro}</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-white/10">
          <button
            type="button"
            onClick={onCancelar}
            disabled={enviando}
            className="text-[10px] font-black uppercase tracking-[0.3em] text-white/50 hover:text-white transition-colors disabled:opacity-40"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={enviar}
            disabled={enviando || motivoCurto}
            className="flex items-center gap-3 bg-blue-500 hover:bg-blue-400 text-[#010c20] px-7 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {enviando ? <Loader2 size={15} className="animate-spin" /> : <PenLine size={15} />}
            Selar retificação
          </button>
        </div>
      </div>
    </div>
  )
}
