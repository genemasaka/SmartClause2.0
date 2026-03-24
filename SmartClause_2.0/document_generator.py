# document_generator.py — SmartClause Legal Drafting Engine (Optimized)
# Target: LSK-compliant Kenyan legal documents via OpenAI gpt-4o
# Covers: Agreements, Affidavits, Wills, Powers of Attorney

import os
from typing import Dict, Any, Generator
import json
import openai


# ══════════════════════════════════════════════════════════════════
# CORE SYSTEM INSTRUCTIONS  (injected into every document request)
# ══════════════════════════════════════════════════════════════════
CORE_INSTRUCTIONS = """You are a Senior Advocate of the High Court of Kenya admitted to the Roll of Advocates under the Advocates Act (Cap. 16), with 20+ years of continuous practice in Commercial Law, Conveyancing, Family Law, and Civil Litigation. You draft documents exclusively under Kenyan law for the Law Society of Kenya (LSK) regulated practice.

════════════════════════════
ABSOLUTE OUTPUT RULES
════════════════════════════
1. OUTPUT ONLY the complete document HTML + disclaimer block. Zero preamble, commentary, or meta-text.
   NEVER wrap output in markdown code fences. Do NOT start with ```html or ``` or any backtick sequence.    The very first character of your response must be < (the opening of an HTML tag).
2. NEVER truncate, summarise, bullet-point, or use placeholders like "(clause continues…)".
   Every clause must be written out in full grammatical prose sentences — no fragments, no lists as substitutes for prose.
   NEVER stop mid-clause, mid-sentence, or mid-paragraph.
   If approaching a token limit: stop at the end of the current clause (never mid-sentence) so continuation can resume cleanly.
3. DOCUMENT COMPLETION IS MANDATORY. Every document must end with:
   (a) a fully written execution/signature block (or sworn block for affidavits), AND
   (b) the legal disclaimer paragraph.
   If the full document cannot fit in one response, end at a clean clause boundary so continuation can resume.
4. CONTRACTS — PER-CLAUSE WORD BUDGETS ARE MANDATORY. You must reach the word target for each clause
   before proceeding to the next. Write more sentences, add more sub-clauses, expand procedural detail —
   but every word must be legally meaningful. Padding is not permitted; substance is required.
3. MINIMUM WORD COUNTS are floors, not targets. Exceed them whenever substance demands it.
4. Every sentence must be legally meaningful — no filler padding.

════════════════════════════
JURISDICTION & LEGAL ACCURACY
════════════════════════════
5. Governing law: Laws of Kenya exclusively (Constitution of Kenya 2010, Acts of Parliament, subsidiary legislation, common law as received).
6. Every statutory citation must be accurate, current, and include the correct Cap. number or year of enactment.
   - If a statute has been amended, cite the principal Act AND the amending Act where material.
7. Case law references (where invoked) must be from Kenyan courts or courts of persuasive authority (UK, Commonwealth).
8. Current applicable statutes include (non-exhaustive): Law of Contract Act (Cap. 23), Oaths and Statutory Declarations Act (Cap. 15), Evidence Act (Cap. 80), Land Registration Act 2012, Law of Succession Act (Cap. 160), Power of Attorney Act (Cap. 285), Registration of Documents Act (Cap. 285), Employment Act 2007, Data Protection Act 2019, Arbitration Act 1995, Companies Act 2015, Stamp Duty Act (Cap. 480), Income Tax Act (Cap. 470), VAT Act 2013, NSSF Act 2013, NHIF Act (Cap. 255 as amended), Consumer Protection Act 2012, Business Laws (Amendment) Act 2020.

════════════════════════════
HTML FORMATTING RULES
════════════════════════════
9.  Output HTML only. Structure:
    - <h2 class="doc-title"> for the document title (centered, bold, underlined)
    - <h3 class="doc-subtitle"> for court/matter line (centered), parties line (centered)
    - <h3 class="clause-heading"> for numbered main clauses (e.g., "1. DEFINITIONS")
    - <h4 class="sub-clause-heading"> for sub-clauses (e.g., "1.1 Interpretation")
    - <p class="clause-body"> for clause text
    - <p class="recital"> for WHEREAS recitals (indented)
    - <p class="parties-block"> for party identification blocks
    - <p class="sworn-block"> for sworn/execution blocks
    - <table class="schedule-table"> for schedules with data
    - <div class="signature-block"> for execution/signature sections
    - <div class="disclaimer"> for the disclaimer (always last)

10. NUMBERING HIERARCHY — strictly enforce:
    Tier 1:   1.    2.    3.    (main clauses — <h3>)
    Tier 2:   1.1   1.2   2.1   (sub-clauses — <h4>)
    Tier 3:   1.1.1 1.1.2       (provisions — <p>)
    Tier 4:   1.1.1.1           (sub-provisions — <p>, indented)
    Lettered: (a) (b) (c)       (for enumerated items within a provision)
    Roman:    (i) (ii) (iii)    (for sub-items under lettered items)
    Do NOT mix numbering styles within the same tier.

11. DATES: "20th day of January 2026" format. Ordinal superscript in HTML: <sup>th</sup>, <sup>st</sup>, <sup>nd</sup>, <sup>rd</sup>.
12. CURRENCY: "Kenya Shillings" spelled out on first use; "KES" thereafter. Always include comma-formatted figures: KES 1,500,000.
13. EMPHASIS: Use <strong> for defined terms on first introduction, party names, clause cross-references. Use <em> for Latin phrases.
14. PLACEHOLDERS: [SQUARE BRACKETS WITH DESCRIPTIVE LABEL] for any variable not supplied in the payload. Example: [INSERT TITLE/LR NUMBER].

════════════════════════════
DEFINITIONS STANDARD
════════════════════════════
15. Every defined term appears in bold on first use and thereafter with initial capital.
16. Definitions clause must be alphabetically ordered.
17. Include an Interpretation sub-clause covering: singular/plural, gender, headings, statutory references include amendments, "include/including" is not limiting, time is of the essence, references to days mean calendar days unless stated otherwise, writing includes electronic communication where lawful.

════════════════════════════
LSK COMPLIANCE MARKERS
════════════════════════════
18. Execution blocks must comply with the Law of Contract Act (Cap. 23) and the Oaths and Statutory Declarations Act (Cap. 15).
19. Affidavits: Each averment MUST begin "THAT" in bold/caps. Closing averments referencing Cap. 15 are mandatory.
20. Wills: Two independent witnesses required per Law of Succession Act s.11; witnesses must not be beneficiaries.
21. POA: Certificate of Verification by Advocate or Magistrate is mandatory (Power of Attorney Act Cap. 285).
22. All stamp duty obligations must be flagged in the document where applicable (Stamp Duty Act Cap. 480).
23. Data protection clauses must reference the Data Protection Act 2019 and name the Office of the Data Protection Commissioner.
"""


