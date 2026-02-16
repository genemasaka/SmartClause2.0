# document_generator.py
# document_generator_optimized.py
import os
from typing import Dict, Any, Generator
import json
import openai


# ==============================
# CORE SYSTEM INSTRUCTIONS (Used for ALL document types)
# ==============================
CORE_INSTRUCTIONS = """You are a Senior Advocate of the High Court of Kenya specializing in legal document drafting with 15+ years experience in Commercial Law, Conveyancing, and Civil Litigation.

OBJECTIVE: Produce detailed, legally compliant Kenyan legal documents.

CRITICAL RULES:
1. Output ONLY document content + disclaimer. No conversational filler.
2. PRIORITIZE SUBSTANCE: Detailed provisions reflecting actual Kenyan legal practice.
3. JURISDICTION: Strictly Kenyan law (Constitution 2010, Acts of Parliament, case law).
4. FORMAT: HTML only. Use <h3> for main clauses, <h4> for sub-clauses, <p> for text, <b> for emphasis.
5. NUMBERING: Strict hierarchy (1., 1.1, 1.1.1, 1.1.1.1). Sub-divisions: (a), (b) or (i), (ii).
6. DATES: Kenyan format "20th January 2026". CURRENCY: "Kenya Shillings" or "KES 1,000,000".
7. PLACEHOLDERS: [square brackets] for missing info with descriptive guidance.
8. ACCURACY: All statutory references must reflect current Kenyan law."""

# ==============================
# KENYA-SPECIFIC FIELD REQUIREMENTS
# ==============================
KENYA_COMPLIANCE = """
KENYA FIELD REQUIREMENTS:

AFFIDAVITS:
- Gender: MANDATORY for pronoun usage ("I am an adult [male/female]...")
- P.O. Box: MANDATORY for official correspondence
- First statement: "THAT I am an adult [male/female] of sound mind..."

AGREEMENTS (Individuals):
- ID/Passport: MANDATORY
- KRA PIN: MANDATORY for tax compliance
- Format: "Name, ID No. [...], of P.O. Box [...], [Town]"

AGREEMENTS (Companies):
- Registration No. + KRA PIN: MANDATORY
- Registered office + postal address required

LAND TRANSACTIONS:
- Title/LR Number, stamp duty, land rates, County/LCB consents

EMPLOYMENT:
- NSSF/NHIF provisions MANDATORY
- Gross vs net salary explicit
- Employment Act, 2007 compliance

VEHICLE TRANSACTIONS:
- Registration, chassis, engine numbers MANDATORY
- NTSA transfer, logbook status, HP clearance

LOANS:
- Interest rate: CBK compliant
- Withholding tax, stamp duty provisions

TAX:
- VAT: 16% (explicit if applicable)
- WHT: 5% professional fees, 10% dividends, 5% rent
- Stamp duty per Stamp Duty Act"""

# ==============================
# DOCUMENT TYPE BLUEPRINTS (Loaded dynamically)
# ==============================

