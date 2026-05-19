/* ============================================================
   ClinicasPage — Listagem com CRUD funcional
   Editar, Desativar, Excluir com ConfirmModal + Toast
   ============================================================ */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Plus,
  Search,
  Building2,
  Wifi,
  WifiOff,
  MoreVertical,
  Edit3,
  Power,
  Trash2,
  Bot,
  Crown,
  Loader2,
} from 'lucide-react'
import { fetchTenants, deleteTenant, updateTenant } from '../../services/api'
import { useToast } from '../../components/Toast'
import ConfirmModal from '../../components/ConfirmModal'
import './ClinicasPage.css'

export default function ClinicasPage() {
  const navigate = useNavigate()
  const { addToast } = useToast()

  const [clinicas, setClinicas] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [menuOpen, setMenuOpen] = useState(null)

  // Modal state
  const [modal, setModal] = useState({ open: false, type: null, clinica: null })
  const [modalLoading, setModalLoading] = useState(false)

  useEffect(() => {
    loadClinicas()
  }, [showInactive])

  async function loadClinicas() {
    setLoading(true)
    try {
      const data = await fetchTenants(!showInactive)
      setClinicas(data)
    } catch {
      // Mock data for development (before backend is connected)
      setClinicas([])
    } finally {
      setLoading(false)
    }
  }

  const filtered = clinicas.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.slug.toLowerCase().includes(search.toLowerCase())
  )

  const activeCount = clinicas.filter(c => c.active).length
  const inactiveCount = clinicas.filter(c => !c.active).length

  function openMenu(e, id) {
    e.stopPropagation()
    setMenuOpen(menuOpen === id ? null : id)
  }

  function handleEdit(clinica) {
    setMenuOpen(null)
    navigate(`/clinicas/${clinica.id}/editar`)
  }

  function handleToggleActive(clinica) {
    setMenuOpen(null)
    setModal({
      open: true,
      type: clinica.active ? 'deactivate' : 'activate',
      clinica,
    })
  }

  function handleDelete(clinica) {
    setMenuOpen(null)
    setModal({ open: true, type: 'delete', clinica })
  }

  async function confirmModalAction() {
    setModalLoading(true)
    try {
      if (modal.type === 'delete') {
        await deleteTenant(modal.clinica.id)
        addToast(`"${modal.clinica.name}" removida com sucesso.`, 'success')
      } else if (modal.type === 'deactivate') {
        await updateTenant(modal.clinica.id, { active: false })
        addToast(`"${modal.clinica.name}" desativada.`, 'warning')
      } else if (modal.type === 'activate') {
        await updateTenant(modal.clinica.id, { active: true })
        addToast(`"${modal.clinica.name}" reativada!`, 'success')
      }
      setModal({ open: false, type: null, clinica: null })
      loadClinicas()
    } catch (err) {
      addToast('Erro ao executar ação. Tente novamente.', 'error')
    } finally {
      setModalLoading(false)
    }
  }

  const MODAL_PROPS = {
    delete: {
      title: 'Excluir clínica?',
      message: `Esta ação não pode ser desfeita. A clínica "${modal.clinica?.name}" será permanentemente removida.`,
      confirmLabel: 'Excluir',
      variant: 'danger',
    },
    deactivate: {
      title: 'Desativar clínica?',
      message: `O atendimento de "${modal.clinica?.name}" será pausado. Você pode reativar depois.`,
      confirmLabel: 'Desativar',
      variant: 'warning',
    },
    activate: {
      title: 'Reativar clínica?',
      message: `O atendimento de "${modal.clinica?.name}" será retomado imediatamente.`,
      confirmLabel: 'Reativar',
      variant: 'warning',
    },
  }

  // Close menu on outside click
  useEffect(() => {
    function handleClick() { setMenuOpen(null) }
    if (menuOpen) {
      document.addEventListener('click', handleClick)
      return () => document.removeEventListener('click', handleClick)
    }
  }, [menuOpen])

  return (
    <div className="clinicas-page">
      {/* Header */}
      <div className="clinicas-header">
        <div>
          <h2 className="clinicas-title">Gestão de Clínicas</h2>
          <p className="k-text-sm k-text-muted">{clinicas.length} clínicas cadastradas</p>
        </div>
        <button className="k-btn k-btn-primary" onClick={() => navigate('/clinicas/nova')} id="btn-nova-clinica">
          <Plus size={18} /> Nova Clínica
        </button>
      </div>

      {/* Search + Filter */}
      <div className="clinicas-toolbar">
        <div className="clinicas-search">
          <Search size={18} className="clinicas-search-icon" />
          <input
            className="k-input"
            placeholder="Buscar por nome ou slug..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            id="input-search-clinicas"
          />
        </div>
        <label className="clinicas-filter-toggle">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={e => setShowInactive(e.target.checked)}
          />
          <span className="k-text-sm">Mostrar inativas</span>
        </label>
      </div>

      {/* Stats */}
      <div className="clinicas-stats">
        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'var(--k-accent-glow)', color: 'var(--k-accent)' }}>
            <Building2 size={22} />
          </div>
          <div>
            <div className="k-stat-value">{clinicas.length}</div>
            <div className="k-stat-label">Total de Clínicas</div>
          </div>
        </div>
        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'var(--k-success-bg)', color: 'var(--k-success)' }}>
            <Wifi size={22} />
          </div>
          <div>
            <div className="k-stat-value">{activeCount}</div>
            <div className="k-stat-label">Ativas</div>
          </div>
        </div>
        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'var(--k-danger-bg)', color: 'var(--k-danger)' }}>
            <WifiOff size={22} />
          </div>
          <div>
            <div className="k-stat-value">{inactiveCount}</div>
            <div className="k-stat-label">Inativas</div>
          </div>
        </div>
      </div>

      {/* Clinics List */}
      {loading ? (
        <div className="clinicas-skeleton-grid">
          {[1, 2, 3].map(i => (
            <div key={i} className="clinica-card-skeleton">
              <div className="k-skeleton" style={{ height: 20, width: '60%', marginBottom: 12 }} />
              <div className="k-skeleton" style={{ height: 14, width: '40%', marginBottom: 8 }} />
              <div className="k-skeleton" style={{ height: 14, width: '80%' }} />
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="clinicas-grid">
          {filtered.map(clinica => (
            <div
              key={clinica.id}
              className={`clinica-card ${!clinica.active ? 'clinica-card--inactive' : ''}`}
              onClick={() => navigate(`/clinicas/${clinica.id}/editar`)}
              id={`card-${clinica.slug}`}
            >
              <div className="clinica-card-header">
                <div>
                  <h3 className="clinica-card-name">{clinica.name}</h3>
                  <span className="clinica-card-slug">/{clinica.slug}</span>
                </div>
                <div className="clinica-card-actions">
                  <span className={`k-badge ${clinica.active ? 'k-badge-success' : 'k-badge-danger'}`}>
                    {clinica.active ? '● Ativa' : '● Inativa'}
                  </span>
                  <button
                    className="k-btn k-btn-ghost k-btn-icon clinica-menu-btn"
                    onClick={(e) => openMenu(e, clinica.id)}
                    id={`menu-${clinica.slug}`}
                  >
                    <MoreVertical size={16} />
                  </button>
                  {menuOpen === clinica.id && (
                    <div className="clinica-menu" onClick={e => e.stopPropagation()}>
                      <button onClick={() => handleEdit(clinica)}>
                        <Edit3 size={14} /> Editar
                      </button>
                      <button onClick={() => handleToggleActive(clinica)}>
                        <Power size={14} /> {clinica.active ? 'Desativar' : 'Reativar'}
                      </button>
                      <button className="clinica-menu-danger" onClick={() => handleDelete(clinica)}>
                        <Trash2 size={14} /> Excluir
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <div className="clinica-card-body">
                <div className="clinica-card-meta">
                  <Bot size={14} />
                  <span>{clinica.evolution_instance || 'Sem instância'}</span>
                </div>
                {clinica.config?.jarvis?.enabled && (
                  <div className="clinica-card-meta clinica-card-meta--premium">
                    <Crown size={14} />
                    <span>Jarvis Ativo</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="k-empty">
          <Building2 size={56} className="k-empty-icon" />
          <h3>Nenhuma clínica encontrada</h3>
          <p className="k-text-sm k-text-muted" style={{ marginTop: 4, marginBottom: 16 }}>
            {search ? 'Tente outro termo de busca.' : 'Cadastre sua primeira clínica para começar.'}
          </p>
          {!search && (
            <button className="k-btn k-btn-primary" onClick={() => navigate('/clinicas/nova')}>
              <Plus size={18} /> Cadastrar Clínica
            </button>
          )}
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={modal.open}
        loading={modalLoading}
        onConfirm={confirmModalAction}
        onCancel={() => setModal({ open: false, type: null, clinica: null })}
        {...(MODAL_PROPS[modal.type] || {})}
      />
    </div>
  )
}