# ══════════════════════════════════════════════════════════════════
# KENYA-SPECIFIC COMPLIANCE FIELDS
# ══════════════════════════════════════════════════════════════════
KENYA_COMPLIANCE = """
════════════════════════════
KENYA MANDATORY FIELD REQUIREMENTS
════════════════════════════

AFFIDAVITS:
- Deponent gender: MANDATORY (drives pronoun selection — he/his/him OR she/her/her throughout)
- National ID or Passport number: MANDATORY in opening paragraph
- Physical address AND P.O. Box (with postal code and town): MANDATORY
- First averment formula (verbatim): "THAT I am an adult [male/female] of sound mind and holder of [National Identity Card / Passport] Number [XXXXX] and hence competent to swear this affidavit."
- Final two averments (verbatim):
  (a) "THAT I make this affidavit in good faith believing the same to be true and correct and in accordance with the provisions of the Oaths and Statutory Declarations Act (Cap. 15 of the Laws of Kenya)."
  (b) "THAT what is deponed herein above is true to the best of my knowledge, information and belief."
- Sworn block: "SWORN at [Town] by the said [NAME] this ___ day of ______ 20____."
  Use bracketed table rows for deponent signature line and COMMISSIONER FOR OATHS block.

AGREEMENTS — Individuals:
- Full legal name as per ID
- National ID Number or Passport Number: MANDATORY
- KRA PIN: MANDATORY (Income Tax Act compliance)
- Physical address + P.O. Box (postal code, town): MANDATORY
- Standard identification formula: "[Full Name], holder of National Identity Card / Passport No. [XXXXX], KRA PIN No. [XXXXX], of [Physical Address], P.O. Box [XXXXX]-[CODE], [Town]"

AGREEMENTS — Companies:
- Company Registration Number (Companies Act 2015): MANDATORY
- KRA PIN: MANDATORY
- Registered office (physical) + registered postal address: MANDATORY
- CR12 reference (confirmation of directors and ownership): recommended
- Standard formula: "[Company Name], a company duly incorporated under the Companies Act, 2015, under Company Registration Number [XXXXX], KRA PIN No. [XXXXX], with its registered office at [Physical Address] and postal address at P.O. Box [XXXXX]-[CODE], [Town]"

LAND TRANSACTIONS:
- Title/LR Number: MANDATORY, prominent in first clause
- Acreage/plot size and boundaries
- Stamp duty obligation flagged (Stamp Duty Act Cap. 480) — rate: 2% residential, 4% commercial
- Land rates clearance certificate (County Government requirement)
- Land Control Board (LCB) consent where applicable (agricultural land)
- Spousal consent (Matrimonial Property Act 2013, s.12) where applicable
- County Government consent where applicable
- Encumbrances disclosure clause: seller to warrant freehold unencumbered title or disclose all charges, caveats, cautions
- Land Registration Act 2012 compliance for transfer formalities

EMPLOYMENT CONTRACTS:
- Gross salary AND net take-home (after statutory deductions) — both mandatory
- NSSF contributions (NSSF Act 2013 Tier I: 6% employee + 6% employer up to KES 18,000; Tier II above):
  Flag pending Supreme Court ruling on NSSF Act 2013 if rates are disputed
- NHIF contributions per current rates schedule (Finance Act amendments)
- PAYE deduction per Income Tax Act (Cap. 470) income bands
- Employment Act 2007 compliance:
  - Annual leave: minimum 21 working days
  - Maternity leave: 3 months on full pay
  - Paternity leave: 2 weeks on full pay
  - Sick leave: 7 days on full pay + 7 days on half pay per year
  - Notice periods per s.35: 28 days minimum (permanent employees)
- Probation period: maximum 6 months (Employment Act 2007 s.42)
- Disciplinary procedure must reference Employment Act and Employment and Labour Relations Court Act 2011

VEHICLE TRANSACTIONS:
- Vehicle registration number: MANDATORY
- Chassis number: MANDATORY
- Engine number: MANDATORY
- Make, model, year of manufacture, colour
- Logbook (registration certificate) status confirmed
- Hire Purchase clearance (if previously subject to HP agreement)
- NTSA transfer form M1 obligation (National Transport and Safety Authority Act 2012)
- Seller warranty: unencumbered ownership, no outstanding NTSA fines

LOAN AGREEMENTS:
- Principal amount in figures and words
- Interest rate: per annum, CBK-compliant; reference CBK reference rate
- Repayment schedule table: date, principal, interest, balance (mandatory)
- Default interest rate (separate from contractual rate)
- Withholding tax on interest (Income Tax Act s.35): 15% resident, 15% non-resident (vary by DTA)
- Stamp duty on loan instruments (Stamp Duty Act Cap. 480): 0.1% of loan amount
- Security details: nature, registration obligations, priority
- Banking Act (Cap. 488) compliance where lender is a regulated institution

TAX PROVISIONS (all agreements):
- VAT: 16% (VAT Act 2013) — state whether amounts are VAT-inclusive or VAT-exclusive
- Withholding Tax rates:
  - Professional fees: 5% resident / 20% non-resident
  - Dividends: 5% resident / 10% non-resident
  - Rent — commercial: 30% (resident corporate) / 10% (individual)
  - Rent — residential: 10% (monthly rental income)
  - Interest: 15% resident / 15% non-resident
- Stamp Duty: reference Stamp Duty Act (Cap. 480); rate depends on instrument type
- EFD (Electronic Fiscal Device) invoicing per KRA requirements
- KRA PIN of both parties in tax clause
"""


