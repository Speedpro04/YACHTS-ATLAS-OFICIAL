import { createClient } from '@supabase/supabase-js'

// Fallbacks fixos. A chave publishable é PÚBLICA por design (roda no navegador,
// protegida por RLS) — gravá-la aqui garante login mesmo se o build arg estiver
// vazio ou com a chave LEGADA desativada (eyJ..., desligada pela Supabase em jun/2026).
const SUPABASE_URL_FALLBACK = 'https://owzelkiyorumnlaycral.supabase.co'
const SUPABASE_KEY_FALLBACK = 'sb_publishable_8LUgM9ojfBs_RPQ2cPgHNA_jxBlIDHE'

const envUrl = import.meta.env.VITE_SUPABASE_URL || ''
const envKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

const supabaseUrl = envUrl || SUPABASE_URL_FALLBACK
// Só aceita chave no formato novo (sb_*). Chave legada (eyJ...) está morta → usa o fallback.
const supabaseKey = envKey.startsWith('sb_') ? envKey : SUPABASE_KEY_FALLBACK

export const supabase = createClient(supabaseUrl, supabaseKey)

export const API_URL = '/api/v1'

/** Situação derivada de um registro selado (view vw_registros_situacao). */
export type SituacaoRegistro = 'vigente' | 'retificado' | 'retificador'

export interface RegistroPayload {
  ativo_id: string
  categoria: string
  titulo?: string
  observacao?: string
  dados?: Record<string, unknown>
  checklist?: unknown[]
  status?: 'registrado' | 'pendente' | 'atencao' | 'concluido'
}

export class ApiError extends Error {
  status: number
  details: unknown

  constructor(message: string, status: number, details: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

// Dedupe + cache curto de GETs: colapsa rajadas de requisições idênticas (várias
// seções pedindo /registros/{id} ao mesmo tempo) numa ÚNICA ida à rede — era isso
// que deixava a tela lenta. Qualquer escrita (POST/PUT/DELETE) limpa o cache para
// manter o dado fresco logo após um cadastro.
const _getCache = new Map<string, { ts: number; promise: Promise<any> }>()
const GET_CACHE_TTL = 1500 // ms — janela curta: junta a rajada, mantém leitura fresca

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const method = (options.method || 'GET').toUpperCase()

  // Escrita invalida o cache de leitura (após criar/editar, a próxima lista vem nova)
  if (method !== 'GET') {
    _getCache.clear()
    return _rawRequest(endpoint, options)
  }

  // GET: reaproveita a requisição em voo / recém-feita para o mesmo endpoint
  const cached = _getCache.get(endpoint)
  if (cached && Date.now() - cached.ts < GET_CACHE_TTL) return cached.promise

  const promise = _rawRequest(endpoint, options)
  _getCache.set(endpoint, { ts: Date.now(), promise })
  promise.catch(() => _getCache.delete(endpoint)) // erro não fica grudado no cache
  return promise
}

async function _rawRequest(endpoint: string, options: RequestInit = {}) {
  // Token da sessão real do Supabase (login unificado backend <-> frontend)
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  
  if (!response.ok) {
    let details: unknown = null
    let message = `Request failed (${response.status})`

    try {
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const payload = await response.json()
        details = payload
        if (payload && typeof payload === 'object' && 'detail' in payload) {
          const detailValue = (payload as { detail?: unknown }).detail
          if (typeof detailValue === 'string' && detailValue.trim()) {
            message = detailValue
          }
        }
      } else {
        const text = await response.text()
        if (text.trim()) {
          details = text
          message = text
        }
      }
    } catch {
      details = null
    }

    throw new ApiError(message, response.status, details)
  }
  
  if (response.status === 204) {
    return null
  }

