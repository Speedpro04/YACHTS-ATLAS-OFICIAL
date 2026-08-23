import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  ShieldCheck, ShieldAlert, Loader2, Anchor, FileCheck, Clock, Archive,
} from 'lucide-react'
import { API_URL } from '../services/api'

/**
 * Página pública de verificação — destino do QR impresso no dossiê.
 *
 * Quem chega aqui é comprador, corretor ou perito de seguradora, SEM conta.
 * Por isso a página não exige login e não expõe o conteúdo do dossiê:
 * confirma autenticidade e integridade, nada além.
 */

interface Resultado {
  autentico: boolean
  protocolo: string
  emitido_em: string
  embarcacao: { nome: string; ficha: string | null; classificacao: string | null }
  custodia: {
    registros_selados: number
    documentos_selados: number
    retificacoes: number
    desde: string | null
    arquivado: boolean
  }
  integridade: {
    registros_com_hash: number
    total: number
    integro: boolean
    algoritmo: string
  }
  // Impressão digital dos dossiês emitidos para este protocolo. Lista porque
  // o mesmo ativo pode ter mais de uma via legítima (reemissão após novo
  // registro selado) — mostrar só a última faria o portador de uma via
  // anterior concluir, erradamente, que o documento dele foi adulterado.
  documentos_emitidos?: { hash: string; emitido_em: string }[]
  // Quantas vias existem ao todo — a lista acima mostra no máximo 5.
  documentos_emitidos_total?: number
  aviso: string
}

