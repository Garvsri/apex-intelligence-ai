import RaceScene from "./components/RaceScene";
import { useEffect, useState } from "react";
import {
  Activity, BrainCircuit, Gauge, Flag, Zap,
  Timer, ChevronRight, Send, RefreshCw, CircleDot,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, AreaChart, Area,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

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
      </div>
      {children}
    </section>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [availableDrivers, setAvailableDrivers] = useState([]);
  const [, setDriversLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [apiStatus, setApiStatus] = useState("CHECKING");
  const [paceData, setPaceData] = useState([]);
  const [paceLoading, setPaceLoading] = useState(true);
  const [raceOptions, setRaceOptions] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(2024);
  const [selectedRace, setSelectedRace] = useState("British Grand Prix");
  const [selectedDriverA, setSelectedDriverA] = useState("HAM");
  const [selectedDriverB, setSelectedDriverB] = useState("VER");
  const [paceError, setPaceError] = useState("");
  const [tyreStints, setTyreStints] = useState([]);
  const [tyreLoading, setTyreLoading] = useState(false);
  const [tyreError, setTyreError] = useState("");
  const [selectedTyreDriver, setSelectedTyreDriver] = useState("ALL");

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => {
        if (!r.ok) throw new Error("API unavailable");
        return r.json();
      })
      .then(() => setApiStatus("CONNECTED"))
      .catch(() => setApiStatus("OFFLINE"));
  }, []);

useEffect(() => {
  let cancelled = false;

  async function loadLapTimes() {
    setPaceLoading(true);
    setPaceError("");

    try {
      const response = await fetch(
        `${API}/race/${selectedSeason}/${encodeURIComponent(
          selectedRace
        )}/laps?drivers=${selectedDriverA},${selectedDriverB}`
      );

      if (!response.ok) {
        throw new Error("Could not load race lap times.");
      }

      const result = await response.json();

      if (!cancelled) {
        setPaceData(result.laps ?? []);
      }
    } catch (error) {
      if (!cancelled) {
        setPaceError(error.message);
      }
    } finally {
      if (!cancelled) {
        setPaceLoading(false);
      }
    }
  }

  loadLapTimes();

  return () => {
    cancelled = true;
  };
}, [selectedSeason, selectedRace, selectedDriverA, selectedDriverB]);
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

useEffect(() => {
  let cancelled = false;

  async function loadRaceOptions() {
    try {
      const response = await fetch(`${API}/races`);

      if (!response.ok) {
        throw new Error("Could not load available races.");
      }

      const result = await response.json();

      if (!cancelled) {
        setRaceOptions(result.races ?? []);

        const availableSeasons = result.seasons ?? [];

        if (availableSeasons.length > 0) {
          const initialSeason = availableSeasons.includes(2024)
            ? 2024
            : availableSeasons[0];

          setSelectedSeason(initialSeason);

          const firstRace = (result.races ?? []).find(
            (race) => race.season === initialSeason
          );

          if (firstRace) {
            setSelectedRace(firstRace.grand_prix);
          }
        }
      }
    } catch (error) {
      console.error("Race options:", error);
    }
  }

  loadRaceOptions();

  return () => {
    cancelled = true;
  };
}, []);

useEffect(() => {
  if (!selectedSeason || !selectedRace) return;

  let cancelled = false;

  async function loadDrivers() {
    setDriversLoading(true);

    try {
      const response = await fetch(
        `${API}/race/${selectedSeason}/${encodeURIComponent(selectedRace)}/drivers`
      );

      if (!response.ok) {
        throw new Error("Could not load drivers for this race.");
      }

      const result = await response.json();

      if (!cancelled) {
        const drivers = result.drivers ?? [];
        setAvailableDrivers(drivers);

        setSelectedDriverA((current) =>
          drivers.includes(current) ? current : drivers[0] ?? ""
        );

        setSelectedDriverB((current) =>
          drivers.includes(current) && current !== drivers[0]
            ? current
            : drivers.find((driver) => driver !== drivers[0]) ?? ""
        );
      }
    } catch (error) {
      if (!cancelled) {
        console.error("Driver options:", error);
        setAvailableDrivers([]);
      }
    } finally {
      if (!cancelled) {
        setDriversLoading(false);
      }
    }
  }

  loadDrivers();

  return () => {
    cancelled = true;
  };
}, [selectedSeason, selectedRace]);

