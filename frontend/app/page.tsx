"use client";

import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [format, setFormat] = useState("9:16");
  const [duration, setDuration] = useState(30);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/generate/plan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, duration, aspect_ratio: format, language: "fr", style: "cinematic" }) });
      if (!res.ok) throw new Error(`Erreur API (${res.status})`);
      setResult(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur inconnue"); }
    finally { setLoading(false); }
  }

  return <main className="page">
    <section className="hero"><div className="badge">● OPEN SOURCE · LOCAL AI</div><h1>Lazarius <span>Video AI</span></h1><p>Décris ta vidéo. Lazarius prépare automatiquement le scénario, le storyboard et les prompts de production.</p></section>
    <section className="card"><label>Ton idée</label><textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ex. Une publicité cinématique pour une entreprise de construction en Côte d’Ivoire..." />
      <div className="controls"><div><label>Format</label><select value={format} onChange={e => setFormat(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option></select></div><div><label>Durée</label><select value={duration} onChange={e => setDuration(Number(e.target.value))}><option value={15}>15 s</option><option value={30}>30 s</option><option value={60}>60 s</option><option value={120}>2 min</option></select></div><button onClick={generate} disabled={loading || !prompt.trim()}>{loading ? "Préparation..." : "Créer le plan vidéo →"}</button></div>
      {error && <p className="error">{error}</p>}</section>
    {result && <section className="result"><h2>Plan généré</h2><pre>{JSON.stringify(result, null, 2)}</pre></section>}
  </main>;
}
