/* ============================================================
   QuarentenaPage — Revisão e aprovação de entidades do grafo
   Lista itens na quarentena com ações de aprovar/rejeitar
   ============================================================ */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Code2,
  Loader2,
  RefreshCw,
  ArrowLeft,
  Database,
  AlertTriangle,
  Trash2,
  Check,
  X,
} from 'lucide-react'
import { fetchQuarantine, approveQuarantine, rejectQuarantine } from '../../services/clinicalApi'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import { useToast } from '../../components/Toast'
import ConfirmModal from '../../components/ConfirmModal'
import './QuarentenaPage.css'

const STATUS_CONFIG = {
  pending: { label: 'Pendente', className: 'k-badge-warning', icon: AlertTriangle },
  approved: { label: 'Aprovado', className: 'k-badge-success', icon: CheckCircle2 },
  rejected: { label: 'Rejeitado', className: 'k-badge-danger', icon: XCircle },
}

const ENTITY_ICONS = {
  Drug: '💊',
  Condition: '🩺',
  Symptom: '🤒',
  Procedure: '🔬',
  Anatomy: '🫀',
  Contraindication: '⚠️',
}

export default function QuarentenaPage() {
  const navigate = useNavigate()
  const { addToast } = useToast()
  const { session } = useClinicalAuth()

  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [expandedId, setExpandedId] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [actionLoading, setActionLoading] = useState(null)

  // Modal
  const [modal, setModal] = useState({ open: false, type: null, ids: [] })
  const [modalLoading, setModalLoading] = useState(false)

  const loadItems = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchQuarantine()
      setItems(Array.isArray(data) ? data : (data?.items || []))
    } catch (err) {
      addToast('Erro ao carregar quarentena.', 'error')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  // Filter & search
  const filtered = items.filter((item) => {
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus
    const matchesSearch =
      !search ||
      (item.source_url || '').toLowerCase().includes(search.toLowerCase()) ||
      JSON.stringify(item.extracted_data || {}).toLowerCase().includes(search.toLowerCase())
    return matchesStatus && matchesSearch
  })

  // Stats
  const pendingCount = items.filter((i) => i.status === 'pending').length
  const approvedCount = items.filter((i) => i.status === 'approved').length
  const rejectedCount = items.filter((i) => i.status === 'rejected').length

  // Selection
  function toggleSelect(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filtered.map((i) => i.id)))
    }
  }

  // Actions
  async function handleApprove(id) {
    setActionLoading(id)
    try {
      await approveQuarantine(id)
      addToast('Entidade aprovada e inserida no grafo!', 'success')
      await loadItems()
    } catch (err) {
      addToast('Erro ao aprovar. Tente novamente.', 'error')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleReject(id) {
    setActionLoading(id)
    try {
      await rejectQuarantine(id)
      addToast('Entidade rejeitada.', 'warning')
      await loadItems()
    } catch (err) {
      addToast('Erro ao rejeitar. Tente novamente.', 'error')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleBulkAction(type) {
    setModalLoading(true)
    const ids = [...modal.ids]
    let successCount = 0
    let errorCount = 0

    for (const id of ids) {
      try {
        if (type === 'approve') await approveQuarantine(id)
        else await rejectQuarantine(id)
        successCount++
      } catch {
        errorCount++
      }
    }

    if (successCount > 0) {
      addToast(
        `${successCount} ite${successCount > 1 ? 'ns' : 'm'} ${type === 'approve' ? 'aprovado' : 'rejeitado'}${successCount > 1 ? 's' : ''}.`,
        type === 'approve' ? 'success' : 'warning'
      )
    }
    if (errorCount > 0) {
      addToast(`${errorCount} ite${errorCount > 1 ? 'ns' : 'm'} com erro.`, 'error')
    }

    setModal({ open: false, type: null, ids: [] })
    setModalLoading(false)
    setSelectedIds(new Set())
    await loadItems()
  }

  function openBulkModal(type) {
    const ids = [...selectedIds].filter((id) => {
      const item = items.find((i) => i.id === id)
      return item && item.status === 'pending'
    })
    if (ids.length === 0) {
      addToast('Selecione itens pendentes para executar a ação.', 'info')
      return
    }
    setModal({ open: true, type, ids })
  }

  // Parse extracted data safely
  function getEntities(item) {
    try {
      const data = typeof item.extracted_data === 'string'
        ? JSON.parse(item.extracted_data)
        : item.extracted_data
      return data?.entities || []
    } catch {
      return []
    }
  }

  function getCypherQueries(item) {
    try {
      const data = typeof item.extracted_data === 'string'
        ? JSON.parse(item.extracted_data)
        : item.extracted_data
      return data?.cypher_queries || []
    } catch {
      return []
    }
  }

  return (
    <div className="quarentena-page">
      {/* Header */}
      <div className="quarentena-header">
        <div className="quarentena-header-left">
          <button className="k-btn k-btn-ghost k-btn-icon" onClick={() => navigate('/clinico')} title="Voltar">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h2 className="quarentena-title">Quarentena do Grafo</h2>
            <p className="k-text-sm k-text-muted">{items.length} itens na quarentena</p>
          </div>
        </div>
        <div className="quarentena-header-right">
          
          <button className="k-btn k-btn-secondary" onClick={loadItems} disabled={loading} id="btn-refresh-quarentena">
            <RefreshCw size={16} className={loading ? 'k-animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="quarentena-stats">
        <div className="k-stat-card" onClick={() => setFilterStatus('pending')} style={{ cursor: 'pointer' }}>
          <div className="k-stat-icon" style={{ background: 'var(--k-warning-bg)', color: 'var(--k-warning)' }}>
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="k-stat-value">{pendingCount}</div>
            <div className="k-stat-label">Pendentes</div>
          </div>
        </div>
        <div className="k-stat-card" onClick={() => setFilterStatus('approved')} style={{ cursor: 'pointer' }}>
          <div className="k-stat-icon" style={{ background: 'var(--k-success-bg)', color: 'var(--k-success)' }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="k-stat-value">{approvedCount}</div>
            <div className="k-stat-label">Aprovados</div>
          </div>
        </div>
        <div className="k-stat-card" onClick={() => setFilterStatus('rejected')} style={{ cursor: 'pointer' }}>
          <div className="k-stat-icon" style={{ background: 'var(--k-danger-bg)', color: 'var(--k-danger)' }}>
            <XCircle size={22} />
          </div>
          <div>
            <div className="k-stat-value">{rejectedCount}</div>
            <div className="k-stat-label">Rejeitados</div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="quarentena-toolbar">
        <div className="quarentena-search">
          <Search size={18} className="quarentena-search-icon" />
          <input
            className="k-input"
            placeholder="Buscar por URL ou entidade..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            id="input-search-quarentena"
          />
        </div>

        <div className="quarentena-filters">
          <select
            className="k-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            id="select-filter-status"
          >
            <option value="all">Todos os status</option>
            <option value="pending">Pendentes</option>
            <option value="approved">Aprovados</option>
            <option value="rejected">Rejeitados</option>
          </select>
        </div>

        {selectedIds.size > 0 && (
          <div className="quarentena-bulk-actions">
            <span className="k-text-sm k-text-muted">{selectedIds.size} selecionado(s)</span>
            <button className="k-btn k-btn-primary" onClick={() => openBulkModal('approve')} id="btn-bulk-approve">
              <Check size={16} /> Aprovar
            </button>
            <button className="k-btn k-btn-danger" onClick={() => openBulkModal('reject')} id="btn-bulk-reject">
              <X size={16} /> Rejeitar
            </button>
          </div>
        )}
      </div>

      {/* Items List */}
      {loading ? (
        <div className="quarentena-loading">
          {[1, 2, 3].map((i) => (
            <div key={i} className="quarentena-item-skeleton">
              <div className="k-skeleton" style={{ height: 20, width: '40%', marginBottom: 8 }} />
              <div className="k-skeleton" style={{ height: 14, width: '70%' }} />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="k-empty">
          <Database size={56} className="k-empty-icon" />
          <h3>{search || filterStatus !== 'all' ? 'Nenhum item encontrado' : 'Quarentena vazia'}</h3>
          <p className="k-text-sm k-text-muted" style={{ marginTop: 4 }}>
            {search || filterStatus !== 'all'
              ? 'Tente alterar os filtros.'
              : 'Nenhuma entidade aguardando revisão.'}
          </p>
        </div>
      ) : (
        <div className="quarentena-list">
          {/* Select all header */}
          <div className="quarentena-list-header">
            <label className="quarentena-checkbox-label">
              <input type="checkbox" checked={selectedIds.size === filtered.length && filtered.length > 0} onChange={toggleSelectAll} />
              <span className="k-text-sm k-text-muted">Selecionar todos</span>
            </label>
          </div>

          {filtered.map((item) => {
            const isExpanded = expandedId === item.id
            const entities = getEntities(item)
            const cypherQueries = getCypherQueries(item)
            const statusConf = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
            const StatusIconComp = statusConf.icon

            return (
              <div
                key={item.id}
                className={`quarentena-item ${isExpanded ? 'quarentena-item--expanded' : ''}`}
              >
                {/* Main row */}
                <div className="quarentena-item-row">
                  <label className="quarentena-checkbox" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(item.id)}
                      onChange={() => toggleSelect(item.id)}
                    />
                  </label>

                  <div className="quarentena-item-content" onClick={() => setExpandedId(isExpanded ? null : item.id)}>
                    <div className="quarentena-item-main">
                      <div className="quarentena-item-title">
                        <span className="quarentena-item-id">#{item.id}</span>
                        <span className={`k-badge ${statusConf.className}`}>
                          <StatusIconComp size={12} />
                          {statusConf.label}
                        </span>
                      </div>
                      <div className="quarentena-item-url">
                        {item.source_url ? (
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink size={12} />
                            {item.source_url.length > 60
                              ? item.source_url.substring(0, 60) + '...'
                              : item.source_url}
                          </a>
                        ) : (
                          <span className="k-text-muted">Sem URL</span>
                        )}
                      </div>
                      <div className="quarentena-item-meta">
                        <span>
                          {entities.length} entidade{entities.length !== 1 ? 's' : ''}
                        </span>
                        <span>•</span>
                        <span>
                          {cypherQueries.length} quer{cypherQueries.length !== 1 ? 'ies' : 'y'} Cypher
                        </span>
                        {item.created_at && (
                          <>
                            <span>•</span>
                            <span>{new Date(item.created_at).toLocaleDateString('pt-BR')}</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="quarentena-item-expand">
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </div>

                  {/* Quick actions */}
                  {item.status === 'pending' && (
                    <div className="quarentena-item-actions">
                      <button
                        className="k-btn k-btn-ghost quarentena-btn-approve"
                        onClick={() => handleApprove(item.id)}
                        disabled={actionLoading === item.id}
                        title="Aprovar"
                        id={`btn-approve-${item.id}`}
                      >
                        {actionLoading === item.id ? (
                          <Loader2 size={16} className="k-animate-spin" />
                        ) : (
                          <CheckCircle2 size={16} />
                        )}
                      </button>
                      <button
                        className="k-btn k-btn-ghost quarentena-btn-reject"
                        onClick={() => handleReject(item.id)}
                        disabled={actionLoading === item.id}
                        title="Rejeitar"
                        id={`btn-reject-${item.id}`}
                      >
                        <XCircle size={16} />
                      </button>
                    </div>
                  )}
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="quarentena-expanded">
                    {/* Entities */}
                    {entities.length > 0 && (
                      <div className="quarentena-section">
                        <h4 className="quarentena-section-title">
                          <Database size={14} /> Entidades Extraídas
                        </h4>
                        <div className="quarentena-entities">
                          {entities.map((ent, idx) => (
                            <div key={idx} className="quarentena-entity">
                              <span className="quarentena-entity-icon">
                                {ENTITY_ICONS[ent.type] || '📎'}
                              </span>
                              <span className="quarentena-entity-name">{ent.name}</span>
                              <span className="quarentena-entity-type">{ent.type}</span>
                              {ent.properties?.cid10 && (
                                <span className="quarentena-entity-cid">
                                  {ent.properties.cid10}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Cypher Queries */}
                    {cypherQueries.length > 0 && (
                      <div className="quarentena-section">
                        <h4 className="quarentena-section-title">
                          <Code2 size={14} /> Queries Cypher (Preview)
                        </h4>
                        <div className="quarentena-cypher">
                          {cypherQueries.map((q, idx) => (
                            <pre key={idx} className="quarentena-cypher-query">{q}</pre>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Raw JSON */}
                    <details className="quarentena-raw">
                      <summary className="k-text-sm k-text-muted">Ver JSON bruto</summary>
                      <pre className="quarentena-raw-json">
                        {JSON.stringify(
                          typeof item.extracted_data === 'string'
                            ? JSON.parse(item.extracted_data)
                            : item.extracted_data,
                          null,
                          2
                        )}
                      </pre>
                    </details>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={modal.open}
        title={modal.type === 'approve' ? 'Aprovar itens selecionados?' : 'Rejeitar itens selecionados?'}
        message={
          modal.type === 'approve'
            ? `${modal.ids.length} ite${modal.ids.length > 1 ? 'ns' : 'm'} ser${modal.ids.length > 1 ? 'ão inseridos' : 'á inserido'} permanentemente no grafo Neo4j.`
            : `${modal.ids.length} ite${modal.ids.length > 1 ? 'ns' : 'm'} ser${modal.ids.length > 1 ? 'ão descartados' : 'á descartado'} da quarentena.`
        }
        confirmLabel={modal.type === 'approve' ? 'Aprovar Todos' : 'Rejeitar Todos'}
        variant={modal.type === 'approve' ? 'warning' : 'danger'}
        loading={modalLoading}
        onConfirm={() => handleBulkAction(modal.type)}
        onCancel={() => setModal({ open: false, type: null, ids: [] })}
      />
    </div>
  )
}
