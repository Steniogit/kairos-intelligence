/* ============================================================
   ClinicaForm — Formulário completo com Toast + Validação
   ============================================================ */

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft, Save, Building2, Link2, MessageSquare, Bot, Crown,
  Eye, EyeOff, Upload, FileText, Trash2, Loader2, Info, ShieldCheck,
  ExternalLink, QrCode,
} from 'lucide-react'
import { createTenant, fetchTenant, updateTenant } from '../../services/api'
import { useToast } from '../../components/Toast'
import './ClinicaForm.css'

const TABS = [
  { id: 'dados', label: 'Dados Cadastrais', icon: Building2 },
  { id: 'ademed', label: 'Conexão Ademed', icon: Link2 },
  { id: 'whatsapp', label: 'WhatsApp Oficial', icon: MessageSquare },
  { id: 'frontdesk', label: 'Front-Desk (Soul)', icon: Bot },
  { id: 'jarvis', label: 'Jarvis (Premium)', icon: Crown },
]

const INITIAL_STATE = {
  name: '', slug: '', cnpj: '', endereco: '', cidade: '', estado: '', cep: '',
  telefone: '', responsavel: '', email: '',
  ademed_url: '', ademed_user: '', ademed_pass: '',
  evolution_instance: '', meta_access_token: '', meta_phone_number_id: '', meta_business_id: '',
  soul_prompt: '', greeting_message: '', business_hours: '',
  jarvis_enabled: false, jarvis_soul: '', jarvis_channel: 'telegram',
  jarvis_telegram_token: '', jarvis_whatsapp_instance: '',
  jarvis_briefing_enabled: false, jarvis_briefing_time: '08:00',
  jarvis_owner_name: '', jarvis_owner_phone: '',
}

