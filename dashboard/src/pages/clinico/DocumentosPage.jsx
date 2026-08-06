/* ============================================================
   DocumentosPage — Geração Avulsa de Documentos Médicos
   Permite gerar documentos sem passar por uma consulta completa.
   Fontes de entrada: texto clínico, áudio, ou consulta anterior.
   Layout de 3 colunas: Input → Seleção → Documentos Gerados
   ============================================================ */

import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  Upload,
  Mic,
  Clipboard,
  Printer,
  Copy,
  Download,
  Check,
  AlertTriangle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  Loader2,
} from 'lucide-react'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import {
  submitSoapText,
  submitSoapAudio,
  generateDocument,
  generateBatch,
  listAdemedTemplates,
} from '../../services/clinicalApi'
import './DocumentosPage.css'

// ═══ Constantes ═════════════════════════════════════════════

/** Tipos de documento disponíveis para geração */
const DOC_TYPES = [
  {
    key: 'receituario',
    label: 'Receituário Médico',
    desc: 'Prescrição de medicamentos com posologia',
    icon: Clipboard,
  },
  {
    key: 'atestado',
    label: 'Atestado Médico',
    desc: 'Declaração de atendimento ou afastamento',
    icon: FileText,
  },
  {
    key: 'solicitacao_exames',
    label: 'Solicitação de Exames',
    desc: 'Pedidos laboratoriais e de imagem',
    icon: FileText,
  },
  {
    key: 'encaminhamento',
    label: 'Encaminhamento',
    desc: 'Referência para especialista',
    icon: FileText,
  },
  {
    key: 'relatorio_medico',
    label: 'Relatório Médico',
    desc: 'Relatório clínico detalhado',
    icon: FileText,
  },
]

/** Extensões de áudio aceitas */
const ACCEPTED_AUDIO = '.wav,.mp3,.ogg,.webm'

/** Mínimo de caracteres para processamento de texto */
const MIN_CHARS = 50

// ═══ Helpers ════════════════════════════════════════════════

/**
 * Formata tamanho de arquivo em unidades legíveis.
 * @param {number} bytes - Tamanho em bytes
 * @returns {string} Tamanho formatado (ex: '1.5 MB')
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ═══ Sub-Componente: Renderização de Knowledge Attribution ═

/**
 * KnowledgeAttribution — Exibe badges de atribuição de conhecimento
 * e barra de cobertura do grafo de conhecimento.
 * @param {{ attribution: object }} props
 */
function KnowledgeAttribution({ attribution }) {
  if (!attribution) return null

  const items = attribution.items || attribution.sources || []
  const coverage = attribution.graph_coverage_percent ?? null
  const disclaimer = attribution.disclaimer || null

  return (
    <div className="docs-attribution">
      <div className="docs-attribution-title">Fontes do Conhecimento</div>

      {items.length > 0 && (
        <div className="docs-attribution-badges">
          {items.map((item, idx) => {
            const isVerified = item.source === 'graph_curated'
            return (
              <span
                key={idx}
                className={`docs-attribution-badge ${
                  isVerified
                    ? 'docs-attribution-badge-verified'
                    : 'docs-attribution-badge-general'
                }`}
                title={
                  !isVerified
                    ? 'Gerado a partir de conhecimento geral da IA — requer validação médica'
                    : undefined
                }
              >
                {isVerified ? (
                  <>
                    <Check size={10} />
                    Base Verificada
                  </>
                ) : (
                  <>
                    <AlertTriangle size={10} />
                    Conhecimento Geral
                  </>
                )}
              </span>
            )
          })}
        </div>
      )}

      {coverage !== null && (
        <div className="docs-coverage-bar">
          <div className="docs-coverage-track">
            <div
              className="docs-coverage-fill"
              style={{ width: `${Math.min(coverage, 100)}%` }}
            />
          </div>
          <span className="docs-coverage-label">{coverage}% grafo</span>
        </div>
      )}

      {disclaimer && (
        <div className="docs-attribution-disclaimer">{disclaimer}</div>
      )}
    </div>
  )
}

// ═══ Componente Principal ═══════════════════════════════════

