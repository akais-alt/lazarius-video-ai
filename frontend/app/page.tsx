"use client";

import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
type Job = { id?: string; job_id?: string; mode?: string; type?: string; status: string; progress?: number; message?: string; result?: any; error?: string };

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [characterDescription, setCharacterDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [motionVideoUrl, setMotionVideoUrl] = useState("");
  const [characterEngine, setCharacterEngine] = useState("auto");
  const [format, setFormat] = useState("9:16");
  const [duration, setDuration] = useState(30);
  const [quality, setQuality] = useState("720p");
  const [mode, setMode] = useState("auto");
  const [chainScenes, setChainScenes] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadingMotion, setUploadingMotion] = useState(false);
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [runtime, setRuntime] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => { fetch(`${API}/generate/runtime`).then(r => r.json()).then(setRuntime).catch(() => {}); }, []);
  const jobId = job?.id ?? job?.job_id;
  useEffect(() => {
    if (!jobId || ["completed", "failed", "waiting_config"].includes(job?.status ?? "")) return;
    const timer = setInterval(async () => { const res = await fetch(`${API}/generate/jobs/${jobId}`); if (res.ok) setJob(await res.json()); }, 1500);
    return () => clearInterval(timer);
  }, [jobId, job?.status]);

  async function upload(file: File, endpoint: string, setter: (url: string) => void, isMotion = false) {
    isMotion ? setUploadingMotion(true) : setUploading(true); setError("");
    try {
      const form = new FormData(); form.append("file", file);
      const res = await fetch(`${API}/generate/media/${endpoint}`, { method: "POST", body: form });
      const data = await res.json(); if (!res.ok) throw new Error(data.detail || `Upload impossible (${res.status})`);
      const absolute = data.url.startsWith("http") ? data.url : `${API.replace(/\/api$/, "")}${data.url}`;
      setter(absolute);
      if (!data.public) setError("Fichier importé. Configure PUBLIC_BASE_URL pour que le moteur Cloud puisse le récupérer.");
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur d'upload"); }
    finally { isMotion ? setUploadingMotion(false) : setUploading(false); }
  }

  async function generate() {
    if (!prompt.trim()) return;
    if (characterEngine === "wan_animate" && (!imageUrl.trim() || !motionVideoUrl.trim())) { setError("Wan2.2 Animate nécessite une image de référence et une vidéo de mouvement."); return; }
    setLoading(true); setError(""); setJob(null);
    try {
      const body = { prompt, duration, aspect_ratio: format, language: "fr", style: "cinematic", mode: (imageUrl.trim() || motionVideoUrl.trim()) ? "cloud" : mode, quality, character_engine: characterEngine, chain_scenes: chainScenes,
        ...(characterDescription.trim() ? { character_description: characterDescription.trim() } : {}),
        ...(imageUrl.trim() ? { image_url: imageUrl.trim() } : {}),
        ...(motionVideoUrl.trim() ? { motion_video_url: motionVideoUrl.trim() } : {}) };
      const res = await fetch(`${API}/generate/video`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json(); if (!res.ok) throw new Error(data.detail || `Erreur API (${res.status})`);
      setJob(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Erreur inconnue"); }
    finally { setLoading(false); }
  }

  const mediaPath = job?.result?.render?.media_url as string | undefined;
  const mediaUrl = mediaPath ? `${API.replace(/\/api$/, "")}${mediaPath}` : undefined;
  const stageLabels: Record<string, string> = { planning: "Scénario et scènes", video_cloud: "Génération vidéo Cloud", voice: "Voix IA", music: "Musique", subtitles: "Sous-titres", editing: "Montage", export: "Export MP4", done: "Terminé" };

  return <main className="page">
    <section className="hero"><div className="badge">● LOW-PC · CLOUD-FIRST · OPEN SOURCE</div><h1>Lazarius <span>Video AI</span></h1><p>Décris une idée, donne une image et, si besoin, une vidéo de mouvement. Lazarius peut utiliser Wan2.2 Animate pour transférer les mouvements vers ton personnage.</p></section>
    <section className="card">
      <label>Ton idée</label><textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ex. Un ouvrier ivoirien présente un chantier moderne à Yamoussoukro..." />
      <label>Personnage — optionnel</label><input value={characterDescription} onChange={e => setCharacterDescription(e.target.value)} maxLength={1000} placeholder="Ex. Homme ivoirien de 25 ans, casque jaune, gilet orange..." />
      <p className="runtime">Le verrou d’identité répète les caractéristiques du personnage dans les prompts.</p>
      <label>Image de référence</label>
      <div className="controls"><input value={imageUrl} onChange={e => setImageUrl(e.target.value)} placeholder="https://.../personnage.jpg" type="url" /><label className="upload-label"><input type="file" accept="image/jpeg,image/png,image/webp" disabled={uploading} onChange={e => e.target.files?.[0] && upload(e.target.files[0], "upload", setImageUrl)} />{uploading ? "Import..." : "Importer une image"}</label></div>
      <label>Moteur de cohérence du personnage</label>
      <select value={characterEngine} onChange={e => setCharacterEngine(e.target.value)}><option value="auto">Automatique</option><option value="i2v_5b">Wan2.2 TI2V-5B — léger</option><option value="wan_animate">Wan2.2 Animate 14B — mouvements avancés</option></select>
      {characterEngine === "wan_animate" && <>
        <p className="runtime">Wan2.2 Animate utilise une vidéo de mouvement pour reproduire poses, gestes et expressions sur l'image de référence.</p>
        <label>Vidéo de mouvement</label>
        <div className="controls"><input value={motionVideoUrl} onChange={e => setMotionVideoUrl(e.target.value)} placeholder="https://.../mouvement.mp4" type="url" /><label className="upload-label"><input type="file" accept="video/mp4,video/webm,video/quicktime" disabled={uploadingMotion} onChange={e => e.target.files?.[0] && upload(e.target.files[0], "upload-motion", setMotionVideoUrl, true)} />{uploadingMotion ? "Import..." : "Importer la vidéo"}</label></div>
      </>}
      {(imageUrl.trim() || motionVideoUrl.trim()) && <p className="runtime">Les médias de référence sont utilisés en mode Cloud. Le serveur doit être publiquement accessible via PUBLIC_BASE_URL.</p>}
      <label className="check"><input type="checkbox" checked={chainScenes} onChange={e => setChainScenes(e.target.checked)} disabled={!imageUrl.trim()} /> Chaîner les scènes</label>
      <div className="controls">
        <div><label>Format</label><select value={format} onChange={e => setFormat(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option></select></div>
        <div><label>Durée</label><select value={duration} onChange={e => setDuration(Number(e.target.value))}><option value={15}>15 s</option><option value={30}>30 s</option><option value={60}>60 s</option><option value={120}>2 min</option></select></div>
        <div><label>Qualité</label><select value={quality} onChange={e => setQuality(e.target.value)}><option>480p</option><option>720p</option><option>1080p</option></select></div>
        <div><label>Moteur</label><select value={mode} onChange={e => setMode(e.target.value)} disabled={Boolean(imageUrl.trim() || motionVideoUrl.trim())}><option value="auto">Automatique</option><option value="cloud">Cloud</option><option value="local">Local GPU</option></select></div>
        <button onClick={generate} disabled={loading || !prompt.trim() || uploading || uploadingMotion}>{loading ? "Lancement..." : characterEngine === "wan_animate" ? "Animer le personnage →" : "Créer la vidéo →"}</button>
      </div>
      {runtime && <div className="runtime">Recommandation : <b>{runtime.recommendation}</b> · GPU : {runtime.gpu} · RAM : {runtime.ram_gb || "?"} Go</div>}
      {error && <p className="error">{error}</p>}
    </section>
    {job && <section className="result"><h2>Production</h2><p><b>{stageLabels[job.message ?? ""] ?? job.status}</b> · {job.message}</p><div className="progress"><div style={{width: `${job.progress ?? 0}%`}} /></div><p>{job.progress ?? 0}%</p>{job.status === "completed" && mediaUrl && <div className="video-result"><video src={mediaUrl} controls playsInline /><a href={mediaUrl} target="_blank" rel="noreferrer">Ouvrir / récupérer le MP4</a></div>}<pre>{JSON.stringify(job.result ?? job, null, 2)}</pre></section>}
  </main>;
}
