"""Acceptance tests AT-01 to AT-09 (see docs/requirements.md) plus parser checks."""
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from backend import auth, config, db, ledger, matching, reports, timeutil
from backend.app import app

T0 = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)


def mins(n):
    return T0 + timedelta(minutes=n)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE", str(tmp_path / "test.db"))
    monkeypatch.setattr(config, "DEMO_MODE", True)
    monkeypatch.setattr(config, "ENABLE_SIMULATOR", True)
    from backend import rate_limit
    rate_limit.limiter.clear_all()
    db.init_db()


def sale_row(sale_id):
    return db.query("SELECT * FROM sales WHERE id=?", (sale_id,))[0]


def alert_types(sale_id=None):
    rows = db.query("SELECT type FROM alerts WHERE resolved_at IS NULL AND sale_id IS ?", (sale_id,)) if sale_id is None \
        else db.query("SELECT type FROM alerts WHERE resolved_at IS NULL AND sale_id=?", (sale_id,))
    return [r["type"] for r in rows]


def test_at01_matching_payment_verifies_sale():
    sid = matching.create_sale(500, now=T0)["sale_id"]
    res = matching.process_payment(500, "TX0001ABC", "telebirr", now=mins(1))
    assert res == {"result": "verified", "sale_id": sid}
    assert sale_row(sid)["status"] == "verified"
    assert ledger.verify_chain()["entries"] == 1


def test_at02_wrong_amount_not_verified():
    sid = matching.create_sale(500, now=T0)["sale_id"]
    res = matching.process_payment(300, "TX0002ABC", now=mins(1))
    assert res["result"] == "mismatch"
    assert sale_row(sid)["status"] == "pending"
    assert "wrong_amount" in alert_types(sid)


def test_at03_duplicate_txn_id_flagged():
    a = matching.create_sale(500, now=T0)["sale_id"]
    matching.process_payment(500, "TX0003ABC", now=mins(1))
    b = matching.create_sale(500, now=mins(2))["sale_id"]
    res = matching.process_payment(500, "TX0003ABC", now=mins(3))
    assert res["result"] == "duplicate"
    assert sale_row(b)["status"] == "pending"
    assert "duplicate_txn" in alert_types(None)


def test_at04_alert_stages():
    sid = matching.create_sale(500, now=T0)["sale_id"]
    assert matching.sale_state(sale_row(sid), mins(1)) == "pending"
    assert matching.sale_state(sale_row(sid), mins(3)) == "waiting"
    matching.refresh_alerts(mins(3))
    assert alert_types(sid) == ["waiting"]
    assert matching.sale_state(sale_row(sid), mins(11)) == "alert"
    matching.refresh_alerts(mins(11))
    matching.refresh_alerts(mins(12))            # must not duplicate alerts
    assert sorted(alert_types(sid)) == ["no_payment", "waiting"]


def test_at05_unassigned_payment():
    res = matching.process_payment(750, "TX0005ABC", now=mins(1))
    assert res["result"] == "unassigned"
    row = db.query("SELECT * FROM payments WHERE txn_id='TX0005ABC'")[0]
    assert row["matched_sale_id"] is None


def test_at06_hash_chain_detects_edit():
    for i, amt in enumerate((100, 200, 300)):
        matching.create_sale(amt, now=mins(i))
        matching.process_payment(amt, f"TX0006A{i}B", now=mins(i))
    assert ledger.verify_chain()["ok"]
    conn = sqlite3.connect(config.DATABASE)
    conn.execute("UPDATE ledger SET amount = 1 WHERE id = 2")
    conn.commit()
    conn.close()
    result = ledger.verify_chain()
    assert not result["ok"] and result["broken_at"] == 2


