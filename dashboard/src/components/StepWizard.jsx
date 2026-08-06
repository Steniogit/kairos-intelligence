/* ============================================================
   StepWizard — Indicador de progresso em etapas horizontais
   Exibe círculos numerados conectados por linhas, com estados
   concluído (✓), atual (pulsante) e futuro (opaco).

   Uso:
     <StepWizard
       steps={[
         { label: 'Dados', icon: User, description: 'Informações pessoais' },
         { label: 'Exame', icon: Stethoscope },
       ]}
       currentStep={1}
       onStepClick={(i) => setStep(i)}
     />
   ============================================================ */

import { Check } from 'lucide-react'
import './StepWizard.css'

/**
 * Determina o estado de um passo em relação ao passo atual.
 * @param {number} index - Índice do passo
 * @param {number} current - Índice do passo atual
 * @returns {'completed' | 'current' | 'future'}
 */
function getStepState(index, current) {
  if (index < current) return 'completed'
  if (index === current) return 'current'
  return 'future'
}

/**
 * @param {Object} props
 * @param {Array<{label: string, icon?: import('lucide-react').LucideIcon, description?: string}>} props.steps
 * @param {number} props.currentStep - Índice do passo atual (0-indexed)
 * @param {(stepIndex: number) => void} [props.onStepClick] - Callback ao clicar em um passo concluído
 */
export default function StepWizard({ steps = [], currentStep = 0, onStepClick }) {
  if (!steps.length) return null

  return (
    <nav className="step-wizard" aria-label="Progresso das etapas">
      {steps.map((step, index) => {
        const state = getStepState(index, currentStep)
        const StepIcon = step.icon
        const isClickable = state === 'completed' && typeof onStepClick === 'function'

        return (
          <div
            key={index}
            className={`step-wizard__item step-wizard__item--${state}`}
          >
            {/* Círculo */}
            <button
              type="button"
              className="step-wizard__circle"
              onClick={isClickable ? () => onStepClick(index) : undefined}
              disabled={!isClickable}
              aria-current={state === 'current' ? 'step' : undefined}
              aria-label={`${state === 'completed' ? 'Concluído' : state === 'current' ? 'Atual' : 'Pendente'}: ${step.label}`}
              title={isClickable ? `Voltar para: ${step.label}` : step.label}
              style={!isClickable ? { pointerEvents: 'none' } : undefined}
            >
              {state === 'completed' ? (
                <Check size={16} strokeWidth={3} />
              ) : StepIcon ? (
                <span className="step-wizard__icon">
                  <StepIcon size={16} />
                </span>
              ) : (
                <span>{index + 1}</span>
              )}
            </button>

            {/* Rótulo e descrição */}
            <div className="step-wizard__content">
              <div className="step-wizard__label">{step.label}</div>
              {step.description && (
                <div className="step-wizard__description">{step.description}</div>
              )}
            </div>
          </div>
        )
      })}
    </nav>
  )
}