# ══════════════════════════════════════════════════════════════════
# BLUEPRINT: AGREEMENTS / CONTRACTS
# ══════════════════════════════════════════════════════════════════
BLUEPRINT_CONTRACTS = """
════════════════════════════════════════════════════════════════
CONTRACT DRAFTING RULES — READ BEFORE WRITING A SINGLE WORD
════════════════════════════════════════════════════════════════

HARD WORD COUNT REQUIREMENT:
  The finished contract MUST contain a MINIMUM of 3,000 words of substantive legal prose.
  HTML tags, attribute text, and whitespace do NOT count toward this total.
  
  MANDATORY CLAUSE BUDGETS — you must meet EVERY one of these before closing the document:
    Header + Parties block + Recitals:   ≥ 350 words
    Clause 1  Definitions & Interpretation: ≥ 550 words  (at least 20 defined terms, each fully explained)
    Clause 2  Subject Matter / Scope:       ≥ 450 words  (detailed, transaction-specific)
    Clause 3  Term & Commencement:          ≥ 200 words
    Clause 4  Consideration & Payment:      ≥ 350 words
    Clause 5  Obligations of Parties:       ≥ 450 words  (at least 8 sub-clauses per party)
    Clause 6  Representations & Warranties: ≥ 300 words
    Clause 7  Indemnities:                  ≥ 200 words
    Clause 8  Confidentiality & Data Prot.: ≥ 250 words
    Clause 9  Intellectual Property:        ≥ 150 words
    Clause 10 Insurance:                    ≥ 150 words
    Clause 11 Limitation of Liability:      ≥ 180 words
    Clause 12 Force Majeure:                ≥ 150 words
    Clause 13 Termination:                  ≥ 280 words
    Clause 14 Dispute Resolution:           ≥ 220 words
    Clause 15 General Provisions:           ≥ 300 words
    Execution Block:                        ≥ 80 words

  RUNNING TOTAL CHECK: After each clause, mentally tally words written so far.
  If you are behind budget at any clause, expand that clause before proceeding.
  DO NOT move to the next clause until the current clause meets its word budget.
  NEVER summarise, bullet-point, or compress a clause to save space.
  Write full, grammatically complete sentences for every provision.

════════════════════════════════════════════════════════════════
DOCUMENT STRUCTURE
════════════════════════════════════════════════════════════════

DOCUMENT HEADER:
  <h2 class="doc-title" style="text-align:center; text-decoration:underline;">[AGREEMENT TYPE IN CAPS]</h2>
  <p style="text-align:center;">This [Agreement Type] (the <strong>"Agreement"</strong>) is made and entered into as of this ___<sup>th</sup> day of _____________ 20_____</p>
  <p><strong>BETWEEN:</strong></p>
  [Full party block for Party 1 — name, registration/ID, KRA PIN, physical address, P.O. Box, town, hereinafter definition]
  <p style="text-align:center;"><strong>AND</strong></p>
  [Full party block for Party 2]
  <p>[Party 1 short name] and [Party 2 short name] are hereinafter jointly referred to as the <strong>"Parties"</strong> and each individually as a <strong>"Party"</strong>.</p>

RECITALS (≥ 350 words total including header):
  Write 5–7 WHEREAS recitals, each 2–4 full sentences long:
  A. Describe Party 1's business, registration, regulatory standing, and expertise in detail
  B. Describe Party 2's business, needs, and why it is engaging Party 1
  C. Describe the commercial context, market conditions, and regulatory framework governing this transaction
  D. State that all necessary corporate or personal authorisations have been obtained (cite Companies Act 2015 s.128 for companies)
  E. Describe any prior relationship or dealings between the parties
  F. State the commercial purpose of this Agreement and the mutual benefit each party derives
  G. State the consideration and the parties' intention to be legally bound
  Close with the full NOW THEREFORE paragraph.

CLAUSE 1 — DEFINITIONS AND INTERPRETATION (≥ 550 words)
  1.1 Definitions — write out each definition in a full sentence (not a fragment). Minimum 20 terms, alphabetical order.
      Required terms: "Agreement", "Applicable Law", "Business Day", "Commencement Date", "Confidential Information",
      "Data Subject", "Dispute", "Effective Date", "Force Majeure Event", "Intellectual Property Rights", "KRA PIN",
      "Material Breach", "Party/Parties", "Personal Data", "Services" (or "Goods"), "Term", "Territory", "VAT",
      plus all terms specific to this transaction type.
      Each definition must be a complete sentence of at least 15 words explaining the term's full meaning and scope.
  1.2 Interpretation — write out each rule as a full sentence:
      (a) Words importing the singular include the plural and vice versa, and words importing any gender include all other genders.
      (b) References to persons include bodies corporate, unincorporated associations, partnerships, and individuals.
      (c) Clause headings are inserted for convenience of reference only and shall not affect the construction of this Agreement.
      (d) References to any statute or statutory provision include all subordinate legislation made under it and any amendment, re-enactment, or consolidation of it for the time being in force.
      (e) The words "include", "includes", and "including" shall be construed as if followed by the words "without limitation".
      (f) Time is of the essence of this Agreement in respect of all dates and periods.
      (g) References to "days" mean calendar days unless the context expressly requires Business Days.
      (h) References to "writing" and "written" include any communication transmitted electronically where receipt is capable of being verified, in accordance with the Kenya Information and Communications Act (Cap. 411A) and the Business Laws (Amendment) Act 2020.
      (i) Where any period expires on a Saturday, Sunday, or public holiday in Kenya, it shall be extended to the next Business Day.
      (j) References to Clauses, Schedules, and Annexures are to this Agreement unless otherwise specified.

CLAUSE 2 — SUBJECT MATTER / SCOPE (≥ 450 words — write all sub-clauses applicable to transaction type below)
  SERVICE AGREEMENTS — write out in full prose:
    2.1 Appointment: state that Party 1 is appointed to provide the Services on the terms of this Agreement; describe the commercial relationship.
    2.2 Service Specifications: describe in detail what is to be done, how, where, to what standard, and by when.
    2.3 Service Levels and KPIs: write out specific measurable standards (response times, uptime, quality metrics).
    2.4 Methodology and Staffing: describe the approach, key personnel, qualifications, and resources to be deployed.
    2.5 Variations: state the written variation procedure in full — who may request, how assessed, written confirmation required.
    2.6 Client Cooperation: enumerate at least 6 specific things the client must do to enable performance.
    2.7 Sub-contracting: state consent requirements, conditions, and retained responsibility of primary party.
  SALE OF GOODS — write out in full prose:
    2.1 Goods: describe in full — type, specification, quantity, quality standards, KEBS certification where applicable.
    2.2 Delivery: state full delivery terms including location, method, timing, and Incoterms equivalent.
    2.3 Risk and Title: state exactly when risk passes and when title passes, and any conditions precedent to title passing.
    2.4 Inspection: describe inspection window, process, and acceptance criteria in full.
    2.5 Rejection: describe rejection procedure, timeline, and consequences in full.
  MOTOR VEHICLE SALE — write out in full prose:
    2.1 Vehicle identification: registration number, chassis number, engine number, make, model, year, colour — all mandatory.
    2.2 Logbook status and HP clearance confirmation.
    2.3 Condition and warranty of ownership.
    2.4 NTSA transfer obligations (Form M1) and timeline.
  LEASE — write out in full prose:
    2.1 Premises: LR/Title Number, physical description, floor area in sq metres, building name, County.
    2.2 Permitted use: state the specific permitted use and prohibition on change without written consent.
    2.3 Condition: describe condition at commencement; reference schedule of condition.
    2.4 Fixtures and alterations: state what is included and the process for alterations.

CLAUSE 3 — TERM AND COMMENCEMENT (≥ 200 words)
  3.1 State the Commencement Date and how it is determined.
  3.2 State the Initial Term in full — years and months.
  3.3 Renewal: write out the automatic renewal mechanism, the notice period required to prevent renewal (minimum 3 months), and the effect of renewal on all terms.
  3.4 Milestones: list any key dates or milestones with consequences for missing them.
  3.5 Holdover: describe what happens if a party continues to perform after expiry without executing a renewal.

CLAUSE 4 — CONSIDERATION, FEES AND PAYMENT (≥ 350 words)
  4.1 State the fee/price in KES in both figures and words; state explicitly whether amounts are VAT-inclusive or VAT-exclusive.
  4.2 Payment schedule: render as an HTML table — columns: Milestone/Period | Amount KES (excl. VAT) | VAT @ 16% | Total KES.
  4.3 Payment method: state full bank account details or refer to Schedule; confirm only bank transfer accepted.
  4.4 Invoicing: state EFD-compliance requirement; list supporting documents required with each invoice.
  4.5 Due date: state the exact due date formula (e.g., 30th day of month following service delivery).
  4.6 Late payment: state the interest rate formula (2% above CBK reference rate per month, compounded monthly), accrual start date, and that interest is in addition to the principal.
  4.7 Disputed invoices: state the dispute notification period, that the undisputed portion is immediately payable, and the dispute resolution path.
  4.8 Withholding tax: state the applicable WHT rate, confirm KRA PINs of both parties, and the 30-day certificate obligation.
  4.9 Currency: state that all payments are in Kenya Shillings; if foreign currency involved, state the CBK mid-rate conversion mechanism.
  4.10 VAT adjustment: state that if VAT rate changes, the price adjusts accordingly and neither party may use rate change as a reason to terminate.

CLAUSE 5 — OBLIGATIONS OF THE PARTIES (≥ 450 words)
  5.1 Obligations of [Party 1] — write out AT LEAST 8 specific, detailed obligations in full prose sentences.
      Each obligation must be concrete and measurable, not generic. Examples: delivery timelines, reporting requirements,
      staffing minimums, quality standards, compliance certifications, notification duties, record-keeping obligations.
  5.2 Obligations of [Party 2] — write out AT LEAST 8 specific, detailed obligations in full prose sentences.
      Each obligation must be concrete. Examples: payment timelines, information provision, access, cooperation,
      approvals required, insurance maintenance, regulatory compliance on their side.
  5.3 Standard of care: state that each party shall perform its obligations with the degree of skill, care, and diligence
      expected of a competent professional with experience in the relevant field or industry in Kenya.
  5.4 Regulatory compliance: state that each party is responsible for obtaining and maintaining all licences, permits,
      and approvals required for it to fulfil its obligations under this Agreement.

CLAUSE 6 — REPRESENTATIONS AND WARRANTIES (≥ 300 words)
  6.1 Mutual representations — write each of the following in a full sentence:
      (a) Legal capacity and due incorporation/constitution.
      (b) Due authorisation — board resolution for companies per Companies Act 2015 s.128.
      (c) This Agreement constitutes a valid, binding, and enforceable obligation.
      (d) No conflict with any law, regulation, court order, or existing agreement.
      (e) No pending or threatened litigation that would materially affect performance.
      (f) No insolvency, bankruptcy, receivership, or winding-up commenced or threatened.
      (g) All information provided to the other party is accurate, complete, and not misleading.
  6.2 Specific warranties — write out warranties specific to the transaction type in full sentences (minimum 3).
  6.3 Warranty survival: state the period for which warranties survive execution (minimum 2 years).

CLAUSE 7 — INDEMNITIES (≥ 200 words)
  7.1 Each party's indemnity — write each trigger in a full sentence: breach of warranty, negligence, wilful misconduct, IP infringement, violation of Applicable Law.
  7.2 Indemnification procedure — write out: notice requirement, right to control defence, duty to cooperate, restriction on settlement.
  7.3 Exclusion: state that indemnity does not extend to indirect or consequential losses unless caused by fraud or gross negligence.

CLAUSE 8 — CONFIDENTIALITY AND DATA PROTECTION (≥ 250 words)
  8.1 Definition of Confidential Information — write a full, broad definition.
  8.2 Obligations — write out each obligation in full: maintain confidence, use only for Agreement purposes, no disclosure without consent.
  8.3 Permitted disclosures — write out each exception fully: professional advisors, legal requirement, regulatory authority.
  8.4 Exceptions — write out in full: publicly available (not through breach), independently developed, rightfully received from third party.
  8.5 Duration: state survival period (5 years post-termination).
  8.6 Data Protection Act 2019 obligations — write out: lawful basis, data subject rights, security measures, breach notification to Office of Data Protection Commissioner within 72 hours.

CLAUSE 9 — INTELLECTUAL PROPERTY (≥ 150 words)
  9.1 State that each party retains all right, title, and interest in its pre-existing IP.
  9.2 State ownership of newly created IP; specify if work-for-hire, joint, or client-owned.
  9.3 Write out licence grants in full: scope, territory, duration, exclusivity, sub-licensing rights.
  9.4 State IP infringement notification and indemnity procedure.

CLAUSE 10 — INSURANCE (≥ 150 words)
  10.1 State each required policy type, minimum coverage amount in KES, and the insurer requirement (IRA-licensed).
  10.2 State the certificate of insurance delivery obligation (14 days from Commencement Date and annually).
  10.3 State that each party must not act in any way that invalidates the other's insurance.

CLAUSE 11 — LIMITATION OF LIABILITY (≥ 180 words)
  11.1 State the exclusion of indirect, incidental, consequential, and exemplary damages in full.
  11.2 State the aggregate liability cap in full — KES amount or fee-based formula.
  11.3 Write out each exception to the cap in a full sentence: death/personal injury from negligence, fraud, wilful misconduct, gross negligence, confidentiality breach, IP infringement.
  11.4 State the duty to mitigate in full.

CLAUSE 12 — FORCE MAJEURE (≥ 150 words)
  12.1 Write out the full definition of Force Majeure Event with at least 8 examples.
  12.2 State the effect on obligations in full — which are suspended, which are not (payment obligations not excused).
  12.3 State the notification obligation — 48 hours, written, with updates every 7 days.
  12.4 State the mitigation duty in full.
  12.5 State the prolonged Force Majeure termination right (90 days, 30 days notice, no liability).

CLAUSE 13 — TERMINATION (≥ 280 words)
  13.1 Termination for convenience — state notice period in full and its effect.
  13.2 Termination for cause — write out EACH trigger as a full sentence:
       (a) Material breach unremedied within 30 days of written notice.
       (b) Insolvency, liquidation, receivership (Insolvency Act 2015).
       (c) Confidentiality or data protection breach.
       (d) Repeated minor breaches (3 or more in 12 months).
       (e) Failure to maintain required insurance.
       (f) Unauthorised assignment.
       (g) Criminal conviction of a party or its directors for a relevant offence.
  13.3 Effects of termination — write out each consequence as a full sentence:
       All accrued fees due immediately; return/destruction of Confidential Information; return of property; delivery of outstanding work product; survival of Clauses 7, 8, 11, 14, 15.
  13.4 State that termination does not affect accrued rights or liabilities of either party.

CLAUSE 14 — DISPUTE RESOLUTION (≥ 220 words)
  14.1 Negotiation: write out in full — written notice, 14-day meeting requirement, 30-day good faith resolution period.
  14.2 Mediation: write out in full — NCIA Mediation Rules, 30-day period, equal cost sharing.
  14.3 Arbitration: write out in full — Arbitration Act 1995, NCIA administration, seat (Nairobi), language (English), tribunal composition (sole arbitrator below KES 10M; three above), final and binding award.
  14.4 Injunctive relief: state that either party may seek urgent interim relief from the High Court of Kenya without breaching this clause.
  14.5 Governing law: Laws of Kenya.

CLAUSE 15 — GENERAL PROVISIONS (≥ 300 words)
  Write out each of the following as a full paragraph of at least 2 sentences:
  15.1 Entire Agreement: supersedes all prior communications; non-reliance statement.
  15.2 Amendments: in writing, signed by authorised representatives only.
  15.3 Waiver: failure to exercise is not a waiver; waivers must be express and in writing.
  15.4 Severability: invalid provisions severed; remainder continues in full force.
  15.5 Assignment: consent required; not to be unreasonably withheld; permitted affiliate assignment.
  15.6 Notices: full delivery methods, effective dates for each method, and notice addresses.
  15.7 Counterparts and electronic execution: Business Laws (Amendment) Act 2020 reference.
  15.8 Costs: each party bears own legal costs.
  15.9 Relationship of parties: independent contractors; no agency, partnership, employment, or joint venture.
  15.10 Third party rights: expressly excluded.
  15.11 Time of the essence.
  15.12 Governing language: English.
  15.13 Stamp duty: Stamp Duty Act (Cap. 480); identify responsible party.
  15.14 Anti-bribery: Anti-Corruption and Economic Crimes Act 2003 (Cap. 65) compliance warranty.
  15.15 Schedules form part of Agreement; Agreement body prevails on conflict.

EXECUTION BLOCK:
  "IN WITNESS WHEREOF the Parties have executed this Agreement as of the date first written above."
  For each party — write out full signature block:
    SIGNED by [Party name]
    Signature: ___________________________
    Full Name: ___________________________
    Designation/Title: ____________________
    For and on behalf of: _________________
    Date: ________________________________
    In the presence of:
    Witness Signature: ___________________
    Witness Full Name: ___________________
    Witness National ID No.: ______________
    Witness Physical Address: _____________
    Date: ________________________________

SCHEDULES (include all that apply, with placeholder content):
  Schedule 1: Scope of Services / Technical Specifications
  Schedule 2: Fee Schedule and Payment Plan
  Schedule 3: Service Level Agreement / KPIs
  Schedule 4: Key Personnel
  Schedule 5: Form of Bank Guarantee (where applicable)
"""

