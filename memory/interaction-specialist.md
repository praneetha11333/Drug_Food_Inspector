# Interaction Specialist — Agentic Workflow

## Trigger
User reports taking a medication alongside food and describes symptoms.

---

## Workflow Steps

### 1. Collect Input
- Drug name(s) taken
- Food consumed
- Symptoms reported
- Timing (when taken, when symptoms started)

### 2. Normalize Drug Name
- Call **RxNav API** to resolve and normalize the drug name to a standard RxCUI identifier
- Handle brand names, generics, and misspellings

### 3. Fetch Interaction Data
- Call **OpenFDA API** using the normalized drug identifier
- Retrieve known drug–food interactions and adverse event reports

### 4. Analyze & Summarize
- Cross-reference reported symptoms against fetched interaction data
- Determine severity: `mild` | `moderate` | `severe`
- Summarize the likely interaction in plain language

### 5. Take Action (based on severity)

| Severity | Action |
|----------|--------|
| Mild | Provide home remedy recommendations |
| Moderate | Provide recommendations + advise monitoring |
| Severe | Immediately recommend scheduling a doctor's appointment |

---

## APIs Used
- **RxNav API** — Drug name normalization → `https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug}`
- **OpenFDA API** — Interaction & adverse event data → `https://api.fda.gov/drug/event.json`

---

## Notes
- Always normalize before querying OpenFDA to ensure accurate results
- If RxNav returns no match, prompt user to clarify the drug name before proceeding
- Severe cases must bypass recommendations and go directly to appointment scheduling
