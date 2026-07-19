import { Lock, AlertTriangle, Loader2 } from 'lucide-react'

/**
 * Confirmação antes de selar um registro.
 *
 * Selar é irreversível: a partir daí o registro não pode ser editado nem
 * excluído — nem pela plataforma. Errou? Só por retificação, e o erro fica
 * visível no dossiê ao lado da correção.
 *
 * O atrito aqui é intencional. É ele que faz a pessoa reler antes de lacrar.
 */
export default function ConfirmarSelo({
  titulo,
  categoria,
  enviando = false,
  onConfirmar,
  onCancelar,
}: {
  titulo: string
  categoria?: string
  enviando?: boolean
  onConfirmar: () => void
  onCancelar: () => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#010c20]/80 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmar-selo-titulo"
    >
      <div className="w-full max-w-lg bg-[#021a3d] border border-[#c5a059]/30 rounded-sm shadow-2xl">
        <div className="flex items-start gap-4 p-6 border-b border-white/10">
          <div className="mt-0.5 text-amber-500">
            <AlertTriangle size={22} strokeWidth={1.8} />
          </div>
          <div>
            <h3
              id="confirmar-selo-titulo"
              className="text-white text-sm font-bold"
            >
              Selar registro na cadeia de custódia
            </h3>
            <p className="text-[10px] text-white/40 uppercase tracking-[0.2em] mt-1">
              Esta ação não pode ser desfeita
            </p>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="bg-white/[0.03] border border-white/10 rounded-sm p-4">
            {categoria && (
              <p className="text-[9px] font-black text-[#c5a059] uppercase tracking-[0.2em] mb-1">
                {categoria}
              </p>
            )}
            <p className="text-white text-sm font-bold leading-snug">{titulo}</p>
          </div>

          <p className="text-white/60 text-[13px] leading-relaxed">
            Depois de selado, este registro <strong className="text-white">não poderá ser
            editado nem excluído</strong> — nem pela Yachts Atlas. Ele recebe um hash
            SHA-256 e passa a integrar permanentemente o histórico da embarcação.
          </p>

          <div className="bg-amber-500/[0.07] border-l-2 border-amber-500 rounded-sm px-4 py-3">
            <p className="text-amber-200/90 text-[12px] leading-relaxed">
              Se houver erro, a correção é feita por <strong>retificação</strong>: o
              registro errado permanece visível no dossiê, com a correção e o motivo
              ao lado. É isso que dá credibilidade ao histórico.
            </p>
          </div>

          <p className="text-white/40 text-[12px]">
            Confira os dados antes de continuar.
          </p>
        </div>

        <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-white/10">
          <button
            type="button"
            onClick={onCancelar}
            disabled={enviando}
            className="text-[10px] font-black uppercase tracking-[0.3em] text-white/50 hover:text-white transition-colors disabled:opacity-40"
          >
            Revisar antes
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={enviando}
            className="flex items-center gap-3 bg-gradient-to-r from-[#c5a059] to-[#b38f4d] hover:from-[#d4b36d] hover:to-[#c5a059] text-[#010c20] px-7 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all disabled:opacity-50"
          >
            {enviando ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <Lock size={15} />
            )}
            Selar definitivamente
          </button>
        </div>
      </div>
    </div>
  )
}
