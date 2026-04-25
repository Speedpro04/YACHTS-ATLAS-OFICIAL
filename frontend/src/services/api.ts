import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseKey)

export const API_URL = '/api/v1'

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
    throw new Error('Request failed')
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
  ativos: {
    list: () => apiRequest('/ativos'),
    create: (data: any) => apiRequest('/ativos', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => apiRequest(`/ativos/${id}`),
    delete: (id: string) => apiRequest(`/ativos/${id}`, { method: 'DELETE' }),
  },
  documentos: {
    list: (ativoId: string) => apiRequest(`/documentos/ativo/${ativoId}`),
    upload: (formData: FormData) => fetch(`${API_URL}/documentos/upload`, {
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
}