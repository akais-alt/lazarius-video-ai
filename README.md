# Lazarius Video AI

Agent open source de génération vidéo IA conçu pour fonctionner même sur un PC peu puissant.

## Pipeline

```text
Prompt → scénario → scènes → prompts visuels → vidéo Cloud/Local
       → voix → musique → sous-titres → montage FFmpeg → MP4
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
                    └── génération vidéo
```

`RUNTIME_MODE=auto|local|cloud` contrôle le choix. En `auto`, un PC sans GPU CUDA suffisamment puissant est orienté vers le cloud.

## Technologies

- Frontend : Next.js + React + TypeScript
- Backend : Python + FastAPI
- Orchestration : agents spécialisés
- Vidéo : ComfyUI + workflows vidéo open source
- Modèle vidéo de référence : Wan 2.2
- Audio : Piper / adaptateur TTS
- Transcription : Whisper / adaptateur STT
- Montage : FFmpeg

Wan 2.2 est intégré nativement dans ComfyUI et dispose de workflows vidéo texte-vers-vidéo et image-vers-vidéo. Les workflows officiels peuvent servir de base à l'intégration du moteur.

## Fonctionnalités actuelles

- API FastAPI légère
- interface Next.js responsive
- détection CPU/RAM/GPU/FFmpeg
- sélection automatique Local/Cloud
- jobs asynchrones avec progression
- génération scénario + storyboard
- prompts visuels attachés directement aux scènes
- adaptateur cloud générique
- modes 480p, 720p et 1080p
- formats 9:16, 16:9 et 1:1
- aucun modèle vidéo lourd obligatoire sur le PC
- état `waiting_config` lorsque le moteur n'est pas configuré

## Important sur le « gratuit »

Le code et les modèles open source peuvent être utilisés sans licence logicielle payante, mais un GPU cloud reste une ressource informatique qui peut être facturée. Lazarius ne promet donc pas un quota cloud gratuit permanent.

Pour rester réellement gratuit, il faut utiliser un GPU local disponible ou une plateforme qui offre actuellement un quota gratuit. Les modèles vidéo Wan 2.2 restent gourmands en ressources pour un rendu confortable.

## Configuration cloud

Copier `.env.example` vers `.env` puis renseigner :

```env
RUNTIME_MODE=auto
CLOUD_VIDEO_PROVIDER=generic
CLOUD_VIDEO_API_URL=
CLOUD_VIDEO_API_KEY=
```

L'adaptateur cloud est volontairement neutre : il peut être relié à un serveur ComfyUI distant/serverless ou à un autre backend compatible.

## API

- `GET /api/generate/runtime` — capacités détectées
- `POST /api/generate/plan` — scénario/storyboard/prompts
- `POST /api/generate/video` — créer un job local ou cloud
- `GET /api/generate/jobs/{job_id}` — suivre le job

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

- `text_to_video.json`
- `image_to_video.json`
- `low_vram.json`

## Roadmap

1. Connecteur ComfyUI distant réel avec soumission et suivi de jobs
2. Génération vidéo multi-scènes réelle
3. TTS réel
4. Whisper réel + sous-titres `.srt`
5. Téléchargement des clips générés
6. Assemblage FFmpeg réel
7. Export MP4 final + URL de téléchargement
8. stockage objet et jobs persistants
9. mode Low-VRAM optimisé
10. connecteurs cloud interchangeables

## Licence

MIT
