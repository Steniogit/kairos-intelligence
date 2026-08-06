/* ============================================================
   SoapCard — Card expansível para seções SOAP clínicas
   Exibe dados da seção com destaque de atualização (diff),
   suporte a edição inline e renderização dinâmica de tipos.

   Uso:
     <SoapCard
       section="subjective"
       title="Queixa Principal"
       icon={User}
       data={{ queixa: 'Dor de cabeça', duracao: '3 dias' }}
       previousData={{ queixa: 'Dor leve' }}
       editable={false}
       defaultExpanded={true}
     />
   ============================================================ */

import { useState, useEffect, useRef, useCallback } from 'react'
import { ChevronDown, Pill } from 'lucide-react'
import './SoapCard.css'

/** Mapa de rótulos por seção */
const SECTION_LABELS = {
  subjective: 'Subjetivo',
  objective: 'Objetivo',
  assessment: 'Avaliação',
  plan: 'Plano',
}

/**
 * Verifica se um objeto possui campos de medicamento.
 * @param {*} value
 * @returns {boolean}
 */
function isMedication(value) {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value) &&
    ('name' in value || 'dosage' in value || 'frequency' in value)
  )
}

/**
 * Verifica superficialmente se dois valores são diferentes.
 * @param {*} a
 * @param {*} b
 * @returns {boolean}
 */
function hasChanged(a, b) {
  if (a === b) return false
  if (a == null || b == null) return a !== b
  return JSON.stringify(a) !== JSON.stringify(b)
}

/**
 * Renderiza um card de medicamento.
 * @param {{ name?: string, dosage?: string, frequency?: string }} med
 * @param {number} index
 */
function MedicationCard({ med, index }) {
  return (
    <div className="soap-card__med" key={index}>
      <Pill size={14} style={{ color: 'var(--k-accent)', flexShrink: 0 }} />
      <div>
        <div className="soap-card__med-name">{med.name || 'Medicamento'}</div>
        {med.frequency && (
          <div className="soap-card__med-detail">{med.frequency}</div>
        )}
      </div>
      {med.dosage && (
        <span className="soap-card__med-dosage">{med.dosage}</span>
      )}
    </div>
  )
}

/**
 * Renderiza o valor de um campo dependendo do tipo.
 * @param {*} value - Valor do campo
 * @param {boolean} editable - Se o campo é editável
 * @param {string} fieldKey - Chave do campo
 * @param {(key: string, newValue: *) => void} onFieldChange - Callback de edição
 */
function FieldValue({ value, editable, fieldKey, onFieldChange }) {
  // String
  if (typeof value === 'string' || typeof value === 'number') {
    if (editable) {
      return (
        <textarea
          className="soap-card__textarea"
          value={String(value)}
          onChange={(e) => onFieldChange(fieldKey, e.target.value)}
          rows={2}
        />
      )
    }
    return <p className="soap-card__field-value">{String(value)}</p>
  }

  // Array
  if (Array.isArray(value)) {
    // Array de medicamentos
    if (value.length > 0 && isMedication(value[0])) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--k-space-xs)' }}>
          {value.map((med, i) => (
            <MedicationCard med={med} index={i} key={i} />
          ))}
        </div>
      )
    }

    // Array de strings curtas → pills
    const allShort = value.every((v) => typeof v === 'string' && v.length < 40)
    if (allShort) {
      return (
        <div className="soap-card__pills">
          {value.map((item, i) => (
            <span className="soap-card__pill" key={i}>{item}</span>
          ))}
        </div>
      )
    }

    // Array genérico → lista
    return (
      <ul className="soap-card__list">
        {value.map((item, i) => (
          <li className="soap-card__list-item" key={i}>
            {typeof item === 'object' ? JSON.stringify(item) : String(item)}
          </li>
        ))}
      </ul>
    )
  }

  // Objeto único de medicamento
  if (isMedication(value)) {
    return <MedicationCard med={value} index={0} />
  }

  // Objeto genérico → renderizar sub-campos
  if (value !== null && typeof value === 'object') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--k-space-sm)', paddingLeft: 'var(--k-space-sm)' }}>
        {Object.entries(value).map(([subKey, subVal]) => (
          <div className="soap-card__field" key={subKey}>
            <span className="soap-card__field-label">{formatFieldLabel(subKey)}</span>
            <FieldValue
              value={subVal}
              editable={editable}
              fieldKey={`${fieldKey}.${subKey}`}
              onFieldChange={onFieldChange}
            />
          </div>
        ))}
      </div>
    )
  }

  // Null/undefined
  return <p className="soap-card__empty">Sem dados</p>
}

