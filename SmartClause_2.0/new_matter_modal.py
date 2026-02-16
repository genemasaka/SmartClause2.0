import streamlit as st
from typing import Dict, Any, List
from datetime import date
import json


class DateJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date and datetime objects."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        # Let the base class handle other types
        return super().default(obj)

# Document type configurations with subtypes
DOC_SUBTYPES: Dict[str, List[str]] = {
    "Agreement": [
    "Share Purchase Agreement",
    "Shareholders Agreement", 
    "Service Agreement",
    "Employment - Contractor",
    "Employment - Permanent Employee",
    "Lease - Commercial",
    "Lease - Car",
    "Lease - Machinery",
    "Lease - Equipment/Energy",
    "Loan Agreement",
    "Non-Disclosure Agreement - Mutual",
    "Non-Disclosure Agreement - One-Way",
    "Sale Agreement - Land",
    "Sale Agreement - General",
    "Tenancy - Residential",
    "Tenancy - Commercial (Controlled)",
    "Property Management Agreement",
    "Sale Agreement - Motor Vehicle",
    "Partnership Agreement",
    "Joint Venture Agreement",
    "Consultancy Agreement",
    "Agency Agreement",
    "Distribution Agreement",
    "Franchise Agreement",
    "Memorandum of Understanding (MOU)",
    "Settlement Agreement",
    "Deed of Assignment",
    "Deed of Guarantee",
    "Deed of Indemnity",
    "Supply Agreement",
    "Software License Agreement",
    "Intellectual Property Assignment",
    "Construction Contract",
    "Catering Agreement",
    "Security Services Agreement"
    ],
    "Affidavit": [
    "Name Change/Confirmation",
    "NTSA Affidavit",
    "Bank Affidavit",
    "Post Mortem",
    "Marriage Affidavit",
    "Lost Documents",
    "One-and-the-Same Person",
    "Withdrawal of Case",
    "Thumb-print (Illiterate Deponent)",
    "Birth Affidavit",
    "Change of Beneficiary",
    "Correction of Name in Documents",
    "Single Status Affidavit",
    "Consent to Travel (Minor)",
    "Support Affidavit",
    "Age Affidavit",
    "Survivorship Affidavit",
    "Heirship Affidavit",
    "Search Affidavit",
    "Service Affidavit",
    "Verification Affidavit",
    "Financial Status Affidavit",
    "Residence Affidavit",
    "Good Conduct Affidavit"
],
    "Will": [],
    "Power of Attorney": [
    "General Power of Attorney",
    "Special Power of Attorney - Property Sale",
    "Special Power of Attorney - Property Purchase",
    "Special Power of Attorney - Vehicle Sale",
    "Special Power of Attorney - Vehicle Registration",
    "Special Power of Attorney - Banking",
    "Special Power of Attorney - Land Matters",
    "Special Power of Attorney - Legal Proceedings",
    "Special Power of Attorney - Business Operations",
    "Special Power of Attorney - Passport Collection",
    "Special Power of Attorney - Visa Application",
    "Enduring Power of Attorney",
    "Power of Attorney - Rental Management",
    "Power of Attorney - Shares Transfer",
    "Power of Attorney - Immigration Matters"
]
}

