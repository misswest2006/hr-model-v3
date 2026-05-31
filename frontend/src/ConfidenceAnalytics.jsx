import { useEffect, useState } from "react";
import { fetchConfidenceAnalytics } from "./api";

export default function ConfidenceAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchConfidenceAnalytics()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading confidence analytics...</div>;
  }

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>📈 CONFIDENCE ANALYTICS</h2>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Best Bucket</span>
          <strong>{data.best_bucket?.bucket || "-"}</strong>
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
          <span>Bucket</span>
          <span>Plays</span>
          <span>HR Hits</span>
          <span>Hit Rate</span>
          <span>Profit</span>
          <span>ROI</span>
          <span>Signal</span>
        </div>

        {data.buckets?.map((b) => (
          <div key={b.bucket} className="results-row">
            <span>{b.bucket}</span>
            <span>{b.plays}</span>
            <span>{b.hr_hits}</span>
            <span>{b.hit_rate}%</span>
            <span>{b.profit}u</span>
            <span>{b.roi}%</span>
            <span>{b.signal}</span>
          </div>
        ))}
      </div>
    </section>
  );
}