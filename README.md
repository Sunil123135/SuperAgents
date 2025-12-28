# Automation Flows & Planning Prompts

This README captures:
1) Final prompts for the four scripted flows.  
2) Code changes made to enable scripted runs and planning.  
3) Step-by-step approach to derive the final prompts (flows and the planning prompt).

---

## Final Prompts (Scripted Flows)

These are the exact TASK texts in `tasks/flows.yaml` (runtime prepends the POLICY preamble from `main.py`):

1) **wiki_extract**  
   ```
   Open Wikipedia. Search for "Supply chain". Open the article.
   Copy the first paragraph and save it to outputs/wiki_supply_chain.txt.
   Then summarize it in 5 bullet points and save to outputs/wiki_summary.json.
   ```
   Evidence: `outputs/wiki_supply_chain.txt`, `outputs/wiki_summary.json`

2) **maps_route**  
   ```
   Open Google Maps. Get driving directions from Hyderabad to Bangalore.
   Extract distance and ETA and save to outputs/maps_route.json.
   ```
   Evidence: `outputs/maps_route.json`

3) **yt_metadata**  
   ```
   Open YouTube. Search for "inventory optimization tutorial".
   Open the top result. Extract title, channel, duration.
   Save to outputs/youtube_top_result.csv.
   ```
   Evidence: `outputs/youtube_top_result.csv`

4) **ppt_edit**  
   ```
   Open the PowerPoint deck at C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 13\Code\temp\deck.pptx
   Standardize title font to Calibri 32 on all slides, add slide numbers,
   export to outputs/deck.pdf, and save updated deck to outputs/deck_updated.pptx.
   ```
   Evidence: `outputs/deck.pdf`, `outputs/deck_updated.pptx`

**Policy preamble (auto-prepended in `main.py`):**
```
POLICY:
- Do not sign in, create accounts, or enter passwords/OTP/payment details.
- If a login wall appears, stop and report BLOCKED_BY_POLICY.
- Save artifacts to ./outputs and reference exact file paths in the final JSON.
```

---

## Planning Prompt (Final)

Used to force a structured, checkbox plan from the LLM (e.g., Gemini):
```
You are a planning agent. For any user goal, output a concise, phase-based execution plan with checkboxes and 1–3 sentence guidance per phase.

Rules:
- Phases (in order): Research -> Design -> Development -> Presentation -> Testing/Finalization -> Delivery.
- Under each phase, list 4–8 concrete, ordered tasks with '- [ ]' checkboxes.
- Keep tasks specific, actionable, and scoped to the user's goal; classroom-friendly if educational.
- Include brief tooling/format hints when relevant (e.g., JS/CSS/HTML; Canvas/SVG/Three.js).
- Avoid filler; no prose outside the plan.
- Do not invent constraints beyond the user's ask.
- If animations or code are involved, note frameworks or file types briefly (e.g., HTML/CSS/JS).
- End with a short 'Deliverables' block listing expected artifacts/links/files.

User goal:
'I am a middle school physics teacher preparing to teach the law of conservation of momentum. Could you create a series of clear and accurate demonstration animations and organize them into a simple presentation html?'
```

---

## Code Changes Summary

**Prompts**
- `prompts/decision_prompt.txt`: Added Run Mode contract (tool-first, retries, success JSON).
- `prompts/browser_decision_prompt.txt`: Added browser selector/screenshot discipline.
- `prompts/summarizer_prompt.txt`: Added structured evidence output (summary, evidence checklist, artifacts, final JSON).

**Scripted runs & logging**
- `main.py`: Added `--run tasks/flows.yaml` mode, policy preamble injection, per-flow result logging to `runs/<flow_id>/result.json`, index at `runs/index.json`, evidence checks, optional OBS hooks. Added status reset per run.
- `tasks/flows.yaml`: Added four flows (wiki_extract, maps_route, yt_metadata, ppt_edit) with evidence targets.
- `utils/utils.py`: Hardened `log_step` to strip non-ASCII symbols to avoid Windows console encoding errors.

**Planning helper**
- `tmp_plan.py`: Small helper to call the planning prompt via `ModelManager`/Gemini.

**Generated/updated runtime artifacts**
- `runs/wiki_extract/result.json` (failed due to missing browser tooling).
- Stubbed `runs/yt_metadata/result.json`, `runs/ppt_edit/result.json` (not executed; tooling unavailable).

---

## Step-by-Step Approach to Final Prompts

1) **Identify flow goals & evidence**  
   - Captured each flow’s task and required output artifacts in `tasks/flows.yaml`.  
   - Added policy preamble to enforce safety and file-path reporting.

2) **Strengthen planner & browser prompts**  
   - Decision prompt: added Run Mode contract (tool-first, retries, structured success JSON).  
   - Browser prompt: added selector discipline and mandatory screenshots.  
   - Summarizer prompt: required evidence checklist, artifacts list, final JSON.

3) **Scripted execution path**  
   - Added `--run tasks/flows.yaml` to `main.py`, per-flow logging to `runs/`, evidence checks, and optional OBS recording hooks.

4) **Stabilize logging**  
   - Stripped non-ASCII symbols in `log_step` to prevent Windows console Unicode errors during runs.

5) **Derive a reusable planning prompt**  
   - Requirements: phase-based, checkbox tasks, concise guidance, tooling hints, deliverables block.  
   - Validated via `tmp_plan.py` calling Gemini; captured the returned plan for the conservation-of-momentum animations request.

6) **Runtime observations**  
   - Browser MCP tooling is currently unavailable/disabled (SSE/browser agent), so only `wiki_extract` ran and failed; other flows were stubbed with `success=false`.  
   - To execute flows end-to-end, enable a browser MCP server/SSE proxy and rerun `uv run main.py --run tasks/flows.yaml`.

---

## How to Reproduce

1) Ensure `.env` has `GEMINI_API_KEY`.  
2) (Optional) Enable browser MCP/SSE and start proxy if you need browser flows.  
3) Run scripted flows:  
   ```
   uv run main.py --run tasks/flows.yaml
   ```
4) Results: `runs/<flow_id>/result.json`, index at `runs/index.json`.  
5) Planning prompt test (prints Gemini plan):  
   ```
   uv run tmp_plan.py
   ```

---

## Deliverables (Current State)

- Final flow prompts: `tasks/flows.yaml` (with policy preamble in `main.py`).  
- Planning prompt: see section above (also in `tmp_plan.py`).  
- Logs/Results: `runs/wiki_extract/result.json` (failed due to missing browser tools); stub JSONs for `yt_metadata`, `ppt_edit`.  
- Updated prompts and runtime code as listed in “Code Changes Summary.”
