import { useEffect, useMemo, useState } from "react";
import { fetchModelHealth, fetchSnapshotHealth } from "./api";

export default function ModelHealth() {
  const [health, setHealth] = useState(null);
  const [snapshots, setSnapshots] = useState([]);

  useEffect(() => {
    fetchModelHealth().then(setHealth).catch(console.error);
    fetchSnapshotHealth().then(setSnapshots).catch(console.error);
  }, []);

  const bestSnapshot = useMemo(() => {
    if (!snapshots.length) return null;

    return [...snapshots].sort((a, b) => {
      const hrDiff = Number(b.hr_hits || 0) - Number(a.hr_hits || 0);
      if (hrDiff !== 0) return hrDiff;

      return Number(b.roi || 0) - Number(a.roi || 0);
    })[0];
  }, [snapshots]);

  if (!health) {
    return <div className="empty-state">Loading model health...</div>;
  }

  const card = {
    background: "rgba(0,0,0,.95)",
    border: "1px solid rgba(255,20,147,.65)",
    borderRadius: "22px",
    padding: "18px",
    boxShadow: "0 0 22px rgba(255,20,147,.2)",
  };

  const winnerCard = {
    ...card,
    border: "1px solid rgba(255,215,0,.85)",
    boxShadow: "0 0 28px rgba(255,215,0,.25)",
  };

  const row = {
    display: "grid",
    gridTemplateColumns: "repeat(6, 1fr)",
    gap: "10px",
    padding: "13px",
    borderRadius: "14px",
    background: "rgba(255,255,255,.05)",
  };

  return (
    <section style={{ display: "grid", gap: "24px" }}>
      <div className="page-title">
        <h2>🩺 MODEL HEALTH 💎</h2>
        <p>Snapshot performance, confidence buckets, grading health, and pending results</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "16px" }}>
        {[
          ["Total Plays", health.total_plays],
          ["YES Plays", health.yes_plays],
          ["Pending Results", health.pending_results],
          ["Avg Confidence", health.avg_confidence],
          ["Avg Edge", `${health.avg_edge}%`],
          ["Avg Model Prob", `${health.avg_model_prob}%`],
        ].map(([label, value]) => (
          <div style={card} key={label}>
            <span style={{ color: "#f7c7df", fontSize: "13px" }}>{label}</span>
            <strong style={{ display: "block", marginTop: "8px", fontSize: "30px" }}>
              {value}
            </strong>
          </div>
        ))}
      </div>

      {bestSnapshot && (
        <div style={winnerCard}>
          <h3 style={{ color: "#ffd700", fontSize: "30px", marginTop: 0 }}>
            🏆 Best Snapshot
          </h3>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: "14px",
            }}
          >
            <div>
              <span style={{ color: "#f7c7df" }}>Snapshot</span>
              <strong style={{ display: "block", fontSize: "30px", color: "#fff" }}>
                {bestSnapshot.snapshot}
              </strong>
            </div>

            <div>
              <span style={{ color: "#f7c7df" }}>YES Plays</span>
              <strong style={{ display: "block", fontSize: "30px", color: "#fff" }}>
                {bestSnapshot.yes_plays}
              </strong>
            </div>

            <div>
              <span style={{ color: "#f7c7df" }}>HR Hits</span>
              <strong style={{ display: "block", fontSize: "30px", color: "#00ff99" }}>
                {bestSnapshot.hr_hits}
              </strong>
            </div>

            <div>
              <span style={{ color: "#f7c7df" }}>Hit Rate</span>
              <strong style={{ display: "block", fontSize: "30px", color: "#fff" }}>
                {bestSnapshot.hit_rate}%
              </strong>
            </div>

            <div>
              <span style={{ color: "#f7c7df" }}>ROI</span>
              <strong style={{ display: "block", fontSize: "30px", color: "#ffd700" }}>
                {bestSnapshot.roi}%
              </strong>
            </div>
          </div>
        </div>
      )}

      <div style={card}>
        <h3 style={{ color: "#ff1493", fontSize: "26px", marginTop: 0 }}>
          📸 Snapshot Performance
        </h3>

        <div style={{ display: "grid", gap: "8px" }}>
          <div style={{ ...row, color: "#ff75c7", fontWeight: 900 }}>
            <span>Snapshot</span>
            <span>Total Plays</span>
            <span>YES Plays</span>
            <span>HR Hits</span>
            <span>Hit Rate</span>
            <span>ROI</span>
          </div>

          {snapshots.map((s) => (
            <div style={row} key={s.snapshot}>
              <span>{s.snapshot}</span>
              <span>{s.total_plays}</span>
              <span>{s.yes_plays}</span>
              <span>{s.hr_hits}</span>
              <span>{s.hit_rate}%</span>
              <span>{s.roi}%</span>
            </div>
          ))}
        </div>
      </div>

      <div style={card}>
        <h3 style={{ color: "#ff1493", fontSize: "26px", marginTop: 0 }}>
          💎 Confidence Buckets
        </h3>

        <div style={{ display: "grid", gap: "8px" }}>
          <div
            style={{
              ...row,
              gridTemplateColumns: "repeat(7, 1fr)",
              color: "#ff75c7",
              fontWeight: 900,
            }}
          >
            <span>Bucket</span>
            <span>Plays</span>
            <span>HRs</span>
            <span>HR Rate</span>
            <span>Avg Edge</span>
            <span>Avg Prob</span>
            <span>ROI</span>
          </div>

          {health.confidence_buckets.map((b) => (
            <div style={{ ...row, gridTemplateColumns: "repeat(7, 1fr)" }} key={b.bucket}>
              <span>{b.bucket}</span>
              <span>{b.plays}</span>
              <span>{b.hrs}</span>
              <span>{b.hr_rate}%</span>
              <span>{b.avg_edge}%</span>
              <span>{b.avg_model_prob}%</span>
              <span>{b.roi}%</span>
            </div>
          ))}
        </div>
      </div>

      <div style={card}>
        <h3 style={{ color: "#ff1493", fontSize: "26px", marginTop: 0 }}>
          🔥 Grade Summary
        </h3>

        <div style={{ display: "grid", gap: "8px" }}>
          <div style={{ ...row, color: "#ff75c7", fontWeight: 900 }}>
            <span>Grade</span>
            <span>Plays</span>
            <span>HRs</span>
            <span>HR Rate</span>
            <span>Profit</span>
            <span>ROI</span>
          </div>

          {health.grade_summary.map((g) => (
            <div style={row} key={g.grade}>
              <span>{g.grade}</span>
              <span>{g.plays}</span>
              <span>{g.hrs}</span>
              <span>{g.hr_rate}%</span>
              <span>{g.profit}</span>
              <span>{g.roi}%</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}