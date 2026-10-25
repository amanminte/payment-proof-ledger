# Threat Model: Payment Proof & Sales Ledger (PPL)

**Context:** INSA Cybersecurity Summer Camp 2026  
**Document version:** v1.0 (aligned with Requirements v0.2)

---

## 1. Assets

1. **Merchant Inventory & Revenue:** Physical goods released only upon confirmed receipt of money; revenue records.
2. **Sales Ledger Integrity:** Historical transaction logs, amounts, timestamps, and verification states.
3. **SMS Ingestion Endpoint (`/api/sms`):** Availability and authenticity of the webhook receiving forwarded SMS messages.
4. **Sensitive Data & Credentials:** Application secret keys (`SECRET_KEY`), webhook auth token (`SMS_TOKEN`), and customer privacy (one-time passwords / banking codes).

---

## 2. Attackers & Threat Actors

| Threat Actor | Motivation | Capability |
| :--- | :--- | :--- |
| **Dishonest Buyer (Scammer)** | Obtain goods without paying. | Uses fake SMS generator apps, pre-generated screenshots, manipulated Photoshop/AI receipts, or replays old transaction IDs. |
| **Dishonest Employee / Cashier** | Skim cash or collude with buyers; alter past records to conceal discrepancies. | Has direct access to cashier web UI; may have physical access to the local store computer. |
| **Network / External Attacker** | Disrupt store operations, inject bogus payment notifications, or tamper with communications. | Can probe open network ports, forge HTTP requests against the web server, or intercept insecure traffic. |

---

## 3. Attacks and Defenses

| Threat / Attack Vector | Risk | System Defense & Mitigation | Relevant Requirement |
| :--- | :--- | :--- | :--- |
| **Fake Payment Screenshot / Fake SMS shown on buyer phone** | High | Cashier does not rely on buyer's phone. Sale remains `pending` / `waiting` / `alert` until an authentic matching SMS arrives on the merchant's device and is ingested into PPL. | BR-01, FR-02, FR-03, FR-04 |
| **Transaction ID Replay (Reusing a past receipt)** | High | Database enforces `UNIQUE` constraint on `payments.txn_id`. Replays trigger a `duplicate_txn` alert and prevent sale verification. | BRU-02, AT-03 |
| **Unauthorized SMS Injection to Webhook** | High | `/api/sms` requires an `X-Token` header. Verified using constant-time comparison (`hmac.compare_digest`) against `SMS_TOKEN`. Requests without or with incorrect token receive HTTP 401. | NFR-02, AT-07 |
| **Historical Ledger Tampering (Database Alteration)** | Medium | Cryptographic SHA-256 hash chain links each verified sale to the previous entry (`prev_hash`). Tampering breaks the chain and is flagged immediately upon audit (`verify_chain()`). Latest hash is published on reports. | FR-08, AT-06 |
| **OTP / Sensitive SMS Leakage** | High | Regular expression filters identify OTP / PIN / verification messages (`OTP_RE`) and discard them immediately prior to database storage or forwarding. | BRU-03, AT-08 |
| **SQL Injection & Web Attacks** | Medium | All database queries are strictly parameterized (`db.query`). HTML forms enforce CSRF tokens via secret session tokens; Jinja2 auto-escapes output. Input amounts and transaction IDs are validated against strict regex/type checks. | NFR-05, AT-07 |
| **Wrong Amount Claimed** | Medium | If incoming payment amount doesn't match the open sale amount, system logs a `wrong_amount` mismatch alert and does not verify the sale. | FR-03, AT-02 |
| **Delayed Payment SMS** | Low | Staged alerting: yellow at 2 minutes, red at 10 minutes. Late arrivals still match open sales and clear the alert (`AT-09`). | FR-04, AT-09 |

---

## 4. What This Tool Does NOT Stop (Residual Risks & Boundaries)

1. **Carrier-Level SMS Sender Spoofing:** If an attacker has telecommunications-grade access to spoof SMS originating from official shortcodes directly to the merchant's SIM, the merchant device will still forward it. Ultimate confirmation for large transactions remains verifying the official balance in the Telebirr/CBE app.
2. **Full Host / Root Compromise:** If an attacker or insider has full administrative access to the server, they could theoretically recalculate the entire hash chain from a specific point forward. Hence, the owner should keep an offline or offsite record of daily closing hashes.
3. **Device Malware on Forwarder Phone:** If the Android phone forwarding SMS is infected with malware, SMS forwards could be dropped or intercepted.
4. **Matching by Amount and Time Window (Ambiguity on Identical Concurrent Amounts):** When two different customers simultaneously open sales for the exact same amount (e.g. two separate customers both buying 500 ETB items within the same minute), PPL matches by exact amount and chronological arrival. Either customer's payment could verify either open sale. Cashiers should note customer names or check recent transaction IDs for high-value concurrent sales.

---

## 5. Assumptions

- **A-01:** The merchant's Android device receiving SMS is trustworthy and not compromised.
- **A-02:** The local network or hosting environment for PPL is protected from unauthenticated write access to the filesystem (`ppl.db`, `.env`).
- **A-03:** Legitimate Telebirr and CBE payment confirmation SMS messages arrive within normal network thresholds (typically < 2–5 minutes).
