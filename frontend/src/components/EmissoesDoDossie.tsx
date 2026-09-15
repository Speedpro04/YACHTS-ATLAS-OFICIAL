import { useCallback, useEffect, useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { api } from '../services/api'

/**
 * As emissões de dossiê desta Marina, e o que ela cobrou por cada uma.
 *
 * POR QUE ESTA TELA EXISTE. O painel sabia dizer "2 dossiês" e nada mais: qual
 * embarcação, quando, por quanto — nada. A Marina que precisava reemitir para
 * um comprador que perdeu o PDF gerava de novo sem saber que já havia emitido
 * aquele, gastando uma das quatro do ano.
 *
 * O DINHEIRO AQUI NÃO É NOSSO, e a tela precisa deixar isso claro. O dossiê é
 * combinado entre o dono da Marina e o dono do ativo e pago direto na conta
 * dela — 100% é dela. A plataforma não cobra, não intermedeia e não concilia:
 * guarda o número que ela digitou, para o controle dela. Por isso o rótulo diz
 * "informado pela Marina", e não "faturamento".
 *
 * UMA LINHA POR EMISSÃO, NUNCA AGRUPADA. O mesmo barco pode sair duas vezes no
 * mesmo dia — o Netuno II saiu às 10:36 e às 10:59 em 26/08. O protocolo é o
 * mesmo nas duas (ele identifica a EMBARCAÇÃO), então quem separa é a hora e o
 * hash do arquivo. Agrupar faria duas emissões legítimas parecerem uma
 * contagem em dobro.
 */

type Emissao = {
  id: string
  ativo_id: string
  nome: string
  comprimento: number | null
  protocolo: string
  emitido_em: string
  created_at: string
  hash_curto: string | null
  canal: string | null
  valor: number | null
  moeda: string | null
}

const MOEDAS: Record<string, string> = { BRL: 'R$', USD: 'US$', EUR: '€' }

function dinheiro(valor: number | null, moeda: string | null): string {
  if (valor === null || valor === undefined) return ''
  const simbolo = MOEDAS[(moeda || 'BRL').toUpperCase()] || (moeda || '')
  return `${simbolo} ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
}

export default function EmissoesDoDossie() {
  const [emissoes, setEmissoes] = useState<Emissao[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [editando, setEditando] = useState<string | null>(null)
  const [rascunho, setRascunho] = useState('')
  const [salvando, setSalvando] = useState('')

  const carregar = useCallback(async () => {
    try {
      const r = await api.dossie.emissoes()
      setEmissoes(r.emissoes || [])
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível carregar as emissões.')
    }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  async function salvar(emissao: Emissao) {
    const limpo = rascunho.trim().replace(/\./g, '').replace(',', '.')
    const valor = limpo === '' ? null : Number(limpo)
    if (valor !== null && (Number.isNaN(valor) || valor < 0)) {
      setErro('Valor inválido.')
      return
    }
    setSalvando(emissao.id)
    try {
      await api.dossie.anotarValor(emissao.id, valor, emissao.moeda || 'BRL')
      setEditando(null)
      await carregar()
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível salvar o valor.')
    } finally {
      setSalvando('')
    }
  }

  // Soma só o que está na mesma moeda. Misturar real com dólar daria um número
  // que não é nenhum dos dois — e ninguém perceberia olhando.
  const comValor = (emissoes || []).filter((e) => e.valor != null)
  const moedas = new Set(comValor.map((e) => (e.moeda || 'BRL').toUpperCase()))
  const total = comValor.reduce((s, e) => s + (e.valor || 0), 0)
  const moedaUnica = moedas.size === 1 ? [...moedas][0] : null

  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-sm p-6 space-y-5">
      <div>
        <h2 className="text-white font-bold text-sm flex items-center gap-2.5">
          <Download size={16} className="text-[#c5a059]" />
          Dossiês emitidos
        </h2>
        <p className="text-white/35 text-[11px] mt-2 leading-relaxed max-w-2xl">
          Cada emissão, com a data, o protocolo e a impressão digital do arquivo.
          O valor é <strong className="text-white/60">seu controle</strong>: você
          informa quanto cobrou, e o Atlas apenas guarda — o dossiê é combinado
          direto com o proprietário, e o valor é integralmente da Marina.
        </p>
      </div>

      {erro && (
        <div className="bg-rose-500/10 border border-rose-400/30 rounded-sm px-4 py-3">
          <p className="text-rose-200 text-[11px]">{erro}</p>
        </div>
      )}

      {emissoes === null ? (
        <p className="text-white/25 text-[11px] flex items-center gap-2">
          <Loader2 size={12} className="animate-spin" /> Carregando…
        </p>
      ) : emissoes.length === 0 ? (
        <p className="text-white/25 text-[11px]">
          Nenhum dossiê emitido ainda. Assim que o primeiro sair, ele aparece aqui.
        </p>
      ) : (
        <>
          <ul className="space-y-2">
            {emissoes.map((e) => {
              const quando = new Date(e.created_at)
              return (
                <li
                  key={e.id}
                  className="flex items-center gap-4 flex-wrap bg-white/[0.02] border border-white/5 rounded-sm px-4 py-3"
                >
                  <div className="min-w-[200px] flex-1">
                    <p className="text-white/80 text-sm truncate">
                      {e.nome}
                      {e.comprimento ? (
                        <span className="text-white/30"> · {e.comprimento} pés</span>
                      ) : null}
                    </p>
                    {/* Hora e hash: é o que separa duas emissões do MESMO barco.
                        O protocolo vem igual nas duas — ele é da embarcação. */}
                    <p className="text-white/25 text-[9px] uppercase tracking-widest mt-1">
                      {quando.toLocaleDateString('pt-BR')} às{' '}
                      {quando.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      {e.hash_curto ? <> · <span className="font-mono">{e.hash_curto}</span></> : null}
                    </p>
                  </div>

                  {editando === e.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        autoFocus
                        value={rascunho}
                        onChange={(ev) => setRascunho(ev.target.value)}
                        onKeyDown={(ev) => {
                          if (ev.key === 'Enter') salvar(e)
                          if (ev.key === 'Escape') setEditando(null)
                        }}
                        inputMode="decimal"
                        placeholder="0,00"
                        className="w-28 bg-white/[0.03] border border-[#c5a059]/40 rounded-sm px-3 py-1.5 text-white text-sm text-right outline-none"
                      />
                      <button
                        onClick={() => salvar(e)}
                        disabled={salvando === e.id}
                        className="bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-40 text-[#010c20] px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
                      >
                        {salvando === e.id ? 'Salvando' : 'Salvar'}
                      </button>
                      <button
                        onClick={() => setEditando(null)}
                        className="text-white/40 hover:text-white/70 text-[9px] font-black uppercase tracking-widest"
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditando(e.id)
                        setRascunho(e.valor != null ? String(e.valor).replace('.', ',') : '')
                      }}
                      title="Informar quanto você cobrou por este dossiê"
                      className="text-sm px-3 py-1.5 rounded-sm border border-white/10 hover:border-[#c5a059]/40 transition-colors"
                    >
                      {e.valor != null ? (
                        <span className="text-white/80">{dinheiro(e.valor, e.moeda)}</span>
                      ) : (
                        <span className="text-white/25 text-[10px] uppercase tracking-widest font-black">
                          Informar valor
                        </span>
                      )}
                    </button>
                  )}
                </li>
              )
            })}
          </ul>

          {comValor.length > 0 && (
            <div className="flex items-baseline justify-between gap-4 pt-4 border-t border-white/5">
              <p className="text-white/30 text-[9px] uppercase tracking-[0.25em] font-black">
                Informado pela Marina · {comValor.length} de {emissoes.length}{' '}
                {emissoes.length === 1 ? 'emissão' : 'emissões'}
              </p>
              {/* Sem moeda única não há total: somar real com dólar entregaria
                  um número que não é nem um nem outro. */}
              <p className="text-white/80 text-lg">
                {moedaUnica
                  ? dinheiro(total, moedaUnica)
                  : <span className="text-white/30 text-[11px]">moedas diferentes — sem total</span>}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
