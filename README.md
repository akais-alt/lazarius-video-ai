# Lazarius Video AI

Agent open source de génération vidéo IA conçu pour fonctionner même sur un PC peu puissant.

## Pipeline

```text
Prompt + image optionnelle → scénario → scènes → prompts visuels
→ Wan 2.2 T2V / TI2V-5B I2V → clips → voix Piper → Whisper
→ sous-titres SRT → montage FFmpeg → MP4
```

## Architecture Low-PC / Cloud-first

Le PC utilisateur prépare les tâches légères et choisit ensuite entre moteur local et rendu distant.

```text
PC utilisateur
  ├─ Next.js
  ├─ FastAPI
  ├─ scénario / storyboard / prompts
  └─ détection CPU/RAM/GPU
          │
          ├── GPU local disponible
          │
          └── Cloud GPU / serveur distant
                    │
                    └── ComfyUI / Wan 2.2
```

`RUNTIME_MODE=auto|local|cloud` contrôle le choix. En `auto`, un PC sans GPU CUDA suffisamment puissant est orienté vers le cloud.

## Technologies

- Frontend : Next.js + React + TypeScript
- Backend : Python + FastAPI
- Orchestration : agents spécialisés
- Vidéo : ComfyUI + workflows vidéo open source
- Modèle vidéo : Wan 2.2
- Audio : Piper
- Transcription : faster-whisper
- Montage : FFmpeg

Wan 2.2 propose un modèle 5B capable de texte→vidéo et image→vidéo. Le workflow TI2V-5B officiel utilise `wan2.2_ti2v_5B_fp16.safetensors` et `wan2.2_vae.safetensors`. citeturn0search1turn0search2

## Fonctionnalités actuelles

- API FastAPI légère
- interface Next.js responsive
- détection CPU/RAM/GPU/FFmpeg
- sélection automatique Local/Cloud
- jobs asynchrones avec progression
- génération scénario + storyboard
- prompts visuels attachés directement aux scènes
- Wan 2.2 T2V cloud
- Wan 2.2 TI2V-5B image→vidéo
- image de départ via URL publique
- import d'image depuis le navigateur (JPG/PNG/WebP, limite configurable)
- option first-image → last-frame → scène suivante
- workflow ComfyUI paramétrable
- seed aléatoire par génération
- adaptateur cloud `/generate/sync`
- téléchargement automatique des clips retournés
- assemblage vidéo multi-scènes avec FFmpeg
- TTS Piper optionnel
- transcription faster-whisper optionnelle
- génération de sous-titres SRT
- intégration des sous-titres dans le MP4
- formats 9:16, 16:9 et 1:1
- qualités 480p, 720p et 1080p
- aucun modèle vidéo lourd obligatoire sur le PC
- état `waiting_config` lorsque le moteur n'est pas configuré

## Image → vidéo et chaînage des scènes

L'interface accepte une URL d'image ou un fichier image. Lorsqu'une image est fournie, Lazarius force le rendu Cloud et sélectionne automatiquement `workflows/image_to_video_5b.json`.

Le mode « Chaîner les scènes » génère la première scène, extrait sa dernière image avec FFmpeg, puis utilise cette image comme image de départ de la scène suivante. Pour un moteur cloud, les images intermédiaires doivent être accessibles publiquement via `PUBLIC_BASE_URL`.

Pour Vast.ai Serverless, le wrapper ComfyUI peut détecter une URL utilisée comme image d'entrée dans le workflow, télécharger cette image sur le worker, puis exécuter le workflow. citeturn2search0

Le workflow utilise le nœud natif `Wan22ImageToVideoLatent` et les paramètres largeur, hauteur et longueur de vidéo. citeturn0search2turn1search2

## Important sur le « gratuit »

Le code et les modèles open source peuvent être utilisés sans licence logicielle payante, mais un GPU cloud reste une ressource informatique qui peut être facturée. Lazarius ne promet donc pas un quota cloud gratuit permanent.

Pour rester réellement gratuit, il faut utiliser un GPU local disponible ou une plateforme qui offre actuellement un quota gratuit.

## Configuration cloud

Copier `.env.example` vers `.env` puis renseigner :

```env
RUNTIME_MODE=auto
CLOUD_VIDEO_PROVIDER=vast
CLOUD_VIDEO_API_URL=https://TON_ENDPOINT
CLOUD_VIDEO_API_KEY=
CLOUD_VIDEO_WORKFLOW=workflows/text_to_video.json
CLOUD_VIDEO_I2V_WORKFLOW=workflows/image_to_video_5b.json
PUBLIC_BASE_URL=https://ton-backend-public.example.com
MAX_IMAGE_UPLOAD_MB=10
```

`PUBLIC_BASE_URL` est nécessaire pour que Vast/ComfyUI puisse récupérer les images importées par le navigateur et les dernières images produites pendant le chaînage. Pour une image déjà hébergée publiquement, `image_url` peut continuer à être utilisé directement.

Pour un serveur ComfyUI/Vast compatible, l'adaptateur utilise `/generate/sync`. Le serveur accepte un workflow ComfyUI complet et retourne notamment des URL présignées lorsque le stockage S3 est configuré. citeturn2search0

## API

- `GET /api/generate/runtime` — capacités détectées
- `POST /api/generate/plan` — scénario/storyboard/prompts
- `POST /api/generate/media/upload` — importer une image JPG/PNG/WebP
- `POST /api/generate/video` — créer un job T2V ou I2V, avec option `chain_scenes`
- `GET /api/generate/jobs/{job_id}` — suivre le job
- `GET /api/media/{filename}` — lire un média généré ou une image importée

## Installation

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Puis ouvrir `http://localhost:3000`.

## Workflows ComfyUI

- `text_to_video.json` — Wan 2.2 T2V API workflow
- `image_to_video_5b.json` — Wan 2.2 TI2V-5B I2V Low-VRAM

Les workflows utilisent notamment les placeholders `__PROMPT__`, `__IMAGE_URL__`, `__WIDTH__`, `__HEIGHT__`, `__FRAMES__` et `__RANDOM_INT__`.

## Roadmap

1. ~~Connecteur ComfyUI distant réel~~
2. ~~Génération vidéo multi-scènes~~
3. ~~TTS réel avec Piper~~
4. ~~Whisper réel + sous-titres `.srt`~~
5. ~~Téléchargement des clips générés~~
6. ~~Assemblage FFmpeg réel~~
7. ~~Export MP4 final + URL de lecture~~
8. stockage objet et jobs persistants
9. sous-titres brûlés/animés façon TikTok
10. musique de fond et ducking automatique
11. ~~image-to-video~~
12. ~~workflow Wan2.2 TI2V-5B Low-VRAM~~
13. ~~connecteurs cloud interchangeables~~
14. ~~first-frame / last-frame chaining~~
15. ~~import d'images depuis le navigateur~~

## Licence

MIT
