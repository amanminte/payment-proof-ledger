"""Tamper-evident ledger using a hash chain (FR-08).

Each entry stores the hash of the previous entry, so editing an old record
breaks the chain. Limit: someone with full database access could recompute
the whole chain, so the latest hash is shown on the reports page for the
owner to compare with a saved copy.
"""
import hashlib

from . import db
from .timeutil import iso

GENESIS = "0" * 64


def compute_hash(prev_hash, sale_id, amount, created_at):
    data = f"{prev_hash}|{sale_id}|{float(amount):.2f}|{created_at}".encode()
    return hashlib.sha256(data).hexdigest()


def add_entry(conn, sale_id, amount, created_at):
    row = conn.execute("SELECT hash FROM ledger ORDER BY id DESC LIMIT 1").fetchone()
    prev = row["hash"] if row else GENESIS
    created = iso(created_at)
    h = compute_hash(prev, sale_id, amount, created)
    conn.execute(
        "INSERT INTO ledger(sale_id, amount, created_at, prev_hash, hash) VALUES (?,?,?,?,?)",
        (sale_id, amount, created, prev, h),
    )
    return h


def verify_chain():
    """Re-compute the chain and verify cross-table consistency with sales table.

    Returns {ok, broken_at, entries, latest_hash, reason}.
    Checks:
    1. Cryptographic SHA-256 link integrity of all ledger entries.
    2. Each ledger entry must point to an existing verified sale with the exact matching amount.
    3. No two ledger entries may reference the same sale.
    4. Every sale marked 'verified' must have exactly one ledger entry with matching amount.
    """
    rows = db.query("SELECT * FROM ledger ORDER BY id")
    prev = GENESIS
    seen_sale_ids = set()

    for r in rows:
        expected = compute_hash(r["prev_hash"], r["sale_id"], r["amount"], r["created_at"])
        if r["prev_hash"] != prev or r["hash"] != expected:
            return {
                "ok": False,
                "broken_at": r["id"],
                "reason": f"Cryptographic hash chain break at ledger entry #{r['id']}",
                "entries": len(rows),
                "latest_hash": rows[-1]["hash"] if rows else None,
            }

        sales = db.query("SELECT * FROM sales WHERE id = ?", (r["sale_id"],))
        if not sales:
            return {
                "ok": False,
                "broken_at": r["id"],
                "reason": f"Ledger entry #{r['id']} points to nonexistent sale #{r['sale_id']}",
                "entries": len(rows),
                "latest_hash": rows[-1]["hash"] if rows else None,
            }
        sale = sales[0]
        if sale["status"] != "verified":
            return {
                "ok": False,
                "broken_at": r["id"],
                "reason": f"Ledger entry #{r['id']} points to unverified sale #{r['sale_id']} (status: {sale['status']})",
                "entries": len(rows),
                "latest_hash": rows[-1]["hash"] if rows else None,
            }
        if abs(float(sale["amount"]) - float(r["amount"])) > 0.001:
            return {
                "ok": False,
                "broken_at": r["id"],
                "reason": f"Ledger entry #{r['id']} amount ({r['amount']}) does not match sale #{r['sale_id']} amount ({sale['amount']})",
                "entries": len(rows),
                "latest_hash": rows[-1]["hash"] if rows else None,
            }
        if r["sale_id"] in seen_sale_ids:
            return {
                "ok": False,
                "broken_at": r["id"],
                "reason": f"Duplicate ledger entry for sale #{r['sale_id']}",
                "entries": len(rows),
                "latest_hash": rows[-1]["hash"] if rows else None,
            }
        seen_sale_ids.add(r["sale_id"])
        prev = r["hash"]

    # Verify that every verified sale in the database has a matching ledger entry
    verified_sales = db.query("SELECT * FROM sales WHERE status = 'verified' ORDER BY id")
    for vs in verified_sales:
        if vs["id"] not in seen_sale_ids:
            return {
                "ok": False,
                "broken_at": vs["id"],
                "reason": f"Verified sale #{vs['id']} has no matching entry in ledger",
                "entries": len(rows),
                "latest_hash": prev if rows else None,
            }

    return {
        "ok": True,
        "broken_at": None,
        "entries": len(rows),
        "latest_hash": prev if rows else None,
    }
