import { useEffect, useMemo, useState } from "react";
import { fetchSlate, fetchYesTracker, fetchYesResults } from "./api";
import "./App.css";
import ModelHealth from "./ModelHealth";
import ConfidenceAnalytics from "./ConfidenceAnalytics";
import SnapshotAnalytics from "./SnapshotAnalytics";
import TopPerformerAnalytics from "./TopPerformerAnalytics";
import FeatureAnalytics from "./FeatureAnalytics";
import AutoTuner from "./AutoTuner";
import EvAnalytics from "./EvAnalytics";
import TeamAnalytics from "./TeamAnalytics";
import TodayPlays from "./TodayPlays";

const FOUR_HOURS = 14400000;

const SPORTSBOOKS = {
  FanDuel: { label: "FanDuel", logo: "/fanduel-logo.png" },
  DraftKings: { label: "DraftKings", logo: "/draftkings-logo.png" },
  BetMGM: { label: "BetMGM", logo: "/betmgm-logo.png" },
};

function percent(value) {
  if (value === undefined || value === null || value === "") return "0.0%";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function edgePercent(value) {
  if (value === undefined || value === null || value === "") return "0.0%";
  const num = Number(value) * 100;
  return `${num >= 0 ? "+" : ""}${num.toFixed(1)}%`;
}

function cleanPlay(play) {
  if (!play) return "No";
  if (play.includes("YES")) return "Yes 🔥";
  if (play.includes("POWER")) return "Power Bat 💣";
  if (play.includes("VALUE")) return "Value Lean 👀";
  return play;
}

function initials(name) {
  if (!name) return "?";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function opponentFromGame(game, team) {
  if (!game || !team || !game.includes(" vs ")) return "";
  const [away, home] = game.split(" vs ");
  if (away === team) return home;
  if (home === team) return away;
  return "";
}

function gradeClass(grade) {
  if (grade === "A+" || grade === "A") return "grade-value grade-a";
  if (grade === "B") return "grade-value grade-b";
  if (grade === "C") return "grade-value grade-c";
  return "grade-value grade-d";
}

function playClass(play) {
  if (!play) return "play-value play-no";
  if (play.includes("YES")) return "play-value play-yes";
  if (play.includes("POWER")) return "play-value play-yes";
  if (play.includes("VALUE")) return "play-value play-yes";
  return "play-value play-no";
}

function hrScore(pick) {
  return Math.round(Number(pick.hr_score || 0));
}

function decisionScore(pick) {
  return Math.round(Number(pick.decision_score || 0));
}

function pickLadder(pick) {
  const edge = Number(pick?.best_edge || 0);
  const confidence = Number(pick?.confidence || 0);
  const weakness = Number(pick?.pitcher_weakness_score || 0);
  const spotMatch = Number(pick?.pitcher_lineup_weak_spot || 0);
  const modelProb = Number(pick?.model_prob || 0);
  const lineup = Number(pick?.lineup_spot || 0);
  const backendPlay = String(pick?.play || "");
  const backendTier = String(pick?.tier || "");
  const backendGrade = String(pick?.grade || "");
  const backendDecision = Number(pick?.decision_score || 0);
  const backendHR = Number(pick?.hr_score || 0);

  if (backendPlay.includes("YES")) {
    return {
      label: "MODEL YES 🔥",
      rank: 5,
      reason: `${backendGrade || "Grade"} ${backendTier || ""} | HR ${Math.round(
        backendHR
      )} | Decision ${Math.round(backendDecision)}`,
    };
  }

  if (backendPlay.includes("POWER")) {
    return {
      label: "POWER BAT 💣",
      rank: 4,
      reason: `${backendGrade || "Grade"} ${backendTier || ""} | HR ${Math.round(
        backendHR
      )} | Decision ${Math.round(backendDecision)}`,
    };
  }

  if (backendPlay.includes("LEAN")) {
    return {
      label: "VALUE LEAN 👀",
      rank: 3,
      reason: `${backendGrade || "Grade"} ${backendTier || ""} | HR ${Math.round(
        backendHR
      )} | Decision ${Math.round(backendDecision)}`,
    };
  }

  const hasElitePitcherCombo = weakness >= 10 && spotMatch >= 10;
  const hasStrongPitcherCombo = weakness >= 8 && spotMatch >= 8;
  const hasPositiveEdge = edge > 0;
  const hasGoodEdge = edge >= 0.05;
  const hasOkayConfidence = confidence >= 65;
  const hasGoodConfidence = confidence >= 70;
  const isMiddleOrValueLineup = lineup >= 4 && lineup <= 9;

  if (
    hasElitePitcherCombo &&
    hasGoodEdge &&
    hasGoodConfidence &&
    isMiddleOrValueLineup
  ) {
    return {
      label: "MUST BET 🔥",
      rank: 5,
      reason: "10/10 Weakness + 10/10 Spot Match + strong edge + lineup value",
    };
  }

  if (hasElitePitcherCombo && hasPositiveEdge && hasOkayConfidence) {
    return {
      label: "STRONG LOOK 💣",
      rank: 4,
      reason: "10/10 Weakness + 10/10 Spot Match + positive edge",
    };
  }

  if (hasStrongPitcherCombo && hasPositiveEdge && confidence >= 60) {
    return {
      label: "SPRINKLE ONLY ⚡",
      rank: 3,
      reason: "Strong pitcher setup with positive edge",
    };
  }

  if (modelProb >= 0.2 && confidence >= 75 && hasPositiveEdge) {
    return {
      label: "WATCH 👀",
      rank: 2,
      reason: "Good model profile but missing elite pitcher confirmation",
    };
  }

  return {
    label: "PASS",
    rank: 1,
    reason: "Not enough confirmed HR signals",
  };
}

function SportsbookLogo({ book }) {
  const data = SPORTSBOOKS[book];

  if (!data) {
    return <div className="sportsbook-text">{book || "Book"}</div>;
  }

  return (
    <div className="sportsbook-full-logo">
      <img src={data.logo} alt={data.label} />
    </div>
  );
}

function Metric({ label, value, tone = "" }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
    </div>
  );
}

function PlayerHeadshot({ pick, large = false }) {
  return (
    <div className={large ? "headshot headshot-large" : "headshot"}>
      {pick.player_headshot ? (
        <img src={pick.player_headshot} alt={pick.player} />
      ) : (
        <span>{initials(pick.player)}</span>
      )}
    </div>
  );
}

function PlayerCard({ pick, index }) {
  const dScore = decisionScore(pick);
  const ladder = pickLadder(pick);

  return (
    <article className="player-card">
      <div className="player-top clean-player-top">
        <div className="rank-chip">#{index + 1}</div>

        <PlayerHeadshot pick={pick} />

        <div className="player-name-block clean-name-block">
          <h3>{pick.player}</h3>
          <p>{pick.team}</p>
        </div>

        <div className="odds-logo-block">
          <SportsbookLogo book={pick.best_book} />
          <strong>{pick.best_odds || "-"}</strong>
        </div>
      </div>

      <div className="clean-info-row">
        <span>Pitcher: {pick.pitcher}</span>
        <span>Lineup Spot: {pick.lineup_spot || "-"}</span>
        <span>🕒 {pick.game_time || "-"}</span>
        <span>📸 {pick.snapshot || "MANUAL"}</span>
      </div>

      <div className="rank-badge-row">
        <span className="edge-badge">{ladder.label}</span>
        <span className="prob-badge">Decision {dScore}</span>
        <span className="tier-badge">{pick.tier || "WATCH"}</span>
      </div>

      <div className="metric-grid">
        <Metric label="Pick Ladder" value={ladder.label} />
        <Metric label="Decision Score" value={dScore} />
        <Metric label="Reason" value={ladder.reason} />
        <Metric label="Model Prob" value={percent(pick.model_prob)} />
        <Metric
          label="Edge"
          value={edgePercent(pick.best_edge)}
          tone={Number(pick.best_edge) >= 0 ? "positive" : "negative"}
        />
        <Metric label="Confidence" value={pick.confidence ?? "-"} />
        <Metric label="Pitcher Weakness" value={`🔥 ${pick.pitcher_weakness_score ?? 0}/10`} />
        <Metric label="Pitcher Spot Match" value={`🎯 ${pick.pitcher_lineup_weak_spot ?? 0}/10`} />
        <Metric label="HR Score" value={hrScore(pick)} />
        <Metric label="EV Score" value={pick.ev_score ?? "-"} />
        <Metric label="Decision Score" value={decisionScore(pick)} />
        <Metric label="Power Score" value={pick.power_score ?? "-"} />
        <Metric label="Smash Score" value={pick.smash_score ?? "-"} />
        <Metric label="Lineup Boost" value={pick.lineup_boost ?? "-"} />
        <Metric label="Stake" value={`${pick.stake || 0}u`} />
      </div>

      <div className="player-footer">
        <span className={gradeClass(pick.grade)}>Grade: {pick.grade}</span>
        <span className={playClass(pick.play)}>Play: {cleanPlay(pick.play)}</span>
      </div>
    </article>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function ModelPlayOfDay({ pick }) {
  if (!pick) return null;

  const dScore = decisionScore(pick);
  const ladder = pickLadder(pick);

  return (
    <section className="model-play-card">
      <div className="model-main">
        <div className="model-label">💎 MODEL PLAY OF THE DAY 💎</div>

        <div className="model-player-row">
          <PlayerHeadshot pick={pick} large />

          <div>
            <h2>{pick.player}</h2>
            <p>
              {pick.team} vs {pick.pitcher}
            </p>

            <div className="model-pills">
              <span className={gradeClass(pick.grade)}>Grade: {pick.grade}</span>
              <span className={playClass(pick.play)}>Play: {cleanPlay(pick.play)}</span>
              <span className="tier-badge">{ladder.label}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="model-metrics">
        <Metric label="Decision Score" value={dScore} />
        <Metric label="Pick Ladder" value={ladder.label} />
        <Metric label="Model Prob" value={percent(pick.model_prob)} />
        <Metric label="Edge" value={edgePercent(pick.best_edge)} />
        <Metric label="Best Odds" value={pick.best_odds} />
      </div>
    </section>
  );
}

function MatchupDropdown({ group, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  const topPlayer = [...group.players].sort((a, b) => {
    const hrDiff = hrScore(b) - hrScore(a);
    if (hrDiff !== 0) return hrDiff;

    const decisionDiff = decisionScore(b) - decisionScore(a);
    if (decisionDiff !== 0) return decisionDiff;

    return Number(b.best_edge || 0) - Number(a.best_edge || 0);
  })[0];

  return (
    <section className="matchup-card">
      <button className="matchup-header" onClick={() => setOpen(!open)}>
        <div className="matchup-title-row">
          <h2>{group.team}</h2>
          <span className="matchup-vs">vs</span>
          <h3>{group.opponent || "Opponent"}</h3>
        </div>

        <div className="top-player-box">
          <div className="top-player-title">🚀 Top Pick</div>
          <div className="top-player-name">{topPlayer?.player}</div>
          <div className="top-player-stats">
            <span>{pickLadder(topPlayer).label}</span>
            <span>•</span>
            <b>{edgePercent(topPlayer?.best_edge)}</b>
          </div>
        </div>

        <div className="dropdown-control">
          <span>{group.players.length}</span>
          <b>{open ? "▲" : "▼"}</b>
        </div>
      </button>

      {open && (
        <div className="matchup-body">
          {group.players.map((pick, index) => (
            <PlayerCard key={`${group.team}-${pick.player}-${index}`} pick={pick} index={index} />
          ))}
        </div>
      )}
    </section>
  );
}

function YesPlaysSection({ yesPicks }) {
  const [tracker, setTracker] = useState(null);

  useEffect(() => {
    fetchYesTracker().then(setTracker).catch(console.error);
  }, []);

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>🔥 YES PLAYS 🔥</h2>
        <p>YES plays ranked by HR Score first, then Decision Score.</p>
      </div>

      {tracker && (
        <div className="stats-grid" style={{ marginBottom: "24px" }}>
          <StatCard icon="🔥" label="YES Plays" value={tracker.yes_plays} />
          <StatCard icon="💣" label="HR Hits" value={tracker.hr_hits} />
          <StatCard icon="⏳" label="Pending" value={tracker.pending} />
          <StatCard icon="📈" label="Hit Rate" value={`${tracker.hit_rate}%`} />
          <StatCard icon="💰" label="Profit" value={`${tracker.profit}u`} />
        </div>
      )}

      <div className="top3-grid">
        {yesPicks.map((pick, index) => (
          <PlayerCard key={`yes-${pick.player}-${index}`} pick={pick} index={index} />
        ))}
      </div>
    </section>
  );
}

function SmashSpotSection({ picks }) {
  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>🔥 SMASH SPOT PLAYS 🔥</h2>
        <p>Players with elite pitcher weakness and pitcher spot match.</p>
      </div>

      <div className="top3-grid">
        {picks.map((pick, index) => (
          <PlayerCard key={`smash-${pick.player}-${index}`} pick={pick} index={index} />
        ))}
      </div>
    </section>
  );
}

function ResultsCenter() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    fetchYesResults().then(setRows).catch(console.error);
  }, []);

  return (
    <section className="team-showcase-section">
      <div className="page-title">
        <h2>📊 RESULTS CENTER</h2>
        <p>Live YES play results, profit, snapshot, and grading status.</p>
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span>Player</span>
          <span>Team</span>
          <span>Snapshot</span>
          <span>Odds</span>
          <span>Conf</span>
          <span>Grade</span>
          <span>Result</span>
          <span>Profit</span>
        </div>

        {rows.map((r, i) => (
          <div className="results-row" key={`${r.player}-${i}`}>
            <span>{r.player}</span>
            <span>{r.team}</span>
            <span>{r.snapshot}</span>
            <span>
              {r.book} {r.odds}
            </span>
            <span>{r.confidence}</span>
            <span>{r.grade}</span>
            <span>{r.result}</span>
            <span>{r.profit}u</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [picks, setPicks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  async function loadSlate() {
    try {
      setLoading(true);
      const data = await fetchSlate();
      setPicks(data?.picks || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Backend not responding", error);
      setPicks([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSlate();
    const interval = setInterval(loadSlate, FOUR_HOURS);
    return () => clearInterval(interval);
  }, []);

  const validPicks = useMemo(() => {
    return picks.filter((pick) => pick.player && pick.team);
  }, [picks]);

  const rankedPicks = useMemo(() => {
    return [...validPicks].sort((a, b) => {
      const hrDiff = hrScore(b) - hrScore(a);
      if (hrDiff !== 0) return hrDiff;

      const decisionDiff = decisionScore(b) - decisionScore(a);
      if (decisionDiff !== 0) return decisionDiff;

      return Number(b.best_edge || 0) - Number(a.best_edge || 0);
    });
  }, [validPicks]);

  const yesPicks = useMemo(() => {
    return rankedPicks.filter((pick) => pick.play?.includes("YES"));
  }, [rankedPicks]);

  const smashSpotPicks = useMemo(() => {
    return rankedPicks.filter((pick) => {
      const smash = Number(pick.smash_score || 0);
      const hr = Number(pick.hr_score || 0);
      const decision = Number(pick.decision_score || 0);

      return smash >= 70 || (hr >= 98 && decision >= 80);
    });
  }, [rankedPicks]);

  const matchupGroups = useMemo(() => {
    const grouped = {};

    rankedPicks.forEach((pick) => {
      const opponent = opponentFromGame(pick.game, pick.team);
      const key = `${pick.game}__${pick.team}`;

      if (!grouped[key]) {
        grouped[key] = {
          game: pick.game,
          team: pick.team,
          opponent,
          players: [],
        };
      }

      grouped[key].players.push(pick);
    });

    return Object.values(grouped);
  }, [rankedPicks]);

  const groupedByTeam = useMemo(() => {
    const grouped = {};

    rankedPicks.forEach((pick) => {
      if (!grouped[pick.team]) grouped[pick.team] = [];
      grouped[pick.team].push(pick);
    });

    return Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b));
  }, [rankedPicks]);

  const modelPlay = rankedPicks[0] || null;

  const avgEdge = useMemo(() => {
    const validEdges = validPicks.filter((pick) => {
      const edge = Number(pick.best_edge);
      return Number.isFinite(edge) && edge > -100;
    });

    if (!validEdges.length) return "0.0%";

    const sum = validEdges.reduce(
      (acc, pick) => acc + Number(pick.best_edge || 0),
      0
    );

    return edgePercent(sum / validEdges.length);
  }, [validPicks]);

  const topEdge = useMemo(() => {
    if (!validPicks.length) return "0.0%";
    const top = Math.max(...validPicks.map((pick) => Number(pick.best_edge || 0)));
    return edgePercent(top);
  }, [validPicks]);

  const totalStake = validPicks.reduce((acc, pick) => acc + Number(pick.stake || 0), 0);
  const teamCount = new Set(validPicks.map((pick) => pick.team)).size;

  function switchTab(tab) {
    setActiveTab(tab);
    setSidebarOpen(false);
  }

  return (
    <div className="app">
      <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
        ☰
      </button>

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      <aside className={sidebarOpen ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <div className="brand-crown">♕</div>
          <h1>BeYOUnique</h1>
          <div className="brand-diamond">◇</div>
          <p>Discipline. Data. Diamonds.</p>
        </div>

        <nav>
          <button className={activeTab === "dashboard" ? "active" : ""} onClick={() => switchTab("dashboard")}>🏠 Dashboard</button>
          <button className={activeTab === "today" ? "active" : ""} onClick={() => switchTab("today")}>📱 Live Today</button>
          <button className={activeTab === "smash" ? "active" : ""} onClick={() => switchTab("smash")}>🔥 Smash Spot</button>
          <button className={activeTab === "yes" ? "active" : ""} onClick={() => switchTab("yes")}>🔥 YES Plays</button>
          <button className={activeTab === "results" ? "active" : ""} onClick={() => switchTab("results")}>📊 Results Center</button>
          <button className={activeTab === "top" ? "active" : ""} onClick={() => switchTab("top")}>🔥 Top Players</button>
          <button className={activeTab === "health" ? "active" : ""} onClick={() => switchTab("health")}>🩺 Model Health</button>
          <button className={activeTab === "confidence" ? "active" : ""} onClick={() => switchTab("confidence")}>📈 Confidence Analytics</button>
          <button className={activeTab === "snapshot" ? "active" : ""} onClick={() => switchTab("snapshot")}>📸 Snapshot Analytics</button>
          <button className={activeTab === "performers" ? "active" : ""} onClick={() => switchTab("performers")}>🏆 Top Performers</button>
          <button className={activeTab === "features" ? "active" : ""} onClick={() => switchTab("features")}>🧬 Feature Analytics</button>
          <button className={activeTab === "autotuner" ? "active" : ""} onClick={() => switchTab("autotuner")}>🤖 Auto Tuner</button>
          <button className={activeTab === "ev" ? "active" : ""} onClick={() => switchTab("ev")}>💰 EV Analytics</button>
          <button className={activeTab === "teams" ? "active" : ""} onClick={() => switchTab("teams")}>🏟️ Team Analytics</button>
        </nav>

        <div className="bankroll-card">
          <span>Refresh</span>
          <strong>Every 4 Hours</strong>
          <button onClick={loadSlate}>Refresh Now</button>
        </div>
      </aside>

      <main className="main">
        <header className="hero-header">
          <div className="hero-diamond hero-left">💎</div>
          <div>
            <h1>HR BETTING</h1>
            <h2>◇ DASHBOARD ◇</h2>
          </div>
          <div className="hero-diamond hero-right">💎</div>
        </header>

        {activeTab !== "health" && activeTab !== "today" && (
          <>
            <section className="stats-grid">
              <StatCard icon="💎" label="Total Graded Plays" value={validPicks.length} />
              <StatCard icon="🔥" label="YES Plays" value={yesPicks.length} />
              <StatCard icon="💥" label="Smash Spots" value={smashSpotPicks.length} />
              <StatCard icon="📈" label="Avg Edge" value={avgEdge} />
              <StatCard icon="👑" label="Top Edge" value={topEdge} />
              <StatCard icon="💰" label="Total Stake" value={`${totalStake.toFixed(1)}u`} />
            </section>

            <div className="toolbar">
              <button className="refresh-btn" onClick={loadSlate}>
                ↻ Refresh Slate
              </button>

              <div className="updated-text">
                Last updated:{" "}
                {lastUpdated
                  ? lastUpdated.toLocaleString([], {
                      month: "numeric",
                      day: "numeric",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "--"}
              </div>

              <div className="team-count-display">{teamCount} teams loaded</div>
            </div>
          </>
        )}

        {activeTab !== "health" &&
          activeTab !== "yes" &&
          activeTab !== "results" &&
          activeTab !== "smash" &&
          activeTab !== "today" && (
            <ModelPlayOfDay pick={modelPlay} />
          )}

        {activeTab === "health" ? (
          <ModelHealth />
        ) : activeTab === "today" ? (
          <TodayPlays />
        ) : loading ? (
          <div className="empty-state">Loading slate...</div>
        ) : validPicks.length === 0 ? (
          <div className="empty-state">No completed player rows yet. Run stat enrichment and the model.</div>
        ) : activeTab === "smash" ? (
          <SmashSpotSection picks={smashSpotPicks} />
        ) : activeTab === "yes" ? (
          <YesPlaysSection yesPicks={yesPicks} />
        ) : activeTab === "results" ? (
          <ResultsCenter />
        ) : activeTab === "confidence" ? (
          <ConfidenceAnalytics />
        ) : activeTab === "snapshot" ? (
          <SnapshotAnalytics />
        ) : activeTab === "performers" ? (
          <TopPerformerAnalytics />
        ) : activeTab === "features" ? (
          <FeatureAnalytics />
        ) : activeTab === "autotuner" ? (
          <AutoTuner />
        ) : activeTab === "ev" ? (
          <EvAnalytics />
        ) : activeTab === "teams" ? (
          <TeamAnalytics />
        ) : activeTab === "top" ? (
          <section className="team-showcase-grid">
            {groupedByTeam.map(([team, players]) => (
              <section className="team-showcase-section" key={team}>
                <div className="page-title">
                  <h2>{team}</h2>
                  <p>Ranked by HR Score first, then Decision Score.</p>
                </div>

                <div className="top3-grid">
                  {players.map((pick, index) => (
                    <PlayerCard key={`${team}-${pick.player}-${index}`} pick={pick} index={index} />
                  ))}
                </div>
              </section>
            ))}
          </section>
        ) : (
          <section className="matchup-list">
            {matchupGroups.map((group) => (
              <MatchupDropdown
                key={`${group.game}-${group.team}`}
                group={group}
                defaultOpen={true}
              />
            ))}
          </section>
        )}

        <footer className="footer-motto">💎 Discipline. Data. Diamonds. 💎</footer>
      </main>
    </div>
  );
}