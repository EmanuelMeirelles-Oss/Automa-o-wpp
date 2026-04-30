import { useState, useEffect } from 'react'
import './App.css'

interface Lead {
  id: number
  nome: string
  telefone: string
  cidade: string
  tem_site: boolean
  instagram?: string
  avaliacao?: string
  status_disparo: string
}

function App() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [botStatus, setBotStatus] = useState({ is_running: false, is_extracting: false, logs: [] })
  const [newLead, setNewLead] = useState({ nome: '', telefone: '', cidade: '', tem_site: false })
  const [addError, setAddError] = useState<string | null>(null)
  const [extractQuery, setExtractQuery] = useState('')

  const fetchLeads = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/leads')
      const data = await res.json()
      setLeads(data)
    } catch (e) {
      // Falha silenciosa no painel se a api estiver caindo (trata-se pro usuario nao ver erros feios)
    }
  }

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/bot/status')
      const data = await res.json()
      setBotStatus(data)
    } catch (e) {}
  }

  useEffect(() => {
    fetchLeads()
    const statusIntv = setInterval(fetchStatus, 2000)
    const leadsIntv = setInterval(fetchLeads, 5000)
    return () => { clearInterval(statusIntv); clearInterval(leadsIntv) }
  }, [])

  const handleAddLead = async (e: React.FormEvent | React.MouseEvent) => {
    if (e) e.preventDefault();
    if (!newLead.nome || !newLead.telefone || !newLead.cidade) {
      setAddError('Preencha os campos de Nome, Telefone e Cidade.');
      return;
    }
    setAddError(null)
    try {
      const payload = { ...newLead, telefone: newLead.telefone.replace(/\D/g, '') }
      const res = await fetch('http://127.0.0.1:8000/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        const errorMsg = err.detail ?? 'Erro ao adicionar lead. Tente novamente.'
        setAddError(errorMsg)
        alert(errorMsg)
        return
      }
      setNewLead({ nome: '', telefone: '', cidade: '', tem_site: false })
      fetchLeads()
      alert("Lead adicionado com sucesso!")
    } catch {
      setAddError('Servidor indisponível. Verifique se o backend está rodando.')
      alert('Servidor indisponível. Verifique se o backend (Python) está rodando. Execute o iniciar_sistema.bat!')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/leads/${id}`, { method: 'DELETE' })
      fetchLeads()
    } catch {
      alert("Erro ao conectar com o servidor.")
    }
  }

  const handleClearQueue = async () => {
    if (window.confirm("Tem certeza que deseja apagar TODA a fila de leads?")) {
        try {
          await fetch(`http://127.0.0.1:8000/api/leads/clear`, { method: 'DELETE' })
          fetchLeads()
        } catch {
          alert("Erro ao conectar com o servidor.")
        }
    }
  }

  const handleResetStatus = async (id: number) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/leads/${id}/reset`, { method: 'PUT' })
      fetchLeads()
    } catch {
      alert("Erro ao conectar com o servidor.")
    }
  }

  const handleExtract = async (e: React.FormEvent | React.MouseEvent) => {
    if (e) e.preventDefault();
    if (!extractQuery) {
        alert("Preencha o termo de busca antes de mapear.");
        return;
    }
    try {
      await fetch('http://127.0.0.1:8000/api/bot/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ termo: extractQuery })
      })
      setExtractQuery('')
      fetchStatus()
      alert("Mapeamento iniciado em segundo plano!")
    } catch {
      alert("Erro ao conectar com o servidor. Verifique se o backend está rodando. Execute iniciar_sistema.bat")
    }
  }

  const handleStopExtract = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/bot/stop_extract', { method: 'POST' })
      fetchStatus()
    } catch {
      alert("Erro ao conectar com o servidor.")
    }
  }

  const handleStart = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/bot/start', { method: 'POST' })
      fetchStatus()
    } catch {
      alert("Erro ao conectar com o servidor. O backend Python está rodando?")
    }
  }

  const handleStop = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/bot/stop', { method: 'POST' })
      fetchStatus()
    } catch {
      alert("Erro ao conectar com o servidor.")
    }
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
             <div className="input-group">
                <input className="modern-input" placeholder="Nome do Estabelecimento" value={newLead.nome} onChange={(e) => setNewLead({...newLead, nome: e.target.value})} />
                <input className="modern-input" placeholder="Telefone (+55)" value={newLead.telefone} onChange={(e) => setNewLead({...newLead, telefone: e.target.value})} />
                <input className="modern-input" placeholder="Cidade/Região" value={newLead.cidade} onChange={(e) => setNewLead({...newLead, cidade: e.target.value})} />
                <label className="checkbox-label">
                  <input type="checkbox" className="modern-checkbox" checked={newLead.tem_site} onChange={(e) => setNewLead({...newLead, tem_site: e.target.checked})} />
                  Este lead possui algum site atualmente?
                </label>
                {addError && (
                  <div style={{color: '#f87171', fontSize: '0.85rem', padding: '8px 12px', background: 'rgba(248,113,113,0.1)', borderRadius: '6px', border: '1px solid rgba(248,113,113,0.3)'}}>
                    {addError}
                  </div>
                )}
                <button type="button" onClick={handleAddLead} className="btn btn-accent">Adicionar Lead à Fila</button>
             </div>
          </div>

          <div className="panel-card">
             <h3>📍 Extrator Automático (Google Maps)</h3>
             <p className="panel-desc">Digite um nicho e região. O robô vai varrer o Google Maps de forma invisível e importar os contatos direto para a fila principal.</p>
             <div className="input-group">
                <input className="modern-input" placeholder="Ex: Clínicas Odontológicas em São Paulo" value={extractQuery} onChange={(e) => setExtractQuery(e.target.value)} disabled={botStatus.is_extracting} />
                <button type="button" onClick={handleExtract} className="btn" style={{backgroundColor: '#10b981', color: '#fff'}} disabled={botStatus.is_extracting}>
                    {botStatus.is_extracting ? 'Mapeando...' : 'Iniciar Mapeamento'}
                </button>
                {botStatus.is_extracting && (
                  <button type="button" onClick={handleStopExtract} className="btn btn-danger">Parar</button>
                )}
             </div>
          </div>

        </div>

        <div className="right-panel">
          <div className="panel-card full-height">
            <div className="table-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                    <h2>📋 Fila Principal ({leads.length})</h2>
                    <button onClick={fetchLeads} className="btn-icon" title="Atualizar Tabela">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                    </button>
                </div>
                {leads.length > 0 && (
                    <button onClick={handleClearQueue} className="btn btn-danger" style={{padding: '6px 14px', fontSize: '12px'}}>
                        Esvaziar Toda a Fila
                    </button>
                )}
            </div>
            
            <div className="table-wrapper">
              <table className="leads-table">
                <thead>
                  <tr>
                    <th>Empresa</th>
                    <th>Telefone</th>
                    <th>Qualificação (Radar)</th>
                    <th>Condição Tática</th>
                    <th>Status Processo</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(lead => (
                    <tr key={lead.id}>
                      <td className="main-col">{lead.nome}<br/><span style={{fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 400}}>{lead.cidade}</span></td>
                      <td className="sec-col">{lead.telefone.replace(/(\d{2})(\d{2})(\d{5})(\d{4})/, '+$1 $2 $3-$4')}</td>
                      <td>
                        <div style={{display: 'flex', flexDirection: 'column', gap: '4px'}}>
                           <span style={{fontSize: '0.85rem'}}>{lead.avaliacao || 'Sem Avaliação'}</span>
                           {lead.instagram ? (
                             <a href={lead.instagram} target="_blank" rel="noreferrer" style={{color: '#ec4899', fontSize: '0.75rem', textDecoration: 'none'}}>Ver Instagram</a>
                           ) : (
                             <span style={{color: '#a1a1aa', fontSize: '0.75rem'}}>Sem Instagram</span>
                           )}
                        </div>
                      </td>
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
                         <div style={{display: 'flex', gap: '8px'}}>
                           {lead.status_disparo !== 'PENDENTE' && (
                             <button className="btn-icon" title="Tentar Novamente (Voltar para a Fila)" onClick={()=>handleResetStatus(lead.id)}>
                               🔄
                             </button>
                           )}
                           <button className="btn-remove" title="Excluir Definitivamente" onClick={()=>handleDelete(lead.id)}>✕</button>
                         </div>
                      </td>
                    </tr>
                  ))}
                  {leads.length === 0 && (
                      <tr><td colSpan={6} style={{textAlign:'center', padding: '40px', color: '#71717a'}}>A fila de prospects está vazia. Insira novos alvos manualmente para começar.</td></tr>
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
