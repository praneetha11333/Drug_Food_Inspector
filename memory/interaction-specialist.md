# Interaction Specialist — Agent

## Role
A single agent responsible for one job: take the user's drug, food, and symptoms — look it up using real APIs — and return a severity with a summary.

---

## Input (from LangGraph State)
- Drug name
- Food consumed
- Symptoms reported
- Timing

## Output (to LangGraph State)
- `rxcui` — normalized drug identifier
- `interaction_summary` — plain language summary of the interaction
- `severity` — `mild` | `moderate` | `severe`

---

## What It Does

### Step 1 — Normalize Drug Name
- Calls **RxNav API** with the drug name
- Returns a standard `RxCUI` identifier
- If no match → ask user to clarify drug name, do not proceed

### Step 2 — Fetch Interaction Data
- Calls **OpenFDA API** using the `RxCUI`
- Retrieves real adverse event reports from the FDA database

### Step 3 — Analyze & Output
- Cross-references user symptoms against fetched adverse event data
- Determines severity based on fetched data, not LLM knowledge
- Writes `rxcui`, `interaction_summary`, and `severity` to LangGraph State

---

## Tools (Real API Calls — Not LLM Knowledge)
- `rxnav_normalize(drug_name)` → `https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug}`
- `openfda_fetch(rxcui)` → `https://api.fda.gov/drug/event.json?search=patient.drug.openfda.rxcui:{rxcui}`

---

## Rules
- Always normalize before querying OpenFDA
- Never determine severity from LLM knowledge — only from fetched data
- Does not recommend or schedule — only analyzes and outputs severity