def test_at07_missing_token_rejected():
    client = app.test_client()
    # Physical Gateway Field Trial 1: default sender '127' without token -> rejected (401)
    t1 = client.post("/api/sms", json={"sender": "127", "message": "x"})
    assert t1.status_code == 401

    # Physical Gateway Field Trial 2: wildcard sender '*' without token -> rejected (401)
    t2 = client.post("/api/sms", json={"sender": "*", "message": "x"})
    assert t2.status_code == 401

    # Invalid token rejected
    assert client.post("/api/sms", json={"message": "x"},
                       headers={"X-Token": "wrong"}).status_code == 401

    # Physical Gateway Field Trial 3: authenticated webhook succeeds (200)
    # Accepts token via X-Token header or ?token= URL query parameter
    ok_hdr = client.post("/api/sms", json={"message": "x"}, headers={"X-Token": config.SMS_TOKEN})
    assert ok_hdr.status_code == 200

    ok_query = client.post(f"/api/sms?token={config.SMS_TOKEN}", json={"message": "x"})
    assert ok_query.status_code == 200


def test_at08_otp_discarded():
    client = app.test_client()
    r = client.post("/api/sms", json={"message": "Your OTP is 123456. You received 500 ETB. Transaction ID ABC123XYZ"},
                    headers={"X-Token": config.SMS_TOKEN})
    assert r.get_json()["result"] == "discarded"
    assert db.query("SELECT COUNT(*) AS n FROM payments")[0]["n"] == 0


def test_at09_late_payment_clears_alert():
    sid = matching.create_sale(500, now=T0)["sale_id"]
    matching.refresh_alerts(mins(11))
    assert matching.sale_state(sale_row(sid), mins(11)) == "alert"
    assert "no_payment" in alert_types(sid)
    res = matching.process_payment(500, "TX0009ABC", now=mins(12))
    assert res["result"] == "verified"
    assert matching.sale_state(sale_row(sid), mins(12)) == "verified"
    # Unresolved alert is cleared from active board
    assert alert_types(sid) == []
    # Audit evidence: record is preserved in database with resolved_at timestamp
    all_alerts = db.query("SELECT * FROM alerts WHERE sale_id=?", (sid,))
    assert len(all_alerts) > 0
    assert all_alerts[0]["resolved_at"] is not None


# ---- extra checks ----
def test_payment_before_sale_still_matches():
    matching.process_payment(400, "TX0010ABC", now=T0)
    result = matching.create_sale(400, now=mins(2))
    assert result["verified"]


