# Dex Cognitive Agents Specification

## 1. PlannerAgent (Gemini-powered)

Role:

* Interpret user input
* Generate structured plan
* Assign risk level
* Propose tool sequence

Constraints:

* Must return valid JSON schema
* Must not hallucinate tool names
* Must not generate executable shell strings directly
* Must not bypass risk gating

---

## 2. RiskEngine

Role:

* Validate risk score
* Enforce confirmation for high-risk tasks
* Log risk distribution
* Block unsafe operations

High-risk examples:

* Shell execution
* File deletion
* Email sending
* WhatsApp sending
* Reminder modification

---

## 3. ExecutorAgent

Role:

* Execute approved tools only
* Validate arguments
* Return structured result
* Never trust LLM blindly

---

## 4. VerifierAgent

Role:

* Confirm expected outcome
* Detect anomalies
* Flag incomplete execution
* Log success/failure

---

## 5. TelemetryAgent

Role:

* Record latency
* Record token usage
* Record failure cases
* Log risk category
