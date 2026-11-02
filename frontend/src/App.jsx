import RaceScene from "./components/RaceScene";
import StrategySimulator from "./components/StrategySimulator";
import { useEffect, useState } from "react";
import {
  Activity, BrainCircuit, Flag,
  Timer, ChevronRight, Send, RefreshCw, CircleDot, Trash2,
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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
  const [strategyData, setStrategyData] = useState(null);
  const [strategyLoading, setStrategyLoading] = useState(false);
  const [strategyError, setStrategyError] = useState("");
  const [selectedStrategyDriver, setSelectedStrategyDriver] = useState("ALL");
  // RACE STRATEGY SIMULATOR
const [strategyMode, setStrategyMode] = useState("historical");
const [simulationLoading, setSimulationLoading] = useState(false);
const [simulationError, setSimulationError] = useState("");
const [historicalResult, setHistoricalResult] = useState(null);
const [liveResult, setLiveResult] = useState(null);

const [customDriver, setCustomDriver] = useState("HAM");
const [customRaceLaps, setCustomRaceLaps] = useState(52);
const [customPitLoss, setCustomPitLoss] = useState(22);
const [customStints, setCustomStints] = useState([
  { compound: "MEDIUM", laps: 26 },
  { compound: "HARD", laps: 26 },
]);
const [customLoading, setCustomLoading] = useState(false);
const [customError, setCustomError] = useState("");
const [customResult, setCustomResult] = useState(null);


const [simulationRaceLaps, setSimulationRaceLaps] = useState(52);
const [simulationPitLoss, setSimulationPitLoss] = useState(22);
const [simulationMaxStops, setSimulationMaxStops] = useState(3);

const [liveRemainingLaps, setLiveRemainingLaps] = useState(20);

const [liveDriverStates, setLiveDriverStates] = useState({
  [selectedDriverA]: {
    current_compound: "MEDIUM",
    tyre_age: 15,
  },
  [selectedDriverB]: {
    current_compound: "HARD",
    tyre_age: 10,
  },
});

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
  if (availableDrivers.length === 0) return;
  setCustomDriver((current) =>
    availableDrivers.includes(current) ? current : availableDrivers[0]
  );
}, [availableDrivers]);

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