def test_parse_message_cases():
    ok = matching.parse_message("Dear customer, you have received 1,250.50 ETB from Abebe via Telebirr. "
                                "Transaction ID: DAB1C2D3EF. Thank you.")
    assert ok["kind"] == "payment" and ok["amount"] == 1250.50
    assert ok["txn_id"] == "DAB1C2D3EF" and ok["provider"] == "telebirr"

    cbe1 = matching.parse_message("Dear Customer, Your A/C 1000123456 has been credited with ETB 500.00 on 20-Oct-2026. "
                                  "Ref. No: FT24294ABCD. Your current balance is ETB 12,500.00.")
    assert cbe1["kind"] == "payment" and cbe1["amount"] == 500.0
    assert cbe1["txn_id"] == "FT24294ABCD" and cbe1["provider"] == "cbe"

    cbe2 = matching.parse_message("Your Account 1000... Credited with Birr 750.25 by Mobile Banking. "
                                  "Ref No: FT98765ZYXW. Commercial Bank of Ethiopia.")
    assert cbe2["kind"] == "payment" and cbe2["amount"] == 750.25
    assert cbe2["txn_id"] == "FT98765ZYXW" and cbe2["provider"] == "cbe"

    amharic = matching.parse_message("ውድ ደንበኛ 300.00 ብር ከ 0911000000 ተቀብለዋል:: የግብይት ቁጥር: DA99887766")
    assert amharic["kind"] == "payment" and amharic["amount"] == 300.00
    assert amharic["txn_id"] == "DA99887766"

    # Simulated Telebirr transfer receipt (outgoing wording must be ignored)
    real_telebirr = (
        "Dear Almaz \n"
        "You have transferred ETB 80.00 to Chala Bekele (2519****0001) on 02/10/2026 07:55:30. "
        "Your transaction number is TB8899AACC. The service fee is ETB 0.87 and 15% VAT on the service fee is ETB 0.13. "
        "Your current E-Money Account balance is ETB 147.15. To download your payment information please click this link: "
        "https://transactioninfo.ethiotelecom.et/receipt/TB8899AACC.\n\n"
        "Thank you for using telebirr\nEthio telecom"
    )
    # Outgoing transfer messages must be IGNORED (cannot be used to verify retail sales)
    p_tb = matching.parse_message(real_telebirr)
    assert p_tb["kind"] == "ignored"

    # Outgoing CBE mobile banking transfer receipt must also be IGNORED
    real_cbe = (
        "Dear Customer, You have successfully transferred ETB 50.00 from account 1**0001 "
        "to account 1**0002. Your current balance is ETB 1,952.11. "
        "Ref No: FT8899AABB. Commercial Bank of Ethiopia."
    )
    p_cbe = matching.parse_message(real_cbe)
    assert p_cbe["kind"] == "ignored"

    # Sample CBE incoming payment received by seller
    real_cbe_recv = (
        "Dear Merchant Store You have received ETB 200.00 from account 1**0003 "
        "(Abebe Kebede) to your account 1**0001. Your current balance is ETB450.39. "
        "Thanks for Banking with CBE. https://mbreciept.cbe.com.et/v2-cbeMockTxnId200  "
        "for feedback: https://forms.gle/mockFeedbackUrl123"
    )
    p_cbe_recv = matching.parse_message(real_cbe_recv)
    assert p_cbe_recv["kind"] == "payment" and p_cbe_recv["amount"] == 200.00
    assert p_cbe_recv["txn_id"] == "v2-cbeMockTxnId200" and p_cbe_recv["provider"] == "cbe"

    # Sample Telebirr incoming payment received by seller
    real_tb_recv = (
        "Dear Merchant \n"
        "You have received ETB 1.00 from Almaz Tesfaye(2519****0004)  on 18/10/2026 10:02:41. "
        "Your transaction number is TB11223344. Your current E-Money Account balance is ETB 25.85.\n"
        "Thank you for using telebirr\nEthio telecom"
    )
    p_tb_recv = matching.parse_message(real_tb_recv)
    assert p_tb_recv["kind"] == "payment" and p_tb_recv["amount"] == 1.00
    assert p_tb_recv["txn_id"] == "TB11223344" and p_tb_recv["provider"] == "telebirr"

    assert matching.parse_message("You have sent 500 ETB. Transaction ID: AB12CD34")["kind"] == "ignored"
    assert matching.parse_message("Your OTP is 4821")["kind"] == "otp"
    assert matching.parse_message("የማረጋገጫ ኮድዎ 4821 ነው")["kind"] == "otp"


def test_input_validation():
    for bad in ("abc", "-5", "0", "99999999999"):
        with pytest.raises(ValueError):
            matching.validate_amount(bad)
    with pytest.raises(ValueError):
        matching.validate_txn_id("a b;DROP TABLE sales")


def test_sql_injection_text_is_harmless():
    with pytest.raises(ValueError):
        matching.process_payment(500, "x'; DROP TABLE sales;--")
    assert db.query("SELECT COUNT(*) AS n FROM sales")[0]["n"] == 0


def test_reports_totals_and_profit():
    now = datetime.now(timezone.utc)
    matching.create_sale(500, cost=300, now=now)
    matching.process_payment(500, "TX0011ABC", now=now)
    p = reports.summary(now)["periods"]
    assert p["today"]["count"] == 1 and p["today"]["total"] == 500
    assert p["month"]["profit"] == 200


def test_pages_load_and_csrf_enforced():
    c = app.test_client()
    # Unauthenticated client visiting protected route is redirected to /login
    for path in ("/", "/sales/new", "/inbox", "/reports", "/register"):
        assert c.get(path).status_code == 302
    assert c.get("/login").status_code == 200

    # Log in as test user
    with c.session_transaction() as s:
        s["user_id"] = 1
        s["role"] = "owner"
        s["is_owner"] = True
        s["csrf"] = "abc"

    # Authenticated owner can load cashier registration page
    assert c.get("/register").status_code == 200

    for path in ("/", "/sales/new", "/inbox", "/reports"):
        assert c.get(path).status_code == 200

    assert c.post("/sales/new", data={"amount": "500"}).status_code == 400   # no CSRF token
    r = c.post("/sales/new", data={"amount": "500", "csrf_token": "abc"})
    assert r.status_code == 302


