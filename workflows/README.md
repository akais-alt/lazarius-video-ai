# ComfyUI workflows

Workflows API-format utilisés par Lazarius Video AI.

## Disponibles

- `text_to_video.json` — Wan 2.2 14B T2V pour rendu Cloud.
- `image_to_video_5b.json` — Wan 2.2 TI2V-5B I2V Low-VRAM.

## Image → vidéo

`image_to_video_5b.json` utilise le modèle officiel `wan2.2_ti2v_5B_fp16.safetensors`, le VAE `wan2.2_vae.safetensors` et le nœud `Wan22ImageToVideoLatent`.

Lazarius remplace automatiquement :

- `__PROMPT__`
- `__IMAGE_URL__`
- `__WIDTH__`
- `__HEIGHT__`
- `__FRAMES__`
- `__RANDOM_INT__`

Pour un endpoint Vast.ai ComfyUI, `__IMAGE_URL__` peut être une URL accessible : le wrapper Vast peut télécharger automatiquement une image utilisée comme entrée du workflow avant l'exécution. Voir la documentation officielle Vast.ai.

## Modèles TI2V-5B

Le workflow officiel ComfyUI indique le modèle `wan2.2_ti2v_5B_fp16.safetensors` et le VAE `wan2.2_vae.safetensors`. Le modèle 5B est destiné à la fois au texte→vidéo et à l'image→vidéo.
