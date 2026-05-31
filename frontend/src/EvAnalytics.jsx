import { useEffect, useState } from "react";
import { fetchEvAnalytics } from "./api";

export default function EvAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchEvAnalytics()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading EV analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>💰 EV ANALYTICS</h2>
        <p>Compare model probability against sportsbook implied probability.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best EV Play</span>
          <strong>{data.best_ev_play?.player || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Best EV Edge</span>
          <strong>{data.best_ev_play?.ev_edge || 0}%</strong>
        </div>

        <div className="stat-card">
          <span>Average EV Edge</span>
          <strong>{data.average_edge}%</strong>
        </div>

        <div className="stat-card">
          <span>Total YES Plays</span>
          <strong>{data.total_yes_plays}</strong>
        </div>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Player</span>
          <span>Team</span>
          <span>Book/Odds</span>
          <span>Model Prob</span>
          <span>Implied Prob</span>
          <span>EV Edge</span>
          <span>Conf</span>
          <span>Result</span>
        </div>

        {data.plays?.map((p, i) => (
          <div className="results-row" key={`${p.player}-${i}`}>
            <span>{p.player}</span>
            <span>{p.team}</span>
            <span>{p.book} {p.odds}</span>
            <span>{p.model_prob}%</span>
            <span>{p.implied_prob}%</span>
            <span>{p.ev_edge}%</span>
            <span>{p.confidence}</span>
            <span>{p.result}</span>
          </div>
        ))}
      </div>
    </section>
  );
}