import { useState, useRef, useEffect } from 'react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import KBStudio from './KBStudio';

function LogsView() {
  const [sysState, setSysState] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await fetch('/state');
        const data = await response.json();
        if (!response.ok || data.error) throw new Error(data.error || "Failed to parse API states");
        setSysState(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchState();
  }, []);

  if (error) return <div className="error-msg"><b>CRITICAL:</b> Unable to connect to Data Engine ({error})</div>;
  if (!sysState) return <div className="loading-msg">Connecting to Orchestrator matrices...</div>;

  return (
    <div className="logs-view">
      <div className="data-panel">
        <h3>Active Engram Trace (Ecphory Working Page)</h3>
        <pre>{JSON.stringify(sysState.engram_trace, null, 2)}</pre>
      </div>

      <div className="data-panel">
        <h3>Temporal Buffer (Stage Log)</h3>
        <pre>{JSON.stringify(sysState.stage_log, null, 2)}</pre>
      </div>

      <div className="data-panel">
        <h3>Session Log (Permanent History)</h3>
        <pre>{JSON.stringify(sysState.session_log, null, 2)}</pre>
      </div>
    </div>
  );
}

function App() {
  const [currentView, setCurrentView] = useState('chat'); // 'chat' | 'kb' | 'logs'

  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [thresholdVal, setThresholdVal] = useState(0.90);
  const [semanticThresholdVal, setSemanticThresholdVal] = useState(0.70);
  const [noSearchVal, setNoSearchVal] = useState(false);
  const [noMemorizeVal, setNoMemorizeVal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [serverLogs, setServerLogs] = useState([]);
  const [showWipeDropdown, setShowWipeDropdown] = useState(false);
  const [wipeOptions, setWipeOptions] = useState({ knowledge_base: true, session_log: true, stage_log: true, current_trace: true });
  const chatEndRef = useRef(null);

  // Rehydrate historic dialogue memory array organically!
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/state');
        if (res.ok) {
          const data = await res.json();
          if (data.session_log && data.session_log.length > 0) {
            const rehydrated = [];
            data.session_log.forEach(log => {
              rehydrated.push({ role: 'user', text: log.query });
              rehydrated.push({ role: 'bot', text: log.response });
            });
            setMessages(rehydrated);
          } else {
            setMessages([{ role: 'system', text: '[System Engine Online. Virtual Graph matrix successfully initialized...]' }]);
          }
        }
      } catch (err) { }
    };
    fetchHistory();
  }, []);

  const handleWipeMemory = async () => {
    if (!window.confirm("Are you sure you want to selectively wipe the chosen memory sectors?")) return;
    try {
      const res = await fetch('/memory', { 
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(wipeOptions)
      });
      if (res.ok) {
        setMessages([{ role: 'system', text: '[System Engine Memory selectively Wiped. Matrix re-initialized.]' }]);
        setServerLogs([]);
        setShowWipeDropdown(false);
        if (currentView !== 'chat') {
          window.location.reload();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleForceDayChange = async () => {
    if (!window.confirm("Are you sure you want to force a day transition? This will trigger total atomizer compression!")) return;
    try {
      const res = await fetch('/day-change', { method: 'POST' });
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'system', text: '[System Control: Day Cycle Advanced. Commencing Atomizer compression sequence...]' }]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (currentView === 'chat') scrollToBottom();
  }, [messages, isLoading, serverLogs, currentView]);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const text = inputVal.trim();
    if (!text) return;

    setMessages(prev => [...prev, { role: 'user', text: text }]);
    setInputVal('');
    setServerLogs([]);
    setIsLoading(true);

    try {
      await fetch('/logs', { method: 'DELETE' });
    } catch (e) { /* ignore cleanup errors */ }

    const pollLogs = setInterval(async () => {
      try {
        const res = await fetch('/logs');
        if (res.ok) {
          const data = await res.json();
          setServerLogs(data.logs || []);
        }
      } catch (err) { }
    }, 400);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, threshold: Number(thresholdVal), semantic_threshold: Number(semanticThresholdVal), no_search: noSearchVal, no_memorize: noMemorizeVal })
      });

      const data = await response.json();
      clearInterval(pollLogs);

      if (response.ok) {
        setMessages(prev => [...prev, { role: 'bot', text: data.response }]);
      } else {
        throw new Error(data.response || 'Network error');
      }
    } catch (err) {
      clearInterval(pollLogs);
      setMessages(prev => [...prev, { role: 'error', text: 'CRITICAL: Extrapolator Bridge Dropped (API check required)' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="header-nav">
        <h2>EngramTrace</h2>
        <div className="nav-buttons">
          <div className="threshold-group">
            <label>Drift</label>
            <input
              type="number" step="0.01" min="0.0" max="1.0"
              value={thresholdVal}
              onChange={e => setThresholdVal(e.target.value)}
            />
          </div>
          <div className="threshold-group">
            <label>Search</label>
            <input
              type="number" step="0.01" min="0.0" max="1.0"
              value={semanticThresholdVal}
              onChange={e => setSemanticThresholdVal(e.target.value)}
            />
          </div>
          <div style={{ position: 'relative' }}>
            <button className="nav-btn danger-btn" onClick={() => setShowWipeDropdown(!showWipeDropdown)}>Wipe &#9662;</button>
            {showWipeDropdown && (
              <div style={{ position: 'absolute', top: '100%', left: 0, backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', padding: '0.8rem', borderRadius: '4px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '0.5rem', minWidth: '180px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', marginBottom: '0.2rem' }}>Wipe Selector</span>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <input type="checkbox" checked={wipeOptions.knowledge_base} onChange={e => setWipeOptions(p => ({ ...p, knowledge_base: e.target.checked }))} /> Knowledge Base (KB)
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <input type="checkbox" checked={wipeOptions.session_log} onChange={e => setWipeOptions(p => ({ ...p, session_log: e.target.checked }))} /> Session Logs
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <input type="checkbox" checked={wipeOptions.stage_log} onChange={e => setWipeOptions(p => ({ ...p, stage_log: e.target.checked }))} /> Stage Logs
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <input type="checkbox" checked={wipeOptions.current_trace} onChange={e => setWipeOptions(p => ({ ...p, current_trace: e.target.checked }))} /> Current Trace
                </label>
                <button className="danger-btn" style={{ marginTop: '0.5rem', padding: '0.4rem' }} onClick={handleWipeMemory}>Confirm Wipe</button>
              </div>
            )}
          </div>
          <button className="nav-btn warning-btn" onClick={handleForceDayChange}>Day Change</button>
          <div className="nav-divider" />
          <button
            className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >Chat</button>
          <button
            className={`nav-btn ${currentView === 'kb' ? 'active' : ''}`}
            onClick={() => setCurrentView('kb')}
          >KB Studio</button>
          <button
            className={`nav-btn ${currentView === 'logs' ? 'active' : ''}`}
            onClick={() => setCurrentView('logs')}
          >Logs</button>
        </div>
      </div>

      {currentView === 'kb' && <KBStudio />}
      {currentView === 'logs' && <LogsView />}
      {currentView === 'chat' && (
        <>
          <div className="chat-box">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role === 'user' ? 'user-msg' :
                msg.role === 'error' ? 'error-msg' : 'system-msg'
                }`}>
                <b>{msg.role === 'user' ? 'COMMAND:' : msg.role === 'error' ? 'ERROR:' : 'ENGRAM:'}</b>
                <div className="markdown-content">
                  <ReactMarkdown>{typeof msg.text === 'string' ? msg.text : JSON.stringify(msg.text)}</ReactMarkdown>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message loading-msg">
                <i>Process Output Stream:</i><br />
                {serverLogs.length === 0 ? "Evaluating topological drift and checking vectors..." :
                  serverLogs.map((log, i) => <div key={i}>&gt; {log}</div>)
                }
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="input-area">
            <textarea
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Send a query to the Engram Graph... (Shift+Enter for newline)"
              disabled={isLoading}
              autoComplete="off"
              rows={3}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end', justifyContent: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={noSearchVal}
                  onChange={e => setNoSearchVal(e.target.checked)}
                />
                Restrict to current trace
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={noMemorizeVal}
                  onChange={e => setNoMemorizeVal(e.target.checked)}
                />
                Do not memorize
              </label>
              <button onClick={handleSubmit} disabled={isLoading || !inputVal.trim()} style={{ height: '100%' }}>
                Execute
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
