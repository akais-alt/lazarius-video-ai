# Lazarius Career Agent

Agent GitHub Actions pour automatiser la recherche de stages/emplois en Génie Civil – Travaux Publics en Côte d'Ivoire.

## Ce que fait le prototype

Chaque jour, le workflow peut :
1. rechercher des entreprises avec une API de recherche configurable ;
2. qualifier les entreprises selon le profil de Siaka Kamagate ;
3. éviter les doublons ;
4. préparer jusqu'à 20 candidatures ;
5. envoyer les candidatures via Microsoft Graph Outlook lorsque le mode d'envoi automatique est activé ;
6. analyser les nouveaux messages Outlook ;
7. produire un résumé quotidien ;
8. envoyer ce résumé sur WhatsApp Cloud API.

Le système fonctionne sans PC allumé grâce à GitHub Actions. Il dépend toutefois des API externes et de leurs identifiants.

## Important

Le dépôt principal est `akais-alt/lazarius-video-ai`. Le code Career Agent est isolé dans `career-agent/` sur la branche `career-agent`, car cette connexion GitHub ne permet pas de créer un nouveau dépôt directement.

## Secrets GitHub à configurer

- `OPENAI_API_KEY` : clé du fournisseur LLM choisi
- `SEARCH_API_KEY` : clé de recherche Web
- `SEARCH_ENGINE_ID` : identifiant du moteur de recherche
- `OUTLOOK_TENANT_ID`
- `OUTLOOK_CLIENT_ID`
- `OUTLOOK_CLIENT_SECRET`
- `OUTLOOK_REFRESH_TOKEN`
- `OUTLOOK_SENDER_EMAIL`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_RECIPIENT`

## Fonctionnement prudent

Par défaut, `AUTO_SEND=false`. L'agent collecte et prépare les candidatures sans les expédier. Passer à `AUTO_SEND=true` seulement après vérification des modèles et des secrets.

La limite quotidienne est `DAILY_LIMIT=20` et le code refuse les doublons récents.

## Lancer localement

```bash
cd career-agent
python -m pip install -r requirements.txt
python -m career_agent --dry-run
```

## GitHub Actions

Le workflow `.github/workflows/career-agent.yml` est planifié tous les jours. Pour changer l'heure, modifier la ligne cron. GitHub Actions utilise UTC.

## Prochaine configuration

1. Ajouter les secrets.
2. Mettre ton CV et ta lettre dans `career-agent/documents/` ou dans un stockage privé accessible par le job.
3. Vérifier la recherche et les emails générés avec `AUTO_SEND=false`.
4. Activer `AUTO_SEND=true` seulement lorsque tout est correct.
5. Le rapport WhatsApp quotidien reste le canal principal de notification.
