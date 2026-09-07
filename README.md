# Lazarius Video AI

Agent open source de génération vidéo IA conçu pour fonctionner même sur un PC peu puissant.

## Pipeline

```text
Prompt + personnage + image optionnelle → scénario → scènes → prompts visuels
→ verrou d'identité → Wan 2.2 T2V / TI2V-5B I2V → clips → voix Piper → Whisper
→ sous-titres SRT → montage FFmpeg → MP4
```

## Architecture Low-PC / Cloud-first

Le PC utilisateur prépare les tâches légères et choisit ensuite entre moteur local et rendu distant.

```text
PC utilisateur
  ├─ Next.js
  ├─ FastAPI
  ├─ scénario / storyboard / prompts
  ├─ identité du personnage
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

Wan 2.2 propose notamment des modèles pour texte→vidéo et image→vidéo. Le workflow actuel de Lazarius utilise le modèle TI2V-5B pour l'I2V. La branche Wan2.2 Animate ajoute une référence de personnage et peut transférer les expressions, gestes et mouvements depuis une vidéo de pose. citeturn0search0turn0search2

## Fonctionnalités actuelles

- API FastAPI légère
- interface Next.js responsive
- détection CPU/RAM/GPU/FFmpeg
- sélection automatique Local/Cloud
- jobs asynchrones avec progression
- génération scénario + storyboard
- prompts visuels attachés directement aux scènes
- description de personnage jusqu'à 1000 caractères
- verrou d'identité injecté dans les prompts de toutes les scènes
- image de référence pour renforcer l'identité visuelle
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

## Cohérence du personnage

L'utilisateur peut fournir une description comme :

```text
Homme ivoirien de 25 ans, cheveux courts noirs, visage ovale,
casque de chantier jaune, gilet orange réfléchissant,
pantalon bleu et chaussures de sécurité noires.
```

Lazarius transforme cette description en **CHARACTER IDENTITY LOCK** et l'ajoute à chaque prompt visuel. L'objectif est de réduire les changements de visage, de coiffure, d'âge, de proportions et de vêtements entre les scènes.

Une image de référence peut également être fournie. Elle est envoyée au workflow I2V et peut être réutilisée comme point de départ de chaque scène. Lorsque le chaînage est activé, la dernière image du clip précédent devient le point de départ du clip suivant.

Ce verrou par prompt améliore la cohérence mais ne constitue pas une garantie de copie faciale parfaite. Pour une fidélité supérieure, la prochaine étape est l'intégration du workflow **Wan2.2 Animate** avec référence personnage et vidéo de mouvement. Le nœud WanAnimateToVideo accepte notamment `reference_image`, `pose_video` et `continue_motion` pour maintenir la continuité temporelle. citeturn0search0turn0search5

## Image → vidéo et chaînage des scènes

L'interface accepte une URL d'image ou un fichier image. Lorsqu'une image est fournie, Lazarius force le rendu Cloud et sélectionne automatiquement `workflows/image_to_video_5b.json`.

Le mode « Chaîner les scènes » génère la première scène, extrait sa dernière image avec FFmpeg, puis utilise cette image comme image de départ de la scène suivante. Pour un moteur cloud, les images intermédiaires doivent être accessibles publiquement via `PUBLIC_BASE_URL`.

Pour Vast.ai Serverless, le wrapper ComfyUI peut détecter une URL utilisée comme image d'entrée dans le workflow, télécharger cette image sur le worker, puis exécuter le workflow.

Le workflow utilise le nœud natif `Wan22ImageToVideoLatent` et les paramètres largeur, hauteur et longueur de vidéo.

## Wan2.2 Animate — prochaine étape

Le workflow officiel ComfyUI Wan2.2 Animate utilise une image de référence et une vidéo de mouvement. Il propose notamment deux usages :

- **Move** : animer le personnage de référence avec le mouvement d'une vidéo pilote.
- **Mix/Replace** : remplacer le personnage d'une vidéo tout en conservant ses mouvements et expressions.

L'intégration dans Lazarius sera faite comme un moteur distinct afin de conserver le workflow TI2V-5B léger pour les machines/clouds disposant de moins de ressources. Le workflow officiel complet dépend de plusieurs nœuds et modèles supplémentaires, notamment pour le traitement du mouvement et de la référence. citeturn0search2turn0search6

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

`PUBLIC_BASE_URL` est nécessaire pour que le moteur cloud puisse récupérer les images importées par le navigateur et les dernières images produites pendant le chaînage. Pour une image déjà hébergée publiquement, `image_url` peut continuer à être utilisé directement.

Pour un serveur ComfyUI/Vast compatible, l'adaptateur utilise `/generate/sync`.

## API

- `GET /api/generate/runtime` — capacités détectées
- `POST /api/generate/plan` — scénario/storyboard/prompts + verrou d'identité
- `POST /api/generate/media/upload` — importer une image JPG/PNG/WebP
- `POST /api/generate/video` — créer un job T2V ou I2V, avec personnage et option `chain_scenes`
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
16. ~~verrou d'identité du personnage~~
17. workflow Wan2.2 Animate avec image de référence + vidéo de mouvement
18. continuité avancée avec `continue_motion`
19. sélection automatique du meilleur moteur selon VRAM/coût
20. historique des projets + stockage persistant

## Licence

MIT
