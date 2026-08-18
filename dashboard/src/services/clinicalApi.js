/* ============================================================
   clinicalApi.js — Camada de serviços do Módulo Clínico
   Centraliza todas as chamadas HTTP/WS ao kairos-clinical
   ============================================================ */

import axios from 'axios'

// ═══ Configuração ═══════════════════════════════════════════
// Usa proxy local do nginx (same-origin) para evitar problemas de CORS
const CLINICAL_API_URL = '/clinical-api'

const clinicalApi = axios.create({
  baseURL: CLINICAL_API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor para injetar token e tenant_slug
clinicalApi.interceptors.request.use((config) => {
  const session = sessionStorage.getItem('k-clinical-session')
  if (session) {
    try {
      const { token, tenantSlug } = JSON.parse(session)
      if (token) config.headers['Authorization'] = `Bearer ${token}`
      if (tenantSlug) config.headers['X-Tenant-Slug'] = tenantSlug
    } catch(e) {}
  }
  return config
})

// ═══ Health & Pre-Flight ════════════════════════════════════

export async function clinicalHealth() {
  const { data } = await clinicalApi.get('/health')
  return data
}

export async function runPreflight() {
  const { data } = await clinicalApi.get('/api/v1/clinical/preflight')
  return data
}

// ═══ SOAP ═══════════════════════════════════════════════════

export async function submitSoapAudio(file) {
  const formData = new FormData()
  formData.append('audio', file)
  const { data } = await clinicalApi.post('/api/v1/clinical/soap', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return data
}

export async function submitSoapText(text) {
  const { data } = await clinicalApi.post('/api/v1/clinical/soap/text', { text })
  return data
}

export async function uploadBackup(file, sessionId) {
  const formData = new FormData()
  formData.append('audio', file)
  formData.append('session_id', sessionId)
  const { data } = await clinicalApi.post('/api/v1/clinical/soap/backup', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return data
}

// ═══ Quarentena ═════════════════════════════════════════════

export async function fetchQuarantine(status = 'all') {
  const params = status ? { status } : { status: 'all' }
  const { data } = await clinicalApi.get('/api/v1/quarantine', { params })
  return data
}

export async function approveQuarantine(id, reviewer = 'admin') {
  const { data } = await clinicalApi.post(`/api/v1/quarantine/${id}/approve`, null, {
    params: { reviewer }
  })
  return data
}

export async function rejectQuarantine(id, notes = '', reviewer = 'admin') {
  const { data } = await clinicalApi.post(`/api/v1/quarantine/${id}/reject`, { notes, reviewer })
  return data
}

export async function suggestKnowledge(payload) {
  const { data } = await clinicalApi.post('/api/v1/quarantine/suggest', payload)
  return data
}

// ═══ Curador Científico ════════════════════════════════════

export async function ingestUrl(url) {
  const { data } = await clinicalApi.post('/api/v1/clinical/ingest', { url })
  return data
}

export async function previewUrl(url) {
  const { data } = await clinicalApi.post('/api/v1/clinical/ingest/preview', { url })
  return data
}

// ═══ Ademed (Documentos Médicos) ════════════════════════════

export async function listAdemedTemplates() {
  const { data } = await clinicalApi.get('/api/v1/clinical/ademed/templates')
  return data
}

export async function generateDocument(soap, templateType, patientInfo = {}) {
  const { data } = await clinicalApi.post('/api/v1/clinical/ademed/generate', {
    soap,
    template_type: templateType,
    patient_info: patientInfo,
  })
  return data
}

export async function generateBatch(soap, templateTypes, patientInfo = {}) {
  const { data } = await clinicalApi.post('/api/v1/clinical/ademed/generate/batch', {
    soap,
    template_types: templateTypes,
    patient_info: patientInfo,
  })
  return data
}

// ═══ Grafo de Conhecimento ══════════════════════════════════

export async function searchGraph(query, entityType = null) {
  const params = { q: query }
  if (entityType) params.type = entityType
  const { data } = await clinicalApi.get('/api/v1/graph/search', { params })
  return data
}

// ═══ Copiloto (WebSocket) ══════════════════════════════════

export function getCopilotWSUrl(sessionId = null) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBase = `${protocol}//${window.location.host}/clinical-api`
  let url = `${wsBase}/ws/copilot`
  
  const params = new URLSearchParams()
  if (sessionId) params.append('session_id', sessionId)
  
  const session = sessionStorage.getItem('k-clinical-session')
  if (session) {
    try {
      const { tenantSlug } = JSON.parse(session)
      if (tenantSlug) params.append('tenant_slug', tenantSlug)
    } catch(e) {}
  }
  
  const qs = params.toString()
  return qs ? `${url}?${qs}` : url
}

export async function listCopilotSessions() {
  const { data } = await clinicalApi.get('/api/v1/copilot/sessions')
  return data
}

// ═══ Pacientes ══════════════════════════════════════════════

export async function searchPatients(query) {
  const { data } = await clinicalApi.get('/api/v1/patients/search', {
    params: { q: query }
  })
  return data
}

export async function createPatient(patient) {
  const { data } = await clinicalApi.post('/api/v1/patients', patient)
  return data
}

// ═══ Arquivos do Paciente ════════════════════════════════

export async function uploadPatientFile(patientId, file, fileType = 'outro', description = '') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('file_type', fileType)
  formData.append('description', description)
  const { data } = await clinicalApi.post(`/api/v1/patients/${patientId}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export async function listPatientFiles(patientId) {
  const { data } = await clinicalApi.get(`/api/v1/patients/${patientId}/files`)
  return data
}

export async function getFileDownloadUrl(fileId) {
  const { data } = await clinicalApi.get(`/api/v1/patients/files/${fileId}/download`)
  return data
}

export async function deletePatientFile(fileId) {
  const { data } = await clinicalApi.delete(`/api/v1/patients/files/${fileId}`)
  return data
}

// ═══ Consultas (Histórico) ══════════════════════════════════

export async function saveConsultation(consultation) {
  const { data } = await clinicalApi.post('/api/v1/consultations', consultation)
  return data
}

export async function listConsultations(query = '', page = 1, limit = 20) {
  const { data } = await clinicalApi.get('/api/v1/consultations', {
    params: { q: query, page, limit }
  })
  return data
}

export async function getConsultation(id) {
  const { data } = await clinicalApi.get(`/api/v1/consultations/${id}`)
  return data
}

// ═══ Exportações ════════════════════════════════════════════

export { CLINICAL_API_URL }
export default clinicalApi

export async function searchKnowledgeGraph(message, doctorId) {
  const { data } = await clinicalApi.post('api/v1/clinical/graph/chat', {
    message,
    doctor_id: doctorId
  })
  return data
}
