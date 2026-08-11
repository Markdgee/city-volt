# CityVolt — Agentic Organisation (H9CEAI Final Project)

A low-cost EV startup targeting budget-conscious urban commuters across the EU. Five agents
— **Marlowe** (Researcher) → **Iris** (Designer) → **Deshi** (Maker) → **Sasha**
(Communicator) → **Priya** (Manager) — research the live EU vehicle-registration market,
design a launch concept, build a working prototype around it, write launch copy, and produce
an executive summary.

## ⚠ One last check before you rely on this for submission

The live data source is **Eurostat's public REST API**. The dataset code (`road_eqr_zev`,
zero-emission vehicle registrations by country) was confirmed directly from Eurostat's own
"Key figures on transport - passenger car registrations" article — it's a real, current
table, not a guess. It has **not** been tool-verified from this build environment (no
network access to `ec.europa.eu` here), so do this 2-minute sanity check before you build
submission evidence around it:

1. Paste this into a browser: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/road_eqr_zev?format=JSON&lang=EN`
2. You should see a wall of JSON. If instead you get an error, try the related table
   `road_eqr_carpda` (total registrations by motor energy — useful for computing EV *share*
   of all registrations, not just raw EV counts).
3. Open `docs/index.html` directly in a browser and confirm the country bars populate with
   real numbers.

If either step fails, tell Claude the exact error/response and the parsing logic in
`pipeline.py` / `index.html` can be adjusted to match Eurostat's actual JSON-stat structure
for that table.

## Live data source

**Eurostat** — the EU's official statistics agency — publishes vehicle registration data via
a public, no-auth-required REST API:
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/road_eqr_zev`

Queried live in two places:
1. `orchestrator/pipeline.py` — Marlowe (Researcher) calls it as a real tool mid-run
2. `docs/index.html` — the deployed prototype calls it client-side via `fetch()` on load

Neither hardcodes, caches, or copy-pastes a data snapshot.

## Project structure

```
cityvolt/
├── agents/                 # Five system prompts — also your "Agent Designs" source
│   ├── 01_researcher.md
│   ├── 02_designer.md
│   ├── 03_maker.md
│   ├── 04_communicator.md
│   └── 05_manager.md
├── orchestrator/
│   ├── pipeline.py         # Runs all 5 agents; Researcher uses the live Eurostat tool
│   └── requirements.txt
├── docs/
│   └── index.html          # GitHub Pages prototype — deploy this folder
├── evidence/                # Auto-populated when you run pipeline.py
├── .env.example
└── .gitignore
```

## Running the pipeline

```bash
cd orchestrator
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp ../.env.example ../.env      # edit ../.env with your real ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY ../.env | cut -d '=' -f2)

python pipeline.py
```

Each stage prints to console and saves a timestamped `.md` file into `evidence/` — your raw
material for "The Pipeline in Action". Run it more than once across your revision weeks;
since the underlying data is live, later runs may surface a genuinely different finding.

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, folder: `/docs`.
3. Live URL: `https://<username>.github.io/<repo-name>/`.
4. Open it in a private/incognito window before submitting, to confirm no login is needed.

## What's still on you

- **Do the 2-minute sanity check above** — the code is real and confirmed, just not tool-tested from this build environment.
- **Real evidence** from your own `pipeline.py` run for the submission document.
- **Screenshots** of the deployed prototype.
- **Regulatory & Ethical Considerations** — this pivot makes GDPR and the EU AI Act directly
  applicable (CityVolt is an EU business processing EU customer/registration-adjacent data),
  which is worth leaning into in that section.
- **Reflection** — must be your own words, not AI-generated, per the module brief.

## Technical requirement checklist

- [x] At least one agent connects to a live external data source via a tool call — Researcher, via `EU_DATA_TOOL`
- [x] Live query happens at moment of use, not hardcoded/cached — both `pipeline.py` and `docs/index.html`
- [x] Dataset code confirmed real (road_eqr_zev, cited by Eurostat itself) — [ ] do the 2-min browser sanity check above
- [x] No secrets committed — `.env` is gitignored
- [ ] Zip the complete codebase for submission
- [ ] GitHub Pages URL live for 8+ weeks post-deadline
