# 📋 PPL Defense: 1-Page Evaluator Q&A Cheat Sheet
*INSA Cybersecurity Summer Camp &middot; Amanuel Mintesenot (CTC-1849-26) & Nahom Mekuria (CTC-6077-26)*

---

### ⏱️ The 3-Minute Team Speaking Split
* **Teammate 1 (Opening & Live Demo &middot; 90s):** Explains the retail scam problem in Ethiopia, demonstrates opening a 500 ETB sale, triggers the live cash chime with an incoming SMS, and shows the duplicate replay trap.
* **Teammate 2 (Security, Cryptography & Closing &middot; 90s):** Explains the SHA-256 hash chain ledger, demonstrates the 10-minute ephemeral cashier passcode, and explains the residual threat model boundaries.

---

### 🎯 5 Core Defense Questions (20-Second Answers)

#### Q1: *"Can't a scammer fake the SMS too?"*
> **Answer (Teammate 1):**  
> *"A fake-SMS app only tricks someone looking at the buyer's screen. PPL strictly ignores that screen and trusts only the SMS that arrives on the merchant's own phone from the bank's shortcode. While sender names can be spoofed cheaply through commercial bulk-SMS services, trusting the sender name is not cryptographic. PPL significantly reduces counter scams by ignoring the buyer's device. For large sales, we recommend a secondary in-app balance check."*

#### Q2: *"Why not just check the Telebirr or CBE mobile app?"*
> **Answer (Teammate 2):**  
> *"Checking the banking app is best when time permits. In a crowded kiosk or queue, cashiers skip it. PPL automates the match in under 1 second, warns at 2 minutes, alerts in red at 10 minutes if no payment arrives, and logs scam attempts. It supports the banking app—it does not replace it."*

#### Q3: *"What stops a dishonest cashier from cheating?"*
> **Answer (Teammate 1):**  
> *"A cashier cannot view daily revenue totals, cannot create owner accounts, cannot trigger simulated payments, and cannot cancel warning or alert sales after 2 minutes. Furthermore, if someone alters past sales in the SQLite database, the ledger audit flags it. What we don't stop: off-the-books transactions where a cashier accepts physical cash without opening a sale. That is documented in our threat model."*

#### Q4: *"Is your SHA-256 hash chain tamper-proof?"*
> **Answer (Teammate 2):**  
> *"No cryptographic hash stored locally is completely tamper-proof—it is **tamper-evident**. Altering an amount, deleting a block, or injecting an unverified sale breaks the chain immediately. Because a root intruder could theoretically recalculate hashes forward, the store owner exports and saves the daily closing digest offline for verifiable comparison."*

#### Q5: *"Does it work with real messages, and what happens when it can't parse one?"*
> **Answer (Teammate 1):**  
> *"Yes. We verified it against test messages modeled on real Telebirr English, Telebirr Amharic (`ተቀብለዋል`, `የግብይት ቁጥር`), and CBE Mobile Banking receipt formats (`mbreciept.cbe.com.et`), with all personal details replaced. If an incoming message cannot be parsed, it fails safe: it is marked `unparsed`, no sale verifies, and the cashier is instructed to check the official bank app. It also drops sensitive OTPs and ignores outgoing transfers."*

---

### 💡 Bonus Question: *"Did you use AI to build this?"*
> **Answer (Both):**  
> *"Yes, as an interactive pair-programming and security testing tool with Antigravity (Google DeepMind). We authored the requirements and threat model, and used adversarial probes to attack our own implementation. That attack-driven review uncovered critical vulnerabilities—such as public owner registration and unindexed sales manipulation—which we hardened with 30 passing automated regression tests."*

#### Q7: *"Did your Android hardware gateway work right away on the first attempt?"*
> **Answer (Teammate 1):**  
> *"No, and that failure was valuable! In Trial 1 and 2, our phone forwarder hit the endpoint without the secret token, and PPL strictly blocked it with HTTP 401 Unauthorized. That empirically proved our security gate cannot be bypassed by changing sender filters or network pings. In Trial 3, we supplied the token via the query parameter and enabled local network mode, and it succeeded with 200 OK. We documented all 3 trials in Section 10 of our technical blueprint."*

---

### ⚠️ Upfront Honest Limits (Say These Before Evaluators Ask)
1. **Concurrent Identical Amounts:** Matching is by exact amount and time window. If two customers simultaneously owe 500 ETB, payments match chronologically. Cashiers should note customer names on large simultaneous sales.
2. **Demo Mode:** Ships with known demo credentials (`owner123`, `cashier123`) for evaluator review; production enforces 32-character random secrets (`DEMO_MODE=0`).
3. **Screening Aid:** PPL is a real-time operational screening aid, not a replacement for official bank statements.
