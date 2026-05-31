import { useEffect, useState } from "react";
import { fetchTopPerformerAnalytics } from "./api";

export default function TopPerformerAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchTopPerformerAnalytics()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading top performer analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>🏆 TOP PERFORMER ANALYTICS</h2>
        <p>Find which players your model predicts best and worst.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best Player</span>
          <strong>{data.best_player?.player || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Best ROI</span>
          <strong>{data.best_player?.roi || 0}%</strong>
        </div>

        <div className="stat-card">
          <span>Worst Player</span>
          <strong>{data.worst_player?.player || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Worst ROI</span>
          <strong>{data.worst_player?.roi || 0}%</strong>
        </div>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Player</span>
          <span>Team</span>
          <span>Plays</span>
          <span>HR Hits</span>
          <span>Hit Rate</span>
          <span>Profit</span>
          <span>ROI</span>
          <span>Signal</span>
        </div>

        {data.players?.map((p) => (
          <div className="results-row" key={p.player}>
            <span>{p.player}</span>
            <span>{p.team}</span>
            <span>{p.plays}</span>
            <span>{p.hr_hits}</span>
            <span>{p.hit_rate}%</span>
            <span>{p.profit}u</span>
            <span>{p.roi}%</span>
            <span>{p.signal}</span>
          </div>
        ))}
      </div>
    </section>
  );
}