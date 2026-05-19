/* ============================================================
   ConfiguracoesPage — Command Center de Infraestrutura
   Status live dos serviços + Reasoning Health + Canais CEO
   ============================================================ */

import { useState, useEffect, useCallback } from 'react'
import {
  Settings, RefreshCw, Cpu, Database, MessageSquare, Radio,
  CheckCircle2, XCircle, AlertTriangle, Loader2, Shield,
  Zap, Brain, HardDrive, Server, Eye, EyeOff, Save,
  Activity, HeartPulse, TrendingUp, TrendingDown, Clock,
} from 'lucide-react'
import { fetchSystemStatus, updatePrometheusConfig, fetchReasoningHealth } from '../../services/api'
import { useToast } from '../../components/Toast'
import './ConfiguracoesPage.css'

const SERVICE_ICONS = {
  'Gemini': Brain,
  'OpenRouter': Zap,
  'Evolution Go': MessageSquare,
  'PostgreSQL': Database,
  'ChromaDB': HardDrive,
  'Neo4j': Database,
  'Redis': Server,
  'MinIO': HardDrive,
}

const STATUS_CONFIG = {
  online: { icon: CheckCircle2, color: 'var(--k-success)', label: 'Online' },
  offline: { icon: XCircle, color: 'var(--k-danger)', label: 'Offline' },
  degraded: { icon: AlertTriangle, color: 'var(--k-warning)', label: 'Degradado' },
  checking: { icon: Loader2, color: 'var(--k-text-muted)', label: 'Verificando...' },
}

const HEALTH_CONFIG = {
  healthy:  { color: 'var(--k-success)', label: 'Saudável', icon: HeartPulse },
  warning:  { color: 'var(--k-warning)', label: 'Atenção',  icon: AlertTriangle },
  critical: { color: 'var(--k-danger)',  label: 'Crítico',  icon: XCircle },
}

// Mock data for development (will be replaced by real API)
const MOCK_STATUS = {
  providers: [
    { name: 'Gemini', configured: true, masked_key: '••••7f3a', status: 'online', latency_ms: 120, model: 'gemini-2.5-pro' },
    { name: 'OpenRouter', configured: true, masked_key: '••••a2b1', status: 'online', latency_ms: 85, model: 'claude-sonnet-4' },
  ],
  services: [
    { name: 'Evolution Go', status: 'online', version: '2.1.0', details: '3 instâncias ativas' },
    { name: 'PostgreSQL', status: 'online', version: '16-alpine', details: '2 databases' },
    { name: 'ChromaDB', status: 'online', version: 'latest', details: '3 coleções' },
    { name: 'Neo4j', status: 'online', version: '5-community', details: '127 nós no grafo' },
    { name: 'Redis', status: 'online', version: '7-alpine', details: '42MB / 256MB' },
    { name: 'MinIO', status: 'online', version: 'latest', details: '1.2 GB armazenados' },
  ],
}

const MOCK_REASONING = {
  agents: [
    { agent_name: 'Front-Desk', tenant_slug: 'clinica-sorriso', total_calls: 184, successful_calls: 179, failures: 5, loops_detected: 0, success_rate: 97.3, status: 'healthy', last_error: '', last_updated: new Date().toISOString() },
    { agent_name: 'Manager', tenant_slug: 'clinica-sorriso', total_calls: 52, successful_calls: 38, failures: 14, loops_detected: 1, success_rate: 73.1, status: 'critical', last_error: 'ademed_login: Timeout na autenticação', last_updated: new Date().toISOString() },
    { agent_name: 'Front-Desk', tenant_slug: 'clinica-vida', total_calls: 97, successful_calls: 92, failures: 5, loops_detected: 0, success_rate: 94.8, status: 'healthy', last_error: '', last_updated: new Date().toISOString() },
    { agent_name: 'Sincronizador', tenant_slug: 'global', total_calls: 310, successful_calls: 287, failures: 23, loops_detected: 2, success_rate: 92.6, status: 'warning', last_error: 'sync_erp: Rate limit exceeded', last_updated: new Date().toISOString() },
  ],
}

