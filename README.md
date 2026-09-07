# Lazarius Video AI

Agent open source de génération vidéo IA conçu pour fonctionner même sur un PC peu puissant.

## Architecture Low-PC / Cloud-first

Le PC de l'utilisateur ne doit pas obligatoirement posséder une grosse carte graphique. L'application sépare la préparation légère du rendu vidéo lourd :

```text
PC utilisateur
  ├─ interface Next.js
  ├─ FastAPI
  ├─ scénario / storyboard / prompts
  └─ détection des capacités
          │
          ├── Local GPU (si disponible)
          │
          └── Cloud GPU (si PC faible)
                    │
                    └── génération vidéo
```

Le moteur est sélectionné avec `RUNTIME_MODE=auto|local|cloud`. En `auto`, Lazarius privilégie le cloud lorsqu'aucun GPU CUDA n'est détecté.

## Fonctionnalités actuelles

- API FastAPI légère
- interface Next.js responsive
- détection CPU/RAM/GPU/FFmpeg
- mode automatique Local/Cloud
- jobs asynchrones avec progression
- adaptateur cloud vidéo générique
- aucun modèle vidéo lourd obligatoire sur le PC
- mode planning/demo si aucun fournisseur cloud n'est configuré

## Configuration cloud

Copier `.env.example` vers `.env` puis renseigner, si nécessaire :

```env
RUNTIME_MODE=auto
CLOUD_VIDEO_PROVIDER=generic
CLOUD_VIDEO_API_URL=
CLOUD_VIDEO_API_KEY=
```

L'adaptateur cloud est volontairement neutre : il n'impose pas un fournisseur précis. Il pourra être relié à un serveur ComfyUI cloud/serverless ou à un autre backend compatible.

## API

- `GET /api/generate/runtime` — capacités détectées
- `POST /api/generate/plan` — préparer scénario/storyboard
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

## Important

Le mode cloud déporte le calcul, mais un fournisseur cloud peut être payant selon son offre. Le dépôt ne promet pas une génération cloud gratuite. Pour un fonctionnement réellement gratuit, il faudra soit utiliser un service disposant d'un quota gratuit, soit exécuter un moteur open source sur une machine GPU disponible.

## Roadmap

1. Adapter cloud ComfyUI/serverless avec suivi réel des jobs
2. Génération vidéo multi-scènes
3. TTS + Whisper + sous-titres
4. Montage FFmpeg distant
5. stockage objet et téléchargement MP4
6. mode Low-VRAM local pour les PC équipés d'un petit GPU

## Licence

MIT
