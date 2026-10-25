# Presentation Slides: Payment Proof & Sales Ledger (PPL)
### INSA Cybersecurity Summer Camp 2026 &middot; Final Project Presentation

---

## Slide 1: Title & Overview
### **Payment Proof & Sales Ledger (PPL)**
**A Tamper-Evident POS Verification Engine for Ethiopian Micro-Merchants**

* **Authors:** Amanuel Mintesenot & Nahom Mekuria (2-Person Engineering Team)
* **Target:** Small shops, kiosks, and retail counters across Ethiopia
* **Core Philosophy:** *Zero trust on the customer's screen — verify only on the merchant's device.*

---

## Slide 2: The Real-World Problem
### **Why Ethiopian Merchants Lose Money Every Day**
1. **The Telebirr / CBE Boom:** Over 90% of urban micro-payments are cashless.
2. **Fake Screenshot Scam:** Scammers show AI-generated receipts or fake-SMS apps.
3. **The Busy Counter Trap:** Cashiers don't have time to log in to bank apps during rush hours.
4. **Replay Attacks:** Scammers reuse yesterday's valid transaction receipt for a new purchase.
5. **Direct Loss:** Merchants hand over inventory for money that was never sent.

---

## Slide 3: The PPL Architecture
### **How PPL Eliminates Visual Deception**

```
Customer Pays (Telebirr/CBE) ---> Bank Sends SMS to Merchant Phone
                                              |
                                 (Silent Android Forwarder)
                                              |
                                              v
Cashier Counter Board  <--- Live Sync <--- PPL Backend (Flask)
(Rings Chime & Turns Green!)              - Regex Parser (ETB/Birr/URL)
                                          - Replay Check (Unique Txn ID)
                                          - Cryptographic Hash Ledger
```

* **Cashier Experience:** Opens sale with 1 tap (`50`, `100`, `200`, `500 ETB`).
* **Owner Advantage:** The owner's phone receives the bank SMS and auto-forwards it; the cashier at the counter gets instant verification without needing the owner's phone!

---

## Slide 4: Security & Fraud Defense Engine
### **Multi-Layer Threat Traps**

* **Fake Buyer (No SMS):**
  * `0 – 2 min`: Pending (waiting).
  * `2 – 10 min`: Yellow warning (delayed).
  * `> 10 min`: Red alert **"NO PAYMENT &middot; DO NOT RELEASE GOODS"**.
* **Replayed Receipt:** Re-using a transaction ID triggers instant `duplicate_txn` alert (`BRU-02`).
* **Underpayment Trick:** Sending 50 ETB for a 500 ETB purchase triggers `wrong_amount` mismatch (`AT-02`).
* **Anti-Phishing Filter:** Banking OTPs & passcodes are recognized and immediately dropped (`BRU-03`).
* **Endpoint Authentication:** `/api/sms` guarded by secret token evaluated with timing-safe comparison (`hmac.compare_digest`).

---

## Slide 5: Tamper-Evident Cryptography
### **SHA-256 Hash Chain Ledger**

* Every verified sale is cryptographically linked to the previous transaction:
  $$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} \parallel \text{Sale\_ID}_n \parallel \text{Amount}_n \parallel \text{Timestamp}_n)$$
* **Mathematical Immutability:** Editing any past sale in the database breaks the chain instantly.
* **On-Demand Audit (`verify_chain`):** Automatically pinpoints the exact corrupted row.
* **Offline Verification:** Closing daily SHA-256 hash is exported for owner offline records.

---

## Slide 6: Dual Roles & Operational Safety (FR-10)
### **Cashier vs. Shop Owner Separation & Dynamic TTL Tokens**

* **Cashier Mode (Default):**
  * Superfast 1-tap sale creation.
  * Live verification board with auto-sync and sound chime.
  * Restricted from viewing sensitive profit margins or ledger tampering screens.
* **Shop Owner Mode:**
  * Authenticated with salted Scrypt/PBKDF2 credentials.
  * Complete daily, 7-day, and monthly revenue totals.
  * Profit margins (sales minus wholesale item costs).
  * Cryptographic ledger health verification.
* **Ephemeral Shift Passcodes (10-Minute TTL):**
  * Solves static PIN shoulder-surfing: owner issues a dynamic 6-digit passcode.
  * Cashier unlocks reports for exactly 10 minutes to complete shift accounting, with automatic revocation.

---

## Slide 7: Live Demonstration Walkthrough
### **3-Minute Demo Sequence for Evaluators**

1. **Step 1: Legitimate Telebirr Sale**
   * Open sale for `80.00 ETB`. Feed genuine Telebirr SMS &rarr; Dashboard chimes and turns Verified!
2. **Step 2: Catching a Replay Scammer**
   * Open new sale for `80.00 ETB`. Feed same message again &rarr; Flagged as `Duplicate Replay Attack`!
3. **Step 3: Staged Alert Timeout**
   * Show a pending sale turning yellow and red when no money arrives.
4. **Step 4: Tamper Detection Proof**
   * Modify a ledger row in `ppl.db` &rarr; Reports page flashes red: *"TAMPERED AT ENTRY #X"*.

---

## Slide 8: Summary & Impact
* **Automated Test Suite:** 30 out of 30 automated acceptance & security tests passing.
* **Production Hardened:** Zero-dependency audio engine, DaisyUI / Tailwind mobile-responsive UI, parameterized SQL queries, ephemeral TTL passcodes, brute-force rate-limiting.
* **Accessible:** Requires no expensive hardware or private banking APIs.
* **GitHub Repository:** [https://github.com/amanminte/payment-proof-ledger](https://github.com/amanminte/payment-proof-ledger)
