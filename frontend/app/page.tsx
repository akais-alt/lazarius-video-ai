"use client";

import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type Job = { id?: string; job_id?: string; mode?: string; status: string; progress?: number; message?: string; result?: any; error?: string };

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [format, setFormat] = useState("9:16");
  const [duration, setDuration] = useState(30);
  const [quality, setQuality] = useState("720p");
  const [mode, setMode] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [runtime, setRuntime] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/generate/runtime`).then(r => r.json()).then(setRuntime).catch(() => {});
  }, []);

  const jobId = job?.id ?? job?.job_id;
  useEffect(() => {
    if (!jobId || ["completed", "failed", "waiting_config"].includes(job?.status ?? "")) return;
    const timer = setInterval(async () => {
      const res = await fetch(`${API}/generate/jobs/${jobId}`);
      if (res.ok) setJob(await res.json());
    }, 1500);
    return () => clearInterval(timer);
  }, [jobId, job?.status]);

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true); setError(""); setJob(null);
    try {
      const res = await fetch(`${API}/generate/video`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, duration, aspect_ratio: format, language: "fr", style: "cinematic", mode, quality }) });
      if (!res.ok) throw new Error(`Erreur API (${res.status})`);
      setJob(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur inconnue"); }
    finally { setLoading(false); }
  }

  const stageLabels: Record<string, string> = { planning: "Scénario et scènes", video_cloud: "Génération vidéo Cloud", voice: "Voix IA", music: "Musique", subtitles: "Sous-titres", editing: "Montage", export: "Export MP4", done: "Terminé" };

  return <main className="page">
    <section className="hero"><div className="badge">● LOW-PC · CLOUD-FIRST · OPEN SOURCE</div><h1>Lazarius <span>Video AI</span></h1><p>Décris une idée. Lazarius orchestre scénario → scènes → vidéo → voix → musique → sous-titres → montage → MP4.</p></section>
    <section className="card">
      <label>Ton idée</label><textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ex. Une publicité cinématique pour une entreprise de construction en Côte d’Ivoire..." />
      <div className="controls">
        <div><label>Format</label><select value={format} onChange={e => setFormat(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option></select></div>
        <div><label>Durée</label><select value={duration} onChange={e => setDuration(Number(e.target.value))}><option value={15}>15 s</option><option value={30}>30 s</option><option value={60}>60 s</option><option value={120}>2 min</option></select></div>
        <div><label>Qualité</label><select value={quality} onChange={e => setQuality(e.target.value)}><option>480p</option><option>720p</option><option>1080p</option></select></div>
        <div><label>Moteur</label><select value={mode} onChange={e => setMode(e.target.value)}><option value="auto">Automatique</option><option value="cloud">Cloud</option><option value="local">Local GPU</option></select></div>
        <button onClick={generate} disabled={loading || !prompt.trim()}>{loading ? "Lancement..." : "Créer la vidéo →"}</button>
      </div>
      {runtime && <div className="runtime">Recommandation : <b>{runtime.recommendation}</b> · GPU : {runtime.gpu} · RAM : {runtime.ram_gb || "?"} Go</div>}
      {error && <p className="error">{error}</p>}
    </section>
    {job && <section className="result"><h2>Production</h2><p><b>{stageLabels[job.message ?? ""] ?? job.status}</b> · {job.message}</p><div className="progress"><div style={{width: `${job.progress ?? 0}%`}} /></div><p>{job.progress ?? 0}%</p>{job.status === "completed" && <div className="success">Pipeline terminée. Le moteur cloud peut maintenant fournir les médias et le rendu MP4 via son adaptateur configuré.</div>}<pre>{JSON.stringify(job.result ?? job, null, 2)}</pre></section>}
  </main>;
}
