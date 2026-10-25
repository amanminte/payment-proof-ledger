import hmac
import os
import secrets
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

from . import auth, config, db, ledger, matching, rate_limit, reports
from .timeutil import iso, now_utc, parse, start_of_local_day

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
_ready = set()


@app.before_request
def _ensure_db():
    config.validate_secrets()
    if config.DATABASE not in _ready:
        db.init_db()
        _ready.add(config.DATABASE)


def _csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.context_processor
def inject_globals():
    user = auth.get_user_by_id(session.get("user_id"))
    is_owner = bool(user and user["role"] == "owner" and session.get("is_owner", True))

    # Ephemeral cashier accounting authorization check (FR-10)
    cashier_accounting_remaining = 0
    cashier_accounting_active = False
    cashier_until = session.get("cashier_accounting_until")
    if cashier_until:
        try:
            exp = parse(cashier_until)
            rem = int((exp - now_utc()).total_seconds())
            if rem > 0:
                cashier_accounting_remaining = rem
                cashier_accounting_active = True
            else:
                session.pop("cashier_accounting_until", None)
        except Exception:
            session.pop("cashier_accounting_until", None)

    return {
        "csrf_token": _csrf,
        "current_user": user,
        "is_owner": is_owner,
        "cashier_accounting_active": cashier_accounting_active,
        "cashier_accounting_remaining": cashier_accounting_remaining,
        "enable_simulator": config.ENABLE_SIMULATOR,
    }


