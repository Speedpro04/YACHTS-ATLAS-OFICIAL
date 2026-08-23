import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, ArrowRight } from 'lucide-react'

/**
 * Entrada manual da verificação — o caminho de quem não conseguiu ler o QR.
 *
 * O dossiê impresso manda, em letras claras: "Sem câmera: acesse o endereço e
 * informe protocolo, código e data de emissão". Até agora esse endereço não
 * existia — `App.tsx` só declarava `/verificar/:protocolo`, e a página de
 * resultado respondia "Link incompleto. [...] informe o protocolo e o código"
 * sem oferecer um único campo para informar.
 *
 * Quem lê o dossiê é comprador, corretor e perito de seguradora, com o papel na
 * mão e um leitor de QR que pode simplesmente não abrir. Prometer uma saída
 * manual e não entregá-la é o que faz essa pessoa concluir que a verificação é
 * decorativa — e a verificação é o produto.
 *
 * Esta tela não valida nada: ela monta a MESMA URL que o QR carrega e entrega
 * para a página de resultado, que já existe e funciona. Uma porta de entrada,
 * não uma segunda implementação.
 */
export default function VerificacaoManual() {
  const navigate = useNavigate()
  const [protocolo, setProtocolo] = useState('')
  const [codigo, setCodigo] = useState('')
  const [emissao, setEmissao] = useState('')
  const [erro, setErro] = useState('')

  const verificar = (ev: React.FormEvent) => {
    ev.preventDefault()

    const p = protocolo.trim().toUpperCase()
    const c = codigo.trim().toLowerCase()
    const e = emissao.trim()

    if (!p || !c || !e) {
      setErro('Preencha os três campos impressos na última página do dossiê.')
      return
    }

    // A data vai no formato do QR (DD-MM-AAAA). O dossiê imprime com barras,
    // e é assim que a pessoa digita — converter aqui evita transformar um
    // detalhe de formato em "documento não localizado", que é a mensagem mais
    // desanimadora possível para quem está conferindo autenticidade.
    const dataQR = e.replace(/\//g, '-')

    navigate(`/verificar/${encodeURIComponent(p)}?s=${encodeURIComponent(c)}&e=${encodeURIComponent(dataQR)}`)
  }

  const campo = 'w-full bg-transparent border-b border-[#c5a059]/25 text-white py-2.5 ' +
    'outline-none focus:border-[#c5a059] transition-colors font-mono text-[15px] ' +
    'placeholder:text-white/20 placeholder:font-sans placeholder:italic'
  const rotulo = 'block text-[10px] uppercase tracking-[0.25em] text-[#c5a059]/70 font-bold mb-1'

  return (
    <div className="min-h-screen bg-[#010c20] text-white flex flex-col items-center px-5 py-10"
         style={{ background: 'radial-gradient(circle at 50% 0%, #021a3d 0%, #010c20 70%)' }}>
      <header className="w-full max-w-3xl mb-8">
        <div className="text-[#c5a059] font-black uppercase tracking-[0.3em] text-sm">Yachts Atlas</div>
        <div className="text-white/40 text-[10px] uppercase tracking-[0.15em] mt-1">
          Verificação de autenticidade do dossiê
        </div>
      </header>

      <main className="w-full max-w-3xl">
        <div className="bg-[#c5a059]/[0.04] border border-[#c5a059]/20 rounded-sm p-7">
          <div className="flex items-start gap-4 mb-7">
            <ShieldCheck size={26} className="text-[#c5a059] shrink-0 mt-0.5" />
            <div>
              <h1 className="text-lg font-bold text-white">Verificar um dossiê</h1>
              <p className="text-white/55 text-sm mt-2 leading-relaxed">
                Informe os três dados impressos na última página do dossiê, no
                quadro <span className="text-[#c5a059]">Verificação de Autenticidade</span>.
                A plataforma recalcula os hashes dos registros selados e confirma
                a autenticidade do documento.
              </p>
            </div>
          </div>

          <form onSubmit={verificar} className="space-y-6">
            <div>
              <label className={rotulo} htmlFor="v_protocolo">Protocolo</label>
              <input id="v_protocolo" className={campo} value={protocolo} autoFocus
                     onChange={(ev) => { setProtocolo(ev.target.value); setErro('') }}
                     placeholder="YA-IATE-2015-3A38" autoComplete="off" spellCheck={false} />
            </div>

            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className={rotulo} htmlFor="v_codigo">Código de verificação</label>
                <input id="v_codigo" className={campo} value={codigo}
                       onChange={(ev) => { setCodigo(ev.target.value); setErro('') }}
                       placeholder="8C8A4BC9E350" autoComplete="off" spellCheck={false} />
              </div>
              <div>
                <label className={rotulo} htmlFor="v_emissao">Data de emissão</label>
                <input id="v_emissao" className={campo} value={emissao}
                       onChange={(ev) => { setEmissao(ev.target.value); setErro('') }}
                       placeholder="22/08/2026" autoComplete="off" inputMode="numeric" />
              </div>
            </div>

            {erro && <p className="text-rose-400 text-[13px]">{erro}</p>}

            <div className="flex items-center justify-between gap-4 flex-wrap pt-1">
              <p className="text-white/30 text-[12px] leading-relaxed max-w-sm">
                Os três juntos são exclusivos deste documento. Sem eles, a consulta
                não retorna dados — nem o conteúdo do dossiê é exposto publicamente.
              </p>
              <button type="submit"
                      className="inline-flex items-center gap-3 bg-[#c5a059] hover:bg-[#e0bc5c]
                                 text-[#07070d] px-8 py-3.5 rounded-sm text-[11px] font-black
                                 uppercase tracking-[0.25em] transition-colors">
                Verificar
                <ArrowRight size={14} />
              </button>
            </div>
          </form>
        </div>

        <p className="text-white/25 text-[12px] mt-6 leading-relaxed">
          Com a câmera à mão, apontar para o QR Code impresso no dossiê preenche
          estes três campos automaticamente.
        </p>
      </main>

      <footer className="w-full max-w-3xl mt-10 pt-5 border-t border-white/10
                         text-[10px] text-white/30 tracking-[0.1em]">
        AXOS HUB · CNPJ 26.998.571/0001-50 · yachtsatlas.online
      </footer>
    </div>
  )
}
