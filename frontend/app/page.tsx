export default function Home() {
  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 40, fontFamily: 'Arial, sans-serif' }}>
      <h1>Lazarius Video AI</h1>
      <p>Transforme une idée en vidéo avec des modèles IA open source.</p>
      <textarea
        placeholder="Décris la vidéo que tu veux créer..."
        style={{ width: '100%', minHeight: 180, padding: 16, marginTop: 20 }}
      />
      <button style={{ marginTop: 16, padding: '12px 20px' }}>Générer la vidéo</button>
    </main>
  );
}
