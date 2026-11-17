import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Hero from './Hero.jsx';
import { requestJson } from './api.js';
import './styles.css';

const percent = (value) => `${(value * 100).toFixed(1)}%`;
const displayDate = (value) => new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
});
const modelNames = { raw_poisson: 'Raw Poisson', calibrated_poisson: 'Calibrated Poisson',
  historical_frequency: 'Historical frequencies', always_home: 'Always home' };

function FixtureResult({ result, snapshot }) {
  return <div className="fixture-result">
    <header className="result-heading"><div><p className="section-label">Match outlook</p><h3>{result.home} <span>vs</span> {result.away}</h3><p className="muted">{result.home} at home · historical model</p></div>
      <div className="score"><span>Most likely score</span><strong>{result.score[0]} <span>–</span> {result.score[1]}</strong><span>{percent(result.score_probability)} exact-score probability</span></div>
    </header>
    <div className="probability-grid" aria-label="Outcome probabilities">
      {['Home win', 'Draw', 'Away win'].map((label, i) => <div className="probability" key={label}>
        <span>{label}</span><strong>{percent(result.probabilities[i])}</strong>
        <div className="probability-track" aria-hidden="true"><div style={{ width: percent(result.probabilities[i]) }} /></div>
      </div>)}
    </div>
    <p className="goals-note">Model expected goals: <strong>{result.home_goals.toFixed(2)}</strong> home / <strong>{result.away_goals.toFixed(2)}</strong> away.</p>
    <p className="fine-print">Goal-rate estimates, not shot-based xG. The exact score uses the raw Poisson distribution; calibrated outcome probabilities can favour a different winner.</p>
    <div className="form-heading"><h3>Recent historical form</h3><p className="muted">Last 10 recorded matches per team</p></div>
    <div className="table-scroll"><table className="stats-table"><caption className="sr-only">Historical team statistics, ending {displayDate(snapshot.end)}</caption><thead><tr><th scope="col">Team</th><th scope="col">Matches</th><th scope="col">Goals / match</th><th scope="col">Conceded / match</th><th scope="col">Points / match</th></tr></thead><tbody>
      {result.stats.map((team) => <tr key={team.team}><th scope="row">{team.team}</th><td>{team.matches}</td><td>{team.goals_per_match.toFixed(2)}</td><td>{team.conceded_per_match.toFixed(2)}</td><td>{team.points_per_match.toFixed(2)}</td></tr>)}
    </tbody></table></div>
    <p className="fine-print">Descriptive context through {displayDate(snapshot.end)}. These averages are not additional model inputs.</p>
  </div>;
}

function Performance({ meta }) {
  const query = `?league=${encodeURIComponent(meta.league.id)}`;
  return <section id="performance" className="content-section" aria-labelledby="performance-title">
    <div className="section-heading"><div><p className="section-label">{meta.league.name} evaluation</p><h2 id="performance-title">Tested on a future season.</h2></div><a className="text-link" href={`/api/evaluation${query}`} download={`${meta.league.id}-evaluation.json`}>Download evaluation ↗</a></div>
    <p className="section-intro">Training ended {displayDate(meta.splits.train.end)}. Calibration used the next season. The {meta.splits.test.count} test matches, from {displayDate(meta.splits.test.start)} to {displayDate(meta.splits.test.end)}, stayed outside both steps.</p>
    {meta.snapshot.missing_results > 0 && <p className="honesty-note">Partial test-season coverage: {meta.snapshot.missing_results} fixture results are missing from the pinned upstream source and are excluded, not estimated.</p>}
    <div className="table-scroll"><table><caption className="sr-only">Held-out evaluation. Higher accuracy is better; lower log loss and Brier are better.</caption><thead><tr><th scope="col">Predictor</th><th scope="col">Accuracy</th><th scope="col">Log loss</th><th scope="col">Brier score</th></tr></thead><tbody>
      {Object.entries(meta.metrics).map(([key, values]) => <tr key={key}><th scope="row">{modelNames[key] || key}</th><td>{percent(values.accuracy)}</td><td>{values.log_loss.toFixed(3)}</td><td>{values.brier.toFixed(3)}</td></tr>)}
    </tbody></table></div>
    <p className="honesty-note">Compare calibrated and raw log loss above. Calibration is not guaranteed to improve future predictions, and the test set was not used to tune the model.</p>
    <details className="method-details"><summary>What these measurements mean</summary><div><p>Accuracy counts the most likely outcome. Log loss penalizes confident mistakes. Multiclass Brier sums squared probability errors across home, draw and away (0–2).</p><p>{meta.production_note}</p><p>The downloadable report includes reliability bins, sample counts, dates, promoted-team treatment and source checksums.</p></div></details>
  </section>;
}

