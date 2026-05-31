"""
seed_banking_db.py
==================
Full banking database seed — respects the production schema.
Bank: Kairos Bank Mozambique S.A.
Account prefix: 00830 (Kairos internal)

Generates:
  - Reference data (countries, currencies, banks, branches)
  - 200 corporate customers with addresses and signatories
  - 400 accounts
  - 2000 transactions:
      1000 EFT  (750 us-on-us, 250 us-on-them)
       500 IFT
       500 CTR
  - 50 loans with collateral
  - AML alerts for suspicious transactions

Run:
    python seed_banking_db.py
    → creates kairos_banking.db
"""

import argparse
import sqlite3
import random
import string
from datetime import datetime, date, timedelta

random.seed(99)

DB_PATH = "kairos_banking.db"

# ── Kairos Bank identity ───────────────────────────────────────────────────
KAIROS_BANK_ID        = 1
KAIROS_BANK_NAME      = "Kairos Bank Mozambique S.A."
KAIROS_SWIFT          = "KAIRSMZM"
KAIROS_BANK_CODE      = "00830"
KAIROS_ACCOUNT_PREFIX = "008301"   # all internal accounts start with this

# ── Reference pools ────────────────────────────────────────────────────────
PROVINCES = [
    "Maputo Cidade", "Maputo Província", "Gaza", "Inhambane",
    "Sofala", "Manica", "Tete", "Zambézia", "Nampula",
    "Cabo Delgado", "Niassa",
]

BUSINESS_TYPES = [
    "Comércio Geral", "Serviços Financeiros", "Construção Civil",
    "Transportes e Logística", "Agricultura e Pecuária",
    "Indústria Transformadora", "Tecnologia de Informação",
    "Saúde e Farmácia", "Educação", "Hotelaria e Turismo",
    "Importação e Exportação", "Consultoria e Assessoria",
    "Energia e Recursos Naturais", "Telecomunicações",
]

FIRST_NAMES = [
    "João", "Maria", "António", "Fátima", "Carlos", "Ana",
    "Manuel", "Sofia", "Pedro", "Isabel", "Luís", "Beatriz",
    "Fernando", "Cristina", "Rodrigo", "Paula", "Eduardo", "Sandra",
    "Miguel", "Carla", "Álvaro", "Teresa", "Nuno", "Margarida",
    "Domingos", "Celeste", "Adriano", "Graça", "Felício", "Esperança",
    "Hélder", "Dina", "Narciso", "Lurdes", "Ernesto", "Conceição",
]

LAST_NAMES = [
    "Machava", "Mabunda", "Nhantumbo", "Sitoe", "Tembe",
    "Cossa", "Mondlane", "Machangana", "Nhavene", "Chibuto",
    "Munguambe", "Bila", "Chaúque", "Muianga", "Nhateve",
    "Magaia", "Cumbe", "Macamo", "Muchanga", "Chemane",
    "Vilanculos", "Zunguze", "Mahumane", "Guambe", "Nguenha",
    "Matsimbe", "Nhacuamba", "Cuvele", "Pateguana", "Uamusse",
]

EXTERNAL_BANKS = [
    ("Banco Comercial e de Investimentos", "BCIMMZMM", "00100"),
    ("Millennium BIM",                     "BIMMZMM1", "00200"),
    ("Absa Bank Mozambique",               "ABSAMAMX", "00300"),
    ("Société Générale Mozambique",        "SOGEMZMM", "00400"),
    ("Nedbank Mozambique",                 "NEDBMZMM", "00500"),
    ("First Capital Bank",                 "FCBKMZMM", "00600"),
    ("African Banking Corporation",        "ABCBMZMM", "00700"),
    ("FNB Mozambique",                     "FNBSMZMM", "00800"),
    ("Moza Banco",                         "MOZAMZMM", "00900"),
]

FOREIGN_BANKS = [
    ("Standard Bank South Africa",         "SBZAZAJJ", "ZA"),
    ("Barclays Bank UK",                   "BARCGB22", "GB"),
    ("Deutsche Bank AG",                   "DEUTDEDB", "DE"),
    ("Citibank N.A.",                      "CITIUS33", "US"),
    ("BNP Paribas",                        "BNPAFRPP", "FR"),
    ("HSBC Bank",                          "HSBCGB2L", "GB"),
    ("Absa Group Limited",                 "ABSAZAJJ", "ZA"),
    ("Nedbank Group",                      "NEDSZA22", "ZA"),
    ("Investec Bank",                      "INVEJOHA", "ZA"),
    ("Banco Espirito Santo Angola",        "BESAANLA", "AO"),
]

COUNTRIES_DATA = [
    ("MZ", "Mozambique",     "MOZ", "LOW",    False, False),
    ("ZA", "South Africa",   "ZAF", "LOW",    False, False),
    ("PT", "Portugal",       "PRT", "LOW",    False, False),
    ("GB", "United Kingdom", "GBR", "LOW",    False, False),
    ("DE", "Germany",        "DEU", "LOW",    False, False),
    ("US", "United States",  "USA", "LOW",    False, False),
    ("FR", "France",         "FRA", "LOW",    False, False),
    ("AO", "Angola",         "AGO", "MEDIUM", False, False),
    ("TZ", "Tanzania",       "TZA", "LOW",    False, False),
    ("ZW", "Zimbabwe",       "ZWE", "HIGH",   False, True),
    ("IR", "Iran",           "IRN", "HIGH",   True,  True),
    ("KP", "North Korea",    "PRK", "HIGH",   True,  True),
    ("RU", "Russia",         "RUS", "HIGH",   False, True),
    ("CN", "China",          "CHN", "MEDIUM", False, False),
    ("IN", "India",          "IND", "LOW",    False, False),
    ("BR", "Brazil",         "BRA", "MEDIUM", False, False),
    ("AE", "UAE",            "ARE", "MEDIUM", False, False),
]

