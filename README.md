# Lazarius Video AI

Agent open source de génération vidéo IA conçu pour fonctionner même sur un PC peu puissant.

## Pipeline

```text
Prompt → scénario → scènes → prompts visuels → vidéo Cloud/Local
       → voix Piper → Whisper → sous-titres SRT → montage FFmpeg → MP4
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
- Modèle vidéo de référence : Wan 2.2
- Audio : Piper
- Transcription : faster-whisper
- Montage : FFmpeg

Wan 2.2 est intégré nativement dans ComfyUI et propose des workflows officiels texte-vers-vidéo et image-vers-vidéo. La version TI2V-5B est annoncée comme adaptée à environ 8 Go de VRAM avec l'offloading natif ComfyUI ; la version 14B T2V est également disponible pour les rendus cloud plus lourds. citeturn0search0

## Fonctionnalités actuelles

- API FastAPI légère
- interface Next.js responsive
- détection CPU/RAM/GPU/FFmpeg
- sélection automatique Local/Cloud
- jobs asynchrones avec progression
- génération scénario + storyboard
- prompts visuels attachés directement aux scènes
- workflow ComfyUI/Wan 2.2 paramétrable
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

## Important sur le « gratuit »

Le code et les modèles open source peuvent être utilisés sans licence logicielle payante, mais un GPU cloud reste une ressource informatique qui peut être facturée. Lazarius ne promet donc pas un quota cloud gratuit permanent.

Pour rester réellement gratuit, il faut utiliser un GPU local disponible ou une plateforme qui offre actuellement un quota gratuit. Wan 2.2 est open source sous Apache 2.0, mais les besoins matériels restent importants pour un rendu confortable. citeturn0search0

## Configuration cloud

Copier `.env.example` vers `.env` puis renseigner :

```env
RUNTIME_MODE=auto
CLOUD_VIDEO_PROVIDER=vast
CLOUD_VIDEO_API_URL=https://TON_ENDPOINT/generate
CLOUD_VIDEO_API_KEY=
CLOUD_VIDEO_WORKFLOW=workflows/text_to_video.json
```

Pour un serveur ComfyUI/Vast compatible, l'adaptateur utilise `/generate/sync`. Si aucun endpoint cloud n'est configuré, Lazarius ne simule pas de vidéo et retourne `waiting_config`.

## API

- `GET /api/generate/runtime` — capacités détectées
- `POST /api/generate/plan` — scénario/storyboard/prompts
- `POST /api/generate/video` — créer un job local ou cloud
- `GET /api/generate/jobs/{job_id}` — suivre le job
- `GET /api/media/{filename}` — lire un MP4 généré

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

Les workflows exportés peuvent être placés dans `workflows/` :

- `text_to_video.json` — Wan 2.2 T2V API workflow
- `image_to_video.json` — à ajouter
- `low_vram.json` — à ajouter

Le workflow T2V actuel utilise les placeholders `__PROMPT__`, `__WIDTH__`, `__HEIGHT__`, `__FRAMES__` et `__RANDOM_INT__`, remplacés automatiquement par le backend.

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
11. image-to-video et first/last-frame
12. workflow Wan2.2 TI2V-5B Low-VRAM
13. connecteurs cloud interchangeables

## Licence

MIT
