"""
Performance monitoring script for VerfAi authentication pipeline.
Session 1 Activity: Prototype Monitoring

Tests two critical auth functions independently with 3 test cases each:

  FUNCTION 4 — SignupUseCase.execute()
    Critical operation: bcrypt password hashing (12 rounds) + validation logic.
    Test cases vary path: valid signup / duplicate email / weak password.

  FUNCTION 5 — LoginUseCase.execute()
    Critical operation: bcrypt password verification + JWT token generation.
    Test cases vary path: valid login / wrong password / non-existent user.

No AI models required — runs immediately without model loading.

Run from within the backend virtual environment:
    cd backend
    .venv\\Scripts\\activate
    cd "../MODEL TEST"
    python test_auth_performance.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.use_cases.auth import SignupUseCase, LoginUseCase
from src.domain.services import BCryptPasswordHasher, EmailValidator, PasswordValidator
from src.domain.entities import User, UserAlreadyExistsError, InvalidCredentialsError
from src.infrastructure.jwt_service import JWTService

SEP  = "=" * 80
SEP2 = "-" * 80

# ---------------------------------------------------------------------------
# Minimal in-memory mock for UserRepository
# ---------------------------------------------------------------------------
class _MockUserRepo:
    def __init__(self):
        self._users: dict[str, User] = {}  # keyed by email
        self._counter = 1

    def create_user(self, user: User) -> User:
        user.id = f"mock-user-{self._counter}"
        self._counter += 1
        self._users[user.email] = user
        return user

    def get_by_email(self, email: str):
        return self._users.get(email)

    def get_by_id(self, user_id: str):
        for u in self._users.values():
            if u.id == user_id:
                return u
        return None

    def update_last_login(self, user_id: str) -> None:
        pass

    def get_user_roles(self, user_id: str) -> list:
        return []


def fmt_time(seconds: float) -> str:
    return f"{seconds:.3f} sec"


# ---------------------------------------------------------------------------
# FUNCTION 4 — SignupUseCase.execute()
# Test cases cover: success / duplicate email / weak password
# ---------------------------------------------------------------------------
SIGNUP_TEST_CASES = [
    (
        "Valid New User",
        "testuser@example.com",
        "TestUser",
        "SecurePass1!",
        "Full path: email validation → password validation → bcrypt hash → DB save",
    ),
    (
        "Duplicate Email",
        "testuser@example.com",   # same as above — already in repo after test 1
        "TestUser2",
        "SecurePass1!",
        "Early exit after DB lookup (no bcrypt — fastest path)",
    ),
    (
        "Weak Password",
        "weakuser@example.com",
        "WeakUser",
        "password",               # fails PasswordValidator before bcrypt
        "Exits at password validation — no bcrypt called",
    ),
]


def signup_bottleneck(elapsed: float, outcome: str) -> str:
    if outcome == "error_duplicate":
        return "Negligible — exits at duplicate check"
    if outcome == "error_weak_password":
        return "Negligible — exits at password validation"
    if elapsed > 0.5:
        return "bcrypt hashing (12 rounds) — intentional security cost"
    return "bcrypt hashing — within expected range"


def run_signup_tests(signup_uc):
    print(f"\n{SEP}")
    print("FUNCTION 4: SignupUseCase.execute()")
    print("Critical operation: input validation + bcrypt password hashing")
    print(SEP)

    results = []
    for label, email, username, password, expected_path in SIGNUP_TEST_CASES:
        print(f"\n  [{label}]")
        print(f"  Email    : {email}  |  Password: {password}")
        print(f"  Expected : {expected_path}")

        outcome = "success"
        created_user = None
        error_msg = None

        start = time.time()
        try:
            created_user = signup_uc.execute(email, username, password)
        except UserAlreadyExistsError as e:
            outcome = "error_duplicate"
            error_msg = str(e)
        except ValueError as e:
            outcome = "error_weak_password"
            error_msg = str(e)
        end = time.time()
        elapsed = end - start

        bottleneck = signup_bottleneck(elapsed, outcome)

        if outcome == "success":
            print(f"  Result   : User created — ID: {created_user.id}")
        else:
            print(f"  Result   : {outcome} — {error_msg[:80]}")
        print(f"  Time     : {fmt_time(elapsed)}")
        print(f"  Bottleneck: {bottleneck}")

        results.append({
            "label":      label,
            "outcome":    outcome,
            "elapsed":    elapsed,
            "bottleneck": bottleneck,
        })

    # Performance table
    print(f"\n{SEP}")
    print("PERFORMANCE TABLE — Function 4: SignupUseCase.execute()")
    print(SEP)
    row = "{:<28}  {:<12}  {:<22}  {:<35}"
    print(row.format("Test Case", "Time", "Outcome", "Identified Bottleneck"))
    print(SEP2)
    for r in results:
        print(row.format(
            r["label"][:28],
            fmt_time(r["elapsed"]),
            r["outcome"][:22],
            r["bottleneck"][:35],
        ))
    print(SEP)

    return results


# ---------------------------------------------------------------------------
# FUNCTION 5 — LoginUseCase.execute()
# Test cases cover: valid login / wrong password / non-existent user
# ---------------------------------------------------------------------------
LOGIN_TEST_CASES = [
    (
        "Valid Credentials",
        "testuser@example.com",
        "SecurePass1!",
        "Full path: DB lookup → bcrypt verify → JWT generation",
    ),
    (
        "Wrong Password",
        "testuser@example.com",
        "WrongPass99!",
        "DB lookup succeeds → bcrypt verify runs fully → fails",
    ),
    (
        "Non-existent User",
        "nobody@example.com",
        "AnyPass1!",
        "Early exit after DB lookup — no bcrypt called",
    ),
]


def login_bottleneck(elapsed: float, outcome: str) -> str:
    if outcome == "error_not_found":
        return "Negligible — exits at user lookup"
    if outcome == "error_wrong_password":
        if elapsed > 0.3:
            return "bcrypt verify still runs fully even on failure"
        return "bcrypt verify ran — within range"
    if elapsed > 0.5:
        return "bcrypt verify (12 rounds) + JWT generation"
    return "bcrypt verify + JWT — within expected range"


def run_login_tests(login_uc):
    print(f"\n{SEP}")
    print("FUNCTION 5: LoginUseCase.execute()")
    print("Critical operation: bcrypt password verification + JWT token generation")
    print(SEP)

    results = []
    for label, email, password, expected_path in LOGIN_TEST_CASES:
        print(f"\n  [{label}]")
        print(f"  Email    : {email}  |  Password: {password}")
        print(f"  Expected : {expected_path}")

        outcome = "success"
        auth_result = None
        error_msg = None

        start = time.time()
        try:
            auth_result = login_uc.execute(email, password)
        except InvalidCredentialsError as e:
            error_msg = str(e)
            outcome = "error_wrong_password" if "password" in str(e).lower() or "invalid" in str(e).lower() else "error_not_found"
            # Distinguish: if user doesn't exist the repo returns None instantly
            # We detect this by checking if it was a very fast fail
        end = time.time()
        elapsed = end - start

        # Refine outcome: non-existent user lookup is near-instant
        if outcome != "success" and elapsed < 0.05:
            outcome = "error_not_found"

        bottleneck = login_bottleneck(elapsed, outcome)

        if outcome == "success":
            print(f"  Result   : Login OK — access token issued")
            print(f"             Token: {auth_result.tokens.access_token[:40]}...")
        else:
            print(f"  Result   : {outcome} — {error_msg}")
        print(f"  Time     : {fmt_time(elapsed)}")
        print(f"  Bottleneck: {bottleneck}")

        results.append({
            "label":      label,
            "outcome":    outcome,
            "elapsed":    elapsed,
            "bottleneck": bottleneck,
        })

    # Performance table
    print(f"\n{SEP}")
    print("PERFORMANCE TABLE — Function 5: LoginUseCase.execute()")
    print(SEP)
    row = "{:<28}  {:<12}  {:<22}  {:<35}"
    print(row.format("Test Case", "Time", "Outcome", "Identified Bottleneck"))
    print(SEP2)
    for r in results:
        print(row.format(
            r["label"][:28],
            fmt_time(r["elapsed"]),
            r["outcome"][:22],
            r["bottleneck"][:35],
        ))
    print(SEP)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("VERFAI — SESSION 1 ACTIVITY: PROTOTYPE MONITORING")
    print("Functions 4 & 5: Authentication pipeline (no AI models required)")
    print(SEP)

    # --- Shared real dependencies (no mocks for the actual logic) ---
    print("\nInitializing auth services...")
    hasher     = BCryptPasswordHasher(rounds=12)   # production setting
    jwt_svc    = JWTService(secret_key="perf-test-secret-key")
    email_val  = EmailValidator()
    pass_val   = PasswordValidator()
    user_repo  = _MockUserRepo()

    signup_uc  = SignupUseCase(user_repo, hasher, email_val, pass_val)
    login_uc   = LoginUseCase(user_repo, hasher, jwt_svc)

    print("  [OK] BCryptPasswordHasher (12 rounds)")
    print("  [OK] JWTService")
    print("  [OK] In-memory UserRepository")
    print()
    print("  NOTE: Signup test 1 creates the user that Login tests 1 & 2 use.")
    print("        Run order matters — do not reorder test cases.")

    # Run signup first (seeds the user repo for login tests)
    run_signup_tests(signup_uc)
    run_login_tests(login_uc)

    print("\nDone. Both performance tables above can be submitted for the activity.")
    print(SEP)


if __name__ == "__main__":
    main()
