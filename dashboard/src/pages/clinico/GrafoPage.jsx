
import { Cpu, Network } from 'lucide-react'
import AIChat from '../../components/AIChat'

export default function GrafoPage() {
  return (
    <div className="k-page">
      <div className="k-page-header">
        <div>
          <h2>Grafo de Conhecimento & Literatura Científica</h2>
          <p className="k-text-muted">Cruzamento inteligente do histórico dos seus pacientes com a literatura médica global</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', height: 'calc(100vh - 180px)', marginTop: '1rem' }}>
        
        {/* Lado Esquerdo: Contexto Local */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="k-card" style={{ flex: 1 }}>
            <div className="k-card-header">
              <Network size={18} className="k-primary" />
              <h3>Visualizador do Grafo Clínico</h3>
            </div>
            <div className="k-card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
              <div style={{ textAlign: 'center' }}>
                <p>Nesta área, será exibida a visualização interativa do seu banco de dados (Pacientes ↔ Medicamentos ↔ Doenças).</p>
                <br/>
                <p><em>Utilize o chat ao lado para extrair conhecimentos do Grafo e da Literatura Científica simultaneamente.</em></p>
              </div>
            </div>
          </div>
        </div>

        {/* Lado Direito: AIChat */}
        <div style={{ flex: 1 }}>
          <div className="k-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div className="k-card-header">
              <Cpu size={18} className="k-primary" />
              <h3>Kairós AI - Agente Especialista</h3>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <AIChat />
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
