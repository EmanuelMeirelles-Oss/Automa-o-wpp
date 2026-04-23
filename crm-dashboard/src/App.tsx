import { useState, useEffect } from 'react'
import './App.css'

interface Lead {
  id: number
  nome: string
  telefone: string
  cidade: string
  tem_site: boolean
  status_disparo: string
}

function App() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [botStatus, setBotStatus] = useState({ is_running: false, logs: [] })
  const [newLead, setNewLead] = useState({ nome: '', telefone: '', cidade: '', tem_site: false })

  const fetchLeads = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/leads')
      const data = await res.json()
      setLeads(data)
    } catch (e) {
      // Falha silenciosa no painel se a api estiver caindo (trata-se pro usuario nao ver erros feios)
    }
  }

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/bot/status')
      const data = await res.json()
      setBotStatus(data)
    } catch (e) {}
  }

  useEffect(() => {
    fetchLeads()
    const intv = setInterval(fetchStatus, 2000)
    return () => clearInterval(intv)
  }, [])

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault()
    await fetch('http://localhost:8000/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newLead)
    })
    setNewLead({ nome: '', telefone: '', cidade: '', tem_site: false })
    fetchLeads()
  }

  const handleDelete = async (id: number) => {
    await fetch(`http://localhost:8000/api/leads/${id}`, { method: 'DELETE' })
    fetchLeads()
  }

  const handleStart = async () => {
    await fetch('http://localhost:8000/api/bot/start', { method: 'POST' })
    fetchStatus()
  }

  const handleStop = async () => {
    await fetch('http://localhost:8000/api/bot/stop', { method: 'POST' })
    fetchStatus()
  }

  // Traducoes do BD para interface
  const parseStatusLabel = (status: string) => {
    switch(status) {
      case 'PENDENTE': return 'Pendente'
      case 'ENVIANDO': return 'Disparando'
      case 'SUCESSO': return 'Concluído'
      case 'ERRO': return 'Falhou/Abortado'
      default: return 'Desconhecido'
    }
  }

  // Extracao de hora para os Logs do terminal para ficar elegante
  const formatTerminalLog = (log: string) => {
      // Filtra termos tecnicos/ingles se existirem de forma grosseira
      let handledLog = log.replace("Traceback", "Rastreamento").replace("SessionNotCreatedException", "Sessão Conflitante")
      
      return handledLog;
  }

  return (
    <div className="layout">
      <header className="modern-header">
        <div className="title-area">
          <h1 className="title">Terminal Operacional</h1>
          <div className="subtitle">Gestor de Disparos em Massa & CRM via Whatsapp</div>
        </div>
        <div className={`status-badge ${botStatus.is_running ? 'status-on' : 'status-off'}`}>
          <div className="indicator"></div>
          {botStatus.is_running ? 'SISTEMA ATIVO (DISPARANDO)' : 'SISTEMA PAUSADO'}
        </div>
      </header>

      <main className="content">
        <div className="left-panel flex flex-col gap-6" style={{display: 'flex', flexDirection: 'column', gap: '24px'}}>
          
          <div className="panel-card">
            <h2><span style={{opacity: 0.5}}>⚡</span> Controles de Execução</h2>
            <p className="panel-desc">Inicie ou interrompa a distribuição das mensagens programadas. O processo roda no background.</p>
            
            <div className="btn-group">
              <button 
                onClick={handleStart} 
                disabled={botStatus.is_running}
                className="btn btn-primary">
                 Start Escala
              </button>
              <button 
                onClick={handleStop}
                disabled={!botStatus.is_running} 
                className="btn btn-danger">
                 Pausar Envios
              </button>
            </div>
          </div>

          <div className="panel-card terminal-card">
            <div className="terminal-header">
              <div className="mac-btn mac-close"></div>
              <div className="mac-btn mac-min"></div>
              <div className="mac-btn mac-max"></div>
            </div>
            <div className="logs-box">
              {botStatus.logs.length === 0 && <span style={{opacity:0.5}}>&gt; Nenhum log registrado em sessão.</span>}
              {botStatus.logs.slice(-8).map((log, i) => (
                <div key={i} className="log-line">
                  <span className="log-time">[{new Date().toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit', second:'2-digit'})}]</span>
                  <span className="log-msg">{formatTerminalLog(log)}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="panel-card">
             <h3>Inserção Manual Rápida</h3>
             <form onSubmit={handleAddLead} className="input-group">
                <input className="modern-input" required placeholder="Nome do Estabelecimento" value={newLead.nome} onChange={(e) => setNewLead({...newLead, nome: e.target.value})} />
                <input className="modern-input" required placeholder="Telefone (+55)" value={newLead.telefone} onChange={(e) => setNewLead({...newLead, telefone: e.target.value})} />
                <input className="modern-input" required placeholder="Cidade/Região" value={newLead.cidade} onChange={(e) => setNewLead({...newLead, cidade: e.target.value})} />
                <label className="checkbox-label">
                  <input type="checkbox" className="modern-checkbox" checked={newLead.tem_site} onChange={(e) => setNewLead({...newLead, tem_site: e.target.checked})} />
                  Este lead possui algum site atualmente?
                </label>
                <button type="submit" className="btn btn-accent">Adicionar Lead à Fila</button>
             </form>
          </div>

        </div>

        <div className="right-panel">
          <div className="panel-card full-height">
            <div className="table-header">
                <h2>📋 Fila Principal ({leads.length})</h2>
                <button onClick={fetchLeads} className="btn-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                </button>
            </div>
            
            <div className="table-wrapper">
              <table className="leads-table">
                <thead>
                  <tr>
                    <th>Empresa</th>
                    <th>Telefone</th>
                    <th>Condição Tática</th>
                    <th>Status Processo</th>
                    <th>Del</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(lead => (
                    <tr key={lead.id}>
                      <td className="main-col">{lead.nome}<br/><span style={{fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 400}}>{lead.cidade}</span></td>
                      <td className="sec-col">{lead.telefone.replace(/(\d{2})(\d{2})(\d{5})(\d{4})/, '+$1 $2 $3-$4')}</td>
                      <td>
                        <span className={`tag ${lead.tem_site ? 'tag-default' : 'tag-default'}`}>
                           {lead.tem_site ? 'Site Existente' : 'Sem Site'}
                        </span>
                      </td>
                      <td>
                        <span className={`tag tag-${lead.status_disparo.toLowerCase()}`}>
                          {parseStatusLabel(lead.status_disparo)}
                        </span>
                      </td>
                      <td>
                         <button className="btn-remove" onClick={()=>handleDelete(lead.id)}>✕</button>
                      </td>
                    </tr>
                  ))}
                  {leads.length === 0 && (
                      <tr><td colSpan={5} style={{textAlign:'center', padding: '40px', color: '#71717a'}}>A fila de prospects está vazia. Insira novos alvos manualmente para começar.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
