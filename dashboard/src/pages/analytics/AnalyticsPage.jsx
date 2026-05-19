/* ============================================================
   AnalyticsPage — Dashboard de Analytics (Fase 4)
   ============================================================ */

import {
  BarChart3,
  TrendingUp,
  MessageSquare,
  Zap,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Minus,
} from 'lucide-react'
import './AnalyticsPage.css'

const MOCK_STATS = [
  { label: 'Mensagens Hoje', value: '1.247', icon: MessageSquare, color: 'var(--k-accent)', bg: 'rgba(139,92,246,0.15)' },
  { label: 'Tokens Consumidos', value: '84.3K', icon: Zap, color: 'var(--k-gold)', bg: 'var(--k-gold-glow)' },
  { label: 'Taxa de Resolução', value: '94%', icon: TrendingUp, color: 'var(--k-success)', bg: 'var(--k-success-bg)' },
  { label: 'Alertas de Sentimento', value: '3', icon: AlertTriangle, color: 'var(--k-warning)', bg: 'var(--k-warning-bg)' },
]

const MOCK_SENTIMENT = [
  { clinica: 'Clínica Sorriso', positivo: 87, neutro: 10, negativo: 3, alertas: 1 },
  { clinica: 'OdontoVida', positivo: 92, neutro: 6, negativo: 2, alertas: 0 },
  { clinica: 'Clínica Harmonia', positivo: 78, neutro: 14, negativo: 8, alertas: 2 },
]

export default function AnalyticsPage() {
  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h2 className="clinicas-title">Analytics & Auditoria Cognitiva</h2>
        <span className="k-badge k-badge-info">Fase 4</span>
      </div>

      {/* Stat Cards */}
      <div className="analytics-stats">
        {MOCK_STATS.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="k-stat-card">
              <div className="k-stat-icon" style={{ background: stat.bg, color: stat.color }}>
                <Icon size={22} />
              </div>
              <div>
                <div className="k-stat-value">{stat.value}</div>
                <div className="k-stat-label">{stat.label}</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Auditoria Cognitiva */}
      <div className="k-card">
        <h3 style={{ marginBottom: 16, fontWeight: 700 }}>
          🧠 Auditoria Cognitiva de Sentimento
        </h3>
        <p className="k-text-sm k-text-muted" style={{ marginBottom: 16 }}>
          O sistema analisa todas as conversas do dia e avalia o humor dos pacientes.
        </p>

        <div className="k-table-wrapper">
          <table className="k-table">
            <thead>
              <tr>
                <th>Clínica</th>
                <th>Positivo</th>
                <th>Neutro</th>
                <th>Negativo</th>
                <th>Alertas</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_SENTIMENT.map((row) => (
                <tr key={row.clinica}>
                  <td style={{ fontWeight: 600 }}>{row.clinica}</td>
                  <td>
                    <span className="analytics-sentiment analytics-sentiment--positive">
                      <ThumbsUp size={12} /> {row.positivo}%
                    </span>
                  </td>
                  <td>
                    <span className="analytics-sentiment analytics-sentiment--neutral">
                      <Minus size={12} /> {row.neutro}%
                    </span>
                  </td>
                  <td>
                    <span className="analytics-sentiment analytics-sentiment--negative">
                      <ThumbsDown size={12} /> {row.negativo}%
                    </span>
                  </td>
                  <td>
                    {row.alertas > 0 ? (
                      <span className="k-badge k-badge-warning">{row.alertas} alerta{row.alertas > 1 ? 's' : ''}</span>
                    ) : (
                      <span className="k-badge k-badge-success">Tudo OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Placeholder */}
      <div className="k-card analytics-placeholder">
        <BarChart3 size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
        <h3>Gráficos de Consumo</h3>
        <p className="k-text-sm k-text-muted">
          Os gráficos detalhados de consumo de tokens, custo por clínica e logs técnicos estarão disponíveis quando o backend estiver integrado.
        </p>
      </div>
    </div>
  )
}
