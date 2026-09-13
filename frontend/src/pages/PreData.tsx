import { useEffect, useMemo, useState } from 'react'
import { Anchor, Camera, Check, ChevronDown, Database, Lock, RefreshCw, X } from 'lucide-react'
import { api } from '../services/api'
import ConfirmarSelo from '../components/ConfirmarSelo'

/**
 * Pré-Data — o armário de dados crus.
 *
 * Aqui NADA foi tratado. É o que chegou do píer pelo Atlas Pré-Data: fotos e
 * anotações feitas com a mão suja, na hora do serviço, sem conferência. Esta
 * tela existe para guardar e mostrar — não para parecer registro.
 *
 * Por que o aviso é grande e fica no topo: pré-dado com cara de registro é
 * pior que pré-dado nenhum. Alguém lê "horímetro 412,5" numa tabela bem
 * formatada e usa como se fosse verdade conferida — e a partir daí o erro viaja
 * com aparência de fato.
 *
 * POR EMBARCAÇÃO, sem misturar. Dois barcos são duas histórias; lista corrida
 * faz o revisor conferir o serviço de um olhando a foto do outro.
 */

type Envio = {
  id: string
  categoria: string
  titulo: string | null
  observacao: string | null
  dados: Record<string, any>
  created_at: string
}

type FotoPendente = {
  id: string
  nome_arquivo: string
  categoria: string
  descricao: string | null
  created_at: string
  /** URL assinada, válida por uma hora. Null quando a assinatura falhou. */
  url: string | null
}

type Embarcacao = {
  ativo_id: string
  nome: string
  embarcacao: string
  ano: number | null
  pes: number | null
  envios: Envio[]
  fotos_pendentes: FotoPendente[]
}