/**
 * DocumentosPage — Página de geração avulsa de documentos médicos.
 * Permite entrada por texto ou áudio, processa via SOAP com IA,
 * e gera múltiplos documentos em lote.
 */
export default function DocumentosPage() {
  const { session } = useClinicalAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  // ─── Estado: Aba de entrada ────────────────────────────────
  const [activeInputTab, setActiveInputTab] = useState('text')

  // ─── Estado: Entrada de texto ──────────────────────────────
  const [clinicalText, setClinicalText] = useState('')

  // ─── Estado: Entrada de áudio ──────────────────────────────
  const [audioFile, setAudioFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  // ─── Estado: Processamento SOAP ────────────────────────────
  const [isProcessing, setIsProcessing] = useState(false)
  const [soapResult, setSoapResult] = useState(null)
  const [soapExpanded, setSoapExpanded] = useState(false)
  const [knowledgeAttribution, setKnowledgeAttribution] = useState(null)
  const [processError, setProcessError] = useState(null)

  // ─── Estado: Seleção de documentos ─────────────────────────
  const [selectedDocTypes, setSelectedDocTypes] = useState(new Set())

  // ─── Estado: Informações do paciente ───────────────────────
  const [patientInfo, setPatientInfo] = useState({
    name: '',
    birthDate: '',
    cpf: '',
  })

  // ─── Estado: Geração de documentos ─────────────────────────
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedDocs, setGeneratedDocs] = useState([])
  const [activeDocTab, setActiveDocTab] = useState(0)
  const [copiedDocIdx, setCopiedDocIdx] = useState(null)
  const [generateError, setGenerateError] = useState(null)

  // ═══ Handlers: Input ══════════════════════════════════════

  /** Valida se a entrada é suficiente para processamento */
  const canProcess =
    (activeInputTab === 'text' && clinicalText.trim().length >= MIN_CHARS) ||
    (activeInputTab === 'audio' && audioFile !== null)

  /** Manipula seleção de arquivo de áudio */
  function handleFileSelect(e) {
    const file = e.target.files?.[0]
    if (file) {
      setAudioFile(file)
      setProcessError(null)
    }
  }

  /** Manipula drag over na dropzone */
  function handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  /** Manipula drag leave na dropzone */
  function handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  /** Manipula drop de arquivo na dropzone */
  function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase()
      if (['wav', 'mp3', 'ogg', 'webm'].includes(ext)) {
        setAudioFile(file)
        setProcessError(null)
      } else {
        setProcessError('Formato de arquivo não suportado. Use .wav, .mp3, .ogg ou .webm.')
      }
    }
  }

  /** Remove o arquivo de áudio selecionado */
  function handleRemoveFile() {
    setAudioFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // ═══ Handler: Processar com IA ════════════════════════════

  /**
   * Envia texto ou áudio para processamento SOAP.
   * O resultado é armazenado em soapResult e usado na geração.
   */
  async function handleProcess() {
    if (!canProcess) return

    setIsProcessing(true)
    setProcessError(null)
    setSoapResult(null)
    setKnowledgeAttribution(null)
    // Limpa documentos anteriores ao reprocessar
    setGeneratedDocs([])
    setSelectedDocTypes(new Set())

    try {
      let result
      if (activeInputTab === 'text') {
        result = await submitSoapText(clinicalText.trim())
      } else if (activeInputTab === 'audio') {
        result = await submitSoapAudio(audioFile)
      }

      // Extrai SOAP — o backend pode retornar em diferentes formatos
      const soap = result?.soap || result?.copilot?.soap || result || {}
      const normalizedSoap = {
        S: soap.subjective || soap.S || soap.s || '',
        O: soap.objective || soap.O || soap.o || '',
        A: soap.assessment || soap.A || soap.a || '',
        P: soap.plan || soap.P || soap.p || '',
      }

      setSoapResult(normalizedSoap)

      // Extrai knowledge_attribution se presente
      const attr =
        result?.knowledge_attribution ||
        result?.copilot?.knowledge_attribution ||
        null
      setKnowledgeAttribution(attr)
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Erro ao processar com IA. Tente novamente.'
      setProcessError(msg)
    } finally {
      setIsProcessing(false)
    }
  }

  // ═══ Handler: Seleção de tipos de documento ═══════════════

  /** Alterna seleção de um tipo de documento */
  function toggleDocType(key) {
    setSelectedDocTypes((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  // ═══ Handler: Atualizar info do paciente ══════════════════

  /** Atualiza um campo de informação do paciente */
  function handlePatientChange(field, value) {
    setPatientInfo((prev) => ({ ...prev, [field]: value }))
  }

  // ═══ Handler: Gerar Documentos ════════════════════════════

  /**
   * Chama generateBatch com o SOAP, tipos selecionados e info do paciente.
   * Armazena os documentos gerados para exibição.
   */
  async function handleGenerateDocs() {
    if (!soapResult || selectedDocTypes.size === 0) return

    setIsGenerating(true)
    setGenerateError(null)
    setGeneratedDocs([])

    try {
      const types = Array.from(selectedDocTypes)
      const pInfo = {
        nome: patientInfo.name || undefined,
        data_nascimento: patientInfo.birthDate || undefined,
        cpf: patientInfo.cpf || undefined,
      }

      const result = await generateBatch(soapResult, types, pInfo)

      // O backend pode retornar array direto ou { documents: [...] }
      const docs = Array.isArray(result) ? result : result?.documents || [result]

      // Normaliza os documentos para exibição
      const normalizedDocs = docs.map((doc, idx) => {
        const typeKey = doc.template_type || doc.type || types[idx] || 'documento'
        const typeMeta = DOC_TYPES.find((t) => t.key === typeKey)
        return {
          type: typeKey,
          title: typeMeta?.label || doc.title || typeKey,
          content: doc.content || doc.text || doc.document || JSON.stringify(doc, null, 2),
          knowledge_attribution: doc.knowledge_attribution || null,
        }
      })

      setGeneratedDocs(normalizedDocs)
      setActiveDocTab(0)
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Erro ao gerar documentos. Tente novamente.'
      setGenerateError(msg)
    } finally {
      setIsGenerating(false)
    }
  }

  // ═══ Handler: Ações nos documentos ════════════════════════

  /** Copia conteúdo do documento para a área de transferência */
  function handleCopyDoc(idx) {
    const doc = generatedDocs[idx]
    if (!doc) return

    navigator.clipboard.writeText(doc.content).then(() => {
      setCopiedDocIdx(idx)
      setTimeout(() => setCopiedDocIdx(null), 2000)
    })
  }

  /** Abre janela de impressão para o documento */
  function handlePrintDoc(idx) {
    const doc = generatedDocs[idx]
    if (!doc) return

    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>${doc.title}</title>
          <style>
            body { font-family: 'Inter', 'Segoe UI', sans-serif; padding: 40px; color: #1a1a1a; }
            h1 { font-size: 1.25rem; border-bottom: 2px solid #333; padding-bottom: 8px; margin-bottom: 24px; }
            pre { white-space: pre-wrap; font-family: inherit; line-height: 1.7; font-size: 0.9rem; }
          </style>
        </head>
        <body>
          <h1>${doc.title}</h1>
          <pre>${doc.content}</pre>
        </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }

  // ═══ Render: Painel de Entrada (Coluna 1) ═════════════════

  function renderInputPanel() {
    const stepState = soapResult ? 'done' : isProcessing ? 'active' : 'active'

    return (
      <div className="docs-panel">
        {/* Header */}
        <div className="docs-panel-header">
          <span className={`docs-panel-step ${stepState === 'done' ? 'docs-panel-step-done' : 'docs-panel-step-active'}`}>
            {soapResult ? <Check size={12} /> : '1'}
          </span>
          <span className="docs-panel-title">Fonte de Dados</span>
        </div>

        {/* Tabs */}
        <div className="docs-input-tabs">
          <button
            className={`docs-input-tab ${activeInputTab === 'text' ? 'docs-input-tab-active' : ''}`}
            onClick={() => setActiveInputTab('text')}
          >
            <FileText size={14} />
            Texto
          </button>
          <button
            className={`docs-input-tab ${activeInputTab === 'audio' ? 'docs-input-tab-active' : ''}`}
            onClick={() => setActiveInputTab('audio')}
          >
            <Mic size={14} />
            Áudio
          </button>
          <button
            className={`docs-input-tab ${activeInputTab === 'previous' ? 'docs-input-tab-active' : ''}`}
            onClick={() => setActiveInputTab('previous')}
          >
            <Clipboard size={14} />
            Consulta
          </button>
        </div>

        {/* Tab Content */}
        <div className="docs-panel-body">
          {activeInputTab === 'text' && renderTextInput()}
          {activeInputTab === 'audio' && renderAudioInput()}
          {activeInputTab === 'previous' && renderPreviousInput()}

          {/* SOAP Preview (aparece após processamento) */}
          {soapResult && renderSoapPreview()}

          {/* Atribuição de conhecimento */}
          {knowledgeAttribution && (
            <KnowledgeAttribution attribution={knowledgeAttribution} />
          )}

          {/* Erro de processamento */}
          {processError && (
            <div className="docs-error-banner">
              <AlertTriangle size={16} />
              <span>{processError}</span>
            </div>
          )}
        </div>

        {/* Footer: Botão de processamento */}
        <div className="docs-panel-footer">
          <button
            className="docs-process-btn"
            disabled={!canProcess || isProcessing}
            onClick={handleProcess}
          >
            {isProcessing ? (
              <>
                <Loader2 size={16} className="k-animate-spin" />
                Processando…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Processar com IA
              </>
            )}
          </button>
        </div>
      </div>
    )
  }

  /** Renderiza a aba de entrada por texto */
  function renderTextInput() {
    const charCount = clinicalText.trim().length
    const isEnough = charCount >= MIN_CHARS

    return (
      <div className="docs-textarea-wrapper">
        <textarea
          className="docs-textarea"
          value={clinicalText}
          onChange={(e) => setClinicalText(e.target.value)}
          placeholder="Cole aqui a transcrição da consulta ou descreva o caso clínico..."
          disabled={isProcessing}
        />
        <div className="docs-char-counter">
          <span className={isEnough ? 'docs-char-counter-ok' : 'docs-char-counter-low'}>
            {charCount} caracteres
          </span>
          {!isEnough && (
            <span>Mínimo: {MIN_CHARS} caracteres</span>
          )}
        </div>
      </div>
    )
  }

  /** Renderiza a aba de upload de áudio */
  function renderAudioInput() {
    return (
      <>
        {!audioFile ? (
          <div
            className={`docs-dropzone ${isDragging ? 'docs-dropzone-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="docs-dropzone-icon">
              <Mic size={24} />
            </div>
            <span className="docs-dropzone-text">
              Arraste o arquivo de áudio aqui
            </span>
            <span className="docs-dropzone-hint">
              ou clique para selecionar — .wav, .mp3, .ogg, .webm
            </span>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_AUDIO}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        ) : (
          <div className="docs-file-info">
            <div className="docs-file-icon">
              <Mic size={18} />
            </div>
            <div className="docs-file-details">
              <div className="docs-file-name">{audioFile.name}</div>
              <div className="docs-file-size">{formatFileSize(audioFile.size)}</div>
            </div>
            <button
              className="docs-file-remove"
              onClick={handleRemoveFile}
              disabled={isProcessing}
            >
              Remover
            </button>
          </div>
        )}
      </>
    )
  }

  /** Renderiza a aba de consulta anterior (futura) */
  function renderPreviousInput() {
    return (
      <div className="docs-coming-soon">
        <div className="docs-coming-soon-icon">
          <Clipboard size={24} />
        </div>
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--k-text-primary)' }}>
          Em breve
        </span>
        <span style={{ fontSize: '0.8125rem' }}>
          Importação de dados de consultas anteriores será adicionada em uma futura atualização.
        </span>
      </div>
    )
  }

  /** Renderiza a preview compacta do resultado SOAP */
  function renderSoapPreview() {
    return (
      <div className="docs-soap-preview">
        <div className="docs-soap-preview-title">
          <Check size={14} />
          SOAP Gerado com Sucesso
        </div>
        <div className="docs-soap-letters">
          {['S', 'O', 'A', 'P'].map((letter) => (
            <span key={letter} className={`docs-soap-letter docs-soap-letter-${letter}`}>
              {letter}
            </span>
          ))}
        </div>
        <button
          className="docs-soap-toggle"
          onClick={() => setSoapExpanded(!soapExpanded)}
        >
          {soapExpanded ? (
            <>
              <ChevronUp size={12} /> Ocultar detalhes
            </>
          ) : (
            <>
              <ChevronDown size={12} /> Ver detalhes
            </>
          )}
        </button>
        {soapExpanded && (
          <div className="docs-soap-detail">
            {['S', 'O', 'A', 'P'].map((letter) => (
              soapResult[letter] ? (
                <div key={letter} style={{ marginBottom: 8 }}>
                  <strong style={{ color: 'var(--k-text-primary)' }}>
                    [{letter}]{' '}
                  </strong>
                  {soapResult[letter]}
                </div>
              ) : null
            ))}
          </div>
        )}
      </div>
    )
  }

  // ═══ Render: Painel de Seleção (Coluna 2) ═════════════════

  function renderSelectionPanel() {
    const isActive = soapResult !== null
    const isDone = generatedDocs.length > 0

    return (
      <div className={`docs-panel ${!isActive ? 'docs-panel-disabled' : ''}`}>
        {/* Header */}
        <div className="docs-panel-header">
          <span
            className={`docs-panel-step ${
              isDone
                ? 'docs-panel-step-done'
                : isActive
                  ? 'docs-panel-step-active'
                  : ''
            }`}
          >
            {isDone ? <Check size={12} /> : '2'}
          </span>
          <span className="docs-panel-title">Seleção de Documentos</span>
        </div>

        <div className="docs-panel-body">
          {isActive ? (
            <>
              {/* Grid de tipos de documento */}
              <div className="docs-type-grid">
                {DOC_TYPES.map((docType) => {
                  const Icon = docType.icon
                  const isSelected = selectedDocTypes.has(docType.key)

                  return (
                    <div
                      key={docType.key}
                      className={`docs-type-card ${isSelected ? 'docs-type-card-selected' : ''}`}
                      onClick={() => toggleDocType(docType.key)}
                    >
                      <div className="docs-type-check">
                        <Check size={10} />
                      </div>
                      <div className="docs-type-icon">
                        <Icon size={18} />
                      </div>
                      <span className="docs-type-label">{docType.label}</span>
                      <span className="docs-type-desc">{docType.desc}</span>
                    </div>
                  )
                })}
              </div>

              {/* Informações do Paciente */}
              <div className="docs-patient-section">
                <span className="docs-patient-title">Dados do Paciente</span>

                <div className="docs-patient-field">
                  <label className="docs-patient-label">Nome do Paciente</label>
                  <input
                    type="text"
                    className="docs-patient-input"
                    placeholder="Nome completo"
                    value={patientInfo.name}
                    onChange={(e) => handlePatientChange('name', e.target.value)}
                  />
                </div>

                <div className="docs-patient-field">
                  <label className="docs-patient-label">Data de Nascimento</label>
                  <input
                    type="date"
                    className="docs-patient-input"
                    value={patientInfo.birthDate}
                    onChange={(e) => handlePatientChange('birthDate', e.target.value)}
                  />
                </div>

                <div className="docs-patient-field">
                  <label className="docs-patient-label">CPF (opcional)</label>
                  <input
                    type="text"
                    className="docs-patient-input"
                    placeholder="000.000.000-00"
                    value={patientInfo.cpf}
                    onChange={(e) => handlePatientChange('cpf', e.target.value)}
                  />
                </div>
              </div>

              {/* Erro de geração */}
              {generateError && (
                <div className="docs-error-banner">
                  <AlertTriangle size={16} />
                  <span>{generateError}</span>
                </div>
              )}
            </>
          ) : (
            <div className="docs-empty-panel">
              <div className="docs-empty-icon">
                <FileText size={24} />
              </div>
              <span className="docs-empty-text">
                Processe um texto ou áudio clínico para selecionar os documentos
              </span>
            </div>
          )}
        </div>

        {/* Footer: Botão de geração */}
        {isActive && (
          <div className="docs-panel-footer">
            <button
              className="docs-generate-btn"
              disabled={selectedDocTypes.size === 0 || isGenerating}
              onClick={handleGenerateDocs}
            >
              {isGenerating ? (
                <>
                  <Loader2 size={16} className="k-animate-spin" />
                  Gerando {selectedDocTypes.size} documento{selectedDocTypes.size > 1 ? 's' : ''}…
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Gerar {selectedDocTypes.size > 0 ? selectedDocTypes.size : ''} Documento{selectedDocTypes.size !== 1 ? 's' : ''}
                </>
              )}
            </button>
          </div>
        )}
      </div>
    )
  }

  // ═══ Render: Painel de Documentos Gerados (Coluna 3) ══════

  function renderOutputPanel() {
    const hasDocuments = generatedDocs.length > 0

    return (
      <div className={`docs-panel ${!hasDocuments ? 'docs-panel-disabled' : ''}`}>
        {/* Header */}
        <div className="docs-panel-header">
          <span
            className={`docs-panel-step ${
              hasDocuments ? 'docs-panel-step-done' : ''
            }`}
          >
            {hasDocuments ? <Check size={12} /> : '3'}
          </span>
          <span className="docs-panel-title">Documentos Gerados</span>
        </div>

        {hasDocuments ? (
          <>
            {/* Tabs de documentos */}
            <div className="docs-output-tabs">
              {generatedDocs.map((doc, idx) => (
                <button
                  key={idx}
                  className={`docs-output-tab ${activeDocTab === idx ? 'docs-output-tab-active' : ''}`}
                  onClick={() => setActiveDocTab(idx)}
                >
                  {doc.title}
                </button>
              ))}
            </div>

            {/* Conteúdo do documento ativo */}
            <div className="docs-panel-body">
              {generatedDocs[activeDocTab] && (
                <div className="docs-document-card">
                  {/* Barra de título */}
                  <div className="docs-document-title-bar">
                    <div className="docs-document-title-icon">
                      <FileText size={14} />
                    </div>
                    <span className="docs-document-title-text">
                      {generatedDocs[activeDocTab].title}
                    </span>
                  </div>

                  {/* Corpo do documento */}
                  <div className="docs-document-body">
                    {generatedDocs[activeDocTab].content}
                  </div>

                  {/* Ações */}
                  <div className="docs-document-actions">
                    <button
                      className={`docs-action-btn ${copiedDocIdx === activeDocTab ? 'docs-action-btn-copied' : ''}`}
                      onClick={() => handleCopyDoc(activeDocTab)}
                    >
                      {copiedDocIdx === activeDocTab ? (
                        <>
                          <Check size={14} />
                          Copiado!
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          Copiar
                        </>
                      )}
                    </button>
                    <button
                      className="docs-action-btn"
                      onClick={() => handlePrintDoc(activeDocTab)}
                    >
                      <Printer size={14} />
                      Imprimir
                    </button>
                  </div>

                  {/* Atribuição por documento */}
                  {generatedDocs[activeDocTab].knowledge_attribution && (
                    <KnowledgeAttribution
                      attribution={generatedDocs[activeDocTab].knowledge_attribution}
                    />
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="docs-panel-body">
            <div className="docs-empty-panel">
              <div className="docs-empty-icon">
                <Sparkles size={24} />
              </div>
              <span className="docs-empty-text">
                Os documentos gerados aparecerão aqui
              </span>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ═══ Render Principal ═════════════════════════════════════

  return (
    <div className="docs-page">
      {/* Header */}
      <div className="docs-header">
        <div className="docs-header-left">
          <button
            className="docs-back-btn"
            onClick={() => navigate('/clinico')}
          >
            <ArrowLeft size={14} />
            Voltar
          </button>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="docs-title-icon">
              <FileText size={18} />
            </span>
            <h1 className="docs-title">Documentos Avulsos</h1>
          </div>
        </div>
        
      </div>

      {/* Body: 3 colunas */}
      <div className="docs-body">
        {renderInputPanel()}
        {renderSelectionPanel()}
        {renderOutputPanel()}
      </div>
    </div>
  )
}
