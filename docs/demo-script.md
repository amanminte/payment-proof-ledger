# Live Demo Script & Evaluator Walkthrough (3 Minutes)
### Payment Proof & Sales Ledger (PPL) &middot; INSA Cybersecurity Summer Camp 2026

Use this script during your in-person presentation or project evaluation. It demonstrates the real-world problem, the instant verification engine, multi-layer fraud detection, and cryptographic tamper evidence.

---

## Pre-Demo Setup (Before the Judges Arrive)
1. In PowerShell, make sure the app is running:
   ```powershell
   cd "payment-proof-ledger"
   .\.venv\Scripts\python -m backend.app
   ```
2. Open two browser tabs:
   * **Tab 1 (Cashier Board):** `http://127.0.0.1:5000`
   * **Tab 2 (Bank SMS Simulator):** `http://127.0.0.1:5000/inbox`
3. **Optional Live Android Hardware Gateway:**
   * Connect Android phone to the same Wi-Fi.
   * Open *Incoming SMS to URL forwarder* app.
   * Target Webhook URL: `http://<your-laptop-ip>:5000/api/sms?token=change-me`
   * Sender filter: `*` (or `127` for Telebirr)
   * Local network mode: **ON**
   * Tap **TEST** &rarr; Shows `Success (200)`.
   *(Field testing note: Trials 1 & 2 verified that missing tokens are strictly rejected with 401; Trial 3 established authenticated local communication).*

---

## The 3-Minute Presentation Script

### 1. The Hook & The Problem (0:00 – 0:30)
> *"Hello respected evaluators. In Ethiopian shops today, digital retail payments are dominated by Telebirr and CBE Mobile Banking. But shopkeepers are losing thousands of Birr to a widespread scam: buyers show fake confirmation screenshots, AI-edited receipts, or fake-SMS apps.*
> 
> *A busy cashier glances at the buyer's screen, believes it, releases the goods, and the money never arrives.*
> 
> *Our project, **Payment Proof & Sales Ledger (PPL)**, enforces a zero-trust rule: **never trust the customer's phone — verify only against the authentic incoming SMS on the merchant's device.**"*

---

### 2. Live Demo: Legitimate Sale & Instant Verification (0:30 – 1:15)
> *"Let's see how a legitimate transaction works."*

1. On **Tab 1 (Cashier Board)**:
   * Click **New Sale**.
   * Tap the **`200 ETB`** 1-tap quick button.
   * Click **Open Sale**.
   * *Say:* *"The cashier opens a 200 Birr sale in one tap. The board shows `Pending`."*
2. Switch to **Tab 2 (Inbox Simulator)**:
   * Click the sample button: **"CBE Mobile (200.00 ETB)"**.
   * Click **Process Payment Message**.
3. Switch back to **Tab 1 (Cashier Board)**:
   * Listen to the **cash register chime**!
   * Point to the screen: The pending sale disappears, and **Verified Today** updates with a green checkmark!
   * *Say:* *"In under one second, the merchant's phone catches the bank SMS, PPL parses the transaction ID, validates the amount, plays the chime, and the cashier safely hands over the items."*

---

### 3. Live Demo: Catching Scammers Red-Handed (1:15 – 2:00)
> *"Now let's see how PPL stops fraudsters."*

#### Attack A: Replaying an Old Receipt (Replay Attack)
1. Open a new sale for **`200 ETB`**.
2. Go to **Inbox**, and click the exact same **"CBE Mobile (200.00 ETB)"** sample button again.
3. Click **Process**.
4. *Say:* *"The scammer tries to reuse the receipt from 5 minutes ago. PPL checks the unique transaction ID constraint and immediately flags a **Duplicate Replay Attack** (`BRU-02`). The sale remains unverified and the merchant's goods are safe."*