def _check_csrf():
    if not hmac.compare_digest(request.form.get("csrf_token", ""), session.get("csrf", "x")):
        abort(400)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    client_ip = request.remote_addr or "127.0.0.1"
    limiter_key = f"login:{client_ip}"

    # Check brute-force lockout
    is_locked, rem = rate_limit.limiter.check_lockout(limiter_key)
    if is_locked:
        flash(f"Too many failed login attempts. Locked out for {rem} seconds.", "error")
        return render_template("login.html"), 429

    if request.method == "POST":
        _check_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = auth.authenticate(username, password)
        if not user:
            is_now_locked, lock_rem, attempts = rate_limit.limiter.record_failure(limiter_key)
            if is_now_locked:
                flash(f"Too many failed login attempts. Locked out for {lock_rem} seconds.", "error")
                return render_template("login.html"), 429
            flash(f"Invalid username or password. (Attempt {attempts} of {rate_limit.MAX_ATTEMPTS})", "error")
            return redirect(url_for("login_page"))

        # Success - reset rate limit
        rate_limit.limiter.reset(limiter_key)
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["username"] = user["username"]
        if user["role"] == "owner":
            session["is_owner"] = True
        flash(f"Welcome back, {user['username']} ({user['role'].capitalize()})!", "success")

        # Sanitize next redirect to prevent Open Redirect
        next_url = request.args.get("next")
        if not next_url or not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url:
            next_url = url_for("dashboard")
        return redirect(next_url)
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    user_count = auth.count_users()
    is_initial_setup = (user_count == 0)

    # Public registration is disabled; only logged-in owners can create staff accounts
    if not is_initial_setup:
        user = auth.get_user_by_id(session.get("user_id"))
        if not user or user["role"] != "owner" or not session.get("is_owner", True):
            flash("Public registration is disabled. Cashier accounts must be created by the Shop Owner.", "error")
            return redirect(url_for("dashboard") if session.get("user_id") else url_for("login_page"))

    if request.method == "POST":
        _check_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Role is strictly determined by system logic, never by visitor input
        role = "owner" if is_initial_setup else "cashier"

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register_page"))
        try:
            new_user = auth.create_user(username, password, role)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("register_page"))

        if is_initial_setup:
            session["user_id"] = new_user["id"]
            session["role"] = new_user["role"]
            session["username"] = new_user["username"]
            session["is_owner"] = True
            flash("Initial Store Owner account configured! Signed in.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(f"Cashier account '@{new_user['username']}' created successfully.", "success")
            return redirect(url_for("dashboard"))

    return render_template("register.html", is_initial_setup=is_initial_setup)


@app.route("/logout", methods=["POST"])
def logout():
    _check_csrf()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login_page"))


@app.route("/owner/toggle-mode", methods=["POST"])
@app.route("/owner/unlock", methods=["POST"])
@app.route("/owner/lock", methods=["POST"])
@login_required
def toggle_owner_mode():
    _check_csrf()
    user = auth.get_user_by_id(session.get("user_id"))
    if not user or user["role"] != "owner":
        flash("Only the shop owner can switch to Owner Mode.", "error")
        return redirect(request.referrer or url_for("dashboard"))
    current_state = session.get("is_owner", True)
    session["is_owner"] = not current_state
    if session["is_owner"]:
        flash("Switched to Owner Mode (Full Privileges).", "success")
    else:
        flash("Switched to Cashier View (Preview Mode).", "info")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/owner/generate-passcode", methods=["POST"])
@login_required
def generate_passcode():
    _check_csrf()
    user = auth.get_user_by_id(session.get("user_id"))
    if not user or user["role"] != "owner":
        abort(403)
    token_info = auth.generate_ephemeral_passcode(
        created_by=user["id"],
        ttl_minutes=config.ACCOUNTING_PASSCODE_TTL_MIN,
    )
    flash(
        f"Ephemeral Passcode Generated: {token_info['token']} (Valid for {token_info['ttl_minutes']} minutes). Provide this to the cashier.",
        "success",
    )
    return redirect(url_for("reports_page"))


@app.route("/owner/revoke-passcode", methods=["POST"])
@login_required
def revoke_passcode():
    _check_csrf()
    user = auth.get_user_by_id(session.get("user_id"))
    if not user or user["role"] != "owner":
        abort(403)
    auth.revoke_all_passcodes(created_by=user["id"])
    flash("Active cashier accounting passcode has been revoked.", "info")
    return redirect(url_for("reports_page"))


@app.route("/cashier/verify-passcode", methods=["POST"])
@login_required
def verify_passcode():
    _check_csrf()
    client_ip = request.remote_addr or "127.0.0.1"
    limiter_key = f"passcode:{client_ip}:{session.get('user_id', 'anon')}"

    is_locked, rem = rate_limit.limiter.check_lockout(limiter_key)
    if is_locked:
        flash(f"Too many failed passcode attempts. Locked out for {rem} seconds.", "error")
        return redirect(url_for("reports_page")), 429

    passcode = request.form.get("passcode", "")
    result = auth.verify_and_consume_passcode(passcode)
    if result["ok"]:
        rate_limit.limiter.reset(limiter_key)
        session["cashier_accounting_until"] = result["expires_at"]
        flash("10-Minute Accounting Session Unlocked! Access will auto-expire in 10 minutes.", "success")
    else:
        is_now_locked, lock_rem, attempts = rate_limit.limiter.record_failure(limiter_key)
        if is_now_locked:
            flash(f"Too many failed passcode attempts. Locked out for {lock_rem} seconds.", "error")
            return redirect(url_for("reports_page")), 429
        flash(f"{result['error']} (Attempt {attempts} of {rate_limit.MAX_ATTEMPTS})", "error")
    return redirect(url_for("reports_page"))


@app.route("/cashier/lock-accounting", methods=["POST"])
@login_required
def lock_cashier_accounting():
    _check_csrf()
    session.pop("cashier_accounting_until", None)
    flash("Cashier accounting session closed and re-locked.", "info")
    return redirect(url_for("reports_page"))


@app.route("/api/live")
@login_required
def live_status():
    now = now_utc()
    matching.refresh_alerts(now)
    open_sales = []
    for s in db.query("SELECT * FROM sales WHERE status = 'pending' ORDER BY created_at DESC"):
        open_sales.append({
            "id": s["id"],
            "amount": float(s["amount"]),
            "state": matching.sale_state(s, now),
            "age": int(matching.age_minutes(s, now)),
            "created_at": s["created_at"],
        })
    day_start = iso(start_of_local_day(now))
    flagged = db.query(
        "SELECT COUNT(*) AS n FROM alerts WHERE type != 'waiting' AND resolved_at IS NULL AND created_at >= ?",
        (day_start,),
    )[0]["n"]

    user = auth.get_user_by_id(session.get("user_id"))
    is_owner = bool(user and user["role"] == "owner" and session.get("is_owner", True))
    cashier_active = False
    cashier_until = session.get("cashier_accounting_until")
    if cashier_until:
        try:
            if parse(cashier_until) > now:
                cashier_active = True
        except Exception:
            pass

    can_view_totals = is_owner or cashier_active
    today_summary = reports.summary(now)["periods"]["today"] if can_view_totals else None
    chain = ledger.verify_chain()

    return jsonify({
        "open_sales": open_sales,
        "flagged": flagged,
        "today_total": today_summary["total"] if today_summary else None,
        "today_count": today_summary["count"] if today_summary else None,
        "can_view_totals": can_view_totals,
        "chain_ok": chain["ok"],
        "latest_hash": chain.get("latest_hash"),
    })


@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    now = now_utc()
    matching.refresh_alerts(now)
    open_sales = []
    for s in db.query("SELECT * FROM sales WHERE status = 'pending' ORDER BY created_at DESC"):
        open_sales.append(dict(s, state=matching.sale_state(s, now),
                               age=int(matching.age_minutes(s, now))))
    day_start = iso(start_of_local_day(now))
    flagged = db.query(
        "SELECT COUNT(*) AS n FROM alerts WHERE type != 'waiting' AND resolved_at IS NULL AND created_at >= ?",
        (day_start,),
    )[0]["n"]

    user = auth.get_user_by_id(session.get("user_id"))
    is_owner = bool(user and user["role"] == "owner" and session.get("is_owner", True))
    cashier_active = False
    cashier_until = session.get("cashier_accounting_until")
    if cashier_until:
        try:
            if parse(cashier_until) > now:
                cashier_active = True
        except Exception:
            pass

    can_view_totals = is_owner or cashier_active
    today_data = reports.summary(now)["periods"]["today"] if can_view_totals else None

    return render_template(
        "dashboard.html",
        open_sales=open_sales,
        flagged=flagged,
        today=today_data,
        can_view_totals=can_view_totals,
        chain=ledger.verify_chain(),
    )


@app.route("/sales/<int:sale_id>/cancel", methods=["POST"])
@login_required
def cancel_sale(sale_id):
    _check_csrf()
    is_owner = session.get("is_owner", False)
    try:
        sale = matching.cancel_sale(sale_id, allow_staged=is_owner)
        flash(f"Sale #{sale_id} ({sale['amount']:.2f} ETB) was cancelled.", "info")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("dashboard"))