def test_authentication_and_password_hashing():
    from backend import auth
    # Verify default users are seeded
    owner = auth.authenticate("owner", "owner123")
    assert owner is not None and owner["role"] == "owner"

    # Password must NEVER be stored in plain text
    row = db.query("SELECT password_hash FROM users WHERE username='owner'")[0]
    assert "owner123" not in row["password_hash"]
    assert "scrypt:" in row["password_hash"] or "pbkdf2:" in row["password_hash"]

    # Wrong password rejected
    assert auth.authenticate("owner", "wrongpassword") is None
    assert auth.authenticate("nonexistent", "owner123") is None

    # Register new cashier
    new_user = auth.create_user("teshome", "secret123", role="cashier")
    assert new_user["username"] == "teshome" and new_user["role"] == "cashier"
    assert auth.authenticate("teshome", "secret123") is not None


def test_sql_injection_on_login():
    from backend import auth
    # Attempt SQL injection in username
    bad_user = "' OR '1'='1' --"
    assert auth.authenticate(bad_user, "anything") is None
    with pytest.raises(ValueError):
        auth.create_user(bad_user, "password123")


def test_cancel_pending_sale():
    sid = matching.create_sale(350, now=T0)["sale_id"]
    assert sale_row(sid)["status"] == "pending"
    
    # Cancel the initial pending sale within 2 min
    matching.cancel_sale(sid, now=T0)
    assert sale_row(sid)["status"] == "cancelled"
    
    # Subsequent payment should NOT match a cancelled sale
    res = matching.process_payment(350, "TX_CANCELLED_01", now=mins(1))
    assert res["result"] == "unassigned"
    
    # Cannot cancel an already verified sale
    sid2 = matching.create_sale(100, now=T0)["sale_id"]
    matching.process_payment(100, "TX_VERIFIED_02", now=mins(1))
    with pytest.raises(ValueError, match="recorded in the ledger"):
        matching.cancel_sale(sid2)

    # Cashier cannot cancel warning (yellow, >2m) or alert (red, >10m) sales
    sid3 = matching.create_sale(200, now=T0)["sale_id"]
    with pytest.raises(ValueError, match="locked to preserve audit evidence"):
        matching.cancel_sale(sid3, now=mins(3), allow_staged=False)


def test_ephemeral_passcode_lifecycle():
    from backend import auth
    
    # 1. Generate passcode valid for 10 min from T0
    p = auth.generate_ephemeral_passcode(created_by=1, ttl_minutes=10, now=T0)
    assert len(p["token"]) == 6
    assert p["token"].isdigit()
    
    # 2. Check active passcode
    active = auth.get_active_passcode(now=mins(2))
    assert active is not None
    assert active["token"] == p["token"]
    assert active["remaining_seconds"] == 8 * 60

    # 3. Test invalid passcode format & non-existent passcode
    assert not auth.verify_and_consume_passcode("123", now=mins(2))["ok"]
    assert not auth.verify_and_consume_passcode("999999", now=mins(2))["ok"]

    # 4. Expired passcode is rejected after 10 minutes
    p_exp = auth.generate_ephemeral_passcode(created_by=1, ttl_minutes=10, now=T0)
    assert not auth.verify_and_consume_passcode(p_exp["token"], now=mins(11))["ok"]

    # 5. Valid passcode verifies and consumes successfully
    p_valid = auth.generate_ephemeral_passcode(created_by=1, ttl_minutes=10, now=T0)
    res = auth.verify_and_consume_passcode(p_valid["token"], now=mins(3))
    assert res["ok"]
    assert res["token"] == p_valid["token"]

    # 6. Replay protection: cannot be used twice
    replay = auth.verify_and_consume_passcode(p_valid["token"], now=mins(4))
    assert not replay["ok"]

    # 7. Revoke active passcode
    p_rev = auth.generate_ephemeral_passcode(created_by=1, ttl_minutes=10, now=T0)
    auth.revoke_all_passcodes()
    assert auth.get_active_passcode(now=mins(1)) is None
    assert not auth.verify_and_consume_passcode(p_rev["token"], now=mins(1))["ok"]