#### Attack B: The Partial Underpayment Trick
1. Open a new sale for **`500 ETB`**.
2. Go to **Inbox**, paste a message for only **`50 ETB`**:
   ```text
   Dear customer, you have received ETB 50.00 from account 1**9999. https://mbreciept.cbe.com.et/v2-underpay99
   ```
3. Click **Process**.
4. Show the alert log: **`wrong_amount`** mismatch! The 500 ETB sale is not tricked.

#### Attack C: Staged Alert Timers & Dismiss
* Show that pending sales turn **Yellow (`Waiting...`)** at 2 minutes, and **Red (`NO PAYMENT - DO NOT RELEASE`)** at 10 minutes.
* Show the **in-page dismiss modal** on fresh pending sales if a customer changes their mind before the warning triggers. Point out that warning and red alert sales are locked from cashiers to preserve audit evidence!

---

### 4. Cryptographic Ledger & Owner Security (2:00 – 2:40)
> *"PPL doesn't just protect the counter—it protects the business owner from internal employee tampering."*

1. Click **Reports** in the navigation bar while signed in as Cashier.
2. Show that it is **locked in Cashier Mode** (`FR-10`): cashiers cannot inspect business profit margins or tamper screens without authorization.
3. Demonstrate **Ephemeral Accounting Access**:
   * *Say:* *"Instead of a vulnerable static PIN that employees can shoulder-surf, PPL implements ephemeral 10-minute passcodes."*
   * Show the Owner generating an ephemeral 10-minute passcode (`849201`).
   * Cashier enters the code &rarr; Click **Unlock**.
   * Highlight the **Temporary Cashier Accounting Session** banner with the live auto-locking countdown timer!
4. Point to the **Cryptographic Hash Chain Integrity** card:
   * *Say:* *"Every verified sale is cryptographically linked to the previous transaction using a SHA-256 block hash:*
     $$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} \parallel \text{Sale\_ID} \parallel \text{Amount} \parallel \text{Time})$$
   * *If an employee or hacker enters the SQLite database directly and alters a past sale amount from 500 to 50, the hash chain breaks instantly and pinpoints the exact corrupted row."*
5. Show the **Latest Closing Hash** and click **Copy Hash**:
   * *Say:* *"The owner can save this daily closing digest offline to provide verifiable audit evidence."*

---

### 5. Conclusion & Technical Summary (2:40 – 3:00)
> *"To summarize:
> 1. **Zero Hardware Cost:** Runs on the merchant's existing laptop and Android phone.
> 2. **Ethiopian Bank Native:** Specifically tuned for real Telebirr (English & Amharic) and CBE mobile banking messages.
> 3. **Comprehensive Test Suite:** 30 automated acceptance and security tests passing.
> 4. **Production Code:** Full codebase, threat model, and architectural documentation are available on our public GitHub repository.
> 
> Thank you, and we welcome your questions!"*

---

## Likely Questions from Evaluators & How to Answer

### Q1: *"What if the scammer sends a fake SMS directly to the merchant's SIM?"*
> **Answer:** *"A real SMS on the merchant's own SIM requires carrier-level shortcode spoofing, which is exponentially harder than faking a screenshot on a buyer's screen. However, as noted in our Threat Model (`docs/threat-model.md`), for exceptionally large transactions, checking the balance in the official bank app remains the ultimate source of truth."*

### Q2: *"Why does the cashier not have access to delete red alerts?"*
> **Answer:** *"Under requirement `FR-10`, if a cashier could delete red 'NO PAYMENT' alerts, a dishonest employee who colluded with a scammer could destroy the audit trail. Warning and alert sales are locked so the store owner can investigate all failed payment claims."*

### Q3: *"Can this work if the merchant's phone is outside the shop on 4G?"*
> **Answer:** *"Yes! The `/api/sms` endpoint is an HTTP webhook. Using a free Cloudflare Tunnel or ngrok, the owner's phone can forward bank SMS from anywhere in Addis Ababa over mobile data."*
