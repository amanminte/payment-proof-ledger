# Payment Proof & Sales Ledger: Requirements Document

**Working title.** Draft v0.2, Oct 15, 2026.  
**Authors:** Amanuel Mintesenot & Nahom Mekuria (2-Person Engineering Team)  
**Context:** INSA cybersecurity summer camp (Deadline: Oct 25, 2026)

---

## 1. Purpose and Scope

Small sellers in Ethiopia are sometimes shown fake payment confirmations (AI-made images or fake-SMS apps) and release goods without being paid. This system helps a seller match each sale to a real incoming payment message on the seller's own phone, flags claimed payments that never arrive, and keeps a tamper-evident sales record with daily, weekly, and monthly totals.

- **In scope:** capturing the seller's incoming payment SMS, matching it to an open sale, mismatch alerts, a sales ledger, reports, a backend hash chain, and a web form that simulates incoming SMS for testing.
- **Out of scope:** reading text from photos (OCR), reused-photo detection (deferred), complex employee permissions, a hash-chain screen, live checks against Telebirr or CBE systems, forgery detection of images, a native mobile app, any list of known scammers.

---

## 2. Stakeholders and Roles

| Role | Responsibility and authority |
| :--- | :--- |
| **Shop owner** | Owns the outcome. Sees all sales, flagged attempts, and reports. Can edit settings. |
| **Cashier / employee** | Opens sales and confirms handovers. Cannot edit or delete records. |
| **Buyer** | Claims to have paid and may show a photo or message. Has no access to the system. |
| **Payment provider (external)** | Sends the payment SMS to the seller. The system has no access to provider systems. |

---

## 3. Current Problems (To Confirm in Seller Interviews)

1. A buyer shows a fake confirmation and the seller releases goods without checking the balance.
2. In a busy queue there is no time to check each payment by hand.
3. Sales and payments are tracked manually or not at all, so mismatches go unnoticed.
4. Employees can alter records without anyone noticing.

---

## 4. Assumptions and Constraints

### Assumptions
- The seller uses an Android phone to receive payment SMS.
- The seller has internet access for the web page.
- The payment SMS arrives within a couple of minutes of a real payment.

### Constraints
- **CON-01:** The system has no access to provider APIs or systems.
- **CON-02:** Automatic SMS capture works on Android only.
- **CON-03:** Delivery deadline is Oct 25, 2026.
- **CON-04:** One developer.

---

## 5. Requirements (Priority: M = Must, S = Should, C = Could)

### Business Requirements
| ID | Requirement | Pri |
| :--- | :--- | :---: |
| **BR-01** | Reduce the chance that a seller releases goods for a payment that never arrived. | M |
| **BR-02** | Give the owner a trustworthy record of sales and attempted fake payments. | M |

### User Requirements (Stories)
| ID | Story | Pri |
| :--- | :--- | :---: |
| **UR-01** | As a cashier, I want a yellow warning, then a red alert, when a claimed payment has not arrived, so that I do not release goods while it is unconfirmed. | M |
| **UR-02** | As an owner, I want daily, weekly and monthly totals, so that I can see how the shop is doing. | M |
| **UR-03** | As an owner, I want to see how many claimed payments never arrived, so that I know how often scam attempts happen. | S |
| **UR-04** | As an owner, I want to know if a record was changed afterward, so that I can trust the ledger. | S |

### Functional Requirements
| ID | Requirement | Source | Pri |
| :--- | :--- | :--- | :---: |
| **FR-01** | The system shall receive each incoming payment SMS forwarded from the seller's phone and extract provider, amount, transaction ID and time. A web form that simulates an incoming SMS shall use the same processing path. | Owner | M |
| **FR-02** | The system shall let a cashier open a sale with the amount the buyer claims to have paid. | Cashier | M |
| **FR-03** | The system shall mark a sale "verified" only when an incoming message matches its amount within 10 minutes and carries a transaction ID not logged before. | Owner | M |
| **FR-04** | The system shall show a "No matching payment" alert in two stages (yellow after 2 minutes with no matching message, red after 10 minutes) and log the attempt at red. A late payment shall still match the sale and clear the alert. | Cashier | M |
| **FR-05** | The system shall list incoming payments that match no open sale as "unassigned". | Owner | M |
| **FR-06** | The system shall add verified sales to the ledger and produce daily, weekly and monthly totals. | Owner | M |
| **FR-07** | The system shall record an optional cost per sale and report profit as sales minus recorded cost. | Owner | S |
| **FR-08** | The system shall store a hash of each ledger entry linked to the previous entry and report when the chain is broken (an on-demand check, no dedicated screen); the latest hash shall appear on the daily report so the owner can compare it with a saved copy. | Owner | S |
| **FR-09** | The system shall store a hash of each attached buyer photo and flag a photo reused on a different sale. Deferred: build only if time remains. | Owner | S |
| **FR-10** | The system shall require a PIN login and give owner and cashier different permissions (two fixed roles only). | Owner | C |