export default function Verificacao() {
  const { protocolo } = useParams<{ protocolo: string }>()
  const [params] = useSearchParams()
  const [dados, setDados] = useState<Resultado | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)

  const s = params.get('s') || ''
  const e = params.get('e') || ''

  useEffect(() => {
    if (!protocolo || !s || !e) {
      setErro('Link incompleto. Use o QR Code impresso no dossiê ou informe o protocolo e o código de verificação.')
      setCarregando(false)
      return
    }
    const url = `${API_URL}/verificar/${encodeURIComponent(protocolo)}?s=${encodeURIComponent(s)}&e=${encodeURIComponent(e)}`
    fetch(url)
      .then(async (r) => {
        if (!r.ok) {
          const j = await r.json().catch(() => null)
          throw new Error(j?.detail || 'Documento não localizado.')
        }
        return r.json()
      })
      .then(setDados)
      .catch((err) => setErro(err.message))
      .finally(() => setCarregando(false))
  }, [protocolo, s, e])

  const Moldura = ({ children }: { children: React.ReactNode }) => (
    <div className="min-h-screen bg-[#010c20] text-white flex flex-col items-center px-5 py-10"
         style={{ background: 'radial-gradient(circle at 50% 0%, #021a3d 0%, #010c20 70%)' }}>
      <header className="w-full max-w-3xl mb-8">
        <div className="text-[#c5a059] font-black uppercase tracking-[0.3em] text-sm">Yachts Atlas</div>
        <div className="text-white/40 text-[10px] uppercase tracking-[0.15em] mt-1">
          Verificação de autenticidade do dossiê
        </div>
      </header>
      <main className="w-full max-w-3xl">{children}</main>
      <footer className="w-full max-w-3xl mt-10 pt-5 border-t border-white/10
                         text-[10px] text-white/30 tracking-[0.1em]">
        AXOS HUB · CNPJ 26.998.571/0001-50 · yachtsatlas.online
      </footer>
    </div>
  )

  if (carregando) {
    return (
      <Moldura>
        <div className="flex items-center gap-3 text-white/50 py-16 justify-center">
          <Loader2 size={20} className="animate-spin" />
          <span className="text-sm">Recalculando os hashes da cadeia de custódia…</span>
        </div>
      </Moldura>
    )
  }

  if (erro || !dados) {
    return (
      <Moldura>
        <div className="bg-rose-500/[0.07] border border-rose-500/30 rounded-sm p-7">
          <div className="flex items-start gap-4">
            <ShieldAlert size={26} className="text-rose-400 shrink-0 mt-0.5" />
            <div>
              <h1 className="text-lg font-bold text-white">Documento não localizado</h1>
              <p className="text-white/60 text-sm mt-2 leading-relaxed">{erro}</p>
              <p className="text-white/35 text-[13px] mt-4 leading-relaxed">
                Confira se o protocolo e o código de verificação correspondem
                exatamente aos impressos na última página do dossiê. Se o
                documento foi recebido por terceiros, peça a via original.
              </p>
            </div>
          </div>
        </div>
      </Moldura>
    )
  }

  const { embarcacao, custodia, integridade } = dados
  const integro = integridade.integro

  return (
    <Moldura>
      {/* Veredito */}
      <div className={`rounded-sm p-7 border ${integro
        ? 'bg-emerald-500/[0.07] border-emerald-500/30'
        : 'bg-amber-500/[0.07] border-amber-500/30'}`}>
        <div className="flex items-start gap-4">
          <ShieldCheck size={28} className={integro ? 'text-emerald-400 shrink-0' : 'text-amber-400 shrink-0'} />
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-white">
              {integro ? 'Documento autêntico' : 'Documento autêntico — integridade parcial'}
            </h1>
            <p className="text-white/60 text-sm mt-2 leading-relaxed">
              {integro
                ? 'Este dossiê foi emitido pela plataforma Yachts Atlas e a cadeia de custódia está íntegra.'
                : `${integridade.registros_com_hash} de ${integridade.total} registros com hash verificado. Solicite esclarecimento ao custodiante.`}
            </p>
            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-[11px] uppercase tracking-[0.12em] text-white/40">
              <span>Protocolo <span className="text-[#c5a059] font-bold">{dados.protocolo}</span></span>
              <span>Emitido em <span className="text-white/70 font-bold">{dados.emitido_em.replace(/-/g, '/')}</span></span>
            </div>
          </div>
        </div>
      </div>

      {/* Embarcação */}
      <div className="mt-5 bg-[#021a3d] border border-white/10 rounded-sm p-6">
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059]">
          <Anchor size={13} /> Embarcação
        </div>
        <div className="mt-3 flex items-end justify-between gap-4 flex-wrap">
          <div>
            <div className="text-2xl font-serif font-bold text-white">{embarcacao.nome}</div>
            {embarcacao.ficha && (
              <div className="text-white/45 text-sm mt-1">{embarcacao.ficha}</div>
            )}
          </div>
          {embarcacao.classificacao && (
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#ffcf8a]
                             bg-[#c5a059]/[0.14] border border-[#c5a059]/40 px-4 py-2 rounded-sm">
              {/* "Índice de Custódia", não "Classificação". O número mede
                  abrangência de registro (50% categorias preenchidas, 25%
                  volume de manutenção, 15% documentos) — nada sobre a condição
                  da embarcação. Um barco com o casco furado pontua igual a um
                  intacto com o mesmo tanto de registro. Chamar de
                  "Classificação" fazia o comprador ler como estado do ativo, o
                  que contradiz a própria FAQ do site: o Atlas não inspecciona. */}
              Índice de Custódia: {embarcacao.classificacao}
            </span>
          )}
        </div>
        {custodia.arquivado && (
          <div className="mt-4 flex items-center gap-2 text-amber-300/80 text-[13px]
                          bg-amber-500/[0.07] border-l-2 border-amber-500 px-3 py-2 rounded-sm">
            <Archive size={14} /> Ativo arquivado — o histórico permanece selado e íntegro.
          </div>
        )}
      </div>

      {/* Custódia em números */}
      <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { n: custodia.registros_selados, l: 'Registros selados', Icon: FileCheck },
          { n: custodia.documentos_selados, l: 'Documentos selados', Icon: FileCheck },
          { n: custodia.retificacoes, l: 'Retificações', Icon: FileCheck },
          { n: custodia.desde || '—', l: 'Custódia desde', Icon: Clock },
        ].map(({ n, l, Icon }) => (
          <div key={l} className="bg-[#021a3d] border border-white/10 rounded-sm p-4">
            <Icon size={14} className="text-[#c5a059]/60 mb-2" />
            <div className="text-xl font-serif font-bold text-white leading-none">{n}</div>
            <div className="text-[9px] font-black uppercase tracking-[0.15em] text-white/35 mt-2">{l}</div>
          </div>
        ))}
      </div>

      {/* Integridade */}
      <div className="mt-5 bg-[#021a3d] border border-white/10 rounded-sm p-6">
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059]">
          Integridade da cadeia
        </div>
        <p className="text-white/60 text-[13px] mt-3 leading-relaxed">
          Cada registro recebe um hash <span className="text-white/80">{integridade.algoritmo}</span> no
          momento em que é selado. Registros selados não podem ser editados nem
          excluídos — nem pela própria plataforma. Correções são feitas por
          retificação, e o registro original permanece visível ao lado da correção.
        </p>
        <div className="mt-4 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
          <div className={`h-full rounded-full ${integro ? 'bg-emerald-400' : 'bg-amber-400'}`}
               style={{ width: `${integridade.total ? (integridade.registros_com_hash / integridade.total) * 100 : 0}%` }} />
        </div>
        <div className="mt-2 text-[11px] text-white/40">
          {integridade.registros_com_hash} de {integridade.total} registros com hash verificado
        </div>
      </div>

      {/* Impressão digital do documento.

          A assinatura do QR cobre protocolo + data de emissão, NÃO o conteúdo:
          quem recebesse um dossiê legítimo podia editar valores, apagar o
          histórico de sinistros, e o QR continuaria dizendo "autêntico".

          Este bloco fecha isso. O portador calcula o SHA-256 do próprio PDF e
          compara com o que a plataforma registrou ao emitir. Bateu, é o
          original; não bateu, foi mexido depois da emissão. */}
      {dados.documentos_emitidos && dados.documentos_emitidos.length > 0 && (
        <div className="mt-5 bg-[#021a3d] border border-white/10 rounded-sm p-6">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059]">
            Impressão digital do documento
          </div>
          <p className="text-white/60 text-[13px] mt-3 leading-relaxed">
            O PDF entregue pela plataforma tem a impressão digital abaixo. Se o
            documento em suas mãos tiver outra, ele foi <span className="text-white/80">alterado
            depois da emissão</span> — o QR Code sozinho não detecta edição de conteúdo.
          </p>
          <div className="mt-4 space-y-2">
            {dados.documentos_emitidos.map((d) => (
              <div key={d.hash} className="bg-black/25 border border-white/5 rounded-sm px-4 py-3">
                <div className="text-[10px] uppercase tracking-[0.15em] text-white/35">
                  Emitido em {d.emitido_em}
                </div>
                <div className="font-mono text-[11px] text-[#c5a059] break-all mt-1 leading-relaxed">
                  {d.hash}
                </div>
              </div>
            ))}
          </div>
          {typeof dados.documentos_emitidos_total === 'number' &&
           dados.documentos_emitidos_total > dados.documentos_emitidos.length && (
            /* Sem este aviso, o portador de uma via antiga não encontra a dele na
               lista e conclui que o documento é falso — o oposto do que esta
               página existe para fazer. A conferência automática não tem o
               limite de 5: ela busca a impressão digital em todas as emissões. */
            <p className="text-amber-300/60 text-[11.5px] mt-4 leading-relaxed">
              Mostrando as {dados.documentos_emitidos.length} vias mais recentes de{' '}
              <span className="text-amber-300/90">{dados.documentos_emitidos_total}</span>.
              Se a sua não estiver aqui, use a conferência automática abaixo — ela
              alcança todas.
            </p>
          )}
          <p className="text-white/30 text-[11.5px] mt-4 leading-relaxed">
            Mais de uma linha significa mais de uma via legítima emitida — a sua
            precisa bater com <span className="text-white/50">uma delas</span>.
            {' '}<a href="/conferir" className="text-[#c5a059] underline underline-offset-2">
              Confira seu arquivo automaticamente
            </a>{' '}— ele não sai do seu computador. No terminal:{' '}
            <span className="text-white/50 font-mono">shasum -a 256 dossie.pdf</span> (macOS/Linux)
            ou <span className="text-white/50 font-mono">certutil -hashfile dossie.pdf SHA256</span> (Windows).
          </p>
        </div>
      )}

      {/* Aviso de escopo */}
      <p className="mt-5 text-white/30 text-[12px] leading-relaxed">{dados.aviso}</p>
    </Moldura>
  )
}