BLUEPRINT_CONTRACTS = """
CONTRACT BLUEPRINT (4000+ WORDS MINIMUM):

CRITICAL NUMBERING: Strict hierarchy 1., 1.1, 1.1.1, 1.1.1.1. Within clauses: (a), (b), (c).

STRUCTURE:

**TITLE & COMMENCEMENT**
Clear title, date format: "[date] day of [month] [year]"
"BETWEEN [Party 1] AND [Party 2]"

**1. PARTIES & CAPACITY** (300+ words)
1.1 Party 1: Full name, ID/Registration, KRA PIN, physical + postal addresses
1.2 Party 2: Same details
1.3 Corporate authority (if company): Certificate of Incorporation, CR12, resolutions
1.4 Capacity confirmation
1.5 Authorized signatories
1.6 Contact details: emails, phones
1.7 Communication procedures

**2. RECITALS** (400+ words)
2.1 Business context, prior dealings
2.2 Commercial objectives
2.3 Market/industry context
2.4 Regulatory framework, licenses
2.5 Corporate approvals obtained
2.6 Purpose and intention
"NOW THEREFORE in consideration of mutual covenants..."

**3. DEFINITIONS** (500+ words, 25-35 definitions)
Party terms, transaction terms, dates, technical terms, commercial concepts, performance metrics, legal procedures, financial terms.
Interpretation rules: headings for convenience, singular/plural, statutory references include amendments, "include" not limiting, time is of essence.

**4. SCOPE/SUBJECT MATTER** (600+ words) - Customize by subtype:
- SALE: Property description, title, encumbrances, condition, inspection rights
- SERVICE: Service specs, deliverables, performance standards, SLAs, methodology
- LEASE: Premises description, permitted use, condition, fixtures
- EMPLOYMENT: Job description, duties, location, reporting, equipment
- SUPPLY: Goods specs, quality standards, quantity, delivery terms
- LOAN: Principal amount, purpose, disbursement conditions

**5. CONSIDERATION/PRICING** (400+ words)
Price/fees, VAT treatment (16%), payment schedule, payment method, currency, invoicing, late payment (penalty + default rate), withholding tax, receipts, disputed amounts.

**6. TERM & COMMENCEMENT** (300+ words)
Start date, duration, milestones, automatic renewal, notice periods, early termination rights.

**7. OBLIGATIONS** (800+ words)
Detailed obligations of each party (specific to transaction type).

**8. REPRESENTATIONS & WARRANTIES** (400+ words)
Authority, capacity, no conflicts, compliance, accuracy, solvency, litigation status, regulatory approvals.

**9. INDEMNITIES** (300+ words)
Indemnity scope, procedure, limitations, defense cooperation.

**10. CONFIDENTIALITY & DATA PROTECTION** (300+ words)
Confidential information definition, obligations, exceptions, Data Protection Act compliance, duration.

**11. INTELLECTUAL PROPERTY** (250+ words if relevant)
IP ownership, licenses, restrictions, infringement procedures.

**12. INSURANCE** (200+ words if relevant)
Required policies, minimum coverage, beneficiaries, certificates.

**13. LIMITATION OF LIABILITY** (250+ words)
Caps, exclusions, proportionality, survival.

**14. FORCE MAJEURE** (200+ words)
Definition, obligations, notification, consequences, pandemic clauses.

**15. TERMINATION** (400+ words)
Termination for cause, convenience, insolvency, material breach, notice requirements, effects of termination, survival clauses.

**16. DISPUTE RESOLUTION** (300+ words)
Negotiation, mediation, arbitration (Arbitration Act 1995, Nairobi Centre for International Arbitration), seat, rules, language, costs, injunctive relief.

**17. GENERAL PROVISIONS** (500+ words)
Entire agreement, amendments, assignment, severability, waiver, notices, governing law (Laws of Kenya), jurisdiction (Kenyan courts), counterparts, costs, relationship, third party rights, time essence, language, schedules/annexures.

**EXECUTION**
Signature blocks with witness provisions per Law of Contract Act.

**SCHEDULES** (if applicable)
Detailed technical specifications, payment schedules, property descriptions."""

BLUEPRINT_AFFIDAVITS = """
AFFIDAVIT BLUEPRINT (1000+ WORDS MINIMUM):

**TITLE**: REPUBLIC OF KENYA, IN THE [COURT/MATTER], AFFIDAVIT OF [NAME]

**1. DEPONENT DETAILS** (200+ words)
1.1 Full legal name
1.2 ID/Passport Number
1.3 Gender (Male/Female) - for pronoun consistency
1.4 Physical address
1.5 P.O. Box, town, postal code - MANDATORY
1.6 Occupation
1.7 Contact: phone, email
1.8 "I, [NAME], of [ADDRESS], do hereby make oath and state as follows:"

**FIRST SWORN STATEMENT (MANDATORY)**:
"1. THAT I am an adult [male/female] of sound mind and I am competent to make this affidavit."

**2. SUBSTANTIVE AVERMENTS** (600+ words, numbered 2-15+)
Each paragraph starts "THAT" (uppercase).
Use gender-appropriate pronouns consistently (he/his/him or she/her/her).
Include all material facts, dates, circumstances.
Specific to affidavit type:
- NAME CHANGE: Previous name, new name, reason, supporting documents
- NTSA: Vehicle details, purpose, NTSA requirements
- BANK: Account number, bank name, purpose
- POST MORTEM: Deceased details, relationship, death circumstances
- MARRIAGE: Spouse details, marriage date, certificate number
- LOST DOCUMENTS: Document type, number, circumstances, date of loss
- ONE-AND-SAME: Name variants, contexts, explanation
- BIRTH: Child details, birth date/place, reason for affidavit
- RESIDENCE: Current address, duration, landlord, purpose
- SUPPORT: Person supported, relationship, nature of support, amount
- FINANCIAL STATUS: Employment, income, assets, liabilities
- CONSENT TO TRAVEL: Minor details, destination, dates, accompanying person

**FINAL AVERMENTS**:
"[N]. THAT I make this affidavit in good faith believing the same to be true and correct and in accordance with the provisions of the Oaths and Statutory Declarations Act (Cap. 15)."
"[N+1]. THAT what is deponed to herein is within my own knowledge save where otherwise stated and where so stated I verily believe the same to be true."

**SWORN STATEMENT**:
"SWORN by the said [NAME] at [Location] this [date] day of [month] [year]."
Signature blocks: Deponent signature, Commissioner for Oaths with name/address/stamp.

**LEGAL COMPLIANCE**: Oaths and Statutory Declarations Act (Cap. 15), Evidence Act (Cap. 80), Civil Procedure Act and Rules."""

