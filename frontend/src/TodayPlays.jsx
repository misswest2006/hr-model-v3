import { useEffect, useState } from "react";
import { fetchTodayPlays } from "./api";

function edgePercent(value) {
  if (value === undefined || value === null || value === "") return "0.0%";
  const num = Number(value) * 100;
  return `${num >= 0 ? "+" : ""}${num.toFixed(1)}%`;
}

function percent(value) {
  if (value === undefined || value === null || value === "") return "0.0%";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function playBadge(playCode) {
  if (playCode === "YES") return "YES 🔥";
  if (playCode === "POWER_BAT") return "POWER BAT 💣";
  if (playCode === "VALUE_LEAN") return "VALUE LEAN 👀";
  return playCode || "-";
}

export default function TodayPlays() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadToday() {
    try {
      setLoading(true);
      const res = await fetchTodayPlays();
      setData(res);
    } catch (error) {
      console.error("Today Plays error", error);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadToday();
  }, []);

  if (loading) {
    return <div className="empty-state">Loading today&apos;s plays...</div>;
  }

  if (!data || !data.plays || data.plays.length === 0) {
    return (
      <section className="team-showcase-section">
        <div className="page-title">
          <h2>🔥 LIVE TODAY CENTER 🔥</h2>
          <p>No official plays yet. Run stat enrichment and the model.</p>
        </div>
      </section>
    );
  }

  const yes = data.yes || [];
  const powerBats = data.power_bats || [];
  const valueLeans = data.value_leans || [];

  function PlayTable({ title, rows }) {
    return (
      <section className="team-showcase-section">
        <div className="page-title">
          <h2>{title}</h2>
          <p>Today&apos;s active model plays from the latest model output.</p>
        </div>

        <div className="results-table">
          <div className="results-row results-header">
            <span>Player</span>
            <span>Team</span>
            <span>Pitcher</span>
            <span>Play</span>
            <span>Odds</span>
            <span>Edge</span>
            <span>Conf</span>
            <span>HR</span>
            <span>Stake</span>
          </div>

          {rows.map((r, i) => (
            <div className="results-row" key={`${r.player}-${i}`}>
              <span>{r.player}</span>
              <span>{r.team}</span>
              <span>{r.pitcher}</span>
              <span>{playBadge(r.PlayCode || r.play_code)}</span>
              <span>{r.best_book} {r.best_odds}</span>
              <span>{edgePercent(r.edge)}</span>
              <span>{r.confidence}</span>
              <span>{r.hr_score}</span>
              <span>{r.stake}u</span>
            </div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="page-title">
        <h2>🔥 LIVE TODAY CENTER 🔥</h2>
        <p>
          Date: {data.date || "-"} | Snapshot: {data.snapshot || "-"} | Total Stake:{" "}
          {data.total_stake || 0}u
        </p>
      </div>

      <div className="stats-grid" style={{ marginBottom: "24px" }}>
        <div className="stat-card">
          <div className="stat-icon">🔥</div>
          <div>
            <span>YES Plays</span>
            <strong>{data.yes_count}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💣</div>
          <div>
            <span>Power Bats</span>
            <strong>{data.power_bat_count}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">👀</div>
          <div>
            <span>Value Leans</span>
            <strong>{data.value_lean_count}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div>
            <span>Total Stake</span>
            <strong>{data.total_stake}u</strong>
          </div>
        </div>
      </div>

      <PlayTable title="🔥 OFFICIAL YES PLAYS 🔥" rows={yes} />
      <PlayTable title="💣 POWER BATS 💣" rows={powerBats} />
      <PlayTable title="👀 VALUE LEANS 👀" rows={valueLeans} />
    </section>
  );
}