useEffect(() => {
  if (!selectedSeason || !selectedRace) return;

  let cancelled = false;

  async function loadRaceStrategy() {
    setStrategyLoading(true);
    setStrategyError("");
    setStrategyData(null);

    try {
      const response = await fetch(
        `${API}/race/${selectedSeason}/${encodeURIComponent(selectedRace)}/strategy/overview`
      );
      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Could not load race strategy analysis."
        );
      }

      if (!cancelled) {
        setStrategyData(result);
        setSelectedStrategyDriver("ALL");
      }
    } catch (error) {
      if (!cancelled) setStrategyError(error.message);
    } finally {
      if (!cancelled) setStrategyLoading(false);
    }
  }

  loadRaceStrategy();

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
// Run historical race strategy simulation
async function runHistoricalSimulation(e) {
  e.preventDefault();

  setSimulationLoading(true);
  setSimulationError("");
  setHistoricalResult(null);

  try {
    const response = await fetch(
      `${API}/race/${selectedSeason}/${encodeURIComponent(
        selectedRace
      )}/strategy/simulate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pit_loss_seconds: Number(simulationPitLoss),
          max_stops: Number(simulationMaxStops),
          race_laps: Number(simulationRaceLaps),
          driver:selectedStrategyDriver === "ALL"? null:selectedStrategyDriver,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Historical simulation failed."
      );
    }

    setHistoricalResult(data);
  } catch (error) {
    setSimulationError(error.message);
  } finally {
    setSimulationLoading(false);
  }
}


// Run live race-state strategy simulation
async function runLiveSimulation(e) {
  e.preventDefault();

  setSimulationLoading(true);
  setSimulationError("");
  setLiveResult(null);

  try {
    const drivers = [...new Set([
      selectedDriverA,
      selectedDriverB,
    ])].filter(Boolean);

    if (drivers.length === 0) {
      throw new Error("Select at least one driver.");
    }

    const driverStates = {};

    for (const driver of drivers) {
      const state = liveDriverStates[driver];

      if (!state) {
        throw new Error(`Missing tyre state for ${driver}.`);
      }

      driverStates[driver] = {
        current_compound: state.current_compound,
        tyre_age: Number(state.tyre_age),
      };
    }

    const response = await fetch(
      `${API}/race/${selectedSeason}/${encodeURIComponent(
        selectedRace
      )}/strategy/live`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          remaining_laps: Number(liveRemainingLaps),
          pit_loss_seconds: Number(simulationPitLoss),
          max_stops: Number(simulationMaxStops),
          driver_states: driverStates,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Live simulation failed."
      );
    }

    setLiveResult(data);
  } catch (error) {
    setSimulationError(error.message);
  } finally {
    setSimulationLoading(false);
  }
}


// Evaluate the user-defined tyre strategy.
async function runCustomStrategy(e) {
  e.preventDefault();
  setCustomLoading(true);
  setCustomError("");
  setCustomResult(null);

  try {
    const response = await fetch(
      `${API}/race/${selectedSeason}/${encodeURIComponent(selectedRace)}/strategy/custom`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          driver: customDriver,
          race_laps: Number(customRaceLaps),
          pit_loss_seconds: Number(customPitLoss),
          stints: customStints.map((stint) => ({
            compound: stint.compound,
            laps: Number(stint.laps),
          })),
          require_two_compounds: true,
        }),
      }
    );

    const data = await response.json();
    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Custom strategy evaluation failed."
      );
    }
    setCustomResult(data);
  } catch (error) {
    setCustomError(error.message);
  } finally {
    setCustomLoading(false);
  }
}

function updateCustomStint(index, field, value) {
  setCustomStints((current) =>
    current.map((stint, stintIndex) =>
      stintIndex === index
        ? { ...stint, [field]: field === "laps" ? value : value }
        : stint
    )
  );
}

function addCustomStint() {
  setCustomStints((current) => {
    if (current.length >= 4) return current;
    const previousCompound = current[current.length - 1]?.compound;
    const nextCompound = ["SOFT", "MEDIUM", "HARD"].find(
      (compound) => compound !== previousCompound
    ) ?? "MEDIUM";
    return [...current, { compound: nextCompound, laps: 1 }];
  });
}

function removeCustomStint(index) {
  setCustomStints((current) =>
    current.length <= 1
      ? current
      : current.filter((_, stintIndex) => stintIndex !== index)
  );
}

// Update tyre state for a live driver
function updateLiveDriverState(driver, field, value) {
  setLiveDriverStates((current) => ({
    ...current,
    [driver]: {
      current_compound: "MEDIUM",
      tyre_age: 10,
      ...current[driver],
      [field]: value,
    },
  }));
}


// Format seconds as minutes and seconds
function formatRaceTime(seconds) {
  const value = Number(seconds);

  if (!Number.isFinite(value)) return "—";

  const minutes = Math.floor(value / 60);
  const remainingSeconds = (value % 60).toFixed(3);

  return `${minutes}m ${remainingSeconds}s`;
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

const strategyDrivers = strategyData?.drivers ?? [];
const visibleStrategyDrivers = strategyDrivers.filter(
  (driver) =>
    selectedStrategyDriver === "ALL" ||
    driver.driver === selectedStrategyDriver
);
const strategyPitWindows = (strategyData?.pit_windows ?? []).filter(
  (window) =>
    selectedStrategyDriver === "ALL" ||
    window.driver === selectedStrategyDriver
);
const strategyCompoundComparison = strategyData?.compound_comparison ?? [];

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
                  <b>
                {stint.raw_r_squared != null && Number.isFinite(Number(stint.raw_r_squared))? Number(stint.raw_r_squared).toFixed(3): "—"}</b>
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

        <section
          className="degradation-grid-item"
          style={{ gridColumn: "1 / -1", minWidth: 0, width: "100%", maxWidth: "100%", boxSizing: "border-box" }}
        >
          <Panel title="RACE STRATEGY INTELLIGENCE · HISTORICAL ANALYSIS" className="degradation-wide-panel">
            {strategyLoading ? (
              <p className="small-note">Analyzing historical pit strategies...</p>
            ) : strategyError ? (
              <p className="error-text">
                {strategyError}
                {" "}The strategy overview endpoint must be enabled in FastAPI.
              </p>
            ) : !strategyData ? (
              <p className="small-note">No strategy analysis is available.</p>
            ) : (
              <>
                <div className="tyre-strategy-controls">
                  <label htmlFor="strategy-driver-filter">DRIVER</label>
                  <select
                    id="strategy-driver-filter"
                    value={selectedStrategyDriver}
                    onChange={(e) => setSelectedStrategyDriver(e.target.value)}
                  >
                    <option value="ALL">All drivers</option>
                    {strategyDrivers.map((driver) => (
                      <option key={driver.driver} value={driver.driver}>
                        {driver.driver}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="strategy-summary-grid" style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: "10px",
                  margin: "12px 0"
                }}>
                  <div className="strategy-stat">
                    <small>DRIVERS ANALYZED</small>
                    <strong>{strategyData.total_drivers ?? strategyDrivers.length}</strong>
                  </div>
                  <div className="strategy-stat">
                    <small>PIT TRANSITIONS</small>
                    <strong>{strategyData.total_pit_transitions ?? strategyPitWindows.length}</strong>
                  </div>
                  <div className="strategy-stat">
                    <small>COMPOUNDS OBSERVED</small>
                    <strong>{strategyCompoundComparison.length}</strong>
                  </div>
                </div>

                <h3 className="strategy-subheading">RECORDED TYRE STRATEGIES</h3>
                <div className="strategy-driver-grid" style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                  gap: "10px"
                }}>
                  {visibleStrategyDrivers.map((driver) => (
                    <div className="strategy-driver-card" key={driver.driver}>
                      <div className="strategy-card-heading">
                        <strong>{driver.driver}</strong>
                        <span>{driver.strategy_type ?? "Strategy unavailable"}</span>
                      </div>
                      <div className="strategy-compound-sequence">
                        {(driver.compound_sequence ?? []).map((compound, index) => (
                          <span
                            key={`${driver.driver}-${index}`}
                            style={{
                              borderColor: tyreCompoundColor(compound),
                              color: tyreCompoundColor(compound)
                            }}
                          >
                            {String(compound).replaceAll("_", " ")}
                          </span>
                        ))}
                      </div>
                      <div className="strategy-card-meta">
                        <span>{driver.total_stints ?? driver.stints?.length ?? 0} stints</span>
                        <span>{driver.estimated_pit_stops ?? "—"} estimated stops</span>
                      </div>
                      <div className="strategy-stint-list">
                        {(driver.stints ?? []).map((stint) => (
                          <div key={`${driver.driver}-stint-${stint.stint}`}>
                            <span>S{stint.stint} · {stint.compound}</span>
                            <span>L{stint.start_lap}–{stint.end_lap} · {stint.stint_laps} laps</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <h3 className="strategy-subheading">ESTIMATED PIT WINDOWS</h3>
                {strategyPitWindows.length === 0 ? (
                  <p className="small-note">No pit-window transitions for this driver.</p>
                ) : (
                  <div className="strategy-table-wrap">
                    <table className="strategy-table">
                      <thead>
                        <tr>
                          <th>DRIVER</th>
                          <th>EST. WINDOW</th>
                          <th>FROM</th>
                          <th>TO</th>
                          <th>PREVIOUS STINT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {strategyPitWindows.map((window, index) => (
                          <tr key={`${window.driver}-${window.from_stint}-${index}`}>
                            <td>{window.driver}</td>
                            <td>Lap {window.pit_window_lap}</td>
                            <td>{window.previous_compound}</td>
                            <td>{window.next_compound}</td>
                            <td>{window.previous_stint_length} laps</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <h3 className="strategy-subheading">COMPOUND COMPARISON · DESCRIPTIVE</h3>
                <div className="strategy-table-wrap">
                  <table className="strategy-table">
                    <thead>
                      <tr>
                        <th>COMPOUND</th>
                        <th>DRIVERS</th>
                        <th>LAP RECORDS</th>
                        <th>MEAN LAP</th>
                        <th>MEDIAN LAP</th>
                        <th>MEAN TYRE AGE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {strategyCompoundComparison.map((compound) => (
                        <tr key={compound.compound}>
                          <td>
                            <span className="strategy-compound-dot" style={{
                              background: tyreCompoundColor(compound.compound)
                            }} />
                            {compound.compound}
                          </td>
                          <td>{compound.drivers}</td>
                          <td>{compound.valid_lap_records}</td>
                          <td>{compound.mean_lap_seconds?.toFixed?.(3) ?? "—"} s</td>
                          <td>{compound.median_lap_seconds?.toFixed?.(3) ?? "—"} s</td>
                          <td>{compound.mean_tyre_age?.toFixed?.(2) ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <p className="small-note strategy-metric-note">
                  {strategyData.metric_note ?? "Historical descriptive analysis only. Pit windows are inferred from stint boundaries; compound lap averages are not adjusted for race conditions."}
                </p>
              </>
            )}
                    </Panel>
        </section>

        {/* ======================================
            APEX RACE STRATEGY OPTIMIZER V2
        ====================================== */}

        <section
          className="degradation-grid-item"
          style={{
            gridColumn: "1 / -1",
            minWidth: 0,
            width: "100%",
            maxWidth: "100%",
            boxSizing: "border-box",
          }}
        >
          <Panel
            title="APEX RACE STRATEGY OPTIMIZER · HISTORICAL & LIVE SIMULATION"
            className="degradation-wide-panel"
          >
            <div className="simulator-header">
              <div>
                <h3>Strategy Simulation Engine V2</h3>
                <p className="small-note">
                  Optimize tyre compounds, pit stops and future pit windows.
                </p>
              </div>

              <div className="simulator-status">
                <CircleDot size={10} />
                ENGINE READY
              </div>
            </div>

            {/* MODE SELECTOR */}
            <div className="simulator-tabs">
              <button
                type="button"
                className={strategyMode === "historical" ? "active" : ""}
                onClick={() => {
                  setStrategyMode("historical");
                  setSimulationError("");
                }}
              >
                <Timer size={15} />
                Historical Simulation
              </button>

              <button
                type="button"
                className={strategyMode === "live" ? "active" : ""}
                onClick={() => {
                  setStrategyMode("live");
                  setSimulationError("");
                }}
              >
                <Activity size={15} />
                Live Strategy Snapshot
              </button>
            </div>

            {/* COMMON SETTINGS */}
            <div className="simulator-controls">
              <label>
                PIT LOSS · SECONDS
                <input
                  type="number"
                  min="0"
                  max="90"
                  step="0.5"
                  value={simulationPitLoss}
                  onChange={(e) =>
                    setSimulationPitLoss(e.target.value)
                  }
                />
              </label>

              <label>
                MAXIMUM PIT STOPS
                <select
                  value={simulationMaxStops}
                  onChange={(e) =>
                    setSimulationMaxStops(Number(e.target.value))
                  }
                >
                  {[1, 2, 3].map((stops) => (
                    <option key={stops} value={stops}>
                      {stops}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {strategyMode === "historical" && (
            <form
              className="simulator-form"
              onSubmit={runHistoricalSimulation}
            >
              <label>
                SELECT DRIVER
                <select
                  value={selectedStrategyDriver}
                  onChange={(e) => {
                    setSelectedStrategyDriver(e.target.value);
                    setHistoricalResult(null);
                    setSimulationError("");
                  }}
                >
                  <option value="ALL">All Drivers</option>

                  {availableDrivers.map((driver) => (
                    <option key={driver} value={driver}>
                      {driver}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                RACE DISTANCE · LAPS
                <input
                  type="number"
                  min="10"
                  max="120"
                  value={simulationRaceLaps}
                  onChange={(e) =>
                    setSimulationRaceLaps(e.target.value)
                  }
                  required
                />
              </label>

              <button
                type="submit"
                disabled={simulationLoading}
              >
                <RefreshCw size={15} />
                {simulationLoading
                  ? "Optimizing..."
                  : "Optimize Historical Strategy"}
              </button>
            </form>
          )}

            {/* LIVE SIMULATION FORM */}
            {strategyMode === "live" && (
              <form
                className="simulator-form live-simulator-form"
                onSubmit={runLiveSimulation}
              >
                <label>
                  REMAINING RACE LAPS
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={liveRemainingLaps}
                    onChange={(e) =>
                      setLiveRemainingLaps(e.target.value)
                    }
                    required
                  />
                </label>

                {[...new Set([
                  selectedDriverA,
                  selectedDriverB,
                ])].filter(Boolean).map((driver) => {
                  const state = liveDriverStates[driver] ?? {
                    current_compound: "MEDIUM",
                    tyre_age: 10,
                  };

                  return (
                    <div
                      className="live-driver-input"
                      key={driver}
                    >
                      <h4>{driver} · CURRENT TYRE STATE</h4>

                      <label>
                        COMPOUND
                        <select
                          value={state.current_compound}
                          onChange={(e) =>
                            updateLiveDriverState(
                              driver,
                              "current_compound",
                              e.target.value
                            )
                          }
                        >
                          {["SOFT", "MEDIUM", "HARD"].map(
                            (compound) => (
                              <option
                                key={compound}
                                value={compound}
                              >
                                {compound}
                              </option>
                            )
                          )}
                        </select>
                      </label>

                      <label>
                        TYRE AGE · LAPS
                        <input
                          type="number"
                          min="1"
                          max="100"
                          value={state.tyre_age}
                          onChange={(e) =>
                            updateLiveDriverState(
                              driver,
                              "tyre_age",
                              e.target.value
                            )
                          }
                          required
                        />
                      </label>
                    </div>
                  );
                })}

                <button
                  type="submit"
                  disabled={simulationLoading}
                >
                  <Activity size={15} />
                  {simulationLoading
                    ? "Calculating..."
                    : "Calculate Live Strategy"}
                </button>

                <p className="small-note">
                  Uses manually entered race-state snapshots.
                  This is not connected to live F1 telemetry.
                </p>
              </form>
            )}

            {/* ERROR STATE */}
            {simulationError && (
              <div className="simulator-error">
                <Activity size={15} />
                {simulationError}
              </div>
            )}

            {/* HISTORICAL RESULTS */}
            {strategyMode === "historical" &&
              historicalResult && (
                <div className="simulator-results">
                  <div className="simulator-result-heading">
                    <h3>HISTORICAL OPTIMIZATION RESULTS</h3>
                    <span>
                      {historicalResult.race_laps} RACE LAPS
                    </span>
                  </div>

                  {(historicalResult.driver_results ?? []).map(
                    (driverResult) => {
                      const strategy = driverResult.best_strategy;

                      if (!strategy) return null;

                      return (
                        <div
                          className="simulation-driver-result"
                          key={driverResult.driver}
                        >
                          <div className="simulation-driver-heading">
                            <h3>{driverResult.driver}</h3>
                            <span>
                              {strategy.stops} PIT STOPS
                            </span>
                          </div>

                          <div className="simulation-metrics">
                            <div>
                              <small>ESTIMATED RACE TIME</small>
                              <strong>
                                {formatRaceTime(
                                  strategy.estimated_total_seconds
                                )}
                              </strong>
                            </div>

                            <div>
                              <small>ESTIMATED SECONDS</small>
                              <strong>
                                {Number(
                                  strategy.estimated_total_seconds
                                ).toFixed(3)}
                              </strong>
                            </div>

                            <div>
                              <small>STINTS</small>
                              <strong>
                                {strategy.stints?.length ?? 0}
                              </strong>
                            </div>
                          </div>

                          <h4 className="strategy-subheading">
                            RECOMMENDED STINT TIMELINE
                          </h4>

                          <div className="simulation-stint-list">
                            {(strategy.stints ?? []).map(
                              (stint) => (
                                <div
                                  className="simulation-stint"
                                  key={stint.stint}
                                >
                                  <div
                                    className="simulation-stint-color"
                                    style={{
                                      background: tyreCompoundColor(
                                        stint.compound
                                      ),
                                    }}
                                  />

                                  <div className="simulation-stint-info">
                                    <strong>
                                      STINT {stint.stint} · {stint.compound}
                                    </strong>
                                    <span>
                                      L{stint.start_lap}–{stint.end_lap}
                                    </span>
                                  </div>

                                  <b>{stint.laps} LAPS</b>
                                </div>
                              )
                            )}
                          </div>

                          <h4 className="strategy-subheading">
                            ALTERNATIVE STRATEGIES
                          </h4>

                          <div className="simulation-alternatives">
                            {(driverResult.alternatives ?? []).map(
                              (alternative, index) => (
                                <div
                                  className="simulation-alternative"
                                  key={`${alternative.stops}-${index}`}
                                >
                                  <div>
                                    <strong>
                                      OPTION {index + 1}
                                    </strong>
                                    <span>
                                      {alternative.stops} stops
                                    </span>
                                  </div>

                                  <div className="alternative-compounds">
                                    {(alternative.stints ?? []).map(
                                      (stint, stintIndex) => (
                                        <span
                                          key={stintIndex}
                                          style={{
                                            borderColor: tyreCompoundColor(
                                              stint.compound
                                            ),
                                            color: tyreCompoundColor(
                                              stint.compound
                                            ),
                                          }}
                                        >
                                          {stint.compound}
                                        </span>
                                      )
                                    )}
                                  </div>

                                  <strong>
                                    {Number(
                                      alternative.estimated_total_seconds
                                    ).toFixed(3)} s
                                  </strong>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      );
                    }
                  )}

                  <div className="simulator-note">
                    {historicalResult.model_note}
                  </div>

                  {(historicalResult.limitations ?? []).length > 0 && (
                    <details className="simulator-limitations">
                      <summary>MODEL LIMITATIONS</summary>
                      <ul>
                        {historicalResult.limitations.map(
                          (item, index) => (
                            <li key={index}>{item}</li>
                          )
                        )}
                      </ul>
                    </details>
                  )}
                </div>
              )}

            {/* LIVE RESULTS */}
            {strategyMode === "live" && liveResult && (
              <div className="simulator-results">
                <div className="simulator-result-heading">
                  <h3>LIVE STRATEGY RECOMMENDATIONS</h3>
                  <span>
                    {liveResult.remaining_laps} LAPS REMAINING
                  </span>
                </div>

                {(liveResult.driver_results ?? []).map(
                  (driverResult) => {
                    const recommendation =
                      driverResult.recommendation;

                    if (!recommendation) return null;

                    return (
                      <div
                        className="simulation-driver-result"
                        key={driverResult.driver}
                      >
                        <div className="simulation-driver-heading">
                          <h3>{driverResult.driver}</h3>
                          <span className="pit-recommendation">
                            {recommendation.action.replaceAll("_", " ").toUpperCase()}
                          </span>
                        </div>

                        <div className="simulation-metrics">
                          <div>
                            <small>CURRENT TYRE</small>
                            <strong>
                              {driverResult.current_compound}
                            </strong>
                          </div>

                          <div>
                            <small>TYRE AGE</small>
                            <strong>
                              {driverResult.current_tyre_age} LAPS
                            </strong>
                          </div>

                          <div>
                            <small>NEW COMPOUND</small>
                            <strong
                              style={{
                                color: tyreCompoundColor(
                                  recommendation.compound
                                ),
                              }}
                            >
                              {recommendation.compound}
                            </strong>
                          </div>

                          <div>
                            <small>ESTIMATED REMAINING TIME</small>
                            <strong>
                              {formatRaceTime(
                                recommendation.estimated_remaining_seconds
                              )}
                            </strong>
                          </div>

                          <div>
                            <small>PIT AFTER</small>
                            <strong>
                              {recommendation.laps_until_pit === 0
                                ? "NOW"
                                : `${recommendation.laps_until_pit} LAPS`}
                            </strong>
                          </div>

                          <div>
                            <small>ADDITIONAL STOPS</small>
                            <strong>
                              {recommendation.stops_added}
                            </strong>
                          </div>
                        </div>

                        <h4 className="strategy-subheading">
                          RECOMMENDED STINT PLAN
                        </h4>

                        <div className="simulation-stint-list">
                          {(recommendation.stints ?? []).map(
                            (stint) => (
                              <div
                                className="simulation-stint"
                                key={stint.stint}
                              >
                                <div
                                  className="simulation-stint-color"
                                  style={{
                                    background: tyreCompoundColor(
                                      stint.compound
                                    ),
                                  }}
                                />

                                <div className="simulation-stint-info">
                                  <strong>
                                    STINT {stint.stint} · {stint.compound}
                                  </strong>
                                  <span>
                                    L{stint.start_lap}–{stint.end_lap}
                                  </span>
                                </div>

                                <b>{stint.laps} LAPS</b>
                              </div>
                            )
                          )}
                        </div>

                        <h4 className="strategy-subheading">
                          ALTERNATIVE PIT WINDOWS
                        </h4>

                        <div className="simulation-alternatives">
                          {(driverResult.alternatives ?? []).map(
                            (alternative, index) => (
                              <div
                                className="simulation-alternative"
                                key={`${alternative.action}-${alternative.laps_until_pit}-${index}`}
                              >
                                <div>
                                  <strong>
                                    {alternative.action
                                      .replaceAll("_", " ")
                                      .toUpperCase()}
                                  </strong>
                                  <span>
                                    {alternative.laps_until_pit === 0
                                      ? "Pit now"
                                      : `Pit after ${alternative.laps_until_pit} laps`}
                                  </span>
                                </div>

                                <strong>
                                  {alternative.compound}
                                </strong>

                                <strong>
                                  {Number(
                                    alternative.estimated_remaining_seconds
                                  ).toFixed(3)} s
                                </strong>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    );
                  }
                )}

                <div className="simulator-note">
                  {liveResult.model_note}
                </div>

                {(liveResult.limitations ?? []).length > 0 && (
                  <details className="simulator-limitations">
                    <summary>MODEL LIMITATIONS</summary>
                    <ul>
                      {liveResult.limitations.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            )}

            {/* CUSTOM STRATEGY BUILDER */}
            <div className="custom-strategy-builder" style={{
              marginTop: "22px",
              paddingTop: "20px",
              borderTop: "1px solid #29313b"
            }}>
              <div className="simulator-header">
                <div>
                  <h3>CUSTOM STRATEGY BUILDER</h3>
                  <p className="small-note">
                    Design your own dry-tyre stint sequence and compare its estimated time with the optimizer.
                  </p>
                </div>
                <span className="simulator-status">USER-DEFINED PLAN</span>
              </div>

              <form className="simulator-controls" onSubmit={runCustomStrategy}>
                <label>
                  DRIVER
                  <select
                    value={customDriver}
                    onChange={(e) => {
                      setCustomDriver(e.target.value);
                      setCustomResult(null);
                    }}
                    required
                  >
                    {availableDrivers.map((driver) => (
                      <option key={driver} value={driver}>{driver}</option>
                    ))}
                  </select>
                </label>

                <label>
                  RACE DISTANCE · LAPS
                  <input
                    type="number"
                    min="10"
                    max="120"
                    value={customRaceLaps}
                    onChange={(e) => {
                      setCustomRaceLaps(e.target.value);
                      setCustomResult(null);
                    }}
                    required
                  />
                </label>

                <label>
                  PIT LOSS · SECONDS
                  <input
                    type="number"
                    min="0"
                    max="90"
                    step="0.5"
                    value={customPitLoss}
                    onChange={(e) => {
                      setCustomPitLoss(e.target.value);
                      setCustomResult(null);
                    }}
                    required
                  />
                </label>

                <div style={{ gridColumn: "1 / -1" }}>
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "12px",
                    marginBottom: "10px"
                  }}>
                    <h4 className="strategy-subheading" style={{ margin: 0 }}>
                      YOUR STINT SEQUENCE
                    </h4>
                    <button
                      type="button"
                      className="custom-add-stint-btn"
                      onClick={addCustomStint}
                      disabled={customStints.length >= 4}
                    >
                      <span aria-hidden="true">+</span> ADD STINT
                    </button>
                  </div>

                  {customStints.map((stint, index) => (
                    <div
                      key={`custom-stint-${index}`}
                      className="live-driver-input"
                      style={{
                        display: "grid",
                        gridTemplateColumns: "minmax(120px, 1fr) minmax(100px, 1fr) auto",
                        alignItems: "end",
                        gap: "10px",
                        marginBottom: "10px"
                      }}
                    >
                      <label>
                        STINT {index + 1} · COMPOUND
                        <select
                          value={stint.compound}
                          onChange={(e) => {
                            updateCustomStint(index, "compound", e.target.value);
                            setCustomResult(null);
                          }}
                        >
                          {["SOFT", "MEDIUM", "HARD"].map((compound) => (
                            <option key={compound} value={compound}>{compound}</option>
                          ))}
                        </select>
                      </label>

                      <label>
                        LAPS
                        <input
                          type="number"
                          min="1"
                          max="120"
                          value={stint.laps}
                          onChange={(e) => {
                            updateCustomStint(index, "laps", e.target.value);
                            setCustomResult(null);
                          }}
                          required
                        />
                      </label>

                      <button
                        type="button"
                        className="custom-remove-stint-btn"
                        onClick={() => {
                          removeCustomStint(index);
                          setCustomResult(null);
                        }}
                        disabled={customStints.length <= 1}
                        aria-label={`Remove stint ${index + 1}`}
                        title={`Remove stint ${index + 1}`}
                      >
                        <Trash2 size={17} strokeWidth={2} aria-hidden="true" />
                      </button>
                    </div>
                  ))}

                  <div className="small-note" style={{ marginTop: "8px" }}>
                    Planned laps: {customStints.reduce(
                      (total, stint) => total + (Number(stint.laps) || 0), 0
                    )} / {Number(customRaceLaps) || 0}
                    {" · "}Pit stops: {Math.max(0, customStints.length - 1)}
                    {" · "}Use at least two different dry compounds.
                  </div>
                </div>

                <button className="custom-evaluate-btn" type="submit" disabled={customLoading || availableDrivers.length === 0}>
                  <Activity size={15} />
                  {customLoading ? "Evaluating plan..." : "Evaluate Custom Strategy"}
                </button>
              </form>

              {customError && (
                <div className="simulator-error" role="alert">
                  <Activity size={15} />
                  {customError}
                </div>
              )}

              {customResult && (
                <div className="simulator-results">
                  <div className="simulator-result-heading">
                    <h3>{customResult.driver} · CUSTOM PLAN</h3>
                    <span>{customResult.race_laps} RACE LAPS</span>
                  </div>

                  <div className="simulation-metrics">
                    <div>
                      <small>CUSTOM ESTIMATED TIME</small>
                      <strong>{formatRaceTime(customResult.estimated_total_seconds)}</strong>
                    </div>
                    <div>
                      <small>OPTIMIZER ESTIMATE</small>
                      <strong>{formatRaceTime(customResult.recommended_total_seconds)}</strong>
                    </div>
                    <div>
                      <small>DIFFERENCE VS OPTIMIZER</small>
                      <strong style={{
                        color: customResult.custom_is_faster ? "#39c77a" : "#ff777d"
                      }}>
                        {customResult.delta_vs_recommended_seconds > 0 ? "+" : ""}
                        {Number(customResult.delta_vs_recommended_seconds).toFixed(3)} s
                      </strong>
                    </div>
                    <div>
                      <small>PIT STOPS</small>
                      <strong>{customResult.pit_stops}</strong>
                    </div>
                  </div>

                  <section className="strategy-comparison-chart" aria-label="Custom and recommended strategy stint comparison">
                    <div className="strategy-comparison-chart-heading">
                      <h4>RACE DISTANCE COMPARISON</h4>
                      <span>STINT DISTRIBUTION · {customResult.race_laps} LAPS</span>
                    </div>
                    {[
                      {
                        label: "CUSTOM PLAN",
                        stints: customResult.stints ?? [],
                      },
                      {
                        label: "OPTIMIZER PLAN",
                        stints: customResult.recommended_strategy?.stints ?? [],
                      },
                    ].map((plan) => (
                      <div className="strategy-comparison-row" key={plan.label}>
                        <div className="strategy-comparison-label">{plan.label}</div>
                        <div className="strategy-comparison-track" role="img" aria-label={`${plan.label}: ${plan.stints.map((stint) => `${stint.compound} ${stint.laps} laps`).join(", ")}`}>
                          {plan.stints.map((stint) => {
                            const lapShare = (Number(stint.laps) / Number(customResult.race_laps)) * 100;
                            return (
                              <div
                                className="strategy-comparison-segment"
                                key={`${plan.label}-${stint.stint}`}
                                style={{
                                  flexBasis: `${lapShare}%`,
                                  background: tyreCompoundColor(stint.compound),
                                }}
                                title={`Stint ${stint.stint}: ${stint.compound}, ${stint.laps} laps (L${stint.start_lap}–L${stint.end_lap})`}
                              >
                                <span>{stint.compound}</span>
                                <b>{stint.laps}L</b>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                    <div className="strategy-comparison-axis">
                      <span>LAP 1</span>
                      <span>LAP {customResult.race_laps}</span>
                    </div>
                    <div className="strategy-comparison-legend">
                      {[...new Set([...(customResult.stints ?? []), ...(customResult.recommended_strategy?.stints ?? [])].map((stint) => stint.compound))].map((compound) => (
                        <span key={compound}>
                          <i style={{ background: tyreCompoundColor(compound) }} />
                          {compound}
                        </span>
                      ))}
                    </div>
                  </section>

                  <p className="small-note">
                    {customResult.custom_is_faster
                      ? "Your custom plan has a lower modelled time than the optimizer's selected plan."
                      : Math.abs(Number(customResult.delta_vs_recommended_seconds)) < 0.001
                        ? "Your custom plan matches the optimizer's estimated time."
                        : "The optimizer's selected plan has a lower modelled time than your custom plan."}
                  </p>

                  <h4 className="strategy-subheading">CUSTOM STINT TIMELINE</h4>
                  <div className="simulation-stint-list">
                    {customResult.stints.map((stint) => (
                      <div className="simulation-stint" key={`custom-result-${stint.stint}`}>
                        <div
                          className="simulation-stint-color"
                          style={{ background: tyreCompoundColor(stint.compound) }}
                        />
                        <div className="simulation-stint-info">
                          <strong>STINT {stint.stint} · {stint.compound}</strong>
                          <span>L{stint.start_lap}–L{stint.end_lap}</span>
                        </div>
                        <b>{stint.laps} LAPS</b>
                      </div>
                    ))}
                  </div>

                  <h4 className="strategy-subheading">OPTIMIZER'S RECOMMENDED PLAN</h4>
                  <div className="simulation-stint-list">
                    {(customResult.recommended_strategy?.stints ?? []).map((stint) => (
                      <div className="simulation-stint" key={`recommended-${stint.stint}`}>
                        <div
                          className="simulation-stint-color"
                          style={{ background: tyreCompoundColor(stint.compound) }}
                        />
                        <div className="simulation-stint-info">
                          <strong>STINT {stint.stint} · {stint.compound}</strong>
                          <span>L{stint.start_lap}–L{stint.end_lap}</span>
                        </div>
                        <b>{stint.laps} LAPS</b>
                      </div>
                    ))}
                  </div>

                  <div className="simulator-note">{customResult.model_note}</div>
                  <details className="simulator-limitations">
                    <summary>MODEL LIMITATIONS</summary>
                    <ul>
                      {(customResult.limitations ?? []).map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </details>
                </div>
              )}
            </div>

          </Panel>
        </section>

      </main>



      <footer className="footer"><span>APEX INTELLIGENCE AI Â· F1 ANALYTICS</span><span>LANGGRAPH Â· RAG Â· OLLAMA Â· FASTAPI</span></footer>
    </div>
  );
}
export default App;