useEffect(() => {
  if (!selectedSeason || !selectedRace) return;

  let cancelled = false;

  async function loadTyreStints() {
    setTyreLoading(true);
    setTyreError("");
    setTyreStints([]);

    try {
      const response = await fetch(
        `${API}/race/${selectedSeason}/${encodeURIComponent(
          selectedRace
        )}/stints`
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Could not load tyre stint data."
        );
      }

      if (!cancelled) {
        setTyreStints(result.stints ?? []);
      }
    } catch (error) {
      if (!cancelled) {
        setTyreError(error.message);
      }
    } finally {
      if (!cancelled) {
        setTyreLoading(false);
      }
    }
  }

  loadTyreStints();

  return () => {
    cancelled = true;
  };
}, [selectedSeason, selectedRace]);



async function compareDrivers(e) {
  e?.preventDefault();
  setComparison(null);

  if (selectedDriverA === selectedDriverB) {
    setComparison({
      error: "Choose two different drivers for a meaningful comparison.",
    });
    return;
  }

  try {
    const response = await fetch(
      `${API}/race/${selectedSeason}/${encodeURIComponent(
        selectedRace
      )}/laps?drivers=${encodeURIComponent(
        `${selectedDriverA},${selectedDriverB}`
      )}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Could not compare drivers for this race."
      );
    }

    const laps = data.laps ?? [];

    const getMean = (driver) => {
      const times = laps
        .map((lap) => lap[driver])
        .filter(
          (time) =>
            typeof time === "number" &&
            Number.isFinite(time) &&
            time > 0
        );

      return {
        mean_lap_seconds: times.length
          ? times.reduce((sum, time) => sum + time, 0) / times.length
          : null,
        valid_laps: times.length,
      };
    };

    const driverAStats = getMean(selectedDriverA);
    const driverBStats = getMean(selectedDriverB);

    if (
      driverAStats.mean_lap_seconds === null ||
      driverBStats.mean_lap_seconds === null
    ) {
      throw new Error(
        "Insufficient valid lap data for one or both selected drivers."
      );
    }

    setComparison({
      [selectedDriverA]: driverAStats,
      [selectedDriverB]: driverBStats,
      mean_gap_seconds:
        driverAStats.mean_lap_seconds -
        driverBStats.mean_lap_seconds,
    });
  } catch (err) {
    setComparison({ error: err.message });
  }
}

const tyreCompoundColor = (compound) => {
  const colors = {
    SOFT: "#ff4b52",
    MEDIUM: "#f4c542",
    HARD: "#e5e7eb",
    INTERMEDIATE: "#39c77a",
    WET: "#4aa3ff",
  };

  return colors[String(compound ?? "").toUpperCase()] ?? "#858b98";
};

const tyreDrivers = [
  ...new Set(tyreStints.map((stint) => stint.driver)),
].sort();

const visibleTyreStints = tyreStints.filter(
  (stint) =>
    selectedTyreDriver === "ALL" ||
    stint.driver === selectedTyreDriver
);

const totalRaceLaps = Math.max(
  1,
  ...tyreStints.map((stint) => Number(stint.end_lap) || 1)
);

const gap = comparison?.mean_gap_seconds;

const gapText = Number.isFinite(gap)
  ? `${gap > 0 ? "+" : ""}${gap.toFixed(3)} s`
  : "—";


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

<div className="race-selector-strip">
  <label>
    SEASON
    <select
      onChange={(e) => {
  const season = Number(e.target.value);
  setComparison(null);
  setSelectedSeason(season);

  const firstRace = raceOptions.find(
    (race) => race.season === season
  );

  if (firstRace) {
    setSelectedRace(firstRace.grand_prix);
  }
}}
    >
      {[...new Set(raceOptions.map((race) => race.season))]
        .sort((a, b) => b - a)
        .map((season) => (
          <option key={season} value={season}>
            {season}
          </option>
        ))}
    </select>
  </label>

  <label>
    GRAND PRIX
    <select
      value={selectedRace}
      onChange={(e) => {
  setComparison(null);
  setSelectedRace(e.target.value);
}}
    >
      {raceOptions
        .filter((race) => race.season === selectedSeason)
        .map((race) => (
          <option key={race.dataset_id} value={race.grand_prix}>
            {race.grand_prix}
          </option>
        ))}
    </select>
  </label>

  <label>
    DRIVER A
    <select
      value={selectedDriverA}
      onChange={(e) => {
  setComparison(null);
  setSelectedDriverA(e.target.value);
}}
    >
      {availableDrivers.map((driver) => (
        <option key={driver} value={driver}>
          {driver}
        </option>
      ))}
    </select>
  </label>

  <label>
    DRIVER B
    <select
      value={selectedDriverB}
      onChange={(e) => {
  setComparison(null);
  setSelectedDriverB(e.target.value);
}}
    >
      {availableDrivers.map((driver) => (
        <option key={driver} value={driver}>
          {driver}
        </option>
      ))}
    </select>
  </label>
</div>

<div className="session-strip">
  <div className="session-brand">
    <span className="f1-mark">APEX //</span> RACE DATA & INTELLIGENCE
  </div>
  <div>
    SESSION: <b>{selectedSeason} {selectedRace.toUpperCase()}</b>
  </div>
  <div className="historical-tag">
    <CircleDot size={10} /> HISTORICAL DATA
  </div>
</div>
      <main id="overview" className="command-grid">
        <aside className="left-column">

<Panel title="DRIVER PACE MONITOR">
  {[selectedDriverA, selectedDriverB].map((driver, index) => {
    const times = paceData
      .map((lap) => lap[driver])
      .filter(
        (time) => typeof time === "number" && Number.isFinite(time)
      );

    const meanLapTime = times.length
      ? times.reduce((sum, time) => sum + time, 0) / times.length
      : null;

    return (
      <div className="driver-row" key={`${index}-${driver}`}>
        <span className={`driver-stripe ${index === 0 ? "ham" : "ver"}`} />
        <div>
          <b>{driver}</b>
          <small>{index === 0 ? "Driver A" : "Driver B"}</small>
        </div>
        <strong>
          {meanLapTime !== null ? meanLapTime.toFixed(3) : "—"}
          <small>s</small>
        </strong>
      </div>
    );
  })}

  <div className="small-note">
    Mean recorded lap duration · seconds
  </div>
</Panel>



          <Panel title="LAP TIME TREND">
            {paceLoading ? (
              <p>Loading real race lap times...</p>
            ) : paceError ? (
              <p className="error-text">{paceError}</p>
            ) : (
              <>
                <div className="chart-box small-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={paceData}>
                      <CartesianGrid stroke="#282d35" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="lap"
                        stroke="#7e8794"
                        tick={{ fontSize: 9 }}
                      />
                      <YAxis
                        domain={["dataMin - 0.3", "dataMax + 0.3"]}
                        stroke="#7e8794"
                        tick={{ fontSize: 9 }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#11151b",
                          border: "1px solid #373d47",
                        }}
                      />

                      <Line
                        dataKey={selectedDriverA}
                        name={selectedDriverA}
                        stroke="#ff4b52"
                        dot={false}
                        strokeWidth={2}
                        connectNulls={false}
                      />
                      <Line
                        dataKey={selectedDriverB}
                        name={selectedDriverB}
                        stroke="#dce2e9"
                        dot={false}
                        strokeWidth={2}
                        connectNulls={false}
                      />

                    </LineChart>
                  </ResponsiveContainer>
                </div>


                  <div className="legend">
                    <span className="red-dot" /> {selectedDriverA}
                    <span className="white-dot" /> {selectedDriverB}
                  </div>

              </>
            )}
          </Panel>


          <Panel title="DATA INTEGRITY">
            <div className="integrity-stat"> <Activity size={17} /> <span>Valid lap records</span> <b>{paceData.length}</b></div>
            <div className="integrity-stat"> <Timer size={17} /> <span>Drivers selected</span> <b>{new Set([selectedDriverA, selectedDriverB]).size}</b></div>

<p className="small-note">
  Source: {selectedSeason} {selectedRace} race session
</p>

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
          
<Panel title="TYRE STRATEGY COMPARISON">
  <div className="tyre-strategy-controls">
    <label htmlFor="tyre-driver-filter">DRIVER</label>
    <select
      id="tyre-driver-filter"
      value={selectedTyreDriver}
      onChange={(e) => setSelectedTyreDriver(e.target.value)}
    >
      <option value="ALL">All drivers</option>
      {tyreDrivers.map((driver) => (
        <option key={driver} value={driver}>
          {driver}
        </option>
      ))}
    </select>
  </div>

  <div className="tyre-legend">
    {[
      ["SOFT", "#ff4b52"],
      ["MEDIUM", "#f4c542"],
      ["HARD", "#e5e7eb"],
      ["INTERMEDIATE", "#39c77a"],
      ["WET", "#4aa3ff"],
    ].map(([compound, color]) => (
      <span key={compound} className="tyre-legend-item">
        <i style={{ backgroundColor: color }} />
        {compound}
      </span>
    ))}
  </div>
{tyreLoading ? (
  <p className="small-note">Loading real tyre stint data...</p>
) : tyreError ? (
  <p className="error-text">{tyreError}</p>
) : visibleTyreStints.length === 0 ? (
  <div className="tyre-empty-state">
    <div className="tyre-empty-icon">🏁</div>

    <h3>Tyre strategy unavailable</h3>

    <p>
      Stint-level tyre data isn't available for this race yet.
      Explore the 2024 British Grand Prix to see the tyre strategy
      comparison in action.
    </p>

    <button
      className="tyre-explore-button"
      onClick={() => {
        setSelectedSeason(2024);
        setSelectedRace("British Grand Prix");
      }}
    >
      Explore supported race →
    </button>
  </div>
) : (
  <>
      
<div className="tyre-timeline">
  {Object.entries(
    visibleTyreStints.reduce((groups, stint) => {
      if (!groups[stint.driver]) {
        groups[stint.driver] = [];
      }

      groups[stint.driver].push(stint);
      return groups;
    }, {})
  ).map(([driver, driverStints]) => (
    <div className="tyre-timeline-row" key={driver}>
      <div className="tyre-driver-label">
        <b>{driver}</b>
      </div>

      <div className="tyre-track">
        {driverStints.map((stint, index) => {
          const startLap = Number(stint.start_lap);
          const endLap = Number(stint.end_lap);

          const left =
            ((Math.max(1, startLap) - 1) / totalRaceLaps) * 100;

          const width =
            (Math.max(1, endLap - startLap + 1) /
              totalRaceLaps) * 100;

          return (
            <div
              className="tyre-stint-bar"
              key={`${driver}-${stint.stint}-${index}`}
              style={{
                left: `${left}%`,
                width: `${Math.max(width, 1.5)}%`,
                backgroundColor: tyreCompoundColor(stint.compound),
              }}
              title={`${driver} · ${stint.compound ?? "Unknown"} · Laps ${stint.start_lap}–${stint.end_lap}`}
            ><span>
  {{
    SOFT: "S",
    MEDIUM: "M",
    HARD: "H",
    INTERMEDIATE: "I",
    WET: "W",
  }[String(stint.compound ?? "UNKNOWN").toUpperCase()] ?? "?"}
</span>
            </div>
          );
        })}
      </div>

      <div className="tyre-stint-laps">
        {driverStints.map((stint, index) => (
          <span key={`${driver}-laps-${index}`}>
            S{stint.stint}: L{stint.start_lap}–{stint.end_lap}
            {index < driverStints.length - 1 ? "  |  " : ""}
          </span>
        ))}
      </div>

      <div className="tyre-stint-stats">
        <span>
          {driverStints.reduce(
            (total, stint) =>
              total +
              Math.max(
                0,
                Number(stint.end_lap) - Number(stint.start_lap) + 1
              ),
            0
          )}{" "}
          recorded stint laps
        </span>
        <span>{driverStints.length} stints</span>
      </div>
    </div>
  ))}
</div>


      <p className="small-note">
        Bars represent recorded stint lap ranges. Lap ranges and
        lap-record counts can differ when data is incomplete.
        Average lap times are not adjusted for traffic, weather,
        fuel load, or safety-car periods.
      </p>
    </>
  )}
</Panel>



<Panel title="DRIVER COMPARISON">
  <div className="compare-form">
    <div className="comparison-result">
      <div>
        <span>Driver A · {selectedDriverA}</span>
        <b>
          {comparison?.[selectedDriverA]?.mean_lap_seconds != null
            ? `${comparison[selectedDriverA].mean_lap_seconds.toFixed(3)} s`
            : "—"}
        </b>
      </div>

      <div>
        <span>Driver B · {selectedDriverB}</span>
        <b>
          {comparison?.[selectedDriverB]?.mean_lap_seconds != null
            ? `${comparison[selectedDriverB].mean_lap_seconds.toFixed(3)} s`
            : "—"}
        </b>
      </div>

      <div>
        <span>Mean gap (A − B)</span>
        <b>{gapText}</b>
      </div>

      {comparison?.error && (
        <p className="error-text">{comparison.error}</p>
      )}

      {!comparison?.error && comparison && (
        <small>
          {selectedDriverA === selectedDriverB
            ? "Choose two different drivers."
            : gap < 0
              ? `${selectedDriverA} has the lower mean lap time.`
              : gap > 0
                ? `${selectedDriverB} has the lower mean lap time.`
                : "Both mean lap times are equal."}
        </small>
      )}
    </div>

    <button
      type="button"
      onClick={() => compareDrivers()}
      disabled={loading || selectedDriverA === selectedDriverB}
    >
      <RefreshCw size={13} />
      {loading ? "Comparing..." : "Compare selected drivers"}
    </button>
  </div>
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
