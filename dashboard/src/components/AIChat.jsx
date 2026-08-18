
import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, BookOpen } from 'lucide-react'
import { searchKnowledgeGraph } from '../services/clinicalApi'
import { useClinicalAuth } from './ClinicalAuthGate'
import './AIChat.css'

export default function AIChat() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Olá, doutor(a)! Sou seu assistente baseado na literatura científica e no histórico da nossa clínica. O que deseja pesquisar?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)
  const { session } = useClinicalAuth()

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!loading) {
      inputRef.current?.focus()
    }
  }, [loading])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    const userText = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userText }])
    setLoading(true)
    
    try {
      const resp = await searchKnowledgeGraph(userText, session?.crm || 'default-doc')
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: resp.answer,
        refs: resp.references,
        local: resp.local_context
      }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: 'Desculpe, ocorreu um erro de conexão com a Base de Conhecimento.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="k-chat-container">
      <div className="k-chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`k-chat-msg ${msg.role === 'ai' ? 'k-chat-ai' : 'k-chat-user'}`}>
            <div className="k-chat-avatar">
              {msg.role === 'ai' ? <Bot size={16}/> : <User size={16}/>}
            </div>
            <div className="k-chat-bubble">
              <div className="k-chat-text">{msg.text}</div>
              
              {/* Scientific References */}
              {msg.refs && msg.refs.length > 0 && (
                <div className="k-chat-refs">
                  <strong><BookOpen size={12}/> Literatura Encontrada:</strong>
                  <ul>
                    {msg.refs.map((r, idx) => (
                      <li key={idx}>
                        {r.title} ({r.year}) - <em>{r.authors}</em>
                        {r.doi && <a href={r.doi} target="_blank" rel="noreferrer"> [Link]</a>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Local Graph Context */}
              {msg.local && msg.local.length > 0 && (
                <div className="k-chat-local">
                  <strong>Contexto da Clínica (Neo4j):</strong>
                  <ul>
                    {msg.local.map((p, idx) => <li key={idx}>{p}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="k-chat-msg k-chat-ai">
            <div className="k-chat-avatar"><Bot size={16}/></div>
            <div className="k-chat-bubble"><div className="k-chat-loading">Pesquisando na literatura e no grafo...</div></div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="k-chat-input-area" onSubmit={handleSend}>
        <input 
          ref={inputRef}
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Pergunte sobre um diagnóstico, tratamento ou paciente..."
          disabled={loading}
        />
        <button type="submit" disabled={loading} className="k-btn-chat">
          <Send size={18} />
        </button>
      </form>
    </div>
  )
}
