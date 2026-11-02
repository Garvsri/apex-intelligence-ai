
import { useState } from "react";
import { RefreshCw, Play, Flag, Timer, Gauge } from "lucide-react";

const API = "http://127.0.0.1:8000";

const COMPOUNDS = ["SOFT", "MEDIUM", "HARD"];

function formatTime(seconds) {
  if (!Number.isFinite(Number(seconds))) return "—";
  const value = Number(seconds);
  const minutes = Math.floor(value / 60);
  const remaining = (value % 60).toFixed(3);
  return `${minutes}:${remaining.padStart(6, "0")}`;
}

function Stat({ label, value }) {
  return (
    <div className="strategy-stat">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function StintList({ stints = [] }) {
  if (!stints.length) return <p className="small-note">No stint data.</p>;

  return (
    <div className="strategy-stint-list">
      {stints.map((stint, index) => (
        <div key={`${stint.stint}-${index}`}>
          <span>
            <b>STINT {stint.stint}</b> · {stint.compound}
          </span>
          <span>
            L{stint.start_lap}–L{stint.end_lap} ({stint.laps} laps)
          </span>
        </div>
      ))}
    </div>
  );
}

function HistoricalResults({ data }) {
  const results = data?.driver_results ?? [];

  return (
    <div>
      <div className="strategy-summary-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: 10,
          margin: "16px 0"
        }}
      >
        <Stat label="RACE LAPS" value={data.race_laps} />
        <Stat label="DRIVERS ANALYZED" value={data.drivers_analyzed} />
        <Stat label="PIT LOSS" value={`${data.pit_loss_seconds}s`} />
        <Stat label="MAX STOPS" value={data.max_stops} />
      </div>

      <h3 className="strategy-subheading">OPTIMIZED STRATEGIES</h3>

      {results.map((item) => {
        const best = item.best_strategy;

        return (
          <div className="strategy-driver-card" key={item.driver}
            style={{ marginBottom: 12 }}
          >
            <div className="strategy-card-heading">
              <strong>{item.driver}</strong>
              <span>FIELD RANK #{item.field_rank}</span>
            </div>

            <div className="strategy-summary-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: 10,
                marginTop: 12
              }}
            >
              <Stat label="ESTIMATED RACE TIME"
                value={formatTime(best.estimated_total_seconds)} />
              <Stat label="PIT STOPS" value={best.stops} />
              <Stat label="STRATEGY RANK" value={`#${best.rank}`} />
            </div>

            <h4 className="strategy-subheading">RECOMMENDED STINTS</h4>
            <StintList stints={best.stints} />

            <h4 className="strategy-subheading">ALTERNATIVE STRATEGIES</h4>

            {(item.alternatives ?? []).map((alternative, index) => (
              <div className="strategy-card-meta"
                key={`${item.driver}-${index}`}
                style={{ padding: "8px 0", borderTop: "1px solid #29313b" }}
              >
                <span>
                  #{alternative.rank} · {alternative.stops} stops
                </span>
                <strong>
                  {formatTime(alternative.estimated_total_seconds)}
                </strong>
              </div>
            ))}
          </div>
        );
      })}

      <h3 className="strategy-subheading">FIELD RANKING</h3>

      <div className="strategy-table-wrap">
        <table className="strategy-table">
          <thead>
            <tr>
              <th>POSITION</th>
              <th>DRIVER</th>
              <th>ESTIMATED TIME</th>
              <th>STOPS</th>
            </tr>
          </thead>
          <tbody>
            {(data.field_ranking ?? []).map((driver) => (
              <tr key={driver.driver}>
                <td>{driver.position}</td>
                <td>{driver.driver}</td>
                <td>{formatTime(driver.estimated_total_seconds)}</td>
                <td>{driver.stops}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="small-note strategy-metric-note">{data.model_note}</p>
    </div>
  );
}

function LiveResults({ data }) {
  return (
    <div>
      {(data.driver_results ?? []).map((item) => {
        const recommendation = item.recommendation;

        return (
          <div className="strategy-driver-card"
            key={item.driver}
            style={{ marginBottom: 12 }}
          >
            <div className="strategy-card-heading">
              <strong>{item.driver}</strong>
              <span>
                {item.current_compound} · {item.current_tyre_age} laps old
              </span>
            </div>

            <div className="strategy-summary-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: 10,
                marginTop: 12
              }}
            >
              <Stat label="RECOMMENDATION"
                value={recommendation.action.replaceAll("_", " ").toUpperCase()} />
              <Stat label="NEXT COMPOUND"
                value={recommendation.compound} />
              <Stat label="EST. REMAINING TIME"
                value={formatTime(recommendation.estimated_remaining_seconds)} />
              <Stat label="PIT IN"
                value={`${recommendation.laps_until_pit} laps`} />
            </div>

            <h4 className="strategy-subheading">RECOMMENDED STINT PLAN</h4>
            <StintList stints={recommendation.stints} />

            <h4 className="strategy-subheading">ALTERNATIVES</h4>

            {(item.alternatives ?? []).map((alternative, index) => (
              <div className="strategy-card-meta"
                key={`${item.driver}-alternative-${index}`}
                style={{ padding: "8px 0", borderTop: "1px solid #29313b" }}
              >
                <span>
                  {alternative.action.replaceAll("_", " ")} ·
                  {" "}{alternative.compound} ·
                  {" "}{alternative.laps_until_pit} laps until pit
                </span>
                <strong>
                  {formatTime(alternative.estimated_remaining_seconds)}
                </strong>
              </div>
            ))}
          </div>
        );
      })}

      <p className="small-note strategy-metric-note">{data.model_note}</p>
    </div>
  );
}