function App() {
  const [league, setLeague] = useState('premier-league');
  const [leagues, setLeagues] = useState([]);
  const [meta, setMeta] = useState(null);
  const [home, setHome] = useState('Arsenal');
  const [away, setAway] = useState('Chelsea');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setError(''); setBusy(true); setMeta(null); setResult(null);
    async function load() {
      try {
        const catalog = await requestJson('/api/leagues', { signal: controller.signal });
        if (controller.signal.aborted) return;
        setLeagues(catalog.leagues);
        const data = await requestJson(`/api/meta?league=${encodeURIComponent(league)}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setMeta(data);
        const preferred = league === 'la-liga' ? ['FC Barcelona', 'Real Madrid CF'] : ['Arsenal', 'Chelsea'];
        const initialHome = data.teams.includes(preferred[0]) ? preferred[0] : data.teams[0];
        const initialAway = data.teams.includes(preferred[1]) ? preferred[1] : data.teams[1];
        setHome(initialHome); setAway(initialAway);
        const prediction = await requestJson('/api/predict', { method: 'POST',
          headers: { 'Content-Type': 'application/json' }, signal: controller.signal,
          body: JSON.stringify({ league, home: initialHome, away: initialAway }) });
        if (!controller.signal.aborted) setResult(prediction);
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message);
      } finally {
        if (!controller.signal.aborted) setBusy(false);
      }
    }
    load();
    return () => controller.abort();
  }, [attempt, league]);

  async function submit(event) {
    event.preventDefault();
    setResult(null); setError('');
    if (home === away) { setError('Choose two different teams.'); return; }
    setBusy(true);
    try {
      setResult(await requestJson('/api/predict', { method: 'POST',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ league, home, away }) }));
    } catch (failure) { setError(failure.message); }
    finally { setBusy(false); }
  }

  function changeTeam(setter, value) { setter(value); setResult(null); setError(''); }
  function changeLeague(value) { setMeta(null); setResult(null); setError(''); setBusy(true); setLeague(value); }
  const leagueName = leagues.find((item) => item.id === league)?.name || 'Premier League';

  return <>
    <a className="skip-link" href="#predict-match">Skip to match predictor</a>
    <Hero snapshot={meta?.snapshot} leagueName={leagueName} />
    <main className="app-content">
      <section id="predict-match" className="content-section predictor" aria-labelledby="predict-title" aria-busy={busy}>
        <div className="section-heading"><div><p className="section-label">Your fixture. Its possibilities.</p><h2 id="predict-title">Pick the next match.</h2></div>{meta && <p className="snapshot">Snapshot through<br /><strong>{displayDate(meta.snapshot.end)}</strong></p>}</div>
        <p className="section-intro">Choose two teams from the historical {leagueName} snapshot. See the outcome probabilities, most likely score and the numbers behind them.</p>
        <div className="league-picker"><label htmlFor="league">League<select id="league" value={league} disabled={busy || !leagues.length} onChange={(event) => changeLeague(event.target.value)}>{leagues.length ? leagues.map((item) => <option key={item.id} value={item.id}>{item.name}</option>) : <option value={league}>Loading leagues…</option>}</select></label><p>Independent team models and evaluation for each league.</p></div>
        <div className="snapshot-notice"><span className="notice-dot" aria-hidden="true" /><p>Historical analysis. No live injuries, lineups, transfers or odds. The team list reflects the dataset, not current league membership.</p></div>
        {meta?.snapshot.missing_results > 0 && <p className="honesty-note">{meta.snapshot.missing_results} upstream {leagueName} results are missing and excluded. This snapshot contains {meta.snapshot.matches.toLocaleString()} completed matches.</p>}
        {error && <div className="error-state" role="alert"><p>{error}</p>{!meta && <button className="secondary-button" type="button" onClick={() => setAttempt(attempt + 1)} disabled={busy}>Retry connection</button>}</div>}
        <form className="fixture-form" onSubmit={submit}>
          <div className="team-fields"><label htmlFor="home-team">Home team<select id="home-team" value={home} disabled={!meta || busy} onChange={(e) => changeTeam(setHome, e.target.value)}>{meta ? meta.teams.map((team) => <option key={team}>{team}</option>) : <option>Loading teams…</option>}</select></label><span className="versus" aria-hidden="true">vs</span><label htmlFor="away-team">Away team<select id="away-team" value={away} disabled={!meta || busy} onChange={(e) => changeTeam(setAway, e.target.value)}>{meta ? meta.teams.map((team) => <option key={team}>{team}</option>) : <option>Loading teams…</option>}</select></label></div>
          <button className="primary-button" type="submit" disabled={!meta || busy}>{busy ? 'Calculating…' : 'Predict match'}<span aria-hidden="true">↗</span></button>
        </form>
        <p role="status" aria-live="polite" className={busy ? 'loading-note' : 'sr-only'}>{busy ? 'Loading match data and probabilities…' : result ? `Prediction ready for ${result.home} against ${result.away}.` : ''}</p>
        {result ? <FixtureResult result={result} snapshot={meta.snapshot} /> : !busy && !error && <div className="empty-state"><h3>A new fixture, a new picture.</h3><p>Select Predict match to calculate the possibilities.</p></div>}
      </section>
      {meta && <Performance meta={meta} />}
      <section id="model-notes" className="content-section method-section" aria-labelledby="model-title">
        <div><p className="section-label">Behind the forecast</p><h2 id="model-title">Football is uncertain.<br />The model should say so.</h2></div>
        <div className="method-copy"><p>Each league has its own model and data. Historical team attack, defence and home advantage estimate each side’s goal rate. A Poisson model turns those rates into scorelines and outcome probabilities. A separate, later season learns the calibration temperature.</p><p>Older results receive less weight. Promoted teams unseen during evaluation receive league-average strengths. No test results enter the frozen evaluation model.</p><p>The app model is refitted on its league’s dataset. Its future accuracy is unmeasured, and the old calibration temperature may not transfer well. No injuries, player ratings, live updates or betting guarantees are included.</p><div className="method-links"><a className="text-link" href={`/api/matches.csv?league=${encodeURIComponent(league)}`} download={`${league}-matches.csv`}>Download {leagueName} matches ↗</a><a className="text-link" href="https://github.com/openfootball/football.json" target="_blank" rel="noreferrer">OpenFootball / CC0 ↗</a></div></div>
      </section>
      <footer className="app-footer"><a href="#mm-title" className="footer-brand">MatchMind AI</a><p>Real history. Estimated probabilities. No guaranteed outcomes.</p><a href="/photo-credits.txt">Photo & animation credits</a></footer>
    </main>
  </>;
}

createRoot(document.getElementById('root')).render(<App />);
