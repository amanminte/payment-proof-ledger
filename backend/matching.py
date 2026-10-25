"""Sales, SMS parsing and matching (FR-01 to FR-05, BRU-01 to BRU-03).

IMPORTANT: the regex patterns below are generic guesses. Copy 5-10 REAL
Telebirr / CBE "money received" messages (with names and numbers blanked)
into the tests and adjust the patterns until they all parse.
"""
import re
from datetime import timedelta

from . import config, db, ledger
from .timeutil import iso, now_utc, parse

# ---------- parsing ----------
OTP_RE = re.compile(r"\b(otp|one[- ]?time|verification code|passcode|pin)\b|የማረጋገጫ\s*ኮድ", re.I)
RECEIVED_RE = re.compile(r"\b(received|credited|deposit(?:ed)?)\b|ተቀብለዋል|ገቢ", re.I)
AMOUNT_RE = re.compile(
    r"(?:ETB|Birr|ብር)\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:ETB|Birr|ብር)", re.I)
TXN_RE = re.compile(
    r"\b(?:transaction\s*(?:id|number|no\.?)|txn\s*id|ref\.?(?:erence)?(?:\s*(?:no\.?|number|id))?|id|የግብይት\s*ቁጥር)"
    r"\s*(?:is|:|-)?\s*([A-Za-z0-9_-]{6,35})\b", re.I)
URL_TXN_RE = re.compile(r"(?:cbe\.com\.et|ethiotelecom\.et/receipt)/([A-Za-z0-9_-]{6,35})", re.I)
TXN_VALID = re.compile(r"^[A-Za-z0-9_-]{5,35}$")


def extract_payment_amount(text):
    """Find the transaction amount, ignoring account balances."""
    matches = list(AMOUNT_RE.finditer(text))
    if not matches:
        return None
    for m in matches:
        start = m.start()
        pre_text = text[max(0, start - 35):start].lower()
        if re.search(r"\b(balance|bal|current\s*bal(?:ance)?|ሒሳብ)\b", pre_text):
            continue
        post_text = text[m.end():min(len(text), m.end() + 25)].lower()
        if re.search(r"^\s*(?:is\s*)?balance\b", post_text):
            continue
        val_str = (m.group(1) or m.group(2)).replace(",", "")
        try:
            return float(val_str)
        except ValueError:
            continue
    return None


def parse_message(text):
    """Return {'kind': 'otp' | 'ignored' | 'unparsed' | 'payment', ...}."""
    text = (text or "")[:1000]
    if OTP_RE.search(text):
        return {"kind": "otp"}                      # BRU-03: never stored
    if not RECEIVED_RE.search(text):
        return {"kind": "ignored"}                  # e.g. "you sent 500 ETB" or outgoing "you transferred"
    amount = extract_payment_amount(text)
    txn_m = TXN_RE.search(text) or URL_TXN_RE.search(text)
    if amount is None or not txn_m:
        return {"kind": "unparsed"}
    low = text.lower()
    provider = "telebirr" if "telebirr" in low else "cbe" if (
        "cbe" in low or "commercial bank" in low or "a/c" in low or txn_m.group(1).upper().startswith("FT")
    ) else None
    return {"kind": "payment", "amount": amount, "txn_id": txn_m.group(1), "provider": provider}


# ---------- validation ----------
def validate_amount(value):
    try:
        amount = round(float(str(value).replace(",", "")), 2)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if not 0 < amount <= config.MAX_AMOUNT:
        raise ValueError(f"Amount must be between 0 and {config.MAX_AMOUNT}.")
    return amount


def validate_txn_id(value):
    value = (value or "").strip()
    if not TXN_VALID.match(value):
        raise ValueError("Transaction ID must be 5-35 characters (letters, digits, '-' or '_').")
    return value


# ---------- sale state ----------
def age_minutes(sale, now):
    return (now - parse(sale["created_at"])).total_seconds() / 60


def sale_state(sale, now):
    """verified | pending | waiting (yellow) | alert (red)."""
    if sale["status"] == "verified":
        return "verified"
    age = age_minutes(sale, now)
    if age >= config.RED_AFTER_MIN:
        return "alert"
    if age >= config.YELLOW_AFTER_MIN:
        return "waiting"
    return "pending"


def refresh_alerts(now=None):
    """Log a 'waiting' / 'no_payment' alert once per unverified sale (FR-04)."""
    now = now or now_utc()
    with db.connect() as conn:
        for s in conn.execute("SELECT * FROM sales WHERE status = 'pending'").fetchall():
            for kind, limit in (("waiting", config.YELLOW_AFTER_MIN), ("no_payment", config.RED_AFTER_MIN)):
                if age_minutes(s, now) >= limit:
                    conn.execute(
                        "INSERT INTO alerts(sale_id, type, created_at) "
                        "SELECT ?, ?, ? WHERE NOT EXISTS "
                        "(SELECT 1 FROM alerts WHERE sale_id = ? AND type = ? AND resolved_at IS NULL)",
                        (s["id"], kind, iso(now), s["id"], kind))


