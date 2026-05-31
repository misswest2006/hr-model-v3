import { useEffect, useState } from "react";
import { fetchTeamAnalytics } from "./api";

export default function TeamAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchTeamAnalytics()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading team analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>🏟️ TEAM ANALYTICS</h2>
        <p>Find which teams your HR model predicts best and worst.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best Team</span>
          <strong>{data.best_team?.team || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Best ROI</span>
          <strong>{data.best_team?.roi || 0}%</strong>
        </div>

        <div className="stat-card">
          <span>Worst Team</span>
          <strong>{data.worst_team?.team || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Worst ROI</span>
          <strong>{data.worst_team?.roi || 0}%</strong>
        </div>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Team</span>
          <span>Plays</span>
          <span>HR Hits</span>
          <span>Hit Rate</span>
          <span>Profit</span>
          <span>Stake</span>
          <span>ROI</span>
          <span>Signal</span>
        </div>

        {data.teams?.map((t) => (
          <div className="results-row" key={t.team}>
            <span>{t.team}</span>
            <span>{t.plays}</span>
            <span>{t.hr_hits}</span>
            <span>{t.hit_rate}%</span>
            <span>{t.profit}u</span>
            <span>{t.stake}u</span>
            <span>{t.roi}%</span>
            <span>{t.signal}</span>
          </div>
        ))}
      </div>
    </section>
  );
}