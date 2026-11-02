import RaceScene from "./components/RaceScene";
import { useEffect, useState } from "react";
import {
  Activity, BrainCircuit, Flag,
  Timer, ChevronRight, Send, RefreshCw, CircleDot,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

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
  const [degradationData, setDegradationData] = useState(null);
  const [degradationLoading, setDegradationLoading] = useState(false);
  const [degradationError, setDegradationError] = useState("");
  const [selectedDegradationDriver, setSelectedDegradationDriver] = useState("ALL");

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

useEffect(() => {
  if (!selectedSeason || !selectedRace) return;

  let cancelled = false;

  async function loadTyreDegradation() {
    setDegradationLoading(true);
    setDegradationError("");
    setDegradationData(null);

    try {
      const response = await fetch(
        `${API}/race/${selectedSeason}/${encodeURIComponent(
          selectedRace
        )}/tyre-degradation-v2`
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Could not load tyre degradation analysis."
        );
      }

      if (!cancelled) {
        setDegradationData(result);
      }
    } catch (error) {
      if (!cancelled) {
        setDegradationError(error.message);
      }
    } finally {
      if (!cancelled) {
        setDegradationLoading(false);
      }
    }
  }

  loadTyreDegradation();

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

const degradationStints = degradationData?.stints ?? [];
const degradationDrivers = [
  ...new Set(degradationStints.map((stint) => stint.driver).filter(Boolean)),
].sort();
const visibleDegradationStints = degradationStints.filter(
  (stint) =>
    selectedDegradationDriver === "ALL" ||
    stint.driver === selectedDegradationDriver
);

const degradationChartData = visibleDegradationStints
  .map((stint) => {
    const robust = stint.robust_degradation_seconds_per_lap;
    const linear = stint.raw_degradation_seconds_per_lap;

    const robustValue =
      robust != null && Number.isFinite(Number(robust))
        ? Number(robust)
        : null;

    const linearValue =
      linear != null && Number.isFinite(Number(linear))
        ? Number(linear)
        : null;

    return {
      label: `${stint.driver} S${stint.stint}`,
      driver: stint.driver,
      stint: stint.stint,
      compound: stint.compound,
      robust_slope: robustValue,
      linear_slope: linearValue,
    };
  })
  .filter(
    (stint) =>
      stint.robust_slope !== null ||
      stint.linear_slope !== null
  );

const formatSlope = (value) =>
  value != null && Number.isFinite(Number(value))
    ? `${Number(value) >= 0 ? "+" : ""}${Number(value).toFixed(4)} s/lap`
    : "—";

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
<Panel
  title={`TYRE DEGRADATION TREND · ${
    selectedDegradationDriver === "ALL"
      ? "ALL DRIVERS"
      : selectedDegradationDriver
  }`}
  className="left-degradation-chart-panel"
>
  <div className="tyre-strategy-controls">
    <label htmlFor="left-degradation-driver">
      DRIVER
    </label>

    <select
      id="left-degradation-driver"
      value={selectedDegradationDriver}
      onChange={(e) =>
        setSelectedDegradationDriver(e.target.value)
      }
    >
      <option value="ALL">All drivers</option>
      {degradationDrivers.map((driver) => (
        <option key={driver} value={driver}>
          {driver}
        </option>
      ))}
    </select>
  </div>

  {degradationLoading ? (
    <p className="small-note">Loading degradation trends...</p>
  ) : degradationError ? (
    <p className="error-text">{degradationError}</p>
  ) : degradationChartData.length === 0 ? (
    <p className="small-note">
      No valid regression slopes are available for this selection.
    </p>
  ) : (
    <>
      <div className="chart-box small-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={degradationChartData}
            margin={{ top: 8, right: 8, left: -18, bottom: 4 }}
          >
            <CartesianGrid
              stroke="#282d35"
              strokeDasharray="3 3"
            />

            <XAxis dataKey="label" hide />

            <YAxis
              stroke="#7e8794"
              tick={{ fontSize: 8 }}
              tickFormatter={(value) =>
                `${Number(value).toFixed(2)}s`
              }
              width={38}
            />

            <Tooltip
              contentStyle={{
                background: "#11151b",
                border: "1px solid #373d47",
                fontSize: "11px",
              }}
              formatter={(value, name) => [
                `${Number(value).toFixed(4)} s/lap`,
                name === "robust_slope"
                  ? "Robust Theil-Sen"
                  : "Linear regression",
              ]}
              labelFormatter={(label) =>
                `Driver / stint: ${label}`
              }
            />

            <Line
              type="monotone"
              dataKey="robust_slope"
              name="Robust Theil-Sen"
              stroke="#f4c542"
              strokeWidth={2}
              dot={{ r: 3, fill: "#f4c542" }}
            />

            <Line
              type="monotone"
              dataKey="linear_slope"
              name="Linear regression"
              stroke="#ff4b52"
              strokeWidth={1.5}
              dot={{ r: 2, fill: "#ff4b52" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="small-note">
        {selectedDegradationDriver === "ALL"
          ? "Showing all drivers."
          : `Showing ${selectedDegradationDriver} only.`}
        {" "}Yellow: robust regression. Red: linear regression.
        Values represent observed lap-time changes per tyre-age lap.
      </p>
    </>
  )}
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
        </aside>

        <section
          className="degradation-grid-item"
          style={{ gridColumn: "1 / -1", minWidth: 0, width: "100%", maxWidth: "100%", boxSizing: "border-box" }}
        >
          <Panel title="TYRE DEGRADATION ANALYSIS · MODEL V2.1" className="degradation-wide-panel">
  {degradationLoading ? (
    <p className="small-note">Running robust tyre degradation analysis...</p>
  ) : degradationError ? (
    <p className="error-text">{degradationError}</p>
  ) : !degradationData || degradationStints.length === 0 ? (
    <p className="small-note">
      No tyre degradation results are available for this race.
    </p>
  ) : (
    <>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
        gap: "10px",
        marginBottom: "14px"
      }}>
        <div style={{ background: "#111820", border: "1px solid #29313b", borderRadius: "8px", padding: "12px" }}>
          <small style={{ color: "#8e9aa8", display: "block" }}>VALID LAP RECORDS</small>
          <strong style={{ fontSize: "22px" }}>{degradationData.total_valid_laps ?? "—"}</strong>
        </div>
        <div style={{ background: "#111820", border: "1px solid #29313b", borderRadius: "8px", padding: "12px" }}>
          <small style={{ color: "#8e9aa8", display: "block" }}>ANALYZED STINTS</small>
          <strong style={{ fontSize: "22px" }}>{degradationData.total_stints ?? degradationStints.length}</strong>
        </div>
      </div>

      <div className="tyre-strategy-controls">
        <label htmlFor="degradation-driver-filter">DRIVER</label>
        <select
          id="degradation-driver-filter"
          value={selectedDegradationDriver}
          onChange={(e) => setSelectedDegradationDriver(e.target.value)}
        >
          <option value="ALL">All drivers</option>
          {degradationDrivers.map((driver) => (
            <option key={driver} value={driver}>{driver}</option>
          ))}
        </select>
      </div>

      <div style={{ marginTop: "12px" }}>
        <div className="model-label">ROBUST THEIL–SEN SLOPE · SECONDS PER TYRE-AGE LAP</div>
        {degradationChartData.length > 0 ? (
          <div className="chart-box tyre-chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={degradationChartData} margin={{ top: 8, right: 12, left: 2, bottom: 8 }}>
                <CartesianGrid stroke="#282d35" strokeDasharray="3 3" />
                <XAxis dataKey="label" stroke="#7e8794" tick={{ fontSize: 9 }} />
                <YAxis
                  stroke="#7e8794"
                  tick={{ fontSize: 9 }}
                  tickFormatter={(value) => `${Number(value).toFixed(2)}s`}
                />
                <Tooltip
                  contentStyle={{ background: "#11151b", border: "1px solid #373d47" }}
                  formatter={(value, name) => [`${Number(value).toFixed(4)} s/lap`, name === "robust_slope" ? "Robust slope" : "Linear slope"]}
                  labelFormatter={(label) => `Driver / stint: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="robust_slope"
                  name="Robust Theil-Sen"
                  stroke="#f4c542"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls={false}
                />

                <Line
                  type="monotone"
                  dataKey="linear_slope"
                  name="Ordinary Linear Regression"
                  stroke="#ff4b52"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="small-note">No stints have enough tyre-age data to plot a robust slope.</p>
        )}
      </div>

      <div className="degradation-stint-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "9px", marginTop: "14px" }}>
        {visibleDegradationStints.map((stint, index) => {
          const reliability = String(stint.reliability ?? "unknown").toLowerCase();
          const badgeColor = reliability === "high" ? "#39c77a" : reliability === "medium" ? "#f4c542" : "#ff777d";
          const outlierLaps = Array.isArray(stint.outlier_laps) ? stint.outlier_laps : [];
          const sectors = Array.isArray(stint.sector_analysis)
            ? stint.sector_analysis.map((sector, sectorIndex) => [
                sector.sector ?? sector.name ?? `Sector ${sectorIndex + 1}`,
                sector,
              ])
            : stint.sector_analysis && typeof stint.sector_analysis === "object"
              ? Object.entries(stint.sector_analysis)
              : [];

          return (
            <details
              key={`${stint.driver}-${stint.stint}-${index}`}
              style={{ background: "#111820", border: "1px solid #29313b", borderRadius: "8px", padding: "10px 12px" }}
            >
              <summary style={{ cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
                <span>
                  <strong>{stint.driver}</strong>
                  <small style={{ color: "#9aa5b1", marginLeft: "8px" }}>
                    STINT {stint.stint} · {stint.compound ?? "UNKNOWN"}
                  </small>
                </span>
                <span style={{ color: badgeColor, fontSize: "10px", fontWeight: 700, textTransform: "uppercase" }}>
                  {reliability} reliability
                </span>
              </summary>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "9px", marginTop: "12px" }}>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>ROBUST SLOPE</small>
                  <b>{formatSlope(stint.robust_degradation_seconds_per_lap)}</b>
                </div>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>LINEAR R²</small>
                  <b>{stint.r_squared != null && Number.isFinite(Number(stint.r_squared)) ? Number(stint.r_squared).toFixed(3) : "—"}</b>
                </div>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>VALID LAPS / TYRE AGES</small>
                  <b>{stint.valid_laps ?? "—"} /{" "}{stint.tyre_age_start != null && stint.tyre_age_end != null? `${stint.tyre_age_start}–${stint.tyre_age_end}`: "—"}</b>
                </div>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>FIT / DATA</small>
                  <b>{stint.statistical_fit_quality ?? "—"} / {stint.data_sufficiency ?? "—"}</b>
                </div>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>LAP-TIME TREND</small>
                  <b>{String(stint.lap_time_trend ?? "—").replaceAll("_", " ")}</b>
                </div>
                <div>
                  <small style={{ color: "#8e9aa8", display: "block" }}>OUTLIER LAPS</small>
                  <b>{outlierLaps.length ? outlierLaps.join(", ") : "None flagged"}</b>
                </div>
              </div>

              {sectors.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <small style={{ color: "#8e9aa8", display: "block", marginBottom: "6px" }}>SECTOR ANALYSIS</small>
                  {sectors.map(([sector, details]) => (
                    <div key={sector} style={{ display: "flex", justifyContent: "space-between", gap: "10px", padding: "4px 0", borderTop: "1px solid #29313b", fontSize: "12px" }}>
                      <span>{String(sector).replaceAll("_", " ").toUpperCase()}</span>
                      <span style={{ color: "#dce2e9" }}>
                        {details && typeof details === "object"
                          ? Object.entries(details).map(([key, value]) =>
                              `${key.replaceAll("_", " ")}: ${typeof value === "number" ? value.toFixed(4) : String(value)}`
                            ).join(" · ")
                          : String(details)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {Array.isArray(stint.context_warnings) && stint.context_warnings.length > 0 && (
                <ul style={{ color: "#9aa5b1", fontSize: "11px", paddingLeft: "17px", marginBottom: 0 }}>
                  {stint.context_warnings.map((warning, warningIndex) => (
                    <li key={warningIndex}>{warning}</li>
                  ))}
                </ul>
              )}
            </details>
          );
        })}
      </div>

      <p className="small-note" style={{ marginTop: "12px" }}>
        {degradationData.metric_note ?? "Robust slopes describe observed lap-time trends against tyre age, not pure causal tyre wear."}
        {" "}Statistical reliability describes the regression evidence; tyre-wear interpretation remains uncertain because race conditions can affect lap times.
      </p>
    </>
  )}
</Panel>
        </section>

      </main>



      <footer className="footer"><span>APEX INTELLIGENCE AI Â· F1 ANALYTICS</span><span>LANGGRAPH Â· RAG Â· OLLAMA Â· FASTAPI</span></footer>
    </div>
  );
}

export default App;
