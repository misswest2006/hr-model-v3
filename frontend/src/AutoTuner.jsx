import { useEffect, useState } from "react";
import { fetchAutoTuner } from "./api";

export default function AutoTuner() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchAutoTuner()
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="empty-state">Loading Auto-Tuner...</div>;
  }

  return (
    <section className="team-showcase-section">

      <div className="page-title">
        <h2>🤖 AUTO TUNER</h2>
        <p>
          Model optimization recommendations based on historical results.
        </p>
      </div>

      <div className="stats-grid">

        <div className="stat-card">
          <span>Best Snapshot</span>
          <strong>
            {data.best_snapshot?.snapshot || "-"}
          </strong>
        </div>

        <div className="stat-card">
          <span>Best Feature</span>
          <strong>
            {data.best_feature?.feature || "-"}
          </strong>
        </div>

        <div className="stat-card">
          <span>Best Confidence</span>
          <strong>
            {data.best_confidence_bucket?.bucket || "-"}
          </strong>
        </div>

      </div>

      <div className="results-table">

        <div className="results-row results-header">
          <span>Recommendation</span>
        </div>

        {data.recommendations?.map((item, idx) => (
          <div
            key={idx}
            className="results-row"
          >
            <span>{item}</span>
          </div>
        ))}

      </div>

    </section>
  );
}