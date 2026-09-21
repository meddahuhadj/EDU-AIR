# EDU-AIR SMART SURFACE — PWA

Contactless AI-powered interactive whiteboard. This folder is the **installable
web app** (PWA): smart surface, air pointer, air draw, air 3D, air vision, air
lab, air quiz, air presentation, AI teacher, calibration, history, settings,
privacy and security — in **English, French, Dutch and Arabic**.

The camera/hand-tracking AI is a **local desktop application**. It runs on the
teacher's own machine and never leaves it; no deployment file in this repo ships
or uploads the AI.

## What makes it a PWA

| Piece | File | Notes |
| --- | --- | --- |
| Web app manifest | `manifest.webmanifest` | standalone display, maskable icons, shortcuts, 4 locales |
| Service worker | `sw.js` | precached app shell; network-first HTML, cache-first assets, offline fallback |
| SW registration | `app.js` (`registerServiceWorker`, `wirePwa`) | registered from `./sw.js` with scope `./` |
| Install UI | `index.html` (`#btnInstall`) + Settings → "Install app" | uses `beforeinstallprompt`; falls back to a toast |
| Offline / online | `app.js` | toasts `offline.on` / `offline.off` |
| Theme + iOS meta | `index.html` | `theme-color`, `apple-mobile-web-app-*`, `apple-touch-icon` |

After the first visit the app launches and works with no connection.

## Run locally

Any static server works (the service worker needs `http://localhost` or HTTPS):

```powershell
# from this folder
python -m http.server 8080
# then open http://localhost:8080
```

`file://` will load the UI but the service worker stays disabled (browsers
require a secure origin).

## Deploy

All three targets publish **this repo root** and are pre-configured:

- **Vercel** — `vercel.json` (`cleanUrls`, `sw.js` never cached). `vercel` or import the repo.
- **Netlify** — `netlify.toml` + `_headers` (no build command, `publish = "."`).
- **Render** — `render.yaml` Blueprint (static site, `sw.js` never cached).

All configs agree on the same rules: no build step, app shell served fresh, and
`sw.js` marked `no-cache, no-store, must-revalidate`.

> The 300+ MB desktop ZIP is git-ignored, so it is never uploaded to a static
> host. Link to the GitHub release instead (below).

## Get the desktop app

- Download (release `v1.0-beta`):
  `https://github.com/meddahuhadj/EDU-AIR/releases/download/v1.0-beta/EDU-AIR-Windows.zip`
- Checksum: `EDU-AIR-Windows.zip.sha256` on the same release.
- Windows 10 / 11 (x64). Unzip and run — no installer, no admin rights.

## Privacy

The web app never requests the camera or microphone. Camera/mic processing
happens only in the local desktop app, on-device. Local demo data lives in
`localStorage` and can be cleared from **Settings → Reset all local data**.
