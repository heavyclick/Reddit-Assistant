import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Account endpoints
export const getAccounts = () => api.get('/accounts')
export const getAccount = (id: string) => api.get(`/accounts/${id}`)
export const createAccount = (data: any) => api.post('/accounts', data)
export const updateAccount = (id: string, data: any) => api.patch(`/accounts/${id}`, data)
export const deleteAccount = (id: string) => api.delete(`/accounts/${id}`)

// Draft endpoints
export const getDrafts = (params?: any) => api.get('/drafts', { params })
export const getDraft = (id: string) => api.get(`/drafts/${id}`)
export const approveDraft = (id: string, data: any) => api.post(`/drafts/${id}/approve`, data)
export const rejectDraft = (id: string, data: any) => api.post(`/drafts/${id}/reject`, data)
export const regenerateDraft = (id: string, instructions?: string) =>
  api.post(`/drafts/${id}/regenerate`, { custom_instructions: instructions })

// Opportunity endpoints
export const getOpportunities = (params?: any) => api.get('/opportunities', { params })

// Analytics endpoints
export const getAnalytics = (accountId: string, days = 30) =>
  api.get(`/analytics/${accountId}?days=${days}`)
export const getInsights = (accountId: string) => api.get(`/insights/${accountId}`)

// Job trigger endpoints
export const triggerMonitor = () => api.post('/jobs/monitor')
export const triggerGenerateDrafts = () => api.post('/jobs/generate-drafts')
export const triggerPostApproved = () => api.post('/jobs/post-approved')
export const triggerTrackPerformance = () => api.post('/jobs/track-performance')

export default api
