import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { ShieldCheck, ShieldAlert, ChevronRight, Loader2, Check } from 'lucide-react'

/**
 * Consentimento do titular para o dossiê sair para terceiro.
 *
 * POR QUE ISTO APARECE NA FICHA DA EMBARCAÇÃO
 * -------------------------------------------
 * O consentimento é colhido UMA VEZ, no cadastro do ativo — não a cada
 * liberação. Pedir aprovação do armador a cada envio mataria a promessa de
 * velocidade do produto: o comprador está no píer esperando, e o armador
 * pode estar navegando.
 *
 * O QUE A TELA NÃO PODE FAZER
 * ---------------------------
 * Deixar a marina marcar "autorizado" sem ter o texto à vista. Colher
 * consentimento sem mostrar com o que se concorda é o mesmo que não colher —
 * e numa auditoria vira uma linha que não se sustenta. Por isso o termo abre
 * inteiro antes do botão, e não atrás de um link.
 *
 * Retirar é um EVENTO, não um apagamento: o histórico inteiro fica. Uma
 * plataforma de custódia que apagasse a própria trilha de consentimento
 * estaria contradizendo o que vende.
 */

type Estado = {
  vigente: boolean | null
  evento: string | null
  registrado_em: string | null
  termo_versao: string | null
  titular_nome: string | null
  termo_atual_versao: string
  termo_atual_texto: string
  desatualizado: boolean
}

const VIAS: { valor: 'contrato_marina' | 'assinatura_digital' | 'email' | 'presencial'; rotulo: string }[] = [
  { valor: 'contrato_marina', rotulo: 'Contrato com a Marina' },
  { valor: 'assinatura_digital', rotulo: 'Assinatura digital' },
  { valor: 'email', rotulo: 'E-mail do titular' },
  { valor: 'presencial', rotulo: 'Presencial' },
]