export default function PreData() {
  const [lista, setLista] = useState<Embarcacao[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [aberta, setAberta] = useState<string | null>(null)
  const [recarregando, setRecarregando] = useState(false)
  // O tratamento acontece AQUI, e não em outra tela: é nesta que a pessoa está
  // olhando o rascunho ao lado da foto que ele explica. Mandar procurar o
  // mesmo item noutro lugar é onde a revisão se perde.
  const [tratando, setTratando] = useState<string>('')
  const [selar, setSelar] = useState<Envio | null>(null)
  // A recusa pede motivo antes de acontecer. Não é burocracia: recusar sem
  // dizer por quê devolve o colaborador ao mesmo erro amanhã, e deixa o
  // revisor seguinte sem saber se aquilo foi analisado ou descartado por engano.
  const [recusar, setRecusar] = useState<{ tipo: 'foto' | 'envio'; id: string; rotulo: string } | null>(null)
  const [motivo, setMotivo] = useState('')

  async function carregar() {
    setRecarregando(true)
    try {
      const r = await api.registros.preData()
      setLista(r.embarcacoes || [])
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível carregar.')
    } finally {
      setRecarregando(false)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  /**
   * Aprova uma foto do campo: ela deixa de ser pré-dado e passa a contar no
   * dossiê. Some desta aba justamente por isso — o que foi tratado não é mais
   * dado cru, e deixá-lo aqui faria a aba virar histórico em vez de fila.
   */
  async function aprovarFoto(docId: string) {
    setTratando(docId)
    try {
      await api.documentos.aprovar(docId)
      await carregar()
      setErro(null)
    } catch (e: any) {
      // A mensagem do servidor vem inteira: as recusas reais desta rota
      // (papel insuficiente, documento já tratado) são as que repetir o clique
      // não resolve.
      setErro(e?.message || 'Não foi possível aprovar a foto.')
    } finally {
      setTratando('')
    }
  }

  /**
   * Recusa o item: sai da fila, continua no banco com motivo e autor.
   *
   * Nada é apagado. Pré-dado descartado em silêncio é dado perdido — um mês
   * depois ninguém sabe se aquela foto foi analisada ou sumiu.
   */
  async function confirmarRecusa() {
    if (!recusar) return
    const texto = motivo.trim()
    if (texto.length < 3) {
      setErro('Diga o motivo da recusa.')
      return
    }
    setTratando(recusar.id)
    try {
      if (recusar.tipo === 'foto') await api.documentos.recusar(recusar.id, texto)
      else await api.registros.rascunho.recusar(recusar.id, texto)
      setRecusar(null)
      setMotivo('')
      await carregar()
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível recusar.')
    } finally {
      setTratando('')
    }
  }

  /**
   * Sela o rascunho: o pré-dado vira registro, e a partir daí não pode mais ser
   * editado nem excluído. Irreversível — por isso passa pela confirmação, e não
   * por um clique direto.
   */
  async function selarRascunho(envio: Envio) {
    setTratando(envio.id)
    try {
      await api.registros.rascunho.selar(envio.id)
      setSelar(null)
      await carregar()
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível selar o registro.')
    } finally {
      setTratando('')
    }
  }

  const totais = useMemo(() => {
    const l = lista || []
    return {
      embarcacoes: l.length,
      envios: l.reduce((s, e) => s + e.envios.length, 0),
      fotos: l.reduce((s, e) => s + e.fotos_pendentes.length, 0),
    }
  }, [lista])

  return (
    <div className="p-6 md:p-10 lg:p-14">
      <header className="pb-8 border-b border-white/5">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Database size={20} className="text-[#c5a059]" />
              <h1 className="text-3xl md:text-5xl font-serif font-bold">Pré-Data</h1>
            </div>
            <p className="text-white/40 text-[10px] uppercase tracking-[0.4em] font-black ml-9">
              Armário de dados crus · vindos do campo
            </p>
          </div>

          <button
            onClick={carregar}
            disabled={recarregando}
            className="flex items-center gap-3 rounded-sm border border-white/10 text-white/40 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] transition-colors hover:text-white/80 hover:border-white/20 disabled:opacity-40"
          >
            <RefreshCw size={14} className={recarregando ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </header>

      {/* O aviso não é decoração: é o que impede alguém de ler isto como
          registro. Fica antes de qualquer número, e não se fecha. */}
      <div className="mt-8 border border-[#c5a059]/25 bg-[#c5a059]/[0.04] rounded-sm px-6 py-5">
        <p className="text-[#c5a059] text-[10px] uppercase tracking-[0.3em] font-black mb-2">
          Dados sem tratamento
        </p>
        <p className="text-white/55 text-sm leading-relaxed max-w-3xl">
          Nada aqui foi conferido, corrigido ou selado. É o que a equipe capturou
          no barco, como capturou. Enquanto estiver nesta aba, não entra no
          Dossiê Atlas, não conta no Índice de Custódia e não aparece na
          verificação pública.
        </p>
      </div>

      {/* Três números, discretos. Quem abre a aba quer saber o tamanho da fila
          antes de decidir por onde começar. */}
      <dl className="mt-8 grid grid-cols-3 gap-4 md:gap-6 max-w-2xl">
        {[
          ['Embarcações', totais.embarcacoes],
          ['Envios', totais.envios],
          ['Fotos', totais.fotos],
        ].map(([rotulo, valor]) => (
          <div key={rotulo as string} className="bg-white/[0.02] border border-white/5 rounded-sm px-5 py-5">
            <dt className="text-white/30 text-[9px] uppercase tracking-[0.3em] font-black">
              {rotulo}
            </dt>
            <dd className="text-3xl font-serif font-bold mt-2">{valor as number}</dd>
          </div>
        ))}
      </dl>

      <main className="mt-10">
        {erro && (
          <p className="text-[#e5d5b7] text-sm">{erro}</p>
        )}

        {lista === null && !erro && <div className="py-24" aria-busy="true" />}

        {lista?.length === 0 && (
          <div className="text-center py-24 bg-white/[0.01] border border-white/5 rounded-sm">
            <p className="text-white/30 text-[10px] uppercase tracking-[0.3em] font-black">
              Nenhum envio do campo
            </p>
            <p className="mt-4 text-white/20 text-[10px] uppercase tracking-[0.2em] font-black">
              O que a equipe registrar no Atlas Pré-Data aparece aqui
            </p>
          </div>
        )}

        <ul className="space-y-4">
          {(lista || []).map((e) => {
            const total = e.envios.length + e.fotos_pendentes.length
            const abertaAgora = aberta === e.ativo_id
            return (
              <li
                key={e.ativo_id}
                className="bg-white/[0.02] border border-white/5 rounded-sm overflow-hidden"
              >
                <button
                  onClick={() => setAberta(abertaAgora ? null : e.ativo_id)}
                  aria-expanded={abertaAgora}
                  className="w-full text-left px-6 py-6 flex items-center gap-5 hover:bg-white/[0.02] transition-colors"
                >
                  <Anchor size={20} className="text-[#c5a059] shrink-0" />

                  <span className="min-w-0 flex-1">
                    <span className="block text-xl font-bold truncate">{e.nome}</span>
                    <span className="block text-[9px] text-white/35 uppercase tracking-widest mt-1 truncate">
                      {e.embarcacao}
                      {e.pes ? ` · ${e.pes} pés` : ''}
                      {e.ano ? ` · ${e.ano}` : ''}
                    </span>
                  </span>

                  {/* A contagem é a informação principal da linha fechada.
                      Fica em ouro e por extenso — "5 envios" se lê de longe;
                      um "5" sozinho faz parar para entender do que é. */}
                  <span className="shrink-0 text-right">
                    <span className="block text-[#c5a059] text-[11px] font-black uppercase tracking-[0.2em]">
                      {e.envios.length} {e.envios.length === 1 ? 'envio' : 'envios'}
                    </span>
                    {e.fotos_pendentes.length > 0 && (
                      <span className="block text-white/30 text-[9px] uppercase tracking-widest mt-1">
                        {e.fotos_pendentes.length}{' '}
                        {e.fotos_pendentes.length === 1 ? 'foto' : 'fotos'}
                      </span>
                    )}
                  </span>

                  <ChevronDown
                    size={16}
                    className={`shrink-0 text-white/20 transition-transform ${abertaAgora ? 'rotate-180' : ''}`}
                  />
                </button>

                {abertaAgora && (
                  <div className="border-t border-white/5 px-6 py-6 space-y-4">
                    {e.envios.map((env) => (
                      <Envio
                        key={env.id}
                        envio={env}
                        selando={tratando === env.id}
                        onSelar={() => setSelar(env)}
                        onRecusar={() => { setRecusar({ tipo: 'envio', id: env.id, rotulo: env.titulo || 'Registro de campo' }); setMotivo('') }}
                      />
                    ))}

                    {e.fotos_pendentes.length > 0 && (
                      <div className="pt-2">
                        <p className="text-white/30 text-[9px] uppercase tracking-[0.3em] font-black mb-3">
                          Fotos aguardando revisão
                        </p>
                        <ul className="space-y-2">
                          {e.fotos_pendentes.map((f) => (
                            <li
                              key={f.id}
                              className="flex items-center gap-3 text-sm text-white/60"
                            >
                              {/* A MINIATURA, e não o nome do arquivo.
                                  Aprovar "IMG_4821.jpg" sem ver é carimbo: o
                                  revisor não sabe se é o barco certo, se a
                                  avaria aparece, se é um panfleto. Clicar abre
                                  em tamanho real, que é quando se decide. */}
                              {f.url ? (
                                <a
                                  href={f.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="shrink-0 w-16 h-16 rounded-sm overflow-hidden border border-white/10 hover:border-[#c5a059]/50 transition-colors bg-white/[0.03]"
                                  title="Abrir em tamanho real"
                                >
                                  <img
                                    src={f.url}
                                    alt={f.nome_arquivo}
                                    loading="lazy"
                                    className="w-full h-full object-cover"
                                  />
                                </a>
                              ) : (
                                /* Sem imagem a aba ainda serve — mas quem revisa
                                   precisa saber que está decidindo às cegas. */
                                <span
                                  className="shrink-0 w-16 h-16 rounded-sm border border-amber-500/30 bg-amber-500/5 flex items-center justify-center"
                                  title="A imagem não pôde ser carregada"
                                >
                                  <Camera size={16} className="text-amber-500/60" />
                                </span>
                              )}
                              <span className="truncate flex-1">{f.nome_arquivo}</span>
                              <span className="text-white/25 text-[9px] uppercase tracking-widest shrink-0">
                                {new Date(f.created_at).toLocaleDateString('pt-BR')}
                              </span>
                              <button
                                onClick={() => aprovarFoto(f.id)}
                                disabled={tratando === f.id}
                                className="shrink-0 flex items-center gap-1.5 border border-[#c5a059]/40 hover:bg-[#c5a059]/10 disabled:opacity-40 text-[#c5a059] px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
                              >
                                <Check size={12} />
                                {tratando === f.id ? 'Aprovando' : 'Aprovar'}
                              </button>
                              <button
                                onClick={() => { setRecusar({ tipo: 'foto', id: f.id, rotulo: f.nome_arquivo }); setMotivo('') }}
                                disabled={tratando === f.id}
                                className="shrink-0 flex items-center gap-1.5 border border-white/10 hover:border-rose-400/40 hover:text-rose-400 disabled:opacity-40 text-white/40 px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
                              >
                                <X size={12} /> Recusar
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <p className="text-white/25 text-[9px] uppercase tracking-widest pt-3 border-t border-white/5 leading-relaxed">
                      {total} {total === 1 ? 'item' : 'itens'} desta embarcação ·
                      nenhum deles no Dossiê Atlas
                    </p>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      </main>

      {/* A recusa pede o motivo ANTES de acontecer. O campo não tem valor
          sugerido de propósito: motivo pronto em lista vira clique automático, e
          o que se quer aqui é a frase que o colaborador do píer vai ler. */}
      {recusar && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#010c20]/80 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-lg bg-[#021a3d] border border-white/10 rounded-sm shadow-2xl p-6 space-y-5">
            <div>
              <h3 className="text-white text-sm font-bold">Recusar este item</h3>
              <p className="text-white/40 text-[11px] mt-2 leading-relaxed">
                {recusar.rotulo}
              </p>
            </div>
            <p className="text-white/50 text-[11px] leading-relaxed">
              Nada é apagado: o item sai da fila e continua guardado, com o seu
              nome, a hora e o motivo. Quem mandou do píer precisa saber por quê.
            </p>
            <div>
              <label className="block text-white/30 text-[9px] uppercase tracking-[0.25em] font-black mb-2">
                Motivo
              </label>
              <textarea
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                rows={3}
                autoFocus
                placeholder="Ex: foto do barco errado — este é o Aurora Austral"
                className="w-full bg-white/5 border border-white/10 focus:border-[#c5a059]/50 rounded-sm px-4 py-3 text-white text-sm outline-none transition-colors placeholder:text-white/15"
              />
            </div>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => { setRecusar(null); setMotivo('') }}
                className="text-white/40 hover:text-white/70 px-4 py-2.5 text-[9px] font-black uppercase tracking-widest transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmarRecusa}
                disabled={tratando === recusar.id || motivo.trim().length < 3}
                className="flex items-center gap-2 bg-rose-500/80 hover:bg-rose-500 disabled:opacity-30 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
              >
                <X size={12} />
                {tratando === recusar.id ? 'Recusando' : 'Confirmar recusa'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* O atrito antes de selar é o mesmo do resto do sistema, e de propósito:
          quem trata pré-dado está decidindo o que entra no documento probatório. */}
      {selar && (
        <ConfirmarSelo
          titulo={selar.titulo || 'Registro de campo'}
          categoria={selar.categoria}
          enviando={tratando === selar.id}
          onConfirmar={() => selarRascunho(selar)}
          onCancelar={() => setSelar(null)}
        />
      )}
    </div>
  )
}

/**
 * Um envio, exibido como veio.
 *
 * Os campos saem em par chave/valor sem tradução nem formatação de unidade:
 * "horimetro 412,5" e não "Horímetro: 412,5 h". Formatar sugere que alguém leu
 * e conferiu — e ninguém leu. A crueza é a informação.
 */
function Envio({
  envio,
  selando,
  onSelar,
  onRecusar,
}: {
  envio: Envio
  selando: boolean
  onSelar: () => void
  onRecusar: () => void
}) {
  const d = envio.dados || {}
  const meta = new Set([
    'origem',
    'client_id',
    'capturado_em',
    'registrado_por',
    'executado_por',
    'registrado_por_login',
    'fotos_no_aparelho',
  ])
  const campos = Object.entries(d).filter(
    ([k, v]) => !meta.has(k) && v !== undefined && v !== null && v !== '',
  )

  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-sm px-5 py-5">
      <div className="flex items-baseline justify-between gap-4 flex-wrap mb-4">
        <p className="font-bold">{envio.titulo || '—'}</p>
        <p className="text-white/30 text-[9px] uppercase tracking-[0.25em] font-black">
          {envio.categoria} ·{' '}
          {new Date(envio.created_at).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>

      {envio.observacao && (
        <p className="text-white/55 text-sm leading-relaxed mb-4 whitespace-pre-line">
          {envio.observacao}
        </p>
      )}

      {campos.length > 0 && (
        <dl className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
          {campos.map(([k, v]) => (
            <div key={k} className="flex items-baseline justify-between gap-3 min-w-0">
              <dt className="text-white/25 text-[9px] uppercase tracking-[0.2em] font-black truncate">
                {k}
              </dt>
              <dd className="text-white/70 text-sm text-right shrink-0">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}

      <div className="mt-5 pt-4 border-t border-white/5 flex items-center justify-between gap-4 flex-wrap">
        {(d.executado_por || d.registrado_por) && (
          <p className="text-white/30 text-[9px] uppercase tracking-widest leading-relaxed">
            Executou {d.executado_por || '—'} · registrou {d.registrado_por || '—'}
          </p>
        )}
        {/* Selar é o ato que tira o item deste armário e o põe no dossiê.
            Fica ao lado de quem executou, de propósito: é a última coisa que a
            pessoa lê antes de decidir. */}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={onRecusar}
            disabled={selando}
            className="flex items-center gap-2 border border-white/10 hover:border-rose-400/40 hover:text-rose-400 disabled:opacity-40 text-white/40 px-4 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
          >
            <X size={12} /> Recusar
          </button>
          <button
            onClick={onSelar}
            disabled={selando}
            className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-40 text-[#010c20] px-4 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
          >
            <Lock size={12} />
            {selando ? 'Selando' : 'Tratar e selar'}
          </button>
        </div>
      </div>
    </div>
  )
}