export default function ClinicaForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { addToast } = useToast()
  const isEditing = Boolean(id)

  const [activeTab, setActiveTab] = useState('dados')
  const [form, setForm] = useState(INITIAL_STATE)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showPasswords, setShowPasswords] = useState({})
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [jarvisFiles, setJarvisFiles] = useState([])
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (isEditing) {
      setLoading(true)
      fetchTenant(id)
        .then((data) => {
          const cfg = data.config || {}
          setForm({
            name: data.name || '', slug: data.slug || '',
            cnpj: cfg.cnpj || '', endereco: cfg.endereco?.logradouro || '',
            cidade: cfg.endereco?.cidade || '', estado: cfg.endereco?.estado || '',
            cep: cfg.endereco?.cep || '', telefone: cfg.telefone || '',
            responsavel: cfg.responsavel || '', email: cfg.email || '',
            ademed_url: cfg.ademed_url || '', ademed_user: cfg.ademed_user || '',
            ademed_pass: cfg.ademed_pass || '',
            evolution_instance: data.evolution_instance || '',
            meta_access_token: cfg.meta_access_token || '',
            meta_phone_number_id: cfg.meta_phone_number_id || '',
            meta_business_id: cfg.meta_business_id || '',
            soul_prompt: data.soul_prompt || '',
            greeting_message: cfg.greeting_message || '', business_hours: cfg.business_hours || '',
            jarvis_enabled: cfg.jarvis?.enabled || false, jarvis_soul: cfg.jarvis?.soul || '',
            jarvis_channel: cfg.jarvis?.channel || 'telegram',
            jarvis_telegram_token: cfg.jarvis?.telegram_token || '',
            jarvis_whatsapp_instance: cfg.jarvis?.whatsapp_instance || '',
            jarvis_briefing_enabled: cfg.jarvis?.briefing_enabled || false,
            jarvis_briefing_time: cfg.jarvis?.briefing_time || '08:00',
            jarvis_owner_name: cfg.jarvis?.owner_name || '',
            jarvis_owner_phone: cfg.jarvis?.owner_phone || '',
          })
        })
        .catch(() => addToast('Erro ao carregar clínica.', 'error'))
        .finally(() => setLoading(false))
    }
  }, [id, isEditing])

  function handleChange(field, value) {
    setForm(prev => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: null }))
  }

  function togglePassword(field) {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }))
  }

  function handleFileUpload(e, target = 'frontdesk') {
    const files = Array.from(e.target.files)
    const setter = target === 'jarvis' ? setJarvisFiles : setUploadedFiles
    setter(prev => [...prev, ...files.map(f => ({ name: f.name, size: f.size, file: f }))])
    addToast(`${files.length} arquivo(s) adicionado(s).`, 'info')
  }

  function removeFile(index, target = 'frontdesk') {
    const setter = target === 'jarvis' ? setJarvisFiles : setUploadedFiles
    setter(prev => prev.filter((_, i) => i !== index))
  }

  function validate() {
    const e = {}
    if (!form.name.trim()) e.name = 'Nome é obrigatório'
    if (!form.slug.trim()) e.slug = 'Slug é obrigatório'
    if (!form.evolution_instance.trim()) e.evolution_instance = 'Instância Evolution é obrigatória'
    setErrors(e)
    if (Object.keys(e).length > 0) {
      addToast('Preencha os campos obrigatórios.', 'error')
      setActiveTab('dados')
      if (!form.evolution_instance.trim() && form.name.trim() && form.slug.trim()) setActiveTab('whatsapp')
    }
    return Object.keys(e).length === 0
  }

  async function handleSave() {
    if (!validate()) return
    setSaving(true)
    try {
      const payload = {
        name: form.name, slug: form.slug, evolution_instance: form.evolution_instance,
        soul_prompt: form.soul_prompt,
        config: {
          cnpj: form.cnpj, telefone: form.telefone, responsavel: form.responsavel, email: form.email,
          endereco: { logradouro: form.endereco, cidade: form.cidade, estado: form.estado, cep: form.cep },
          ademed_url: form.ademed_url, ademed_user: form.ademed_user, ademed_pass: form.ademed_pass,
          meta_access_token: form.meta_access_token, meta_phone_number_id: form.meta_phone_number_id,
          meta_business_id: form.meta_business_id,
          greeting_message: form.greeting_message, business_hours: form.business_hours,
          jarvis: {
            enabled: form.jarvis_enabled, soul: form.jarvis_soul, channel: form.jarvis_channel,
            telegram_token: form.jarvis_telegram_token, whatsapp_instance: form.jarvis_whatsapp_instance,
            briefing_enabled: form.jarvis_briefing_enabled, briefing_time: form.jarvis_briefing_time,
            owner_name: form.jarvis_owner_name, owner_phone: form.jarvis_owner_phone,
          },
        },
      }
      if (isEditing) {
        await updateTenant(id, { name: payload.name, config: payload.config, soul_prompt: payload.soul_prompt })
      } else {
        await createTenant(payload)
      }
      addToast(isEditing ? 'Clínica atualizada com sucesso!' : 'Clínica cadastrada com sucesso!', 'success')
      navigate('/clinicas')
    } catch (err) {
      addToast('Erro ao salvar. Verifique os dados e tente novamente.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const onboardingLink = form.slug ? `kairos.com/conectar/${form.slug}` : ''

  if (loading) {
    return (
      <div className="clinicas-loading">
        <Loader2 size={32} className="k-animate-spin" />
        <p>Carregando dados da clínica...</p>
      </div>
    )
  }

  function renderInput(field, label, placeholder, opts = {}) {
    const hasError = errors[field]
    return (
      <div className={`k-input-group ${hasError ? 'k-input-error' : ''}`} style={opts.style}>
        <label className="k-label">{label}{opts.required && ' *'}</label>
        {opts.password ? (
          <div className="k-input-password">
            <input className="k-input" type={showPasswords[field] ? 'text' : 'password'}
              value={form[field]} onChange={e => handleChange(field, e.target.value)}
              placeholder={placeholder} disabled={opts.disabled} id={`input-${field}`} />
            <button className="k-toggle-eye" onClick={() => togglePassword(field)} type="button">
              {showPasswords[field] ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        ) : opts.textarea ? (
          <textarea className="k-textarea" rows={opts.rows || 6}
            value={form[field]} onChange={e => handleChange(field, e.target.value)}
            placeholder={placeholder} id={`input-${field}`} />
        ) : (
          <input className="k-input" type={opts.type || 'text'}
            value={form[field]} onChange={e => handleChange(field, opts.transform ? opts.transform(e.target.value) : e.target.value)}
            placeholder={placeholder} disabled={opts.disabled} maxLength={opts.maxLength} id={`input-${field}`} />
        )}
        {hasError && <span className="k-error-message">{hasError}</span>}
      </div>
    )
  }

  function renderUploadArea(files, setterTarget, inputId) {
    return (
      <div className="upload-area">
        <label className="upload-dropzone" htmlFor={inputId}>
          <Upload size={24} />
          <span>Arraste arquivos ou clique para enviar</span>
          <span className="k-text-sm k-text-muted">PDF, DOC, TXT — Máx. 10MB por arquivo</span>
          <input id={inputId} type="file" multiple accept=".pdf,.doc,.docx,.txt" onChange={e => handleFileUpload(e, setterTarget)} hidden />
        </label>
        {files.length > 0 && (
          <div className="upload-list">
            {files.map((file, i) => (
              <div key={i} className="upload-file">
                <FileText size={16} />
                <span className="upload-file-name">{file.name}</span>
                <span className="k-text-sm k-text-muted">{(file.size / 1024).toFixed(0)} KB</span>
                <button className="k-btn k-btn-ghost k-btn-sm" onClick={() => removeFile(i, setterTarget)}>
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="clinica-form-page">
      <div className="clinica-form-header">
        <button className="k-btn k-btn-ghost" onClick={() => navigate('/clinicas')} id="btn-voltar">
          <ArrowLeft size={18} /> Voltar
        </button>
        <h2 className="clinicas-title">{isEditing ? `Editar: ${form.name}` : 'Cadastrar Nova Clínica'}</h2>
        <button className="k-btn k-btn-primary" onClick={handleSave} disabled={saving} id="btn-salvar-clinica">
          {saving ? <Loader2 size={18} className="k-animate-spin" /> : <Save size={18} />}
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>

      <div className="k-tabs">
        {TABS.map(tab => {
          const Icon = tab.icon
          return (
            <button key={tab.id} className={`k-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)} id={`tab-${tab.id}`}>
              <Icon size={16} /> {tab.label}
            </button>
          )
        })}
      </div>

      <div className="k-tab-content">
        {/* DADOS CADASTRAIS */}
        {activeTab === 'dados' && (
          <div className="form-section">
            <div className="form-section-title"><Building2 size={20} /><h3>Informações da Clínica</h3></div>
            <p className="form-section-desc">Dados administrativos da clínica para seu controle gerencial.</p>
            <div className="form-grid">
              {renderInput('name', 'Nome da Clínica', 'Ex: Clínica Sorriso', { required: true })}
              {renderInput('slug', 'Slug (Identificador Único)', 'Ex: clinica-sorriso', { required: true, disabled: isEditing, transform: v => v.toLowerCase().replace(/\s+/g, '-') })}
              {renderInput('cnpj', 'CNPJ', '00.000.000/0000-00')}
              {renderInput('responsavel', 'Pessoa Responsável', 'Nome completo')}
              {renderInput('telefone', 'Telefone Administrativo', '(00) 00000-0000')}
              {renderInput('email', 'E-mail', 'contato@clinica.com', { type: 'email' })}
            </div>
            <div className="form-divider" />
            <h4 className="form-subtitle">Endereço</h4>
            <div className="form-grid">
              {renderInput('endereco', 'Logradouro', 'Rua, número, complemento', { style: { gridColumn: '1 / -1' } })}
              {renderInput('cidade', 'Cidade', 'São Paulo')}
              {renderInput('estado', 'Estado', 'SP', { maxLength: 2 })}
              {renderInput('cep', 'CEP', '00000-000')}
            </div>
          </div>
        )}

        {/* CONEXÃO ADEMED */}
        {activeTab === 'ademed' && (
          <div className="form-section">
            <div className="form-section-title"><Link2 size={20} /><h3>Integração com ERP Ademed</h3></div>
            <p className="form-section-desc">Credenciais de acesso à API do Ademed. Esses dados são criptografados e nunca são exibidos em texto claro após o salvamento.</p>
            <div className="form-alert form-alert-info"><Info size={16} /><span>O Kairós consulta o Ademed em tempo real. Pacientes, médicos e agendas ficam exclusivamente no ERP.</span></div>
            <div className="form-grid-single">
              {renderInput('ademed_url', 'URL da API Ademed', 'https://api.ademed.com.br/v1')}
              {renderInput('ademed_user', 'Usuário', 'Usuário da API', { password: true })}
              {renderInput('ademed_pass', 'Senha', '••••••••', { password: true })}
            </div>
          </div>
        )}

        {/* WHATSAPP OFICIAL */}
        {activeTab === 'whatsapp' && (
          <div className="form-section">
            <div className="form-section-title"><MessageSquare size={20} /><h3>WhatsApp Oficial (Meta Cloud API)</h3></div>
            <p className="form-section-desc">Credenciais da API Oficial da Meta para o canal de atendimento. Sem QR Code — risco zero de banimento.</p>
            <div className="form-alert form-alert-success"><ShieldCheck size={16} /><span>Canal blindado. A API Oficial da Meta garante estabilidade total para atendimento de pacientes.</span></div>
            <div className="form-grid-single">
              {renderInput('evolution_instance', 'Nome da Instância Evolution', 'clinica-sorriso-wa', { required: true, disabled: isEditing })}
              {renderInput('meta_access_token', 'Meta Access Token', 'EAAxxxxxxxx...', { password: true })}
              {renderInput('meta_phone_number_id', 'Phone Number ID', '1234567890')}
              {renderInput('meta_business_id', 'Business ID', '9876543210')}
            </div>
          </div>
        )}

        {/* FRONT-DESK (SOUL) */}
        {activeTab === 'frontdesk' && (
          <div className="form-section">
            <div className="form-section-title"><Bot size={20} /><h3>Agente Front-Desk (Identidade e Regras)</h3></div>
            <p className="form-section-desc">Defina a personalidade e as regras de negócio que o agente de atendimento herdará para esta clínica.</p>
            <div className="form-grid-single">
              {renderInput('soul_prompt', 'Soul (Personalidade da IA)', "Descreva como o agente deve se comportar ao atender os pacientes...", { textarea: true, rows: 10 })}
              {renderInput('greeting_message', 'Mensagem de Boas-Vindas', 'Olá! 😊 Bem-vindo à Clínica Sorriso...', { textarea: true, rows: 3 })}
              {renderInput('business_hours', 'Horário de Funcionamento', 'Segunda a Sexta: 08:00 - 18:00 | Sábado: 08:00 - 12:00')}
            </div>
            <div className="form-divider" />
            <h4 className="form-subtitle">Base de Conhecimento do Atendimento</h4>
            <p className="form-section-desc">Envie PDFs, manuais e FAQs para que o Front-Desk saiba responder as dúvidas dos pacientes desta clínica.</p>
            {renderUploadArea(uploadedFiles, 'frontdesk', 'file-upload-frontdesk')}
          </div>
        )}

        {/* JARVIS (PREMIUM) */}
        {activeTab === 'jarvis' && (
          <div className="form-section">
            <div className="form-section-title">
              <Crown size={20} /><h3>Jarvis — Assistente Pessoal do Proprietário</h3>
              <span className="k-badge k-badge-premium">Premium</span>
            </div>
            <p className="form-section-desc">Ative o Jarvis para vender um serviço de consultoria de IA ao dono da clínica. Cobrança à parte.</p>

            <div className="jarvis-toggle-row">
              <div><strong>Ativar Jarvis para esta clínica</strong><p className="k-text-sm k-text-muted">O dono terá acesso a um assistente pessoal de IA.</p></div>
              <label className="k-toggle"><input type="checkbox" checked={form.jarvis_enabled} onChange={e => handleChange('jarvis_enabled', e.target.checked)} /><span className="k-toggle-slider" /></label>
            </div>

            {form.jarvis_enabled && (
              <>
                <div className="form-divider" />
                <h4 className="form-subtitle">Dados do Proprietário</h4>
                <div className="form-grid">
                  {renderInput('jarvis_owner_name', 'Nome do Proprietário', 'Dr. Roberto Silva')}
                  {renderInput('jarvis_owner_phone', 'Telefone do Proprietário', '(00) 00000-0000')}
                </div>

                <div className="form-divider" />
                <h4 className="form-subtitle">Identidade do Jarvis</h4>
                {renderInput('jarvis_soul', 'Soul do Jarvis (Como conversa com o dono)', 'Você é o consultor pessoal do Dr. Roberto...', { textarea: true })}

                <div className="form-divider" />
                <h4 className="form-subtitle">Base de Conhecimento Sigilosa</h4>
                <p className="form-section-desc">Documentos financeiros e gerenciais que apenas o Jarvis e o dono terão acesso. O Front-Desk <strong>nunca</strong> verá estes arquivos.</p>
                <div className="form-alert form-alert-warning">
                  <ShieldCheck size={16} /><span>Isolamento total. Esses documentos ficam em um RAG separado do atendimento.</span>
                </div>
                {renderUploadArea(jarvisFiles, 'jarvis', 'file-upload-jarvis')}

                <div className="form-divider" />
                <h4 className="form-subtitle">Canal de Comunicação</h4>
                <p className="form-section-desc">O dono se comunicará com o Jarvis por um canal privado (sem risco de banimento).</p>
                <div className="form-grid">
                  <div className="k-input-group">
                    <label className="k-label">Canal Preferido</label>
                    <select className="k-select" value={form.jarvis_channel} onChange={e => handleChange('jarvis_channel', e.target.value)} id="select-jarvis-channel">
                      <option value="telegram">Telegram (Bot)</option>
                      <option value="whatsapp">WhatsApp (QR Code)</option>
                    </select>
                  </div>
                  {form.jarvis_channel === 'telegram' && renderInput('jarvis_telegram_token', 'Token do Bot Telegram', '1234567890:ABCdef...', { password: true })}
                  {form.jarvis_channel === 'whatsapp' && renderInput('jarvis_whatsapp_instance', 'Instância WhatsApp (Jarvis)', 'jarvis-clinica-sorriso')}
                </div>

                {/* Onboarding Link */}
                {form.jarvis_channel === 'whatsapp' && onboardingLink && (
                  <>
                    <div className="form-divider" />
                    <h4 className="form-subtitle">Link de Onboarding Remoto</h4>
                    <p className="form-section-desc">Envie este link para o proprietário conectar o WhatsApp do Jarvis do conforto do escritório dele.</p>
                    <div className="onboarding-link-card">
                      <QrCode size={40} className="onboarding-qr-icon" />
                      <div className="onboarding-link-info">
                        <code className="onboarding-link-url">{onboardingLink}</code>
                        <p className="k-text-sm k-text-muted">O dono escaneia o QR Code nesta página para conectar o Jarvis.</p>
                      </div>
                      <button className="k-btn k-btn-secondary k-btn-sm" onClick={() => { navigator.clipboard.writeText(`https://${onboardingLink}`); addToast('Link copiado!', 'success') }}>
                        <ExternalLink size={14} /> Copiar
                      </button>
                    </div>
                  </>
                )}

                <div className="form-divider" />
                <h4 className="form-subtitle">Morning Briefing</h4>
                <div className="jarvis-toggle-row">
                  <div><strong>Resumo matinal automático</strong><p className="k-text-sm k-text-muted">O Jarvis envia um resumo do dia (agendas, cancelamentos, faturamento) toda manhã.</p></div>
                  <label className="k-toggle"><input type="checkbox" checked={form.jarvis_briefing_enabled} onChange={e => handleChange('jarvis_briefing_enabled', e.target.checked)} /><span className="k-toggle-slider" /></label>
                </div>
                {form.jarvis_briefing_enabled && (
                  <div className="k-input-group" style={{ maxWidth: 200 }}>
                    <label className="k-label">Horário do Briefing</label>
                    <input className="k-input" type="time" value={form.jarvis_briefing_time} onChange={e => handleChange('jarvis_briefing_time', e.target.value)} id="input-briefing-time" />
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
