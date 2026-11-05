# al-capilot.github.io

Root GitHub Pages site for Al-Capilot and Al-business.

## Deployment

- The static site is served by GitHub Pages from the `main` branch and repository root.
- `render.yaml` defines the separate FastAPI backend (`al-business-backend`) and the optional Render static-site service.
- The backend setup, environment variables, API paths, and safety notes are documented in [`backend/README.md`](backend/README.md).
- The website currently calls `https://al-business-backend.onrender.com/run`; the backend provides this compatibility route as well as `/api/chat`.

Do not commit provider API keys. Store them as secret environment variables in the Render dashboard.
