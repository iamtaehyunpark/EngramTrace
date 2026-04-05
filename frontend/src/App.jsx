import { useState, useRef, useEffect } from 'react';
import './App.css';

function DataInspector() {
  const [sysState, setSysState] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await fetch('/state');
        const data = await response.json();
        if(!response.ok || data.error) throw new Error(data.error || "Failed to parse API states");
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
    <div className="data-view">
      <div className="data-panel">
        <h3>1. Active Engram Trace (Ecphory Working Page)</h3>
        <p><i>The isolated vectors dynamically serving as the short-term context anchor locally:</i></p>
        <pre>{JSON.stringify(sysState.engram_trace, null, 2)}</pre>
      </div>
      
      <div className="data-panel">
        <h3>2. Temporal Buffer (Stage Log)</h3>
        <p><i>The continuous conversational loop dictating drift threshold continuity triggers:</i></p>
        <pre>{JSON.stringify(sysState.stage_log, null, 2)}</pre>
      </div>

      <div className="data-panel">
        <h3>3. Long-Term HTML Structure (Knowledge Base)</h3>
        <p><i>The final synthesized DOM block architecture resting in physical storage natively:</i></p>
        <div 
          className="kb-rendered-preview" 
          dangerouslySetInnerHTML={{ __html: sysState.knowledge_base }} 
        />
      </div>
    </div>
  );
}

function App() {
  const [currentView, setCurrentView] = useState('chat'); // 'chat' or 'data'
  
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverLogs, setServerLogs] = useState([]);
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
      } catch (err) {}
    };
    fetchHistory();
  }, []);

  const handleWipeMemory = async () => {
    if (!window.confirm("Are you sure you want to completely wipe all logs, vectors, and the Knowledge Base?")) return;
    try {
      const res = await fetch('/memory', { method: 'DELETE' });
      if (res.ok) {
        setMessages([{ role: 'system', text: '[System Engine Memory Wiped. Virtual Graph matrix successfully initialized...]' }]);
        setServerLogs([]);
        if (currentView === 'data') {
           window.location.reload();
        }
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

    // Push User Command
    setMessages(prev => [...prev, { role: 'user', text: text }]);
    setInputVal('');
    setServerLogs([]);
    setIsLoading(true);

    try {
      // Clear logs on backend before start natively ensuring accurate reading frames
      await fetch('/logs', { method: 'DELETE' });
    } catch (e) { /* ignore cleanup errors */ }

    // Start fetching logs smoothly tracking updates globally over intervals!
    const pollLogs = setInterval(async () => {
      try {
        const res = await fetch('/logs');
        if (res.ok) {
          const data = await res.json();
          setServerLogs(data.logs || []);
        }
      } catch (err) {
        // fail silently avoiding console span bloats
      }
    }, 400);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: text })
      });

      const data = await response.json();
      
      // Conclude log polling correctly
      clearInterval(pollLogs);
      
      if(response.ok) {
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
        <h2>EngramTrace Orchestrator</h2>
        <div className="nav-buttons">
          <button 
            className="nav-btn wipe-btn"
            style={{ backgroundColor: '#ff4444', color: 'white', marginRight: '1rem' }}
            onClick={handleWipeMemory}
          >
            Clear Total Memory
          </button>
          
          <button 
            className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            Chat Console
          </button>
          <button 
            className={`nav-btn ${currentView === 'data' ? 'active' : ''}`}
            onClick={() => setCurrentView('data')}
          >
            Data Inspector
          </button>
        </div>
      </div>
      
      {currentView === 'data' ? (
        <DataInspector />
      ) : (
        <>
          <div className="chat-box">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${
                msg.role === 'user' ? 'user-msg' : 
                msg.role === 'error' ? 'error-msg' : 'system-msg'
              }`}>
                <b>{msg.role === 'user' ? 'COMMAND:' : msg.role === 'error' ? 'ERROR:' : 'ENGRAM:'}</b>
                <br />
                {msg.text.split('\\n').map((line, i) => (
                  <span key={i}>{line}<br/></span>
                ))}
              </div>
            ))}
            {isLoading && (
              <div className="message loading-msg">
                <i>Process Output Stream:</i><br/>
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
                // Submit on Enter (without Shift)
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Send a multi-line query to the Engram Graph... (Shift+Enter for newline)" 
              disabled={isLoading}
              autoComplete="off"
              rows={3}
            />
            <button onClick={handleSubmit} disabled={isLoading || !inputVal.trim()}>
              Execute
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
