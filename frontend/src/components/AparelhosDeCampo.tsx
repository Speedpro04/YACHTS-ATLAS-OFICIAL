import { useCallback, useEffect, useState } from 'react'
import { Smartphone, Plus, X, Copy, Check } from 'lucide-react'
import { api } from '../services/api'

/**
 * Os aparelhos que podem mandar pré-dado — e como cortar o acesso de um deles.
 *
 * Até aqui, o colaborador do píer entrava no Atlas Pré-Data com a conta da
 * Marina. A mesma senha abre o painel: dá para selar registro, emitir dossiê,
 * liberar documento a terceiro e ver a frota inteira. Com o código, o aparelho
 * entra sem saber a senha de ninguém, e só consegue ENVIAR.
 *
 * O código aparece UMA vez. Depois disso só existe o hash no banco — perdeu,
 * gera outro e revoga o antigo, que é o comportamento que se espera de um
 * segredo. Mostrar de novo seria transformar a lista de aparelhos numa lista de
 * chaves.
 */

type Codigo = {
  id: string
  apelido: string
  criado_em: string
  revogado_em: string | null
  ultimo_uso_em: string | null
}

export default function AparelhosDeCampo() {
  const [lista, setLista] = useState<Codigo[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [apelido, setApelido] = useState('')
  const [criando, setCriando] = useState(false)
  const [novo, setNovo] = useState<{ codigo: string; apelido: string } | null>(null)
  const [copiado, setCopiado] = useState(false)

  const carregar = useCallback(async () => {
    try {
      const r = await api.campo.listar()
      setLista(r.codigos || [])
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível carregar.')
    }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  async function criar() {
    setCriando(true)
    try {
      const r = await api.campo.criar(apelido.trim() || 'Aparelho de campo')
      setNovo({ codigo: r.codigo, apelido: r.apelido })
      setApelido('')
      setCopiado(false)
      await carregar()
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível gerar o código.')
    } finally {
      setCriando(false)
    }
  }

  async function revogar(c: Codigo) {
    try {
      await api.campo.revogar(c.id)
      await carregar()
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível revogar.')
    }
  }

  const ativos = (lista || []).filter((c) => !c.revogado_em)

  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-sm p-6 space-y-5">
      <div>
        <h2 className="text-white font-bold text-sm flex items-center gap-2.5">
          <Smartphone size={16} className="text-[#c5a059]" />
          Aparelhos do pátio
        </h2>
        <p className="text-white/35 text-[11px] mt-2 leading-relaxed max-w-2xl">
          Cada aparelho entra no Atlas Pré-Data com um código próprio, sem a senha
          da Marina. Com ele dá para <strong className="text-white/60">enviar</strong>{' '}
          serviço e foto — e só isso: selar registro, emitir dossiê e abrir o
          painel continuam exigindo a sua conta.
        </p>
      </div>

      {erro && (
        <div className="bg-rose-500/10 border border-rose-400/30 rounded-sm px-4 py-3">
          <p className="text-rose-200 text-[11px]">{erro}</p>
        </div>
      )}

      {/* O código recém-criado, à vista e só desta vez. */}
      {novo && (
        <div className="bg-[#c5a059]/10 border border-[#c5a059]/40 rounded-sm p-5 space-y-3">
          <p className="text-[#c5a059] text-[9px] uppercase tracking-[0.25em] font-black">
            Código de {novo.apelido}
          </p>
          <div className="flex items-center gap-3 flex-wrap">
            <code className="text-white text-2xl font-mono tracking-[0.2em]">{novo.codigo}</code>
            <button
              onClick={() => {
                navigator.clipboard?.writeText(novo.codigo)
                setCopiado(true)
              }}
              className="flex items-center gap-2 border border-[#c5a059]/40 hover:bg-[#c5a059]/10 text-[#c5a059] px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
            >
              {copiado ? <Check size={12} /> : <Copy size={12} />}
              {copiado ? 'Copiado' : 'Copiar'}
            </button>
          </div>
          <p className="text-white/50 text-[11px] leading-relaxed">
            Anote agora: ele não é exibido de novo. Se perder, gere outro e revogue
            este.
          </p>
          <button
            onClick={() => setNovo(null)}
            className="text-white/40 hover:text-white/70 text-[9px] font-black uppercase tracking-widest transition-colors"
          >
            Já anotei
          </button>
        </div>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <input
          value={apelido}
          onChange={(e) => setApelido(e.target.value)}
          placeholder="Ex: Celular do pátio"
          className="flex-1 min-w-[220px] bg-white/[0.03] border border-white/10 focus:border-[#c5a059]/40 rounded-sm px-4 py-2.5 text-white text-sm outline-none transition-colors placeholder:text-white/15"
        />
        <button
          onClick={criar}
          disabled={criando}
          className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-40 text-[#010c20] px-4 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
        >
          <Plus size={12} />
          {criando ? 'Gerando' : 'Gerar código'}
        </button>
      </div>

      {ativos.length > 0 && (
        <ul className="space-y-2">
          {ativos.map((c) => (
            <li
              key={c.id}
              className="flex items-center gap-4 bg-white/[0.02] border border-white/5 rounded-sm px-4 py-3"
            >
              <Smartphone size={14} className="text-white/25 shrink-0" />
              <span className="text-white/75 text-sm flex-1 truncate">{c.apelido}</span>
              <span className="text-white/25 text-[9px] uppercase tracking-widest shrink-0">
                {c.ultimo_uso_em
                  ? `usado em ${new Date(c.ultimo_uso_em).toLocaleDateString('pt-BR')}`
                  : 'nunca usado'}
              </span>
              <button
                onClick={() => revogar(c)}
                className="shrink-0 flex items-center gap-1.5 border border-white/10 hover:border-rose-400/40 hover:text-rose-400 text-white/40 px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
              >
                <X size={12} /> Revogar
              </button>
            </li>
          ))}
        </ul>
      )}

      {lista !== null && ativos.length === 0 && !novo && (
        <p className="text-white/25 text-[11px]">
          Nenhum aparelho com acesso. Gere um código para entregar ao colaborador.
        </p>
      )}
    </div>
  )
}
