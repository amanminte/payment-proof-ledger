# Payment Proof & Sales Ledger (PPL)
### A Tamper-Evident Payment Verification Engine for Ethiopian Micro-Merchants
*Final Project Submission &middot; INSA Cybersecurity Summer Camp 2026*

---

## 📌 Project Submission Details

| Requirement | Information |
| :--- | :--- |
| **1. GitHub Repository** | [https://github.com/amanminte/payment-proof-ledger](https://github.com/amanminte/payment-proof-ledger) |
| **2. 5-Minute Video Presentation** | 🎥 **[Click Here to Watch the 5-Minute Video Demo](https://drive.google.com/file/d/1Bc3GrI_GD-QjcjXFtbzs-PhSwOnDMwsq/view?usp=sharing)** |
| **3. Project Name** | **Payment Proof & Sales Ledger (PPL)** |
| **4. Team Information** | • **Amanuel Mintesenot** (Team Leader) &mdash; **CTC ID:** `CTC-1849-26`<br>• **Nahom Mekuria** (Engineering Teammate) &mdash; **CTC ID:** `CTC-6077-26` |

### 📖 Project Summary & Purpose
In Ethiopia, over 90% of daily digital payments rely on Telebirr and CBE Mobile Banking. Because micro-retailers lack private banking APIs, cashiers traditionally verify transactions by looking at the customer's phone screen. Scammers exploit this through fake-SMS generator apps, manipulated digital receipts, and duplicate transaction replays.

**Payment Proof & Sales Ledger (PPL)** eliminates reliance on the buyer's screen. Enforcing a strict zero-trust model (*"verify exclusively on the merchant's device"*), PPL captures genuine bank SMS notifications on the merchant's Android phone, validates transaction IDs and amounts in real time over local Wi-Fi, triggers an audible counter chime 🔔, and seals every verified transaction into a sequential, tamper-evident SHA-256 hash chain ledger.

### 🌟 Main Features
* **Multi-Bank Parsing:** Real-time regex extraction for Telebirr (English & Amharic formats) and Commercial Bank of Ethiopia (CBE) messages.
* **Instant Cashier Feedback:** Zero-reload live dashboard with automatic audible cash chime 🔔 upon verification.
* **Multi-Layer Fraud Traps:** Automatic detection for replayed transaction IDs (`payments.txn_id` UNIQUE constraint), underpayment fraud, and OTP phishing filtering.
* **Staged Visual Timers:** Automated risk escalation from Normal (0-2m) &rarr; Waiting (Yellow at 2m) &rarr; NO PAYMENT Alert (Red at 10m).
* **Cryptographic SHA-256 Ledger:** Sequential mathematical hash chain where `verify_chain()` detects any database tampering, row deletion, or amount modification.
* **Role Separation & Shift Security:** Cashiers cannot view profit margins or daily revenue totals. Shift accounting is unlocked using **ephemeral 10-minute passcodes**.
* **Real Hardware Verified:** Empirically verified with an Android phone running *Incoming SMS to URL forwarder* locked to shortcode `127` over local Wi-Fi.
* **Comprehensive Test Suite:** **30 of 30 automated acceptance and security tests passing** under `pytest`.

---

## Why we built this
In Ethiopia today, almost every small shop, kiosk, and cafe accepts **Telebirr** and **CBE Mobile Banking**. 

Because small retailers don't have private bank APIs or expensive card machines, cashiers have to verify payments by looking at the customer's phone screen. This creates an easy way for scammers to steal:
* They show fake payment screenshots.
* They use apps that generate fake bank SMS messages.
* They alter receipts with photo-editing tools or send 50 Birr for a 500 Birr item.

In a busy shop, the cashier glances quickly, believes the customer, hands over the goods, and loses money. 

Our rule is simple: **Never trust the customer's screen. Only verify against the real SMS message received on the shopkeeper's own phone.**

---

## How it works (in 4 simple steps)

```
[ Customer Pays via Telebirr or CBE ]
                │
                ▼ (Real Bank SMS)
[ Shopkeeper's Android Phone ]
                │ (Local Wi-Fi Webhook)
                ▼
[ PPL Server on Laptop / Counter Device ]
   ├── Checks secret security token
   ├── Reads amount & transaction ID (English & Amharic)
   ├── Blocks duplicate transaction IDs
   └── Matches to open sale
                │
                ▼
[ Cashier Screen Chimes 🔔 & Turns Green! ]
```

1. **Cashier opens a sale:** Tap a quick button (`50`, `100`, `200`, `500 ETB`) or type an amount. The board shows **Pending**.
2. **Customer transfers money:** Through Telebirr (`*127#` / App) or CBE Mobile Banking.
3. **Shop phone catches the bank SMS:** The merchant's Android phone automatically forwards the bank SMS to PPL over local Wi-Fi.
4. **Instant verification:** PPL parses the message, matches the exact amount, checks that the transaction ID was never used before, plays a loud cash register chime 🔔, and marks the sale **Verified** in green.

If no payment arrives, the sale turns **Yellow** after 2 minutes and **Red (NO PAYMENT)** after 10 minutes. If a late payment finally arrives, it still matches and clears the timer alert.

---

## Key Features

* **Real Ethiopian Bank Support:** Understands real Telebirr (English and Amharic formats like `ተቀብለዋል` and `የግብይት ቁጥር`) and Commercial Bank of Ethiopia (CBE) messages.
* **Tested on Real Hardware:** Successfully tested and verified with real Android phones forwarding live Telebirr (`127`) messages over local Wi-Fi.
* **Scam Protection:**
  * **Duplicate Replay Trap:** Reusing an old transaction ID gets flagged immediately.
  * **Underpayment Defense:** Sending 50 Birr for a 500 Birr purchase logs a `wrong_amount` warning and refuses to verify.
  * **OTP Privacy Filter:** Banking OTPs and login codes are automatically thrown away so sensitive codes never get stored.
* **Tamper-Evident Ledger:** Every verified sale is cryptographically linked to the previous one using SHA-256 hashes. If anyone edits or deletes a past sale in the database, `verify_chain()` catches it instantly.
* **Separate Cashier & Owner Roles:**
  * Cashiers cannot see store profit margins or revenue totals.
  * To check shift reports, the owner gives the cashier a **temporary 10-minute passcode** that auto-expires.
* **Rate Limiting:** Protects logins and passcodes against automated guessing attacks.

---

## Quick Start (How to Run)

### 1. Set up the environment
```powershell
# Clone the repository and enter the directory
cd payment-proof-ledger

# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure environment settings
```powershell
# Copy the example configuration
cp .env.example .env
```

For evaluation and testing, `.env` comes ready with:
```ini
DEMO_MODE=1
ENABLE_SIMULATOR=1
HOST=0.0.0.0
DATABASE=ppl.db
ACCOUNTING_PASSCODE_TTL_MIN=10
```
*(Demo accounts seeded: `owner` / `owner123` and `cashier` / `cashier123`).*

### 3. Start the server
```powershell
python -m backend.app
```
Open **http://127.0.0.1:5000** in your browser.

---

## Connecting a Real Android Phone (Optional Field Gateway)

You can forward real bank SMS messages from any Android phone on the same Wi-Fi:

1. Install the free open-source app **"Incoming SMS to URL forwarder"** (available on F-Droid or GitHub).
2. Open the app and create a new rule:
   * **Webhook URL:** `http://<YOUR-LAPTOP-IP>:5000/api/sms?token=change-me`
   * **Sender:** `127` *(for Telebirr)* or `*` *(wildcard for all)*
   * **Text filter:** Leave completely empty.
   * **Local network mode:** Turn **ON** *(allows Wi-Fi connections)*.
3. Tap **TEST** &rarr; returns `200 OK`.
4. Tap **ADD** to save and make sure the rule switch is turned **ON**.

---

## Automated Tests

We wrote **30 automated tests** covering every feature, alert, and edge case:

```powershell
pytest -v
```

All 30 tests pass cleanly in ~20 seconds.

---

## Honest Project Limitations

In the spirit of good engineering, here are the real-world limits we openly disclose:

1. **Concurrent Identical Sales:** If two customers pay the exact same amount (e.g. both 500 ETB) at the same second, PPL matches on a first-come, first-verified basis. Cashiers should note customer names for high-value sales.
2. **Cashier Keeping Cash:** PPL protects against digital payment fraud. It cannot stop a dishonest cashier who takes physical paper Birr and never enters the sale into the system.
3. **Offline Hash Verification:** The SHA-256 hash chain detects database tampering. However, an attacker with full computer access could recalculate forward hashes. Shop owners should copy and save the daily closing hash offline.
4. **Local Network Mode:** For local store Wi-Fi, the app runs on plain HTTP. If deployed over the public internet, HTTPS and a reverse proxy (like Caddy or Nginx) must be added.

---

## Project Structure

```text
payment-proof-ledger/
├── backend/                  # Core Flask app, database & security
│   ├── app.py                # Web routes & webhook endpoint (/api/sms)
│   ├── auth.py               # User sessions & 10-minute ephemeral passcodes
│   ├── config.py             # App settings & production safety guards
│   ├── db.py                 # SQLite helper functions
│   ├── ledger.py             # SHA-256 tamper-evident hash chain & audit check
│   ├── matching.py           # Multi-bank parser (Telebirr/CBE) & matching engine
│   ├── rate_limit.py         # Sliding window rate limiter for login/passcodes
│   ├── reports.py            # Daily/weekly/monthly revenue & profit reports
│   └── tests/
│       └── test_matching.py  # All 30 automated pytest tests
├── frontend/                 # Templates & UI styling
│   ├── static/style.css      # Clean modern styling
│   └── templates/            # HTML templates (Dashboard, Inbox, Reports, etc.)
├── docs/                     # Full project documentation & defense guides
│   ├── PPL-Technical-Blueprint.pdf # 16-page complete technical blueprint
│   ├── final-report.md       # Final project report for evaluators
│   ├── demo-script.md        # 3-minute timed live presentation script
│   ├── evaluator-qa-cheatsheet.md # 1-page defense Q&A cheat sheet
│   ├── presentation-slides.md # Presentation slides
│   ├── requirements.md       # Full requirements document
│   └── threat-model.md       # Threat vectors & architectural boundaries
└── scripts/
    └── generate_pdf_blueprint.py # Script that builds the technical blueprint PDF
```

---

## Authors & Acknowledgments

* **Amanuel Mintesenot** (CTC ID: `CTC-1849-26`) &mdash; Team Leader
* **Nahom Mekuria** (CTC ID: `CTC-6077-26`) &mdash; Engineering Teammate
* **AI Pair-Programming & Security Review:** Developed in collaboration with **Antigravity** (Google DeepMind) as an interactive pair-programming assistant for architectural threat modeling, test suite design, and adversarial code hardening.
* Built for the **INSA Cybersecurity Summer Camp 2026**.
