
import RaceScene from "./components/RaceScene";
import { useEffect, useState } from "react";
import {
  Activity, BrainCircuit, Gauge, Flag, Zap, Radio,
  Timer, ChevronRight, Send, RefreshCw, CircleDot,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, AreaChart, Area,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

const paceData = [
  { lap: 10, ham: 95.1, ver: 95.4 },
  { lap: 15, ham: 94.8, ver: 95.0 },
  { lap: 20, ham: 94.4, ver: 94.7 },
  { lap: 25, ham: 94.6, ver: 94.5 },
  { lap: 30, ham: 94.2, ver: 94.6 },
  { lap: 35, ham: 94.5, ver: 94.3 },
  { lap: 40, ham: 94.1, ver: 94.4 },
  { lap: 45, ham: 94.3, ver: 94.2 },
  { lap: 50, ham: 94.0, ver: 94.2 },
];

const tyreData = Array.from({ length: 11 }, (_, i) => ({
  lap: i * 5,
  soft: Math.min(100, 100 - i * 5.1),
  medium: Math.min(100, 96 - i * 3.1),
}));

function Panel({ title, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-title">
        <span>{title}</span>
        <span className="panel-dots">â€¢â€¢â€¢</span>
      </div>
      {children}
    </section>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [driverA, setDriverA] = useState("HAM");
  const [driverB, setDriverB] = useState("VER");
  const [apiStatus, setApiStatus] = useState("CHECKING");

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => {
        if (!r.ok) throw new Error("API unavailable");
        return r.json();
      })
      .then(() => setApiStatus("CONNECTED"))
      .catch(() => setApiStatus("OFFLINE"));
  }, []);

  async function askApex(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setAnswer("");
    try {
      const response = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      setAnswer(data.answer);
    } catch (err) {
      setAnswer(`Unable to reach Apex API: ${err.message}. Check FastAPI on port 8000.`);
    } finally {
      setLoading(false);
    }
  }

  async function compareDrivers(e) {
    e?.preventDefault();
    setComparison(null);
    try {
      const response = await fetch(`${API}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ driver_a: driverA, driver_b: driverB }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(data.detail || data));
      setComparison(data);
    } catch (err) {
      setComparison({ error: err.message });
    }
  }

  useEffect(() => {
    compareDrivers();
  }, []);

  const gap = comparison?.mean_gap_seconds;
  const gapText = Number.isFinite(gap)
    ? `${gap > 0 ? "+" : ""}${gap.toFixed(3)} s`
    : "â€”";

  return (
    <div className="dashboard">
      <header className="top-nav">
        <div className="logo-mark"><Flag size={23} /></div>
        <div className="logo-type"><strong>APEX</strong><span>INTELLIGENCE AI</span></div>
        <nav>
          <a href="#overview">Overview</a>
          <a href="#analytics">Race Analytics</a>
          <a href="#copilot">AI Copilot</a>
        </nav>
        <div className={`connection ${apiStatus === "CONNECTED" ? "online" : "offline"}`}>
          <span /> {apiStatus === "CONNECTED" ? "API CONNECTED" : apiStatus}
        </div>
      </header>

      <div className="session-strip">
        <div className="session-brand"><span className="f1-mark">APEX //</span> RACE DATA & INTELLIGENCE</div>
        <div>SESSION: <b>2024 BRITISH GP</b></div>
        <div>CIRCUIT: <b>SILVERSTONE</b></div>
        <div className="historical-tag"><CircleDot size={10} /> HISTORICAL DATA</div>
      </div>

      <main id="overview" className="command-grid">
        <aside className="left-column">
          <Panel title="DRIVER PACE MONITOR">
            <div className="driver-row">
              <span className="driver-stripe ham" />
              <div><b>Lewis Hamilton</b><small>HAM Â· Mercedes</small></div>
              <strong>{comparison?.HAM?.mean_lap_seconds?.toFixed(3) ?? "â€”"}<small>s</small></strong>
            </div>
            <div className="driver-row">
              <span className="driver-stripe ver" />
              <div><b>Max Verstappen</b><small>VER Â· Red Bull</small></div>
              <strong>{comparison?.VER?.mean_lap_seconds?.toFixed(3) ?? "â€”"}<small>s</small></strong>
            </div>
            <div className="small-note">Mean recorded lap duration Â· seconds</div>
          </Panel>

          <Panel title="LAP TIME TREND">
            <div className="chart-box small-chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={paceData}>
                  <CartesianGrid stroke="#282d35" strokeDasharray="3 3" />
                  <XAxis dataKey="lap" stroke="#7e8794" tick={{ fontSize: 9 }} />
                  <YAxis domain={["dataMin - 0.3", "dataMax + 0.3"]} stroke="#7e8794" tick={{ fontSize: 9 }} />
                  <Tooltip contentStyle={{ background: "#11151b", border: "1px solid #373d47" }} />
                  <Line dataKey="ham" name="HAM" stroke="#ff4b52" dot={false} strokeWidth={2} />
                  <Line dataKey="ver" name="VER" stroke="#dce2e9" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="legend"><span className="red-dot" /> HAM <span className="white-dot" /> VER</div>
          </Panel>

          <Panel title="DATA INTEGRITY">
            <div className="integrity-stat"><Activity size={17} /><span>Valid lap records</span><b>914</b></div>
            <div className="integrity-stat"><Timer size={17} /><span>Drivers compared</span><b>2</b></div>
            <p className="small-note">Source: OpenF1 Â· 2024 British GP race session</p>
          </Panel>
        </aside>

        <section className="center-column">

         <RaceScene />


          <Panel title="RACE INTELLIGENCE COPILOT" className="copilot-panel" >
            <div className="copilot-intro"><BrainCircuit size={22} /><div><b>Ask Apex</b><small>Ask about F1 strategy, race context, or driver pace</small></div></div>
            <div className="quick-questions">
              {[
                "How does an undercut work in Formula 1?",
                "Compare Hamilton and Verstappen at Silverstone",
                "How do safety cars affect strategy?",
              ].map((q) => <button key={q} onClick={() => setQuestion(q)}>{q}<ChevronRight size={13} /></button>)}
            </div>
            <form className="ask-form" onSubmit={askApex}>
              <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about tyre strategy, lap pace, race conditions..." />
              <button disabled={loading || !question.trim()}><Send size={15} /> {loading ? "Thinking" : "Ask"}</button>
            </form>
            {answer && <div className="answer-box"><div className="answer-label"><BrainCircuit size={13} /> APEX ANALYSIS</div><p>{answer}</p></div>}
          </Panel>
        </section>

        <aside className="right-column" id="analytics">
          <Panel title="TYRE DEGRADATION MODEL">
            <div className="model-label">ILLUSTRATIVE TREND Â· NOT A FITTED MODEL</div>
            <div className="chart-box tyre-chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={tyreData}>
                  <CartesianGrid stroke="#282d35" strokeDasharray="3 3" />
                  <XAxis dataKey="lap" stroke="#7e8794" tick={{ fontSize: 9 }} />
                  <YAxis stroke="#7e8794" tick={{ fontSize: 9 }} />
                  <Tooltip contentStyle={{ background: "#11151b", border: "1px solid #373d47" }} />
                  <Area type="monotone" dataKey="soft" name="Soft index" stroke="#ff4b52" fill="#ff4b52" fillOpacity={0.12} />
                  <Area type="monotone" dataKey="medium" name="Medium index" stroke="#dce2e9" fill="#dce2e9" fillOpacity={0.06} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <p className="small-note">Illustrative curves only. Real tyre degradation requires stint and tyre data.</p>
          </Panel>

          <Panel title="DRIVER COMPARISON">
            <form className="compare-form" onSubmit={compareDrivers}>
              <label>DRIVER A<select value={driverA} onChange={(e) => setDriverA(e.target.value)}><option value="HAM">HAM Â· Hamilton</option><option value="VER">VER Â· Verstappen</option></select></label>
              <label>DRIVER B<select value={driverB} onChange={(e) => setDriverB(e.target.value)}><option value="VER">VER Â· Verstappen</option><option value="HAM">HAM Â· Hamilton</option></select></label>
              <button type="submit"><RefreshCw size={13} /> Compare drivers</button>
            </form>
            {comparison?.error ? <p className="error-text">{comparison.error}</p> : comparison && (
              <div className="comparison-result">
                <div><span>Mean gap (A âˆ’ B)</span><b>{gapText}</b></div>
                <small>{driverA === driverB ? "Choose two different drivers for a meaningful comparison." : gap < 0 ? `${driverA} has the lower mean recorded lap time.` : gap > 0 ? `${driverB} has the lower mean recorded lap time.` : "Both means are equal."}</small>
              </div>
            )}
          </Panel>

          <Panel title="ANALYSIS NOTES">
            <div className="note-line"><Zap size={15} /><span>Lower mean lap time means a lower recorded average.</span></div>
            <div className="note-line"><Activity size={15} /><span>Traffic, tyres, pit stops, and safety cars affect comparisons.</span></div>
            <div className="note-line"><Gauge size={15} /><span>Historical session data; not a live race feed.</span></div>
          </Panel>
        </aside>
      </main>

      <footer className="footer"><span>APEX INTELLIGENCE AI Â· F1 ANALYTICS</span><span>LANGGRAPH Â· RAG Â· OLLAMA Â· FASTAPI</span></footer>
    </div>
  );
}

export default App;
