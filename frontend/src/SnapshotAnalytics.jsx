import { useEffect, useState } from "react";
import { fetchSnapshotAnalytics } from "./api";

export default function SnapshotAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchSnapshotAnalytics()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading snapshot analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>📸 SNAPSHOT ANALYTICS</h2>
        <p>Compare MORNING, ONE_HOUR, LOCK, and MANUAL model performance.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best Snapshot</span>
          <strong>{data.best_snapshot?.snapshot || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Total YES Plays</span>
          <strong>{data.total_yes_plays}</strong>
        </div>

        <div className="stat-card">
          <span>Total HR Hits</span>
          <strong>{data.total_hr_hits}</strong>
        </div>

        <div className="stat-card">
          <span>Total ROI</span>
          <strong>{data.total_roi}%</strong>
        </div>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Snapshot</span>
          <span>Plays</span>
          <span>HR Hits</span>
          <span>Hit Rate</span>
          <span>Profit</span>
          <span>Stake</span>
          <span>ROI</span>
          <span>Signal</span>
        </div>

        {data.snapshots?.map((s) => (
          <div className="results-row" key={s.snapshot}>
            <span>{s.snapshot}</span>
            <span>{s.plays}</span>
            <span>{s.hr_hits}</span>
            <span>{s.hit_rate}%</span>
            <span>{s.profit}u</span>
            <span>{s.stake}u</span>
            <span>{s.roi}%</span>
            <span>{s.signal}</span>
          </div>
        ))}
      </div>
    </section>
  );
}