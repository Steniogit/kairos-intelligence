/* ============================================================
   QuarentenaPage — Central de Curadoria e Biblioteca de Conhecimentos
   - Visão Admin: Quarentena do Grafo (Curadoria Central)
   - Visão Médico: Minhas Sugestões para Biblioteca de Conhecimentos
   - Suporte a Anexo de Arquivos (PDF, DOCX, DOC, TXT, RTF, MD, CSV, XLSX)
   ============================================================ */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Search,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Code2,
  Loader2,
  RefreshCw,
  ArrowLeft,
  Database,
  AlertTriangle,
  Check,
  X,
  Plus,
  BookOpen,
  Send,
  MessageSquare,
  Sparkles,
  Info,
  Clock,
  FileText,
  Upload,
  Paperclip,
  Trash2,
  Eye,
  FileDown
} from 'lucide-react'
import {
  fetchQuarantine,
  approveQuarantine,
  rejectQuarantine,
  suggestKnowledge,
  getQuarantineFileUrl
} from '../../services/clinicalApi'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import { useToast } from '../../components/Toast'
import ConfirmModal from '../../components/ConfirmModal'
import './QuarentenaPage.css'

const STATUS_CONFIG = {
  pending: { label: 'Em Análise', className: 'k-badge-warning', icon: Clock },
  approved: { label: 'Aprovado', className: 'k-badge-success', icon: CheckCircle2 },
  rejected: { label: 'Não Aprovado', className: 'k-badge-danger', icon: XCircle },
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
  const isAdmin = Boolean(session?.isAdmin)

  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [expandedId, setExpandedId] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [actionLoading, setActionLoading] = useState(null)
  const [fileLoadingId, setFileLoadingId] = useState(null)

  // Modais
  const [confirmModal, setConfirmModal] = useState({ open: false, type: null, ids: [] })
  const [confirmLoading, setConfirmLoading] = useState(false)
  
  // Modal de Rejeição com Motivo (Admin)
  const [rejectModal, setRejectModal] = useState({ open: false, id: null })
  const [rejectReason, setRejectReason] = useState('')
  const [rejecting, setRejecting] = useState(false)

  // Modal de Nova Sugestão (Médico / Usuário)
  const [suggestModalOpen, setSuggestModalOpen] = useState(false)
  const [suggestForm, setSuggestForm] = useState({
    title: '',
    source_url: '',
    source_type: 'protocolo',
    content_text: '',
    notes: ''
  })
  const [selectedFile, setSelectedFile] = useState(null)
  const [suggesting, setSuggesting] = useState(false)

  const loadItems = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchQuarantine('all')
      setItems(Array.isArray(data) ? data : (data?.items || []))
    } catch (err) {
      addToast('Erro ao carregar itens de conhecimento.', 'error')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  // Formatação de data brasileira
  const formatDateBR = (dateStr) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch {
      return dateStr
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Filtragem
  const filtered = items.filter((item) => {
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus
    const term = search.toLowerCase()
    const matchesSearch =
      !search ||
      (item.source_url || '').toLowerCase().includes(term) ||
      (item.file_name || '').toLowerCase().includes(term) ||
      (item.raw_text || '').toLowerCase().includes(term) ||
      (item.submitted_by || '').toLowerCase().includes(term) ||
      JSON.stringify(item.extracted_data || {}).toLowerCase().includes(term)
    return matchesStatus && matchesSearch
  })

  // Contadores
  const pendingCount = items.filter((i) => i.status === 'pending').length
  const approvedCount = items.filter((i) => i.status === 'approved').length
  const rejectedCount = items.filter((i) => i.status === 'rejected').length

  // Seleção múltipla (Admin)
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

  // Abrir / Baixar arquivo anexo
  async function handleViewFile(itemId) {
    setFileLoadingId(itemId)
    try {
      const data = await getQuarantineFileUrl(itemId)
      if (data?.url) {
        window.open(data.url, '_blank')
      } else {
        addToast('Arquivo não disponível para visualização.', 'warning')
      }
    } catch (err) {
      addToast('Erro ao abrir arquivo anexo.', 'error')
    } finally {
      setFileLoadingId(null)
    }
  }

  // Ações de Curadoria (Admin)
  async function handleApprove(id) {
    setActionLoading(id)
    try {
      await approveQuarantine(id, session?.name || 'Administrador')
      addToast('Conhecimento aprovado e integrado ao Grafo Global!', 'success')
      await loadItems()
    } catch (err) {
      addToast('Erro ao aprovar. Tente novamente.', 'error')
    } finally {
      setActionLoading(null)
    }
  }

  function openRejectModal(id) {
    setRejectReason('')
    setRejectModal({ open: true, id })
  }

  async function handleConfirmReject() {
    if (!rejectModal.id) return
    setRejecting(true)
    try {
      await rejectQuarantine(
        rejectModal.id,
        rejectReason.trim() || 'Não atende aos critérios científicos da curadoria.',
        session?.name || 'Administrador'
      )
      addToast('Sugestão rejeitada com motivo registrado.', 'warning')
      setRejectModal({ open: false, id: null })
      await loadItems()
    } catch (err) {
      addToast('Erro ao rejeitar sugestão.', 'error')
    } finally {
      setRejecting(false)
    }
  }

  async function handleBulkAction(type) {
    setConfirmLoading(true)
    const ids = [...confirmModal.ids]
    let successCount = 0
    let errorCount = 0

    for (const id of ids) {
      try {
        if (type === 'approve') await approveQuarantine(id, session?.name || 'Administrador')
        else await rejectQuarantine(id, 'Rejeitado em lote pelo Administrador.', session?.name || 'Administrador')
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

    setConfirmModal({ open: false, type: null, ids: [] })
    setConfirmLoading(false)
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
    setConfirmModal({ open: true, type, ids })
  }

  // Manipulação de Arquivo no Formulário
  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      // Preencher título se vazio
      if (!suggestForm.title.trim()) {
        const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')
        setSuggestForm((prev) => ({ ...prev, title: cleanName }))
      }
    }
  }

  // Envio de Nova Sugestão (Médico)
  async function handleCreateSuggestion(e) {
    e.preventDefault()
    if (!suggestForm.title.trim() && !selectedFile) {
      addToast('Por favor, informe o título ou anexe um arquivo.', 'warning')
      return
    }
    setSuggesting(true)
    try {
      const formData = new FormData()
      formData.append('title', suggestForm.title.trim())
      formData.append('source_type', suggestForm.source_type)
      formData.append('source_url', suggestForm.source_url.trim())
      formData.append('content_text', suggestForm.content_text.trim())
      formData.append('notes', suggestForm.notes.trim())

      if (selectedFile) {
        formData.append('file', selectedFile)
      }

      await suggestKnowledge(formData)
      addToast('Sugestão e arquivo enviados com sucesso para a curadoria!', 'success')
      setSuggestModalOpen(false)
      setSuggestForm({ title: '', source_url: '', source_type: 'protocolo', content_text: '', notes: '' })
      setSelectedFile(null)
      await loadItems()
    } catch (err) {
      addToast('Erro ao enviar sugestão: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSuggesting(false)
    }
  }

  function getEntities(item) {
    return item?.extracted_data?.entities || []
  }

  function getCypherQueries(item) {
    return item?.extracted_data?.cypher_queries || []
  }

  return (
    <div className="quarentena-page">
      {/* Header Principal */}
      <div className="quarentena-header">
        <div className="quarentena-header-left">
          <button className="k-btn k-btn-ghost k-btn-icon" onClick={() => navigate('/clinico')} title="Voltar">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h2 className="quarentena-title">
              {isAdmin ? 'Quarentena do Grafo' : 'Minhas Sugestões para Biblioteca de Conhecimentos'}
            </h2>
            <p className="k-text-sm k-text-muted">
              {isAdmin
                ? 'Curadoria Central — Revisão e aprovação de entidades médicas para o Grafo Global'
                : 'Envie protocolos, bulas e artigos médicos (PDF, DOCX, links) para análise da curadoria'}
            </p>
          </div>
        </div>

        <div className="quarentena-header-right">
          {!isAdmin && (
            <button
              className="k-btn k-btn-primary"
              onClick={() => setSuggestModalOpen(true)}
              id="btn-new-suggestion"
            >
              <Plus size={16} /> Sugerir Novo Conhecimento
            </button>
          )}

          <button className="k-btn k-btn-secondary" onClick={loadItems} disabled={loading} id="btn-refresh-quarentena">
            <RefreshCw size={16} className={loading ? 'k-animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="quarentena-stats">
        <div
          className={`k-stat-card ${filterStatus === 'pending' ? 'quarentena-stat--active' : ''}`}
          onClick={() => setFilterStatus(filterStatus === 'pending' ? 'all' : 'pending')}
          style={{ cursor: 'pointer' }}
        >
          <div className="k-stat-icon" style={{ background: 'var(--k-warning-bg)', color: 'var(--k-warning)' }}>
            <Clock size={22} />
          </div>
          <div>
            <div className="k-stat-value">{pendingCount}</div>
            <div className="k-stat-label">Em Análise</div>
          </div>
        </div>

        <div
          className={`k-stat-card ${filterStatus === 'approved' ? 'quarentena-stat--active' : ''}`}
          onClick={() => setFilterStatus(filterStatus === 'approved' ? 'all' : 'approved')}
          style={{ cursor: 'pointer' }}
        >
          <div className="k-stat-icon" style={{ background: 'var(--k-success-bg)', color: 'var(--k-success)' }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="k-stat-value">{approvedCount}</div>
            <div className="k-stat-label">Aprovados</div>
          </div>
        </div>

        <div
          className={`k-stat-card ${filterStatus === 'rejected' ? 'quarentena-stat--active' : ''}`}
          onClick={() => setFilterStatus(filterStatus === 'rejected' ? 'all' : 'rejected')}
          style={{ cursor: 'pointer' }}
        >
          <div className="k-stat-icon" style={{ background: 'var(--k-danger-bg)', color: 'var(--k-danger)' }}>
            <XCircle size={22} />
          </div>
          <div>
            <div className="k-stat-value">{rejectedCount}</div>
            <div className="k-stat-label">Não Aprovados</div>
          </div>
        </div>
      </div>

      {/* Barra de Filtros e Busca */}
      <div className="quarentena-toolbar">
        <div className="quarentena-search">
          <Search size={18} className="quarentena-search-icon" />
          <input
            className="k-input"
            placeholder={isAdmin ? "Buscar por título, arquivo, médico ou entidade..." : "Buscar nas minhas sugestões..."}
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
            <option value="all">Todos os status ({items.length})</option>
            <option value="pending">Em Análise ({pendingCount})</option>
            <option value="approved">Aprovados ({approvedCount})</option>
            <option value="rejected">Não Aprovados ({rejectedCount})</option>
          </select>
        </div>

        {isAdmin && selectedIds.size > 0 && (
          <div className="quarentena-bulk-actions">
            <span className="k-text-sm k-text-muted">{selectedIds.size} selecionado(s)</span>
            <button className="k-btn k-btn-primary" onClick={() => openBulkModal('approve')} id="btn-bulk-approve">
              <Check size={16} /> Aprovar Selecionados
            </button>
            <button className="k-btn k-btn-danger" onClick={() => openBulkModal('reject')} id="btn-bulk-reject">
              <X size={16} /> Rejeitar Selecionados
            </button>
          </div>
        )}
      </div>

      {/* Lista de Itens */}
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
        <div className="k-empty quarentena-empty-card">
          <BookOpen size={56} className="k-empty-icon" style={{ opacity: 0.6 }} />
          <h3>{search || filterStatus !== 'all' ? 'Nenhuma sugestão encontrada' : 'Nenhum item na lista'}</h3>
          <p className="k-text-sm k-text-muted" style={{ marginTop: 4 }}>
            {!isAdmin
              ? 'Você ainda não enviou sugestões de artigos ou diretrizes.'
              : 'Nenhuma entidade médica aguardando curadoria.'}
          </p>
          {!isAdmin && (
            <button
              className="k-btn k-btn-primary"
              onClick={() => setSuggestModalOpen(true)}
              style={{ marginTop: 16 }}
            >
              <Plus size={16} /> Fazer Primeira Sugestão
            </button>
          )}
        </div>
      ) : (
        <div className="quarentena-list">
          {isAdmin && (
            <div className="quarentena-list-header">
              <label className="quarentena-checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedIds.size === filtered.length && filtered.length > 0}
                  onChange={toggleSelectAll}
                />
                <span className="k-text-sm k-text-muted">Selecionar todos</span>
              </label>
            </div>
          )}

          {filtered.map((item) => {
            const isExpanded = expandedId === item.id
            const entities = getEntities(item)
            const cypherQueries = getCypherQueries(item)
            const statusConf = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
            const StatusIconComp = statusConf.icon
            const hasAttachedFile = Boolean(item.storage_key || item.file_name)

            return (
              <div
                key={item.id}
                className={`quarentena-item ${isExpanded ? 'quarentena-item--expanded' : ''} quarentena-item--${item.status}`}
              >
                {/* Linha Principal */}
                <div className="quarentena-item-row">
                  {isAdmin && (
                    <label className="quarentena-checkbox" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(item.id)}
                        onChange={() => toggleSelect(item.id)}
                      />
                    </label>
                  )}

                  <div className="quarentena-item-content" onClick={() => setExpandedId(isExpanded ? null : item.id)}>
                    <div className="quarentena-item-main">
                      <div className="quarentena-item-title">
                        <span className="quarentena-item-id">#{item.id}</span>
                        <span className={`k-badge ${statusConf.className}`}>
                          <StatusIconComp size={12} />
                          {statusConf.label}
                        </span>
                        <span className="quarentena-source-type-tag">
                          {item.source_type?.toUpperCase() || 'DOCUMENTO'}
                        </span>
                      </div>

                      <div className="quarentena-item-url">
                        {item.source_url ? (
                          item.source_url.startsWith('http') ? (
                            <a
                              href={item.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink size={12} />
                              {item.source_url}
                            </a>
                          ) : (
                            <span className="quarentena-title-text">
                              <FileText size={15} style={{ display: 'inline', marginRight: 6, color: 'var(--k-accent)' }} />
                              {item.source_url}
                            </span>
                          )
                        ) : (
                          <span className="k-text-muted">Sugestão sem título</span>
                        )}
                      </div>

                      <div className="quarentena-item-meta">
                        {item.submitted_by && (
                          <span>👤 <strong>Sugerido por:</strong> {item.submitted_by}</span>
                        )}
                        {item.created_at && (
                          <>
                            <span>•</span>
                            <span>Enviado em {formatDateBR(item.created_at)}</span>
                          </>
                        )}
                        {hasAttachedFile && (
                          <>
                            <span>•</span>
                            <span className="quarentena-file-tag">
                              <Paperclip size={11} /> {item.file_name} {item.file_size ? `(${formatFileSize(item.file_size)})` : ''}
                            </span>
                          </>
                        )}
                      </div>

                      {/* Botão de Acesso Rápido ao Arquivo Anexo */}
                      {hasAttachedFile && (
                        <div style={{ marginTop: 6 }} onClick={(e) => e.stopPropagation()}>
                          <button
                            className="k-btn k-btn-secondary k-btn-sm quarentena-view-file-btn"
                            onClick={() => handleViewFile(item.id)}
                            disabled={fileLoadingId === item.id}
                            title="Abrir arquivo anexo em nova aba"
                          >
                            {fileLoadingId === item.id ? (
                              <Loader2 size={13} className="k-animate-spin" />
                            ) : (
                              <Eye size={13} />
                            )}
                            Ver Arquivo Anexo ({item.file_name || 'Documento'})
                          </button>
                        </div>
                      )}

                      {/* Feedback Educativo para o Médico / Usuário */}
                      {!isAdmin && (
                        <div className="quarentena-user-feedback">
                          {item.status === 'pending' && (
                            <div className="quarentena-feedback-box quarentena-feedback--pending">
                              <Clock size={16} />
                              <span>Sua sugestão está na fila de curadoria. Assim que o Administrador aprovar, este conhecimento entrará para toda a plataforma.</span>
                            </div>
                          )}
                          {item.status === 'approved' && (
                            <div className="quarentena-feedback-box quarentena-feedback--approved">
                              <CheckCircle2 size={16} />
                              <span>🎉 <strong>Aprovado pelo Administrador!</strong> Este protocolo já foi adicionado ao Grafo Médico Global e está ativo para todos os médicos.</span>
                            </div>
                          )}
                          {item.status === 'rejected' && (
                            <div className="quarentena-feedback-box quarentena-feedback--rejected">
                              <XCircle size={16} />
                              <div>
                                <div><strong>Não Aprovado pelo Administrador.</strong></div>
                                {item.reviewer_notes && (
                                  <div className="quarentena-feedback-notes">
                                    💬 <em>Motivo da Curadoria:</em> "{item.reviewer_notes}"
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Indicador de Status para o Administrador */}
                      {isAdmin && item.status === 'rejected' && item.reviewer_notes && (
                        <div className="quarentena-admin-rejection-note">
                          <span>Motivo registrado: "{item.reviewer_notes}"</span>
                          {item.reviewed_by && <small> por {item.reviewed_by}</small>}
                        </div>
                      )}
                    </div>

                    <div className="quarentena-item-expand">
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </div>

                  {/* Ações de Aprovação do Admin */}
                  {isAdmin && item.status === 'pending' && (
                    <div className="quarentena-item-actions">
                      <button
                        className="k-btn k-btn-primary quarentena-btn-action-approve"
                        onClick={() => handleApprove(item.id)}
                        disabled={actionLoading === item.id}
                        title="Aprovar e Integrar ao Grafo Global"
                        id={`btn-approve-${item.id}`}
                      >
                        {actionLoading === item.id ? (
                          <Loader2 size={16} className="k-animate-spin" />
                        ) : (
                          <><Check size={14} /> Aprovar</>
                        )}
                      </button>
                      <button
                        className="k-btn k-btn-danger quarentena-btn-action-reject"
                        onClick={() => openRejectModal(item.id)}
                        disabled={actionLoading === item.id}
                        title="Rejeitar com Motivo"
                        id={`btn-reject-${item.id}`}
                      >
                        <X size={14} /> Rejeitar
                      </button>
                    </div>
                  )}
                </div>

                {/* Detalhes Expandidos */}
                {isExpanded && (
                  <div className="quarentena-expanded">
                    {item.raw_text && (
                      <div className="quarentena-section">
                        <h4 className="quarentena-section-title">
                          <FileText size={14} /> Conteúdo Extraído / Resumo
                        </h4>
                        <div className="quarentena-raw-text-box">
                          {item.raw_text}
                        </div>
                      </div>
                    )}

                    {/* Entidades Extraídas (se houver) */}
                    {entities.length > 0 && (
                      <div className="quarentena-section">
                        <h4 className="quarentena-section-title">
                          <Database size={14} /> Entidades Médicas Mapeadas ({entities.length})
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
                                  CID: {ent.properties.cid10}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Queries Cypher (somente Admin) */}
                    {isAdmin && cypherQueries.length > 0 && (
                      <div className="quarentena-section">
                        <h4 className="quarentena-section-title">
                          <Code2 size={14} /> Queries Cypher para Inserção no Neo4j
                        </h4>
                        <div className="quarentena-cypher">
                          {cypherQueries.map((q, idx) => (
                            <pre key={idx} className="quarentena-cypher-query">{q}</pre>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Modal de Nova Sugestão com Upload Multi-Formato */}
      {suggestModalOpen && (
        <div className="quarentena-modal-backdrop">
          <div className="quarentena-modal-card">
            <div className="quarentena-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="quarentena-modal-icon">
                  <Sparkles size={20} />
                </div>
                <div>
                  <h3 className="quarentena-modal-title">Sugerir Novo Conhecimento</h3>
                  <p className="k-text-xs k-text-muted">Envie arquivos (PDF, DOCX), links ou textos para análise da curadoria médica</p>
                </div>
              </div>
              <button
                className="k-btn k-btn-ghost k-btn-icon"
                onClick={() => { setSuggestModalOpen(false); setSelectedFile(null); }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateSuggestion} className="quarentena-modal-form">
              {/* Área de Upload de Arquivo */}
              <div className="quarentena-upload-area">
                <label className="quarentena-form-label">
                  Anexar Arquivo Médico (PDF, DOCX, DOC, TXT, RTF, MD, CSV, XLSX)
                </label>
                
                {selectedFile ? (
                  <div className="quarentena-selected-file">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                      <FileText size={20} style={{ color: 'var(--k-accent)', flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div className="quarentena-selected-file-name">{selectedFile.name}</div>
                        <div className="quarentena-selected-file-size">{formatFileSize(selectedFile.size)}</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="k-btn k-btn-ghost k-btn-sm"
                      onClick={() => setSelectedFile(null)}
                      title="Remover arquivo"
                      style={{ color: 'var(--k-danger)' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ) : (
                  <label className="quarentena-dropzone">
                    <Upload size={24} className="quarentena-dropzone-icon" />
                    <span style={{ fontWeight: 600, color: 'var(--k-text-primary)' }}>
                      Clique para selecionar ou arraste o arquivo aqui
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--k-text-muted)' }}>
                      Formatos aceitos: PDF, DOCX, DOC, TXT, RTF, MD, CSV, XLSX (até 50 MB)
                    </span>
                    <input
                      type="file"
                      hidden
                      onChange={handleFileChange}
                      accept=".pdf,.docx,.doc,.txt,.rtf,.md,.csv,.xlsx,.json,.tsv"
                    />
                  </label>
                )}
              </div>

              <label className="quarentena-form-label">
                Título do Protocolo, Artigo ou Bula *
              </label>
              <input
                className="k-input"
                placeholder="Ex: Protocolo de Manejo Clínico de Dengue 2026"
                value={suggestForm.title}
                onChange={(e) => setSuggestForm({ ...suggestForm, title: e.target.value })}
                required={!selectedFile}
              />

              <div className="quarentena-form-row">
                <div style={{ flex: 1 }}>
                  <label className="quarentena-form-label">Tipo do Conhecimento</label>
                  <select
                    className="k-select"
                    value={suggestForm.source_type}
                    onChange={(e) => setSuggestForm({ ...suggestForm, source_type: e.target.value })}
                  >
                    <option value="protocolo">Protocolo Clínico</option>
                    <option value="diretriz">Diretriz Médica</option>
                    <option value="artigo">Artigo Científico</option>
                    <option value="bula">Bula de Medicamento</option>
                    <option value="outro">Outro Documento</option>
                  </select>
                </div>

                <div style={{ flex: 2 }}>
                  <label className="quarentena-form-label">Link / URL da Fonte (Opcional)</label>
                  <input
                    className="k-input"
                    type="url"
                    placeholder="https://saude.gov.br/... ou link do artigo"
                    value={suggestForm.source_url}
                    onChange={(e) => setSuggestForm({ ...suggestForm, source_url: e.target.value })}
                  />
                </div>
              </div>

              <label className="quarentena-form-label">
                Resumo, Texto Principal ou Observações do Médico (Opcional)
              </label>
              <textarea
                className="k-input quarentena-textarea"
                rows={3}
                placeholder="Pontos mais importantes, doses recomendadas, justificativa de uso ou contexto..."
                value={suggestForm.content_text}
                onChange={(e) => setSuggestForm({ ...suggestForm, content_text: e.target.value })}
              />

              <div className="quarentena-modal-actions">
                <button
                  type="button"
                  className="k-btn k-btn-secondary"
                  onClick={() => { setSuggestModalOpen(false); setSelectedFile(null); }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="k-btn k-btn-primary"
                  disabled={suggesting}
                >
                  {suggesting ? (
                    <><Loader2 size={16} className="k-animate-spin" /> Enviando Arquivo...</>
                  ) : (
                    <><Send size={16} /> Enviar para a Curadoria</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Rejeição com Motivo (Admin) */}
      {rejectModal.open && (
        <div className="quarentena-modal-backdrop">
          <div className="quarentena-modal-card">
            <div className="quarentena-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="quarentena-modal-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}>
                  <XCircle size={20} />
                </div>
                <div>
                  <h3 className="quarentena-modal-title">Rejeitar Sugestão #{rejectModal.id}</h3>
                  <p className="k-text-xs k-text-muted">Informe o motivo da não aprovação para orientar o médico autor</p>
                </div>
              </div>
              <button
                className="k-btn k-btn-ghost k-btn-icon"
                onClick={() => setRejectModal({ open: false, id: null })}
              >
                <X size={18} />
              </button>
            </div>

            <div className="quarentena-modal-form">
              <label className="quarentena-form-label">
                Motivo / Justificativa da Rejeição:
              </label>
              <textarea
                className="k-input quarentena-textarea"
                rows={3}
                placeholder="Ex: Diretriz desatualizada; Favor enviar a versão 2026 publicada pela Sociedade..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />

              <div className="quarentena-modal-actions">
                <button
                  type="button"
                  className="k-btn k-btn-secondary"
                  onClick={() => setRejectModal({ open: false, id: null })}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="k-btn k-btn-danger"
                  onClick={handleConfirmReject}
                  disabled={rejecting}
                >
                  {rejecting ? (
                    <><Loader2 size={16} className="k-animate-spin" /> Registrando...</>
                  ) : (
                    <><X size={16} /> Confirmar Rejeição</>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Ação em Massa (Admin) */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.type === 'approve' ? 'Aprovar itens selecionados?' : 'Rejeitar itens selecionados?'}
        message={
          confirmModal.type === 'approve'
            ? `${confirmModal.ids.length} ite${confirmModal.ids.length > 1 ? 'ns' : 'm'} ser${confirmModal.ids.length > 1 ? 'ão inseridos' : 'á inserido'} permanentemente no Grafo Médico Global.`
            : `${confirmModal.ids.length} ite${confirmModal.ids.length > 1 ? 'ns' : 'm'} ser${confirmModal.ids.length > 1 ? 'ão rejeitados' : 'á rejeitado'}.`
        }
        confirmLabel={confirmModal.type === 'approve' ? 'Aprovar Todos' : 'Rejeitar Todos'}
        variant={confirmModal.type === 'approve' ? 'warning' : 'danger'}
        loading={confirmLoading}
        onConfirm={() => handleBulkAction(confirmModal.type)}
        onCancel={() => setConfirmModal({ open: false, type: null, ids: [] })}
      />
    </div>
  )
}
