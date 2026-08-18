/* ============================================================
   ClinicoDashboard — Visão geral do Módulo Clínico
   Hero + Stats + Action Cards
   ============================================================ */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Stethoscope,
  Activity,
  FileText,
  ShieldAlert,
  Network,
  Heart,
  Loader2,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Mic,
  Search,
  Plus,
  Clock,
} from 'lucide-react'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import { clinicalHealth, fetchQuarantine, listCopilotSessions } from '../../services/clinicalApi'
import { useToast } from '../../components/Toast'
import './ClinicoDashboard.css'

const ACTION_CARDS = [
  {
    id: 'nova-consulta',
    icon: Mic,
    title: 'Nova Consulta',
    description: 'Iniciar consulta com copiloto IA em tempo real',
    path: '/clinico/consulta',
    gradient: 'linear-gradient(135deg, #10b981, #14b8a6)',
    glow: 'rgba(16, 185, 129, 0.2)',
  },
  {
    id: 'documentos',
    icon: FileText,
    title: 'Documentos Médicos',
    description: 'Gerar receitas, atestados e laudos automaticamente',
    path: '/clinico/documentos',
    gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    glow: 'rgba(139, 92, 246, 0.2)',
  },
  {
    id: 'quarentena',
    icon: ShieldAlert,
    title: 'Quarentena do Grafo',
    description: 'Revisar e aprovar entidades médicas extraídas',
    path: '/clinico/quarentena',
    gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    glow: 'rgba(245, 158, 11, 0.2)',
  },
  {
    id: 'grafo',
    icon: Network,
    title: 'Base de Conhecimento',
    description: 'Explorar o grafo médico com busca inteligente',
    path: '/clinico/grafo',
    gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    glow: 'rgba(59, 130, 246, 0.2)',
  },
  {
    id: 'historico',
    icon: Clock,
    title: 'Histórico de Atendimentos',
    description: 'Consultar atendimentos anteriores e documentos',
    path: '/clinico/historico',
    gradient: 'linear-gradient(135deg, #ec4899, #f43f5e)',
    glow: 'rgba(236, 72, 153, 0.2)',
  },
]

export default function ClinicoDashboard() {
  const navigate = useNavigate()
  const { session } = useClinicalAuth()
  const { addToast } = useToast()

  const [serviceStatus, setServiceStatus] = useState('checking')
  const [stats, setStats] = useState({
    quarentinePending: 0,
    activeSessions: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        // Health check
        const health = await clinicalHealth()
        setServiceStatus((health?.postgres === 'online' || health?.status === 'ok') ? 'online' : 'degraded')
      } catch {
        setServiceStatus('offline')
      }

      try {
        // Quarantine count
        const quarantine = await fetchQuarantine()
        const pending = Array.isArray(quarantine)
          ? quarantine.filter((q) => q.status === 'pending').length
          : 0
        setStats((prev) => ({ ...prev, quarentinePending: pending }))
      } catch {
        // Silently ignore
      }

      try {
        // Active copilot sessions
        const sessions = await listCopilotSessions()
        setStats((prev) => ({
          ...prev,
          activeSessions: Array.isArray(sessions) ? sessions.length : 0,
        }))
      } catch {
        // Silently ignore
      }

      setLoading(false)
    }

    loadData()
  }, [])

  const STATUS_MAP = {
    online: { icon: CheckCircle2, label: 'Online', color: 'var(--k-success)', className: 'k-badge-success' },
    offline: { icon: XCircle, label: 'Offline', color: 'var(--k-danger)', className: 'k-badge-danger' },
    degraded: { icon: AlertTriangle, label: 'Degradado', color: 'var(--k-warning)', className: 'k-badge-warning' },
    checking: { icon: Loader2, label: 'Verificando...', color: 'var(--k-text-muted)', className: 'k-badge-info' },
  }

  const status = STATUS_MAP[serviceStatus]
  const StatusIcon = status.icon

  return (
    <div className="clinico-dashboard">
      {/* Header */}
      <div className="clinico-header">
        <div className="clinico-header-left">
          <h2 className="clinico-title">Módulo Clínico</h2>
          <p className="k-text-sm k-text-muted">
            Consultas Médicas/Avaliação
          </p>
        </div>
        
      </div>

      {/* Hero Card */}
      <div className="clinico-hero">
        <div className="clinico-hero-glow" />
        <div className="clinico-hero-content">
          <div className="clinico-hero-icon">
            <Stethoscope size={28} />
          </div>
          <div className="clinico-hero-text">
            <h3>Bem-vindo, {session.doctorName}</h3>
            <p>
              O módulo clínico integra IA generativa com o seu atendimento.
              Transcrição em tempo real, estruturação SOAP automática e geração
              instantânea de documentos médicos.
            </p>
          </div>
          <div className="clinico-hero-status">
            <span className={`k-badge ${status.className}`}>
              <StatusIcon size={14} className={serviceStatus === 'checking' ? 'k-animate-spin' : ''} />
              Serviço {status.label}
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="clinico-stats">
        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }}>
            <Activity size={22} />
          </div>
          <div>
            <div className="k-stat-value">
              {loading ? <span className="k-skeleton" style={{ width: 32, height: 28, display: 'inline-block' }} /> : stats.activeSessions}
            </div>
            <div className="k-stat-label">Sessões Ativas</div>
          </div>
        </div>

        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b' }}>
            <ShieldAlert size={22} />
          </div>
          <div>
            <div className="k-stat-value">
              {loading ? <span className="k-skeleton" style={{ width: 32, height: 28, display: 'inline-block' }} /> : stats.quarentinePending}
            </div>
            <div className="k-stat-label">Itens em Quarentena</div>
          </div>
        </div>

        <div className="k-stat-card">
          <div className="k-stat-icon" style={{ background: 'rgba(139, 92, 246, 0.12)', color: '#8b5cf6' }}>
            <Heart size={22} />
          </div>
          <div>
            <div className="k-stat-value">
              <StatusIcon size={22} style={{ color: status.color }} className={serviceStatus === 'checking' ? 'k-animate-spin' : ''} />
            </div>
            <div className="k-stat-label">Status do Serviço</div>
          </div>
        </div>
      </div>

      {/* Action Cards */}
      <h3 className="clinico-section-title">Ações Rápidas</h3>
      <div className="clinico-actions">
        {ACTION_CARDS.map((card) => {
          const Icon = card.icon
          return (
            <button
              key={card.id}
              className="clinico-action-card"
              onClick={() => navigate(card.path)}
              id={`action-${card.id}`}
            >
              <div
                className="clinico-action-icon"
                style={{ background: card.gradient, boxShadow: `0 4px 20px ${card.glow}` }}
              >
                <Icon size={24} color="white" />
              </div>
              <div className="clinico-action-text">
                <h4>{card.title}</h4>
                <p>{card.description}</p>
              </div>
              <ArrowRight size={18} className="clinico-action-arrow" />
            </button>
          )
        })}
      </div>
    </div>
  )
}
