# Agent instructions

Instructions for AI coding agents working in this repository. Follow these in
addition to any default behaviour of your tool.

## Commit messages: no AI attribution

Commit messages in this repository must contain **no AI attribution**. Do not
append, sign, or co-author with any AI tool.

Never include these lines, or any equivalent wording:

```
Generated with Codebuff 🤖
Co-Authored-By: Codebuff <noreply@codebuff.com>
```

The rule applies to any agent, not just Codebuff: no `Generated with ...` line,
no `Co-Authored-By` trailer naming an AI assistant, and no other signature that
credits a tool rather than a person. Authorship belongs to the human committer.

End each commit message at its own final line of content.

## Commits

- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
- Keep each commit to a single coherent concern.
- Do not commit build output (`build/`, `.svelte-kit/`, `node_modules/`) or
  local environments (`.venv/`); both `.gitignore` files cover these.

## Before committing

Run the checks for whatever you touched:

```bash
uv run pytest                 # API (52 tests)
cd frontend && npm test       # frontend (18 tests)
cd frontend && npm run check  # types and a11y
```
