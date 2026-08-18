/* ============================================================
   ClinicalAuthGate — Controle de Acesso ao Módulo Clínico
   Somente médicos autorizados podem acessar as funcionalidades.
   O cadastro/login é feito no Paperclip (Multi-Tenant).
   ============================================================ */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck,
  Lock,
  Stethoscope,
  AlertCircle,
  Loader2,
  LogOut,
  KeyRound,
  User,
  Building,
  Mail,
  ArrowLeft,
  Eye,
  EyeOff
} from 'lucide-react'
import { clinicalHealth } from '../services/clinicalApi'
import { loginDoctor, registerDoctor, recoverPin } from '../services/api'
import './ClinicalAuthGate.css'

const ClinicalAuthContext = createContext(null)

export function ClinicalAuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Restaurar sessão
    const saved = sessionStorage.getItem('k-clinical-session')
    if (saved) {
      try {
        setSession(JSON.parse(saved))
      } catch (err) {
        console.error('Sessão inválida')
        sessionStorage.removeItem('k-clinical-session')
      }
    }
    setLoading(false)
  }, [])

  const logout = useCallback(() => {
    setSession(null)
    sessionStorage.removeItem('k-clinical-session')
  }, [])

  const login = useCallback((data) => {
    setSession(data)
    sessionStorage.setItem('k-clinical-session', JSON.stringify(data))
  }, [])

  if (loading) {
    return (
      <div className="clinical-auth-loading">
        <Loader2 size={32} className="k-animate-spin" />
        <p>Iniciando Módulo Clínico...</p>
      </div>
    )
  }

  if (!session) {
    return <AuthScreen onLogin={login} />
  }

  return (
    <ClinicalAuthContext.Provider value={{ session, logout }}>
      {children}
    </ClinicalAuthContext.Provider>
  )
}

export function useClinicalAuth() {
  const context = useContext(ClinicalAuthContext)
  if (!context) {
    throw new Error('useClinicalAuth deve ser usado dentro de ClinicalAuthProvider')
  }
  return context
}

// ═══ Auth Screen (Tabs) ═════════════════════════════════════

function AuthScreen({ onLogin }) {
  const [view, setView] = useState('login') // 'login', 'register', 'recover'

  return (
    <div className="clinical-auth-screen">
      <div className="clinical-auth-card">
        <div className="clinical-auth-glow" />
        
        {view !== 'login' && (
          <button
            type="button"
            className="clinical-auth-top-back"
            onClick={() => setView('login')}
            title="Voltar ao início"
          >
            <ArrowLeft size={18} />
          </button>
        )}

        <div className="clinical-auth-icon">
          <ShieldCheck size={32} />
        </div>

        {view === 'login' && <LoginForm onLogin={onLogin} setView={setView} />}
        {view === 'register' && <RegisterForm setView={setView} />}
        {view === 'recover' && <RecoverForm setView={setView} />}
      </div>
    </div>
  )
}

// ═══ Login ══════════════════════════════════════════════════

