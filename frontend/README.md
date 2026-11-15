# ZYNTARA frontend

React, TypeScript, Vite and Tailwind workspace for the ZYNTARA microgravity combustion research project.

## Run locally

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI server origin (for example `http://127.0.0.1:8000`). Start the backend separately; the backend README has the Windows startup commands and lists implemented APIs.

The workspace charts and tables use the locally ingested dataset records. The assistant returns local evidence availability without a Gemini key; Gemini-generated answers are enabled by setting `GEMINI_API_KEY` in the backend `.env`. The flame view is a labeled, illustrative visualization—not NASA footage or a validated combustion simulation.

## Build

```powershell
npm run build
```