def test_cashier_accounting_session_flow():
    from backend import auth
    client = app.test_client()

    # Step 1: Sign in as cashier
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    
    login_res = client.post("/login", data={
        "csrf_token": "csrf123",
        "username": "cashier",
        "password": "cashier123"
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # Step 2: Cashier navigates to /reports -> locked view displayed
    rep_res = client.get("/reports")
    assert rep_res.status_code == 200
    assert b"Shift Accounting Locked" in rep_res.data
    assert b"Owner Mode" not in rep_res.data

    # Step 3: Cashier cannot generate passcodes (Owner only)
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    gen_res = client.post("/owner/generate-passcode", data={"csrf_token": "csrf123"})
    assert gen_res.status_code == 403

    # Step 4: Owner generates ephemeral passcode
    p = auth.generate_ephemeral_passcode(created_by=1, ttl_minutes=10)

    # Step 5: Cashier enters valid passcode
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    verify_res = client.post("/cashier/verify-passcode", data={
        "csrf_token": "csrf123",
        "passcode": p["token"]
    }, follow_redirects=True)
    assert verify_res.status_code == 200
    assert b"Temporary Cashier Accounting Session" in verify_res.data
    assert b"Daily Verified Sales Breakdown" in verify_res.data

    # Step 6: Cashier locks session
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    lock_res = client.post("/cashier/lock-accounting", data={"csrf_token": "csrf123"}, follow_redirects=True)
    assert lock_res.status_code == 200
    assert b"Shift Accounting Locked" in lock_res.data


# ---------------------------------------------------------------------------
# Security Hardening Regression Tests
# ---------------------------------------------------------------------------

def test_public_registration_cannot_create_owner():
    """Item 1: Public visitors cannot register an owner account."""
    client = app.test_client()

    # Visitor tries to register an owner account directly
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    r = client.post("/register", data={
        "csrf_token": "csrf123",
        "username": "fake_owner",
        "password": "password123",
        "confirm_password": "password123",
        "role": "owner"
    }, follow_redirects=True)
    # Registration is blocked because users already exist and visitor is not logged in as owner
    assert b"Public registration is disabled" in r.data
    assert auth.authenticate("fake_owner", "password123") is None

    # Now log in as the legitimate owner and create a staff account
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    client.post("/login", data={"csrf_token": "csrf123", "username": "owner", "password": "owner123"}, follow_redirects=True)

    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    r_owner = client.post("/register", data={
        "csrf_token": "csrf123",
        "username": "new_staff",
        "password": "password123",
        "confirm_password": "password123",
        "role": "owner"  # Maliciously submitted role
    }, follow_redirects=True)
    assert r_owner.status_code == 200
    # Server enforces role='cashier' regardless of form submission
    created = auth.authenticate("new_staff", "password123")
    assert created is not None
    assert created["role"] == "cashier"


def test_simulator_restricted_to_owner_and_flag():
    """Item 2: /inbox/simulate is owner-only and respects ENABLE_SIMULATOR flag."""
    client = app.test_client()

    # Cashier cannot access simulator
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    client.post("/login", data={"csrf_token": "csrf123", "username": "cashier", "password": "cashier123"})

    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    cashier_sim = client.post("/inbox/simulate", data={"csrf_token": "csrf123", "amount": "100", "txn_id": "FAKE_TX01"})
    assert cashier_sim.status_code == 403

    # Sign in as owner
    client.post("/logout", data={"csrf_token": "csrf123"})
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    client.post("/login", data={"csrf_token": "csrf123", "username": "owner", "password": "owner123"})

    # When ENABLE_SIMULATOR=False, even owner is blocked
    config.ENABLE_SIMULATOR = False
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    owner_blocked = client.post("/inbox/simulate", data={"csrf_token": "csrf123", "amount": "100", "txn_id": "FAKE_TX02"})
    assert owner_blocked.status_code == 403

    # When ENABLE_SIMULATOR=True, owner succeeds
    config.ENABLE_SIMULATOR = True
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    owner_ok = client.post("/inbox/simulate", data={"csrf_token": "csrf123", "amount": "100", "txn_id": "FAKE_TX03"}, follow_redirects=True)
    assert owner_ok.status_code == 200


def test_ledger_detects_tampered_sales_table():
    """Item 3: verify_chain() detects direct manipulation of sales table amounts."""
    sid = matching.create_sale(500, now=T0)["sale_id"]
    matching.process_payment(500, "TX_LEDGER_CHK_01", "telebirr", now=mins(1))
    assert ledger.verify_chain()["ok"]

    # Attacker enters SQLite and tampers with sale amount directly
    with db.connect() as conn:
        conn.execute("UPDATE sales SET amount = 9999 WHERE id = ?", (sid,))

    res = ledger.verify_chain()
    assert res["ok"] is False
    assert res["broken_at"] is not None
    assert "amount" in res["reason"]


def test_ledger_detects_injected_verified_sale():
    """Item 3: verify_chain() detects verified sale rows that bypass the ledger."""
    sid = matching.create_sale(500, now=T0)["sale_id"]
    matching.process_payment(500, "TX_LEDGER_CHK_02", "telebirr", now=mins(1))
    assert ledger.verify_chain()["ok"]

    # Attacker injects a verified sale row directly without a ledger entry
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO sales (amount, status, created_at) VALUES (888, 'verified', ?)",
            (timeutil.iso(mins(2)),),
        )

    res = ledger.verify_chain()
    assert res["ok"] is False
    assert "no matching entry in ledger" in res["reason"]


def test_refuse_start_with_default_secrets_in_production():
    """Item 4: Refuse to start if default, short, or placeholder secrets are used when DEMO_MODE=0."""
    saved_demo = config.DEMO_MODE
    saved_key = config.SECRET_KEY
    saved_token = config.SMS_TOKEN
    try:
        config.DEMO_MODE = False

        # 1. Reject 'change-me'
        config.SECRET_KEY = "change-me"
        config.SMS_TOKEN = "a" * 32
        with pytest.raises(RuntimeError, match="Refusing to start with default"):
            config.validate_secrets()

        # 2. Reject short secrets (< 32 chars)
        config.SECRET_KEY = "too-short-secret"
        with pytest.raises(RuntimeError, match="too short"):
            config.validate_secrets()

        # 3. Reject placeholder starting with 'generate-a'
        config.SECRET_KEY = "generate-a-strong-random-key-here-placeholder"
        with pytest.raises(RuntimeError, match="placeholder text"):
            config.validate_secrets()

        # 4. Accept strong 32+ character secrets
        config.SECRET_KEY = "12345678901234567890123456789012"
        config.SMS_TOKEN = "abcdefabcdefabcdefabcdefabcdefab"
        config.validate_secrets()  # Should not raise
    finally:
        config.DEMO_MODE = saved_demo
        config.SECRET_KEY = saved_key
        config.SMS_TOKEN = saved_token


def test_rate_limit_lockout_on_login():
    """Item 5: 5 failed login attempts trigger a 5-minute lockout."""
    from backend import rate_limit
    rate_limit.limiter.clear_all()
    client = app.test_client()

    for i in range(5):
        with client.session_transaction() as sess:
            sess["csrf"] = "csrf123"
        r = client.post("/login", data={"csrf_token": "csrf123", "username": "owner", "password": "wrongpassword"})
        if i < 4:
            assert r.status_code == 302
        else:
            assert r.status_code == 429

    # 6th attempt is blocked immediately with 429
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    blocked = client.post("/login", data={"csrf_token": "csrf123", "username": "owner", "password": "wrongpassword"})
    assert blocked.status_code == 429
    assert b"Locked out" in blocked.data


def test_rate_limit_lockout_on_passcode():
    """Item 5: 5 failed passcode attempts trigger lockout."""
    from backend import rate_limit
    rate_limit.limiter.clear_all()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    client.post("/login", data={"csrf_token": "csrf123", "username": "cashier", "password": "cashier123"})

    for i in range(5):
        with client.session_transaction() as sess:
            sess["csrf"] = "csrf123"
        r = client.post("/cashier/verify-passcode", data={"csrf_token": "csrf123", "passcode": "000000"})
        if i < 4:
            assert r.status_code == 302
        else:
            assert r.status_code == 429

    # 6th attempt is blocked with 429
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    blocked = client.post("/cashier/verify-passcode", data={"csrf_token": "csrf123", "passcode": "000000"})
    assert blocked.status_code == 429


def test_login_open_redirect_prevented():
    """Item 7: External open redirects via next parameter are sanitized."""
    from backend import rate_limit
    rate_limit.limiter.clear_all()
    client = app.test_client()

    # Attempt external URLs
    for evil_url in ("https://evil.example.com", "//evil.example.com", "\\\\evil.example.com"):
        with client.session_transaction() as sess:
            sess["csrf"] = "csrf123"
        r = client.post(f"/login?next={evil_url}", data={
            "csrf_token": "csrf123",
            "username": "cashier",
            "password": "cashier123"
        })
        assert r.status_code == 302
        # Redirected safely to local dashboard, NOT to evil site
        assert r.headers["Location"].endswith("/dashboard") or r.headers["Location"] == "/dashboard"

    # Valid internal relative URL is permitted for unauthenticated login
    client_valid = app.test_client()
    with client_valid.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    r_valid = client_valid.post("/login?next=/reports", data={
        "csrf_token": "csrf123",
        "username": "owner",
        "password": "owner123"
    })
    assert r_valid.headers["Location"].endswith("/reports") or r_valid.headers["Location"] == "/reports"


def test_parser_ignores_outgoing_transfers_and_parses_balance_before_amount():
    """Item 9: Outgoing transfer messages are ignored, and amounts following 'balance' are excluded."""
    # Outgoing transfer message
    out_msg = "You have transferred ETB 1,200.00 to Merchant Kelemu. Transaction ID: DJ999888."
    assert matching.parse_message(out_msg)["kind"] == "ignored"

    # Message mentioning balance before the actual payment amount
    bal_msg = (
        "Dear Customer, Your current balance is ETB 15,000.00. "
        "You have received ETB 250.00 from Abebe Bikila via Telebirr. "
        "Transaction number is DJI882910."
    )
    p = matching.parse_message(bal_msg)
    assert p["kind"] == "payment"
    assert p["amount"] == 250.00  # Must be 250.00, NOT 15,000.00
    assert p["txn_id"] == "DJI882910"


def test_cashier_cannot_see_today_totals_on_live_or_dashboard():
    """Item 11: /api/live and dashboard do not expose financials to cashiers."""
    from backend import rate_limit
    rate_limit.limiter.clear_all()
    client = app.test_client()

    # Create and verify a sale
    sid = matching.create_sale(300, now=T0)["sale_id"]
    matching.process_payment(300, "TX_CASHIER_PRIV_01", "telebirr", now=mins(1))

    # Log in as cashier
    with client.session_transaction() as sess:
        sess["csrf"] = "csrf123"
    client.post("/login", data={"csrf_token": "csrf123", "username": "cashier", "password": "cashier123"})

    # Live API check
    live_res = client.get("/api/live")
    live_data = live_res.get_json()
    assert live_data["today_total"] is None
    assert live_data["today_count"] is None
    assert live_data["can_view_totals"] is False

    # Dashboard check
    dash_res = client.get("/dashboard")
    assert b"Owner Restricted" in dash_res.data
    assert b"300.00" not in dash_res.data or b"stat_today_total" not in dash_res.data