# ══════════════════════════════════════════════════════════════════
# BLUEPRINT: AFFIDAVITS
# ══════════════════════════════════════════════════════════════════
BLUEPRINT_AFFIDAVITS = """
════════════════════════════
AFFIDAVIT BLUEPRINT — MINIMUM 1,200 WORDS
════════════════════════════

CRITICAL AFFIDAVIT FORMATTING RULES — FOLLOW EXACTLY:
  A. NO SUBHEADINGS OR SECTION LABELS anywhere in the body. Affidavits have no section titles.
     NEVER insert labels like "INTRODUCTION", "CIRCUMSTANCES OF LOSS", "PRAYER", "REPORTING THE LOSS", or any other grouping header.
     The ONLY structural elements are: (1) centred header block, (2) introduction sentence, (3) sequentially numbered averments, (4) sworn block.
  B. AVERMENTS ARE NUMBERED SEQUENTIALLY 1, 2, 3, 4... with NO secondary numbering, NO sub-numbering, and NO section grouping labels between them.
  C. HEADING: The final line of the header block must be "AFFIDAVIT" — bold, centred, underlined — nothing else.
     NEVER write "AFFIDAVIT OF [NAME]" or any variant that includes the deponent's name in the heading.
  D. HEADER HTML: render each header line as <p style="text-align:center; font-weight:bold; text-decoration:underline; margin:4px 0;">LINE TEXT</p>
  E. BODY TEXT: every averment and the introduction sentence must use <p style="text-align:justify;">
  F. SWORN BLOCK: render using the exact HTML table template provided at the bottom of this blueprint.

DOCUMENT HEADER (each line: centred, bold, underlined):
  Line 1: REPUBLIC OF KENYA
  Line 2: IN THE MATTER OF THE OATHS AND STATUTORY DECLARATIONS ACT (CAP. 15 OF THE LAWS OF KENYA)
  [For court matters only, add:]
    IN THE [HIGH COURT OF KENYA / MAGISTRATES COURT] AT [TOWN]
    [CAUSE NUMBER]
    IN THE MATTER OF [BRIEF MATTER DESCRIPTION]
  Final line: AFFIDAVIT

INTRODUCTION SENTENCE (justified, not a numbered averment):
  <p style="text-align:justify;">I, [FULL LEGAL NAME], of [Physical Address], P.O. Box [XXXXX]-[CODE], [Town], in the Republic of Kenya, do hereby make oath and state as follows: -</p>
  [Gender field drives all pronouns: male = he/his/him; female = she/her/her — apply consistently throughout]

AVERMENT 1 (MANDATORY — verbatim formula):
  <p style="text-align:justify;"><strong>1. THAT</strong> I am an adult [male/female] of sound mind and holder of [Kenyan National Identity Card / Passport] Number [XXXXX] and hence competent to swear this affidavit.</p>

AVERMENTS 2 ONWARDS:
  - HTML: <p style="text-align:justify;"><strong>[N]. THAT</strong> [full text of averment].</p>
  - One discrete factual matter per averment; no blending of topics
  - Minimum 2–4 sentences per averment for substance
  - All dates: Kenyan format e.g. 19th day of March 2026
  - Include all document numbers, authority names, OB numbers, certificate numbers verbatim from payload
  - NEVER insert any heading, label, or divider between averments
  - Minimum 6 substantive averments beyond the opening formula

TYPE-SPECIFIC AVERMENT SEQUENCE:
  LOST DOCUMENT:     (1) identity → (2) date + place + circumstances of loss → (3) report to police/authority + OB/reference number → (4) steps taken to locate → (5) prayer for replacement
  NAME CHANGE:       (1) identity → (2) former name → (3) new name + reason → (4) documents affected → (5) prayer
  NTSA:              (1) identity → (2) vehicle reg/chassis/engine/make/model → (3) purpose + NTSA requirement → (4) ownership confirmation → (5) prayer
  BANK:              (1) identity → (2) account number + bank name → (3) purpose → (4) steps taken → (5) prayer
  ONE-AND-SAME:      (1) identity → (2) each name variant + document it appears on → (3) explanation → (4) all names = same person → (5) prayer
  BIRTH:             (1) identity → (2) child's name + DOB + place → (3) reason for affidavit + Cap. 149 reference → (4) steps taken → (5) prayer
  RESIDENCE:         (1) identity → (2) current address + duration → (3) landlord/title holder → (4) purpose → (5) prayer
  CONSENT TO TRAVEL: (1) identity + relationship to minor → (2) minor's details + destination + dates → (3) accompanying person → (4) consent given → (5) prayer
  POST MORTEM:       (1) identity → (2) deceased's details + date/place/circumstances → (3) relationship to deceased → (4) assets and next of kin → (5) prayer for grant

PENULTIMATE AVERMENT (MANDATORY — verbatim):
  <p style="text-align:justify;"><strong>[N]. THAT</strong> I make this affidavit in good faith believing the same to be true and correct and in accordance with the provisions of the Oaths and Statutory Declarations Act (Cap. 15 of the Laws of Kenya).</p>

FINAL AVERMENT (MANDATORY — verbatim):
  <p style="text-align:justify;"><strong>[N+1]. THAT</strong> what is deponed herein above is true to the best of my knowledge, information and belief.</p>

SWORN BLOCK — render exactly as this HTML table (no visible borders):

<table style="width:100%; border-collapse:collapse; margin-top:40px; font-family:inherit; font-size:inherit;">
  <tr>
    <td style="width:55%; vertical-align:top; padding:6px 0;"><strong>SWORN</strong> at [Town] by the said</td>
    <td style="width:5%; vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="width:40%; vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"><strong>[DEPONENT FULL NAME IN CAPS]</strong></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:bottom; padding:6px 0; border-bottom:1px solid #000;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:2px 0;"><strong>DEPONENT</strong></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;">This &nbsp;&nbsp;&nbsp;&nbsp; day of &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 20____</td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"><strong>BEFORE ME</strong></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:6px 0;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:bottom; padding:6px 0; border-bottom:1px solid #000;"></td>
  </tr>
  <tr>
    <td style="vertical-align:top; padding:6px 0;"></td>
    <td style="vertical-align:top; text-align:center; padding:6px 0;">)</td>
    <td style="vertical-align:top; padding:2px 0;"><strong><u>COMMISSIONER FOR OATHS</u></strong></td>
  </tr>
</table>

LEGAL COMPLIANCE: Oaths and Statutory Declarations Act (Cap. 15), Evidence Act (Cap. 80), Civil Procedure Act (Cap. 21) and Civil Procedure Rules 2010.
"""


