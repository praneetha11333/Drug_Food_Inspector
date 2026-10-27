# Remedy Advisor — Agent

## Role
Activated for `mild` cases only. Gives the user simple, safe things they can do at home.

---

## Input (from LangGraph State)
- `severity` — `mild`
- `interaction_summary`
- Drug name, food, symptoms

## Output (to User via Stream)
- 2–3 practical home remedy suggestions based on the interaction
- A warning: if symptoms worsen, seek medical attention

---

## What It Does
- Reads the interaction summary from LangGraph State
- Suggests practical actions (e.g. hydration, rest, avoid further intake)
- Always ends with: "if symptoms worsen, see a doctor"

---

## Rules
- Never recommend prescription medications
- Keep it short — 2 to 3 suggestions only
- Does not handle moderate or severe cases
