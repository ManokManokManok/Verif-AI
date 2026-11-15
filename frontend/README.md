# Verif-AI Frontend

The React frontend provides scam detection, image analysis, guidance, account
management, personal analytics, and an admin dashboard.

## Technology

- React 18 and Vite
- React Router
- CSS and React context/hooks
- Fetch-based API clients
- Vitest and React Testing Library

## Project structure

```text
frontend/
├── src/
│   ├── api/             # Backend API clients
│   ├── components/      # Shared, authentication, report, and admin components
│   ├── context/         # Authentication and theme state
│   ├── hooks/           # Admin data hooks
│   ├── pages/           # Application pages and admin dashboard
│   ├── utils/           # Validation, formatting, and other helpers
│   ├── App.jsx          # Routes
│   └── index.css        # Global styles
├── tests/
├── package.json
└── vite.config.js
```

The shared API client in `src/api/client.js` handles authentication, detection,
and analysis history requests. `analysis.js`, `admin.js`, `analytics.js`,
`chatbot.js`, and `reports.js` provide additional feature-specific requests.

## Local development

From the `frontend` folder:

```powershell
npm install
npm run dev
```

Open the address printed by Vite, normally `http://localhost:5173`. Start the
backend separately; see the [backend setup guide](../backend/SETUP_TEAM.md).

The frontend defaults to the local backend. To configure another backend,
create a local `frontend/.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000/api
```

`VITE_API_URL` is the backend origin used by the chatbot API.
`VITE_API_BASE_URL` is the API base used by the shared, admin, and reports
clients. Point both at the same backend and include `/api` only in
`VITE_API_BASE_URL`. Ensure the backend CORS settings and the frontend content
security policy allow the configured origin.

The `VITE_` variables are included in browser code. Do not put credentials or
API keys in them.

## Pages and authentication

- Public routes include the landing page, detection, guidance chatbot, login,
  registration, and password recovery.
- Settings and personal analytics require authentication. The admin dashboard
  also requires an admin role.
- `AuthContext` manages login state and session expiration. The API client
  stores access and refresh tokens in browser localStorage and handles token
  refresh. These tokens are not HTTP-only cookies.

Text detection uses the backend gatekeeper and BERT pipeline; image analysis
uses the separate Gemini image endpoint. See the
[API reference](../backend/docs/API_REFERENCE.md).

## Tests and build

From the `frontend` folder:

```powershell
npm run test:run          # Run tests once
npm test -- --watch       # Run tests in watch mode
npm run build             # Build into dist/
npm run preview           # Preview a production build
```

Watch mode is disabled by default in the Vitest configuration. Coverage
reporting requires a compatible Vitest coverage provider, which is not listed
in the current frontend dependencies.

## Deploying the frontend to Vercel

The frontend is a static Vite single-page application. Import the repository
into Vercel and set the project root to `frontend`. If prompted, use:

- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Install command: `npm install`

The [Vercel configuration](vercel.json) rewrites application routes to
`index.html` so direct visits and refreshes work.

Set these Vercel environment variables for Production and, if appropriate,
Preview:

```env
VITE_API_URL=https://<your-backend-host>
VITE_API_BASE_URL=https://<your-backend-host>/api
```

Use the public HTTPS origin of the backend, not `localhost`. The Django backend
must separately allow the frontend origin in its CORS configuration. Rebuild
the frontend after changing these variables. Deploying the frontend does not
deploy the backend.

For a temporary laptop-hosted demo, see the
[backend README](../backend/README.md). Guest text-chat and image-analysis
allowances are best-effort session controls, not security-grade quotas.

## Further documentation

- [Backend API reference](../backend/docs/API_REFERENCE.md)
- [Backend security overview](../backend/docs/SECURITY.md)
- [Admin components](src/components/admin/README.md)
- [Admin modularization notes](src/pages/admin/MODULARIZATION_SUMMARY.md)