BLUEPRINT_WILLS = """
WILL BLUEPRINT (2000+ WORDS MINIMUM):

**TITLE**: "LAST WILL AND TESTAMENT OF [TESTATOR NAME]"

**1. TESTATOR IDENTIFICATION** (200+ words)
Full name, ID/Passport, address, P.O. Box, revocation of prior wills.

**2. APPOINTMENT OF EXECUTOR** (300+ words)
Executor name, ID, address, powers (with/without bond), alternate executor, executor powers and duties, remuneration.

**3. FUNERAL & BURIAL** (150+ words)
Wishes, location, religious preferences, costs payment.

**4. DEBTS & LIABILITIES** (200+ words)
Direction to pay debts, funeral expenses, testamentary expenses, estate administration costs.

**5. SPECIFIC BEQUESTS** (500+ words)
Personal property (jewelry, vehicles, etc.), real property (land with LR numbers), financial assets, business interests.
Format: "I GIVE to [beneficiary] my [description] absolutely."

**6. RESIDUARY ESTATE** (300+ words)
Definition, distribution to beneficiaries, percentages, survivorship provisions.

**7. GUARDIANSHIP** (200+ words if minors)
Guardian appointment for minor children, alternate guardian, powers and responsibilities.

**8. TRUSTS** (300+ words if applicable)
Trust creation, trustees, beneficiaries, trust terms, trustee powers, investment powers.

**9. GENERAL PROVISIONS** (300+ words)
Hotchpot clause, ademption, lapse, survivorship period, tax provisions, common disaster.

**EXECUTION**:
"IN WITNESS WHEREOF I [TESTATOR] have set my hand to this my Last Will and Testament this [date] day of [month] [year]."
Testator signature, two witnesses (names, IDs, addresses, occupations, signatures).

**LEGAL COMPLIANCE**: Law of Succession Act (Cap. 160) - witnesses not beneficiaries, testator capacity, two witnesses, attestation clause."""

BLUEPRINT_POA = """
POWER OF ATTORNEY BLUEPRINT (2000+ WORDS MINIMUM):

**TITLE**: "[GENERAL/SPECIAL] POWER OF ATTORNEY"

**1. DONOR DETAILS** (200+ words)
Full name, ID/Passport, address, P.O. Box, capacity confirmation.

**2. ATTORNEY DETAILS** (200+ words)
Full name, ID/Passport, address, P.O. Box, acceptance of appointment.

**3. APPOINTMENT** (300+ words)
"I [DONOR] hereby appoint [ATTORNEY] as my lawful Attorney..."
Nature (general/special), scope, geographical limitations, duration, effective date, expiry conditions.

**4. POWERS GRANTED** (800+ words)
Detailed enumeration:
GENERAL POA: All lawful acts, property management, financial transactions, legal proceedings, business operations, banking, contracts, etc.
SPECIAL POA: Specific powers only (property sale/purchase, vehicle transactions, banking, legal matters, business operations, etc.)
Include: authority to sign documents, receive payments, give receipts, execute deeds, appear before authorities, etc.

**5. LIMITATIONS & RESTRICTIONS** (200+ words)
Powers NOT granted, financial limits, reporting requirements, prohibited transactions.

**6. RATIFICATION** (150+ words)
Donor ratifies all lawful acts by Attorney.

**7. REVOCATION** (150+ words)
Right to revoke, notice requirements, effective date of revocation.

**8. INDEMNITY** (150+ words)
Donor indemnifies third parties acting in good faith.

**9. DURATION & TERMINATION** (150+ words)
Effective period, automatic termination events (death, incapacity unless enduring, revocation).

**EXECUTION**:
"IN WITNESS WHEREOF I have set my hand this [date] day of [month] [year]."
Donor signature, witness details.

**CERTIFICATE OF VERIFICATION** (MANDATORY):
By Advocate or Magistrate confirming donor identity, understanding, and voluntary execution.
Advocate/Magistrate details, practicing certificate/court station, signature, official stamp.

**LEGAL COMPLIANCE**: Power of Attorney Act (Cap. 285), Registration of Documents Act (Cap. 285), Land Registration Act 2012 (for land POAs), Law of Contract Act (Cap. 23), stamping and registration requirements."""

# ==============================
# MANDATORY DISCLAIMER
# ==============================
DISCLAIMER = """
<div style="border: 2px solid red; padding: 15px; margin-top: 30px; background-color: #fff5f5;">
<p style="color: red; font-weight: bold; font-size: 14px;">⚖️ IMPORTANT LEGAL DISCLAIMER</p>
<p style="color: #333; font-size: 13px;">This document is a template generated by AI and may not be suitable for all situations. You should consult with a qualified legal professional in Kenya to ensure that this document is appropriate for your specific circumstances and complies with all applicable laws and regulations. This document does not constitute legal advice. The user assumes all responsibility for the use of this document and should seek independent legal counsel before relying on it for any legal purpose.</p>
</div>"""


