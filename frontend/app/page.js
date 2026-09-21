"use client";

import { useEffect, useState } from "react";
import "./style.css";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const KEY_STORAGE = "yta_founder_api_key";

function authHeaders(token, json = false) {
  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    Authorization: "Bearer " + token,
  };
}

async function apiFetch(path, token, options = {}) {
  const headers = { ...authHeaders(token, Boolean(options.body)), ...(options.headers || {}) };
  const response = await fetch(API + path, { ...options, headers });
  if (response.status === 401) throw new Error("API key invalid ya missing hai.");
  return response;
}

function RiskBadge({ level }) {
  return <span className={"risk risk-" + String(level || "LOW").toLowerCase()}>{level || "LOW"}</span>;
}

function ReviewCard({ video, token, onChanged, onLogout }) {
  const [watched, setWatched] = useState(false);
  const [disclosureAnswer, setDisclosureAnswer] = useState(
    typeof video.disclosure_suggestion === "boolean" ? video.disclosure_suggestion : null
  );
  const [disclosureTouched, setDisclosureTouched] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [mediaUrl, setMediaUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    let objectUrl = "";
    fetch(API + "/api/videos/" + video.id + "/media", {
      headers: authHeaders(token),
    })
      .then((response) => {
        if (response.status === 401) {
          onLogout();
          throw new Error("API key invalid ya missing hai.");
        }
        if (!response.ok) throw new Error("Video load nahi ho paaya.");
        return response.blob();
      })
      .then((blob) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setMediaUrl(objectUrl);
      })
      .catch(() => {
        if (active) setVideoError(true);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [token, video.id, onLogout]);

  const canDecide =
    watched && disclosureTouched && disclosureAnswer !== null && videoReady && !videoError && !busy;

  const downloadVideo = async () => {
    setError("");
    try {
      const response = await apiFetch("/api/videos/" + video.id + "/media", token);
      if (!response.ok) throw new Error("Video download nahi ho paaya.");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = video.id + ".mp4";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err.message.includes("API key")) onLogout();
      setError(err.message || "Video download nahi ho paaya.");
    }
  };

  const submitDecision = async (approve) => {
    setBusy(true);
    setError("");
    try {
      const reviewResponse = await apiFetch("/api/videos/" + video.id + "/review", token, {
        method: "POST",
        body: JSON.stringify({
          watched_confirmed: watched,
          disclosure_answer: disclosureAnswer,
        }),
      });
      const reviewData = await reviewResponse.json().catch(() => ({}));
      if (!reviewResponse.ok) throw new Error(reviewData.detail || "Review save nahi ho paaya.");

      const approvalResponse = await apiFetch("/api/videos/" + video.id + "/approval", token, {
        method: "POST",
        body: JSON.stringify({ approve }),
      });
      const approvalData = await approvalResponse.json().catch(() => ({}));
      if (!approvalResponse.ok) throw new Error(approvalData.detail || "Decision save nahi ho paaya.");
      onChanged();
    } catch (err) {
      if (err.message.includes("API key")) onLogout();
      setError(err.message || "Decision save nahi ho paaya.");
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
        {mediaUrl ? (
          <video
            className="player"
            controls
            playsInline
            preload="metadata"
            src={mediaUrl}
            onCanPlay={() => { setVideoReady(true); setVideoError(false); }}
            onError={() => { setVideoReady(false); setVideoError(true); }}
          />
        ) : (
          <div className="video-message">Video load ho raha hai…</div>
        )}
      </div>

      <div className="video-actions">
        <button type="button" className="link-button" onClick={downloadVideo}>Video download fallback</button>
        {videoError && <span className="error-inline">Video abhi load nahi ho paaya, dobara try karo.</span>}
      </div>

      <details className="context-panel">
        <summary>📝 Script / Brief dekhein</summary>
        <div className="context-grid">
          <div><h4>Script</h4><pre>{video.script || "Script available nahi hai."}</pre></div>
          <div><h4>Production brief</h4><pre>{video.brief || "Brief available nahi hai."}</pre></div>
        </div>
      </details>

      <div className="checks">
        <div className="check-row"><span>⚖ Rights cleared</span><strong>{video.rights_cleared ? "✅" : "❌"}</strong></div>
        <div className="check-row"><span>🛡 Advertiser risk</span><RiskBadge level={video.advertiser_risk_level} /></div>
      </div>

      <div className="disclosure-panel">
        <div>
          <h4>🔖 AI / synthetic-content disclosure</h4>
          <p>System suggestion: <strong>{video.disclosure_suggestion ? "Required" : "Not indicated"}</strong></p>
          <p className="hint">{video.disclosure_suggestion_reason || "No suggestion reason available."}</p>
        </div>
        <div className="toggle" role="group" aria-label="Disclosure answer">
          <button type="button" className={disclosureAnswer === true ? "toggle-button selected" : "toggle-button"}
            onClick={() => { setDisclosureAnswer(true); setDisclosureTouched(true); }}>Yes</button>
          <button type="button" className={disclosureAnswer === false ? "toggle-button selected" : "toggle-button"}
            onClick={() => { setDisclosureAnswer(false); setDisclosureTouched(true); }}>No</button>
        </div>
        {!disclosureTouched && <p className="hint">System suggestion pre-selected hai. Final answer ke liye Yes/No ko khud confirm karein.</p>}
      </div>

      <label className="watch-confirm">
        <input type="checkbox" checked={watched} onChange={(event) => setWatched(event.target.checked)} />
        <span><strong>Maine poora video dekh liya hai</strong><br />aur ye script/brief se match karta hai.</span>
      </label>

      <p className="text-only-note">Automated checks sirf title, description, script/brief aur metadata dekhte hain. Actual video/audio match ka final confirmation aapko karna hai.</p>
      {error && <div className="error-box">{error}</div>}

      <div className="decision-actions">
        <button className="primary" disabled={!canDecide} onClick={() => submitDecision(true)}>✅ Approve</button>
        <button className="secondary" disabled={!canDecide} onClick={() => submitDecision(false)}>❌ Reject</button>
      </div>
      {!canDecide && <p className="gate-note">Decision ke liye video play hona, disclosure answer ko khud select karna, aur watch-confirmation checkbox tick karna zaroori hai.</p>}
    </section>
  );
}

function Login({ onLogin }) {
  const [key, setKey] = useState("");
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    if (!key.trim()) return setError("Founder API key enter karein.");
    setError("");
    try {
      const response = await fetch(API + "/api/dashboard", { headers: authHeaders(key.trim()) });
      if (response.status === 401) throw new Error("Founder API key galat hai.");
      if (!response.ok) throw new Error("Dashboard verify nahi ho paaya.");
      localStorage.setItem(KEY_STORAGE, key.trim());
      onLogin(key.trim());
    } catch (err) {
      setError(err.message || "Login verify nahi ho paaya.");
    }
  };

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="eyebrow">Founder access</div>
        <h1>YouTube Automation</h1>
        <p>Dashboard access ke liye apni founder API key enter karein.</p>
        <form onSubmit={submit}>
          <label>Founder API key<input type="password" value={key} onChange={(e) => setKey(e.target.value)} autoComplete="current-password" /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="primary" type="submit">Unlock dashboard</button>
        </form>
        <p className="hint">Key sirf is browser/device ke localStorage mein rakhi jaati hai.</p>
      </section>
    </main>
  );
}