### Business Rules
- **BRU-01:** A sale cannot be logged as verified without a matching incoming message.
- **BRU-02:** A transaction ID can be used for only one sale.
- **BRU-03:** One-time-password messages are never stored or forwarded.
- **BRU-04:** Profit is reported only when a cost has been recorded; otherwise the report is labeled "sales".

### Non-Functional Requirements
| ID | Requirement |
| :--- | :--- |
| **NFR-01** | The system shall match an incoming message to an open sale within 2 seconds of receiving it. |
| **NFR-02** | The forwarding endpoint shall accept requests only with a secret token. |
| **NFR-03** | Sales data shall be stored only on the seller's own server. |
| **NFR-04** | A cashier shall be able to open a sale in at most 3 taps and 1 typed amount, on a phone browser. |
| **NFR-05** | All inputs shall be validated and database queries parameterized. |

---

## 6. Acceptance Tests

| Test | Given / When / Then | Covers |
| :--- | :--- | :--- |
| **AT-01** | Given an open sale of 500, when a message for 500 with a new ID arrives within 10 minutes, then the sale is verified and added to the ledger. | FR-03, FR-06 |
| **AT-02** | Given an open sale of 500, when a message for 300 arrives, then the sale is not verified and a mismatch is logged. | FR-03 |
| **AT-03** | Given a transaction ID already used, when it arrives again for another sale, then the sale is flagged as a duplicate. | FR-03, BRU-02 |
| **AT-04** | Given an open sale, when 2 minutes pass with no message, then the sale turns yellow; when 10 minutes pass, then it turns red and the attempt is logged. | FR-04 |
| **AT-05** | Given a payment with no open sale, when it arrives, then it appears under "unassigned". | FR-05 |
| **AT-06** | Given a stored ledger, when one entry is edited directly in the database, then the chain warning appears. | FR-08 |
| **AT-07** | Given a request without the secret token, when it hits the endpoint, then it is rejected. | NFR-02 |
| **AT-08** | Given an OTP message, when it is forwarded, then it is discarded. | BRU-03 |
| **AT-09** | Given an open sale that has turned yellow, when a matching message arrives, then the sale is verified and the alert clears. | FR-03, FR-04 |

---

## 7. Traceability

| Need | Stakeholder | Requirements | Tests |
| :--- | :--- | :--- | :--- |
| Do not release goods unpaid | Cashier, owner | BR-01, UR-01, FR-02 to FR-04 | AT-01 to AT-04 |
| Trustworthy records and totals | Owner | BR-02, UR-02 to UR-04, FR-05 to FR-09 | AT-05, AT-06 |
| Protect the system and data | Owner | FR-10, NFR-02, NFR-03, NFR-05, BRU-03 | AT-07, AT-08 |

---

## 8. Open Questions for Seller Interviews

1. What do you do today when a buyer shows a payment?
2. Have you lost money to a fake confirmation? How often and how much?
3. How long does a real payment SMS usually take to arrive?
4. Would you use a tool that matches each sale to the real incoming payment? What would stop you?
5. Do you track costs, or only sales?

*Update this document after the interviews, and mark any requirement that changes with the reason.*

---

## 9. Delivery Plan

1. **Oct 15:** seller interviews; update this document.
2. **Oct 16:** backend and database (sales, payments, alerts); create-sale page, amount only.
3. **Oct 17:** payment inbox with simulated SMS; matching.
4. **Oct 18:** alert stages; reports for today, week and month.
5. **Oct 19:** checkpoint. The full demo must run end to end, including a caught fake buyer; otherwise pivot.
6. **Oct 20–21:** secret-token check, input validation, backend hash chain; real SMS forwarding only if the core is stable.
7. **Oct 22:** run all acceptance tests, ideally with a real seller.
8. **Oct 23:** threat model, BPMN diagrams, report, slides.
9. **Oct 24–25:** rehearse, keep a buffer, submit.

---

## 10. Changes in v0.2

- The alert is now staged (yellow at 2 minutes, red at 10) so a delayed honest payment is not flagged as a scam: FR-03, FR-04, UR-01, AT-01, AT-04, new AT-09.
- A web form that simulates SMS is added so matching can be built and tested before real forwarding: FR-01.
- Reused-photo detection is deferred, because the real proof is the incoming SMS, not the photo: FR-09.
- The hash chain stays in the backend; the daily report shows the latest hash for comparison: FR-08.
- Permissions are limited to two fixed roles: FR-10.
