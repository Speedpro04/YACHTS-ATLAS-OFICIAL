import { useCallback, useEffect, useState } from 'react'
import { Camera, Check, Lock, PenLine } from 'lucide-react'
import { api } from '../services/api'
import ConfirmarSelo from './ConfirmarSelo'
import { rotuloDoCampo } from '../config/servicosCategorias'

/**
 * A mesa do escritório — o meio do caminho que faltava.
 *
 *     chega (Pré-Data)  ->  trabalha (aqui)  ->  sela (vira prova)
 *
 * O que vem do píer vem incompleto DE PROPÓSITO: mão suja, pressa, campo que a
 * ficha não perguntou, palavra escrita torto. Antes disto, o escritório tinha
 * duas opções — selar o erro para sempre ou não selar nada. Nenhuma das duas
 * serve para um documento que vai a uma seguradora.
 *
 * Aqui tudo é editável, e salvar não trava nada. Trava é o selo, que fica no
 * fim e tem confirmação própria. Depois dele, correção só por retificação —
 * e retificação aparece no dossiê ao lado do erro, para sempre.
 *
 * POR QUE DENTRO DA EMBARCAÇÃO, e não numa lista geral: o revisor precisa do
 * barco na frente para julgar o que lê. "Horímetro 412" não quer dizer nada
 * solto; quer dizer muito ao lado das outras 15 leituras daquele motor.
 */

type Foto = {
  id: string
  nome_arquivo: string
  categoria: string
  descricao: string | null
  created_at: string
  status: string
  url: string | null
}

type Item = {
  id: string
  categoria: string
  titulo: string | null
  observacao: string | null
  dados: Record<string, any>
  created_at: string
  fotos: Foto[]
}

/** Metadados de proveniência: não são campo do serviço e não se editam. */
const META = new Set([
  'origem', 'client_id', 'capturado_em', 'capturado_por', 'fotos_no_aparelho',
  'registrado_por', 'registrado_por_login', 'executado_por', 'condicao',
  'aprovado_em', 'aprovado_por', 'recusado_em', 'recusado_por', 'motivo_recusa',
  'original_do_pier',
  // A observação tem campo próprio, grande, aqui em cima. Os envios de 11/09
  // guardavam ela DENTRO de `dados`, e sem esta linha ela aparecia duas vezes:
  // vazia no campo de texto e espremida num input de 40 caracteres no meio dos
  // "Não" — que é onde a frase do mecânico some.
  'observacao',
])

const CONDICOES = ['concluido', 'atencao', 'pendente'] as const