export default function ConfiguracoesPage() {
  const { addToast } = useToast()
  const [status, setStatus] = useState(null)
  const [reasoning, setReasoning] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastCheck, setLastCheck] = useState(null)

  // Prometheus config
  const [prometheusConfig, setPrometheusConfig] = useState({
    ceo_whatsapp: '',
    ceo_telegram_token: '',
    ceo_mask: 'Você é o Prometheus, consultor estratégico pessoal do CEO do Kairós Intelligence. Trate-o como "Chefe". Seja direto, analítico e estratégico.',
  })
  const [showPasswords, setShowPasswords] = useState({})
  const [savingPrometheus, setSavingPrometheus] = useState(false)

  const loadStatus = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)

    try {
      const [statusData, reasoningData] = await Promise.all([
        fetchSystemStatus(),
        fetchReasoningHealth(),
      ])
      setStatus(statusData)
      setReasoning(reasoningData)
    } catch {
      // Use mock in development
      setStatus(MOCK_STATUS)
      setReasoning(MOCK_REASONING)
    } finally {
      setLoading(false)
      setRefreshing(false)
      setLastCheck(new Date())
    }
  }, [])

  useEffect(() => {
    loadStatus()
    const interval = setInterval(() => loadStatus(true), 30000)
    return () => clearInterval(interval)
  }, [loadStatus])

  async function handleSavePrometheus() {
    setSavingPrometheus(true)
    try {
      await updatePrometheusConfig(prometheusConfig)
      addToast('Configurações do Prometheus salvas!', 'success')
    } catch {
      addToast('Erro ao salvar. Backend não conectado.', 'error')
    } finally {
      setSavingPrometheus(false)
    }
  }

  function renderStatusBadge(s) {
    const cfg = STATUS_CONFIG[s] || STATUS_CONFIG.checking
    const Icon = cfg.icon
    return (
      <span className="config-status-badge" style={{ color: cfg.color }}>
        <Icon size={14} className={s === 'checking' ? 'k-animate-spin' : ''} />
        {cfg.label}
      </span>
    )
  }

  function renderHealthBadge(s) {
    const cfg = HEALTH_CONFIG[s] || HEALTH_CONFIG.healthy
    const Icon = cfg.icon
    return (
      <span className="config-health-badge" style={{ '--health-color': cfg.color }}>
        <Icon size={13} />
        {cfg.label}
      </span>
    )
  }

  function renderSuccessRateBar(rate) {
    const color = rate >= 95 ? 'var(--k-success)' : rate >= 85 ? 'var(--k-warning)' : 'var(--k-danger)'
    return (
      <div className="reasoning-rate-bar">
        <div className="reasoning-rate-fill" style={{ width: `${rate}%`, background: color }} />
        <span className="reasoning-rate-label">{rate}%</span>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="clinicas-loading">
        <Loader2 size={32} className="k-animate-spin" />
        <p>Consultando infraestrutura...</p>
      </div>
    )
  }

  const allOnline = status?.services?.every(s => s.status === 'online') && status?.providers?.every(p => p.status === 'online')
  const hasCritical = reasoning?.agents?.some(a => a.status === 'critical')

  return (
    <div className="config-page">
      {/* Header */}
      <div className="config-header">
        <div>
          <h2 className="config-title">
            <Settings size={24} /> Command Center
          </h2>
          <p className="k-text-sm k-text-muted">
            Monitoramento live da infraestrutura Kairós
            {lastCheck && <> · Última verificação: {lastCheck.toLocaleTimeString('pt-BR')}</>}
          </p>
        </div>
        <div className="config-header-actions">
          <span className={`config-global-status ${allOnline && !hasCritical ? 'config-global-online' : 'config-global-alert'}`}>
            {allOnline && !hasCritical ? <><CheckCircle2 size={16} /> Todos os sistemas operacionais</> : <><AlertTriangle size={16} /> Atenção necessária</>}
          </span>
          <button className="k-btn k-btn-secondary" onClick={() => loadStatus(true)} disabled={refreshing}>
            <RefreshCw size={16} className={refreshing ? 'k-animate-spin' : ''} />
            {refreshing ? 'Verificando...' : 'Verificar Agora'}
          </button>
        </div>
      </div>

      {/* Section 1: AI Providers */}
      <div className="config-section">
        <h3 className="config-section-title"><Cpu size={18} /> Provedores de IA</h3>
        <div className="config-cards-grid">
          {status?.providers?.map((provider, i) => {
            const Icon = SERVICE_ICONS[provider.name] || Cpu
            return (
              <div key={i} className={`config-service-card ${provider.status !== 'online' ? 'config-service-card--alert' : ''}`}>
                <div className="config-service-header">
                  <div className="config-service-icon config-service-icon--provider">
                    <Icon size={20} />
                  </div>
                  <div className="config-service-info">
                    <strong>{provider.name}</strong>
                    {provider.model && <span className="config-service-model">{provider.model}</span>}
                  </div>
                  {renderStatusBadge(provider.status)}
                </div>
                <div className="config-service-details">
                  <div className="config-detail-row">
                    <Shield size={13} />
                    <span>Chave: <code>{provider.masked_key}</code></span>
                  </div>
                  {provider.latency_ms && (
                    <div className="config-detail-row">
                      <Radio size={13} />
                      <span>Latência: {provider.latency_ms}ms</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Section 2: Infrastructure */}
      <div className="config-section">
        <h3 className="config-section-title"><Server size={18} /> Infraestrutura</h3>
        <div className="config-cards-grid config-cards-grid--infra">
          {status?.services?.map((service, i) => {
            const Icon = SERVICE_ICONS[service.name] || Server
            return (
              <div key={i} className={`config-service-card config-service-card--compact ${service.status !== 'online' ? 'config-service-card--alert' : ''}`}>
                <div className="config-service-header">
                  <div className="config-service-icon">
                    <Icon size={18} />
                  </div>
                  <div className="config-service-info">
                    <strong>{service.name}</strong>
                    {service.version && <span className="config-service-version">{service.version}</span>}
                  </div>
                  {renderStatusBadge(service.status)}
                </div>
                {service.details && (
                  <p className="config-service-meta">{service.details}</p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Section 3: Reasoning Health — NEW! */}
      <div className="config-section config-section--reasoning">
        <h3 className="config-section-title">
          <Activity size={18} /> Reasoning Health
          <span className="config-section-badge">OpenClaw Telemetry</span>
        </h3>
        <p className="k-text-sm k-text-muted" style={{ marginBottom: 16 }}>
          Taxa de sucesso das ferramentas executadas por cada agente. Alertas são disparados se cair abaixo de 85%.
        </p>

        {reasoning?.agents?.length > 0 ? (
          <div className="reasoning-table-wrapper">
            <table className="reasoning-table">
              <thead>
                <tr>
                  <th>Agente</th>
                  <th>Clínica</th>
                  <th>Chamadas</th>
                  <th>Taxa de Sucesso</th>
                  <th>Falhas</th>
                  <th>Loops</th>
                  <th>Status</th>
                  <th>Último Erro</th>
                </tr>
              </thead>
              <tbody>
                {reasoning.agents.map((agent, i) => (
                  <tr key={i} className={`reasoning-row reasoning-row--${agent.status}`}>
                    <td>
                      <div className="reasoning-agent-name">
                        <HeartPulse size={14} style={{ color: HEALTH_CONFIG[agent.status]?.color }} />
                        {agent.agent_name}
                      </div>
                    </td>
                    <td>
                      <span className="reasoning-tenant">{agent.tenant_slug}</span>
                    </td>
                    <td className="reasoning-number">{agent.total_calls}</td>
                    <td>{renderSuccessRateBar(agent.success_rate)}</td>
                    <td className="reasoning-number">
                      {agent.failures > 0 ? (
                        <span className="reasoning-failures">
                          <TrendingDown size={12} /> {agent.failures}
                        </span>
                      ) : (
                        <span className="reasoning-ok">0</span>
                      )}
                    </td>
                    <td className="reasoning-number">
                      {agent.loops_detected > 0 ? (
                        <span className="reasoning-loops">
                          <AlertTriangle size={12} /> {agent.loops_detected}
                        </span>
                      ) : (
                        <span className="reasoning-ok">0</span>
                      )}
                    </td>
                    <td>{renderHealthBadge(agent.status)}</td>
                    <td>
                      {agent.last_error ? (
                        <span className="reasoning-error-msg">{agent.last_error}</span>
                      ) : (
                        <span className="reasoning-ok">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="reasoning-empty">
            <Activity size={32} />
            <p>Nenhum dado de telemetria recebido ainda.</p>
            <span className="k-text-sm k-text-muted">Os agentes começarão a reportar após o deploy na VPS.</span>
          </div>
        )}
      </div>

      {/* Section 4: Prometheus / CEO Channels */}
      <div className="config-section">
        <h3 className="config-section-title"><Brain size={18} /> Prometheus — Canais do CEO</h3>
        <p className="k-text-sm k-text-muted" style={{ marginBottom: 16 }}>
          Configure como o Prometheus se comunica com você fora do painel.
        </p>
        <div className="config-prometheus-form">
          <div className="form-grid">
            <div className="k-input-group">
              <label className="k-label">WhatsApp Pessoal do CEO</label>
              <input className="k-input" value={prometheusConfig.ceo_whatsapp}
                onChange={e => setPrometheusConfig(p => ({ ...p, ceo_whatsapp: e.target.value }))}
                placeholder="(00) 00000-0000" id="input-ceo-whatsapp" />
            </div>
            <div className="k-input-group">
              <label className="k-label">Token Bot Telegram do CEO</label>
              <div className="k-input-password">
                <input className="k-input" type={showPasswords.ceo_tg ? 'text' : 'password'}
                  value={prometheusConfig.ceo_telegram_token}
                  onChange={e => setPrometheusConfig(p => ({ ...p, ceo_telegram_token: e.target.value }))}
                  placeholder="1234567890:ABCdef..." id="input-ceo-telegram" />
                <button className="k-toggle-eye" onClick={() => setShowPasswords(p => ({ ...p, ceo_tg: !p.ceo_tg }))} type="button">
                  {showPasswords.ceo_tg ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>
          <div className="k-input-group" style={{ marginTop: 16 }}>
            <label className="k-label">Máscara do CEO (Identidade do Prometheus)</label>
            <textarea className="k-textarea" rows={4} value={prometheusConfig.ceo_mask}
              onChange={e => setPrometheusConfig(p => ({ ...p, ceo_mask: e.target.value }))}
              placeholder="Descreva como o Prometheus deve se comportar ao falar com você..."
              id="input-ceo-mask" />
          </div>
          <div style={{ marginTop: 16 }}>
            <button className="k-btn k-btn-primary" onClick={handleSavePrometheus} disabled={savingPrometheus}>
              {savingPrometheus ? <Loader2 size={16} className="k-animate-spin" /> : <Save size={16} />}
              {savingPrometheus ? 'Salvando...' : 'Salvar Configurações'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