# ---------- core logic ----------
def _verify(conn, sale_id, amount, payment_id, now):
    conn.execute("UPDATE sales SET status='verified', verified_at=?, payment_id=? WHERE id=?",
                 (iso(now), payment_id, sale_id))
    conn.execute("UPDATE alerts SET resolved_at=? WHERE sale_id=? AND resolved_at IS NULL AND type IN ('waiting', 'no_payment')",
                 (iso(now), sale_id))
    ledger.add_entry(conn, sale_id, amount, now)         # FR-06, FR-08


def cancel_sale(sale_id, now=None, allow_staged=False):
    """Cancel an initial pending sale before warning or alert stages.

    Once a sale enters waiting (yellow, 2m) or alert (red, 10m), cashiers
    cannot delete it to ensure potential scams are preserved in audit records.
    """
    now = now or now_utc()
    with db.connect() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if not sale:
            raise ValueError("Sale not found.")
        if sale["status"] == "verified":
            raise ValueError("Cannot cancel a verified sale that is recorded in the ledger.")
        if sale["status"] != "pending":
            raise ValueError("Sale is already closed or cancelled.")
        if not allow_staged and age_minutes(sale, now) >= config.YELLOW_AFTER_MIN:
            raise ValueError("Cannot cancel: warning and alert sales are locked to preserve audit evidence.")
        conn.execute("UPDATE sales SET status='cancelled' WHERE id=?", (sale_id,))
        conn.execute("UPDATE alerts SET resolved_at=? WHERE sale_id=? AND resolved_at IS NULL AND type IN ('waiting', 'no_payment')",
                     (iso(now), sale_id))
        return dict(sale)


def create_sale(amount, cost=None, now=None):
    """Open a sale (FR-02). If a matching payment already arrived, verify at once."""
    now = now or now_utc()
    amount = validate_amount(amount)
    cost = validate_amount(cost) if cost not in (None, "") else None
    with db.connect() as conn:
        sale_id = conn.execute(
            "INSERT INTO sales(amount, cost, status, created_at) VALUES (?,?, 'pending', ?)",
            (amount, cost, iso(now))).lastrowid
        earliest = iso(now - timedelta(minutes=config.UNASSIGNED_WINDOW_MIN))
        pay = conn.execute(
            "SELECT id FROM payments WHERE matched_sale_id IS NULL AND ABS(amount-?)<0.005 "
            "AND received_at >= ? ORDER BY received_at LIMIT 1", (amount, earliest)).fetchone()
        if pay:
            conn.execute("UPDATE payments SET matched_sale_id=? WHERE id=?", (sale_id, pay["id"]))
            _verify(conn, sale_id, amount, pay["id"], now)
            return {"sale_id": sale_id, "verified": True}
    return {"sale_id": sale_id, "verified": False}


def process_payment(amount, txn_id, provider=None, received_at=None, now=None):
    """Handle one incoming payment (FR-03, FR-05, BRU-02).

    Returns {'result': 'verified' | 'duplicate' | 'mismatch' | 'unassigned', ...}.
    A late payment still matches an open sale and clears its alert (FR-04).
    """
    now = now or now_utc()
    received_at = received_at or now
    amount = validate_amount(amount)
    txn_id = validate_txn_id(txn_id)
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM payments WHERE txn_id=?", (txn_id,)).fetchone():
            conn.execute("INSERT INTO alerts(sale_id, type, created_at) VALUES (NULL,'duplicate_txn',?)",
                         (iso(now),))
            return {"result": "duplicate"}
        sale = conn.execute(
            "SELECT * FROM sales WHERE status = 'pending' AND ABS(amount-?)<0.005 "
            "ORDER BY created_at LIMIT 1", (amount,)).fetchone()
        pid = conn.execute(
            "INSERT INTO payments(provider, amount, txn_id, received_at, matched_sale_id) VALUES (?,?,?,?,?)",
            (provider, amount, txn_id, iso(received_at), sale["id"] if sale else None)).lastrowid
        if sale:
            _verify(conn, sale["id"], sale["amount"], pid, now)
            return {"result": "verified", "sale_id": sale["id"]}
        newest_open = conn.execute(
            "SELECT id FROM sales WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1").fetchone()
        if newest_open:
            conn.execute("INSERT INTO alerts(sale_id, type, created_at) VALUES (?,'wrong_amount',?)",
                         (newest_open["id"], iso(now)))
            return {"result": "mismatch", "sale_id": newest_open["id"]}
        return {"result": "unassigned"}


def process_message(text, now=None):
    """Raw SMS text -> parse -> process (shared by the real and simulated paths)."""
    parsed = parse_message(text)
    if parsed["kind"] != "payment":
        return {"result": "discarded", "reason": parsed["kind"]}
    return process_payment(parsed["amount"], parsed["txn_id"], parsed["provider"], now=now)