export default function ConsentimentoTitular({ ativoId }: { ativoId: string }) {
  const [estado, setEstado] = useState<Estado | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [aberto, setAberto] = useState(false)
  const [via, setVia] = useState<typeof VIAS[number]['valor']>('contrato_marina')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const carregar = async () => {
    try {
      setEstado(await api.ativos.consentimento(ativoId))
      setErro(null)
    } catch {
      // `vigente: null` = "não sei", que a tela mostra como indisponível.
      // Nunca como "autorizado": seria afirmar base legal por falha de rede.
      setEstado(null)
      setErro('Não foi possível consultar o consentimento.')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => { carregar() }, [ativoId])

  const registrar = async (evento: 'concedido' | 'revogado') => {
    setSalvando(true)
    setErro(null)
    try {
      await api.ativos.registrarConsentimento(ativoId, { evento, obtido_via: via })
      await carregar()
      setAberto(false)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível registrar. Tente novamente.')
    } finally {
      setSalvando(false)
    }
  }

  if (carregando) {
    return (
      <div className="flex items-center gap-2 px-5 py-4 text-[11px] text-white/40">
        <Loader2 size={13} className="animate-spin" /> Consultando consentimento…
      </div>
    )
  }

  const ok = estado?.vigente === true
  const data = estado?.registrado_em
    ? new Date(estado.registrado_em).toLocaleDateString('pt-BR')
    : null

  return (
    <div className={`rounded-sm border ${ok ? 'border-emerald-500/25 bg-emerald-500/[0.04]'
                                            : 'border-amber-500/30 bg-amber-500/[0.05]'}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 py-4">
        <div className="flex items-start gap-3">
          {ok
            ? <ShieldCheck size={17} className="text-emerald-400 shrink-0 mt-0.5" />
            : <ShieldAlert size={17} className="text-amber-400 shrink-0 mt-0.5" />}
          <div>
            <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${
              ok ? 'text-emerald-400/90' : 'text-amber-400/90'}`}>
              {ok ? 'Titular autorizou o compartilhamento'
                  : estado?.evento === 'revogado'
                    ? 'Titular retirou a autorização'
                    : 'Autorização do titular não registrada'}
            </p>
            <p className="text-[11px] leading-relaxed text-white/50 mt-1.5 max-w-xl">
              {ok ? (
                <>
                  Registrada em {data}
                  {estado?.titular_nome ? <> por <span className="text-white/70">{estado.titular_nome}</span></> : null}.
                  {estado?.desatualizado && (
                    <span className="text-amber-400/90"> O termo mudou desde então — recolha para atualizar.</span>
                  )}
                </>
              ) : (
                <>
                  O dossiê desta embarcação <strong className="text-white/70">não pode ser liberado
                  para terceiros</strong> enquanto o armador não autorizar. A Marina continua
                  emitindo e consultando normalmente — a exigência vale só para o envio a
                  comprador, corretor, seguradora ou perito.
                </>
              )}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setAberto((v) => !v)}
          aria-expanded={aberto}
          className="shrink-0 self-start sm:self-center flex items-center gap-1.5 px-4 py-2 rounded-sm
                     border border-white/15 text-[10px] font-black uppercase tracking-[0.18em]
                     text-white/70 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all"
        >
          {ok ? 'Ver termo' : 'Registrar autorização'}
          <ChevronRight size={12} className={`transition-transform ${aberto ? 'rotate-90' : ''}`} />
        </button>
      </div>

      {aberto && (
        <div className="border-t border-white/10 px-5 py-5 space-y-4 animate-in fade-in duration-200">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-2">
              Termo · versão {estado?.termo_atual_versao}
            </p>
            {/* O texto vem inteiro, e não resumido: a marina precisa poder ler
                ao titular exatamente o que ele está autorizando. */}
            <p className="text-[11px] leading-relaxed text-white/60 max-w-3xl">
              {estado?.termo_atual_texto}
            </p>
          </div>

          {!ok && (
            <>
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 mb-2">
                  Como a autorização foi obtida
                </p>
                <div className="flex flex-wrap gap-2">
                  {VIAS.map((v) => (
                    <button
                      key={v.valor}
                      type="button"
                      onClick={() => setVia(v.valor)}
                      className={`px-3 py-1.5 rounded-sm text-[10px] font-bold uppercase tracking-[0.12em]
                                  border transition-all ${
                        via === v.valor
                          ? 'border-[#c5a059]/60 text-[#c5a059] bg-[#c5a059]/10'
                          : 'border-white/12 text-white/45 hover:text-white/70'}`}
                    >
                      {via === v.valor && <Check size={10} className="inline mr-1 -mt-0.5" />}
                      {v.rotulo}
                    </button>
                  ))}
                </div>
              </div>
              <p className="text-[10px] leading-relaxed text-white/35 max-w-3xl">
                Ao registrar, a Marina declara que o titular concordou com o texto acima. O
                registro é permanente e datado — pode ser retirado depois, mas não apagado.
              </p>
            </>
          )}

          {erro && <p className="text-[11px] text-red-400/90">{erro}</p>}

          <div className="flex flex-wrap gap-2">
            {ok ? (
              <button
                type="button"
                disabled={salvando}
                onClick={() => registrar('revogado')}
                className="px-4 py-2 rounded-sm border border-red-500/30 text-[10px] font-black
                           uppercase tracking-[0.18em] text-red-400/90 hover:bg-red-500/10
                           transition-all disabled:opacity-40"
              >
                {salvando ? 'Registrando…' : 'Retirar autorização'}
              </button>
            ) : (
              <button
                type="button"
                disabled={salvando}
                onClick={() => registrar('concedido')}
                className="px-5 py-2 rounded-sm bg-[#c5a059] text-[#010c20] text-[10px] font-black
                           uppercase tracking-[0.18em] hover:bg-[#d4b06a] transition-all
                           disabled:opacity-40"
              >
                {salvando ? 'Registrando…' : 'Registrar autorização do titular'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
