---
name: heygen_video
description: Genera video con avatar HeyGen (TTS + lip-sync). Usa quando l'utente vuole creare un video con avatar che parla.
---

# HeyGen Video

Genera video usando l'API HeyGen: un avatar (Zihan di default) legge lo script con sincronizzazione delle labbra.

## Workflow

1. Assicurati di avere uno script/testo pronto.
2. Esegui lo script Python dalla workspace:
   ```
   cd /Users/macminiai/.openclaw/workspace-avatar && python3 skills/heygen_video/scripts/gen_heygen_video.py --text "<TESTO>" --avatar "<AVATAR_ID>" --size "1280x720"
   ```
3. Leggi l'output finale.
4. Comunica solo risultato reale o errore reale.

## Parametri

- `--text`: Testo da pronunciare (obbligatorio)
- `--avatar`: ID avatar (default: `7f6390b2e98d45149dc5661ca3aa642d` = Zihan)
- `--voice`: Voice ID (default: 6924376faa724608a539daba27d691b6 = Savvy Stefano, Italiano)
- `--size`: Risoluzione - 1280x720 (default), 1920x1080, 640x360
- `--output-dir`: Cartella output (default: output/videos)

## Costi indicativi

- Video 1280x720: ~$0.10-0.30 per clip breve
- Piano free: ~3 minuti/mese

## Fallback

Se HeyGen non è raggiungibile, segnala l'errore. Non inventare video.