function LoginForm({ onLogin, setView }) {
  const [crm, setCrm] = useState('')
  const [pin, setPin] = useState('')
  const [showPin, setShowPin] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (!crm.trim() || !pin.trim()) {
      setError('Por favor, informe o CRM e o PIN.')
      return
    }

    setLoading(true)

    try {
      // 1. Fazer login no Paperclip
      const data = await loginDoctor({ crm, pin })
      
      // 2. Verificar se a API clínica está respondendo
      try {
        await clinicalHealth()
      } catch (err) {
        throw new Error('Módulo Clínico (Backend) está offline.')
      }

      // 3. Salvar sessão
      onLogin({
        token: data.token,
        tenantSlug: data.tenant_slug,
        tenantName: data.tenant_name,
        name: data.name,
        crm: data.crm,
        avatarUrl: data.avatar_url,
        isAdmin: data.is_admin
      })

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erro ao conectar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h2 className="clinical-auth-title">Módulo Clínico</h2>
      <p className="clinical-auth-subtitle">Acesso restrito a profissionais de saúde</p>

      <form className="clinical-auth-form" onSubmit={handleSubmit}>
        <label className="clinical-auth-label">CRM</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type="text"
            placeholder="Ex: 123456-SP"
            value={crm}
            onChange={(e) => setCrm(e.target.value.toUpperCase())}
            required
          />
          <User size={16} className="clinical-auth-input-icon" />
        </div>

        <label className="clinical-auth-label">PIN</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type={showPin ? 'text' : 'password'}
            placeholder="Digite seu PIN numérico"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            required
          />
          <button
            type="button"
            className="clinical-auth-eye-btn"
            onClick={() => setShowPin(!showPin)}
            tabIndex={-1}
            title={showPin ? 'Ocultar PIN' : 'Mostrar PIN'}
          >
            {showPin ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        {error && (
          <div className="clinical-auth-error">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <button
          className="k-btn k-btn-primary clinical-auth-btn"
          type="submit"
          disabled={loading}
        >
          {loading ? (
            <><Loader2 size={18} className="k-animate-spin" /> Verificando...</>
          ) : (
            <><Stethoscope size={18} /> Entrar no Consultório</>
          )}
        </button>
      </form>

      <div className="clinical-auth-links">
        <button className="k-btn-link" onClick={() => setView('recover')}>Esqueci meu PIN</button>
        <button className="k-btn-link" onClick={() => setView('register')}>Primeiro Acesso? Cadastre-se</button>
      </div>
    </>
  )
}

// ═══ Register ═══════════════════════════════════════════════

function RegisterForm({ setView }) {
  const [form, setForm] = useState({ invite_code: '', name: '', crm: '', pin: '', pinConfirm: '' })
  const [showPin, setShowPin] = useState(false)
  const [showPinConfirm, setShowPinConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (form.pin !== form.pinConfirm) {
      setError('Os PINs não conferem')
      return
    }

    setLoading(true)
    try {
      await registerDoctor({
        invite_code: form.invite_code,
        name: form.name,
        crm: form.crm,
        pin: form.pin
      })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao realizar cadastro')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <>
        <h2 className="clinical-auth-title" style={{color: 'var(--k-success)'}}>Cadastro Realizado!</h2>
        <p className="clinical-auth-subtitle">Você já pode acessar o sistema com seu CRM e PIN.</p>
        <button className="k-btn k-btn-primary clinical-auth-btn" onClick={() => setView('login')} style={{marginTop: '24px'}}>
          Ir para Login
        </button>
      </>
    )
  }

  return (
    <>
      <h2 className="clinical-auth-title">Cadastro Médico</h2>
      <p className="clinical-auth-subtitle">Insira o código de convite da sua clínica</p>

      <form className="clinical-auth-form" onSubmit={handleSubmit}>
        <label className="clinical-auth-label">Código de Convite</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type="text"
            placeholder="Ex: CLINSORRISO26"
            value={form.invite_code}
            onChange={(e) => setForm({...form, invite_code: e.target.value.toUpperCase()})}
            required
          />
          <Building size={16} className="clinical-auth-input-icon" />
        </div>

        <label className="clinical-auth-label">Nome Completo</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type="text"
            placeholder="Dr. João Silva"
            value={form.name}
            onChange={(e) => setForm({...form, name: e.target.value})}
            required
          />
        </div>

        <label className="clinical-auth-label">CRM</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type="text"
            placeholder="Ex: 123456-SP"
            value={form.crm}
            onChange={(e) => setForm({...form, crm: e.target.value.toUpperCase()})}
            required
          />
        </div>

        <div className="clinical-auth-pin-row">
          <div>
            <label className="clinical-auth-label">Crie um PIN</label>
            <div className="clinical-auth-input-wrapper" style={{marginBottom: 0}}>
              <input
                className="k-input clinical-auth-input"
                type={showPin ? 'text' : 'password'}
                placeholder="Ex: 1234"
                value={form.pin}
                onChange={(e) => setForm({...form, pin: e.target.value})}
                required
              />
              <button
                type="button"
                className="clinical-auth-eye-btn"
                onClick={() => setShowPin(!showPin)}
                tabIndex={-1}
                title={showPin ? 'Ocultar PIN' : 'Mostrar PIN'}
              >
                {showPin ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <div>
            <label className="clinical-auth-label">Confirme o PIN</label>
            <div className="clinical-auth-input-wrapper" style={{marginBottom: 0}}>
              <input
                className="k-input clinical-auth-input"
                type={showPinConfirm ? 'text' : 'password'}
                placeholder="Confirme"
                value={form.pinConfirm}
                onChange={(e) => setForm({...form, pinConfirm: e.target.value})}
                required
              />
              <button
                type="button"
                className="clinical-auth-eye-btn"
                onClick={() => setShowPinConfirm(!showPinConfirm)}
                tabIndex={-1}
                title={showPinConfirm ? 'Ocultar PIN' : 'Mostrar PIN'}
              >
                {showPinConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="clinical-auth-error">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <div className="clinical-auth-actions">
          <button className="k-btn k-btn-primary clinical-auth-btn" type="submit" disabled={loading}>
            {loading ? <Loader2 size={18} className="k-animate-spin" /> : 'Finalizar Cadastro'}
          </button>
          <button
            type="button"
            className="k-btn k-btn-secondary clinical-auth-btn clinical-auth-btn-secondary"
            onClick={() => setView('login')}
          >
            <ArrowLeft size={18} /> Voltar para o Login
          </button>
        </div>
      </form>
    </>
  )
}

// ═══ Recover PIN ════════════════════════════════════════════

function RecoverForm({ setView }) {
  const [crm, setCrm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (!crm.trim()) {
      setError('Por favor, informe o CRM.')
      return
    }

    setLoading(true)

    try {
      await recoverPin(crm)
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao solicitar recuperação')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <>
        <h2 className="clinical-auth-title" style={{color: 'var(--k-success)'}}>Solicitação Enviada</h2>
        <p className="clinical-auth-subtitle">Se o CRM existir, as instruções foram enviadas para os meios de contato do médico e do administrador da clínica.</p>
        <button className="k-btn k-btn-primary clinical-auth-btn" onClick={() => setView('login')} style={{marginTop: '24px'}}>
          Voltar para Login
        </button>
      </>
    )
  }

  return (
    <>
      <h2 className="clinical-auth-title">Recuperar PIN</h2>
      <p className="clinical-auth-subtitle">Informe seu CRM para enviarmos instruções ao administrador da clínica.</p>

      <form className="clinical-auth-form" onSubmit={handleSubmit}>
        <label className="clinical-auth-label">CRM</label>
        <div className="clinical-auth-input-wrapper">
          <input
            className="k-input clinical-auth-input"
            type="text"
            placeholder="Ex: 123456-SP"
            value={crm}
            onChange={(e) => setCrm(e.target.value.toUpperCase())}
            required
          />
          <User size={16} className="clinical-auth-input-icon" />
        </div>

        {error && (
          <div className="clinical-auth-error">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <div className="clinical-auth-actions">
          <button className="k-btn k-btn-primary clinical-auth-btn" type="submit" disabled={loading}>
            {loading ? <Loader2 size={18} className="k-animate-spin" /> : 'Solicitar Recuperação'}
          </button>
          <button
            type="button"
            className="k-btn k-btn-secondary clinical-auth-btn clinical-auth-btn-secondary"
            onClick={() => setView('login')}
          >
            <ArrowLeft size={18} /> Voltar para o Login
          </button>
        </div>
      </form>
    </>
  )
}