  return response.json()
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
    signup: (data: { email: string; password: string; nome: string }) =>
      apiRequest('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
    // Sessão do Supabase é criada no navegador, mas quem decide se a conta pode
    // USAR o sistema é o backend: responde 402 com o motivo quando o pagamento
    // está pendente ou em atraso. Ver PrivateRoute e app/core/acesso.py.
    me: () => apiRequest('/auth/me'),
    logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  },
  owner: {
    /**
     * Manda ao armador o código de acesso ao portal, por e-mail e WhatsApp.
     * Responde 200 mesmo para e-mail desconhecido — dizer "não existe"
     * entregaria de graça quem é dono de barco na plataforma.
     */
    codigo: (email: string) =>
      apiRequest('/owner/codigo', { method: 'POST', body: JSON.stringify({ email }) }),
  },
  leads: {
    // Vagas fundadoras reais (20 no total, 4 por estado). Conta como ocupada
    // tanto a paga quanto a reservada dentro do prazo — é o mesmo número que
    // decide o preço no cadastro, então a página nunca promete uma vaga que o
    // checkout vai negar.
    vagasFundadoras: (): Promise<{
      total: number; ocupadas: number; restantes: number; vagas_por_estado: number
      estados: string[]
      por_estado: Record<string, { total: number; ocupadas: number; restantes: number }>
    }> => apiRequest('/leads/marina/vagas'),
    marina: (data: { marina: string; name: string; email: string; fleet: string; source?: string }) =>
      apiRequest('/leads/marina', { method: 'POST', body: JSON.stringify(data) }),
    parceiro: (data: { categoria: string; empresa: string; responsavel: string; email: string; telefone?: string; cidade?: string; mensagem?: string }) =>
      apiRequest('/leads/parceiro', { method: 'POST', body: JSON.stringify(data) }),
    // Cadastro da marina: retorna { modo: 'gratis' | 'pago' }. 'gratis' = vaga
    // fundadora pré-autorizada (6 meses, sem checkout); 'pago' = segue p/ Stripe,
    // e aí o backend manda em checkout_url qual oferta abrir — fundadora
    // (USD 200, 20 vagas) enquanto houver vaga, oficial (USD 250) depois.
    registrarMarina: (data: {
      name: string; email: string; password: string;
      cnpj?: string; phone?: string; city?: string; state?: string; website?: string
      // Quem indicou: só dá para capturar no cadastro — depois ninguém lembra.
      indicada_por?: string
    }): Promise<{
      modo: 'gratis' | 'pago'; marina?: string; billing_starts_at?: string; slot_number?: number
      oferta?: 'fundadora' | 'oficial'; preco_mensal?: number
      vagas_restantes?: number; checkout_url?: string
    }> =>
      apiRequest('/leads/marina/registrar', { method: 'POST', body: JSON.stringify(data) }),
  },
  parceiros: {
    // Fire-and-forget: registra o clique sem bloquear a navegação (keepalive)
    registrarClique: (data: { partner_id: string; categoria: string; tipo_contato: 'whatsapp' | 'email' | 'site' }) => {
      try {
        fetch(`${API_URL}/parceiros/clique`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
          keepalive: true,
        }).catch(() => {})
      } catch {
        /* nunca interromper o usuário por causa do rastreio */
      }
    },
  },
  normas: {
    list: () => apiRequest('/normas/'),
  },
  chatbot: {
    ask: (mensagem: string, session_id?: string) =>
      apiRequest('/chatbot/ask', {
        method: 'POST',
        body: JSON.stringify({ mensagem, session_id }),
      }),
  },
  registros: {
    /** Registros SELADOS, já com a situação derivada (vigente/retificado/retificador). */
    list: (ativoId: string) => apiRequest(`/registros/${ativoId}`),
    /** Sela direto. IRREVERSÍVEL — não pode ser editado nem excluído depois. */
    create: (data: RegistroPayload) =>
      apiRequest('/registros/', { method: 'POST', body: JSON.stringify(data) }),
    stats: (ativoId: string) => apiRequest(`/registros/stats/${ativoId}`),
    /**
     * Corrige um registro já selado. Não apaga nem altera o original: cria um
     * novo apontando pra ele. Os dois aparecem no dossiê, com o motivo à vista.
     */
    retificar: (data: RegistroPayload & { retifica_id: string; motivo_retificacao: string }) =>
      apiRequest('/registros/retificar', { method: 'POST', body: JSON.stringify(data) }),
    /** Rascunhos: editáveis e descartáveis. Não entram no dossiê. */
    rascunho: {
      list: (ativoId: string) => apiRequest(`/registros/rascunho/${ativoId}`),
      create: (data: RegistroPayload) =>
        apiRequest('/registros/rascunho', { method: 'POST', body: JSON.stringify(data) }),
      update: (id: string, data: Partial<RegistroPayload>) =>
        apiRequest(`/registros/rascunho/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
      descartar: (id: string) =>
        apiRequest(`/registros/rascunho/${id}`, { method: 'DELETE' }),
      /** Sela o rascunho. A partir daqui não há volta. */
      selar: (id: string) =>
        apiRequest(`/registros/rascunho/${id}/selar`, { method: 'POST' }),
    },
  },
  ativos: {
    list: () => apiRequest('/ativos'),
    create: (data: any) => apiRequest('/ativos', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => apiRequest(`/ativos/${id}`),
    /**
     * Define ou troca o dono da embarcação. É o que dá ao armador acesso ao
     * Portal do Proprietário: ele entra digitando este e-mail e vê só o barco
     * dele. E-mail vazio desfaz o vínculo — barco vendido.
     */
    definirProprietario: (id: string, dados: { proprietario_email?: string | null; proprietario_telefone?: string | null }) =>
      apiRequest(`/ativos/${id}/proprietario`, { method: 'PATCH', body: JSON.stringify(dados) }),
    /**
     * Arquiva o ativo — NÃO apaga. Um ativo com registros selados não pode ser
     * excluído: a cadeia de custódia é o produto.
     */
    arquivar: (id: string, motivo?: string) =>
      apiRequest(`/ativos/${id}${motivo ? `?motivo=${encodeURIComponent(motivo)}` : ''}`, {
        method: 'DELETE',
      }),
  },
  documentos: {
    list: (ativoId: string) => apiRequest(`/documentos/ativo/${ativoId}`),
    upload: async (
      ativoId: string,
      tipo: string,
      categoria: string,
      formData: FormData,
      geo?: { lat: number; lng: number; acc?: number } | null,
      descricao?: string,
    ) => {
      const { data: { session } } = await supabase.auth.getSession()
      const params = new URLSearchParams({ tipo, categoria })
      if (descricao && descricao.trim()) params.set('descricao', descricao.trim())
      if (geo && Number.isFinite(geo.lat) && Number.isFinite(geo.lng)) {
        params.set('latitude', String(geo.lat))
        params.set('longitude', String(geo.lng))
        if (typeof geo.acc === 'number' && Number.isFinite(geo.acc)) params.set('geo_precisao', String(geo.acc))
        params.set('geo_fonte', 'dispositivo')
      }
      const response = await fetch(`${API_URL}/documentos/upload/${ativoId}?${params.toString()}`, {
        method: 'POST',
        headers: session?.access_token ? { 'Authorization': `Bearer ${session.access_token}` } : {},
        body: formData,
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        const message = (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string')
          ? payload.detail
          : `Upload falhou (${response.status})`
        throw new ApiError(message, response.status, payload)
      }
      return payload
    },
    get: (id: string) => apiRequest(`/documentos/${id}`),
    download: (id: string) => apiRequest(`/documentos/${id}/download`),
  },
  integridade: {
    verify: (docId: string) => apiRequest(`/integridade/${docId}/verify`),
    relatorio: (ativoId: string) => apiRequest(`/integridade/ativo/${ativoId}/relatorio`),
  },
  pagamentos: {
    planos: () => apiRequest('/payments/plans'),
    checkoutOnboarding: (data: {
      email: string,
      marina_id: string,
      success_url: string,
      cancel_url: string,
    }) => apiRequest('/payments/checkout/onboarding', { method: 'POST', body: JSON.stringify(data) }),
  },
  dossie: {
    // Pedido público de dossiê (broker / comprador / seguradora)
    solicitar: (data: {
      solicitante_nome: string
      solicitante_email: string
      solicitante_telefone?: string
      finalidade?: 'venda' | 'seguro' | 'outro'
      marina_nome?: string
      ativo_id?: string
      mensagem?: string
    }) => apiRequest('/dossie/solicitar', { method: 'POST', body: JSON.stringify(data) }),
    // Painel (autenticado): listar / liberar / recusar pedidos
    listSolicitacoes: (status?: string) =>
      apiRequest(`/dossie/solicitacoes${status ? `?status=${status}` : ''}`),
    liberar: (id: string) =>
      apiRequest(`/dossie/solicitacoes/${id}/liberar`, { method: 'POST' }),
    recusar: (id: string) =>
      apiRequest(`/dossie/solicitacoes/${id}/recusar`, { method: 'POST' }),
    // Gera o PDF do dossiê do próprio ativo (dono/marina) e devolve uma URL local
    pdfUrl: async (ativoId: string) => {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${API_URL}/dossie/${ativoId}/pdf`, {
        headers: session?.access_token ? { 'Authorization': `Bearer ${session.access_token}` } : {},
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => null)
        const message = (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string')
          ? payload.detail
          : `Falha ao gerar dossiê (${response.status})`
        throw new ApiError(message, response.status, payload)
      }
      const blob = await response.blob()
      return URL.createObjectURL(blob)
    },
  },
}
