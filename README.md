# Raise ExxonMobil Recruiting Agent

Automates candidate record writing in WorkLlama. Replaces the Word doc
copy-paste workflow with a recruiter-facing screening form that writes
directly to WorkLlama via browser automation.

---

## What it does

1. Recruiter opens the screening form during a live call
2. Salesforce data pre-fills known fields
3. Recruiter captures live call fields (pay rate, commute, XOM history, etc.)
4. On submit, Claude generates a professional handoff note
5. Playwright logs into WorkLlama and writes all fields + note directly
6. No copy-paste. No Word doc. One button.

---

## Stack

- **Flask** — web server + screening form
- **Claude API (claude-sonnet-4-20250514)** — handoff note generation
- **Playwright (Chromium)** — WorkLlama browser automation
- **Render** — cloud hosting

---

## Deploy to Render

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial deploy"
git remote add origin https://github.com/YOUR_ORG/raise-exxon-agent.git
git push -u origin main
```

### Step 2 — Create Render service

1. Go to https://render.com and create a new Web Service
2. Connect your GitHub repo
3. Render will detect `render.yaml` automatically

### Step 3 — Set environment variables in Render dashboard

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (from console.anthropic.com) |
| `WORKLLAMA_URL` | `https://app.workllama.com` (confirm with Vishnu/Surbhi) |
| `WORKLLAMA_EMAIL` | The Raise service account email for WorkLlama |
| `WORKLLAMA_PASSWORD` | The password for that account |

> Use a dedicated service account for WorkLlama — not a personal recruiter login.
> Ask Vishnu or Surbhi to create one labeled something like `agent@raiserecruiting.com`.

### Step 4 — Deploy

Render builds automatically. First build takes ~3 minutes (Playwright install).

---

## Update WorkLlama selectors (do this once you have access)

All placeholder selectors are in `agent.py` at the top, clearly marked with `# TODO: verify`.

The fastest way to get real selectors:

```bash
pip install playwright
playwright install chromium
playwright codegen https://app.workllama.com
```

This opens a browser with a live selector inspector. Log in, navigate to a
candidate record, hover over each field, and copy the selector it shows.
Replace the corresponding `# TODO: verify` line in `agent.py`.

Fields to capture selectors for:
- Login email input
- Login password input
- Login submit button
- Candidate search input
- Search result row (to click into candidate)
- Phone, city, pay rate fields
- Source and work auth dropdowns
- Notes tab button
- Add note button
- Note textarea
- Note save button

---

## Run locally for testing

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

export ANTHROPIC_API_KEY=sk-...
export WORKLLAMA_EMAIL=agent@raiserecruiting.com
export WORKLLAMA_PASSWORD=...

python app.py
```

Open http://localhost:5000 in your browser.

To test the form without hitting WorkLlama, comment out the
`write_to_workllama` call in `app.py` and just return the generated note.

---

## Open questions to resolve with WorkLlama access

- [ ] Confirm the WorkLlama app URL (may differ from app.workllama.com)
- [ ] Confirm whether candidate lookup works by email or requires internal ID
- [ ] Confirm field names for source and work auth dropdowns (option labels matter for select_option)
- [ ] Confirm whether note creation requires a specific note type selection
- [ ] Confirm whether Beeline submission can be triggered from WorkLlama UI or only via Beeline directly

---

## Next phases

- **Phase 2** — Beeline portal submission via browser automation (RTR attachment + candidate submit)
- **Phase 3** — Salesforce status update via MCP after WorkLlama write completes
- **Phase 4** — Teams channel notification via Microsoft 365 MCP
- **Phase 5** — Automated talent community matching when new Beeline req arrives