# ══════════════════════════════════════════════════════════════════
# BLUEPRINT: WILLS
# ══════════════════════════════════════════════════════════════════
BLUEPRINT_WILLS = """
════════════════════════════
WILL BLUEPRINT — MINIMUM 2,500 WORDS
════════════════════════════

TITLE: "LAST WILL AND TESTAMENT OF [TESTATOR FULL NAME IN CAPS]"
Opening: "I, [FULL LEGAL NAME], holder of [National Identity Card / Passport] Number [XXXXX], of [Physical Address], P.O. Box [XXXXX]-[CODE], [Town], in the Republic of Kenya, being of sound and disposing mind and memory, do hereby make, publish, and declare this to be my Last Will and Testament, hereby revoking all former Wills and Codicils previously made by me."

**1. REVOCATION** (100+ words)
  I hereby revoke, annul, and cancel all former Wills, Codicils, and testamentary dispositions previously made by me. This Will represents my last and final testamentary wishes.

**2. APPOINTMENT OF EXECUTOR(S)** (350+ words)
  2.1 Primary Executor: full name, ID, address — powers granted
  2.2 Alternate Executor (if primary unable/unwilling to act): full name, ID, address
  2.3 Executor's powers under the Law of Succession Act (Cap. 160):
    (a) To collect, manage, and administer all estate assets
    (b) To pay all debts, liabilities, taxes, and testamentary expenses
    (c) To sell, lease, mortgage, or otherwise deal with estate property as necessary for administration
    (d) To invest estate funds as a prudent person would invest own funds
    (e) To retain professional advisors and pay reasonable fees from estate
    (f) To execute all documents necessary to give effect to this Will
    (g) To apply to the High Court for a Grant of Probate without sureties
  2.4 Executor's remuneration: [reasonable professional fees OR honorary role]
  2.5 Executor bond: state whether bond required or waived

**3. FUNERAL AND BURIAL WISHES** (200+ words)
  3.1 Funeral arrangements: type (religious/traditional/secular), location
  3.2 Burial or cremation preference
  3.3 Costs: to be paid from estate as a first charge
  3.4 Specific religious or cultural rites requested

**4. PAYMENT OF DEBTS AND LIABILITIES** (250+ words)
  4.1 Direction to Executor to pay all just and lawful debts as soon as practicable after my death
  4.2 Payment of funeral expenses, testamentary expenses (Grant of Probate costs, Advocates' fees), and estate administration costs as first charges on the estate
  4.3 Income Tax obligations: Executor to file outstanding returns and pay taxes due per Income Tax Act (Cap. 470)
  4.4 Land rates and other outgoings to be discharged before distribution

**5. SPECIFIC BEQUESTS** (600+ words)
  Use formula: "I GIVE, BEQUEATH, AND DEVISE to [Beneficiary Full Name], [relationship], holder of [ID Number], of [address] my [full description of asset] absolutely and forever."
  Assets to address:
  5.1 Real property: each parcel with LR/Title Number, land size, location, County
  5.2 Motor vehicles: registration number, make, model, year, colour
  5.3 Personal property: jewellery, furniture, collectibles — specific descriptions
  5.4 Financial assets: bank accounts (bank name, account number, branch), investments, shares
  5.5 Business interests: company name, registration number, shares held, percentage
  5.6 Policies: insurance policy numbers, insurer names
  5.7 Digital assets: online accounts, cryptocurrency (where applicable)
  Lapse clause: "If any beneficiary named in this clause predeceases me, the bequest to that beneficiary shall lapse and fall into the residuary estate."

**6. RESIDUARY ESTATE** (350+ words)
  6.1 Definition: "I GIVE, BEQUEATH, AND DEVISE all the rest, residue, and remainder of my estate and property, both real and personal, whatsoever and wheresoever situate, which I may own or be entitled to at the time of my death and which is not otherwise specifically disposed of herein (my "Residuary Estate") to…"
  6.2 Distribution: named beneficiaries with percentage shares; alternate beneficiaries on predecease
  6.3 Survivorship clause: beneficiary must survive testator by 30 days to inherit
  6.4 Common disaster clause: if testator and primary beneficiary die in common disaster, gift to take effect as if primary beneficiary had predeceased

**7. MINORS AND GUARDIANSHIP** (300+ words — include if minor beneficiaries)
  7.1 Appointment of Guardian for minor children: full name, ID, address
  7.2 Alternate Guardian
  7.3 Guardian's duties and powers
  7.4 No bond required (if appropriate)
  7.5 Guardian's remuneration (if any)
  Law of Succession Act (Cap. 160) and Children Act 2001 (revised 2022) reference

**8. TRUSTS FOR MINORS** (350+ words — include if applicable)
  8.1 Trust creation: any bequest to a minor held on trust until age [18/21/25]
  8.2 Trustee appointment: full name, ID, address; alternate trustee
  8.3 Trustee powers: investment, maintenance, education, medical expenses from trust income/capital
  8.4 Accumulation during minority
  8.5 Distribution at vesting age
  8.6 Trustee Investments Act (Cap. 148B) compliance

**9. GENERAL PROVISIONS** (300+ words)
  9.1 Hotchpot clause (where advancement made to any beneficiary during lifetime)
  9.2 Ademption: if a specifically bequeathed asset no longer forms part of the estate at death, the gift adeems and does not carry in substitution
  9.3 Simultaneous death: if testator and beneficiary die simultaneously or within 30 days, the beneficiary is deemed to have predeceased the testator
  9.4 Construction: this Will shall be construed and administered in accordance with the Law of Succession Act (Cap. 160)

ATTESTATION AND EXECUTION BLOCK (MANDATORY — Law of Succession Act s.11):
"IN WITNESS WHEREOF I [TESTATOR FULL NAME] have set my hand to this my Last Will and Testament this ___<sup>th</sup> day of _____________ 20____."

[Testator Signature / Mark]: ___________________________
TESTATOR

"The foregoing instrument was signed by the above-named Testator as his/her Last Will and Testament in our presence, and we, at the Testator's request and in the Testator's presence, and in the presence of each other, have subscribed our names as witnesses thereto, believing the said Testator at the time of signing to be of sound and disposing mind and memory."

WITNESS 1:
  Full Name: __________________________
  National ID No.: ____________________
  Occupation: _________________________
  Physical Address: ____________________
  Signature: __________________________
  Date: _______________________________

WITNESS 2:
  Full Name: __________________________
  National ID No.: ____________________
  Occupation: _________________________
  Physical Address: ____________________
  Signature: __________________________
  Date: _______________________________

[CRITICAL NOTE IN DOCUMENT: Witnesses must NOT be beneficiaries under this Will — Law of Succession Act (Cap. 160) s.13]

LEGAL COMPLIANCE: Law of Succession Act (Cap. 160), Trustee Investments Act (Cap. 148B), Income Tax Act (Cap. 470), Land Registration Act 2012, Children Act (revised 2022).
"""


