# Phase 4: Frontend — Complete

## Design decisions (see the design-token rationale in `app/globals.css` and `tailwind.config.ts`)

Rather than default to one of the generic AI-generated looks (cream+serif, black+acid-green, or broadsheet), the design is grounded in the one thing this product actually has that's unique: a **13-stage status pipeline**. That became the signature element — `components/jobs/status-pipeline.tsx` renders it as a connected node rail with color intensity that deepens as a candidate advances (dim gray → violet → deep violet → green), diverging to red/gray only at negative terminal states. The same component and color scale appear on every job card *and* as the dashboard's funnel chart, so the "big picture" and "this one job's position" speak the same visual language.

Type: **Space Grotesk** (display) + **Inter** (body/UI) + **JetBrains Mono** (salary figures, dates — tabular numerals so columns actually align, which matters for an audience of engineers).

## What's built

- `app/layout.tsx` — root layout, fonts wired via `next/font/google`, `AuthProvider` finally mounted (held off in Phase 2/3 on purpose)
- `app/(dashboard)/layout.tsx` + `components/layout/sidebar.tsx` — Linear/Raycast-style persistent nav shell
- `app/(dashboard)/jobs/page.tsx` — the tracker: search, status-tab filters, job cards with the pipeline rail, optimistic status updates (`useUpdateJobStatus` in `lib/hooks/use-jobs.ts` updates the UI instantly and rolls back on error)
- `app/(dashboard)/dashboard/page.tsx` — funnel chart + stat cards built from the same `ACTIVE_PIPELINE` data model. This is intentionally the lightweight version — full analytics (demand trends, charts across all saved jobs) is explicitly Phase 6 scope, not duplicated here
- `components/jobs/create-job-dialog.tsx` — the application-logging form
- Hand-rolled UI primitives (`Button`, `Badge`, `Input`, `Dialog`) in ShadCN's API style, built on Radix primitives
- Accessibility basics from the skill's quality floor: visible focus rings (`globals.css`), `prefers-reduced-motion` respected, `role="img"` + `aria-label` on the pipeline rail since its meaning isn't conveyed by text alone

## On verification — being straight with you

For the backend (Phases 2–3) I actually installed dependencies and imported the running app, which caught two real missing dependencies. I tried to do the same here: `npm install` kept getting killed mid-install because backgrounded processes don't survive between tool calls in this sandbox, and a partial install left some corrupted files that a sandbox filesystem I/O error then prevented me from fully cleaning up (harmless — cosmetic, doesn't affect the delivered source).

Since I couldn't get a real `tsc --noEmit` run, I did the closest manual substitute I could: scripted checks confirming **every internal `@/...` import resolves to a real file** and **every named import matches an actual named export** across all 30 source files — both checks came back clean on the second pass (the first pass had a bug in my own regex, not the code, which I caught by inspecting the flagged results rather than trusting them blindly). I also hand-verified every Tailwind `stage-*` color class used in components exists in the config. This is a real check, but it's not a substitute for an actual compiler run — normal small TS errors (a wrong prop type, a typo in a JSX attribute) could still be lurking. First thing to do after `npm install` locally: run `npm run typecheck`.

## Local setup

```bash
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

## Next: Phase 5 — AI Engine

This is where the product's actual differentiation lives: the JD analyzer, skill-gap engine, ATS resume optimizer, cover letter generator, and interview prep — built on the provider-abstracted AI orchestrator from the Phase 1 revision (Claude primary, OpenAI fallback, prompts as versioned files, per-call cost tracking).
