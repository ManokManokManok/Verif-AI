# Verif-AI Rubric Demo Guide (Script + Tips)

This guide is tailored to the rubric sections shown in your screenshot:

- **Part 1: Security & Core (45 pts)**
  - Authentication
  - Input Validation
  - Database Security
  - Threat Modeling
  - Audit Trail
  - Gas Optimization

Use this as your live presenter script.

---

## 0) Demo Goal (say this first)

"In this demo, I will prove that Verif-AI implements secure authentication, strong validation, protected data access, and auditable actions. I’ll show both code evidence and test execution for each rubric criterion."

---

## 1) Fast Pre-Demo Setup (5 minutes before presenting)

### Terminal A (Backend)

```powershell
cd backend
python manage.py runserver
```


```powershell
cd contracts
npm install
npm test
```

### Terminal C (Backend targeted security tests)

```powershell
cd backend
python -m pytest tests/test_admin_security.py tests/test_validators.py -v
```

If tests are slow on your machine, run only one file live and keep the other as prepared evidence.

---

## 2) Live Demo Script (Rubric-Aligned)

## Part 1: Security & Core

### A. Authentication (Weight x2.0)

### Show

1. Open `backend/docs/SECURITY.md` and point to auth controls + MFA section.
2. Open `backend/src/interfaces/rest/views.py` and show auth endpoints (`register`, `login`, `refresh`, `logout`, MFA send/verify).
3. Open `backend/src/infrastructure/audit_logger.py` and point to auth events (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `TOKEN_REFRESH`, MFA events).

### Say

"Authentication is layered: password policy + hashing, JWT session flow, logout token invalidation, endpoint rate limiting, and MFA. Security events are audited for both successful and failed auth flows."

### Score Booster Tip

- If asked about MFA depth: mention code generation, expiry window, attempt limits, and audit logging.

---

### B. Input Validation (Weight x2.0)

### Show

1. Open `backend/src/infrastructure/validators.py` (schema validators, sanitization helpers).
2. Open `backend/tests/test_validators.py` and highlight:
   - unknown field rejection
   - email/password validation
   - HTML/script sanitization
3. Open `backend/tests/test_admin_security.py` and highlight injection/XSS test intentions.

### Say

"Validation is server-side and schema-based. Requests are validated by endpoint-specific validators, unexpected fields are rejected, and dangerous input is sanitized for safe processing/logging."

### Score Booster Tip

- Live-run `test_validators.py` if possible; it quickly proves XSS/injection-resistant validation behavior.

---

### C. Database Security (Weight x2.0)

### Show

1. Open `backend/src/infrastructure/mongodb/connection.py`:
   - TLS enforcement logic
   - role-based client/URI handling
2. Open `backend/verfai/settings.py`:
   - secure cookie flags
   - CSRF middleware
   - security logging config
3. Open `backend/docs/Plat_tech_modifications/SECURITY_REVIEW_SUMMARY.md` (Mongo least-privilege status).

### Say

"Database access is protected with role-based connection strategy and TLS enforcement for remote MongoDB. On the app side, security settings enforce secure cookies, CSRF middleware, and centralized security logging."

### Score Booster Tip

- Be explicit on production gap closure: Atlas role users and IP whitelist must be configured in deployment.

---

### D. Threat Modeling (Weight x2.0)

### Current Reality

- `backend/docs/SECURITY.md` and `backend/docs/DOCUMENTATION_IMPROVEMENTS.md` both mark **formal STRIDE threat model** as pending.

### How to Demo Without Losing Too Many Points

1. Show existing risk/security review artifacts:
   - `backend/docs/Plat_tech_modifications/SECURITY_REVIEW_SUMMARY.md`
   - `backend/docs/Plat_tech_modifications/SECURITY_REVIEW_REPORT.md`
2. State this clearly:
   - "We have implemented controls and security review evidence, and a formal STRIDE/DFD document is the next hardening artifact."

### Say

"Our controls are implemented and tested, and we maintain security review reports. The remaining documentation gap is formal STRIDE + DFD packaging, which is already listed in our next-step plan."

### Score Booster Tip

- Prepare a 1-slide mini-STRIDE matrix before demo day (even simple) to move this row closer to "Good".

---

### E. Audit Trail (Weight x1.0)

### Show

1. Open `backend/src/infrastructure/audit_logger.py`:
   - event taxonomy
   - dual-write behavior (security logger + Mongo collection)
   - TTL index for retention
2. Open `backend/verfai/settings.py`:
   - `security.log` rotating handler
   - sensitive-data filtering
3. Open `backend/src/interfaces/rest/views.py` and show examples of `get_audit_logger().log_event(...)` in auth flows.

### Say

"All critical auth and user-management actions are logged through a centralized audit service with structured event types, retention controls, and sensitive-data filtering."

### Score Booster Tip

- Mention that external log storage/SIEM export is the next step if examiner asks for stronger tamper-evidence guarantees.

---


### Say

"The system enforces least-privilege writes, strict input checks, and privacy-first storage design. We validate this with automated tests and static security audit evidence."

### Score Booster Tip

- Run `npm test` live and call out the unauthorized access + invalid data tests as security proof.

---

### G. Gas Optimization (Weight x2.0)

### Show

1. Open the deployment or security notes and point to the relevant operational guidance.
2. Open a representative backend test and highlight the assertion that demonstrates the workflow.

### Say

"We optimized the logging path to preserve verifiability requirements while reducing storage overhead."

### Score Booster Tip

- Emphasize benchmark evidence + explicit gas threshold test (not just claim).

---

## 3) 12-Minute Demo Timeline

- **Minute 0-1:** architecture + objective
- **Minute 1-4:** Authentication + Input Validation
- **Minute 4-6:** Database Security + Audit Trail
- **Minute 6-7:** Threat modeling status + mitigation plan
- **Minute 7-10:** Security tests and validation evidence
- **Minute 10-11:** Gas optimization proof
- **Minute 11-12:** recap mapped to rubric rows

---

## 4) Recap Slide Script (Final 30 seconds)

"For Security & Core, we demonstrated strong authentication, schema-based validation, hardened data access settings, and centralized auditability with test and code evidence."

---

## 5) High-Impact Tips to Maximize Rubric Score

1. **Always pair claim + proof** (code file + test output + doc reference).
2. **Demo failures intentionally** (unauthorized call, invalid input) to show controls actually block attacks.
3. **Be honest about gap items** (formal STRIDE/DFD) and present a concrete completion plan.
4. **Keep one "evidence tab set" ready** in your editor to avoid slow navigation.
5. **End each section with rubric language**: "This addresses Authentication/Input Validation/...".

---

## 6) Optional One-Command Evidence Pack (if you want a clean run)

```powershell
# Backend security checks
cd backend
python -m pytest tests/test_validators.py tests/test_admin_security.py -v

npm test
```

If environment issues occur during live presentation, show prepared logs/screenshots and continue with code walkthrough.