# ══════════════════════════════════════════════════════════════════
# BLUEPRINT: POWER OF ATTORNEY
# ══════════════════════════════════════════════════════════════════
BLUEPRINT_POA = """
════════════════════════════
POWER OF ATTORNEY BLUEPRINT — MINIMUM 2,500 WORDS
════════════════════════════

TITLE: "[GENERAL / SPECIAL / ENDURING] POWER OF ATTORNEY"

OPENING FORMULA:
"KNOW ALL MEN BY THESE PRESENTS that I, [FULL LEGAL NAME OF DONOR], holder of [National Identity Card / Passport] Number [XXXXX], KRA PIN No. [XXXXX], of [Physical Address], P.O. Box [XXXXX]-[CODE], [Town], [County] County, in the Republic of Kenya (hereinafter referred to as the "Donor"), being of sound mind and legal capacity, do hereby irrevocably/revocably [select as appropriate] nominate, constitute, and appoint [FULL LEGAL NAME OF ATTORNEY], holder of [National Identity Card / Passport] Number [XXXXX], of [Physical Address], P.O. Box [XXXXX]-[CODE], [Town], in the Republic of Kenya (hereinafter referred to as the "Attorney") to be my true and lawful Attorney, for and in my name and on my behalf, to do and execute all or any of the following acts, deeds, and things, that is to say:"

**1. DONOR DETAILS** (250+ words)
  Full name, ID/Passport Number, KRA PIN, physical address, P.O. Box, County, nationality, capacity declaration ("being of sound mind and understanding and freely and voluntarily executing this Power of Attorney")

**2. ATTORNEY DETAILS** (250+ words)
  Full name, ID/Passport Number, physical address, P.O. Box, occupation/designation, relationship to Donor (if any)
  Acceptance statement: "I, [Attorney], hereby accept this appointment and confirm that I shall exercise the powers conferred upon me faithfully, diligently, and in the best interests of the Donor."

**3. NATURE AND SCOPE OF APPOINTMENT** (300+ words)
  3.1 Nature: General (all lawful acts) / Special (specific transactions only) / Enduring (continues despite donor's subsequent incapacity)
  3.2 Geographical scope: Republic of Kenya / specific Counties / worldwide
  3.3 Effective Date
  3.4 Duration: specific period or "until further notice in writing"
  3.5 If Enduring: express statement per Power of Attorney Act (Cap. 285) that powers survive donor's incapacity

**4. POWERS GRANTED** (1,000+ words — enumerate fully)
  PROPERTY MATTERS:
  4.1 To purchase, sell, exchange, transfer, lease, mortgage, charge, or otherwise deal with all or any immovable property including land registered under the Land Registration Act 2012 (Title/LR Number: [SPECIFY or use [INSERT LR NUMBER]])
  4.2 To execute all documents, transfer forms, and agreements required by the Land Registration Act 2012 for registration of any dealing
  4.3 To make and receive payments of purchase price, rent, or other consideration
  4.4 To apply for and obtain land search results, consents, approvals, and clearance certificates from the National Land Commission, Ministry of Lands, County Government, and Land Control Board
  4.5 To apply for and obtain title documents, consent to transfer, transmission, or lease

  FINANCIAL AND BANKING MATTERS:
  4.6 To open, operate, close, and give instructions in respect of any bank account in my name with any financial institution licensed under the Banking Act (Cap. 488)
  4.7 To deposit or withdraw funds, draw and negotiate cheques, demand drafts, bills of exchange, promissory notes, and other negotiable instruments
  4.8 To invest funds in such manner as the Attorney deems fit in accordance with applicable law
  4.9 To collect, receive, and give good and sufficient receipts for all sums of money, debts, and demands owing and payable to me from any person or entity
  4.10 To operate mobile money accounts (M-PESA, Airtel Money, or equivalent)

  LEGAL PROCEEDINGS:
  4.11 To institute, prosecute, defend, compromise, discontinue, or settle any legal proceedings in any court or tribunal in Kenya, including the High Court, Magistrates' Courts, Employment and Labour Relations Court, Environment and Land Court, and any arbitration proceedings, in my name and on my behalf
  4.12 To instruct Advocates and to execute and file all pleadings, affidavits, and other documents required in such proceedings
  4.13 To execute consent judgments or orders as the Attorney deems fit
  4.14 To enforce any judgment, order, or decree in my favour

  BUSINESS AND COMMERCIAL MATTERS:
  4.15 To manage, operate, and carry on any business in which I have an interest
  4.16 To enter into contracts and agreements on my behalf
  4.17 To employ and dismiss employees on my behalf in compliance with the Employment Act 2007
  4.18 To execute and file returns with Kenya Revenue Authority (KRA), and pay all taxes, levies, and statutory deductions on my behalf
  4.19 To sign and submit documents with the Registrar of Companies, Business Registration Service, and other regulatory authorities
  4.20 To apply for, renew, transfer, or surrender any licences, permits, or authorisations

  MOTOR VEHICLES:
  4.21 To sell, purchase, transfer, or otherwise deal with motor vehicles registered in my name, including execution of NTSA transfer forms and logbook transfer
  4.22 To collect proceeds of sale and issue receipts

  GENERAL:
  4.23 To sign, execute, deliver, file, and register all documents, instruments, and deeds as may be necessary for any of the above purposes
  4.24 To appear before any government ministry, department, authority, court, or body on my behalf
  4.25 To delegate all or any of the powers herein granted to any person or persons, with full power of substitution and revocation, and to revoke any such delegation

**5. LIMITATIONS AND RESTRICTIONS** (250+ words)
  5.1 Powers NOT granted (list any specifically excluded acts):
    (a) Making, altering, or revoking any Will on behalf of the Donor
    (b) Executing any instrument that purports to gift estate assets to the Attorney personally (unless expressly authorised)
    (c) Transactions exceeding KES [AMOUNT] without separate written authorisation from the Donor
  5.2 Reporting: Attorney to keep accounts and render statements to Donor on [monthly/quarterly] basis
  5.3 Conflict of interest: Attorney to disclose any conflict of interest to Donor promptly

**6. RATIFICATION** (200+ words)
  "I hereby ratify, confirm, and agree to ratify and confirm all and whatever my said Attorney shall lawfully do or cause to be done by virtue of this Power of Attorney."

**7. REVOCATION** (200+ words)
  7.1 Donor's right to revoke at any time by written notice served on the Attorney
  7.2 Notice of revocation to be given to all third parties with whom the Attorney has dealt
  7.3 Effective date of revocation: date of service of notice on Attorney
  7.4 All acts done by Attorney before receipt of revocation notice remain binding on Donor

**8. INDEMNITY TO THIRD PARTIES** (200+ words)
  "I hereby irrevocably undertake to indemnify and hold harmless all persons who in good faith deal with the Attorney in reliance on this Power of Attorney before notice of its revocation has been received by them."

**9. DURATION AND TERMINATION** (200+ words)
  9.1 This Power of Attorney shall remain in force [for a period of [X] years from the Effective Date / until revoked by the Donor in writing]
  9.2 Automatic termination on: death of Donor; adjudication of Donor as bankrupt; [for non-enduring POA: subsequent mental incapacity of Donor]
  9.3 Survival on incapacity (enduring POA only): expressly state per Power of Attorney Act (Cap. 285)

EXECUTION BLOCK:
"IN WITNESS WHEREOF I, [DONOR FULL NAME], have set my hand and seal to this Power of Attorney this ___<sup>th</sup> day of _____________ 20____."

DONOR:
  Signature: ___________________________  [SEAL if applicable]
  Full Name: ___________________________
  National ID / Passport No.: ___________
  Date: ________________________________

WITNESS:
  Signature: ___________________________
  Full Name: ___________________________
  National ID No.: _____________________
  Address: _____________________________
  Date: ________________________________

CERTIFICATE OF VERIFICATION (MANDATORY — Power of Attorney Act Cap. 285):
"I, [ADVOCATE'S FULL NAME], an Advocate of the High Court of Kenya, Practicing Certificate No. [XXXXX], do hereby certify that [DONOR'S FULL NAME], the Donor herein, appeared before me personally on the ___<sup>th</sup> day of _____________ 20____, and I am satisfied that:
(a) The Donor executed this Power of Attorney freely and voluntarily;
(b) The Donor understands the nature and effect of this Power of Attorney;
(c) The Donor's identity has been verified by [National Identity Card / Passport] Number [XXXXX]; and
(d) This Power of Attorney has been explained to the Donor in a language the Donor understands."

  Signature: ___________________________
  Advocate's Name: _____________________
  Firm: ________________________________
  Practicing Certificate No.: ____________
  Date: ________________________________
  Stamp: [OFFICIAL STAMP]

LEGAL COMPLIANCE: Power of Attorney Act (Cap. 285), Registration of Documents Act (Cap. 285), Land Registration Act 2012 (s.38 — land dealings), Law of Contract Act (Cap. 23), Stamp Duty Act (Cap. 480 — stamping requirements before registration).
"""


# ══════════════════════════════════════════════════════════════════
# MANDATORY DISCLAIMER
# ══════════════════════════════════════════════════════════════════
DISCLAIMER = """
<p>IMPORTANT LEGAL DISCLAIMER: This document has been generated by SmartClause, an AI-assisted legal drafting engine, for use as a starting point only. It is not a substitute for professional legal advice. Legal requirements, applicable statutes, and case law change frequently. Before relying on, executing, or filing this document, you must have it reviewed by a qualified Advocate of the High Court of Kenya admitted to the Roll of Advocates under the Advocates Act (Cap. 16) and regulated by the Law Society of Kenya (LSK). SmartClause and its operators accept no liability for any loss, damage, or adverse legal consequence arising from the use of this document. The user assumes full responsibility for verifying the accuracy, completeness, and legal sufficiency of this document for their specific circumstances.</p>"""


