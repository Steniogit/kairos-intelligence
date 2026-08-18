import { createPortal } from 'react-dom';
/* ============================================================
   ConsultaPage — Página de Consulta Médica com Copiloto IA
   Wizard de 4 etapas:
     0. Verificação pré-voo (preflight)
     1. Consulta ao vivo (transcrição + SOAP em tempo real)
     2. Revisão SOAP (edição manual)
     3. Seleção e geração de documentos médicos
   ============================================================ */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import {Loader2, CheckCircle2, XCircle, Mic, MicOff, Pause, Play, Square, Clock, Wifi, WifiOff, AlertTriangle, Volume2, Lightbulb, FileText, Printer, Copy, Check, RefreshCw, ArrowRight, ArrowLeft, Database, Brain, HardDrive, Server, Shield, Sparkles, MessageSquare, ClipboardList, Stethoscope, FilePlus, FileCheck, Send, ChevronRight, Trash2, Download, User, Search, X, Edit3, UserPlus, Upload, Eye, Plus} from 'lucide-react'
import { useClinicalAuth } from '../../components/ClinicalAuthGate'
import clinicalApi, { runPreflight, getCopilotWSUrl, generateBatch, searchPatients, saveConsultation , uploadPatientFile, listPatientFiles, getFileDownloadUrl, deletePatientFile, createPatient} from '../../services/clinicalApi'
import { useToast } from '../../components/Toast'
import ConfirmModal from '../../components/ConfirmModal'
import './ConsultaPage.css'

// ═══ Constantes ═════════════════════════════════════════════
const PREFLIGHT_CHECKS = [
  { key: 'postgres',         label: 'Prontuários',          icon: Database,   critical: true  },
  { key: 'neo4j',            label: 'Assistente de IA', icon: Server,     critical: false },
  { key: 'chromadb',         label: 'Busca Inteligente',    icon: Brain,      critical: false },
  { key: 'gemini',           label: 'Admed IA',            icon: Sparkles,   critical: true  },
  { key: 'tmpfs',            label: 'Armazenamento Seguro', icon: HardDrive,  critical: false },
  { key: 'write_permission', label: 'Proteção de Dados',    icon: Shield,     critical: false },
]

const HEARTBEAT_INTERVAL = 5000
const AUDIO_LEVEL_INTERVAL = 3000
const STAGGER_DELAY = 300
const MIC_TEST_DURATION = 3000

/** Mapeamento dos tipos de documento para exibição */
const DOC_TYPES = [
  { key: 'receituario',         label: 'Receituário',           desc: 'Prescrição de medicamentos',        icon: ClipboardList },
  { key: 'atestado',            label: 'Atestado Médico',       desc: 'Declaração de atendimento ou afastamento', icon: FileCheck },
  { key: 'solicitacao_exames',  label: 'Solicitação de Exames', desc: 'Pedidos laboratoriais e de imagem', icon: FilePlus },
  { key: 'encaminhamento',      label: 'Encaminhamento',        desc: 'Referência para especialista',      icon: Send },
  { key: 'relatorio_medico',    label: 'Relatório Médico',      desc: 'Relatório clínico detalhado',       icon: FileText },
]

/** Cores para as letras S-O-A-P */
const SOAP_COLORS = {
  S: '#10b981',
  O: '#3b82f6',
  A: '#f59e0b',
  P: '#8b5cf6',
}

const SOAP_LABELS = {
  S: 'Subjetivo',
  O: 'Objetivo',
  A: 'Avaliação',
  P: 'Plano',
}

// ═══ Helpers ════════════════════════════════════════════════

/** Formata segundos em MM:SS */
function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

/** Formata timestamp da transcrição */
function formatTimestamp(seconds) {
  return formatTime(seconds)
}

/** Retorna classe CSS de confiança */
function confidenceClass(value) {
  if (value >= 0.8) return 'high'
  if (value >= 0.5) return 'medium'
  return 'low'
}

// ═══ Sub-Componente: AudioMeter inline simplificado ════════
// Usado quando o componente AudioMeter externo não está disponível
function InlineAudioMeter({ level = 0, size = 'small' }) {
  const barCount = size === 'small' ? 5 : 8
  const barH = size === 'small' ? 16 : 24

  return (
    <div className="consulta-audio-mini" style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: barH }}>
      {Array.from({ length: barCount }).map((_, i) => {
        const threshold = (i + 1) / barCount
        const active = level >= threshold
        return (
          <div
            key={i}
            style={{
              width: size === 'small' ? 3 : 4,
              height: `${20 + (i * (80 / barCount))}%`,
              borderRadius: 2,
              background: active
                ? (i / barCount > 0.7 ? 'var(--k-danger)' : 'var(--k-success)')
                : 'var(--k-bg-elevated)',
              transition: 'background 100ms',
            }}
          />
        )
      })}
    </div>
  )
}

// ═══ Sub-Componente: SoapMiniCard ═══════════════════════════
// Versão inline caso SoapCard não exista como componente separado
function SoapMiniCard({ letter, content, updating }) {
  const color = SOAP_COLORS[letter] || 'var(--k-accent)'
  const label = SOAP_LABELS[letter] || letter

  return (
    <div
      className="consulta-review-card"
      style={{ borderColor: updating ? color : undefined }}
    >
      <div className="consulta-review-card-header">
        <div
          className="consulta-review-card-letter"
          style={{ background: color }}
        >
          {letter}
        </div>
        <span className="consulta-review-card-label">{label}</span>
        {updating && <Loader2 size={12} className="k-animate-spin" style={{ color, marginLeft: 'auto' }} />}
      </div>
      <div style={{ fontSize: '0.8125rem', color: 'var(--k-text-secondary)', lineHeight: 1.6, minHeight: 40 }}>
        {content || <span style={{ color: 'var(--k-text-muted)', fontStyle: 'italic' }}>Aguardando dados…</span>}
      </div>
    </div>
  )
}

// ═══ Componente Principal ═══════════════════════════════════

/**
 * ConsultaPage — Página principal de consulta médica com copiloto IA.
 * Gerencia um wizard de 4 etapas, WebSocket, Web Speech API e geração
 * automática de documentos médicos.
 */
