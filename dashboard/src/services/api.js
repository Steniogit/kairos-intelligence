/* ============================================================
   api.js — Camada de serviços (Frontend → Paperclip Backend)
   Centraliza todas as chamadas HTTP ao Control Plane
   ============================================================ */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3000/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Tenants (Clínicas) ───────────────────────────────────────

export async function fetchTenants(activeOnly = true) {
  const { data } = await api.get('/tenants', { params: { active_only: activeOnly } })
  return data
}

export async function fetchTenant(id) {
  const { data } = await api.get(`/tenants/${id}`)
  return data
}

export async function createTenant(payload) {
  const { data } = await api.post('/tenants', payload)
  return data
}

export async function updateTenant(id, payload) {
  const { data } = await api.put(`/tenants/${id}`, payload)
  return data
}

export async function deleteTenant(id) {
  const { data } = await api.delete(`/tenants/${id}`)
  return data
}

// ── System Status (Command Center) ──────────────────────────

export async function fetchSystemStatus() {
  const { data } = await api.get('/system/status')
  return data
}

// ── Prometheus Config ────────────────────────────────────────

export async function updatePrometheusConfig(config) {
  const { data } = await api.put('/system/prometheus', config)
  return data
}

// ── Reasoning Health (Telemetria) ────────────────────────────

export async function fetchReasoningHealth() {
  const { data } = await api.get('/system/reasoning-health')
  return data
}

// ── File Upload ──────────────────────────────────────────────

export async function uploadFile(tenantId, file, type = 'frontdesk') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  const { data } = await api.post(`/tenants/${tenantId}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

// ── Health Check ─────────────────────────────────────────────

export async function healthCheck() {
  const { data } = await api.get('/health')
  return data
}

export default api
