import React, { useEffect, useRef } from 'react';
import { fluidSimulation } from './fluid.js';
import './hero.css';

function Arrow() {
  return <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

export default function Hero({ snapshot, leagueName }) {
  const stage = useRef(null);
  useEffect(() => {
    const canvas = stage.current.querySelector('canvas');
    const pause = stage.current.querySelector('#mm-pause');
    const status = stage.current.querySelector('#mm-motion-status');
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    let simulation;
    function syncMotion() {
      const paused = motion.matches || pause.checked;
      canvas.hidden = paused;
      if (!paused && !simulation) {
        try {
          simulation = fluidSimulation(canvas);
        } catch (error) {
          console.warn('MatchMind: WebGL unavailable; retaining the CSS background.', error);
          pause.checked = true;
          canvas.hidden = true;
          status.textContent = 'Static background mode. Predictions remain available.';
        }
      }
      simulation?.setPaused(paused || pause.checked);
    }
    syncMotion();
    pause.addEventListener('change', syncMotion);
    motion.addEventListener('change', syncMotion);
    return () => {
      simulation?.destroy();
      pause.removeEventListener('change', syncMotion);
      motion.removeEventListener('change', syncMotion);
    };
  }, []);

  const cutoff = snapshot?.end ? new Date(`${snapshot.end}T00:00:00Z`).toLocaleDateString('en-GB', {
    month: 'long', year: 'numeric', timeZone: 'UTC',
  }) : 'the historical snapshot';

  return <section className="mm-hero" ref={stage} aria-labelledby="mm-title">
    <div className="mm-atmosphere" aria-hidden="true" />
    <canvas className="mm-fluid" aria-hidden="true" />
    <div className="mm-scrim" aria-hidden="true" />
    <header className="mm-nav">
      <a className="mm-brand" href="#predict-match" aria-label="MatchMind AI — go to predictions">
        <svg viewBox="0 0 30 30" fill="none" aria-hidden="true"><rect x="2" y="4" width="26" height="22" rx="6" stroke="currentColor" strokeWidth="1.5" /><path d="M15 4v22M2 11h4v8H2m26-8h-4v8h4" stroke="currentColor" strokeWidth="1.3" /><circle cx="15" cy="15" r="4.2" stroke="currentColor" strokeWidth="1.3" /></svg>
        MatchMind AI
      </a>
      <nav className="mm-links" aria-label="Main navigation">
        <a href="#predict-match">Predictions</a><a href="#performance">Performance</a><a href="#model-notes">The model</a>
      </nav>
      <a className="mm-button" href="#predict-match">Explore a fixture <span aria-hidden="true">↗</span></a>
    </header>
    <figure className="mm-player mm-player-left">
      <div className="mm-player-photo"><img src="/photos/haaland.jpg" alt="Erling Haaland in a Manchester City shirt, photographed in 2023" width="1224" height="1599" fetchPriority="high" /></div>
      <figcaption>Erling Haaland<span>Football icons</span></figcaption>
    </figure>
    <figure className="mm-player mm-player-right">
      <div className="mm-player-photo"><img src="/photos/salah.png" alt="Mohamed Salah in a Liverpool shirt on the pitch" width="547" height="365" fetchPriority="high" /></div>
      <figcaption>Mohamed Salah<span>Football icons</span></figcaption>
    </figure>
    <div className="mm-center">
      <p className="mm-badge">Premier League &amp; La Liga. Beyond the score.</p>
      <h1 className="mm-title" id="mm-title">{['The', 'beautiful', 'game.'].map((word, i) => <React.Fragment key={word}><span className="mm-word" style={{ '--word': i }}>{word}</span>{' '}</React.Fragment>)}<br />{['A', 'clearer', 'picture.'].map((word, i) => <React.Fragment key={word}><span className="mm-word" style={{ '--word': i + 3 }}>{word}</span>{' '}</React.Fragment>)}</h1>
      <p className="mm-subtitle">Every fixture has a story. Explore its possibilities with real match history and honest probabilities.</p>
      <div className="mm-action"><p>Two teams. Three outcomes.</p><a className="mm-button" href="#predict-match">Pick your fixture <Arrow /></a></div>
      <p className="mm-freshness">Historical data through {cutoff}. No live injury feed.</p>
    </div>
    <footer className="mm-bottom">
      <p><span className="mm-match-count">{snapshot ? `${snapshot.matches.toLocaleString()} matches.` : 'Real match history.'}</span>{snapshot ? `${snapshot.seasons.length} seasons of ${leagueName} history.` : 'Premier League and La Liga analysis.'}<br />Independent project. No player endorsement.</p>
      <a className="mm-scroll" href="#predict-match"><span aria-hidden="true">↓</span> Explore the match</a>
      <div className="mm-controls">
        <label className="mm-motion-control"><input type="checkbox" id="mm-pause" />Pause motion</label>
        <details className="mm-credits" id="mm-photo-credits"><summary>Football photography / credits</summary>
          Haaland: <a href="https://commons.wikimedia.org/wiki/File:Erling_Haaland_2023_(fullcropped-v2).jpg" target="_blank" rel="noreferrer">Jacek Stanislawek</a> / <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>.<br />
          Salah: user-supplied photograph; photographer and licence unspecified.<br />Cropped and toned for display. <a href="/photo-credits.txt">Full credits</a>.
        </details>
      </div>
    </footer>
    <p className="mm-sr-only" id="mm-motion-status" role="status" />
  </section>;
}