export default function EmTrabalho({ ativoId }: { ativoId: string }) {
  const [itens, setItens] = useState<Item[] | null>(null)
  const [orfas, setOrfas] = useState<Foto[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState('')
  const [selar, setSelar] = useState<Item | null>(null)

  const carregar = useCallback(async () => {
    try {
      const r = await api.registros.emTrabalho(ativoId)
      setItens(r.em_trabalho || [])
      setOrfas(r.fotos_sem_registro || [])
      setErro(null)
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível carregar.')
    }
  }, [ativoId])

  useEffect(() => { carregar() }, [carregar])

  async function salvar(item: Item, campos: Record<string, any>) {
    setSalvando(item.id)
    try {
      await api.registros.rascunho.update(item.id, campos)
      await carregar()
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível salvar.')
    } finally {
      setSalvando('')
    }
  }

  async function selarItem(item: Item) {
    setSalvando(item.id)
    try {
      await api.registros.rascunho.selar(item.id)
      setSelar(null)
      await carregar()
    } catch (e: any) {
      setErro(e?.message || 'Não foi possível selar.')
    } finally {
      setSalvando('')
    }
  }

  // Nada em trabalho e nenhuma foto solta: a seção inteira some. Bloco vazio
  // permanente vira ruído, e quem não usa o Pré-Data nunca deveria vê-lo.
  if (itens !== null && itens.length === 0 && orfas.length === 0) return null

  return (
    <div className="bg-[#021431] border border-[#c5a059]/20 rounded-sm p-6 md:p-8 space-y-6">
      <div>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <PenLine size={20} className="text-[#c5a059]" /> Em trabalho
        </h2>
        <p className="text-white/30 text-[10px] mt-1.5 uppercase tracking-[0.3em] font-black">
          Veio do píer · ainda não selado · editável
        </p>
      </div>

      {erro && (
        <div className="bg-rose-500/10 border border-rose-400/30 rounded-sm px-4 py-3">
          <p className="text-rose-200 text-[11px] leading-relaxed">{erro}</p>
        </div>
      )}

      {(itens || []).map((item) => (
        <Cartao
          key={item.id}
          item={item}
          ocupado={salvando === item.id}
          onSalvar={(campos) => salvar(item, campos)}
          onSelar={() => setSelar(item)}
        />
      ))}

      {orfas.length > 0 && (
        <div className="border border-white/5 rounded-sm p-5">
          <p className="text-white/30 text-[9px] uppercase tracking-[0.3em] font-black mb-4">
            Fotos desta embarcação sem registro que as explique
          </p>
          <div className="flex flex-wrap gap-3">
            {orfas.map((f) => <Miniatura key={f.id} foto={f} />)}
          </div>
        </div>
      )}

      {/* Letras miúdas, e não aviso grande: é informação de rodapé de contrato,
          para quem procura. Vira alarme se ganhar destaque. */}
      <p className="text-white/20 text-[10px] leading-relaxed pt-4 border-t border-white/5">
        Tudo fica armazenado no banco de dados, inclusive o que veio do píer antes
        das edições. Disponível em caso de auditoria.
      </p>

      {selar && (
        <ConfirmarSelo
          titulo={selar.titulo || 'Registro de campo'}
          categoria={selar.categoria}
          enviando={salvando === selar.id}
          onConfirmar={() => selarItem(selar)}
          onCancelar={() => setSelar(null)}
        />
      )}
    </div>
  )
}

function Miniatura({ foto }: { foto: Foto }) {
  if (!foto.url) {
    return (
      <span
        className="w-20 h-20 rounded-sm border border-amber-500/30 bg-amber-500/5 flex items-center justify-center"
        title="A imagem não pôde ser carregada"
      >
        <Camera size={18} className="text-amber-500/60" />
      </span>
    )
  }
  return (
    <a
      href={foto.url}
      target="_blank"
      rel="noreferrer"
      title={`${foto.nome_arquivo} — abrir em tamanho real`}
      className="w-20 h-20 rounded-sm overflow-hidden border border-white/10 hover:border-[#c5a059]/50 transition-colors"
    >
      <img src={foto.url} alt={foto.nome_arquivo} loading="lazy" className="w-full h-full object-cover" />
    </a>
  )
}

function Cartao({
  item,
  ocupado,
  onSalvar,
  onSelar,
}: {
  item: Item
  ocupado: boolean
  onSalvar: (campos: Record<string, any>) => void
  onSelar: () => void
}) {
  const d = item.dados || {}
  const camposDoServico = Object.keys(d).filter((k) => !META.has(k))

  const [titulo, setTitulo] = useState(item.titulo || '')
  // Lê os dois formatos: a coluna (app atual) e `dados.observacao` (app de 11/09).
  const [observacao, setObservacao] = useState(item.observacao || String(d.observacao || ''))
  const [condicao, setCondicao] = useState(String(d.condicao || 'concluido'))
  const [campos, setCampos] = useState<Record<string, string>>(
    Object.fromEntries(camposDoServico.map((k) => [k, String(d[k] ?? '')])),
  )

  const mudou =
    titulo !== (item.titulo || '') ||
    observacao !== (item.observacao || String(d.observacao || '')) ||
    condicao !== String(d.condicao || 'concluido') ||
    camposDoServico.some((k) => campos[k] !== String(d[k] ?? ''))

  const salvar = () => {
    // A observação passa a viver na COLUNA, uma só. Sai de `dados` para não
    // existir em dois lugares — duas cópias do mesmo texto divergem na primeira
    // edição, e aí ninguém sabe qual delas o dossiê vai imprimir. O que veio do
    // píer continua guardado em `original_do_pier`, intocado.
    const { observacao: _antiga, ...resto } = d
    onSalvar({
      titulo: titulo.trim() || null,
      observacao: observacao.trim() || null,
      dados: { ...resto, ...campos, condicao },
    })
  }

  const editado = Boolean(d.original_do_pier)

  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-sm p-5 space-y-5">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="O que foi feito"
          className="flex-1 min-w-[240px] bg-transparent border-b border-white/10 focus:border-[#c5a059]/50 text-white font-bold text-base outline-none transition-colors pb-1"
        />
        <p className="text-white/30 text-[9px] uppercase tracking-[0.25em] font-black">
          {item.categoria} ·{' '}
          {new Date(item.created_at).toLocaleDateString('pt-BR')}
          {editado && ' · editado'}
        </p>
      </div>

      <div>
        <label className="block text-white/25 text-[9px] uppercase tracking-[0.25em] font-black mb-2">
          Observação de quem executou
        </label>
        <textarea
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
          rows={3}
          placeholder="Sem observação"
          className="w-full bg-white/[0.03] border border-white/10 focus:border-[#c5a059]/40 rounded-sm px-4 py-3 text-white/85 text-sm leading-relaxed outline-none transition-colors placeholder:text-white/15"
        />
      </div>

      <div>
        <label className="block text-white/25 text-[9px] uppercase tracking-[0.25em] font-black mb-2">
          Condição
        </label>
        <div className="flex gap-2">
          {CONDICOES.map((c) => (
            <button
              key={c}
              onClick={() => setCondicao(c)}
              className={`px-4 py-2 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all border ${
                condicao === c
                  ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]'
                  : 'border-white/10 text-white/40 hover:border-white/25'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {camposDoServico.length > 0 && (
        <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {camposDoServico.map((k) => (
            <div key={k} className="flex items-center justify-between gap-3">
              <label className="text-white/25 text-[9px] uppercase tracking-[0.2em] font-black truncate">
                {rotuloDoCampo(k)}
              </label>
              <input
                value={campos[k] ?? ''}
                onChange={(e) => setCampos({ ...campos, [k]: e.target.value })}
                className="w-40 bg-white/[0.03] border border-white/10 focus:border-[#c5a059]/40 rounded-sm px-3 py-1.5 text-white/80 text-sm text-right outline-none transition-colors"
              />
            </div>
          ))}
        </div>
      )}

      {item.fotos.length > 0 && (
        <div>
          <p className="text-white/25 text-[9px] uppercase tracking-[0.25em] font-black mb-3">
            {item.fotos.length === 1 ? 'Foto deste serviço' : `${item.fotos.length} fotos deste serviço`}
          </p>
          <div className="flex flex-wrap gap-3">
            {item.fotos.map((f) => <Miniatura key={f.id} foto={f} />)}
          </div>
        </div>
      )}

      <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-4 flex-wrap">
        <p className="text-white/25 text-[9px] uppercase tracking-widest">
          Executou {d.executado_por || d.capturado_por || '—'} · registrou{' '}
          {d.registrado_por || d.capturado_por || '—'}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={salvar}
            disabled={ocupado || !mudou}
            className="flex items-center gap-2 border border-[#c5a059]/40 hover:bg-[#c5a059]/10 disabled:opacity-30 disabled:cursor-not-allowed text-[#c5a059] px-4 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
          >
            <Check size={12} />
            {ocupado ? 'Salvando' : mudou ? 'Salvar' : 'Salvo'}
          </button>
          {/* Selar fica separado e por último: é o único aqui que não tem volta. */}
          <button
            onClick={onSelar}
            disabled={ocupado || mudou}
            title={mudou ? 'Salve as alterações antes de selar' : undefined}
            className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-30 disabled:cursor-not-allowed text-[#010c20] px-4 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
          >
            <Lock size={12} /> Selar registro
          </button>
        </div>
      </div>
    </div>
  )
}