# Field schemas based on selected subtype 
DOC_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
     "Share Purchase Agreement": [
        {"key": "buyer_name", "label": "Buyer Name", "type": "text", "required": True},
        {"key": "buyer_id", "label": "Buyer ID/Registration Number", "type": "text", "required": True},
        {"key": "seller_name", "label": "Seller Name", "type": "text", "required": True},
        {"key": "seller_id", "label": "Seller ID/Registration Number", "type": "text", "required": True},
        {"key": "target_company", "label": "Target Company", "type": "text", "required": True},
        {"key": "shares_number", "label": "Number of Shares", "type": "text", "required": True},
        {"key": "share_class", "label": "Class of Shares", "type": "text"},
        {"key": "purchase_price", "label": "Purchase Price (KES)", "type": "text", "required": True},
        {"key": "payment_terms", "label": "Payment Terms", "type": "textarea"},
        {"key": "closing_date", "label": "Closing Date", "type": "date"},
        {"key": "warranties_period", "label": "Warranties Period (months)", "type": "text", "default": "12"},
        {"key": "governing_law", "label": "Governing Law", "type": "text", "default": "Laws of Kenya"},
    ],
    "Shareholders Agreement": [
        {"key": "company_name", "label": "Company Name", "type": "text", "required": True},
        {"key": "company_registration", "label": "Company Registration Number", "type": "text", "required": True},
        {"key": "shareholders", "label": "Shareholders (comma separated)", "type": "textarea", "required": True},
        {"key": "shareholding_structure", "label": "Shareholding Structure (%)", "type": "textarea", "required": True},
        {"key": "board_seats", "label": "Board Seats Allocation", "type": "text"},
        {"key": "quorum", "label": "Quorum Requirements", "type": "text"},
        {"key": "voting_rights", "label": "Special Voting Rights", "type": "textarea"},
        {"key": "preemption_rights", "label": "Pre-emption Rights", "type": "text", "default": "Yes"},
        {"key": "drag_along", "label": "Drag-Along Rights", "type": "text", "default": "Yes"},
        {"key": "tag_along", "label": "Tag-Along Rights", "type": "text", "default": "Yes"},
    ],
    "Service Agreement": [
        {"key": "provider_name", "label": "Service Provider", "type": "text", "required": True},
        {"key": "provider_address", "label": "Provider Address", "type": "textarea", "required": True},
        {"key": "provider_pin", "label": "Provider KRA PIN", "type": "text"},
        {"key": "client_name", "label": "Client", "type": "text", "required": True},
        {"key": "client_address", "label": "Client Address", "type": "textarea", "required": True},
        {"key": "services_scope", "label": "Services Scope", "type": "textarea", "required": True},
        {"key": "service_term", "label": "Term (months)", "type": "text"},
        {"key": "commencement_date", "label": "Commencement Date", "type": "date"},
        {"key": "fees", "label": "Service Fees (KES)", "type": "text", "required": True},
        {"key": "payment_terms", "label": "Payment Terms", "type": "text"},
        {"key": "vat_applicable", "label": "VAT Applicable", "type": "text", "default": "Yes"},
        {"key": "termination_notice", "label": "Termination Notice (days)", "type": "text", "default": "30"},
    ],
    "Employment - Contractor": [
        {"key": "company_name", "label": "Company Name", "type": "text", "required": True},
        {"key": "company_pin", "label": "Company KRA PIN", "type": "text"},
        {"key": "contractor_name", "label": "Contractor Name", "type": "text", "required": True},
        {"key": "contractor_id", "label": "Contractor ID/Passport Number", "type": "text", "required": True},
        {"key": "contractor_pin", "label": "Contractor KRA PIN", "type": "text"},
        {"key": "services_scope", "label": "Services Scope", "type": "textarea", "required": True},
        {"key": "contract_term", "label": "Contract Term (months)", "type": "text"},
        {"key": "payment_amount", "label": "Payment Amount (KES)", "type": "text", "required": True},
        {"key": "payment_frequency", "label": "Payment Frequency", "type": "text", "default": "Monthly"},
        {"key": "withholding_tax", "label": "Withholding Tax Rate (%)", "type": "text", "default": "5"},
        {"key": "ip_ownership", "label": "IP Ownership", "type": "text", "default": "Company"},
    ],
    "Employment - Permanent Employee": [
        {"key": "employer_name", "label": "Employer", "type": "text", "required": True},
        {"key": "employer_pin", "label": "Employer KRA PIN", "type": "text"},
        {"key": "employee_name", "label": "Employee", "type": "text", "required": True},
        {"key": "employee_id", "label": "Employee ID Number", "type": "text", "required": True},
        {"key": "employee_pin", "label": "Employee KRA PIN", "type": "text"},
        {"key": "job_title", "label": "Job Title", "type": "text", "required": True},
        {"key": "department", "label": "Department", "type": "text"},
        {"key": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"key": "basic_salary", "label": "Basic Salary (KES)", "type": "text", "required": True},
        {"key": "housing_allowance", "label": "Housing Allowance (KES)", "type": "text"},
        {"key": "transport_allowance", "label": "Transport Allowance (KES)", "type": "text"},
        {"key": "probation_period", "label": "Probation Period (months)", "type": "text", "default": "3"},
        {"key": "notice_period", "label": "Notice Period (days)", "type": "text", "default": "30"},
        {"key": "annual_leave", "label": "Annual Leave Days", "type": "text", "default": "21"},
    ],
    "Lease - Commercial": [
        {"key": "landlord_name", "label": "Landlord Name", "type": "text", "required": True},
        {"key": "landlord_id", "label": "Landlord ID/Registration", "type": "text", "required": True},
        {"key": "tenant_name", "label": "Tenant Name", "type": "text", "required": True},
        {"key": "tenant_id", "label": "Tenant ID/Registration", "type": "text", "required": True},
        {"key": "property_description", "label": "Property Description", "type": "textarea", "required": True},
        {"key": "lr_number", "label": "L.R. Number", "type": "text"},
        {"key": "monthly_rent", "label": "Monthly Rent (KES)", "type": "text", "required": True},
        {"key": "security_deposit", "label": "Security Deposit (KES)", "type": "text", "required": True},
        {"key": "lease_term", "label": "Lease Term (years)", "type": "text", "required": True},
        {"key": "commencement_date", "label": "Commencement Date", "type": "date", "required": True},
        {"key": "permitted_use", "label": "Permitted Use", "type": "textarea"},
        {"key": "rent_review_period", "label": "Rent Review Period (years)", "type": "text", "default": "2"},
        {"key": "utilities_responsibility", "label": "Utilities Paid By", "type": "text", "default": "Tenant"},
    ],
    "Lease - Car": [
        {"key": "lessor_name", "label": "Lessor Name", "type": "text", "required": True},
        {"key": "lessor_id", "label": "Lessor ID/Registration", "type": "text", "required": True},
        {"key": "lessee_name", "label": "Lessee Name", "type": "text", "required": True},
        {"key": "lessee_id", "label": "Lessee ID/License Number", "type": "text", "required": True},
        {"key": "vehicle_make", "label": "Vehicle Make", "type": "text", "required": True},
        {"key": "vehicle_model", "label": "Vehicle Model", "type": "text", "required": True},
        {"key": "vehicle_year", "label": "Year of Manufacture", "type": "text", "required": True},
        {"key": "registration_number", "label": "Registration Number", "type": "text", "required": True},
        {"key": "chassis_number", "label": "Chassis Number", "type": "text"},
        {"key": "monthly_payment", "label": "Monthly Lease Payment (KES)", "type": "text", "required": True},
        {"key": "lease_period", "label": "Lease Period (months)", "type": "text", "required": True},
        {"key": "mileage_limit", "label": "Monthly Mileage Limit (km)", "type": "text"},
        {"key": "maintenance_responsibility", "label": "Maintenance By", "type": "text", "default": "Lessor"},
        {"key": "insurance_responsibility", "label": "Insurance By", "type": "text", "default": "Lessor"},
    ],
    "Lease - Machinery": [
        {"key": "lessor_name", "label": "Lessor Name", "type": "text", "required": True},
        {"key": "lessor_registration", "label": "Lessor Registration", "type": "text"},
        {"key": "lessee_name", "label": "Lessee Name", "type": "text", "required": True},
        {"key": "lessee_registration", "label": "Lessee Registration", "type": "text"},
        {"key": "machinery_description", "label": "Machinery Description", "type": "textarea", "required": True},
        {"key": "serial_numbers", "label": "Serial Numbers", "type": "text"},
        {"key": "monthly_payment", "label": "Monthly Lease Payment (KES)", "type": "text", "required": True},
        {"key": "lease_term", "label": "Lease Term (months)", "type": "text", "required": True},
        {"key": "location", "label": "Location of Use", "type": "text", "required": True},
        {"key": "maintenance_schedule", "label": "Maintenance Schedule", "type": "textarea"},
        {"key": "insurance_value", "label": "Insurance Value (KES)", "type": "text"},
        {"key": "purchase_option", "label": "Purchase Option at End", "type": "text", "default": "Yes"},
    ],
    "Lease - Equipment/Energy": [
        {"key": "lessor_name", "label": "Lessor Name", "type": "text", "required": True},
        {"key": "lessee_name", "label": "Lessee Name", "type": "text", "required": True},
        {"key": "equipment_description", "label": "Equipment Description", "type": "textarea", "required": True},
        {"key": "equipment_value", "label": "Equipment Value (KES)", "type": "text", "required": True},
        {"key": "monthly_payment", "label": "Monthly Payment (KES)", "type": "text", "required": True},
        {"key": "lease_period", "label": "Lease Period (months)", "type": "text", "required": True},
        {"key": "energy_specifications", "label": "Energy Specifications", "type": "textarea"},
        {"key": "installation_date", "label": "Installation Date", "type": "date"},
        {"key": "maintenance_terms", "label": "Maintenance Terms", "type": "textarea"},
    ],
    "Loan Agreement": [
        {"key": "lender_name", "label": "Lender Name", "type": "text", "required": True},
        {"key": "lender_id", "label": "Lender ID/Registration", "type": "text", "required": True},
        {"key": "borrower_name", "label": "Borrower Name", "type": "text", "required": True},
        {"key": "borrower_id", "label": "Borrower ID/Registration", "type": "text", "required": True},
        {"key": "loan_amount", "label": "Loan Amount (KES)", "type": "text", "required": True},
        {"key": "interest_rate", "label": "Interest Rate (% p.a.)", "type": "text", "required": True},
        {"key": "loan_term", "label": "Loan Term (months)", "type": "text", "required": True},
        {"key": "repayment_schedule", "label": "Repayment Schedule", "type": "text", "default": "Monthly"},
        {"key": "disbursement_date", "label": "Disbursement Date", "type": "date"},
        {"key": "security_offered", "label": "Security/Collateral", "type": "textarea"},
        {"key": "purpose", "label": "Purpose of Loan", "type": "textarea"},
        {"key": "default_interest", "label": "Default Interest Rate (%)", "type": "text"},
    ],
    "Non-Disclosure Agreement - Mutual": [
        {"key": "party_a_name", "label": "Party A Name", "type": "text", "required": True},
        {"key": "party_a_registration", "label": "Party A Registration", "type": "text"},
        {"key": "party_b_name", "label": "Party B Name", "type": "text", "required": True},
        {"key": "party_b_registration", "label": "Party B Registration", "type": "text"},
        {"key": "purpose", "label": "Purpose of Disclosure", "type": "textarea", "required": True},
        {"key": "duration", "label": "Confidentiality Period (years)", "type": "text", "default": "3"},
        {"key": "effective_date", "label": "Effective Date", "type": "date"},
    ],
    "Non-Disclosure Agreement - One-Way": [
        {"key": "disclosing_party", "label": "Disclosing Party", "type": "text", "required": True},
        {"key": "disclosing_registration", "label": "Disclosing Party Registration", "type": "text"},
        {"key": "receiving_party", "label": "Receiving Party", "type": "text", "required": True},
        {"key": "receiving_registration", "label": "Receiving Party Registration", "type": "text"},
        {"key": "purpose", "label": "Purpose of Disclosure", "type": "textarea", "required": True},
        {"key": "duration", "label": "Confidentiality Period (years)", "type": "text", "default": "3"},
        {"key": "effective_date", "label": "Effective Date", "type": "date"},
    ],
    "Sale Agreement - Land": [
        {"key": "vendor_name", "label": "Vendor Name", "type": "text", "required": True},
        {"key": "vendor_id", "label": "Vendor ID Number", "type": "text", "required": True},
        {"key": "purchaser_name", "label": "Purchaser Name", "type": "text", "required": True},
        {"key": "purchaser_id", "label": "Purchaser ID Number", "type": "text", "required": True},
        {"key": "property_description", "label": "Property Description", "type": "textarea", "required": True},
        {"key": "lr_number", "label": "L.R. Number", "type": "text", "required": True},
        {"key": "plot_number", "label": "Plot Number", "type": "text"},
        {"key": "area", "label": "Area (acres/hectares)", "type": "text", "required": True},
        {"key": "purchase_price", "label": "Purchase Price (KES)", "type": "text", "required": True},
        {"key": "deposit_amount", "label": "Deposit Amount (KES)", "type": "text"},
        {"key": "balance_payment_date", "label": "Balance Payment Date", "type": "date"},
        {"key": "possession_date", "label": "Date of Giving Possession", "type": "date"},
    ],
    "Sale Agreement - General": [
        {"key": "seller_name", "label": "Seller Name", "type": "text", "required": True},
        {"key": "seller_id", "label": "Seller ID/Registration", "type": "text", "required": True},
        {"key": "buyer_name", "label": "Buyer Name", "type": "text", "required": True},
        {"key": "buyer_id", "label": "Buyer ID/Registration", "type": "text", "required": True},
        {"key": "goods_description", "label": "Description of Goods", "type": "textarea", "required": True},
        {"key": "purchase_price", "label": "Purchase Price (KES)", "type": "text", "required": True},
        {"key": "payment_terms", "label": "Payment Terms", "type": "textarea"},
        {"key": "delivery_terms", "label": "Delivery Terms", "type": "textarea"},
        {"key": "warranty_period", "label": "Warranty Period", "type": "text"},
    ],
    "Tenancy - Residential": [
        {"key": "landlord_name", "label": "Landlord Name", "type": "text", "required": True},
        {"key": "landlord_id", "label": "Landlord ID Number", "type": "text", "required": True},
        {"key": "tenant_name", "label": "Tenant Name", "type": "text", "required": True},
        {"key": "tenant_id", "label": "Tenant ID Number", "type": "text", "required": True},
        {"key": "property_address", "label": "Property Address", "type": "textarea", "required": True},
        {"key": "property_type", "label": "Property Type", "type": "text", "default": "Apartment"},
        {"key": "monthly_rent", "label": "Monthly Rent (KES)", "type": "text", "required": True},
        {"key": "security_deposit", "label": "Security Deposit (KES)", "type": "text", "required": True},
        {"key": "lease_period", "label": "Lease Period (months)", "type": "text", "default": "12"},
        {"key": "commencement_date", "label": "Commencement Date", "type": "date", "required": True},
        {"key": "utilities_included", "label": "Utilities Included", "type": "text"},
        {"key": "number_occupants", "label": "Maximum Number of Occupants", "type": "text"},
    ],
    "Tenancy - Commercial (Controlled)": [
        {"key": "landlord_name", "label": "Landlord Name", "type": "text", "required": True},
        {"key": "landlord_id", "label": "Landlord ID/Registration", "type": "text", "required": True},
        {"key": "tenant_name", "label": "Tenant Name", "type": "text", "required": True},
        {"key": "tenant_registration", "label": "Tenant Registration", "type": "text", "required": True},
        {"key": "premises_address", "label": "Premises Address", "type": "textarea", "required": True},
        {"key": "monthly_rent", "label": "Monthly Rent (KES)", "type": "text", "required": True},
        {"key": "service_charge", "label": "Service Charge (KES)", "type": "text"},
        {"key": "rent_control_number", "label": "Rent Control Number", "type": "text"},
        {"key": "permitted_use", "label": "Permitted Use", "type": "text", "required": True},
        {"key": "lease_term", "label": "Lease Term (years)", "type": "text", "required": True},
    ],
    "Property Management Agreement": [
        {"key": "owner_name", "label": "Property Owner", "type": "text", "required": True},
        {"key": "owner_id", "label": "Owner ID/Registration", "type": "text", "required": True},
        {"key": "manager_name", "label": "Property Manager", "type": "text", "required": True},
        {"key": "manager_registration", "label": "Manager Registration", "type": "text", "required": True},
        {"key": "property_description", "label": "Property Description", "type": "textarea", "required": True},
        {"key": "management_fee", "label": "Management Fee (%)", "type": "text", "required": True},
        {"key": "services_scope", "label": "Services to be Provided", "type": "textarea", "required": True},
        {"key": "term", "label": "Agreement Term (years)", "type": "text", "required": True},
        {"key": "authority_limits", "label": "Manager's Authority Limits", "type": "textarea"},
    ],
    "Sale Agreement - Motor Vehicle": [
        {"key": "seller_name", "label": "Seller Name", "type": "text", "required": True},
        {"key": "seller_id", "label": "Seller ID Number", "type": "text", "required": True},
        {"key": "buyer_name", "label": "Buyer Name", "type": "text", "required": True},
        {"key": "buyer_id", "label": "Buyer ID Number", "type": "text", "required": True},
        {"key": "vehicle_make", "label": "Vehicle Make", "type": "text", "required": True},
        {"key": "vehicle_model", "label": "Vehicle Model", "type": "text", "required": True},
        {"key": "year_manufacture", "label": "Year of Manufacture", "type": "text", "required": True},
        {"key": "registration_number", "label": "Registration Number", "type": "text", "required": True},
        {"key": "chassis_number", "label": "Chassis Number", "type": "text", "required": True},
        {"key": "engine_number", "label": "Engine Number", "type": "text"},
        {"key": "mileage", "label": "Current Mileage (km)", "type": "text"},
        {"key": "purchase_price", "label": "Purchase Price (KES)", "type": "text", "required": True},
        {"key": "payment_method", "label": "Payment Method", "type": "text"},
    ],
    "Partnership Agreement": [
        {"key": "partnership_name", "label": "Partnership Name", "type": "text", "required": True},
        {"key": "partners", "label": "Partners (comma separated)", "type": "textarea", "required": True},
        {"key": "business_nature", "label": "Nature of Business", "type": "textarea", "required": True},
        {"key": "capital_contributions", "label": "Capital Contributions", "type": "textarea", "required": True},
        {"key": "profit_sharing", "label": "Profit/Loss Sharing Ratio", "type": "textarea", "required": True},
        {"key": "management_structure", "label": "Management Structure", "type": "textarea"},
        {"key": "commencement_date", "label": "Commencement Date", "type": "date"},
        {"key": "duration", "label": "Duration (years)", "type": "text"},
    ],
    "Joint Venture Agreement": [
        {"key": "party_a", "label": "Party A", "type": "text", "required": True},
        {"key": "party_b", "label": "Party B", "type": "text", "required": True},
        {"key": "jv_purpose", "label": "Joint Venture Purpose", "type": "textarea", "required": True},
        {"key": "contributions", "label": "Contributions of Each Party", "type": "textarea", "required": True},
        {"key": "profit_sharing", "label": "Profit Sharing", "type": "text", "required": True},
        {"key": "management_structure", "label": "Management Structure", "type": "textarea"},
        {"key": "duration", "label": "Duration (years)", "type": "text"},
    ],
    "Consultancy Agreement": [
        {"key": "client_name", "label": "Client Name", "type": "text", "required": True},
        {"key": "consultant_name", "label": "Consultant Name", "type": "text", "required": True},
        {"key": "services_scope", "label": "Scope of Services", "type": "textarea", "required": True},
        {"key": "deliverables", "label": "Deliverables", "type": "textarea"},
        {"key": "fees", "label": "Consultancy Fees (KES)", "type": "text", "required": True},
        {"key": "payment_terms", "label": "Payment Terms", "type": "text"},
        {"key": "term", "label": "Term (months)", "type": "text"},
        {"key": "ip_ownership", "label": "IP Ownership", "type": "text", "default": "Client"},
    ],
    "Agency Agreement": [
        {"key": "principal_name", "label": "Principal Name", "type": "text", "required": True},
        {"key": "agent_name", "label": "Agent Name", "type": "text", "required": True},
        {"key": "territory", "label": "Territory/Region", "type": "text", "required": True},
        {"key": "products_services", "label": "Products/Services", "type": "textarea", "required": True},
        {"key": "commission_rate", "label": "Commission Rate (%)", "type": "text", "required": True},
        {"key": "exclusivity", "label": "Exclusive Agency", "type": "text", "default": "Yes"},
        {"key": "term", "label": "Term (years)", "type": "text", "required": True},
        {"key": "sales_targets", "label": "Sales Targets", "type": "textarea"},
    ],
    "Distribution Agreement": [
        {"key": "supplier_name", "label": "Supplier Name", "type": "text", "required": True},
        {"key": "distributor_name", "label": "Distributor Name", "type": "text", "required": True},
        {"key": "products", "label": "Products Description", "type": "textarea", "required": True},
        {"key": "territory", "label": "Distribution Territory", "type": "text", "required": True},
        {"key": "exclusivity", "label": "Exclusive Distribution", "type": "text", "default": "Yes"},
        {"key": "minimum_purchases", "label": "Minimum Purchase Obligations", "type": "textarea"},
        {"key": "pricing_terms", "label": "Pricing Terms", "type": "textarea"},
        {"key": "term", "label": "Term (years)", "type": "text", "required": True},
    ],
    "Franchise Agreement": [
        {"key": "franchisor_name", "label": "Franchisor Name", "type": "text", "required": True},
        {"key": "franchisee_name", "label": "Franchisee Name", "type": "text", "required": True},
        {"key": "franchise_location", "label": "Franchise Location", "type": "text", "required": True},
        {"key": "initial_fee", "label": "Initial Franchise Fee (KES)", "type": "text", "required": True},
        {"key": "royalty_rate", "label": "Royalty Rate (%)", "type": "text", "required": True},
        {"key": "advertising_fee", "label": "Advertising Fee (%)", "type": "text"},
        {"key": "term", "label": "Term (years)", "type": "text", "required": True},
        {"key": "renewal_option", "label": "Renewal Option", "type": "text", "default": "Yes"},
    ],
    "Memorandum of Understanding (MOU)": [
        {"key": "party_a", "label": "Party A", "type": "text", "required": True},
        {"key": "party_b", "label": "Party B", "type": "text", "required": True},
        {"key": "purpose", "label": "Purpose of MOU", "type": "textarea", "required": True},
        {"key": "scope", "label": "Scope of Cooperation", "type": "textarea", "required": True},
        {"key": "binding", "label": "Legally Binding", "type": "text", "default": "Non-binding"},
        {"key": "effective_date", "label": "Effective Date", "type": "date"},
        {"key": "duration", "label": "Duration", "type": "text"},
    ],
    "Settlement Agreement": [
        {"key": "party_a", "label": "Party A", "type": "text", "required": True},
        {"key": "party_b", "label": "Party B", "type": "text", "required": True},
        {"key": "dispute_description", "label": "Dispute Description", "type": "textarea", "required": True},
        {"key": "settlement_terms", "label": "Settlement Terms", "type": "textarea", "required": True},
        {"key": "payment_amount", "label": "Settlement Amount (KES)", "type": "text"},
        {"key": "payment_schedule", "label": "Payment Schedule", "type": "textarea"},
        {"key": "release_claims", "label": "Full Release of Claims", "type": "text", "default": "Yes"},
    ],
    "Deed of Assignment": [
        {"key": "assignor_name", "label": "Assignor Name", "type": "text", "required": True},
        {"key": "assignee_name", "label": "Assignee Name", "type": "text", "required": True},
        {"key": "rights_assigned", "label": "Rights Being Assigned", "type": "textarea", "required": True},
        {"key": "consideration", "label": "Consideration (KES)", "type": "text"},
        {"key": "effective_date", "label": "Effective Date", "type": "date"},
    ],
    "Deed of Guarantee": [
        {"key": "guarantor_name", "label": "Guarantor Name", "type": "text", "required": True},
        {"key": "guarantor_id", "label": "Guarantor ID", "type": "text", "required": True},
        {"key": "creditor_name", "label": "Creditor Name", "type": "text", "required": True},
        {"key": "principal_debtor", "label": "Principal Debtor", "type": "text", "required": True},
        {"key": "guaranteed_amount", "label": "Guaranteed Amount (KES)", "type": "text", "required": True},
        {"key": "obligation_description", "label": "Obligation Description", "type": "textarea", "required": True},
    ],
    "Deed of Indemnity": [
        {"key": "indemnifier_name", "label": "Indemnifier Name", "type": "text", "required": True},
        {"key": "indemnitee_name", "label": "Indemnitee Name", "type": "text", "required": True},
        {"key": "indemnity_scope", "label": "Scope of Indemnity", "type": "textarea", "required": True},
        {"key": "maximum_liability", "label": "Maximum Liability (KES)", "type": "text"},
        {"key": "effective_date", "label": "Effective Date", "type": "date"},
    ],
    "Supply Agreement": [
        {"key": "supplier_name", "label": "Supplier Name", "type": "text", "required": True},
        {"key": "buyer_name", "label": "Buyer Name", "type": "text", "required": True},
        {"key": "products_description", "label": "Products Description", "type": "textarea", "required": True},
        {"key": "quantities", "label": "Quantities", "type": "textarea"},
        {"key": "pricing", "label": "Pricing Terms", "type": "textarea", "required": True},
        {"key": "delivery_terms", "label": "Delivery Terms", "type": "textarea"},
        {"key": "payment_terms", "label": "Payment Terms", "type": "text"},
        {"key": "term", "label": "Term (years)", "type": "text"},
    ],
    "Software License Agreement": [
        {"key": "licensor_name", "label": "Licensor Name", "type": "text", "required": True},
        {"key": "licensee_name", "label": "Licensee Name", "type": "text", "required": True},
        {"key": "software_description", "label": "Software Description", "type": "textarea", "required": True},
        {"key": "license_type", "label": "License Type", "type": "text", "default": "Non-exclusive"},
        {"key": "license_fee", "label": "License Fee (KES)", "type": "text", "required": True},
        {"key": "number_users", "label": "Number of Users", "type": "text"},
        {"key": "term", "label": "Term", "type": "text"},
        {"key": "support_maintenance", "label": "Support & Maintenance", "type": "text", "default": "Included"},
    ],
    "Intellectual Property Assignment": [
        {"key": "assignor_name", "label": "Assignor Name", "type": "text", "required": True},
        {"key": "assignee_name", "label": "Assignee Name", "type": "text", "required": True},
        {"key": "ip_description", "label": "IP Description", "type": "textarea", "required": True},
        {"key": "ip_type", "label": "IP Type", "type": "text", "required": True},
        {"key": "consideration", "label": "Consideration (KES)", "type": "text", "required": True},
        {"key": "warranties", "label": "Warranties", "type": "textarea"},
    ],
    "Construction Contract": [
        {"key": "employer_name", "label": "Employer Name", "type": "text", "required": True},
        {"key": "contractor_name", "label": "Contractor Name", "type": "text", "required": True},
        {"key": "project_description", "label": "Project Description", "type": "textarea", "required": True},
        {"key": "site_location", "label": "Site Location", "type": "text", "required": True},
        {"key": "contract_sum", "label": "Contract Sum (KES)", "type": "text", "required": True},
        {"key": "completion_period", "label": "Completion Period (months)", "type": "text", "required": True},
        {"key": "commencement_date", "label": "Commencement Date", "type": "date"},
        {"key": "retention_percentage", "label": "Retention Percentage (%)", "type": "text", "default": "5"},
        {"key": "liquidated_damages", "label": "Liquidated Damages (KES/day)", "type": "text"},
    ],
    "Catering Agreement": [
        {"key": "client_name", "label": "Client Name", "type": "text", "required": True},
        {"key": "caterer_name", "label": "Caterer Name", "type": "text", "required": True},
        {"key": "event_description", "label": "Event Description", "type": "textarea", "required": True},
        {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
        {"key": "venue", "label": "Venue", "type": "text", "required": True},
        {"key": "number_guests", "label": "Number of Guests", "type": "text", "required": True},
        {"key": "menu", "label": "Menu Details", "type": "textarea", "required": True},
        {"key": "total_cost", "label": "Total Cost (KES)", "type": "text", "required": True},
        {"key": "deposit", "label": "Deposit (KES)", "type": "text"},
    ],
    "Security Services Agreement": [
        {"key": "client_name", "label": "Client Name", "type": "text", "required": True},
        {"key": "security_company", "label": "Security Company", "type": "text", "required": True},
        {"key": "premises", "label": "Premises to be Secured", "type": "textarea", "required": True},
        {"key": "services_scope", "label": "Services Scope", "type": "textarea", "required": True},
        {"key": "number_guards", "label": "Number of Guards", "type": "text", "required": True},
        {"key": "monthly_fee", "label": "Monthly Fee (KES)", "type": "text", "required": True},
        {"key": "hours_operation", "label": "Hours of Operation", "type": "text"},
        {"key": "term", "label": "Term (months)", "type": "text"},
    ],
    "Will": [
        {"key": "testator_name", "label": "Testator Name", "type": "text", "required": True},
        {"key": "testator_id", "label": "Testator ID/Passport", "type": "text", "required": True},
        {"key": "executor_name", "label": "Executor Name", "type": "text", "required": True},
        {"key": "executor_id", "label": "Executor ID/Passport", "type": "text", "required": True},
        {"key": "beneficiaries", "label": "Beneficiaries (Comma separated)", "type": "textarea", "required": True},
        {"key": "assets_distribution", "label": "Distribution of Assets", "type": "textarea", "required": True},
        {"key": "guardian_name", "label": "Guardian for Minors", "type": "text"},
        {"key": "signing_date", "label": "Signing Date", "type": "date"},
    ],
    # Affidavit schemas
    "Name Change/Confirmation": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID/Passport Number", "type": "text", "required": True},
        {"key": "previous_name", "label": "Previous Name", "type": "text", "required": True},
        {"key": "new_name", "label": "New Name", "type": "text", "required": True},
        {"key": "reason", "label": "Reason for Name Change", "type": "textarea", "required": True},
        {"key": "address", "label": "Physical Address", "type": "textarea", "required": True},
    ],
    "NTSA Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "vehicle_registration", "label": "Vehicle Registration Number", "type": "text", "required": True},
        {"key": "purpose", "label": "Purpose (e.g., Lost Logbook, Transfer)", "type": "text", "required": True},
        {"key": "circumstances", "label": "Circumstances", "type": "textarea", "required": True},
    ],
    "Bank Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "account_number", "label": "Account Number", "type": "text"},
        {"key": "bank_name", "label": "Bank Name", "type": "text", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Post Mortem": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "deceased_name", "label": "Name of Deceased", "type": "text", "required": True},
        {"key": "date_of_death", "label": "Date of Death", "type": "date", "required": True},
        {"key": "relationship", "label": "Relationship to Deceased", "type": "text", "required": True},
        {"key": "circumstances", "label": "Circumstances", "type": "textarea", "required": True},
    ],
    "Marriage Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "marital_status", "label": "Marital Status", "type": "text", "required": True},
        {"key": "spouse_name", "label": "Spouse's Name (if applicable)", "type": "text"},
        {"key": "marriage_date", "label": "Date of Marriage (if applicable)", "type": "date"},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Lost Documents": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "document_type", "label": "Type of Document Lost", "type": "text", "required": True},
        {"key": "document_number", "label": "Document Number (if known)", "type": "text"},
        {"key": "date_lost", "label": "Date Lost", "type": "date"},
        {"key": "circumstances", "label": "Circumstances of Loss", "type": "textarea", "required": True},
    ],
    "One-and-the-Same Person": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "alternative_names", "label": "Alternative Names Used", "type": "textarea", "required": True},
        {"key": "explanation", "label": "Explanation", "type": "textarea", "required": True},
    ],
    "Withdrawal of Case": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "case_number", "label": "Case Number", "type": "text", "required": True},
        {"key": "court_name", "label": "Court Name", "type": "text", "required": True},
        {"key": "reason", "label": "Reason for Withdrawal", "type": "textarea", "required": True},
    ],
    "Thumb-print (Illiterate Deponent)": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "interpreter_name", "label": "Interpreter's Name", "type": "text", "required": True},
        {"key": "content_explained", "label": "Content Explained", "type": "textarea", "required": True},
    ],
    "Birth Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "child_name", "label": "Child's Name", "type": "text", "required": True},
        {"key": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True},
        {"key": "place_of_birth", "label": "Place of Birth", "type": "text", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Change of Beneficiary": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "policy_number", "label": "Policy/Account Number", "type": "text", "required": True},
        {"key": "previous_beneficiary", "label": "Previous Beneficiary", "type": "text", "required": True},
        {"key": "new_beneficiary", "label": "New Beneficiary", "type": "text", "required": True},
        {"key": "reason", "label": "Reason for Change", "type": "textarea", "required": True},
    ],
    "Correction of Name in Documents": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "document_type", "label": "Document Type", "type": "text", "required": True},
        {"key": "incorrect_name", "label": "Incorrect Name", "type": "text", "required": True},
        {"key": "correct_name", "label": "Correct Name", "type": "text", "required": True},
        {"key": "explanation", "label": "Explanation", "type": "textarea", "required": True},
    ],
    "Single Status Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Consent to Travel (Minor)": [
        {"key": "parent_name", "label": "Parent/Guardian Name", "type": "text", "required": True},
        {"key": "parent_id", "label": "Parent/Guardian ID", "type": "text", "required": True},
        {"key": "child_name", "label": "Child's Full Name", "type": "text", "required": True},
        {"key": "child_passport", "label": "Child's Passport Number", "type": "text", "required": True},
        {"key": "destination", "label": "Destination Country", "type": "text", "required": True},
        {"key": "travel_dates", "label": "Travel Dates", "type": "text", "required": True},
        {"key": "accompanying_person", "label": "Accompanying Person", "type": "text", "required": True},
    ],
    "Support Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "beneficiary_name", "label": "Beneficiary Name", "type": "text", "required": True},
        {"key": "relationship", "label": "Relationship", "type": "text", "required": True},
        {"key": "support_details", "label": "Details of Support", "type": "textarea", "required": True},
    ],
    "Age Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Survivorship Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "deceased_name", "label": "Name of Deceased", "type": "text", "required": True},
        {"key": "date_of_death", "label": "Date of Death", "type": "date", "required": True},
        {"key": "relationship", "label": "Relationship to Deceased", "type": "text", "required": True},
        {"key": "joint_asset", "label": "Joint Asset Description", "type": "textarea", "required": True},
    ],
    "Heirship Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "deceased_name", "label": "Name of Deceased", "type": "text", "required": True},
        {"key": "date_of_death", "label": "Date of Death", "type": "date", "required": True},
        {"key": "relationship", "label": "Relationship to Deceased", "type": "text", "required": True},
        {"key": "heirs_list", "label": "List of Legal Heirs", "type": "textarea", "required": True},
    ],
    "Search Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "property_description", "label": "Property Description", "type": "textarea", "required": True},
        {"key": "search_purpose", "label": "Purpose of Search", "type": "textarea", "required": True},
    ],
    "Service Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "case_number", "label": "Case Number", "type": "text", "required": True},
        {"key": "served_person", "label": "Person Served", "type": "text", "required": True},
        {"key": "date_served", "label": "Date of Service", "type": "date", "required": True},
        {"key": "manner_of_service", "label": "Manner of Service", "type": "textarea", "required": True},
    ],
    "Verification Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "facts_verified", "label": "Facts Being Verified", "type": "textarea", "required": True},
        {"key": "basis_knowledge", "label": "Basis of Knowledge", "type": "textarea", "required": True},
    ],
    "Financial Status Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "monthly_income", "label": "Monthly Income (KES)", "type": "text", "required": True},
        {"key": "monthly_expenses", "label": "Monthly Expenses (KES)", "type": "text", "required": True},
        {"key": "assets", "label": "Assets", "type": "textarea"},
        {"key": "liabilities", "label": "Liabilities", "type": "textarea"},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Residence Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "current_address", "label": "Current Address", "type": "textarea", "required": True},
        {"key": "duration_residence", "label": "Duration of Residence", "type": "text", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
    "Good Conduct Affidavit": [
        {"key": "deponent_name", "label": "Deponent's Full Name", "type": "text", "required": True},
        {"key": "id_number", "label": "ID Number", "type": "text", "required": True},
        {"key": "period_covered", "label": "Period Covered", "type": "text", "required": True},
        {"key": "conduct_details", "label": "Details of Good Conduct", "type": "textarea", "required": True},
        {"key": "purpose", "label": "Purpose", "type": "textarea", "required": True},
    ],
}

