# al-capilot.github.io

Root GitHub Pages site for Al-Capilot and Al-business.

## Deployment

- The static site is served by GitHub Pages from the `main` branch and repository root.
- `render.yaml` defines the separate FastAPI backend service named `al-business-backend`.
- Backend deployment instructions, environment variables, API paths, and safety notes are in [`backend/README.md`](backend/README.md).
- The website currently calls `https://al-business-backend.onrender.com/run`; the backend provides this compatibility route as well as `/api/chat`.

To deploy the backend, connect this repository to Render as a Blueprint and choose the `copilot/render-multi-agent-backend` branch. Add `GOOGLE_API_KEY` and `GROQ_API_KEY` when prompted or in the Render Environment page. Do not commit provider API keys.
