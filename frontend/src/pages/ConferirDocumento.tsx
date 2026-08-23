import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ShieldAlert, Loader2, UploadCloud, Lock, ArrowLeft } from 'lucide-react'
import { API_URL } from '../services/api'

/**
 * Contra-prova — "este PDF é mesmo o que o Yachts Atlas emitiu?"
 *
 * O ARQUIVO NUNCA SAI DO COMPUTADOR de quem verifica. O navegador calcula o
 * SHA-256 localmente (Web Crypto) e envia só a impressão digital. Isso resolve
 * o problema de confiança na ordem certa: ninguém deveria precisar entregar um
 * documento sigiloso a um terceiro só para descobrir se ele é legítimo. De
 * quebra é mais rápido e não custa banda.
 *
 * Aberta e gratuita de propósito. O efeito antifraude vem da EXISTÊNCIA da
 * conferência, não do preço — ninguém adultera um documento que qualquer um
 * confere em dois segundos. Cobrar aqui mataria justamente o que faz funcionar.
 */

type Resultado =
  | { corresponde: true; hash: string; protocolo: string; emitido_em: string; mensagem: string }
  | { corresponde: false; hash: string; mensagem: string }

export default function ConferirDocumento() {
  const [estado, setEstado] = useState<'ocioso' | 'lendo' | 'pronto'>('ocioso')
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [erro, setErro] = useState('')
  const [arrastando, setArrastando] = useState(false)
  const [nomeArquivo, setNomeArquivo] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const conferir = async (arquivo: File) => {
    setErro(''); setResultado(null); setNomeArquivo(arquivo.name); setEstado('lendo')
    try {
      // Web Crypto: o hash é calculado AQUI, no navegador. O arquivo não vai
      // para lugar nenhum — só os 64 caracteres do resultado.
      const buffer = await arquivo.arrayBuffer()
      const digest = await crypto.subtle.digest('SHA-256', buffer)
      const hash = Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, '0')).join('')

      const r = await fetch(`${API_URL}/verificar/documento/${hash}`)
      if (!r.ok) {
        const j = await r.json().catch(() => null)
        throw new Error(j?.detail || 'Não foi possível conferir agora.')
      }
      setResultado(await r.json())
      setEstado('pronto')
    } catch (ex) {
      setErro(ex instanceof Error ? ex.message : 'Não foi possível conferir agora.')
      setEstado('ocioso')
    }
  }

  const aoSoltar = (ev: React.DragEvent) => {
    ev.preventDefault(); setArrastando(false)
    const arquivo = ev.dataTransfer.files?.[0]
    if (arquivo) conferir(arquivo)
  }

  return (
    <div className="min-h-screen bg-[#010c20] text-white flex flex-col items-center px-5 py-10"
         style={{ background: 'radial-gradient(circle at 50% 0%, #021a3d 0%, #010c20 70%)' }}>
      <header className="w-full max-w-3xl mb-8">
        <div className="text-[#c5a059] font-black uppercase tracking-[0.3em] text-sm">Yachts Atlas</div>
        <div className="text-white/40 text-[10px] uppercase tracking-[0.15em] mt-1">
          Conferência de integridade do documento
        </div>
      </header>

      <main className="w-full max-w-3xl">
        <div className="bg-[#c5a059]/[0.04] border border-[#c5a059]/20 rounded-sm p-7">
          <h1 className="text-lg font-bold text-white">Este dossiê foi alterado?</h1>
          <p className="text-white/55 text-sm mt-2 leading-relaxed">
            Selecione o PDF do dossiê. A conferência compara a impressão digital
            do arquivo com a que o Yachts Atlas registrou no momento da emissão.
            Um único caractere alterado muda a impressão digital inteira.
          </p>

          {/* A garantia de privacidade vem ANTES da área de upload, de
              propósito: é a primeira dúvida de quem vai entregar um documento
              sigiloso a um site. */}
          <div className="mt-5 flex items-start gap-3 bg-emerald-500/[0.06] border border-emerald-500/20 rounded-sm px-4 py-3">
            <Lock size={15} className="text-emerald-400 shrink-0 mt-0.5" />
            <p className="text-emerald-100/70 text-[12.5px] leading-relaxed">
              <span className="text-emerald-300 font-semibold">O arquivo não sai do seu computador.</span>{' '}
              A impressão digital é calculada aqui, no seu navegador, e só ela é
              enviada — 64 caracteres. O conteúdo do dossiê nunca é transmitido.
            </p>
          </div>

          <div
            onDragOver={(ev) => { ev.preventDefault(); setArrastando(true) }}
            onDragLeave={() => setArrastando(false)}
            onDrop={aoSoltar}
            onClick={() => inputRef.current?.click()}
            className={`mt-5 border border-dashed rounded-sm px-6 py-10 text-center cursor-pointer
                        transition-colors ${arrastando
                          ? 'border-[#c5a059] bg-[#c5a059]/[0.07]'
                          : 'border-[#c5a059]/25 hover:border-[#c5a059]/50'}`}
          >
            {estado === 'lendo' ? (
              <div className="flex items-center justify-center gap-3 text-white/60">
                <Loader2 size={18} className="animate-spin" />
                <span className="text-sm">Calculando a impressão digital…</span>
              </div>
            ) : (
              <>
                <UploadCloud size={26} className="text-[#c5a059]/70 mx-auto" />
                <div className="text-white/70 text-sm mt-3">
                  Arraste o PDF aqui ou <span className="text-[#c5a059]">clique para selecionar</span>
                </div>
                {nomeArquivo && (
                  <div className="text-white/35 text-[12px] mt-2 font-mono">{nomeArquivo}</div>
                )}
              </>
            )}
            <input ref={inputRef} type="file" accept="application/pdf,.pdf" className="hidden"
                   onChange={(ev) => { const f = ev.target.files?.[0]; if (f) conferir(f) }} />
          </div>

          {erro && <p className="text-rose-400 text-[13px] mt-4">{erro}</p>}
        </div>

        {resultado && (
          <div className={`mt-5 rounded-sm p-7 border ${resultado.corresponde
            ? 'bg-emerald-500/[0.07] border-emerald-500/30'
            : 'bg-rose-500/[0.07] border-rose-500/30'}`}>
            <div className="flex items-start gap-4">
              {resultado.corresponde
                ? <ShieldCheck size={28} className="text-emerald-400 shrink-0" />
                : <ShieldAlert size={28} className="text-rose-400 shrink-0" />}
              <div className="min-w-0">
                <h2 className="text-xl font-bold text-white">
                  {resultado.corresponde ? 'Documento íntegro' : 'Não corresponde'}
                </h2>
                <p className="text-white/60 text-sm mt-2 leading-relaxed">{resultado.mensagem}</p>

                {resultado.corresponde && (
                  <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-[11px] uppercase tracking-[0.12em] text-white/40">
                    <span>Protocolo <span className="text-[#c5a059] font-bold">{resultado.protocolo}</span></span>
                    <span>Emitido em <span className="text-white/70 font-bold">{resultado.emitido_em}</span></span>
                  </div>
                )}

                <div className="mt-4 bg-black/25 border border-white/5 rounded-sm px-4 py-3">
                  <div className="text-[10px] uppercase tracking-[0.15em] text-white/35">
                    Impressão digital do arquivo
                  </div>
                  <div className="font-mono text-[11px] text-white/60 break-all mt-1 leading-relaxed">
                    {resultado.hash}
                  </div>
                </div>

                {!resultado.corresponde && (
                  <p className="text-white/35 text-[12.5px] mt-4 leading-relaxed">
                    Isso não significa necessariamente fraude: o arquivo pode ter
                    sido reimpresso, convertido ou salvo por outro programa, o que
                    altera os bytes sem mudar o conteúdo visível. Na dúvida, peça
                    a via original à marina custodiante.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        <Link to="/verificar"
              className="inline-flex items-center gap-2 text-white/40 hover:text-[#c5a059]
                         transition-colors mt-6 text-[11px] font-black uppercase tracking-[0.2em]">
          <ArrowLeft size={13} />
          Verificar autenticidade pelo protocolo
        </Link>
      </main>

      <footer className="w-full max-w-3xl mt-10 pt-5 border-t border-white/10
                         text-[10px] text-white/30 tracking-[0.1em]">
        AXOS HUB · CNPJ 26.998.571/0001-50 · yachtsatlas.online
      </footer>
    </div>
  )
}
