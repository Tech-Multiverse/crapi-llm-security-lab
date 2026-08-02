import { useState } from 'react';

function Chat() {
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Ask the crAPI chatbot anything. It has access to crAPI tools via LangGraph + Ollama.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setMessages((m) => [...m, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/chatbot/genai/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((m) => [
        ...m,
        { role: 'bot', text: data.response || JSON.stringify(data, null, 2) },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat card">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <strong>{m.role}:</strong>
            <pre>{m.text}</pre>
          </div>
        ))}
        {loading && <div className="message system">typing…</div>}
      </div>
      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask the chatbot something..."
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default Chat;
