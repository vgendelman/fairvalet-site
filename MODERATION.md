# FairValet report moderation

Free pipeline using GitHub Issues + Actions + Pages. No paid services.

## Flow

1. **Submit** — The public form creates a GitHub Issue labeled `pending-report` (via a public intake token). New-issue email notify (Gmail via Actions) is best-effort only and must not block intake.
2. **Review** — Open [issues with `pending-report`](https://github.com/vgendelman/fairvalet-site/issues?q=is%3Aissue+label%3Apending-report).
3. **Approve** — As a repo collaborator/owner, comment exactly:
   ```
   approve
   ```
   (case-insensitive; optional surrounding whitespace). The Action appends the report to `data/reports.json` (email omitted), commits, labels `published`, closes the issue, and may email the submitter a short confirmation via FormSubmit if they left an address.
4. **Reject** — Comment:
   ```
   reject <reason>
   ```
   Labels `rejected`, closes the issue, posts an acknowledgment. Nothing is published.

## Where data lives

| Stage | Location |
| --- | --- |
| Pending | GitHub Issues (`pending-report`) |
| Published | `data/reports.json` → rendered on https://fairvalet.org/reports/ |
| Rejected | Closed issues (`rejected`) |

Public JSON fields only: `id`, `name`, `venue`, `location`, `type`, `title` (optional; short complaint/note title from the form), `details`, `submitted_at`, `published_at`, `issue_number`. Older published rows may still include a legacy `date_shared` key; new reports do not collect or persist it. Published cards show: title → note/details → venue/location → name/date (`submitted_at`, else `published_at`). Older reports without `title` fall back to the type label as the heading. Never put private email in that file.

Submitting the public form always implies consent to publish after review (`consent_public` is always `yes` in the issue payload). There is no opt-out checkbox.

## Intake token (privacy / spam note)

`assets/intake-config.js` is **not** committed. `.github/workflows/deploy-pages.yml` writes it from repo secret `FAIRVALET_INTAKE_TOKEN` into the GitHub Pages deploy artifact only (so main stays clean of secrets; push protection is satisfied).

- Prefer a fine-grained PAT with **Issues: Read and write** on **this repo only**.
- The token is still **publicly readable** on the live static site. Anyone can create issues in this repo with it.
- Mitigations: honeypot on the form, rate limits / abuse monitoring, rotate the secret and re-run **Deploy GitHub Pages** if spam appears.
- Rotate: create a new PAT → `gh secret set FAIRVALET_INTAKE_TOKEN` → push to `main` or run the deploy-pages workflow.
- GitHub Pages must use **Source: GitHub Actions** (not “Deploy from branch”) so the injected file is what visitors get.

`assets/intake-config.example.js` is the committed placeholder. Real `intake-config.js` is gitignored.

## Labels

- `pending-report` — awaiting decision
- `published` — on the site
- `rejected` — not published

## New-issue email notify (Gmail / Vgnoid)

When a new issue opens with label `pending-report` or a title starting with `Report:` (titles containing `TEST` are skipped), workflow [`.github/workflows/notify-new-issue.yml`](.github/workflows/notify-new-issue.yml) emails **from** `Vgnoid@gmail.com` **to** `vgendelman@gmail.com` via Gmail SMTP (`dawidd6/action-send-mail`). Failures are non-fatal (logged; intake still succeeds).

### Required repo secret

| Secret | Value |
| --- | --- |
| `GMAIL_VGNOID_APP_PASSWORD` | 16-character Gmail **App Password** for `Vgnoid@gmail.com` |

Create the App Password (signed in as Vgnoid):

1. Enable **2-Step Verification** on the Google Account: https://myaccount.google.com/signinoptions/two-step
2. Open **App passwords**: https://myaccount.google.com/apppasswords (or Security → 2-Step Verification → App passwords)
3. App name e.g. `FairValet GitHub Notify` → Generate → copy the 16-character password (spaces optional)
4. Add the repo secret (do not paste the password into chat/issues):
   ```bash
   gh secret set GMAIL_VGNOID_APP_PASSWORD --repo vgendelman/fairvalet-site
   ```
   Or: repo → Settings → Secrets and variables → Actions → New repository secret → name `GMAIL_VGNOID_APP_PASSWORD`.

Until the secret is set, the workflow skips send and logs a warning; it will not fail the run.

Site-side FormSubmit (if still present on the form) remains optional fire-and-forget and is unrelated to this workflow.

## FormSubmit confirmation (approve path)

On approve, if the issue JSON includes an email, Actions POSTs to `https://formsubmit.co/ajax/{email}`. FormSubmit may require a one-time activation link the first time an address is used; failures are non-fatal.

## Setup blocker: installing GitHub Actions workflows

The `gh` OAuth token used by this environment has scopes `repo`, `gist`, `read:org` but **not** `workflow`. GitHub rejects any git push that adds or changes files under `.github/workflows/` with that token.

### One-time fix (pick one)

1. **Preferred — grant workflow scope, then push**
   ```bash
   gh auth refresh -h github.com -s repo,workflow
   cd /path/to/fairvalet-site
   mkdir -p .github/workflows
   cp docs/workflows/*.yml .github/workflows/
   git add .github/workflows
   git commit -m "Add moderation and Pages deploy workflows"
   git push origin main
   ```
2. **Or — paste via GitHub web UI** (no `workflow` scope needed for UI edits)
   - Open the repo → **Add file** → create `.github/workflows/deploy-pages.yml` and paste contents from [`docs/workflows/deploy-pages.yml`](docs/workflows/deploy-pages.yml)
   - Same for `.github/workflows/moderate-report.yml` from [`docs/workflows/moderate-report.yml`](docs/workflows/moderate-report.yml)
3. **Then enable Pages from Actions**
   - Settings → Pages → Build and deployment → Source: **GitHub Actions**
   - Run workflow **Deploy GitHub Pages** (or push any commit to `main`)
   - Confirm `https://fairvalet.org/assets/intake-config.js` loads (token injected from `FAIRVALET_INTAKE_TOKEN`)

Until workflows are installed: auto Issue creation and approve/reject Actions do not run; set `GMAIL_VGNOID_APP_PASSWORD` after workflows are live for new-issue Gmail notify.
