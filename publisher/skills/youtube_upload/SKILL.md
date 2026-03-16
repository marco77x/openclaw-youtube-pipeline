---
name: youtube_upload
description: Carica video su YouTube con thumbnail. Usa questa skill per pubblicare video.
---

# YouTube Upload

Carica video su YouTube tramite API v3 con upload resumable via curl.

## Workflow

1. Assicurati di avere: video (.mp4), thumbnail (.png), metadata (.json)
2. Esegui lo script Python:
   python3 skills/youtube_upload/scripts/upload_video.py --video <VIDEO> --title "<TITOLO>" --description "<DESCRIZIONE>" --tags "<TAG1,TAG2>" --privacy <private|unlisted|public> --thumbnail <THUMBNAIL>
3. Leggi il video_id restituito
4. Comunica l'URL del video

## Argomenti
- --video: percorso al file video mp4 (obbligatorio)
- --title: titolo del video (obbligatorio)
- --description: descrizione
- --tags: tag separati da virgola
- --privacy: public, private, unlisted (default: private)
- --thumbnail: percorso all'immagine thumbnail

## Note
- La prima autenticazione richiede approvazione OAuth nel browser
- I token vengono salvati in config/token.pickle
- Il video deve essere formato MP4
- La thumbnail deve essere PNG
