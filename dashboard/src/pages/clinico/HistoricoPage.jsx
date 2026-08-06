/* ============================================================
   HistoricoPage — Histórico de Atendimentos
   Busca por nome/CPF, lista paginada, detalhes de consulta
   ============================================================ */

import { useState, useEffect, useCallback } from 'react'
import {
  Search,
  Clock,
  User,
  FileText,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Stethoscope,
  ArrowLeft,
  Loader2,
  X,
} from 'lucide-react'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import { listConsultations, getConsultation } from '../../services/clinicalApi'
import './HistoricoPage.css'

// ═══ Helpers ═══════════════════════════════════════════════

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}min ${s.toString().padStart(2, '0')}s`
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return dateStr }
}

const SOAP_LABELS = { S: 'Resumo', O: 'Diagnóstico', A: 'Avaliação', P: 'Conduta' }
const SOAP_COLORS = { S: '#10b981', O: '#3b82f6', A: '#f59e0b', P: '#8b5cf6' }

// ═══ Component ════════════════════════════════════════════

export default function HistoricoPage() {
  const { session } = useClinicalAuth()

  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const limit = 15

  // ─── Fetch List ──────────────────────────────────────────

  const fetchList = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listConsultations(query, page, limit)
      setData(result)
    } catch {
      setData({ items: [], total: 0 })
    } finally {
      setLoading(false)
    }
  }, [query, page])

  useEffect(() => { fetchList() }, [fetchList])

  // ─── Fetch Detail ────────────────────────────────────────

  const openDetail = useCallback(async (id) => {
    setDetailLoading(true)
    try {
      const result = await getConsultation(id)
      setDetail(result)
    } catch {
      setDetail(null)
    } finally {
      setDetailLoading(false)
    }
  }, [])

  // ─── Search Handler ──────────────────────────────────────

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchList()
  }

  const totalPages = Math.max(1, Math.ceil(data.total / limit))

  // ─── Detail View ─────────────────────────────────────────

  if (detail) {
    const soap = detail.soap_json || {}
    const soapFormatted = {
      S: typeof soap.subjective === 'string' ? soap.subjective : JSON.stringify(soap.subjective || soap.S || '', null, 2),
      O: typeof soap.objective === 'string' ? soap.objective : JSON.stringify(soap.objective || soap.O || '', null, 2),
      A: typeof soap.assessment === 'string' ? soap.assessment : JSON.stringify(soap.assessment || soap.A || '', null, 2),
      P: typeof soap.plan === 'string' ? soap.plan : JSON.stringify(soap.plan || soap.P || '', null, 2),
    }

    return (
      <div className="historico-page">
        <div className="historico-header">
          <button className="k-btn k-btn-ghost" onClick={() => setDetail(null)}>
            <ArrowLeft size={16} /> Voltar
          </button>
          <h2 className="historico-title">Detalhes da Consulta</h2>
        </div>

        <div className="historico-detail">
          {/* Patient Info */}
          <div className="historico-detail-patient">
            <User size={18} />
            <div>
              <div className="historico-detail-name">{detail.patient_name}</div>
              <div className="historico-detail-meta">
                {detail.patient_cpf && <span>CPF: {detail.patient_cpf}</span>}
                {detail.patient_sex && detail.patient_sex !== 'N' && (
                  <span>Sexo: {detail.patient_sex === 'M' ? 'Masculino' : 'Feminino'}</span>
                )}
                {detail.patient_birth_date && <span>Nasc.: {detail.patient_birth_date}</span>}
              </div>
            </div>
          </div>

          {/* Consultation Meta */}
          <div className="historico-detail-info">
            <div><Calendar size={14} /> {formatDate(detail.created_at)}</div>
            <div><Stethoscope size={14} /> {detail.doctor_name || 'Profissional'}</div>
            <div><Clock size={14} /> {formatDuration(detail.duration_seconds)}</div>
          </div>

          {/* SOAP */}
          <div className="historico-soap-grid">
            {['S', 'O', 'A', 'P'].map(key => (
              <div key={key} className="historico-soap-card">
                <div className="historico-soap-label" style={{ color: SOAP_COLORS[key] }}>
                  {SOAP_LABELS[key]}
                </div>
                <div className="historico-soap-content">
                  {soapFormatted[key] || '—'}
                </div>
              </div>
            ))}
          </div>

          {/* Transcript */}
          {detail.transcript && (
            <div className="historico-transcript">
              <h4><FileText size={16} /> Transcrição</h4>
              <div className="historico-transcript-body">
                {detail.transcript}
              </div>
            </div>
          )}

          {/* Documents */}
          {detail.documents_json && detail.documents_json.length > 0 && (
            <div className="historico-documents">
              <h4><FileText size={16} /> Documentos Gerados</h4>
              {detail.documents_json.map((doc, i) => (
                <div key={i} className="historico-doc-card">
                  <div className="historico-doc-title">{doc.type || `Documento ${i + 1}`}</div>
                  <div className="historico-doc-content">{doc.content || doc.text || '—'}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // ─── List View ───────────────────────────────────────────

  return (
    <div className="historico-page">
      <div className="historico-header">
        <h2 className="historico-title">Histórico de Atendimentos</h2>
        <p className="historico-subtitle">
          Consulte os atendimentos anteriores por nome ou CPF do paciente
        </p>
      </div>

      {/* Search Bar */}
      <form className="historico-search" onSubmit={handleSearch}>
        <div className="historico-search-wrap">
          <Search size={16} className="historico-search-icon" />
          <input
            type="text"
            className="historico-search-input"
            placeholder="Buscar por nome ou CPF..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button type="button" className="historico-search-clear" onClick={() => { setQuery(''); setPage(1) }}>
              <X size={14} />
            </button>
          )}
        </div>
        <button type="submit" className="k-btn k-btn-primary">
          <Search size={16} /> Buscar
        </button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="historico-loading">
          <Loader2 size={28} className="k-animate-spin" />
          <span>Carregando...</span>
        </div>
      ) : data.items.length === 0 ? (
        <div className="historico-empty">
          <Clock size={40} style={{ opacity: 0.3 }} />
          <p>Nenhum atendimento encontrado.</p>
        </div>
      ) : (
        <>
          <div className="historico-list">
            {data.items.map(item => (
              <div
                key={item.id}
                className="historico-item"
                onClick={() => openDetail(item.id)}
                role="button"
                tabIndex={0}
              >
                <div className="historico-item-left">
                  <div className="historico-item-name">
                    <User size={14} /> {item.patient_name}
                  </div>
                  <div className="historico-item-meta">
                    {item.patient_cpf && <span>{item.patient_cpf}</span>}
                    <span><Clock size={12} /> {formatDuration(item.duration_seconds)}</span>
                  </div>
                </div>
                <div className="historico-item-right">
                  <div className="historico-item-date">
                    <Calendar size={12} /> {formatDate(item.created_at)}
                  </div>
                  <div className="historico-item-doctor">
                    {item.doctor_name || 'Profissional'}
                  </div>
                </div>
                <ChevronRight size={16} className="historico-item-arrow" />
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="historico-pagination">
              <button
                className="k-btn k-btn-ghost k-btn-sm"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft size={14} /> Anterior
              </button>
              <span className="historico-page-info">
                Página {page} de {totalPages} ({data.total} registros)
              </span>
              <button
                className="k-btn k-btn-ghost k-btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Próxima <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}

      {/* Detail loading overlay */}
      {detailLoading && (
        <div className="historico-detail-loading">
          <Loader2 size={32} className="k-animate-spin" />
        </div>
      )}
    </div>
  )
}