@app.route("/sales/new", methods=["GET", "POST"])
@login_required
def create_sale():
    if request.method == "POST":
        _check_csrf()
        try:
            result = matching.create_sale(request.form.get("amount"), request.form.get("cost"))
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("create_sale"))
        flash("Sale verified: the payment had already arrived." if result["verified"]
              else "Sale opened. Waiting for the payment. Do NOT release the goods yet.",
              "success" if result["verified"] else "warning")
        return redirect(url_for("dashboard"))
    return render_template("create_sale.html")


@app.route("/inbox")
@login_required
def inbox():
    payments = db.query("SELECT * FROM payments ORDER BY id DESC LIMIT 30")
    alerts = db.query("SELECT * FROM alerts ORDER BY id DESC LIMIT 20")
    return render_template("inbox.html", payments=payments, alerts=alerts)


@app.route("/inbox/simulate", methods=["POST"])
@login_required
def simulate_sms():
    _check_csrf()
    if not config.ENABLE_SIMULATOR:
        abort(403)
    user = auth.get_user_by_id(session.get("user_id"))
    if not user or user["role"] != "owner" or not session.get("is_owner", True):
        abort(403)

    try:
        message = request.form.get("message", "").strip()
        if message:
            result = matching.process_message(message)
        else:
            result = matching.process_payment(request.form.get("amount"), request.form.get("txn_id"),
                                              request.form.get("provider") or None)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("inbox"))
    flash(f"Result: {result['result']}" + (f" ({result['reason']})" if "reason" in result else ""), "info")
    return redirect(url_for("inbox"))


@app.route("/api/sms", methods=["POST"])
def receive_sms():
    token = request.headers.get("X-Token") or request.args.get("token", "")
    if not hmac.compare_digest(token, config.SMS_TOKEN):
        abort(401)
    data = request.get_json(silent=True) or request.form
    text = (data.get("message") or data.get("text") or data.get("body")
            or data.get("msg") or data.get("content") or "")
    return jsonify(matching.process_message(text))


@app.route("/reports")
@login_required
def reports_page():
    user = auth.get_user_by_id(session.get("user_id"))
    is_owner = bool(user and user["role"] == "owner" and session.get("is_owner", True))

    cashier_active = False
    cashier_remaining = 0
    cashier_until = session.get("cashier_accounting_until")
    if cashier_until:
        try:
            exp = parse(cashier_until)
            rem = int((exp - now_utc()).total_seconds())
            if rem > 0:
                cashier_active = True
                cashier_remaining = rem
            else:
                session.pop("cashier_accounting_until", None)
        except Exception:
            session.pop("cashier_accounting_until", None)

    is_authorized = is_owner or cashier_active
    active_passcode = auth.get_active_passcode() if is_owner else None

    return render_template(
        "reports.html",
        is_authorized=is_authorized,
        is_owner=is_owner,
        cashier_accounting_active=cashier_active,
        cashier_accounting_remaining=cashier_remaining,
        active_passcode=active_passcode,
        data=reports.summary() if is_authorized else None,
        chain=ledger.verify_chain() if is_authorized else None,
    )


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(debug=False, host=host)