# Default document types
DEFAULT_DOC_TYPES = ["Agreement", "Affidavit", "Will", "Power of Attorney"]


def render_new_matter_modal():
    """Modal for creating a new matter and generating the first document."""
    
    # Only show if flag is True
    if not st.session_state.get("show_new_matter", False):
        return
    
    # Check if we're in "wait for generation" mode
    if st.session_state.get("wait_for_generation_start", False):
        # Show loading state while waiting for generation to confirm
        @st.dialog("Creating Document...", width="large")
        def wait_dialog():
            st.info("🔄 Setting up your document generation...")
            st.markdown("Please wait while we prepare your document...")
        
        wait_dialog()
        return
    
    # Determine mode: new_matter or new_document (adding to existing matter)
    mode = st.session_state.get("modal_mode", "new_matter")
    existing_matter_id = st.session_state.get("existing_matter_id")
    
    # Fetch existing matter if in new_document mode
    existing_matter = None
    if mode == "new_document" and existing_matter_id:
        from database import DatabaseManager
        db = DatabaseManager()
        db.set_user(st.session_state.user_id)
        existing_matter = db.get_matter(existing_matter_id)
    
    title = "Create New Matter" if mode == "new_matter" else f"Add Document to {existing_matter['name'] if existing_matter else 'Matter'}"
    
    @st.dialog(title, width="large")
    def modal_content():
        st.markdown("""
        <style>
        .sc-modal-body {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .sc-modal-body::-webkit-scrollbar {
            width: 8px;
        }
        .sc-modal-body::-webkit-scrollbar-track {
            background: #1A1D24;
            border-radius: 4px;
        }
        .sc-modal-body::-webkit-scrollbar-thumb {
            background: #252930;
            border-radius: 4px;
        }
        .sc-modal-body::-webkit-scrollbar-thumb:hover {
            background: #2C3039;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Matter details (only show for new matter)
        if mode == "new_matter":
            st.subheader("Matter Details")
            with st.container():
                matter_name = st.text_input("Matter Name*", placeholder="e.g., Smith Property Sale", key="nm_matter_name")
                client = st.text_input("Client*", placeholder="e.g., John Smith", key="nm_client")
                
                col1, col2 = st.columns(2)
                with col1:
                    doc_type = st.selectbox("Document Type*", DEFAULT_DOC_TYPES, key="nm_doc_type")
                counterparty = st.text_input("Counterparty", placeholder="(Optional)", key="nm_counterparty")
                
            internal_ref = st.text_input("Internal Reference", placeholder="(Optional)", key="nm_internal_ref")
            st.divider()
        else:
            doc_type = st.selectbox("Document Type*", DEFAULT_DOC_TYPES, key="nm_doc_type")
            matter_name = existing_matter["name"]
            client = existing_matter["client_name"]
            counterparty = existing_matter.get("counterparty") or ""
            internal_ref = existing_matter.get("internal_reference") or ""
            st.divider()
        
        selected_subtype = None
        subtypes = DOC_SUBTYPES.get(doc_type, [])
        
        if subtypes:
            st.subheader(f"{doc_type} Type")
            subtype_cols = st.columns(2)
            selected_subtypes = []
            
            for idx, subtype in enumerate(subtypes):
                col_idx = idx % 2
                with subtype_cols[col_idx]:
                    if st.toggle(subtype, key=f"nm_subtype_{subtype}", value=False):
                        selected_subtypes.append(subtype)
            
            if len(selected_subtypes) > 1:
                st.warning("Please select only one document subtype")
                selected_subtype = None
            elif len(selected_subtypes) == 1:
                selected_subtype = selected_subtypes[0]
                st.session_state.selected_subtype = selected_subtype
            else:
                selected_subtype = None
                st.session_state.selected_subtype = None
            st.divider()
        else:
            selected_subtype = doc_type
            st.session_state.selected_subtype = selected_subtype
        
        st.subheader("Key Terms")
        st.markdown('<div class="sc-modal-body">', unsafe_allow_html=True)
        
        dynamic_values = {}
        if selected_subtype:
            schema = DOC_SCHEMAS.get(selected_subtype, [])
        else:
            schema = []
            if subtypes:
                st.info(f"Please select a {doc_type.lower()} type above to see key terms")
        
        for field in schema:
            key = field["key"]
            label = field["label"]
            field_type = field.get("type", "text")
            default = field.get("default", "")
            required = field.get("required", False)
            field_label = f"{label}*" if required else label
            
            if field_type == "text":
                dynamic_values[key] = st.text_input(field_label, value=default if isinstance(default, str) else "", key=f"nm_field_{key}")
            elif field_type == "textarea":
                dynamic_values[key] = st.text_area(field_label, value=default if isinstance(default, str) else "", key=f"nm_field_{key}", height=80)
            elif field_type == "date":
                date_value = st.date_input(field_label, key=f"nm_field_{key}")
                dynamic_values[key] = date_value.isoformat() if date_value else None
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        required_fields = {"Matter Name": matter_name, "Client": client} if mode == "new_matter" else {}
        if subtypes and not selected_subtype:
            required_fields[f"{doc_type} Type"] = None
        for field in schema:
            if field.get("required"):
                required_fields[field["label"]] = dynamic_values.get(field["key"])
        
        missing_fields = [name for name, value in required_fields.items() if not value]
        if missing_fields:
            st.warning(f"Please complete: {', '.join(missing_fields)}")
        
        st.divider()
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            if st.button("Cancel", use_container_width=True, key="nm_cancel"):
                st.session_state.show_new_matter = False
                st.session_state.modal_mode = "new_matter"
                st.session_state.existing_matter_id = None
                st.rerun()
        
        with col_right:
            button_text = "Create & Generate" if mode == "new_matter" else "Add & Generate"
            if st.button(button_text, type="primary", use_container_width=True, key="nm_create"):
                if missing_fields:
                    st.error("Please fill in all required fields")
                else:
                    # PAYWALL CHECK: Ensure user has credits or active subscription
                    from subscription_manager import SubscriptionManager
                    from database import DatabaseManager
                    
                    db = DatabaseManager()
                    sub_manager = SubscriptionManager(db)
                    user_id = st.session_state.user_id
                    
                    can_generate, reason = sub_manager.can_generate_document(user_id)
                    
                    if not can_generate:
                        st.error(f"⚠️ Cannot generate document: {reason}")
                        st.markdown("""
                        <div style="background-color: rgba(255, 75, 75, 0.1); border: 1px solid rgba(255, 75, 75, 0.2); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <p style="margin: 0; color: #ff6b6b; font-size: 14px;">
                                Please upgrade your plan or add more seats to continue.
                            </p>
                            <a href="?view=pricing" target="_self" style="display: inline-block; margin-top: 10px; background-color: #ff4b4b; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: 500;">
                                View Pricing Options
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        return # Stop execution
                        
                    payload = {
                        "matter": {
                            "name": matter_name.strip() if matter_name else "",
                            "client": client.strip() if client else "",
                            "counterparty": counterparty.strip() if counterparty else "",
                            "internal_ref": internal_ref.strip() if internal_ref else "",
                        },
                        "document": {
                            "type": doc_type,
                            "subtype": selected_subtype if selected_subtype != doc_type else None,
                            "variables": dynamic_values,
                        },
                        "generation_config": {"jurisdiction": "Kenya", "language": "English", "model": "gpt-4o-mini"}
                    }
                    
                    from database import DatabaseManager
                    db = DatabaseManager()
                    db.set_user(st.session_state.user_id)
                    
                    try:
                        if mode == "new_matter":
                            matter = db.create_matter(
                                name=matter_name.strip() if matter_name else "",
                                client_name=client.strip() if client else "",
                                counterparty=counterparty.strip() if counterparty else None,
                                internal_reference=internal_ref.strip() if internal_ref else None,
                                matter_type=doc_type,
                                jurisdiction="Kenya"
                            )
                            matter_id = matter["id"]
                        else:
                            matter_id = existing_matter_id
                        
                        document_title = f"{selected_subtype or doc_type} - {client.strip() if client else 'Client'}"
                        document = db.create_document(
                            matter_id=matter_id,
                            title=document_title,
                            document_type=doc_type,
                            document_subtype=selected_subtype,
                            generation_payload=payload
                        )
                        
                        # Record document usage for subscription tracking
                        try:
                            usage_recorded = sub_manager.record_document_generation(
                                user_id, 
                                document_type=selected_subtype or doc_type
                            )
                            if usage_recorded:
                                print(f"✅ Document usage recorded for user {user_id}")
                            else:
                                print(f"⚠️ Failed to record document usage for user{user_id}")
                        except Exception as usage_error:
                            print(f"⚠️ Document usage tracking error: {usage_error}")
                            # Don't block document creation if usage tracking fails
                        
                        # CRITICAL FIX: Set state to wait for generation confirmation
                        st.session_state.current_matter_id = matter_id
                        st.session_state.current_document_id = document["id"]
                        st.session_state.new_matter_payload = payload
                        st.session_state.wait_for_generation_start = True
                        st.session_state.generation_complete = False
                        

                        # Navigate to editor
                        from auth import update_query_params
                        update_query_params({"view": "editor"})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    modal_content()


def open_new_matter_modal():
    """Helper function to trigger modal opening."""
    st.session_state.show_new_matter = True