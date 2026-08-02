import { useState } from 'react';
import Chat from './components/Chat';
import ApiExplorer from './components/ApiExplorer';
import Scenarios from './components/Scenarios';

function App() {
  const [tab, setTab] = useState('home');

  return (
    <div className="app">
      <header className="header">
        <h1>crAPI-LLM Security Lab</h1>
        <nav className="nav">
          <button className={tab === 'home' ? 'active' : ''} onClick={() => setTab('home')}>Home</button>
          <button className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>Chatbot</button>
          <button className={tab === 'api' ? 'active' : ''} onClick={() => setTab('api')}>API Explorer</button>
          <button className={tab === 'scenarios' ? 'active' : ''} onClick={() => setTab('scenarios')}>Scenarios</button>
        </nav>
      </header>

      <main className="main">
        {tab === 'home' && <Home />}
        {tab === 'chat' && <Chat />}
        {tab === 'api' && <ApiExplorer />}
        {tab === 'scenarios' && <Scenarios />}
      </main>
    </div>
  );
}

function Home() {
  return (
    <div className="card">
      <h2>Welcome</h2>
      <p>
        This is a hands-on lab for API security, LLM application security, and
        agentic AI attacks. Use the tabs above to:
      </p>
      <ul>
        <li><strong>Chatbot</strong> — talk to crAPI's LangGraph + Ollama chatbot.</li>
        <li><strong>API Explorer</strong> — send requests directly to crAPI endpoints.</li>
        <li><strong>Scenarios</strong> — replay attack and defense demos with one click.</li>
      </ul>
      <p>
        Everything runs locally. The chatbot and agent talk to Ollama, not a
        third-party LLM API.
      </p>
    </div>
  );
}

export default App;
