import { useState } from 'react';

const PRESETS = [
  { name: 'Health check', method: 'GET', path: '/identity/api/auth/jwks.json', body: '' },
  { name: 'Login (admin)', method: 'POST', path: '/identity/api/auth/login', body: JSON.stringify({ email: 'admin@example.com', password: 'Admin!123' }, null, 2) },
  { name: 'List products', method: 'GET', path: '/workshop/api/shop/products', body: '' },
  { name: 'Contact mechanic (SSRF)', method: 'POST', path: '/workshop/api/merchant/contact_mechanic', body: JSON.stringify({ mechanic_api: 'http://www.google.com/' }, null, 2) },
  { name: 'Validate coupon (NoSQL)', method: 'POST', path: '/community/api/v2/coupon/validate-coupon', body: JSON.stringify({ coupon_code: { $ne: null } }, null, 2) },
];

function ApiExplorer() {
  const [method, setMethod] = useState('GET');
  const [path, setPath] = useState('/identity/api/auth/jwks.json');
  const [body, setBody] = useState('');
  const [headers, setHeaders] = useState(JSON.stringify({ 'Content-Type': 'application/json' }, null, 2));
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const send = async () => {
    setLoading(true);
    setResponse('');
    setStatus('');
    try {
      const opts = { method, headers: JSON.parse(headers || '{}') };
      if (method !== 'GET' && method !== 'HEAD' && body.trim()) {
        opts.body = body;
      }
      const res = await fetch(path, opts);
      const text = await res.text();
      setStatus(`${res.status} ${res.statusText}`);
      setResponse(text);
    } catch (err) {
      setStatus('Error');
      setResponse(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (p) => {
    setMethod(p.method);
    setPath(p.path);
    setBody(p.body);
  };

  return (
    <div className="api-explorer card">
      <h2>API Explorer</h2>
      <div className="presets">
        {PRESETS.map((p) => (
          <button key={p.name} onClick={() => loadPreset(p)}>
            {p.name}
          </button>
        ))}
      </div>

      <div className="request-row">
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="/identity/api/auth/jwks.json" />
        <button onClick={send} disabled={loading}>
          {loading ? 'Sending…' : 'Send'}
        </button>
      </div>

      <label>Headers</label>
      <textarea value={headers} onChange={(e) => setHeaders(e.target.value)} rows={3} />

      <label>Body</label>
      <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={6} />

      <div className="response">
        <strong>Status:</strong> {status}
        <pre>{response}</pre>
      </div>
    </div>
  );
}

export default ApiExplorer;
