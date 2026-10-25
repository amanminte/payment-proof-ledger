# Payment Proof & Sales Ledger (PPL)
## A Tamper-Evident Payment Verification Engine for Ethiopian Micro-Merchants

**Authors:** Amanuel Mintesenot (CTC-1849-26) & Nahom Mekuria (CTC-6077-26) — 2-Person Engineering Team  
**Context:** INSA Cybersecurity Summer Camp 2026 (Final Project Submission)  
**Repository:** [https://github.com/amanminte/payment-proof-ledger](https://github.com/amanminte/payment-proof-ledger)  
**Video Presentation:** [Watch 5-Minute Video Walkthrough](https://drive.google.com/file/d/1Bc3GrI_GD-QjcjXFtbzs-PhSwOnDMwsq/view?usp=sharing)  
**Date:** October 2026  

---

## Abstract

In Ethiopia's rapidly expanding digital retail economy, Telebirr and Commercial Bank of Ethiopia (CBE) Mobile Banking dominate daily consumer transactions. However, small merchants routinely fall victim to sophisticated payment deception: fraudsters present fake-SMS generator screens, manipulated transaction receipts, or AI-generated confirmation screenshots, persuading hurried cashiers to release goods without authentic settlement. 

**Payment Proof & Sales Ledger (PPL)** eliminates reliance on the buyer's screen. Operating on the zero-trust principle *"verify through the merchant's device only"*, PPL captures incoming bank SMS messages forwarded automatically from the shop owner's Android phone, parses amounts and transaction references in real time, matches them to pending sales, and records every verified transaction into a tamper-evident SHA-256 hash chain ledger.

---

## 1. Problem Statement & Threat Landscape

### 1.1 The Vulnerability of Visual Confirmation
In high-volume retail environments (kiosks, cafes, grocery shops), sellers lack direct API access to private banking networks. Cashiers verify payments by glancing at the customer's smartphone screen. Threat actors exploit this through:
1. **Fake SMS Generator Apps:** Android apps that simulate incoming SMS notifications appearing to originate from official shortcodes.
2. **AI & Image Manipulation:** Instant editing of genuine past receipts using mobile image editors or generative tools to alter amounts, dates, and merchant names.
3. **Transaction ID Replay Attacks:** Showing genuine receipts from previous days or earlier transactions for a new purchase.
4. **Partial Underpayment:** Sending 50 ETB for a 500 ETB purchase, relying on the merchant's cursory glance at a bank notification.

### 1.2 System Constraints
* **CON-01:** No private bank API access (Telebirr/CBE do not offer open public webhooks for micro-retailers).
* **CON-02:** Background SMS capture is constrained to Android (`RECEIVE_SMS` broadcast architecture).
* **CON-03:** Local-first storage: all sales and cryptographic hash data remain hosted on the merchant's own premise.

---

## 2. System Architecture

PPL adopts a lightweight, resilient three-tier architecture:

```
[ Customer Phone ] ---> Transacts via Telebirr / CBE
                               |
                               v
                     [ Bank GSM Network ]
                               |
                               v
               [ Owner Android Phone (SIM) ]
                               | (Silent HTTP POST via Background Forwarder)
                               v
          +------------------------------------------+
          |           PPL Engine (Flask)             |
          |  1. /api/sms (Token-authenticated)      |
          |  2. Parsing (Regex: Telebirr & CBE)     |
          |  3. Matching Engine (10-min window)      |
          |  4. SHA-256 Hash Chain Ledger            |
          +------------------------------------------+
                               |
                               v (Live JSON Sync / Audio Chime)
                   [ Cashier Counter Board ]
                     - Clean responsive UI with live polling & audio chime
                     - Staged Alert Badges (Pending / Waiting / Alert)
```

### 2.1 Separation of Roles & Ephemeral Passcode Access (`FR-10`)
* **Cashier Role:** Opens sales with 1-tap presets (`50`, `100`, `200`, `500 ETB`) and observes live confirmation. Cannot inspect business profits, aggregated revenue, or tamper audit screens.
* **Shop Owner Role:** Authenticated via salted Scrypt/PBKDF2 credentials. Unrestricted access to financial analytics, net profit reports, and cryptographic ledger health verification.
* **Ephemeral Shift Accounting Tokens (TTL):** To eliminate the risk of static PIN shoulder-surfing or credential leaks, store owners generate dynamic 6-digit passcodes valid for exactly 10 minutes (`access_tokens` table). Cashiers use these single-use codes to temporarily unlock reports for end-of-shift sales reconciliation, featuring automatic session revocation and live countdown auto-locking.

---

## 3. Cryptographic Tamper-Evident Ledger

To prevent retroactive alteration of sales data by dishonest employees or external intruders, PPL records all verified sales in a sequential SHA-256 cryptographic hash chain (`backend/ledger.py`):

$$\text{Hash}_0 = 0^{64} \quad (\text{Genesis Block})$$
$$\text{Hash}_n = \text{SHA-256}\big(\text{Hash}_{n-1} \parallel \text{Sale\_ID}_n \parallel \text{Amount}_n \parallel \text{Timestamp}_n\big)$$

### Tamper Detection Algorithm (`verify_chain`):
1. Traverses all entries ordered by sequential primary key.
2. Re-computes expected digest using the stored previous hash and entry parameters.
3. If an entry's recorded hash or `prev_hash` deviates, the audit immediately flags the state as `TAMPERED` and identifies the exact compromised record index (`broken_at`).
4. The daily closing hash is rendered on the Owner Reports view, allowing the owner to compare the live database digest against an offline physical backup.

---

## 4. Security & Threat Defenses

| Threat Vector | System Countermeasure | Requirement |
| :--- | :--- | :--- |
| **Fake Screenshot on Buyer Phone** | Sale remains `Pending` until genuine SMS arrives on owner's device. Cashier is explicitly instructed not to release goods. | `BR-01`, `FR-03` |
| **Replayed Transaction ID** | `payments.txn_id` enforces a database `UNIQUE` constraint. Replayed IDs trigger a `duplicate_txn` alert. | `BRU-02`, `AT-03` |
| **Partial Underpayment** | Amount validation requires exact matching ($|\text{amount} - \text{sale}| < 0.005$). Mismatches log a `wrong_amount` alert. | `AT-02` |
| **Unauthenticated SMS Injection** | `/api/sms` validates incoming requests with a pre-shared secret (`X-Token`) evaluated via constant-time `hmac.compare_digest`. | `NFR-02`, `AT-07` |
| **Phishing via OTP Injection** | Regex pattern matching detects OTP and authentication codes (`OTP_RE`) and immediately drops them before database ingestion. | `BRU-03`, `AT-08` |
| **Stale Delay False Alarm** | If a network delay causes a payment to arrive after the 10-minute red alert stage, the late arrival matches the sale and clears the alert (`AT-09`). | `FR-04`, `AT-09` |

---

## 5. Acceptance Test Results Matrix

The test suite (`backend/tests/test_matching.py`) validates all business rules and acceptance criteria under `pytest`:

| Test ID | Test Scenario | Expected Outcome | Status |
| :---: | :--- | :--- | :---: |
| **AT-01** | Open sale of 500 ETB matched to new 500 ETB message within 10 min | Verified and recorded in ledger | ✅ PASS |
| **AT-02** | Open sale of 500 ETB received with 300 ETB message | Sale pending; `wrong_amount` alert logged | ✅ PASS |
| **AT-03** | Previously logged transaction ID received for a second sale | Sale pending; `duplicate_txn` alert logged | ✅ PASS |
| **AT-04** | Sale pending at 2 min & 10 min without matching SMS | State changes to `waiting` (2m) and `alert` (10m) | ✅ PASS |
| **AT-05** | Unsolicited payment arrives without open sale | Stored as `unassigned` for retroactive matching | ✅ PASS |
| **AT-06** | Manual database row edit in `ledger` table | `verify_chain()` reports `ok: False` with exact row | ✅ PASS |
| **AT-07** | Endpoint hit without valid token | Rejects unauthenticated requests (Trials 1 & 2 fail with 401); verifies valid token via header or query param (Trial 3 passes with 200) | ✅ PASS |
| **AT-08** | SMS containing banking OTP forwarded to endpoint | Payload discarded; 0 rows inserted in payments | ✅ PASS |
| **AT-09** | Open sale turned red receives matching late payment | Sale verified; temporary timer alerts cleared | ✅ PASS |
| **Parser** | Sample Telebirr English receipt | Extracted 80.00 ETB, ID `TB8899AACC`, provider Telebirr | ✅ PASS |
| **Parser** | Sample CBE Mobile receipt (`mbreciept.cbe.com.et/<id>`) | Extracted 50.00 ETB, ID `v2-cbeMockTxnId50`, provider CBE | ✅ PASS |
| **Parser** | Sample CBE incoming receipt (`200.00 ETB`) | Extracted 200.00 ETB, ID `v2-cbeMockTxnId200`, provider CBE | ✅ PASS |
| **Parser** | Sample Telebirr Amharic incoming (`300.00 ብር`) | Extracted 300.00 ETB, ID `DA99887766` | ✅ PASS |
| **Security**| Parameterized SQL injection defense | Injection payload rejected safely | ✅ PASS |
| **Web** | Web routes & CSRF protection | All routes load 200; unauthenticated POST 400 | ✅ PASS |
| **RBAC** | Public register cannot create owner | Role radio removed; cashier-only provisioning | ✅ PASS |
| **Simulator**| /inbox/simulate locked to owner | 403 returned for cashier or when flag is 0 | ✅ PASS |
| **Ledger** | Sales table cross-check | Detects tampered sales amount & injected rows | ✅ PASS |
| **Rate Limit**| 5 failed attempts trigger lockout | Returns 429 after 5 failures on login & passcode | ✅ PASS |
| **Parser** | Ignore outgoing transfer & balance | Outgoing ignored; balance before amount handled | ✅ PASS |

**Result: 30 of 30 automated tests passed.**

### 5.1 Physical Android Gateway Field Integration Trials

During end-to-end integration testing on the local Wi-Fi network (Flask server at `192.168.1.3:5000`, Android gateway device at `192.168.1.5` running the *Incoming SMS to URL forwarder* app), the team executed a 3-stage empirical validation sequence:

| Trial | Mobile Forwarder Config | Server Response | Engineering Finding & Resolution |
| :---: | :--- | :---: | :--- |
| **Trial 1** | Sender: `127`<br>URL: `http://192.168.1.3:5000/api/sms`<br>Token: *None (omitted)* | `401 Unauthorized`<br>(❌ FAILED) | **Security Boundary Enforced:** Server rejected unauthenticated POST request, proving that external devices cannot inject payment notifications without credentials. |
| **Trial 2** | Sender: `*` (Wildcard)<br>URL: `http://192.168.1.3:5000/api/sms`<br>Token: *None (omitted)* | `401 Unauthorized`<br>(❌ FAILED) | **Filter Independence Confirmed:** Changing the mobile app's SMS sender filter from `127` to wildcard `*` confirmed that sender filtering is strictly independent of the authentication requirement. |
| **Trial 3** | Sender: `*`<br>URL: `http://192.168.1.3:5000/api/sms?token=change-me`<br>Local network mode: **ON** | `200 OK`<br>(✅ SUCCESS) | **End-to-End Operational:** Webhook query parameter authenticated successfully; local network bypass enabled uninterrupted communication. Test ping succeeded and incoming payment SMS matched in real time. |

Following Trial 3, the team locked the mobile forwarder to sender `127` (acting as a mobile-level firewall against spoofed regular SIMs) and processed 4 real Telebirr transactions. All 4 were received, parsed, and verified in real time, triggering the counter audio chime and sealing the cryptographic ledger chain at 9 blocks.

---

## 6. Known Operational Limitations & Future Roadmap

### Known Limitations:
1. **Concurrent Identical Amounts:** When two customers simultaneously purchase items with the exact same price (e.g. both paying 500.00 ETB within the same minute), matching occurs on a first-received, first-verified basis. Cashiers should note customer names or check transaction IDs for high-value concurrent sales.
2. **Offline Hash Verification:** While the SHA-256 hash chain provides mathematical tamper-evidence against unauthorized database edits, someone with full filesystem access could theoretically recalculate forward hashes. Thus, owners should periodically record daily closing hashes offline.

### Future Enhancements:
1. **Lightweight Android Forwarder APK:** An open-source companion app configured with QR-code server pairing.
2. **Audio Speaker Peripheral:** An affordable ESP32 or Bluetooth counter speaker announcing *"Payment of 200 Birr Verified via Telebirr"* in Amharic.
3. **Multi-Store Management:** Cloud-backed replication of local hash chains for multi-branch retailers.

---

## Acknowledgments
Developed by Amanuel Mintesenot (CTC-1849-26) and Nahom Mekuria (CTC-6077-26) for the INSA Cybersecurity Summer Camp 2026. The authors acknowledge the use of **Antigravity** (Google DeepMind) as an interactive AI pair-programming assistant for architectural threat modeling, test suite design, and adversarial security code hardening.
