import { useEffect, useMemo, useState } from "react";
import { fetchSlate } from "./api";
import "./App.css";

const FOUR_HOURS = 14400000;

const SPORTSBOOKS = {
  FanDuel: { label: "FanDuel", logo: "/fanduel-logo.png" },
  DraftKings: { label: "DraftKings", logo: "/draftkings-logo.png" },
  BetMGM: { label: "BetMGM", logo: "/betmgm-logo.png" },
};

const TEAM_LOGO_FALLBACKS = {
  "Arizona Diamondbacks": "https://a.espncdn.com/i/teamlogos/mlb/500/ari.png",
  "Atlanta Braves": "https://a.espncdn.com/i/teamlogos/mlb/500/atl.png",
  "Baltimore Orioles": "https://a.espncdn.com/i/teamlogos/mlb/500/bal.png",
  "Boston Red Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/bos.png",
  "Chicago Cubs": "https://a.espncdn.com/i/teamlogos/mlb/500/chc.png",
  "Chicago White Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/chw.png",
  "Cincinnati Reds": "https://a.espncdn.com/i/teamlogos/mlb/500/cin.png",
  "Cleveland Guardians": "https://a.espncdn.com/i/teamlogos/mlb/500/cle.png",
  "Colorado Rockies": "https://a.espncdn.com/i/teamlogos/mlb/500/col.png",
  "Detroit Tigers": "https://a.espncdn.com/i/teamlogos/mlb/500/det.png",
  "Houston Astros": "https://a.espncdn.com/i/teamlogos/mlb/500/hou.png",
  "Kansas City Royals": "https://a.espncdn.com/i/teamlogos/mlb/500/kc.png",
  "Los Angeles Angels": "https://a.espncdn.com/i/teamlogos/mlb/500/laa.png",
  "Los Angeles Dodgers": "https://a.espncdn.com/i/teamlogos/mlb/500/lad.png",
  "Miami Marlins": "https://a.espncdn.com/i/teamlogos/mlb/500/mia.png",
  "Milwaukee Brewers": "https://a.espncdn.com/i/teamlogos/mlb/500/mil.png",
  "Minnesota Twins": "https://a.espncdn.com/i/teamlogos/mlb/500/min.png",
  "New York Mets": "https://a.espncdn.com/i/teamlogos/mlb/500/nym.png",
  "New York Yankees": "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png",
  Athletics: "https://a.espncdn.com/i/teamlogos/mlb/500/ath.png",
  "Philadelphia Phillies": "https://a.espncdn.com/i/teamlogos/mlb/500/phi.png",
  "Pittsburgh Pirates": "https://a.espncdn.com/i/teamlogos/mlb/500/pit.png",
  "San Diego Padres": "https://a.espncdn.com/i/teamlogos/mlb/500/sd.png",
  "San Francisco Giants": "https://a.espncdn.com/i/teamlogos/mlb/500/sf.png",
  "Seattle Mariners": "https://a.espncdn.com/i/teamlogos/mlb/500/sea.png",
  "St. Louis Cardinals": "https://a.espncdn.com/i/teamlogos/mlb/500/stl.png",
  "Tampa Bay Rays": "https://a.espncdn.com/i/teamlogos/mlb/500/tb.png",
  "Texas Rangers": "https://a.espncdn.com/i/teamlogos/mlb/500/tex.png",
  "Toronto Blue Jays": "https://a.espncdn.com/i/teamlogos/mlb/500/tor.png",
  "Washington Nationals": "https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png",
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
  return play.includes("YES") ? "Yes 🔥" : "No";
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

function getTeamLogo(team, picks) {
  const apiLogo = picks.find((pick) => pick.team === team && pick.team_logo)?.team_logo;
  return apiLogo || TEAM_LOGO_FALLBACKS[team] || "";
}

function getTeamGame(team, picks) {
  return picks.find((pick) => pick.team === team)?.game || "";
}

function gradeClass(grade) {
  if (grade === "A+" || grade === "A") return "grade-value grade-a";
  if (grade === "B") return "grade-value grade-b";
  if (grade === "C") return "grade-value grade-c";
  return "grade-value grade-d";
}

function playClass(play) {
  return play?.includes("YES") ? "play-value play-yes" : "play-value play-no";
}

function hrScore(pick) {
  const confidence = Number(pick.confidence || 0);
  const edge = Number(pick.best_edge || 0) * 100;
  const power = Number(pick.power_score || 0) / 2.5;
  const score = Math.round(confidence * 0.55 + edge * 1.4 + power * 0.35);
  return Math.max(0, Math.min(99, score));
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

function TeamLogo({ src, team, size = "md" }) {
  return (
    <div className={`team-logo team-logo-${size}`}>
      {src ? <img src={src} alt={team} /> : <span>{initials(team)}</span>}
    </div>
  );
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

function PlayerCard({ pick, index }) {
  return (
    <article className="player-card">
      <div className="player-top">
        <div className="rank-chip">#{index + 1}</div>

        <PlayerHeadshot pick={pick} />

        <div className="player-name-block">
          <h3>{pick.player}</h3>
          <p>{pick.team}</p>
          <small>
            Pitcher: {pick.pitcher} • Lineup Spot: {pick.lineup_spot || "-"}
          </small>
        </div>

        <div className="odds-logo-block">
          <SportsbookLogo book={pick.best_book} />
          <strong>{pick.best_odds}</strong>
        </div>
      </div>

      <div className="metric-grid">
        <Metric label="Model Prob" value={percent(pick.model_prob)} />
        <Metric
          label="Edge"
          value={edgePercent(pick.best_edge)}
          tone={Number(pick.best_edge) >= 0 ? "positive" : "negative"}
        />
        <Metric label="Confidence" value={pick.confidence ?? "-"} />
        <Metric label="HR Score" value={hrScore(pick)} />
        <Metric label="Raw Prob" value={percent(pick.raw_model_prob)} />
        <Metric label="Power Score" value={pick.power_score ?? "-"} />
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

  return (
    <section className="model-play-card">
      <div className="model-main">
        <div className="model-label">💎 MODEL PLAY OF THE DAY 💎</div>

        <div className="model-player-row">
          <PlayerHeadshot pick={pick} large />

          <div>
            <h2>{pick.player}</h2>
            <p>{pick.team} vs {pick.pitcher}</p>

            <div className="model-pills">
              <span className={gradeClass(pick.grade)}>Grade: {pick.grade}</span>
              <span className={playClass(pick.play)}>Play: {cleanPlay(pick.play)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="model-metrics">
        <Metric label="Model Prob" value={percent(pick.model_prob)} />
        <Metric
          label="Edge"
          value={edgePercent(pick.best_edge)}
          tone={Number(pick.best_edge) >= 0 ? "positive" : "negative"}
        />
        <Metric label="Best Odds" value={pick.best_odds} />

        <div className="metric sportsbook-metric">
          <span>Best Sportsbook</span>
          <SportsbookLogo book={pick.best_book} />
        </div>
      </div>
    </section>
  );
}

function TopPlayerBox({ player }) {
  if (!player) return null;

  return (
    <div className="top-player-box">
      <div className="top-player-title">🚀 Top Player</div>
      <div className="top-player-name">{player.player}</div>
      <div className="top-player-stats">
        <span>{percent(player.model_prob)}</span>
        <span>•</span>
        <b className={Number(player.best_edge) >= 0 ? "positive" : "negative"}>
          {edgePercent(player.best_edge)}
        </b>
      </div>
    </div>
  );
}

function MatchupDropdown({ group, allPicks, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  const opponent = opponentFromGame(group.game, group.team);
  const opponentLogo = getTeamLogo(opponent, allPicks);

  const topPlayer = [...group.players].sort((a, b) => {
    const probDiff = Number(b.model_prob || 0) - Number(a.model_prob || 0);
    if (probDiff !== 0) return probDiff;
    return Number(b.best_edge || 0) - Number(a.best_edge || 0);
  })[0];

  return (
    <section className="matchup-card">
      <button className="matchup-header" onClick={() => setOpen(!open)}>
        <div className="matchup-title-row">
          <TeamLogo src={group.team_logo || getTeamLogo(group.team, allPicks)} team={group.team} size="lg" />

          <h2>{group.team}</h2>

          <span className="matchup-vs">vs</span>

          <h3>{opponent || "Opponent"}</h3>

          <TeamLogo src={opponentLogo} team={opponent} size="md" />
        </div>

        <TopPlayerBox player={topPlayer} />

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

function TeamShowcaseSection({ team, players, allPicks, rankMode = "edge" }) {
  const logo = getTeamLogo(team, allPicks);
  const game = getTeamGame(team, allPicks);
  const opponent = opponentFromGame(game, team);
  const opponentLogo = getTeamLogo(opponent, allPicks);

  const subtitle =
    rankMode === "edge"
      ? `Top ${players.length} by highest edge`
      : `Top ${players.length} by highest model probability`;

  return (
    <section className="team-showcase-section">
      <div className="team-showcase-header">
        <div className="team-showcase-team">
          <TeamLogo src={logo} team={team} size="lg" />
          <h2>{team}</h2>
        </div>

        <div className="team-showcase-vs">VS</div>

        <div className="team-showcase-team opponent-side">
          <h3>{opponent || "Opponent"}</h3>
          <TeamLogo src={opponentLogo} team={opponent} size="lg" />
        </div>
      </div>

      <div className="team-showcase-subtitle">{subtitle}</div>

      <div className="top3-grid">
        {players.map((pick, index) => (
          <PlayerCard key={`${team}-${pick.player}-${index}`} pick={pick} index={index} />
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

  const matchupGroups = useMemo(() => {
    const grouped = {};

    validPicks.forEach((pick) => {
      const key = `${pick.game}__${pick.team}`;

      if (!grouped[key]) {
        grouped[key] = {
          game: pick.game,
          team: pick.team,
          team_logo: pick.team_logo || getTeamLogo(pick.team, validPicks),
          players: [],
        };
      }

      grouped[key].players.push(pick);
    });

    Object.keys(grouped).forEach((key) => {
      grouped[key].players = grouped[key].players.sort((a, b) => {
        const probDiff = Number(b.model_prob || 0) - Number(a.model_prob || 0);
        if (probDiff !== 0) return probDiff;
        return Number(b.best_edge || 0) - Number(a.best_edge || 0);
      });
    });

    return Object.values(grouped).sort((a, b) => {
      const gameSort = a.game.localeCompare(b.game);
      if (gameSort !== 0) return gameSort;
      return a.team.localeCompare(b.team);
    });
  }, [validPicks]);

  const topPlayersByTeam = useMemo(() => {
    const grouped = {};

    validPicks.forEach((pick) => {
      if (!grouped[pick.team]) grouped[pick.team] = [];
      grouped[pick.team].push(pick);
    });

    return Object.entries(grouped)
      .map(([team, players]) => [
        team,
        [...players]
          .sort((a, b) => {
            const edgeDiff = Number(b.best_edge || 0) - Number(a.best_edge || 0);
            if (edgeDiff !== 0) return edgeDiff;
            return Number(b.model_prob || 0) - Number(a.model_prob || 0);
          })
          .slice(0, 3),
      ])
      .sort(([a], [b]) => a.localeCompare(b));
  }, [validPicks]);

  const highProbabilityByTeam = useMemo(() => {
    const grouped = {};

    validPicks.forEach((pick) => {
      if (!grouped[pick.team]) grouped[pick.team] = [];
      grouped[pick.team].push(pick);
    });

    return Object.entries(grouped)
      .map(([team, players]) => [
        team,
        [...players]
          .sort((a, b) => {
            const probDiff = Number(b.model_prob || 0) - Number(a.model_prob || 0);
            if (probDiff !== 0) return probDiff;
            return Number(b.best_edge || 0) - Number(a.best_edge || 0);
          })
          .slice(0, 4),
      ])
      .sort(([a], [b]) => a.localeCompare(b));
  }, [validPicks]);

  const modelPlay = useMemo(() => {
    if (!validPicks.length) return null;

    return [...validPicks].sort((a, b) => {
      const edgeDiff = Number(b.best_edge || 0) - Number(a.best_edge || 0);
      if (edgeDiff !== 0) return edgeDiff;
      return Number(b.model_prob || 0) - Number(a.model_prob || 0);
    })[0];
  }, [validPicks]);

  const avgEdge = useMemo(() => {
    if (!validPicks.length) return "0.0%";
    const sum = validPicks.reduce((acc, pick) => acc + Number(pick.best_edge || 0), 0);
    return edgePercent(sum / validPicks.length);
  }, [validPicks]);

  const topEdge = useMemo(() => {
    if (!validPicks.length) return "0.0%";
    const top = Math.max(...validPicks.map((pick) => Number(pick.best_edge || 0)));
    return edgePercent(top);
  }, [validPicks]);

  const yesPlays = validPicks.filter((pick) => pick.play?.includes("YES"));
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
          <button className={activeTab === "dashboard" ? "active" : ""} onClick={() => switchTab("dashboard")}>
            🏠 Dashboard
          </button>

          <button className={activeTab === "top" ? "active" : ""} onClick={() => switchTab("top")}>
            🔥 Top Players
          </button>

          <button className={activeTab === "probability" ? "active" : ""} onClick={() => switchTab("probability")}>
            📈 High Probability Plays
          </button>
        </nav>

        <div className="bankroll-card">
          <span>Refresh</span>
          <strong>Every 4 Hours</strong>
          <button onClick={loadSlate}>Refresh Now</button>
        </div>

        <div className="motto-card">
          <div>💎</div>
          <p>Discipline.</p>
          <p>Data.</p>
          <p>Diamonds.</p>
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

        <section className="stats-grid">
          <StatCard icon="💎" label="Total Graded Plays" value={validPicks.length} />
          <StatCard icon="🔥" label="YES Plays" value={yesPlays.length} />
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

        {activeTab === "top" && (
          <div className="page-title">
            <h2>💎 TOP PLAYERS 💎</h2>
            <p>Top 3 by highest edge for each team</p>
          </div>
        )}

        {activeTab === "probability" && (
          <div className="page-title">
            <h2>📈 HIGH PROBABILITY PLAYS</h2>
            <p>Top 4 by highest model probability for each team</p>
          </div>
        )}

        <ModelPlayOfDay pick={modelPlay} />

        {loading ? (
          <div className="empty-state">Loading slate...</div>
        ) : validPicks.length === 0 ? (
          <div className="empty-state">No completed player rows yet. Run stat enrichment and the model.</div>
        ) : activeTab === "dashboard" ? (
          <section className="matchup-list">
            {matchupGroups.map((group, index) => (
              <MatchupDropdown
                key={`${group.game}-${group.team}`}
                group={group}
                allPicks={validPicks}
                defaultOpen={index < 1}
              />
            ))}
          </section>
        ) : activeTab === "top" ? (
          <section className="team-showcase-grid">
            {topPlayersByTeam.map(([team, players]) => (
              <TeamShowcaseSection
                key={team}
                team={team}
                players={players}
                allPicks={validPicks}
                rankMode="edge"
              />
            ))}
          </section>
        ) : (
          <section className="team-showcase-grid">
            {highProbabilityByTeam.map(([team, players]) => (
              <TeamShowcaseSection
                key={team}
                team={team}
                players={players}
                allPicks={validPicks}
                rankMode="probability"
              />
            ))}
          </section>
        )}

        <footer className="footer-motto">💎 Discipline. Data. Diamonds. 💎</footer>
      </main>
    </div>
  );
}