import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const METRICS = [
  { label: "Precision (rules)", value: "0.83" },
  { label: "Recall (rules)", value: "0.38" },
  { label: "F1 (rules)", value: "0.53" },
  { label: "F1 (ML)", value: "0.38" },
];

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
    </div>
  );
}

function EvaluateForm({ onResult }) {
  const [form, setForm] = useState({
    merchant_id: "M001",
    txn_count: "",
    avg_amount: "",
    away_ratio: "",
    merchant_avg_txn_count: "40",
    merchant_std_txn_count: "8",
    merchant_avg_amount: "1200",
    merchant_std_amount: "150",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (key) => (e) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async () => {
    setError("");
    if (!form.merchant_id || !form.txn_count || !form.avg_amount || form.away_ratio === "") {
      setError("Fill in merchant ID, transaction count, average amount, and away ratio.");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        merchant_id: form.merchant_id,
        window_start: new Date().toISOString(),
        txn_count: Number(form.txn_count),
        avg_amount: Number(form.avg_amount),
        away_ratio: Number(form.away_ratio),
        merchant_avg_txn_count: Number(form.merchant_avg_txn_count),
        merchant_std_txn_count: Number(form.merchant_std_txn_count),
        merchant_avg_amount: Number(form.merchant_avg_amount),
        merchant_std_amount: Number(form.merchant_std_amount),
      };
      const res = await fetch(`${API_BASE}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();
      onResult({ ...data, merchant_id: form.merchant_id });
    } catch (err) {
      setError("Couldn't reach the API. Is it running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <p className="card-title">Test a transaction window</p>
      <div className="form-grid">
        <input placeholder="Merchant ID (e.g. M001)" value={form.merchant_id} onChange={update("merchant_id")} />
        <input placeholder="Transaction count" value={form.txn_count} onChange={update("txn_count")} />
        <input placeholder="Average amount" value={form.avg_amount} onChange={update("avg_amount")} />
        <input placeholder="Away-city ratio (0-1)" value={form.away_ratio} onChange={update("away_ratio")} />
      </div>
      {error && <p className="form-error">{error}</p>}
      <button className="primary-btn" onClick={submit} disabled={loading}>
        {loading ? "Evaluating..." : "Evaluate"}
      </button>
    </div>
  );
}

function ResultPanel({ result }) {
  if (!result) return null;
  return (
    <div className="card result-panel result-enter">
      <div className="result-row">
        <span className={`badge ${result.flagged ? "badge-danger" : "badge-success"}`}>
          {result.flagged ? "Flagged" : "Normal"}
        </span>
        <span className="confidence">confidence: {result.confidence}</span>
      </div>
      <ul className="reasons">
        {result.reasons.map((r, i) => (
          <li key={i} style={{ animationDelay: `${i * 80}ms` }} className="reason-item">
            {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

function AuditLog() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/audit-log?limit=15`);
      const data = await res.json();
      setEntries(data.reverse());
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="card">
      <div className="audit-header">
        <p className="card-title">Audit log</p>
        <button className="ghost-btn" onClick={load}>Refresh</button>
      </div>
      {loading ? (
        <p className="muted">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="muted">No entries yet — evaluate a window above.</p>
      ) : (
        <table className="audit-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Merchant</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={i} className="audit-row" style={{ animationDelay: `${i * 40}ms` }}>
                <td>{new Date(e.timestamp).toLocaleTimeString()}</td>
                <td>{e.input.merchant_id}</td>
                <td className={e.result.flagged ? "text-danger" : "text-success"}>
                  {e.result.flagged ? "Flagged" : "Normal"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function App() {
  const [result, setResult] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleResult = (data) => {
    setResult(data);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app">
      <h1 className="title">Fraud spike detector</h1>
      <p className="subtitle">Rule-based + ML anomaly detection for transaction spikes</p>

      <div className="stats-grid">
        {METRICS.map((m) => (
          <StatCard key={m.label} {...m} />
        ))}
      </div>

      <EvaluateForm onResult={handleResult} />
      <ResultPanel result={result} />
      <AuditLog key={refreshKey} />
    </div>
  );
}