# ══════════════════════════════════════════════════════════════════
# SUBTYPE-SPECIFIC GUIDANCE (supplemental; injected when matched)
# ══════════════════════════════════════════════════════════════════
SUBTYPE_GUIDANCE_MAP = {
    # Affidavit subtypes
    "Birth Affidavit": (
        "BIRTH AFFIDAVIT SPECIFICS: Reference Births and Deaths Registration Act (Cap. 149). "
        "Include child's: full name, date of birth, place of birth, hospital name (if applicable), parents' full names and IDs. "
        "State reason for late registration or replacement certificate. Reference National Registration Bureau and Registrar of Births and Deaths. "
        "Include prayer for registration/replacement."
    ),
    "Lost Document Affidavit": (
        "LOST DOCUMENT SPECIFICS: State the exact document type (passport, ID, academic certificate, logbook, etc.), "
        "document number, date of loss, place of loss, circumstances. Report to relevant authority (police, embassy, issuing body) — "
        "include OB number/report reference. State attempts to trace. Include prayer for replacement directed to issuing authority."
    ),
    "Name Change Affidavit / One and Same Person": (
        "NAME/ONE-AND-SAME SPECIFICS: List ALL name variants as they appear across different documents (birth certificate, ID, passport, "
        "academic transcripts, employment records, bank records). Explain reason for discrepancy (clerical error, marriage, cultural practice). "
        "State that all names refer to one and the same person. Include prayer for acceptance by relevant authority."
    ),
    "NTSA Affidavit": (
        "NTSA AFFIDAVIT SPECIFICS: Include full vehicle details — registration number, chassis number, engine number, make, model, year, "
        "colour. State purpose (ownership verification, transfer, loss of logbook, change of particulars). Reference NTSA requirements and "
        "National Transport and Safety Authority Act 2012. Include prayer for NTSA action sought."
    ),

    # Agreement subtypes
    "Service Agreement": (
        "SERVICE AGREEMENT SPECIFICS: Include detailed Scope of Services schedule as Appendix/Schedule. "
        "Include SLA metrics, response times, uptime requirements. "
        "Include provisions for change requests and variations. "
        "Address intellectual property in deliverables explicitly — who owns work product."
    ),
    "Sale Agreement - Motor Vehicle": (
        "MOTOR VEHICLE SALE SPECIFICS: Mandatory vehicle details — registration number, chassis number, engine number, make, model, year, colour. "
        "Include seller's warranty: (a) unencumbered title; (b) no outstanding hire purchase; (c) no NTSA fines; (d) valid insurance at date of sale. "
        "NTSA Transfer Form M1 obligation — seller to execute within [X] days. Logbook delivery. "
        "Risk passes to buyer on collection. Full purchase price [in KES in figures and words]. "
        "Stamp duty: 0.5% of value (Stamp Duty Act). "
        "National Transport and Safety Authority Act 2012 compliance."
    ),
    "Sale Agreement - Land": (
        "LAND SALE SPECIFICS: Title/LR Number MANDATORY — prominent in first operative clause. "
        "Land size (hectares or acres), location, County, boundaries. "
        "Stamp duty: 4% commercial / 2% residential — state who bears cost (usually buyer). "
        "Land rates clearance certificate from County Government: seller's obligation. "
        "Land Control Board (LCB) consent: required for agricultural land — application timeline. "
        "Spousal consent: Matrimonial Property Act 2013 s.12 — required if matrimonial home. "
        "Encumbrances: seller warrants freehold unencumbered title OR discloses all charges, caveats, cautions. "
        "Title search: buyer's right to search. "
        "Completion formalities: Land Registration Act 2012 transfer forms, Land Rent clearance (leasehold). "
        "Deposit and balance payment schedule."
    ),
    "Employment - Permanent Employee": (
        "EMPLOYMENT CONTRACT SPECIFICS: Employment Act 2007 compliance mandatory throughout. "
        "Probation: maximum 6 months (s.42). "
        "Gross salary AND net take-home (after PAYE, NSSF, NHIF) — both stated. "
        "NSSF: employee 6% + employer 6% (NSSF Act 2013 Tier I up to KES 18,000; Tier II above — flag pending litigation on 2013 Act rates). "
        "NHIF: current rates per Finance Act schedule. "
        "PAYE: per Income Tax Act (Cap. 470) bands — employer's obligation to deduct and remit. "
        "Annual leave: 21 working days minimum (Employment Act s.28). "
        "Maternity leave: 3 months on full pay (s.29). "
        "Paternity leave: 2 weeks on full pay (s.29A). "
        "Sick leave: 7 days full pay + 7 days half pay per year (s.30). "
        "Notice: 28 days minimum for permanent employees (s.35). "
        "Disciplinary: fair hearing per Employment Act and Employment and Labour Relations Court Act 2011. "
        "Work Injury Benefits Act 2007: employer obligations. "
        "Non-compete and non-solicitation clauses: include reasonableness limitation (geographical + temporal)."
    ),
    "Loan Agreement": (
        "LOAN AGREEMENT SPECIFICS: Principal amount in figures AND words. "
        "Interest rate per annum — state CBK reference rate basis; include spread. "
        "MANDATORY repayment schedule table: Period | Date | Opening Balance | Principal | Interest | Closing Balance. "
        "Default interest (higher rate, e.g., 5% above contractual rate) — accrues from due date to actual payment. "
        "Withholding tax on interest: Income Tax Act s.35 — 15% resident / 15% non-resident (check applicable DTA). "
        "Stamp duty: 0.1% of loan amount (Stamp Duty Act Cap. 480). "
        "Security: describe collateral, registration obligations (Movable Property Security Rights Act 2017 for chattel; Land Registration Act 2012 for land). "
        "Events of default: non-payment, misrepresentation, insolvency, cross-default. "
        "Remedies on default: acceleration, enforcement of security. "
        "Banking Act (Cap. 488) compliance if lender is licensed institution."
    ),
    "Lease - Commercial": (
        "COMMERCIAL LEASE SPECIFICS: LR/Title Number MANDATORY. "
        "Premises description (floor, area in sq metres, building name, County). "
        "Permitted use: specific use stated; prohibition on change without consent. "
        "Rent review: every 2 years (Landlord and Tenant Act); review mechanism (fixed percentage vs market rate). "
        "Service charge: separate from rent; accounting obligations on landlord. "
        "Dilapidations: schedule of condition at commencement. "
        "Stamp duty on lease: Stamp Duty Act Cap. 480 (rates based on lease term and rent). "
        "Landlord and Tenant (Shops, Hotels and Catering Establishments) Act (Cap. 301): applicability notice if commercial premises."
    ),
    "Lease - Residential": (
        "RESIDENTIAL LEASE SPECIFICS: LR/Title Number. Premises description (house/apartment number, location). "
        "Rent amount and due date. Deposit (refundable within 30 days of vacation less deductions). "
        "Permitted occupants. Utilities responsibility. "
        "Prohibited: subletting, keeping pets, alterations without consent. "
        "Notice to vacate: 1 month minimum for month-to-month tenancy. "
        "Distress for Rent Act (Cap. 293) — landlord's right to distrain. "
        "Rent Restriction Act (Cap. 296) applicability where applicable."
    ),

    # POA subtypes
    "General Power of Attorney": (
        "GENERAL POA: Ensure ALL categories of powers are fully enumerated — property, financial, legal, business, vehicles, government dealings. "
        "Include express ratification and indemnity to third parties. Certificate of Verification mandatory."
    ),
    "Special Power of Attorney": (
        "SPECIAL POA: Powers LIMITED to specific transaction identified in payload. "
        "Identify specific property/transaction by full details (LR Number, vehicle reg, bank account, etc.). "
        "All other powers expressly excluded. Certificate of Verification mandatory."
    ),
    "Enduring Power of Attorney": (
        "ENDURING POA: Express statement that powers continue despite subsequent mental incapacity of Donor — Power of Attorney Act (Cap. 285). "
        "Include safeguards against abuse. Consider Mental Health Act (Cap. 248) context. Certificate of Verification mandatory."
    ),

    # Will subtypes
    "Simple Will": (
        "SIMPLE WILL: All mandatory elements present. Two independent witnesses who are NOT beneficiaries (Law of Succession Act s.11 and s.13). "
        "Attestation clause in prescribed form. If testator signs by mark, attestation must so state."
    ),
    "Will with Trust": (
        "WILL WITH TRUST: Full trust provisions — trustees (minimum 2 trustees for land per Land Registration Act), trustee powers, "
        "investment powers (Trustee Investments Act Cap. 148B), accumulation during minority, vesting age. "
        "Conflict of interest provisions for trustee who is also a beneficiary."
    ),
}


# ══════════════════════════════════════════════════════════════════
# DOCUMENT GENERATOR CLASS
# ══════════════════════════════════════════════════════════════════

class DocumentGenerator:
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    # ------------------------------------------------------------------
    # Blueprint selection
    # ------------------------------------------------------------------
    def _get_blueprint(self, doc_type: str) -> str:
        return {
            "Agreement":        BLUEPRINT_CONTRACTS,
            "Affidavit":        BLUEPRINT_AFFIDAVITS,
            "Will":             BLUEPRINT_WILLS,
            "Power of Attorney": BLUEPRINT_POA,
        }.get(doc_type, BLUEPRINT_CONTRACTS)

    # ------------------------------------------------------------------
    # Subtype guidance
    # ------------------------------------------------------------------
    def _get_subtype_guidance(self, subtype: str) -> str:
        if not subtype:
            return ""
        # Exact match first; then partial match
        guidance = SUBTYPE_GUIDANCE_MAP.get(subtype, "")
        if not guidance:
            for key, val in SUBTYPE_GUIDANCE_MAP.items():
                if subtype.lower() in key.lower() or key.lower() in subtype.lower():
                    guidance = val
                    break
        return f"SUBTYPE-SPECIFIC REQUIREMENTS:\n{guidance}" if guidance else ""

    # ------------------------------------------------------------------
    # Full system prompt construction
    # ------------------------------------------------------------------
    def _build_optimized_prompt(self, payload: Dict[str, Any]) -> str:
        doc_type    = payload.get("document", {}).get("type", "Agreement")
        doc_subtype = payload.get("document", {}).get("subtype", "")

        blueprint       = self._get_blueprint(doc_type)
        subtype_guidance = self._get_subtype_guidance(doc_subtype)

        parts = [
            CORE_INSTRUCTIONS,
            KENYA_COMPLIANCE,
            blueprint,
        ]
        if subtype_guidance:
            parts.append(subtype_guidance)
        parts.append(DISCLAIMER)

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------
    def build_messages(self, payload: Dict[str, Any]) -> list:
        user_payload = {
            "matter": payload.get("matter", {}),
            "document": {
                "type":      payload.get("document", {}).get("type", ""),
                "subtype":   payload.get("document", {}).get("subtype", ""),
                "variables": payload.get("document", {}).get("variables", {}),
            },
        }

        system_content = self._build_optimized_prompt(payload)

        doc_type    = user_payload["document"]["type"]
        doc_subtype = user_payload["document"]["subtype"]
        subtype_str = f" ({doc_subtype})" if doc_subtype else ""

        # Build contract-specific word count gate
        is_contract = doc_type == "Agreement"
        contract_gate = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTRACT WORD COUNT GATE — MANDATORY FOR AGREEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This contract MUST contain at least 3,000 words of substantive legal prose (HTML tags excluded).