export default function ConsultaPage() {
  const formatDateBR = (dateStr) => {
    if (!dateStr) return '';
    if (dateStr.includes('-')) return dateStr.split('-').reverse().join('/');
    return dateStr;
  };

  const { session } = useClinicalAuth()
  const { addToast } = useToast()

  // ─── Estado do wizard ────────────────────────────────────
  const [currentStep, setCurrentStep] = useState(0)

  // ─── Step 0: Preflight ───────────────────────────────────
  const [preflightResult, setPreflightResult] = useState(null)
  const [preflightLoading, setPreflightLoading] = useState(false)
  const [checksVisible, setChecksVisible] = useState([])
  const [micTesting, setMicTesting] = useState(false)
  const [micLevel, setMicLevel] = useState(0)
  const micStreamRef = useRef(null)
  const micAnalyserRef = useRef(null)
  const micAnimRef = useRef(null)

  // ─── Step 1: Live Consultation ───────────────────────────
  const [transcript, setTranscript] = useState([])
  const [interimText, setInterimText] = useState('')
  const [soapData, setSoapData] = useState({ S: '', O: '', A: '', P: '' })
  const [soapUpdating, setSoapUpdating] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [sessionId, setSessionId] = useState(null)
  const [silenceAlert, setSilenceAlert] = useState(false)
  const [lowAudioAlert, setLowAudioAlert] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [showEndModal, setShowEndModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [wsDisconnected, setWsDisconnected] = useState(false)

  // ─── Step 2: SOAP Review ─────────────────────────────────
  const [editedSoap, setEditedSoap] = useState({ S: '', O: '', A: '', P: '' })

  // ─── Step 3: Documents ───────────────────────────────────
  const [selectedDocs, setSelectedDocs] = useState([])
  const [generatingDocs, setGeneratingDocs] = useState(false)
  const [generatedDocs, setGeneratedDocs] = useState([])
  const [copiedDoc, setCopiedDoc] = useState(null)

  // ─── Paciente ─────────────────────────────────────────────
  const [selectedPatient, setSelectedPatient] = useState(null)
  const [patientSearch, setPatientSearch] = useState('')
  const [patientResults, setPatientResults] = useState([])
  const [patientSearching, setPatientSearching] = useState(false)
  const [showNewPatientForm, setShowNewPatientForm] = useState(false)
  const [newPatientName, setNewPatientName] = useState('')
  const [newPatientCpf, setNewPatientCpf] = useState('')
  const [newPatientBirth, setNewPatientBirth] = useState('')
  const [savingPatient, setSavingPatient] = useState(false)
  const [patientFiles, setPatientFiles] = useState([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [uploadFileType, setUploadFileType] = useState('outro')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploading, setUploading] = useState(false)

  // ─── Preview de Documento ─────────────────────────────────
  const [previewDoc, setPreviewDoc] = useState(null) // {index, type, title}
  const [previewContent, setPreviewContent] = useState('')

  // ─── Diarização ───────────────────────────────────
  const [diarizedSegments, setDiarizedSegments] = useState([])
  const [isDiarizing, setIsDiarizing] = useState(false)

  // ─── Refs ────────────────────────────────────────────────
  const wsRef = useRef(null)
  const recognitionRef = useRef(null)
  const timerRef = useRef(null)
  const heartbeatRef = useRef(null)
  const audioLevelRef = useRef(null)
  const transcriptEndRef = useRef(null)
  const startTimeRef = useRef(null)
  const isRecordingRef = useRef(false)
  const isPausedRef = useRef(false)
  const patientSearchTimer = useRef(null)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunkIntervalRef = useRef(null)

  // ═══ Busca de Paciente ═════════════════════════════════════

  const handlePatientSearch = useCallback((value) => {
    setPatientSearch(value)
    if (patientSearchTimer.current) clearTimeout(patientSearchTimer.current)
    if (value.length < 2) {
      setPatientResults([])
      return
    }
    setPatientSearching(true)
    patientSearchTimer.current = setTimeout(async () => {
      try {
        const results = await searchPatients(value)
        setPatientResults(results)
      } catch {
        setPatientResults([])
      } finally {
        setPatientSearching(false)
      }
    }, 400)
  }, [])

    // ═══ Cadastro de Paciente ═══════════════════════════════
  const formatCpf = (value) => {
    const digits = value.replace(/\D/g, '').slice(0, 11)
    if (digits.length <= 3) return digits
    if (digits.length <= 6) return `${digits.slice(0,3)}.${digits.slice(3)}`
    if (digits.length <= 9) return `${digits.slice(0,3)}.${digits.slice(3,6)}.${digits.slice(6)}`
    return `${digits.slice(0,3)}.${digits.slice(3,6)}.${digits.slice(6,9)}-${digits.slice(9)}`
  }

  const handleCreatePatient = async () => {
    if (!newPatientName.trim() || !newPatientCpf.trim() || !newPatientBirth.trim()) {
      addToast('Preencha todos os campos obrigatórios.', 'warning')
      return
    }
    setSavingPatient(true)
    try {
      const patient = await createPatient({
        name: newPatientName.trim(),
        cpf: newPatientCpf.trim(),
        birth_date: newPatientBirth,
        sex: 'N',
      })
      setSelectedPatient(patient)
      setShowNewPatientForm(false)
      setNewPatientName('')
      setNewPatientCpf('')
      setNewPatientBirth('')
      setPatientSearch('')
      setPatientResults([])
      addToast(`Paciente ${patient.name} cadastrado com sucesso!`, 'success')
      loadPatientFiles(patient.id)
    } catch (err) {
      addToast('Erro ao cadastrar paciente: ' + (err?.response?.data?.detail || err.message), 'error')
    } finally {
      setSavingPatient(false)
    }
  }

  // ═══ Arquivos do Paciente ═══════════════════════════════
  const loadPatientFiles = async (patientId) => {
    if (!patientId) return
    setLoadingFiles(true)
    try {
      const files = await listPatientFiles(patientId)
      setPatientFiles(files)
    } catch (err) {
      setPatientFiles([])
    } finally {
      setLoadingFiles(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !selectedPatient) return
    setUploading(true)
    try {
      await uploadPatientFile(selectedPatient.id, file, uploadFileType, uploadDescription)
      addToast('Arquivo anexado com sucesso!', 'success')
      setShowUploadForm(false)
      setUploadFileType('outro')
      setUploadDescription('')
      loadPatientFiles(selectedPatient.id)
    } catch (err) {
      addToast('Erro ao enviar arquivo: ' + (err?.response?.data?.detail || err.message), 'error')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleViewFile = async (fileId) => {
    try {
      const { url } = await getFileDownloadUrl(fileId)
      window.open(url, '_blank')
    } catch (err) {
      addToast('Erro ao abrir arquivo.', 'error')
    }
  }

  const handleDeleteFile = async (fileId) => {
    if (!confirm('Deseja realmente excluir este arquivo?')) return
    try {
      await deletePatientFile(fileId)
      addToast('Arquivo removido.', 'success')
      loadPatientFiles(selectedPatient.id)
    } catch (err) {
      addToast('Erro ao remover arquivo.', 'error')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const fileTypeLabels = {
    exame_lab: 'Exame Laboratorial',
    exame_imagem: 'Exame de Imagem',
    laudo: 'Laudo Médico',
    receita: 'Receita',
    outro: 'Outro',
  }

const handleSelectPatient = useCallback((patient) => {
    setSelectedPatient(patient)
    setPatientSearch('')
    setPatientResults([])
    loadPatientFiles(patient.id)
  }, [])

  // ═══ Preview e PDF de Documento ════════════════════════════

  const handlePreviewDoc = useCallback((docIndex) => {
    const doc = generatedDocs[docIndex]
    const content = doc?.content || doc?.text || JSON.stringify(doc, null, 2)
    const title = DOC_TYPES.find(d => d.key === doc.type)?.label || doc.type || `Documento ${docIndex + 1}`
    setPreviewDoc({ index: docIndex, type: doc.type, title })
    setPreviewContent(content)
  }, [generatedDocs])

  const handleDownloadPdf = useCallback(async () => {
    if (!previewDoc) return
    try {
      // Dynamic import de jsPDF (tree-shaking)
      const { jsPDF } = await import('jspdf')
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pageWidth = pdf.internal.pageSize.getWidth()
      const margin = 20
      const maxWidth = pageWidth - margin * 2
      let y = 20

      // Cabeçalho
      pdf.setFontSize(16)
      pdf.setFont('helvetica', 'bold')
      pdf.text(previewDoc.title, margin, y)
      y += 10

      // Dados do paciente (se selecionado)
      if (selectedPatient) {
        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'normal')
        pdf.text(`Paciente: ${selectedPatient.name}`, margin, y)
        y += 5
        if (selectedPatient.cpf) { pdf.text(`CPF: ${selectedPatient.cpf}`, margin, y); y += 5 }
        if (selectedPatient.birth_date) { pdf.text(`Nasc.: ${formatDateBR(selectedPatient.birth_date)}`, margin, y); y += 5 }
        if (selectedPatient.sex && selectedPatient.sex !== 'N') {
          pdf.text(`Sexo: ${selectedPatient.sex === 'M' ? 'Masculino' : 'Feminino'}`, margin, y)
          y += 5
        }
      }

      // Data
      pdf.setFontSize(9)
      pdf.text(`Data: ${new Date().toLocaleDateString('pt-BR')}`, margin, y)
      y += 10

      // Linha separadora
      pdf.setDrawColor(200)
      pdf.line(margin, y, pageWidth - margin, y)
      y += 8

      // Conteúdo do documento
      pdf.setFontSize(11)
      pdf.setFont('helvetica', 'normal')
      const lines = pdf.splitTextToSize(previewContent, maxWidth)
      for (const line of lines) {
        if (y > 270) { pdf.addPage(); y = 20 }
        pdf.text(line, margin, y)
        y += 5.5
      }

      // Rodapé
      y = Math.max(y + 15, 260)
      if (y > 270) { pdf.addPage(); y = 260 }
      pdf.setDrawColor(180)
      pdf.line(margin + 30, y, pageWidth - margin - 30, y)
      y += 5
      pdf.setFontSize(9)
      pdf.text(session?.doctorName || 'Profissional de Saúde', pageWidth / 2, y, { align: 'center' })
      y += 4
      if (session?.doctorCrm) {
        pdf.text(`CRM: ${session.doctorCrm}`, pageWidth / 2, y, { align: 'center' })
      }

      pdf.save(`${previewDoc.type || 'documento'}_${new Date().toISOString().slice(0,10)}.pdf`)
      addToast('PDF baixado com sucesso!', 'success')
    } catch (err) {
      console.error('Erro ao gerar PDF:', err)
      addToast('Erro ao gerar PDF. Tente novamente.', 'error')
    }
  }, [previewDoc, previewContent, selectedPatient, session, addToast])

  // ═══ Auto-save da Consulta ═════════════════════════════════

  const handleAutoSave = useCallback(async () => {
    try {
      await saveConsultation({
        patient_id: selectedPatient?.id || null,
        doctor_name: session?.doctorName || '',
        doctor_crm: session?.doctorCrm || '',
        transcript: transcript.map(l => `[${formatTime(l.time)}] ${l.text}`).join('\n'),
        soap_json: editedSoap || soapData,
        documents_json: generatedDocs,
        duration_seconds: elapsedTime,
      })
      addToast('Consulta salva no histórico!', 'success')
    } catch (err) {
      console.error('Erro ao salvar consulta:', err)
      addToast('Erro ao salvar consulta no histórico.', 'warning')
    }
  }, [selectedPatient, session, transcript, editedSoap, soapData, generatedDocs, elapsedTime, addToast])

  // ═══ Step 0: Preflight ═══════════════════════════════════

  const doRunPreflight = useCallback(async () => {
    setPreflightLoading(true)
    setPreflightResult(null)
    setChecksVisible([])

    try {
      const result = await runPreflight()
      setPreflightResult(result)

      // Animação escalonada: revela cada check a cada 300ms
      const checks = result?.checks || result || {}
      PREFLIGHT_CHECKS.forEach((check, i) => {
        setTimeout(() => {
          setChecksVisible(prev => [...prev, check.key])
        }, STAGGER_DELAY * (i + 1))
      })
    } catch (err) {
      setPreflightResult({ error: true, message: err.message || 'Falha na verificação' })
      // Mesmo com erro, mostra os cards como falha
      PREFLIGHT_CHECKS.forEach((check, i) => {
        setTimeout(() => {
          setChecksVisible(prev => [...prev, check.key])
        }, STAGGER_DELAY * (i + 1))
      })
    } finally {
      setPreflightLoading(false)
    }
  }, [])

  // Roda o preflight ao montar
  useEffect(() => {
    doRunPreflight()
  }, [doRunPreflight])

  /** Verifica se um check específico passou */
  const checkPassed = useCallback((key) => {
    if (!preflightResult || preflightResult.error) return false
    const checks = preflightResult.checks || preflightResult
    const val = checks[key]
    if (typeof val === 'boolean') return val
    if (typeof val === 'object' && val !== null) return val.ok || val.status === 'ok' || val.connected === true
    return !!val
  }, [preflightResult])

  /** Checks críticos passaram? (gemini + postgres) */
  const criticalsPassed = useMemo(() => {
    if (!preflightResult || preflightResult.error) return false
    return PREFLIGHT_CHECKS
      .filter(c => c.critical)
      .every(c => checkPassed(c.key))
  }, [preflightResult, checkPassed])

  // ─── Teste de Microfone ──────────────────────────────────

  const startMicTest = useCallback(async () => {
    try {
      setMicTesting(true)
      setMicLevel(0)

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micStreamRef.current = stream

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      micAnalyserRef.current = analyser

      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      function readLevel() {
        analyser.getByteFrequencyData(dataArray)
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        setMicLevel(Math.min(avg / 128, 1))
        micAnimRef.current = requestAnimationFrame(readLevel)
      }
      readLevel()

      // Desliga após MIC_TEST_DURATION
      setTimeout(() => {
        cancelAnimationFrame(micAnimRef.current)
        stream.getTracks().forEach(t => t.stop())
        audioCtx.close()
        micStreamRef.current = null
        micAnalyserRef.current = null
        setMicTesting(false)
      }, MIC_TEST_DURATION)
    } catch (err) {
      addToast('Não foi possível acessar o microfone. Verifique as permissões.', 'error')
      setMicTesting(false)
    }
  }, [addToast])

  // ═══ Step 1: WebSocket ═══════════════════════════════════

  const connectWebSocket = useCallback((reconnectSessionId = null) => {
    const url = getCopilotWSUrl(reconnectSessionId)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      setWsDisconnected(false)

      if (reconnectSessionId) {
        ws.send(JSON.stringify({ type: 'reconnect', session_id: reconnectSessionId }))
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        switch (msg.type) {
          case 'connected':
            setSessionId(msg.session_id)
            break

          case 'reconnected':
            setSessionId(msg.session_id || reconnectSessionId)
            addToast('Reconectado à sessão do copiloto.', 'success')
            // Se veio dados SOAP anteriores, restaura
            if (msg.state?.last_soap?.copilot) {
              const copilot = msg.state.last_soap.copilot
              const sp = copilot.soap_partial || {}
              setSoapData({
                S: typeof sp.subjective === 'object' ? JSON.stringify(sp.subjective) : (sp.subjective || ''),
                O: typeof sp.objective === 'object' ? JSON.stringify(sp.objective) : (sp.objective || ''),
                A: typeof sp.assessment === 'object' ? JSON.stringify(sp.assessment) : (sp.assessment || ''),
                P: typeof sp.plan === 'object' ? JSON.stringify(sp.plan) : (sp.plan || ''),
              })
              if (copilot.suggested_questions) {
                setSuggestions(copilot.suggested_questions)
              }
              if (copilot.alerts?.length) {
                copilot.alerts.forEach(a => addToast(`⚠️ ${a.message}`, a.severity === 'high' ? 'error' : 'warning'))
              }
            }
            break

          case 'ack':
            // Confirmação de recebimento — sem ação visual
            break

          case 'soap_update':
          case 'final_soap': {
            setSoapUpdating(true)
            // Backend envia: {type, data: {status, copilot: {soap_partial, alerts, ...}}}
            const copilot = msg.data?.copilot || msg.copilot || {}
            const sp = copilot.soap_partial || {}
            // Formatar dados SOAP — aceitar update parcial (merge)
              const fmt = (v) => {
                if (!v) return ''
                if (typeof v === 'string') return v
                // Formatar objetos como texto legível, ignorando valores vazios
                return Object.entries(v).map(([k, val]) => {
                  if (val === null || val === undefined || val === '') return null
                  if (Array.isArray(val) && val.length === 0) return null
                  if (typeof val === 'object' && !Array.isArray(val) && Object.keys(val).length === 0) return null
                  // Formatar label legível
                  const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                  if (Array.isArray(val)) return `${label}: ${val.join(', ')}`
                  if (typeof val === 'object' && val) {
                    const inner = Object.entries(val)
                      .filter(([, v2]) => v2 !== null && v2 !== '' && !(Array.isArray(v2) && v2.length === 0))
                      .map(([k2, v2]) => `${k2}: ${v2}`)
                      .join(', ')
                    return inner ? `${label}: ${inner}` : null
                  }
                  return `${label}: ${val}`
                }).filter(Boolean).join('\n')
              }
              // Merge: preservar dados anteriores se o novo for vazio
              setSoapData(prev => ({
                S: fmt(sp.subjective) || prev.S,
                O: fmt(sp.objective) || prev.O,
                A: fmt(sp.assessment) || prev.A,
                P: fmt(sp.plan) || prev.P,
              }))
            if (copilot.suggested_questions?.length) {
              setSuggestions(copilot.suggested_questions)
            }
            if (copilot.alerts?.length) {
              copilot.alerts.forEach(a => addToast(`⚠️ ${a.message}`, a.severity === 'high' ? 'error' : 'warning'))
            }
            setTimeout(() => setSoapUpdating(false), 600)
            break
          }

          case 'silence_alert':
            setSilenceAlert(true)
            setTimeout(() => setSilenceAlert(false), 10000)
            break

          case 'low_audio_alert':
            setLowAudioAlert(true)
            setTimeout(() => setLowAudioAlert(false), 8000)
            break

          case 'session_ended':
            addToast('Sessão finalizada pelo servidor.', 'info')
            break

          case 'diarizing':
            setIsDiarizing(true)
            addToast('Processando identificação de falantes...', 'info')
            break

          case 'diarization_result': {
            setIsDiarizing(false)
            const diarData = msg.data || {}
            if (diarData.diarized_segments?.length) {
              setDiarizedSegments(diarData.diarized_segments)
              addToast(`Diarização concluída: ${diarData.segment_count} segmentos identificados`, 'success')
            }
            break
          }

          case 'diarization_error':
            setIsDiarizing(false)
            addToast('Erro na identificação de falantes.', 'warning')
            break

          default:
            break
        }
      } catch {
        // Mensagem não-JSON — ignora
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
      setWsDisconnected(true)
    }

    ws.onerror = () => {
      setWsConnected(false)
      setWsDisconnected(true)
    }

    return ws
  }, [addToast])

  /** Envia mensagem via WebSocket (com verificação) */
  const wsSend = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  // ═══ Step 1: Web Speech API ══════════════════════════════

  const startSpeechRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      addToast('Seu navegador não suporta reconhecimento de voz. Use Chrome.', 'error')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'pt-BR'
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          const text = result[0].transcript.trim()
          if (text) {
            const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000)
            setTranscript(prev => [...prev, { text, time: elapsed }])
            wsSend({ type: 'text', text })
            setSilenceAlert(false)
          }
        } else {
          interim += result[0].transcript
        }
      }
      setInterimText(interim)
    }

    recognition.onerror = (event) => {
      if (event.error === 'no-speech') {
        // Silêncio — normal
        return
      }
      if (event.error === 'aborted') return
      console.warn('SpeechRecognition error:', event.error)
      if (event.error === 'not-allowed') {
        addToast('Microfone bloqueado pelo navegador. Permita o acesso nas configurações do site.', 'error')
      } else if (event.error === 'network') {
        addToast('Erro de rede no reconhecimento de voz. Verifique sua conexão.', 'error')
      }
    }

    // Auto-restart em caso de parada inesperada
    recognition.onend = () => {
      // Usar refs para evitar stale closure
      if (isRecordingRef.current && !isPausedRef.current && recognitionRef.current) {
        try {
          recognition.start()
        } catch {
          // Pode falhar se já estiver rodando
        }
      }
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
      setIsRecording(true)
      isRecordingRef.current = true
      setIsPaused(false)
      isPausedRef.current = false
    } catch (err) {
      console.error('Falha ao iniciar reconhecimento de voz:', err)
      addToast(`Erro ao iniciar microfone: ${err.message}. Verifique as permissões do navegador.`, 'error')
      recognitionRef.current = null
    }
  }, [addToast, wsSend])

  // ─── Iniciar consulta (Step 0 → Step 1) ──────────────────

  const handleStartConsulta = useCallback(() => {
    setCurrentStep(1)
    startTimeRef.current = Date.now()

    // Conecta WebSocket
    connectWebSocket()

    // Inicia reconhecimento de voz
    setTimeout(() => startSpeechRecognition(), 500)

    // Inicia captura de áudio para diarização (MediaRecorder)
    setTimeout(async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        mediaStreamRef.current = stream
        const recorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus',
        })
        mediaRecorderRef.current = recorder

        recorder.ondataavailable = async (e) => {
          if (e.data.size > 0 && !isPausedRef.current) {
            try {
              const buffer = await e.data.arrayBuffer()
              const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)))
              wsSend({ type: 'audio_chunk', data: base64 })
            } catch { /* encoding error — skip chunk */ }
          }
        }

        // Capturar chunks a cada 3 segundos
        recorder.start(3000)
      } catch (err) {
        console.warn('MediaRecorder indisponível para diarização:', err.message)
      }
    }, 800)

    // Timer de tempo decorrido
    timerRef.current = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)

    // Heartbeat a cada 5s
    heartbeatRef.current = setInterval(() => {
      wsSend({ type: 'heartbeat' })
    }, HEARTBEAT_INTERVAL)

    // Envio de nível de áudio a cada 3s
    audioLevelRef.current = setInterval(() => {
      wsSend({ type: 'audio_level', level: audioLevel })
    }, AUDIO_LEVEL_INTERVAL)
  }, [connectWebSocket, startSpeechRecognition, wsSend, audioLevel])

  // ─── Pausar / Retomar ────────────────────────────────────

  const handlePauseResume = useCallback(() => {
    if (isPaused) {
      // Retomar
      if (recognitionRef.current) {
        try { recognitionRef.current.start() } catch { /* já rodando */ }
      }
      // Retomar timer
      startTimeRef.current = Date.now() - (elapsedTime * 1000)
      timerRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 1000)
      // Retomar heartbeat
      heartbeatRef.current = setInterval(() => {
        wsSend({ type: 'heartbeat' })
      }, HEARTBEAT_INTERVAL)
      setIsPaused(false)
      isPausedRef.current = false
      // Retomar MediaRecorder
      if (mediaRecorderRef.current?.state === 'paused') {
        try { mediaRecorderRef.current.resume() } catch { /* ok */ }
      }
    } else {
      // Pausar
      if (recognitionRef.current) {
        try { recognitionRef.current.stop() } catch { /* ok */ }
      }
      // Pausar timer
      clearInterval(timerRef.current)
      // Pausar heartbeat
      clearInterval(heartbeatRef.current)
      setIsPaused(true)
      isPausedRef.current = true
      // Pausar MediaRecorder
      if (mediaRecorderRef.current?.state === 'recording') {
        try { mediaRecorderRef.current.pause() } catch { /* ok */ }
      }
    }
  }, [isPaused, elapsedTime, wsSend])

  // ─── Finalizar Consulta ──────────────────────────────────

  const handleEndConsulta = useCallback(async () => {
    // Parar reconhecimento
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch { /* ok */ }
      recognitionRef.current = null
    }
    setIsRecording(false)
    isRecordingRef.current = false

    // Parar timers
    clearInterval(timerRef.current)
    clearInterval(heartbeatRef.current)
    clearInterval(audioLevelRef.current)

    // Se WS está conectado, enviar mensagem de encerramento e esperar o final_soap
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Instalar handler temporário para capturar final_soap antes de fechar
      const waitForFinalSoap = new Promise((resolve) => {
        const origHandler = wsRef.current.onmessage
        const timeout = setTimeout(() => resolve(null), 15000)
        wsRef.current.onmessage = (event) => {
          if (origHandler) origHandler(event)
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'final_soap' || data.type === 'session_ended') {
              clearTimeout(timeout)
              resolve(data)
            }
          } catch { /* ok */ }
        }
      })
      wsSend({ type: 'end' })
      await waitForFinalSoap
    } else if (transcript.length > 0) {
      // FALLBACK: WS desconectado — gerar SOAP via HTTP
      addToast('Gerando SOAP via API (copiloto desconectado)...', 'info')
      try {
        const fullText = transcript.map(l => l.text).join(' ')
        const response = await clinicalApi.post('/api/v1/clinical/soap/generate', {
          transcript: fullText,
          format: 'structured'
        })
        if (response.data?.soap) {
          const s = response.data.soap
          const fmt = (v) => {
            if (!v) return ''
            if (typeof v === 'string') return v
            return Object.entries(v).map(([k, val]) => {
              if (Array.isArray(val)) return `${k}: ${val.join(', ')}`
              return val ? `${k}: ${val}` : ''
            }).filter(Boolean).join('\n')
          }
          setSoapData({
            S: fmt(s.subjective || s.S || ''),
            O: fmt(s.objective || s.O || ''),
            A: fmt(s.assessment || s.A || ''),
            P: fmt(s.plan || s.P || ''),
          })
        }
      } catch (err) {
        console.error('Fallback SOAP failed:', err)
        addToast('Não foi possível gerar SOAP automaticamente.', 'error')
      }
    }

    // Parar gravação de áudio (MediaRecorder para diarização)
    if (mediaRecorderRef.current) {
      try { mediaRecorderRef.current.stop() } catch { /* ok */ }
      mediaRecorderRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop())
      mediaStreamRef.current = null
    }

    // Fechar WS
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Auto-save no histórico
    handleAutoSave()

    // Preparar revisão
    setEditedSoap({ ...soapData })
    setShowEndModal(false)
    setCurrentStep(2)
  }, [wsSend, soapData, transcript, addToast, handleAutoSave])

  // ─── Cancelar Consulta ───────────────────────────────────

  const handleCancelConsulta = useCallback(() => {
    // Parar reconhecimento
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch { /* ok */ }
      recognitionRef.current = null
    }
    setIsRecording(false)

    // Parar timers
    clearInterval(timerRef.current)
    clearInterval(heartbeatRef.current)
    clearInterval(audioLevelRef.current)
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(t => t.stop())
      micStreamRef.current = null
    }

    // Fechar WS
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Reseta o estado
    setWsConnected(false)
    setTranscript([])
    setInterimText('')
    setSoapData({ S: '', O: '', A: '', P: '' })
    setSuggestions([])
    setSessionId(null)
    setElapsedTime(0)
    setSilenceAlert(false)
    setLowAudioAlert(false)
    setShowCancelModal(false)
    setCurrentStep(0)

    addToast('Atendimento cancelado e dados descartados.', 'info')
  }, [addToast])

  // ─── Reconectar WebSocket ────────────────────────────────

  const handleReconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connectWebSocket(sessionId)
  }, [connectWebSocket, sessionId])

  // ─── Scroll automático do transcript ─────────────────────
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [transcript, interimText])

  // ═══ Step 2: Review ══════════════════════════════════════

  const handleSoapEdit = useCallback((letter, value) => {
    setEditedSoap(prev => ({ ...prev, [letter]: value }))
  }, [])

  const handleAdvanceToDocuments = useCallback(() => {
    setCurrentStep(3)
  }, [])

  // ═══ Step 3: Documents ═══════════════════════════════════

  const toggleDocType = useCallback((key) => {
    setSelectedDocs(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }, [])

  const handleGenerateBatch = useCallback(async () => {
    if (selectedDocs.length === 0) {
      addToast('Selecione ao menos um tipo de documento.', 'warning')
      return
    }

    setGeneratingDocs(true)
    try {
      const result = await generateBatch(editedSoap, selectedDocs)
      const docs = Array.isArray(result) ? result : (result?.documents || [result])
      setGeneratedDocs(docs)
      addToast(`${docs.length} documento(s) gerado(s) com sucesso!`, 'success')
    } catch (err) {
      addToast('Erro ao gerar documentos. Tente novamente.', 'error')
    } finally {
      setGeneratingDocs(false)
    }
  }, [selectedDocs, editedSoap, addToast])

  const handleCopyDoc = useCallback((docIndex) => {
    const doc = generatedDocs[docIndex]
    const text = doc?.content || doc?.text || JSON.stringify(doc, null, 2)
    navigator.clipboard.writeText(text).then(() => {
      setCopiedDoc(docIndex)
      setTimeout(() => setCopiedDoc(null), 2000)
      addToast('Documento copiado!', 'success')
    })
  }, [generatedDocs, addToast])

  const handlePrintDoc = useCallback((docIndex) => {
    const doc = generatedDocs[docIndex]
    const text = doc?.content || doc?.text || JSON.stringify(doc, null, 2)
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(`<pre style="font-family: 'Inter', sans-serif; padding: 40px; white-space: pre-wrap;">${text}</pre>`)
      win.document.close()
      win.print()
    }
  }, [generatedDocs])

  // ═══ Cleanup ═════════════════════════════════════════════
  useEffect(() => {
    return () => {
      // Limpa tudo ao desmontar
      if (recognitionRef.current) {
        try { recognitionRef.current.stop() } catch { /* ok */ }
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      clearInterval(timerRef.current)
      clearInterval(heartbeatRef.current)
      clearInterval(audioLevelRef.current)
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach(t => t.stop())
      }
      cancelAnimationFrame(micAnimRef.current)
    }
  }, [])

  // ═══ Renders por Step ════════════════════════════════════

  // ─── Step 0: Pre-Flight ──────────────────────────────────

  function renderPreflight() {
    const hasError = preflightResult?.error
    const allVisible = checksVisible.length >= PREFLIGHT_CHECKS.length

    const allPassed = allVisible && criticalsPassed && !hasError
    const hasFail = allVisible && !criticalsPassed

    // Títulos dinâmicos baseados no estado
    let preflightTitle = 'Verificação Pré-Consulta'
    let preflightSubtitle = 'Preparando o ambiente para sua consulta…'
    let titleIcon = <Stethoscope size={40} style={{ color: 'var(--k-success)', marginBottom: 'var(--k-space-md)', opacity: 0.8 }} />

    if (allPassed) {
      preflightTitle = 'Ambiente Verificado'
      preflightSubtitle = 'Tudo pronto para iniciar sua consulta!'
      titleIcon = <CheckCircle2 size={40} style={{ color: 'var(--k-success)', marginBottom: 'var(--k-space-md)' }} />
    } else if (hasFail) {
      preflightTitle = 'Atenção Necessária'
      preflightSubtitle = 'Alguns serviços precisam de verificação'
      titleIcon = <AlertTriangle size={40} style={{ color: 'var(--k-warning)', marginBottom: 'var(--k-space-md)' }} />
    }

    return (
      <div className="consulta-preflight">
        {titleIcon}
        <h3 className="consulta-preflight-title">{preflightTitle}</h3>
        <p className="consulta-preflight-subtitle">
          {preflightSubtitle}
        </p>

        <div className="consulta-checks-grid">
          {PREFLIGHT_CHECKS.map((check) => {
            const visible = checksVisible.includes(check.key)
            const passed = checkPassed(check.key)
            const Icon = check.icon

            let statusClass = 'pending'
            let statusText = 'Aguardando…'
            let StatusIcon = Loader2

            if (visible && !hasError) {
              statusClass = passed ? 'ok' : 'fail'
              statusText = passed ? 'Operacional' : 'Indisponível'
              StatusIcon = passed ? CheckCircle2 : XCircle
            } else if (visible && hasError) {
              statusClass = 'fail'
              statusText = 'Erro'
              StatusIcon = XCircle
            } else if (preflightLoading) {
              statusClass = 'checking'
              statusText = 'Verificando…'
            }

            return (
              <div
                key={check.key}
                className={`consulta-check-card ${visible ? 'consulta-check-visible' : ''} ${visible ? (passed && !hasError ? 'consulta-check-ok' : (statusClass === 'fail' ? 'consulta-check-fail' : '')) : ''}`}
              >
                <div className={`consulta-check-icon ${statusClass}`}>
                  {statusClass === 'checking' ? (
                    <Loader2 size={18} className="k-animate-spin" />
                  ) : statusClass === 'ok' ? (
                    <CheckCircle2 size={18} />
                  ) : statusClass === 'fail' ? (
                    <XCircle size={18} />
                  ) : (
                    <Icon size={18} />
                  )}
                </div>
                <div>
                  <div className="consulta-check-name">
                    {check.label}
                  </div>
                  <div className="consulta-check-status">{statusText}</div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Seleção de Paciente */}
        <div className="consulta-patient-selector">
          <h4 className="consulta-patient-title">
            <User size={18} /> Identificação do Paciente
          </h4>

          {selectedPatient ? (
            <>
              <div className="consulta-patient-selected">
                <div className="consulta-patient-info">
                  <div className="consulta-patient-name">
                    <User size={16} /> {selectedPatient.name}
                  </div>
                  <div className="consulta-patient-details">
                    {selectedPatient.cpf && <span>CPF: {selectedPatient.cpf}</span>}
                    {selectedPatient.sex && selectedPatient.sex !== 'N' && (
                      <span>Sexo: {selectedPatient.sex === 'M' ? 'Masculino' : 'Feminino'}</span>
                    )}
                    {selectedPatient.birth_date && <span>Nasc.: {formatDateBR(selectedPatient.birth_date)}</span>}
                  </div>
                </div>
                <button
                  className="k-btn k-btn-ghost k-btn-sm"
                  onClick={() => { setSelectedPatient(null); setPatientFiles([]); }}
                >
                  <X size={14} /> Trocar
                </button>
              </div>

              {/* Arquivos do Paciente */}
              <div style={{ marginTop: 16, padding: '16px', background: 'var(--k-surface-alt, rgba(255,255,255,0.03))', borderRadius: 12, border: '1px solid var(--k-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h5 style={{ margin: 0, fontSize: '0.875rem', color: 'var(--k-text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <FileText size={16} /> Arquivos do Paciente ({patientFiles.length})
                  </h5>
                  <button
                    className="k-btn k-btn-ghost k-btn-sm"
                    onClick={() => setShowUploadForm(!showUploadForm)}
                    style={{ fontSize: '0.75rem' }}
                  >
                    <Plus size={14} /> Anexar
                  </button>
                </div>

                {showUploadForm && (
                  <div style={{ padding: 12, marginBottom: 12, background: 'var(--k-bg-elevated, rgba(0,0,0,0.2))', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <select
                      value={uploadFileType}
                      onChange={e => setUploadFileType(e.target.value)}
                      style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--k-border)', background: 'var(--k-surface)', color: 'var(--k-text-main)', fontSize: '0.8125rem' }}
                    >
                      <option value="exame_lab">Exame Laboratorial</option>
                      <option value="exame_imagem">Exame de Imagem</option>
                      <option value="laudo">Laudo Médico</option>
                      <option value="receita">Receita</option>
                      <option value="outro">Outro</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Descrição (opcional)"
                      value={uploadDescription}
                      onChange={e => setUploadDescription(e.target.value)}
                      style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--k-border)', background: 'var(--k-surface)', color: 'var(--k-text-main)', fontSize: '0.8125rem' }}
                    />
                    <label
                      className="k-btn k-btn-secondary k-btn-sm"
                      style={{ cursor: 'pointer', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                    >
                      <Upload size={14} /> {uploading ? 'Enviando...' : 'Selecionar Arquivo'}
                      <input type="file" hidden onChange={handleFileUpload} disabled={uploading} accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.dicom,.dcm,.doc,.docx" />
                    </label>
                  </div>
                )}

                {loadingFiles ? (
                  <div style={{ textAlign: 'center', padding: 16, color: 'var(--k-text-muted)', fontSize: '0.8125rem' }}>
                    <Loader2 size={16} className="k-animate-spin" style={{ marginRight: 8 }} /> Carregando arquivos...
                  </div>
                ) : patientFiles.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 16, color: 'var(--k-text-muted)', fontSize: '0.8125rem' }}>
                    Nenhum arquivo anexado.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {patientFiles.map(f => (
                      <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--k-bg-elevated, rgba(0,0,0,0.15))', borderRadius: 8, fontSize: '0.8125rem' }}>
                        <FileText size={14} style={{ color: 'var(--k-accent)', flexShrink: 0 }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ color: 'var(--k-text-main)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {f.file_name}
                          </div>
                          <div style={{ color: 'var(--k-text-muted)', fontSize: '0.6875rem', display: 'flex', gap: 8 }}>
                            <span>{fileTypeLabels[f.file_type] || f.file_type}</span>
                            <span>{formatFileSize(f.file_size)}</span>
                            <span>{new Date(f.created_at).toLocaleDateString('pt-BR')}</span>
                          </div>
                        </div>
                        <button className="k-btn k-btn-ghost k-btn-sm" onClick={() => handleViewFile(f.id)} title="Visualizar" style={{ padding: 4 }}>
                          <Eye size={14} />
                        </button>
                        <button className="k-btn k-btn-ghost k-btn-sm" onClick={() => handleDeleteFile(f.id)} title="Excluir" style={{ padding: 4, color: 'var(--k-danger, #ef4444)' }}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="consulta-patient-search">
              <div className="consulta-patient-input-wrap">
                <Search size={16} className="consulta-patient-search-icon" />
                <input
                  type="text"
                  className="consulta-patient-input"
                  placeholder="Buscar paciente por nome ou CPF..."
                  value={patientSearch}
                  onChange={(e) => handlePatientSearch(e.target.value)}
                />
                {patientSearching && <Loader2 size={16} className="k-animate-spin consulta-patient-loading" />}
              </div>

              {patientResults.length > 0 && (
                <div className="consulta-patient-results">
                  {patientResults.map(p => (
                    <button
                      key={p.id}
                      className="consulta-patient-result-item"
                      onClick={() => handleSelectPatient(p)}
                    >
                      <User size={14} />
                      <span className="consulta-patient-result-name">{p.name}</span>
                      <span className="consulta-patient-result-cpf">{p.cpf}</span>
                      {p.sex && p.sex !== 'N' && (
                        <span className="consulta-patient-result-sex">
                          {p.sex === 'M' ? 'M' : 'F'}
                        </span>
                      )}
                      {p.birth_date && (
                        <span className="consulta-patient-result-birth">{formatDateBR(p.birth_date)}</span>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {/* Botao cadastrar novo paciente */}
              {patientSearch.length >= 2 && !patientSearching && patientResults.length === 0 && !showNewPatientForm && (
                <button
                  className="k-btn k-btn-secondary k-btn-sm"
                  style={{ marginTop: 12, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                  onClick={() => { setShowNewPatientForm(true); setNewPatientName(patientSearch); }}
                >
                  <UserPlus size={14} /> Cadastrar Novo Paciente
                </button>
              )}

              {/* Formulario de cadastro rapido */}
              {showNewPatientForm && (
                <div style={{ marginTop: 12, padding: 16, background: 'var(--k-bg-elevated, rgba(0,0,0,0.2))', borderRadius: 10, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <h5 style={{ margin: 0, fontSize: '0.875rem', color: 'var(--k-text-main)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <UserPlus size={16} /> Novo Paciente
                  </h5>
                  <input
                    type="text"
                    placeholder="Nome Completo *"
                    value={newPatientName}
                    onChange={e => setNewPatientName(e.target.value)}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--k-border)', background: 'var(--k-surface)', color: 'var(--k-text-main)', fontSize: '0.875rem' }}
                  />
                  <input
                    type="text"
                    placeholder="CPF *"
                    value={newPatientCpf}
                    onChange={e => setNewPatientCpf(formatCpf(e.target.value))}
                    maxLength={14}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--k-border)', background: 'var(--k-surface)', color: 'var(--k-text-main)', fontSize: '0.875rem' }}
                  />
                  <input
                    type="date"
                    placeholder="Data de Nascimento *"
                    value={newPatientBirth}
                    onChange={e => setNewPatientBirth(e.target.value)}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--k-border)', background: 'var(--k-surface)', color: 'var(--k-text-main)', fontSize: '0.875rem' }}
                  />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      className="k-btn k-btn-primary k-btn-sm"
                      onClick={handleCreatePatient}
                      disabled={savingPatient}
                      style={{ flex: 1 }}
                    >
                      {savingPatient ? 'Salvando...' : 'Cadastrar'}
                    </button>
                    <button
                      className="k-btn k-btn-ghost k-btn-sm"
                      onClick={() => setShowNewPatientForm(false)}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        {/* Teste de Microfone */}
        <div className="consulta-mic-test">
          {micTesting ? (
            <InlineAudioMeter level={micLevel} size="large" />
          ) : (
            <button
              className="k-btn k-btn-secondary"
              onClick={startMicTest}
              disabled={preflightLoading}
            >
              <Mic size={16} />
              Testar Microfone
            </button>
          )}
        </div>

        {/* Erro crítico */}
        {allVisible && !criticalsPassed && (
          <div className="consulta-error-banner">
            <AlertTriangle size={18} />
            <span>Não foi possível conectar a todos os serviços. Tente novamente.</span>
            <button className="k-btn k-btn-ghost k-btn-sm" onClick={doRunPreflight}>
              <RefreshCw size={14} />
              Tentar Novamente
            </button>
          </div>
        )}

        {/* Botão de iniciar */}
        {allVisible && criticalsPassed && (
          <button
            className="k-btn consulta-start-btn consulta-glow"
            onClick={handleStartConsulta}
          >
            <Mic size={20} />
            Iniciar Consulta
          </button>
        )}
      </div>
    )
  }

  // ─── Step 1: Live Consultation ───────────────────────────

  function renderLiveConsultation() {
    return (
      <div className="consulta-live">
        {/* Reconnect Banner */}
        {wsDisconnected && (
          <div className="consulta-reconnect">
            <WifiOff size={16} style={{ color: 'var(--k-warning)' }} />
            <span className="consulta-reconnect-text">
              Conexão com o copiloto perdida.
            </span>
            <button className="k-btn k-btn-secondary k-btn-sm" onClick={handleReconnect}>
              <RefreshCw size={14} />
              Reconectar
            </button>
          </div>
        )}

        {/* Top Bar */}
        <div className="consulta-topbar">
          <div className="consulta-ws-indicator">
            <span className={`consulta-ws-dot ${wsConnected ? 'connected' : 'disconnected'}`} />
            {wsConnected ? 'Copiloto Conectado' : 'Desconectado'}
          </div>

          <InlineAudioMeter level={audioLevel} />

          <div className="consulta-timer">
            <Clock size={14} />
            {formatTime(elapsedTime)}
          </div>

          <div className="consulta-topbar-spacer" />

          {silenceAlert && (
            <div className="consulta-silence-alert">
              <Volume2 size={14} />
              Silêncio prolongado
            </div>
          )}

          {lowAudioAlert && (
            <div className="consulta-silence-alert" style={{ color: 'var(--k-danger)', background: 'var(--k-danger-bg)' }}>
              <Volume2 size={14} />
              Áudio baixo
            </div>
          )}

          {/* Recording indicator */}
          <div className="consulta-recording-indicator" style={{ color: isPaused ? 'var(--k-warning)' : 'var(--k-danger)' }}>
            <span className={`consulta-recording-dot ${isPaused ? 'paused' : ''}`} />
            {isPaused ? 'Pausado' : 'Gravando'}
          </div>
        </div>

        {/* Split Layout */}
        <div className="consulta-split">
          {/* LEFT: Transcript */}
          <div className="consulta-left">
            <div className="consulta-transcript">
              {transcript.length === 0 && !interimText ? (
                <div className="consulta-transcript-empty">
                  <MessageSquare size={40} className="consulta-transcript-empty-icon" />
                  <span>Comece a falar…</span>
                  <span style={{ fontSize: '0.75rem' }}>A transcrição aparecerá aqui em tempo real</span>
                </div>
              ) : (
                <>
                  {transcript.map((entry, i) => (
                    <div key={i} className="consulta-transcript-line">
                      <span className="consulta-timestamp">[{formatTimestamp(entry.time)}]</span>
                      {entry.text}
                    </div>
                  ))}
                  {interimText && (
                    <div className="consulta-transcript-line interim">
                      {interimText}
                    </div>
                  )}
                  <div ref={transcriptEndRef} />
                </>
              )}

              {/* Segmentos Diarizados (após processamento STT) */}
              {diarizedSegments.length > 0 && (
                <div className="consulta-diarized">
                  <div className="consulta-diarized-header">
                    🎙️ Transcrição com Identificação de Falantes
                  </div>
                  {diarizedSegments.map((seg, i) => (
                    <div
                      key={i}
                      className={`consulta-diarized-segment ${seg.role === 'profissional' ? 'speaker-prof' : 'speaker-patient'}`}
                    >
                      <span className="consulta-diarized-badge">
                        {seg.role === 'profissional' ? '🩺 Prof.' : '👤 Paciente'}
                      </span>
                      <span className="consulta-diarized-text">{seg.text}</span>
                    </div>
                  ))}
                </div>
              )}

              {isDiarizing && (
                <div className="consulta-diarized-loading">
                  <Loader2 size={16} className="k-animate-spin" />
                  <span>Identificando falantes...</span>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: SOAP + Suggestions */}
          <div className="consulta-right">
            {/* SOAP Cards */}
            <div className="consulta-soap-panel">
              {['S', 'O', 'A', 'P'].map(letter => (
                <SoapMiniCard
                  key={letter}
                  letter={letter}
                  content={soapData[letter]}
                  updating={soapUpdating}
                />
              ))}
            </div>

            {/* Suggestions */}
            <div className="consulta-suggestions">
              <div className="consulta-suggestions-title">
                <Lightbulb size={14} />
                Sugestões do Copiloto
              </div>
              {suggestions.length > 0 ? (
                suggestions.map((sug, i) => (
                  <div key={i} className="consulta-suggestion-item">
                    <span className="consulta-suggestion-text">
                      {sug.text || sug.suggestion || sug}
                    </span>
                    {(sug.confidence != null) && (
                      <span className={`consulta-suggestion-confidence ${confidenceClass(sug.confidence)}`}>
                        {Math.round(sug.confidence * 100)}%
                      </span>
                    )}
                  </div>
                ))
              ) : (
                <div className="consulta-suggestions-empty">
                  Nenhuma sugestão ainda — continue a consulta
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Action Bar */}
        <div className="consulta-actions">
          <div className="consulta-actions-left">
            <button
              className="k-btn k-btn-secondary"
              onClick={handlePauseResume}
            >
              {isPaused ? <Play size={16} /> : <Pause size={16} />}
              {isPaused ? 'Retomar' : 'Pausar'}
            </button>

            {sessionId && (
              <span style={{ fontSize: '0.6875rem', color: 'var(--k-text-muted)', fontFamily: 'var(--k-font-mono)' }}>
                ID: {sessionId.slice(0, 8)}…
              </span>
            )}
          </div>
          <div className="consulta-actions-right">
            <button
              className="k-btn k-btn-ghost"
              onClick={() => setShowCancelModal(true)}
              style={{ color: 'var(--k-text-muted)' }}
            >
              <Trash2 size={16} />
              Cancelar Atendimento
            </button>
            <button
              className="k-btn k-btn-danger"
              onClick={() => setShowEndModal(true)}
            >
              <Square size={16} />
              Finalizar Consulta
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── Step 2: SOAP Review ─────────────────────────────────

  function renderSoapReview() {
    return (
      <div className="consulta-review">
        <h3 className="consulta-review-title">Revisão do SOAP</h3>
        <p className="consulta-review-subtitle">
          Revise e edite a nota clínica antes de gerar os documentos.
        </p>

        <div className="consulta-review-grid">
          {['S', 'O', 'A', 'P'].map(letter => (
            <div key={letter} className="consulta-review-card">
              <div className="consulta-review-card-header">
                <div
                  className="consulta-review-card-letter"
                  style={{ background: SOAP_COLORS[letter] }}
                >
                  {letter}
                </div>
                <span className="consulta-review-card-label">{SOAP_LABELS[letter]}</span>
              </div>
              <textarea
                className="k-textarea"
                value={editedSoap[letter]}
                onChange={e => handleSoapEdit(letter, e.target.value)}
                placeholder={`Conteúdo ${SOAP_LABELS[letter].toLowerCase()}…`}
                rows={5}
              />
            </div>
          ))}
        </div>

        <div className="consulta-review-actions">
          <button
            className="k-btn k-btn-secondary"
            onClick={() => setCurrentStep(1)}
          >
            <ArrowLeft size={16} />
            Voltar à Consulta
          </button>
          <button
            className="k-btn k-btn-primary"
            onClick={handleAdvanceToDocuments}
            disabled={!editedSoap.S && !editedSoap.O && !editedSoap.A && !editedSoap.P}
          >
            Gerar Documentos
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    )
  }

  // ─── Step 3: Document Selection ──────────────────────────

  function renderDocuments() {
    return (
      <div className="consulta-docs">
        <h3 className="consulta-docs-title">Documentos Médicos</h3>
        <p className="consulta-docs-subtitle">
          Selecione os documentos que deseja gerar a partir do SOAP revisado.
        </p>

        <div className="consulta-docs-types">
          {DOC_TYPES.map(docType => {
            const Icon = docType.icon
            const selected = selectedDocs.includes(docType.key)
            return (
              <div
                key={docType.key}
                className={`consulta-doc-type ${selected ? 'selected' : ''}`}
                onClick={() => toggleDocType(docType.key)}
                role="checkbox"
                aria-checked={selected}
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && toggleDocType(docType.key)}
              >
                <div className="consulta-doc-checkbox">
                  {selected && <Check size={14} />}
                </div>
                <div className="consulta-doc-type-info">
                  <h4>
                    <Icon size={14} style={{ marginRight: 6, verticalAlign: -2, opacity: 0.7 }} />
                    {docType.label}
                  </h4>
                  <p>{docType.desc}</p>
                </div>
              </div>
            )
          })}
        </div>

        <div className="consulta-docs-generate">
          <button
            className="k-btn k-btn-primary"
            onClick={handleGenerateBatch}
            disabled={selectedDocs.length === 0 || generatingDocs}
          >
            {generatingDocs ? (
              <>
                <Loader2 size={16} className="k-animate-spin" />
                Gerando…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Gerar Selecionados
              </>
            )}
          </button>
          <span className="consulta-docs-count">
            {selectedDocs.length} de {DOC_TYPES.length} selecionado(s)
          </span>
        </div>

        {/* Generated Documents */}
        {generatedDocs.length > 0 && (
          <div className="consulta-generated">
            <div className="consulta-generated-title">
              <FileCheck size={18} style={{ color: 'var(--k-success)' }} />
              Documentos Gerados
            </div>

            {generatedDocs.map((doc, i) => {
              const docLabel = DOC_TYPES.find(d => d.key === doc.type)?.label || doc.type || `Documento ${i + 1}`
              const content = doc.content || doc.text || JSON.stringify(doc, null, 2)
              return (
                <div key={i} className="consulta-doc-card">
                  <div className="consulta-doc-card-header">
                    <span className="consulta-doc-card-title">
                      <FileText size={16} style={{ color: 'var(--k-accent)' }} />
                      {docLabel}
                    </span>
                    <div className="consulta-doc-card-actions">
                      <button
                        className="k-btn k-btn-ghost k-btn-sm"
                        onClick={() => handleCopyDoc(i)}
                        title="Copiar"
                      >
                        {copiedDoc === i ? <Check size={14} /> : <Copy size={14} />}
                      </button>
                      <button
                        className="k-btn k-btn-ghost k-btn-sm"
                        onClick={() => handlePreviewDoc(i)}
                        title="Visualizar / Editar / PDF"
                      >
                        <Edit3 size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="consulta-doc-card-body">
                    {content}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Navigation */}
        <div className="consulta-review-actions" style={{ marginTop: 'var(--k-space-lg)' }}>
          <button
            className="k-btn k-btn-secondary"
            onClick={() => setCurrentStep(2)}
          >
            <ArrowLeft size={16} />
            Voltar ao SOAP
          </button>
        </div>
      </div>
    )
  }

  // ═══ Render Principal ════════════════════════════════════

  const STEP_LABELS = [
    'Verificação',
    'Consulta ao Vivo',
    'Revisão SOAP',
    'Documentos',
  ]

  return (
    <div className="consulta-page">
      {/* Header */}
      <div className="consulta-header">
        <div className="consulta-header-left">
          {(() => {
            const portalTarget = document.getElementById('topbar-portal-target');
            const content = (
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <h2 className="consulta-title" style={{ margin: 0, fontSize: '1.2rem', color: 'var(--k-text-main)', border: 'none', padding: 0 }}>Atendimento Médico</h2>
                {/* Step Indicators */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                  {STEP_LABELS.map((label, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span
                        className={`k-badge ${i === currentStep ? 'k-badge-success' : (i < currentStep ? 'k-badge-info' : '')}`}
                        style={{
                          opacity: i <= currentStep ? 1 : 0.4,
                          fontSize: '0.6875rem',
                          cursor: i < currentStep ? 'pointer' : 'default',
                        }}
                        onClick={() => { if (i < currentStep) setCurrentStep(i) }}
                      >
                        {i < currentStep ? <CheckCircle2 size={10} /> : null}
                        {label}
                      </span>
                      {i < STEP_LABELS.length - 1 && (
                        <ChevronRight size={12} style={{ color: 'var(--k-text-muted)', opacity: 0.4 }} />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
            return portalTarget ? createPortal(content, portalTarget) : content;
          })()}
        </div>
        
      </div>

      {/* Body */}
      <div className="consulta-body">
        {currentStep === 0 && renderPreflight()}
        {currentStep === 1 && renderLiveConsultation()}
        {currentStep === 2 && renderSoapReview()}
        {currentStep === 3 && renderDocuments()}
      </div>

      {/* Confirm Modal for ending consultation */}
      <ConfirmModal
        open={showEndModal}
        title="Finalizar Consulta?"
        message="Ao finalizar, a gravação será encerrada e o copiloto processará a nota SOAP final. Você poderá revisar antes de gerar os documentos."
        confirmLabel="Finalizar Consulta"
        variant="danger"
        onConfirm={handleEndConsulta}
        onCancel={() => setShowEndModal(false)}
      />

      {/* Confirm Modal for cancelling consultation */}
      <ConfirmModal
        open={showCancelModal}
        title="Cancelar Atendimento?"
        message="Deseja realmente cancelar este atendimento? A gravação será interrompida e todos os dados atuais serão descartados. Esta ação não pode ser desfeita."
        confirmLabel="Sim, Cancelar"
        variant="danger"
        onConfirm={handleCancelConsulta}
        onCancel={() => setShowCancelModal(false)}
      />

      {/* Document Preview Modal */}
      {previewDoc && (
        <div className="consulta-preview-overlay" onClick={() => setPreviewDoc(null)}>
          <div className="consulta-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="consulta-preview-header">
              <h3>
                <FileText size={18} style={{ color: 'var(--k-accent)' }} />
                {previewDoc.title}
              </h3>
              <button className="k-btn k-btn-ghost k-btn-sm" onClick={() => setPreviewDoc(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="consulta-preview-body">
              <textarea
                className="consulta-preview-textarea"
                value={previewContent}
                onChange={(e) => setPreviewContent(e.target.value)}
                spellCheck={false}
              />
            </div>

            <div className="consulta-preview-footer">
              <button className="k-btn k-btn-secondary" onClick={() => {
                const doc = generatedDocs[previewDoc.index]
                if (doc) {
                  doc.content = previewContent
                  setGeneratedDocs([...generatedDocs])
                }
                addToast('Documento atualizado!', 'success')
              }}>
                <Check size={16} /> Salvar Alterações
              </button>
              <button className="k-btn k-btn-primary" onClick={handleDownloadPdf}>
                <Download size={16} /> Baixar PDF
              </button>
              <button className="k-btn k-btn-ghost" onClick={() => {
                const win = window.open('', '_blank')
                if (win) {
                  win.document.write(`<pre style="font-family: 'Inter', sans-serif; padding: 40px; white-space: pre-wrap;">${previewContent}</pre>`)
                  win.document.close()
                  win.print()
                }
              }}>
                <Printer size={16} /> Imprimir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// FORCE CACHE INVALIDATION 1787015370.2449138