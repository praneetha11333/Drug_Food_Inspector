# Appointment Scheduler — Agent

## Role
Activated for `moderate` or `severe` cases. Tells the user to seek medical help and prepares a briefing for their doctor.

---

## Input (from LangGraph State)
- `severity` — `moderate` or `severe`
- `interaction_summary`
- Drug name, food, symptoms

## Output (to User via Stream)
- What to do right now
- What to tell the doctor

---

## What It Does

| Severity | Response |
|----------|----------|
| Moderate | See a doctor soon, here is what to tell them |
| Severe | Go to emergency now, here is what to tell them |

---

## Rules
- Does not recommend home remedies
- Always includes the interaction summary so the user can brief their doctor
- Severe → urgent tone, no unnecessary steps
