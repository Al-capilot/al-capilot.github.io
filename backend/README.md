# Al-Capilot multi-agent backend

This FastAPI service provides a bounded three-stage project-assistant workflow:

1. Gemini creates an implementation plan.
2. Groq drafts an implementation proposal.
3. Gemini reviews the proposal.

The first release returns text to the website. It does **not** edit a GitHub repository, execute generated code, or deploy an application. Those powerful capabilities need a separate sandbox, explicit user approval, and a branch/PR-based GitHub integration; do not enable arbitrary command execution in the web request process.

## Deploy on Render

The repository-root `render.yaml` defines the `al-business-backend` web service. In Render, create a **Blueprint** from `Al-capilot/al-capilot.github.io`, select branch `copilot/render-multi-agent-backend` for this first deployment, and apply the blueprint. Alternatively create a Python web service with:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Add these environment variables in the Render dashboard (never commit real keys):

- `GOOGLE_API_KEY`: Google AI Studio API key
- `GROQ_API_KEY`: Groq API key
- `GOOGLE_MODEL`: a model ID currently enabled for your Google API project (default: `gemini-2.5-flash`)
- `GROQ_MODEL`: a model ID currently enabled in your Groq console (default: `llama-3.3-70b-versatile`)
- `ALLOWED_ORIGINS`: `https://al-capilot.github.io`

Model availability and free-tier eligibility can change. Confirm the exact model IDs in the provider consoles before deploying. The application reads model names from environment variables, so you can change them in Render without editing code. Provider free tiers have quotas and are not unlimited.

## API

- `GET /health`
- `POST /api/chat` (also supports the existing frontend's `/run` path)

Example body:

```json
{"prompt":"Plan a supplier management dashboard with FastAPI and PostgreSQL"}
```

The successful response contains a `response` string with the plan, implementation proposal, and review. Validation errors and provider quota/configuration errors use HTTP status codes and a `detail` field.

## Safety and operations

- API keys are read server-side from environment variables and are never sent to the browser. The Gemini key is sent to Google's API using an authentication header, not as a URL query parameter.
- Prompts are length-limited; requests are rate-limited per IP in process memory and concurrent model workflows are capped.
- The in-memory rate limit is a basic single-instance guard, not authentication or a durable abuse-prevention system. Before public launch, add real user authentication or an anti-abuse layer and provider budget alerts/quotas. Do not treat CORS as access control.
- No generated code is run. Do not expose a generated-code execution endpoint without an isolated disposable sandbox and strict resource limits.