CURRENCIES_DATA = [
    ("MZN", "Metical Moçambicano",  "MT",  2, "MZ"),
    ("USD", "US Dollar",            "$",   2, "US"),
    ("EUR", "Euro",                 "€",   2, "PT"),
    ("ZAR", "Rand Sul-Africano",    "R",   2, "ZA"),
    ("GBP", "Pound Sterling",       "£",   2, "GB"),
    ("AOA", "Kwanza Angolano",      "Kz",  2, "AO"),
    ("TZS", "Tanzanian Shilling",   "TSh", 2, "TZ"),
]

TX_TYPES = [
    ("EFT",  "Electronic Fund Transfer",      False, True),
    ("IFT",  "International Fund Transfer",   False, True),
    ("CTR",  "Cash Transaction",              True,  True),
    ("DEPO", "Cash Deposit",                  True,  False),
    ("WITH", "Cash Withdrawal",               True,  False),
    ("LOAN", "Loan Disbursement",             False, False),
]

CHANNELS = [
    ("BRANCH",  "Branch Counter"),
    ("ATM",     "ATM"),
    ("ONLINE",  "Internet Banking"),
    ("MOBILE",  "Mobile Banking"),
    ("SWIFT",   "SWIFT Wire"),
    ("TELLER",  "Teller"),
]


# ── Helpers ────────────────────────────────────────────────────────────────
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def rand_date(y1=2000, y2=2025) -> str:
    d = date(y1, 1, 1) + timedelta(days=random.randint(0, (date(y2, 12, 31)-date(y1, 1, 1)).days))
    return d.strftime("%Y-%m-%d")

def rand_tx_date() -> str:
    d = date(2026, 1, 1) + timedelta(days=random.randint(0, 147))
    t = f"{random.randint(7,18):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
    return f"{d} {t}"

def rand_nuit() -> str:
    return str(random.randint(100_000_000, 999_999_999))

def rand_phone() -> str:
    p = random.choice(["21", "84", "85", "86", "87", "82", "83"])
    return "258" + p + "".join([str(random.randint(0,9)) for _ in range(7)])

def rand_email(name: str) -> str:
    clean = name.lower().replace(" ", ".").replace(",","")[:20]
    domains = ["gmail.com", "yahoo.com", "co.mz", "outlook.com"]
    return f"{clean}@{random.choice(domains)}"

def rand_account_kairos() -> str:
    return KAIROS_ACCOUNT_PREFIX + "".join([str(random.randint(0,9)) for _ in range(8)])

def rand_account_external(prefix: str) -> str:
    return prefix + "".join([str(random.randint(0,9)) for _ in range(9)])

def rand_iban_foreign() -> str:
    cc = random.choice(["ZA", "GB", "DE", "PT"])
    return cc + "".join([str(random.randint(0,9)) for _ in range(20)])

def rand_cif() -> str:
    return "KMZ" + "".join([str(random.randint(0,9)) for _ in range(8)])

def rand_id_number() -> str:
    return "".join([str(random.randint(0,9)) for _ in range(12)])

def rand_name() -> tuple:
    f = random.choice(FIRST_NAMES)
    m = random.choice(LAST_NAMES) if random.random() > 0.4 else ""
    l = random.choice(LAST_NAMES)
    full = f"{f} {m} {l}".strip() if m else f"{f} {l}"
    return full, f, m, l

def rand_company() -> str:
    opts = [
        f"{random.choice(LAST_NAMES)} & {random.choice(LAST_NAMES)} {random.choice(['Lda','S.A.','SARL'])}",
        f"Grupo {random.choice(LAST_NAMES)} {random.choice(['Lda','S.A.'])}",
        f"Moçambique {random.choice(BUSINESS_TYPES[:8])} {random.choice(['Lda','S.A.'])}",
        f"{random.choice(LAST_NAMES)} {random.choice(BUSINESS_TYPES[4:])} Lda",
    ]
    return random.choice(opts)

def rand_amount(low, high, threshold=None, above_pct=0.6) -> float:
    if threshold and random.random() < above_pct:
        return round(random.uniform(threshold * 1.01, high), 2)
    return round(random.uniform(low, threshold * 0.99 if threshold else high), 2)


# ── Schema creation ────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS countries (
    country_code        TEXT PRIMARY KEY,
    country_name        TEXT,
    iso3_code           TEXT,
    risk_level          TEXT,
    sanctions_flag      INTEGER,
    fatf_watchlist_flag INTEGER
);