/**
 * Formata uma chave de campo para exibição.
 * Ex: "queixa_principal" → "Queixa principal"
 * @param {string} key
 * @returns {string}
 */
function formatFieldLabel(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/[_-]/g, ' ')
    .replace(/^\w/, (c) => c.toUpperCase())
    .trim()
}

/**
 * @param {Object} props
 * @param {'subjective'|'objective'|'assessment'|'plan'} props.section - Tipo da seção SOAP
 * @param {string} props.title - Título exibido no cabeçalho
 * @param {import('lucide-react').LucideIcon} props.icon - Ícone Lucide
 * @param {Object} props.data - Dados da seção
 * @param {Object} [props.previousData] - Dados anteriores para comparação
 * @param {boolean} [props.editable=false] - Habilitar edição inline
 * @param {(updatedData: Object) => void} [props.onChange] - Callback de alteração
 * @param {boolean} [props.defaultExpanded=true] - Se o card inicia expandido
 */
export default function SoapCard({
  section = 'subjective',
  title,
  icon: Icon,
  data,
  previousData,
  editable = false,
  onChange,
  defaultExpanded = true,
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const [showGlow, setShowGlow] = useState(false)
  const prevDataRef = useRef(previousData)

  const sectionLabel = SECTION_LABELS[section] || section
  const displayTitle = title || sectionLabel

  // Detectar mudança nos dados para disparar animação de glow
  useEffect(() => {
    if (previousData && data && hasChanged(data, previousData)) {
      setShowGlow(true)
      const timer = setTimeout(() => setShowGlow(false), 1500)
      return () => clearTimeout(timer)
    }
  }, [data, previousData])

  /**
   * Lida com alterações em campos individuais.
   * Suporta chaves aninhadas via notação de ponto (ex: "vitals.pressure").
   */
  const handleFieldChange = useCallback(
    (fieldKey, newValue) => {
      if (!onChange || !data) return

      const keys = fieldKey.split('.')
      const updated = JSON.parse(JSON.stringify(data))
      let current = updated

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]]
      }
      current[keys[keys.length - 1]] = newValue

      onChange(updated)
    },
    [data, onChange]
  )

  // Se não há dados
  const isEmpty = !data || (typeof data === 'object' && Object.keys(data).length === 0)

  return (
    <div
      className={[
        'soap-card',
        `soap-card--${section}`,
        showGlow ? 'soap-card--updated' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      style={showGlow ? { '--soap-glow-color': `var(--soap-${section})` } : undefined}
    >
      {/* Cabeçalho */}
      <div
        className="soap-card__header"
        onClick={() => setExpanded((prev) => !prev)}
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        aria-label={`${expanded ? 'Recolher' : 'Expandir'} seção ${displayTitle}`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setExpanded((prev) => !prev)
          }
        }}
      >
        <div className="soap-card__header-left">
          {Icon && (
            <div className="soap-card__icon-wrapper">
              <Icon size={18} />
            </div>
          )}
          <div>
            <div className="soap-card__section-label">{sectionLabel}</div>
            <div className="soap-card__title">{displayTitle}</div>
          </div>
        </div>

        <ChevronDown
          size={18}
          className={`soap-card__chevron ${expanded ? 'soap-card__chevron--open' : ''}`}
        />
      </div>

      {/* Corpo */}
      {expanded && (
        <div className="soap-card__body">
          {isEmpty ? (
            <p className="soap-card__empty">Nenhum dado registrado nesta seção.</p>
          ) : typeof data === 'string' ? (
            /* Dado raiz é uma string simples */
            editable ? (
              <textarea
                className="soap-card__textarea"
                value={data}
                onChange={(e) => onChange?.(e.target.value)}
                rows={3}
              />
            ) : (
              <p className="soap-card__field-value">{data}</p>
            )
          ) : (
            /* Dado raiz é um objeto → iterar campos */
            Object.entries(data).map(([key, value]) => {
              const changed = previousData && hasChanged(value, previousData[key])

              return (
                <div
                  className={`soap-card__field ${changed ? 'soap-card__field--changed' : ''}`}
                  key={key}
                >
                  <span className="soap-card__field-label">{formatFieldLabel(key)}</span>
                  <FieldValue
                    value={value}
                    editable={editable}
                    fieldKey={key}
                    onFieldChange={handleFieldChange}
                  />
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