export default function Home() {
  const [token, setToken] = useState(null);
  const [d, setD] = useState({ pending: [], recent: [] });
  const [loadError, setLoadError] = useState("");

  useEffect(() => setToken(localStorage.getItem(KEY_STORAGE)), []);

  const logout = () => {
    localStorage.removeItem(KEY_STORAGE);
    setToken(null);
  };

  const load = async () => {
    if (!token) return;
    try {
      const response = await apiFetch("/api/dashboard", token);
      if (!response.ok) throw new Error("Dashboard load nahi ho paaya.");
      setD(await response.json());
      setLoadError("");
    } catch (err) {
      if (err.message.includes("API key")) logout();
      setLoadError(err.message || "Dashboard abhi load nahi ho paaya.");
    }
  };

  useEffect(() => { load(); }, [token]);

  if (!token) return <Login onLogin={setToken} />;

  return (
    <main>
      <header className="page-header">
        <div><div className="eyebrow">Founder control center</div><h1>YouTube Automation</h1><p>Pending videos ko ek hi screen par dekhkar final human decision lein.</p></div>
        <div className="header-actions"><div className="pending-count">{d.pending.length} pending</div><button className="logout-button" onClick={logout}>Log out</button></div>
      </header>
      {loadError && <div className="error-box">{loadError}</div>}
      <h2>Needs your review</h2>
      {d.pending.length === 0 ? <div className="empty card">Abhi koi video review ke liye pending nahi hai.</div> :
        d.pending.map((video) => <ReviewCard key={video.id} video={video} token={token} onChanged={load} onLogout={logout} />)}
      <h2>Recent</h2>
      {d.recent.map((video) => <div className="row" key={video.id}><span>{video.title}</span><span>{video.state}</span></div>)}
    </main>
  );
}