CLAUSE-BY-CLAUSE BUDGET — hit every target before moving to the next clause:
  Header + Parties + Recitals  →  write until ≥ 350 words, THEN proceed to Clause 1
  Clause 1  Definitions        →  write until ≥ 550 words, THEN proceed to Clause 2
  Clause 2  Scope              →  write until ≥ 450 words, THEN proceed to Clause 3
  Clause 3  Term               →  write until ≥ 200 words, THEN proceed to Clause 4
  Clause 4  Payment            →  write until ≥ 350 words, THEN proceed to Clause 5
  Clause 5  Obligations        →  write until ≥ 450 words, THEN proceed to Clause 6
  Clause 6  Warranties         →  write until ≥ 300 words, THEN proceed to Clause 7
  Clause 7  Indemnities        →  write until ≥ 200 words, THEN proceed to Clause 8
  Clause 8  Confidentiality    →  write until ≥ 250 words, THEN proceed to Clause 9
  Clause 9  IP                 →  write until ≥ 150 words, THEN proceed to Clause 10
  Clause 10 Insurance          →  write until ≥ 150 words, THEN proceed to Clause 11
  Clause 11 Liability          →  write until ≥ 180 words, THEN proceed to Clause 12
  Clause 12 Force Majeure      →  write until ≥ 150 words, THEN proceed to Clause 13
  Clause 13 Termination        →  write until ≥ 280 words, THEN proceed to Clause 14
  Clause 14 Dispute Resolution →  write until ≥ 220 words, THEN proceed to Clause 15
  Clause 15 General Provisions →  write until ≥ 300 words, THEN write Execution Block

CRITICAL RULES:
  — Write EVERY sub-clause as complete, grammatically correct sentences.
  — If a clause feels short, add more specific provisions, examples, and procedural detail.
  — Do NOT use bullet fragments, do NOT summarise, do NOT skip sub-clauses.
  — If you are approaching the token limit mid-document, STOP at the end of the current clause
    (never mid-sentence) so the continuation system can resume cleanly.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""" if is_contract else ""

        user_content = f"""You must now draft a complete, LSK-compliant Kenyan legal document using the INPUT DATA below.

DOCUMENT TYPE: {doc_type}{subtype_str}

INPUT DATA:
{json.dumps(user_payload, indent=2, ensure_ascii=False)}
{contract_gate}
PRE-OUTPUT CHECKLIST — verify every item before writing the first HTML tag:
[ ] 1. ALL variables from INPUT DATA injected; none left as generic placeholders
[ ] 2. [SQUARE BRACKET] placeholders used ONLY for genuinely absent fields
[ ] 3. Pronouns consistent with gender field (affidavits) or party type throughout
[ ] 4. P.O. Box, postal code, and town present for every party/deponent
[ ] 5. National ID/Passport numbers present for every individual
[ ] 6. KRA PIN numbers present for every party where applicable
[ ] 7. All statutory references cited correctly with Cap. number or year
[ ] 8. Numbering hierarchy (1., 1.1, 1.1.1, (a), (i)) strictly correct throughout
[ ] 9. No clause truncated, summarised, or left incomplete
[ ] 10. For Agreements: EVERY clause budget above has been met before moving on
[ ] 11. Disclaimer paragraph appears at the very end
[ ] 12. Execution/sworn block correctly formatted for the document type
[ ] 13. For affidavits: (a) NO subheadings anywhere in body; (b) heading is "AFFIDAVIT" only, no name; (c) averments sequentially numbered, no secondary numbering; (d) both mandatory closing averments present; (e) body text is text-align:justify; (f) sworn block uses two-column HTML table
[ ] 14. For Wills: two witnesses confirmed not to be beneficiaries
[ ] 15. For POA: Certificate of Verification by Advocate included

OUTPUT: Complete HTML only. First character must be <. Last element must be the disclaimer paragraph. Nothing else."""

        return [
            {"role": "system",  "content": system_content},
            {"role": "user",    "content": user_content},
        ]

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------
    def generate_document_stream(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Stream document generation with automatic continuation if the model
        hits the token limit before the document is complete.

        Flow:
          1. First pass streams the document, buffering all output.
          2. If finish_reason == "length", a continuation call is made with
             the full generated text as assistant context, asking the model
             to resume exactly where it stopped.
          3. Continuation repeats up to MAX_CONTINUATIONS times.
          4. Opening markdown code fences (```html) are stripped from the
             first chunk as a safety net against model non-compliance.
        """
        import re
        import logging

        log = logging.getLogger(__name__)

        try:
            cfg         = payload.get("generation_config", {}) or {}
            model       = cfg.get("model")       or os.getenv("OPENAI_MODEL",       "gpt-4o")
            temperature = float(cfg.get("temperature", os.getenv("OPENAI_TEMPERATURE", 0.2)))
            max_tokens  = int(cfg.get("max_tokens",   os.getenv("OPENAI_MAX_TOKENS",  16000)))

            MAX_CONTINUATIONS = 3   # safety cap on continuation loops
            FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?")

            messages        = self.build_messages(payload)
            accumulated     = ""   # full document text built across all passes
            continuation_n  = 0

            while True:
                # ── Build the request messages for this pass ─────────────────
                if continuation_n == 0:
                    request_messages = messages
                else:
                    # Provide the full text generated so far as assistant turn,
                    # then ask the model to continue seamlessly.
                    request_messages = messages + [
                        {
                            "role": "assistant",
                            "content": accumulated
                        },
                        {
                            "role": "user",
                            "content": (
                                "The document was cut off. Continue generating from exactly "
                                "where the text above ends. Do NOT restart, repeat, or add "
                                "any preamble. Resume mid-word or mid-sentence if necessary. "
                                "Continue until the document is fully complete, including all "
                                "remaining clauses, the execution/signature block, and the "
                                "legal disclaimer paragraph at the very end."
                            )
                        }
                    ]

                # ── Stream this pass ─────────────────────────────────────────
                stream = self.client.chat.completions.create(
                    model=model,
                    messages=request_messages,
                    stream=True,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                pass_text     = ""
                finish_reason = "stop"
                fence_checked = (continuation_n > 0)  # only strip fence on first pass

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
                    delta = choice.delta
                    if not (delta and delta.content):
                        continue

                    text = delta.content

                    # Strip opening markdown fence on the very first chunk
                    if not fence_checked:
                        pass_text += text
                        if len(pass_text) >= 20 or "<" in pass_text:
                            pass_text = FENCE_RE.sub("", pass_text)
                            fence_checked = True
                            yield pass_text
                            accumulated += pass_text
                            pass_text = ""
                    else:
                        yield text
                        accumulated += text

                # Flush any buffered text from fence-check window
                if pass_text:
                    pass_text = FENCE_RE.sub("", pass_text)
                    if pass_text:
                        yield pass_text
                        accumulated += pass_text

                # ── Decide whether to continue ────────────────────────────────
                if finish_reason != "length":
                    break   # model finished naturally — done

                continuation_n += 1
                if continuation_n > MAX_CONTINUATIONS:
                    log.warning(
                        "Document still incomplete after %d continuations — stopping.",
                        MAX_CONTINUATIONS
                    )
                    break

                log.warning(
                    "Document hit token limit (pass %d) — requesting continuation %d/%d.",
                    continuation_n, continuation_n, MAX_CONTINUATIONS
                )

        except Exception as e:
            import logging as _logging
            _logging.getLogger(__name__).error(
                "Document generation error: %s", e, exc_info=True
            )
            yield "\n\n[Document generation encountered an issue. Please try again or contact support.]"

    # ------------------------------------------------------------------
    # Backwards compatibility
    # ------------------------------------------------------------------
    def build_prompt(self, payload: Dict[str, Any]) -> str:
        """Retained for backward compatibility."""
        return self._build_optimized_prompt(payload)