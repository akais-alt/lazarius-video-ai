"use client";

import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type Job = { job_id: string; mode: string; status: string; progress?: number; message?: string; result?: any; error?: string };

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [format, setFormat] = useState("9:16");
  const [duration, setDuration] = useState(30);
  const [mode, setMode] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [runtime, setRuntime] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/generate/runtime`).then(r => r.json()).then(setRuntime).catch(() => {});
  }, []);

  useEffect(() => {
    if (!job?.job_id || ["completed", "failed", "waiting_config"].includes(job.status)) return;
    const timer = setInterval(async () => {
      const res = await fetch(`${API}/generate/jobs/${job.job_id}`);
      if (res.ok) setJob(await res.json());
    }, 1500);
    return () => clearInterval(timer);
  }, [job?.job_id, job?.status]);

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true); setError(""); setJob(null);
    try {
      const res = await fetch(`${API}/generate/video`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, duration, aspect_ratio: format, language: "fr", style: "cinematic", mode }) });
      if (!res.ok) throw new Error(`Erreur API (${res.status})`);
      setJob(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur inconnue"); }
    finally { setLoading(false); }
  }

  return <main className="page">
    <section className="hero"><div className="badge">● LOW-PC · CLOUD-FIRST · OPEN SOURCE</div><h1>Lazarius <span>Video AI</span></h1><p>Ton PC prépare le projet. Le rendu vidéo lourd peut être déporté vers un moteur cloud.</p></section>
    <section className="card">
      <label>Ton idée</label><textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ex. Une publicité cinématique pour une entreprise de construction en Côte d’Ivoire..." />
      <div className="controls">
        <div><label>Format</label><select value={format} onChange={e => setFormat(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option></select></div>
        <div><label>Durée</label><select value={duration} onChange={e => setDuration(Number(e.target.value))}><option value={15}>15 s</option><option value={30}>30 s</option><option value={60}>60 s</option><option value={120}>2 min</option></select></div>
        <div><label>Moteur</label><select value={mode} onChange={e => setMode(e.target.value)}><option value="auto">Automatique</option><option value="cloud">Cloud</option><option value="local">Local GPU</option></select></div>
        <button onClick={generate} disabled={loading || !prompt.trim()}>{loading ? "Lancement..." : "Créer la vidéo →"}</button>
      </div>
      {runtime && <div className="runtime">Mode détecté : <b>{runtime.mode}</b> · GPU : {runtime.gpu} · FFmpeg : {runtime.ffmpeg ? "OK" : "absent"}</div>}
      {error && <p className="error">{error}</p>}
    </section>
    {job && <section className="result"><h2>Production</h2><p><b>{job.status}</b> · {job.message}</p><div className="progress"><div style={{width: `${job.progress ?? 0}%`}} /></div><pre>{JSON.stringify(job.result ?? job, null, 2)}</pre></section>}
  </main>;
}
