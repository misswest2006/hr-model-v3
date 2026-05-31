import { useEffect, useState } from "react";
import { fetchFeatureAnalytics } from "./api";

export default function FeatureAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchFeatureAnalytics().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading feature analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>🧠 FEATURE ANALYTICS</h2>
        <p>Find which model signals are actually producing HRs and ROI.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best Feature</span>
          <strong>{data.best_feature?.feature || "-"}</strong>
        </div>

        <div className="stat-card">
          <span>Best ROI</span>
          <strong>{data.best_feature?.roi || 0}%</strong>
        </div>

        <div className="stat-card">
          <span>Total YES Plays</span>
          <strong>{data.total_yes_plays}</strong>
        </div>

        <div className="stat-card">
          <span>Total HR Hits</span>
          <strong>{data.total_hr_hits}</strong>
        </div>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Feature</span>
          <span>Plays</span>
          <span>HR Hits</span>
          <span>Hit Rate</span>
          <span>Profit</span>
          <span>Stake</span>
          <span>ROI</span>
          <span>Signal</span>
        </div>

        {data.features?.map((f) => (
          <div className="results-row" key={f.feature}>
            <span>{f.feature}</span>
            <span>{f.plays}</span>
            <span>{f.hr_hits}</span>
            <span>{f.hit_rate}%</span>
            <span>{f.profit}u</span>
            <span>{f.stake}u</span>
            <span>{f.roi}%</span>
            <span>{f.signal}</span>
          </div>
        ))}
      </div>
    </section>
  );
}