export default function StrategySimulator({
  season = 2024,
  race = "British Grand Prix",
  availableDrivers = ["VER", "HAM"],
}) {
  const [mode, setMode] = useState("historical");
  const [pitLoss, setPitLoss] = useState(22);
  const [maxStops, setMaxStops] = useState(3);
  const [raceLaps, setRaceLaps] = useState(52);
  const [selectedDriver, setSelectedDriver] = useState("ALL");

  const [remainingLaps, setRemainingLaps] = useState(20);
  const [driverStates, setDriverStates] = useState({
    VER: { current_compound: "MEDIUM", tyre_age: 15 },
    HAM: { current_compound: "HARD", tyre_age: 10 },
  });

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function updateDriver(driver, field, value) {
    setDriverStates((previous) => ({
      ...previous,
      [driver]: {
        ...previous[driver],
        [field]: value,
      },
    }));
  }

  async function runSimulation() {
    setLoading(true);
    setError("");
    setData(null);

    try {
      let endpoint;
      let payload;

      if (mode === "historical") {
        endpoint = `/race/${season}/${encodeURIComponent(race)}/strategy/simulate`;

        payload = {
          pit_loss_seconds: Number(pitLoss),
          max_stops: Number(maxStops),
          race_laps: Number(raceLaps),
          driver: selectedDriver === "ALL" ? null : selectedDriver,
        };
      } else {
        endpoint = `/race/${season}/${encodeURIComponent(race)}/strategy/live`;

        payload = {
          remaining_laps: Number(remainingLaps),
          pit_loss_seconds: Number(pitLoss),
          max_stops: Number(maxStops),
          driver_states: driverStates,
        };
      }

      const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Simulation request failed.");
      }

      setData(result);
    } catch (err) {
      setError(err.message || "Unable to run simulation.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel strategy-simulator-panel">
      <div className="panel-title">
        <span>APEX STRATEGY ENGINE · SIMULATION</span>
        <Gauge size={17} />
      </div>

      <div style={{ display: "flex", gap: 8, margin: "14px 0" }}>
        <button
          className={`strategy-mode-button ${mode === "historical" ? "active" : ""}`}
          onClick={() => {
            setMode("historical");
            setData(null);
            setError("");
          }}
        >
          HISTORICAL
        </button>

        <button
          className={`strategy-mode-button ${mode === "live" ? "active" : ""}`}
          onClick={() => {
            setMode("live");
            setData(null);
            setError("");
          }}
        >
          LIVE SNAPSHOT
        </button>
      </div>

      <div className="strategy-controls-grid">
        <label>
          PIT LOSS (SECONDS)
          <input
            type="number"
            min="0"
            max="90"
            value={pitLoss}
            onChange={(e) => setPitLoss(e.target.value)}
          />
        </label>

        <label>
          MAXIMUM STOPS
          <select
            value={maxStops}
            onChange={(e) => setMaxStops(Number(e.target.value))}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </label>
      </div>

      {mode === "historical" ? (
        <div className="strategy-controls-grid">
          <label>
            RACE LAPS
            <input
              type="number"
              min="10"
              max="120"
              value={raceLaps}
              onChange={(e) => setRaceLaps(e.target.value)}
            />
          </label>

          <label>
            DRIVER
            <select
              value={selectedDriver}
              onChange={(e) => setSelectedDriver(e.target.value)}
            >
              <option value="ALL">Entire field</option>
              {availableDrivers.map((driver) => (
                <option key={driver} value={driver}>{driver}</option>
              ))}
            </select>
          </label>
        </div>
      ) : (
        <>
          <label className="strategy-live-laps">
            REMAINING LAPS
            <input
              type="number"
              min="1"
              max="120"
              value={remainingLaps}
              onChange={(e) => setRemainingLaps(e.target.value)}
            />
          </label>

          <h3 className="strategy-subheading">CURRENT DRIVER TYRE STATES</h3>

          {Object.entries(driverStates).map(([driver, state]) => (
            <div className="strategy-live-driver" key={driver}>
              <strong>{driver}</strong>

              <label>
                COMPOUND
                <select
                  value={state.current_compound}
                  onChange={(e) =>
                    updateDriver(driver, "current_compound", e.target.value)
                  }
                >
                  {COMPOUNDS.map((compound) => (
                    <option key={compound} value={compound}>{compound}</option>
                  ))}
                </select>
              </label>

              <label>
                TYRE AGE
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={state.tyre_age}
                  onChange={(e) =>
                    updateDriver(driver, "tyre_age", Number(e.target.value))
                  }
                />
              </label>
            </div>
          ))}
        </>
      )}

      <button
        className="strategy-run-button"
        onClick={runSimulation}
        disabled={loading}
      >
        {loading ? (
          <><RefreshCw size={16} className="spin" /> ANALYZING...</>
        ) : (
          <><Play size={16} /> RUN STRATEGY SIMULATION</>
        )}
      </button>

      {error && <p className="error-text">{error}</p>}

      {data && (
        <div className="strategy-results">
          <h3 className="strategy-subheading">
            {mode === "historical"
              ? "HISTORICAL OPTIMIZATION RESULTS"
              : "LIVE STRATEGY RECOMMENDATIONS"}
          </h3>

          {mode === "historical" ? (
            <HistoricalResults data={data} />
          ) : (
            <LiveResults data={data} />
          )}

          {data.limitations?.length > 0 && (
            <>
              <h3 className="strategy-subheading">MODEL LIMITATIONS</h3>
              <ul className="small-note">
                {data.limitations.map((limitation, index) => (
                  <li key={index}>{limitation}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </section>
  );
}
