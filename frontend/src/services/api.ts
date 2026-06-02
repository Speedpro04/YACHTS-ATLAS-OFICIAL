import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseKey)

export const API_URL = '/api/v1'

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

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('yachts_token')
  
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
    logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  },
  leads: {
    marina: (data: { marina: string; name: string; email: string; fleet: string; source?: string }) =>
      apiRequest('/leads/marina', { method: 'POST', body: JSON.stringify(data) }),
  },
  registros: {
    list: (ativoId: string) => apiRequest(`/registros/${ativoId}`),
    create: (data: { ativo_id: string; categoria: string; titulo: string; descricao: string }) =>
      apiRequest('/registros/', { method: 'POST', body: JSON.stringify(data) }),
    stats: (ativoId: string) => apiRequest(`/registros/stats/${ativoId}`),
  },
  ativos: {
    list: () => apiRequest('/ativos'),
    create: (data: any) => apiRequest('/ativos', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => apiRequest(`/ativos/${id}`),
    delete: (id: string) => apiRequest(`/ativos/${id}`, { method: 'DELETE' }),
  },
  documentos: {
    list: (ativoId: string) => apiRequest(`/documentos/ativo/${ativoId}`),
    upload: (ativoId: string, tipo: string, categoria: string, formData: FormData) => fetch(`${API_URL}/documentos/upload/${ativoId}?tipo=${tipo}&categoria=${categoria}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('yachts_token')}` },
      body: formData,
    }).then(r => r.json()),
    get: (id: string) => apiRequest(`/documentos/${id}`),
    download: (id: string) => apiRequest(`/documentos/${id}/download`),
  },
  integridade: {
    verify: (docId: string) => apiRequest(`/integridade/${docId}/verify`),
    relatorio: (ativoId: string) => apiRequest(`/integridade/ativo/${ativoId}/relatorio`),
  },
  pagamentos: {
    planos: () => apiRequest('/payments/plans'),
    checkoutDossie: (data: {
      dossier_level: 'compact' | 'executive' | 'superyacht',
      ativo_id: string,
      success_url: string,
      cancel_url: string,
    }) => apiRequest(`/payments/checkout/dossier?dossier_level=${data.dossier_level}&ativo_id=${data.ativo_id}&success_url=${encodeURIComponent(data.success_url)}&cancel_url=${encodeURIComponent(data.cancel_url)}`, { method: 'POST' }),
    checkoutOnboarding: (data: {
      email: string,
      marina_id: string,
      success_url: string,
      cancel_url: string,
    }) => apiRequest('/payments/checkout/onboarding', { method: 'POST', body: JSON.stringify(data) }),
  },
}
