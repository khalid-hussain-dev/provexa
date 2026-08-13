# PROVEXA Experience Builder

Standalone Vite + React user experience for PROVEXA.

## Run locally

```powershell
npm install
$env:VITE_API_MODE="demo"
npm run dev
```

Demo mode uses deterministic local responses and does not require the API host.

For the integrated API host:

```powershell
$env:VITE_API_MODE="live"
npm run dev
```

The Vite proxy forwards `/api` requests to `http://localhost:8000`.

## Checks

```powershell
npm run lint
npm test
npm run build
```

## Scope

The UI covers authentication, candidate evidence, profile analysis, job matching, persisted interviews, readiness results, course progress, and evidence-backed resume optimization. Resume text export and subscription behavior are frontend demonstrations. No backend workflow logic is implemented here.
