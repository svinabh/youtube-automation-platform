"use client";

import { useEffect, useState } from "react";
import "./style.css";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function RiskBadge({ level }) {
  return <span className={"risk risk-" + String(level || "LOW").toLowerCase()}>{level || "LOW"}</span>;
}

function ReviewCard({ video, onChanged }) {
  const [watched, setWatched] = useState(false);
  const [disclosureAnswer, setDisclosureAnswer] = useState(
    typeof video.disclosure_suggestion === "boolean" ? video.disclosure_suggestion : null
  );
  const [disclosureTouched, setDisclosureTouched] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const canDecide =
    watched &&
    disclosureTouched &&
    disclosureAnswer !== null &&
    videoReady &&
    !videoError &&
    !busy;

  const submitDecision = async (approve) => {
    setBusy(true);
    setError("");
    try {
      const reviewResponse = await fetch(API + "/api/videos/" + video.id + "/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          watched_confirmed: watched,
          disclosure_answer: disclosureAnswer,
        }),
      });
      const reviewData = await reviewResponse.json().catch(() => ({}));
      if (!reviewResponse.ok) {
        throw new Error(reviewData.detail || "Review save nahi ho paaya. Dobara try karo.");
      }

      const approvalResponse = await fetch(API + "/api/videos/" + video.id + "/approval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approve }),
      });
      const approvalData = await approvalResponse.json().catch(() => ({}));
      if (!approvalResponse.ok) {
        throw new Error(approvalData.detail || "Decision save nahi ho paaya. Dobara try karo.");
      }
      onChanged();
    } catch (err) {
      setError(err.message || "Decision save nahi ho paaya. Dobara try karo.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="review-card">
      <div className="review-heading">
        <div>
          <div className="eyebrow">🎬 Ready for your review</div>
          <h3>{video.title}</h3>
          <p className="topic"><strong>Topic:</strong> {video.topic}</p>
        </div>
        <span className="status">READY FOR REVIEW</span>
      </div>

      <div className="video-wrap">
        {video.artifact_path ? (
          <video
            className="player"
            controls
            playsInline
            preload="metadata"
            src={API + "/api/videos/" + video.id + "/media"}
            onCanPlay={() => {
              setVideoReady(true);
              setVideoError(false);
            }}
            onError={() => {
              setVideoReady(false);
              setVideoError(true);
            }}
          />
        ) : (
          <div className="video-message">Video file abhi available nahi hai.</div>
        )}
      </div>

      <div className="video-actions">
        <a href={API + "/api/videos/" + video.id + "/media"} download>
          Video download fallback
        </a>
        {!videoReady && !videoError && <span>Video load ho raha hai…</span>}
        {videoError && (
          <span className="error-inline">
            Video abhi load nahi ho paaya, dobara try karo.
          </span>
        )}
      </div>

      <details className="context-panel">
        <summary>📝 Script / Brief dekhein</summary>
        <div className="context-grid">
          <div>
            <h4>Script</h4>
            <pre>{video.script || "Script available nahi hai."}</pre>
          </div>
          <div>
            <h4>Production brief</h4>
            <pre>{video.brief || "Brief available nahi hai."}</pre>
          </div>
        </div>
      </details>

      <div className="checks">
        <div className="check-row">
          <span>⚖ Rights cleared</span>
          <strong>{video.rights_cleared ? "✅" : "❌"}</strong>
        </div>
        <div className="check-row">
          <span>🛡 Advertiser risk</span>
          <RiskBadge level={video.advertiser_risk_level} />
        </div>
      </div>

      <div className="disclosure-panel">
        <div>
          <h4>🔖 AI / synthetic-content disclosure</h4>
          <p>
            System suggestion: <strong>{video.disclosure_suggestion ? "Required" : "Not indicated"}</strong>
          </p>
          <p className="hint">
            {video.disclosure_suggestion_reason || "No suggestion reason available."}
          </p>
        </div>
        <div className="toggle" role="group" aria-label="Disclosure answer">
          <button
            type="button"
            className={disclosureAnswer === true ? "toggle-button selected" : "toggle-button"}
            onClick={() => {
              setDisclosureAnswer(true);
              setDisclosureTouched(true);
            }}
          >
            Yes
          </button>
          <button
            type="button"
            className={disclosureAnswer === false ? "toggle-button selected" : "toggle-button"}
            onClick={() => {
              setDisclosureAnswer(false);
              setDisclosureTouched(true);
            }}
          >
            No
          </button>
        </div>
        {!disclosureTouched && (
          <p className="hint">System suggestion pre-selected hai. Final answer ke liye Yes/No ko khud confirm karein.</p>
        )}
      </div>

      <label className="watch-confirm">
        <input
          type="checkbox"
          checked={watched}
          onChange={(event) => setWatched(event.target.checked)}
        />
        <span>
          <strong>Maine poora video dekh liya hai</strong>
          <br />
          aur ye script/brief se match karta hai.
        </span>
      </label>

      <p className="text-only-note">
        Automated checks sirf title, description, script/brief aur metadata dekhte hain.
        Actual video/audio match ka final confirmation aapko karna hai.
      </p>

      {error && <div className="error-box">{error}</div>}

      <div className="decision-actions">
        <button
          className="primary"
          disabled={!canDecide}
          onClick={() => submitDecision(true)}
        >
          ✅ Approve
        </button>
        <button
          className="secondary"
          disabled={!canDecide}
          onClick={() => submitDecision(false)}
        >
          ❌ Reject
        </button>
      </div>

      {!canDecide && (
        <p className="gate-note">
          Decision ke liye video play hona, disclosure answer ko khud select karna, aur
          watch-confirmation checkbox tick karna zaroori hai.
        </p>
      )}
    </section>
  );
}

export default function Home() {
  const [d, setD] = useState({ pending: [], recent: [] });
  const [loadError, setLoadError] = useState("");

  const load = () =>
    fetch(API + "/api/dashboard")
      .then(async (response) => {
        if (!response.ok) throw new Error("Dashboard load nahi ho paaya.");
        return response.json();
      })
      .then((data) => {
        setD(data);
        setLoadError("");
      })
      .catch(() => setLoadError("Dashboard abhi load nahi ho paaya, dobara try karo."));

  useEffect(() => {
    load();
  }, []);

  return (
    <main>
      <header className="page-header">
        <div>
          <div className="eyebrow">Founder control center</div>
          <h1>YouTube Automation</h1>
          <p>Pending videos ko ek hi screen par dekhkar final human decision lein.</p>
        </div>
        <div className="pending-count">{d.pending.length} pending</div>
      </header>

      {loadError && <div className="error-box">{loadError}</div>}

      <h2>Needs your review</h2>
      {d.pending.length === 0 ? (
        <div className="empty card">Abhi koi video review ke liye pending nahi hai.</div>
      ) : (
        d.pending.map((video) => (
          <ReviewCard key={video.id} video={video} onChanged={load} />
        ))
      )}

      <h2>Recent</h2>
      {d.recent.map((video) => (
        <div className="row" key={video.id}>
          <span>{video.title}</span>
          <span>{video.state}</span>
        </div>
      ))}
    </main>
  );
}