CREATE TABLE IF NOT EXISTS currencies (
    currency_code   TEXT PRIMARY KEY,
    currency_name   TEXT,
    currency_symbol TEXT,
    decimal_places  INTEGER,
    country_code    TEXT,
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS banks (
    bank_id             INTEGER PRIMARY KEY,
    bank_name           TEXT,
    swift_code          TEXT,
    bank_code           TEXT,
    country_code        TEXT,
    city                TEXT,
    address             TEXT,
    regulatory_license  TEXT,
    created_at          TEXT,
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS branches (
    branch_id       INTEGER PRIMARY KEY,
    bank_id         INTEGER,
    branch_code     TEXT,
    branch_name     TEXT,
    city            TEXT,
    country_code    TEXT,
    address         TEXT,
    phone_number    TEXT,
    FOREIGN KEY (bank_id) REFERENCES banks(bank_id),
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id             INTEGER PRIMARY KEY,
    customer_type           TEXT,
    customer_name           TEXT,
    first_name              TEXT,
    middle_name             TEXT,
    last_name               TEXT,
    gender                  TEXT,
    marital_status          TEXT,
    date_of_birth           TEXT,
    incorporation_date      TEXT,
    nationality_code        TEXT,
    country_of_residence    TEXT,
    id_type                 TEXT,
    id_number               TEXT,
    tax_number              TEXT,
    phone_number            TEXT,
    email                   TEXT,
    occupation              TEXT,
    employer_name           TEXT,
    industry                TEXT,
    annual_income           REAL,
    annual_turnover         REAL,
    net_worth               REAL,
    customer_segment        TEXT,
    onboarding_date         TEXT,
    relationship_manager    TEXT,
    risk_rating             TEXT,
    aml_risk_score          REAL,
    pep_flag                INTEGER,
    sanctions_flag          INTEGER,
    deceased_flag           INTEGER,
    customer_status         TEXT,
    created_at              TEXT,
    updated_at              TEXT,
    FOREIGN KEY (nationality_code) REFERENCES countries(country_code),
    FOREIGN KEY (country_of_residence) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS customer_addresses (
    address_id      INTEGER PRIMARY KEY,
    customer_id     INTEGER,
    address_type    TEXT,
    address_line1   TEXT,
    address_line2   TEXT,
    city            TEXT,
    province        TEXT,
    postal_code     TEXT,
    country_code    TEXT,
    start_date      TEXT,
    end_date        TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id              INTEGER PRIMARY KEY,
    customer_id             INTEGER,
    branch_id               INTEGER,
    account_number          TEXT UNIQUE,
    iban                    TEXT,
    account_type            TEXT,
    currency_code           TEXT,
    account_status          TEXT,
    opening_date            TEXT,
    closing_date            TEXT,
    available_balance       REAL,
    ledger_balance          REAL,
    overdraft_limit         REAL,
    interest_rate           REAL,
    dormant_flag            INTEGER,
    last_transaction_date   TEXT,
    created_at              TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id),
    FOREIGN KEY (currency_code) REFERENCES currencies(currency_code)
);

CREATE TABLE IF NOT EXISTS signatories (
    signatory_id        INTEGER PRIMARY KEY,
    full_name           TEXT,
    date_of_birth       TEXT,
    nationality_code    TEXT,
    id_type             TEXT,
    id_number           TEXT,
    phone_number        TEXT,
    email               TEXT,
    occupation          TEXT,
    is_bank_customer    INTEGER,
    linked_customer_id  INTEGER,
    pep_flag            INTEGER,
    sanctions_flag      INTEGER,
    aml_risk_score      REAL,
    created_at          TEXT,
    FOREIGN KEY (linked_customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (nationality_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS corporate_account_signatories (
    mapping_id          INTEGER PRIMARY KEY,
    account_id          INTEGER,
    signatory_id        INTEGER,
    role                TEXT,
    can_view            INTEGER,
    can_authorize       INTEGER,
    signing_limit       REAL,
    mandate_start_date  TEXT,
    mandate_end_date    TEXT,
    created_at          TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (signatory_id) REFERENCES signatories(signatory_id)
);

CREATE TABLE IF NOT EXISTS transaction_types (
    transaction_type_code   TEXT PRIMARY KEY,
    transaction_type_name   TEXT,
    cash_flag               INTEGER,
    aml_high_risk_flag      INTEGER
);

CREATE TABLE IF NOT EXISTS transaction_channels (
    channel_code    TEXT PRIMARY KEY,
    channel_name    TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id              INTEGER PRIMARY KEY,
    account_id                  INTEGER,
    transaction_reference       TEXT UNIQUE,
    transaction_date            TEXT,
    value_date                  TEXT,
    transaction_type_code       TEXT,
    channel_code                TEXT,
    debit_credit_indicator      TEXT,
    amount                      REAL,
    currency_code               TEXT,
    exchange_rate               REAL,
    local_currency_amount       REAL,
    balance_after_transaction   REAL,
    counterparty_account        TEXT,
    counterparty_name           TEXT,
    counterparty_bank           TEXT,
    counterparty_swift          TEXT,
    counterparty_country        TEXT,
    originator_name             TEXT,
    beneficiary_name            TEXT,
    remittance_information      TEXT,
    merchant_name               TEXT,
    merchant_category_code      TEXT,
    atm_id                      TEXT,
    terminal_id                 TEXT,
    device_id                   TEXT,
    ip_address                  TEXT,
    geolocation                 TEXT,
    suspicious_flag             INTEGER,
    suspicious_reason           TEXT,
    structuring_flag            INTEGER,
    sanctions_match_flag        INTEGER,
    flow_type                   TEXT,
    report_type                 TEXT,
    created_at                  TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (currency_code) REFERENCES currencies(currency_code),
    FOREIGN KEY (counterparty_country) REFERENCES countries(country_code),
    FOREIGN KEY (transaction_type_code) REFERENCES transaction_types(transaction_type_code),
    FOREIGN KEY (channel_code) REFERENCES transaction_channels(channel_code)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id                 INTEGER PRIMARY KEY,
    customer_id             INTEGER,
    account_id              INTEGER,
    loan_number             TEXT UNIQUE,
    loan_type               TEXT,
    disbursement_date       TEXT,
    maturity_date           TEXT,
    original_amount         REAL,
    outstanding_principal   REAL,
    accrued_interest        REAL,
    interest_rate           REAL,
    installment_amount      REAL,
    days_past_due           INTEGER,
    stage                   TEXT,
    probability_of_default  REAL,
    loss_given_default      REAL,
    exposure_at_default     REAL,
    expected_credit_loss    REAL,
    collateral_value        REAL,
    restructuring_flag      INTEGER,
    default_flag            INTEGER,
    loan_status             TEXT,
    created_at              TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS collateral (
    collateral_id   INTEGER PRIMARY KEY,
    loan_id         INTEGER,
    collateral_type TEXT,
    description     TEXT,
    collateral_value REAL,
    valuation_date  TEXT,
    ownership_type  TEXT,
    insured_flag    INTEGER,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS cards (
    card_id                 INTEGER PRIMARY KEY,
    customer_id             INTEGER,
    account_id              INTEGER,
    card_number_masked      TEXT,
    card_type               TEXT,
    card_network            TEXT,
    issue_date              TEXT,
    expiry_date             TEXT,
    credit_limit            REAL,
    available_limit         REAL,
    card_status             TEXT,
    contactless_enabled     INTEGER,
    created_at              TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS aml_alerts (
    alert_id                INTEGER PRIMARY KEY,
    transaction_id          INTEGER,
    customer_id             INTEGER,
    alert_type              TEXT,
    alert_score             REAL,
    alert_description       TEXT,
    generated_date          TEXT,
    analyst_name            TEXT,
    investigation_status    TEXT,
    escalation_flag         INTEGER,
    sar_reported_flag       INTEGER,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS sanctions_list (
    sanctions_id        INTEGER PRIMARY KEY,
    entity_name         TEXT,
    entity_type         TEXT,
    country_code        TEXT,
    sanctions_program   TEXT,
    listing_date        TEXT,
    active_flag         INTEGER,
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

CREATE TABLE IF NOT EXISTS fx_rates (
    fx_rate_id      INTEGER PRIMARY KEY,
    from_currency   TEXT,
    to_currency     TEXT,
    rate_date       TEXT,
    exchange_rate   REAL,
    created_at      TEXT,
    FOREIGN KEY (from_currency) REFERENCES currencies(currency_code),
    FOREIGN KEY (to_currency) REFERENCES currencies(currency_code)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tx_account  ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_date     ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_tx_country  ON transactions(counterparty_country);
CREATE INDEX IF NOT EXISTS idx_tx_type     ON transactions(report_type, flow_type);
CREATE INDEX IF NOT EXISTS idx_cus_risk    ON customers(risk_rating);
CREATE INDEX IF NOT EXISTS idx_loans_stage ON loans(stage);
CREATE INDEX IF NOT EXISTS idx_alert_status ON aml_alerts(investigation_status);
"""

# ── Analytical views ───────────────────────────────────────────────────────
VIEWS = """
CREATE VIEW IF NOT EXISTS v_eft_us_on_us AS
SELECT
    t.transaction_id, t.transaction_reference, t.transaction_date,
    t.amount, t.currency_code, t.local_currency_amount,
    t.debit_credit_indicator,
    a_from.account_number   AS from_account,
    c_from.customer_name    AS from_customer_name,
    c_from.customer_id      AS from_customer_id,
    c_from.tax_number       AS from_tax_number,
    t.counterparty_account  AS to_account,
    t.counterparty_name     AS to_customer_name,
    t.remittance_information,
    t.suspicious_flag, t.structuring_flag
FROM transactions t
JOIN accounts a_from ON t.account_id = a_from.account_id
JOIN customers c_from ON a_from.customer_id = c_from.customer_id
WHERE t.report_type = 'EFT' AND t.flow_type = 'us_on_us';

CREATE VIEW IF NOT EXISTS v_eft_us_on_them AS
SELECT
    t.transaction_id, t.transaction_reference, t.transaction_date,
    t.amount, t.currency_code, t.local_currency_amount,
    t.debit_credit_indicator,
    a.account_number        AS internal_account,
    c.customer_name         AS internal_customer_name,
    c.tax_number            AS internal_tax_number,
    t.counterparty_account  AS external_account,
    t.counterparty_name     AS external_customer_name,
    t.counterparty_bank     AS external_bank,
    t.remittance_information,
    t.suspicious_flag, t.structuring_flag
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
WHERE t.report_type = 'EFT' AND t.flow_type IN ('us_on_them_debit','us_on_them_credit');

CREATE VIEW IF NOT EXISTS v_ift AS
SELECT
    t.transaction_id, t.transaction_reference, t.transaction_date,
    t.amount, t.currency_code, t.exchange_rate, t.local_currency_amount,
    t.debit_credit_indicator,
    a.account_number        AS internal_account,
    c.customer_name         AS internal_customer_name,
    c.tax_number            AS internal_tax_number,
    t.counterparty_account  AS foreign_account,
    t.counterparty_name     AS foreign_party_name,
    t.counterparty_bank     AS foreign_bank,
    t.counterparty_swift    AS foreign_swift,
    t.counterparty_country  AS foreign_country,
    t.flow_type,
    t.remittance_information,
    t.suspicious_flag, t.sanctions_match_flag
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
WHERE t.report_type = 'IFT';

CREATE VIEW IF NOT EXISTS v_ctr AS
SELECT
    t.transaction_id, t.transaction_reference, t.transaction_date,
    t.amount, t.local_currency_amount,
    t.debit_credit_indicator,
    a.account_number        AS internal_account,
    c.customer_name         AS internal_customer_name,
    c.tax_number            AS internal_tax_number,
    t.counterparty_name     AS depositor_name,
    t.flow_type,
    t.remittance_information,
    t.suspicious_flag, t.structuring_flag,
    CASE WHEN t.amount >= 250000 THEN 1 ELSE 0 END AS above_threshold
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
WHERE t.report_type = 'CTR';

CREATE VIEW IF NOT EXISTS v_threshold_summary AS
SELECT
    report_type,
    flow_type,
    COUNT(*)                                                    AS total_transactions,
    ROUND(SUM(amount),2)                                        AS total_amount,
    ROUND(AVG(amount),2)                                        AS avg_amount,
    ROUND(MAX(amount),2)                                        AS max_amount,
    SUM(CASE WHEN report_type='CTR' AND amount>=250000 THEN 1 ELSE 0 END) AS ctr_above_250k,
    SUM(CASE WHEN report_type IN ('EFT','IFT') AND amount>=750000 THEN 1 ELSE 0 END) AS eft_ift_above_750k,
    SUM(suspicious_flag)                                        AS suspicious_count,
    SUM(structuring_flag)                                       AS structuring_count
FROM transactions
GROUP BY report_type, flow_type
ORDER BY report_type, flow_type;

CREATE VIEW IF NOT EXISTS v_customer_full AS
SELECT
    c.*,
    a.account_number, a.account_type, a.currency_code,
    a.available_balance, a.account_status,
    s.full_name         AS signatory_name,
    s.id_type           AS signatory_id_type,
    s.id_number         AS signatory_id_number,
    s.phone_number      AS signatory_phone,
    s.nationality_code  AS signatory_nationality
FROM customers c
JOIN accounts a ON c.customer_id = a.customer_id
LEFT JOIN corporate_account_signatories cas ON a.account_id = cas.account_id
LEFT JOIN signatories s ON cas.signatory_id = s.signatory_id;
"""


# ── Seed functions ─────────────────────────────────────────────────────────

def seed_reference_data(c):
    print("  Reference data...")

    c.executemany(
        "INSERT OR IGNORE INTO countries VALUES (?,?,?,?,?,?)",
        COUNTRIES_DATA
    )
    c.executemany(
        "INSERT OR IGNORE INTO currencies VALUES (?,?,?,?,?)",
        CURRENCIES_DATA
    )
    c.executemany(
        "INSERT OR IGNORE INTO transaction_types VALUES (?,?,?,?)",
        TX_TYPES
    )
    c.executemany(
        "INSERT OR IGNORE INTO transaction_channels VALUES (?,?)",
        CHANNELS
    )

    # FX rates (MZN base)
    fx = [
        (1, "USD", "MZN", "2026-05-15", 63.85, now_ts()),
        (2, "EUR", "MZN", "2026-05-15", 69.20, now_ts()),
        (3, "ZAR", "MZN", "2026-05-15",  3.42, now_ts()),
        (4, "GBP", "MZN", "2026-05-15", 80.15, now_ts()),
        (5, "AOA", "MZN", "2026-05-15",  0.07, now_ts()),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO fx_rates VALUES (?,?,?,?,?,?)", fx
    )

    # Kairos Bank
    c.execute("""
        INSERT OR IGNORE INTO banks VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        KAIROS_BANK_ID, KAIROS_BANK_NAME, KAIROS_SWIFT, KAIROS_BANK_CODE,
        "MZ", "Maputo",
        "Av. 25 de Setembro n.1234, Maputo, Mozambique",
        "LIC-BM-2024-0083",
        now_ts()
    ))

    # External banks
    for i, (name, swift, code) in enumerate(EXTERNAL_BANKS, start=2):
        c.execute(
            "INSERT OR IGNORE INTO banks VALUES (?,?,?,?,?,?,?,?,?)",
            (i+1, name, swift, code, "MZ", "Maputo",
             f"Av. {random.choice(LAST_NAMES)} n.{random.randint(1,500)}, Maputo",
             f"LIC-BM-{2010+i}-{i:04d}", now_ts())
        )

    # Foreign banks
    for i, (name, swift, country) in enumerate(FOREIGN_BANKS, start=12):
        c.execute(
            "INSERT OR IGNORE INTO banks VALUES (?,?,?,?,?,?,?,?,?)",
            (i+1, name, swift, f"99{i:03d}", country, "N/A",
             "International", f"INTL-{swift}", now_ts())
        )

    # Kairos branches
    branches = [
        (1, KAIROS_BANK_ID, "KMZ-001", "Sede Maputo",      "Maputo",   "MZ", "Av. 25 de Setembro n.1234", rand_phone()),
        (2, KAIROS_BANK_ID, "KMZ-002", "Beira",            "Beira",    "MZ", "Rua Major Serpa Pinto n.45", rand_phone()),
        (3, KAIROS_BANK_ID, "KMZ-003", "Nampula",          "Nampula",  "MZ", "Av. Paulo Samuel Kankhomba n.78", rand_phone()),
        (4, KAIROS_BANK_ID, "KMZ-004", "Tete",             "Tete",     "MZ", "Av. Eduardo Mondlane n.12", rand_phone()),
        (5, KAIROS_BANK_ID, "KMZ-005", "Quelimane",        "Quelimane","MZ", "Rua Samoedi n.34", rand_phone()),
    ]
    c.executemany("INSERT OR IGNORE INTO branches VALUES (?,?,?,?,?,?,?,?)", branches)

    # Sanctions list
    sanctions = [
        (1, "Shell Company XYZ",  "ENTITY", "IR", "OFAC SDN",  "2020-01-15", 1),
        (2, "Black Market Corp",  "ENTITY", "KP", "UN Sanctions","2019-06-01",1),
        (3, "Ivan Petrov",        "PERSON", "RU", "EU Sanctions","2022-03-10",1),
        (4, "Rogue Trading Ltd",  "ENTITY", "ZW", "OFAC",       "2021-09-22", 1),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO sanctions_list VALUES (?,?,?,?,?,?,?)",
        sanctions
    )


def seed_customers_and_accounts(c, n=200):
    print(f"  {n} corporate customers, accounts, signatories...")

    customers = []
    accounts  = []
    addresses = []
    sigs      = []
    corp_sigs = []
    cards_list= []

    used_accounts = set()
    rm_names = [f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" for _ in range(10)]

    for i in range(1, n+1):
        # Customer
        company_name = rand_company()
        industry     = random.choice(BUSINESS_TYPES)
        province     = random.choice(PROVINCES)
        turnover     = round(random.uniform(500_000, 50_000_000), 2)
        risk         = random.choices(["LOW","MEDIUM","HIGH"], weights=[60,30,10])[0]
        aml_score    = round(random.uniform(0, 100), 2)
        pep          = 1 if random.random() < 0.03 else 0
        onboard      = rand_date(2015, 2024)
        nationality  = random.choices(
            ["MZ","ZA","PT","GB","AO"],
            weights=[80,8,5,4,3]
        )[0]

        customers.append((
            i,                          # customer_id
            "CORPORATE",                # customer_type
            company_name,               # customer_name
            None, None, None,           # first/middle/last (N/A for corporate)
            None, None,                 # gender, marital
            None,                       # dob
            rand_date(2000, 2020),      # incorporation_date
            nationality,                # nationality_code
            "MZ",                       # country_of_residence
            "NUIT",                     # id_type
            rand_nuit(),                # id_number
            rand_nuit(),                # tax_number
            rand_phone(),               # phone
            rand_email(company_name),   # email
            None, None,                 # occupation, employer
            industry,                   # industry
            None,                       # annual_income
            turnover,                   # annual_turnover
            round(turnover * random.uniform(0.3, 1.5), 2),  # net_worth
            random.choice(["SME","CORPORATE","PREMIUM"]),    # segment
            onboard,                    # onboarding_date
            random.choice(rm_names),    # relationship_manager
            risk,                       # risk_rating
            aml_score,                  # aml_risk_score
            pep,                        # pep_flag
            0,                          # sanctions_flag
            0,                          # deceased_flag
            "ACTIVE",                   # customer_status
            now_ts(), now_ts()
        ))

        # Address
        addresses.append((
            i, i, "BUSINESS",
            f"Av. {random.choice(LAST_NAMES)} n.{random.randint(1,999)}",
            f"Bairro {random.choice(LAST_NAMES)}",
            province.split()[0],
            province,
            f"{random.randint(1000,9999)}",
            "MZ",
            onboard, None
        ))

        # Account
        acc_num = rand_account_kairos()
        while acc_num in used_accounts:
            acc_num = rand_account_kairos()
        used_accounts.add(acc_num)

        branch_id = random.randint(1, 5)
        balance   = round(random.uniform(10_000, 5_000_000), 2)
        accounts.append((
            i,                      # account_id
            i,                      # customer_id
            branch_id,
            acc_num,
            f"MZ{acc_num}",         # iban
            random.choice(["CURRENT","SAVINGS","CORPORATE"]),
            "MZN",
            "ACTIVE",
            onboard,
            None,
            balance,
            balance,
            round(balance * 0.1, 2),
            round(random.uniform(0.5, 3.5), 4),
            0,
            rand_tx_date()[:10],
            now_ts()
        ))

        # Signatory (1 per corporate customer — mandatory)
        full_name, fn, mn, ln = rand_name()
        sig_id = i
        sig_nationality = random.choices(
            ["MZ","ZA","PT","AO"],
            weights=[80,10,7,3]
        )[0]
        doc_type = random.choices(
            ["BI","Passaporte","BI","BI"],
            weights=[70,15,10,5]
        )[0]

        sigs.append((
            sig_id,
            full_name,
            rand_date(1960, 1995),
            sig_nationality,
            doc_type,
            rand_id_number(),
            rand_phone(),
            rand_email(full_name),
            random.choice(["Director","CEO","CFO","Gerente","Administrador"]),
            0,              # is_bank_customer
            None,           # linked_customer_id
            1 if pep else 0,
            0,
            round(random.uniform(0, 60), 2),
            now_ts()
        ))

        # Corporate signatory mapping
        corp_sigs.append((
            i,              # mapping_id
            i,              # account_id
            sig_id,
            random.choice(["Director Executivo","Signatário Principal","Administrador"]),
            1, 1,           # can_view, can_authorize
            round(random.uniform(100_000, 10_000_000), 2),  # signing_limit
            onboard,
            rand_date(2030, 2035),
            now_ts()
        ))

        # Card (80% of customers have a card)
        if random.random() < 0.8:
            cards_list.append((
                i, i, i,
                f"**** **** **** {random.randint(1000,9999)}",
                random.choice(["DEBIT","CREDIT","PREPAID"]),
                random.choice(["VISA","MASTERCARD"]),
                onboard,
                rand_date(2027, 2030),
                round(random.uniform(50_000, 500_000), 2),
                round(random.uniform(10_000, 400_000), 2),
                "ACTIVE",
                1,
                now_ts()
            ))

    c.executemany("""
        INSERT OR IGNORE INTO customers VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )""", customers)

    c.executemany("""
        INSERT OR IGNORE INTO customer_addresses VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, addresses)

    c.executemany("""
        INSERT OR IGNORE INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, accounts)

    c.executemany("""
        INSERT OR IGNORE INTO signatories VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, sigs)

    c.executemany("""
        INSERT OR IGNORE INTO corporate_account_signatories VALUES (?,?,?,?,?,?,?,?,?,?)
    """, corp_sigs)

    c.executemany("""
        INSERT OR IGNORE INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, cards_list)

    return [row[3] for row in accounts]  # return account numbers


def seed_transactions(c, account_rows, n_eft_uu=750, n_eft_ut=250, n_ift=500, n_ctr=500, min_structuring: int = 0):
    print(f"  {n_eft_uu+n_eft_ut+n_ift+n_ctr} transactions...")

    # Build lookup: account_number -> account_id
    c.execute("SELECT account_id, account_number, customer_id FROM accounts")
    acc_rows  = c.fetchall()
    acc_id_by_num = {r[1]: r[0] for r in acc_rows}
    acc_nums  = [r[1] for r in acc_rows]
    cust_by_acc = {r[1]: r[2] for r in acc_rows}

    c.execute("SELECT account_id, customer_name FROM accounts a JOIN customers cu ON a.customer_id=cu.customer_id")
    name_by_acc_id = {r[0]: r[1] for r in c.fetchall()}

    txns = []
    tid  = 1

    FX = {"MZN":1.0,"USD":63.85,"EUR":69.20,"ZAR":3.42,"GBP":80.15}

    def make_tx(
        account_id, tx_ref, tx_date, tx_type, channel,
        dc, amount, currency, counterparty_acc, counterparty_name,
        counterparty_bank, counterparty_swift, counterparty_country,
        originator, beneficiary, remittance,
        flow_type, report_type,
        suspicious=0, suspicious_reason=None,
        structuring=0, sanctions=0,
    ):
        rate    = FX.get(currency, 1.0)
        local   = round(amount * rate, 2) if currency != "MZN" else amount
        bal     = round(random.uniform(50_000, 3_000_000), 2)
        return (
            tid, account_id, tx_ref,
            tx_date, tx_date[:10],
            tx_type, channel, dc,
            amount, currency, rate, local, bal,
            counterparty_acc, counterparty_name,
            counterparty_bank, counterparty_swift, counterparty_country,
            originator, beneficiary, remittance,
            None, None, None, None, None, None, None,
            suspicious, suspicious_reason, structuring, sanctions,
            flow_type, report_type,
            now_ts()
        )

    def ensure_min_structuring(txns, min_structuring):
        if min_structuring <= 0:
            return txns

        current = sum(1 for tx in txns if tx[30] == 1)
        if current >= min_structuring:
            return txns

        eligible = [i for i, tx in enumerate(txns)
                    if tx[30] == 0 and tx[8] < 750_000]
        if not eligible:
            return txns

        needed = min_structuring - current
        for idx in random.sample(eligible, min(needed, len(eligible))):
            tx = list(txns[idx])
            tx[30] = 1
            txns[idx] = tuple(tx)

        return txns

    # ── EFT US ON US ──────────────────────────────────────────────────────
    for i in range(n_eft_uu):
        acc_from_num = random.choice(acc_nums)
        acc_to_num   = random.choice([a for a in acc_nums if a != acc_from_num])
        acc_from_id  = acc_id_by_num[acc_from_num]
        acc_to_id    = acc_id_by_num[acc_to_num]
        name_from    = name_by_acc_id[acc_from_id]
        name_to      = name_by_acc_id[acc_to_id]
        amount       = rand_amount(50_000, 5_000_000, 750_000, 0.4)
        suspicious   = 1 if amount > 750_000 and random.random() < 0.1 else 0
        structuring  = 1 if amount < 750_000 and random.random() < 0.35 else 0

        txns.append(make_tx(
            acc_from_id,
            f"EFT-UU-{i+1:06d}",
            rand_tx_date(), "EFT", "ONLINE",
            "D", amount, "MZN",
            acc_to_num, name_to,
            KAIROS_BANK_NAME, KAIROS_SWIFT, "MZ",
            name_from, name_to,
            f"Transferência interna ref.{i+1}",
            "us_on_us", "EFT",
            suspicious, "Montante elevado" if suspicious else None,
            structuring
        ))
        tid += 1  # noqa — tid is used in closure but we rebuild list, track manually

    # ── EFT US ON THEM ────────────────────────────────────────────────────
    for i in range(n_eft_ut):
        direction    = random.choice(["us_on_them_debit","us_on_them_credit"])
        uba_acc_num  = random.choice(acc_nums)
        uba_acc_id   = acc_id_by_num[uba_acc_num]
        uba_name     = name_by_acc_id[uba_acc_id]
        ext_bank_info= random.choice(EXTERNAL_BANKS)
        ext_acc      = rand_account_external(ext_bank_info[2])
        ext_name     = rand_company()
        amount       = rand_amount(50_000, 3_000_000, 750_000, 0.4)
        suspicious   = 1 if amount > 750_000 and random.random() < 0.12 else 0
        structuring  = 1 if amount < 750_000 and random.random() < 0.30 else 0
        dc           = "D" if direction == "us_on_them_debit" else "C"

        txns.append(make_tx(
            uba_acc_id,
            f"EFT-UT-{i+1:06d}",
            rand_tx_date(), "EFT",
            random.choice(["ONLINE","BRANCH"]),
            dc, amount, "MZN",
            ext_acc, ext_name,
            ext_bank_info[0], ext_bank_info[1], "MZ",
            uba_name if dc=="D" else ext_name,
            ext_name  if dc=="D" else uba_name,
            f"Transferência para {ext_name[:20]}",
            direction, "EFT",
            suspicious, "Montante elevado" if suspicious else None,
            structuring
        ))
        tid += 1

    # ── IFT ───────────────────────────────────────────────────────────────
    for i in range(n_ift):
        direction    = random.choice(["ift_outgoing","ift_incoming"])
        uba_acc_num  = random.choice(acc_nums)
        uba_acc_id   = acc_id_by_num[uba_acc_num]
        uba_name     = name_by_acc_id[uba_acc_id]
        foreign_bank = random.choice(FOREIGN_BANKS)
        foreign_acc  = rand_iban_foreign()
        foreign_name = rand_company()
        currency     = random.choice(["USD","EUR","ZAR","GBP","MZN"])
        amount       = rand_amount(100_000, 10_000_000, 750_000, 0.55)
        country      = foreign_bank[2]
        high_risk    = country in ["IR","KP","RU","ZW"]
        suspicious   = 1 if (amount > 750_000 or high_risk) and random.random() < 0.15 else 0
        sanctions_m  = 1 if high_risk and random.random() < 0.05 else 0
        structuring  = 1 if amount < 750_000 and random.random() < 0.25 else 0
        dc           = "D" if direction == "ift_outgoing" else "C"

        txns.append(make_tx(
            uba_acc_id,
            f"IFT-{i+1:06d}",
            rand_tx_date(), "IFT", "SWIFT",
            dc, amount, currency,
            foreign_acc, foreign_name,
            foreign_bank[0], foreign_bank[1], country,
            uba_name if dc=="D" else foreign_name,
            foreign_name if dc=="D" else uba_name,
            f"International transfer — {foreign_bank[0][:20]}",
            direction, "IFT",
            suspicious,
            "Alto risco / Montante elevado" if suspicious else None,
             structuring,sanctions_m
        ))
        tid += 1

    # ── CTR ───────────────────────────────────────────────────────────────
    for i in range(n_ctr):
        direction    = random.choice(["ctr_deposit","ctr_withdrawal"])
        uba_acc_num  = random.choice(acc_nums)
        uba_acc_id   = acc_id_by_num[uba_acc_num]
        uba_name     = name_by_acc_id[uba_acc_id]
        full_name, _, _, _ = rand_name()
        amount       = rand_amount(50_000, 2_000_000, 250_000, 0.65)
        suspicious   = 1 if amount > 500_000 and random.random() < 0.1 else 0
        structuring  = 1 if amount < 250_000 and random.random() < 0.40 else 0
        dc           = "C" if direction == "ctr_deposit" else "D"
        desc         = "Depósito em Numerário" if direction == "ctr_deposit" else "Levantamento em Numerário"

        txns.append(make_tx(
            uba_acc_id,
            f"CTR-{i+1:06d}",
            rand_tx_date(), "CTR", "TELLER",
            dc, amount, "MZN",
            "CASH", full_name,
            KAIROS_BANK_NAME, KAIROS_SWIFT, "MZ",
            full_name if dc=="C" else uba_name,
            uba_name  if dc=="C" else full_name,
            desc,
            direction, "CTR",
            suspicious, "Numerário elevado" if suspicious else None,
            structuring
        ))
        tid += 1

    # Fix tid — we used it as a counter but referenced it wrong above
    # Re-assign proper sequential IDs
    txns_with_ids = []
    for idx, tx in enumerate(txns):
        tx_list = list(tx)
        tx_list[0] = idx + 1
        txns_with_ids.append(tuple(tx_list))

    c.executemany("""
        INSERT OR IGNORE INTO transactions VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, txns_with_ids)

    return len(txns_with_ids)


def seed_loans(c, n=50):
    print(f"  {n} loans with collateral...")

    c.execute("SELECT account_id, customer_id FROM accounts ORDER BY RANDOM() LIMIT ?", (n,))
    rows = c.fetchall()

    loans = []
    collaterals = []
    for i, (acc_id, cust_id) in enumerate(rows, start=1):
        original = round(random.uniform(500_000, 20_000_000), 2)
        dpd      = random.choices([0,0,0,30,60,90,120,180], weights=[50,20,10,8,5,4,2,1])[0]
        stage    = "1" if dpd==0 else ("2" if dpd<=89 else "3")
        default  = 1 if dpd >= 90 else 0
        pd       = round(random.uniform(0.001, 0.35), 6)
        lgd      = round(random.uniform(0.30, 0.70), 6)
        ead      = round(original * random.uniform(0.5, 1.0), 2)
        ecl      = round(pd * lgd * ead, 2)
        coll_val = round(original * random.uniform(0.6, 1.4), 2)

        disb = rand_date(2022, 2024)
        mat  = (date.fromisoformat(disb) + timedelta(days=random.choice([365,730,1095,1460,1825]))).isoformat()

        loans.append((
            i, cust_id, acc_id,
            f"LN-KMZ-{i:06d}",
            random.choice(["MORTGAGE","WORKING_CAPITAL","TERM_LOAN","OVERDRAFT","TRADE_FINANCE"]),
            disb, mat, original,
            round(original * random.uniform(0.3, 0.95), 2),
            round(original * random.uniform(0.01, 0.05), 2),
            round(random.uniform(8.5, 22.0), 4),
            round(original / random.randint(12, 60), 2),
            dpd, stage,
            pd, lgd, ead, ecl, coll_val,
            1 if dpd > 60 else 0,
            default,
            "ACTIVE" if not default else "DEFAULT",
            now_ts()
        ))

        collaterals.append((
            i, i,
            random.choice(["IMÓVEL","VEÍCULO","GARANTIA BANCÁRIA","PENHOR FINANCEIRO","HIPOTECA"]),
            f"Garantia ref.LN-KMZ-{i:06d}",
            coll_val,
            rand_date(2022, 2024),
            random.choice(["PRÓPRIO","TERCEIRO"]),
            1 if random.random() > 0.3 else 0
        ))

    c.executemany("""
        INSERT OR IGNORE INTO loans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, loans)
    c.executemany("""
        INSERT OR IGNORE INTO collateral VALUES (?,?,?,?,?,?,?,?)
    """, collaterals)


def seed_aml_alerts(c):
    print("  AML alerts for suspicious transactions...")

    c.execute("""
        SELECT t.transaction_id, a.customer_id, t.amount, t.report_type,
               t.suspicious_reason, t.structuring_flag, t.sanctions_match_flag
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE t.suspicious_flag = 1 OR t.structuring_flag = 1 OR t.sanctions_match_flag = 1
    """)
    flagged = c.fetchall()

    analysts = [f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" for _ in range(5)]
    alerts   = []

    for i, (tx_id, cust_id, amount, rtype, reason, struct, sanct) in enumerate(flagged, start=1):
        if struct:
            atype  = "STRUCTURING"
            desc   = f"Possível fracionamento de transacções abaixo do limiar. Montante: {amount:,.2f} MZN"
            score  = round(random.uniform(55, 85), 2)
        elif sanct:
            atype  = "SANCTIONS_MATCH"
            desc   = f"Correspondência com lista de sanções. Requer verificação imediata."
            score  = round(random.uniform(80, 100), 2)
        else:
            atype  = f"{rtype}_HIGH_VALUE"
            desc   = reason or f"Transacção de alto valor detectada: {amount:,.2f} MZN"
            score  = round(random.uniform(40, 75), 2)

        status = random.choices(
            ["OPEN","UNDER_REVIEW","CLOSED","ESCALATED"],
            weights=[40, 30, 20, 10]
        )[0]
        sar    = 1 if status == "ESCALATED" and random.random() > 0.4 else 0

        alerts.append((
            i, tx_id, cust_id, atype, score, desc,
            now_ts(),
            random.choice(analysts),
            status,
            1 if status == "ESCALATED" else 0,
            sar
        ))

    c.executemany("""
        INSERT OR IGNORE INTO aml_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, alerts)
    return len(alerts)


def print_summary(conn):
    c = conn.cursor()
    print("\n" + "="*65)
    print("DATABASE SUMMARY — Kairos Bank Mozambique S.A.")
    print("="*65)

    tables = [
        "countries","currencies","banks","branches",
        "customers","accounts","signatories","corporate_account_signatories",
        "transactions","loans","collateral","cards","aml_alerts",
        "sanctions_list","fx_rates"
    ]
    for t in tables:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t:<38} {c.fetchone()[0]:>6} rows")

    print("\nTransaction breakdown:")
    c.execute("SELECT * FROM v_threshold_summary")
    for r in c.fetchall():
        print(f"  {r[0]:<6} {r[1]:<22} {r[2]:>5} txns | "
              f"CTR≥250k:{r[6]:>3} | EFT/IFT≥750k:{r[7]:>3} | "
              f"Suspicious:{r[8]:>3} | Structuring:{r[9]:>3}")

    print(f"\nDatabase: {DB_PATH}")
    print("="*65)
    print("\nConnect:")
    print(f"  sqlite3 {DB_PATH}")
    print(f"  pandas:  pd.read_sql('SELECT ...', sqlite3.connect('{DB_PATH}'))")
    print(f"  duckdb:  duckdb.connect('{DB_PATH}')")
    print(f"  DBeaver: New Connection → SQLite → {DB_PATH}")


if __name__ == "__main__":
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    print(f"Creating {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("Creating schema...")
    conn.executescript(SCHEMA)
    conn.executescript(VIEWS)
    conn.commit()

    print("Seeding data:")
    seed_reference_data(conn.cursor())
    conn.commit()

    account_nums = seed_customers_and_accounts(conn.cursor(), n=200)
    conn.commit()

    n_tx = seed_transactions(conn.cursor(), account_nums,
                             n_eft_uu=8000, n_eft_ut=4000,
                             n_ift=5000, n_ctr=5000, min_structuring=7000)
    conn.commit()

    seed_loans(conn.cursor(), n=50)
    conn.commit()

    n_alerts = seed_aml_alerts(conn.cursor())
    conn.commit()

    print_summary(conn)
    conn.close()
