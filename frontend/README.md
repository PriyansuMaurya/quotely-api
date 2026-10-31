# Quotely frontend

A single-page SvelteKit client for the [Quotely API](../README.md). Shows one
random quote with its author, and fetches a new one on demand.

## Quick start

```bash
npm install
npm run dev          # http://localhost:5173
```

The app calls the deployed API by default. To point it somewhere else, copy
`.env.example` to `.env` and set `PUBLIC_API_BASE_URL` (no trailing slash).

## Scripts

| Script | Purpose |
| ------ | ------- |
| `npm run dev` | Dev server with HMR on port 5173 |
| `npm run build` | Production build into `build/` |
| `npm run preview` | Serve the production build locally |
| `npm run check` | `svelte-check` type and accessibility diagnostics |
| `npm test` | Vitest unit and component tests (18) |
| `npm run test:e2e` | Playwright smoke tests against the production build |

Playwright needs its browser once: `npx playwright install chromium`.

## Behaviour

The page tracks four states — `idle`, `loading`, `success`, `error`:

- **Loading** shows a skeleton and disables the refresh button (`aria-busy`).
- **Success** renders the quote and author inside a keyed block so each new quote
  animates in.
- **Error** distinguishes a dropped connection, a slow request, an HTTP error and
  an unreadable payload, each with its own message, and offers a retry.
- Refreshing aborts any in-flight request, so a fast double-click cannot let an
  older response overwrite a newer one.

## Accessibility

- The quote sits in an `aria-live="polite"` region with `aria-atomic="true"`, so a
  new quote is announced without interrupting the reader.
- Errors use `role="alert"`.
- The refresh button is a real `<button>` with `aria-busy` while loading, a
  visible `focus-visible` ring, and a disabled state that is announced.
- Decorative background and quote glyphs are `aria-hidden`.
- `prefers-reduced-motion` disables the entrance animation and the button spin.
- Layout is mobile-first and verified for horizontal overflow at 375px.

## Deployment (Vercel)

1. Import `PriyansuMaurya/quotely-api` in Vercel.
2. Set **Root Directory** to `frontend`.
3. Vercel reads `vercel.json` (build `npm run build`, output `build`). Optionally
   set `PUBLIC_API_BASE_URL` in the project's environment variables.
4. After the first deploy, **add your Vercel origin to the API's CORS allowlist**,
   or the browser will block the request:

   ```
   Render → quotely-api → Environment → CORS_ALLOWED_ORIGINS
   = https://your-app.vercel.app
   ```

   Comma-separate multiple origins. Preview URLs are not covered by an exact-origin
   allowlist; add each one, or allow a wildcard if you trust every `*.vercel.app`.