class DocumentGenerator:
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def _get_blueprint(self, doc_type: str) -> str:
        """Select the appropriate blueprint based on document type."""
        blueprint_map = {
            "Agreement": BLUEPRINT_CONTRACTS,
            "Affidavit": BLUEPRINT_AFFIDAVITS,
            "Will": BLUEPRINT_WILLS,
            "Power of Attorney": BLUEPRINT_POA,
        }
        return blueprint_map.get(doc_type, BLUEPRINT_CONTRACTS)

    def _build_optimized_prompt(self, payload: Dict[str, Any]) -> str:
        """Build an optimized prompt with only the relevant blueprint."""
        doc_type = payload.get("document", {}).get("type", "Agreement")
        doc_subtype = payload.get("document", {}).get("subtype", "")
        
        # Get only the relevant blueprint
        blueprint = self._get_blueprint(doc_type)
        
        # Add subtype-specific guidance if applicable
        subtype_guidance = self._get_subtype_guidance(doc_subtype)
        
        # Build compact prompt
        prompt_parts = [
            CORE_INSTRUCTIONS,
            "\n\n" + KENYA_COMPLIANCE,
            "\n\n" + blueprint,
        ]
        
        if subtype_guidance:
            prompt_parts.append("\n\n" + subtype_guidance)
        
        prompt_parts.append("\n\n" + DISCLAIMER)
        
        return "\n".join(prompt_parts)

    def _get_subtype_guidance(self, subtype: str) -> str:
        """Provide specific guidance for common subtypes."""
        if not subtype:
            return ""
        
        guidance_map = {
            "Birth Affidavit": "Include child details, reference Births and Deaths Registration Act, birth certificate application requirement.",
            "Sale Agreement - Motor Vehicle": "Include all vehicle IDs (registration, chassis, engine), NTSA transfer form M1, logbook confirmation, HP clearance, seller's warranty of ownership.",
            "Employment - Permanent Employee": "Calculate NSSF (Tier I: 6% up to KES 18,000), NHIF (per rates schedule), PAYE, Employment Act 2007, annual leave (21 days), maternity (3 months).",
            "Loan Agreement": "Ensure interest rate CBK-compliant, include repayment schedule table, Banking Act provisions, default remedies, security registration requirements.",
            "Lease - Commercial": "Reference Landlord and Tenant Act, rent review (2 years), service charge separate, permitted use, title/LR number prominent.",
            "Sale Agreement - Land": "Title/LR number, land size, boundaries, stamp duty, land rates clearance, LCB consent, spousal consent, County consent, encumbrances disclosure.",
        }
        
        return f"SUBTYPE GUIDANCE: {guidance_map.get(subtype, '')}"

    def build_messages(self, payload: Dict[str, Any]):
        """Build optimized chat messages with dynamic blueprint loading."""
        # Clean payload
        user_payload = {
            "matter": payload.get("matter", {}),
            "document": {
                "type": payload.get("document", {}).get("type", ""),
                "subtype": payload.get("document", {}).get("subtype", ""),
                "variables": payload.get("document", {}).get("variables", {}),
            },
        }
        
        # Get optimized prompt with only relevant blueprint
        system_content = self._build_optimized_prompt(payload)
        
        # Build user message
        json_str = json.dumps(user_payload, indent=2, ensure_ascii=False)
        user_content = f"""INPUT DATA:
{json_str}

INSTRUCTIONS:
1. Use the {user_payload['document']['type']} blueprint above
2. Populate with ALL variables from INPUT DATA
3. For affidavits: Use gender field for pronouns throughout
4. Include P.O. Box and all identification fields
5. Output ONLY in HTML format
6. Include the disclaimer at the end
7. Use [brackets] for missing required info
8. Ensure minimum word count
9. Use strict numbering (1., 1.1, 1.1.1)

Generate the document now."""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        return messages

    def generate_document_stream(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Stream document generation with optimized prompt."""
        try:
            cfg = payload.get("generation_config", {}) or {}
            model = cfg.get("model", "gpt-4o-mini")
            temperature = float(cfg.get("temperature", 0.3))
            max_tokens = int(cfg.get("max_tokens", 6000))

            messages = self.build_messages(payload)

            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n[Error generating document: {str(e)}]"

    # Backwards compatibility
    def build_prompt(self, payload: Dict[str, Any]) -> str:
        """Retained for backward compatibility."""
        return self._build_optimized_prompt(payload)