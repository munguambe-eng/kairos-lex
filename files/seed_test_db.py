"""
seed_test_db.py
Generates a local SQLite test database with realistic Mozambican banking data.

Tables mirror the Excel structure your generators expect:
  - transactions  (Sheet1 equivalent)
  - customers     (Cliente equivalent)
  - signatories   (Assinante equivalent)

Transaction breakdown:
  - 1000 EFT:  750 us-on-us, 250 us-on-them
  - 500  IFT
  - 500  CTR

Run:
  python seed_test_db.py
  → creates kairos_test.db in current directory
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta, date

random.seed(42)

DB_PATH = "kairos_test.db"

# ── Constants ──────────────────────────────────────────────────────────────
UBA_PREFIX = "004201"          # All UBA internal accounts start with this
EXTERNAL_BANK_PREFIXES = [     # External bank account prefixes in Mozambique
    "00100", "00200", "00300", "00400", "00500",
    "00600", "00700", "00800", "00900", "01000",
]

MOZAMBICAN_PROVINCES = [
    "Maputo", "Gaza", "Inhambane", "Sofala", "Manica",
    "Tete", "Zambezia", "Nampula", "Cabo Delgado", "Niassa",
]

BUSINESS_TYPES = [
    "Comércio Geral", "Serviços Financeiros", "Construção Civil",
    "Transportes e Logística", "Agricultura e Pecuária",
    "Indústria Transformadora", "Tecnologia de Informação",
    "Saúde e Farmácia", "Educação", "Hotelaria e Turismo",
    "Importação e Exportação", "Consultoria",
]

COMPANY_TYPES = ["LDA", "SA", "SARL", "EP", "Unipessoal LDA"]

EXTERNAL_BANKS = [
    "Banco Comercial e de Investimentos (BCI)",
    "Millennium BIM",
    "Absa Bank Mozambique",
    "Société Générale Mozambique",
    "Nedbank Mozambique",
    "First Capital Bank",
    "African Banking Corporation",
    "FNB Mozambique",
    "Moza Banco",
    "Banco Nacional de Investimento",
]

FOREIGN_BANKS = [
    "Standard Bank South Africa",
    "Barclays Bank UK",
    "Deutsche Bank AG",
    "Citibank N.A.",
    "BNP Paribas",
    "HSBC Bank",
    "Absa Group Limited",
    "First National Bank SA",
    "Nedbank Group",
    "Investec Bank",
]

COMPANY_FIRST_NAMES = [
    "João", "Maria", "António", "Fátima", "Carlos", "Ana",
    "Manuel", "Sofia", "Pedro", "Isabel", "Luís", "Beatriz",
    "Fernando", "Cristina", "Rodrigo", "Paula", "Eduardo", "Sandra",
    "Miguel", "Carla", "Álvaro", "Teresa", "Nuno", "Margarida",
    "Domingos", "Celeste", "Adriano", "Graça", "Felício", "Esperança",
]

COMPANY_LAST_NAMES = [
    "Machava", "Mabunda", "Nhantumbo", "Sitoe", "Tembe",
    "Cossa", "Mondlane", "Machangana", "Nhavene", "Chibuto",
    "Munguambe", "Bila", "Chaúque", "Muianga", "Nhateve",
    "Magaia", "Cumbe", "Macamo", "Muchanga", "Chemane",
    "Vilanculos", "Zunguze", "Mahumane", "Guambe", "Nguenha",
]

CURRENCIES_EFT = ["MZN"]
CURRENCIES_IFT = ["MZN", "USD", "EUR", "ZAR", "GBP"]
CURRENCIES_CTR = ["MZN"]

MOEDA_MODES_EFT = ["TMM2"]   # electronic
MOEDA_MODES_IFT = ["TMM3"]   # wire transfer
MOEDA_MODES_CTR = ["TMM1"]   # cash


# ── Helpers ────────────────────────────────────────────────────────────────
def rand_date(start_year=2020, end_year=2025) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def rand_tx_date() -> str:
    start = date(2026, 1, 1)
    end = date(2026, 5, 15)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def rand_nuit() -> str:
    return str(random.randint(100000000, 999999999))


def rand_phone() -> str:
    prefixes = ["21", "84", "85", "86", "87", "82", "83"]
    p = random.choice(prefixes)
    rest = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"258{p}{rest}"


def rand_account_uba() -> str:
    return UBA_PREFIX + "".join([str(random.randint(0, 9)) for _ in range(8)])


def rand_account_external() -> str:
    prefix = random.choice(EXTERNAL_BANK_PREFIXES)
    return prefix + "".join([str(random.randint(0, 9)) for _ in range(9)])


def rand_account_foreign() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join([str(random.randint(0, 9)) for _ in range(18)])
    return f"{letters}{digits}"


def rand_company_name() -> str:
    words = random.choice([
        ["Moçambique", random.choice(BUSINESS_TYPES[:6])],
        [random.choice(COMPANY_LAST_NAMES), "&", random.choice(COMPANY_LAST_NAMES)],
        [random.choice(COMPANY_LAST_NAMES), random.choice(BUSINESS_TYPES[6:])],
        ["Grupo", random.choice(COMPANY_LAST_NAMES)],
    ])
    suffix = random.choice(COMPANY_TYPES)
    return " ".join(words) + " " + suffix


def rand_person_name() -> tuple:
    first = random.choice(COMPANY_FIRST_NAMES)
    last = random.choice(COMPANY_LAST_NAMES)
    middle = random.choice(COMPANY_LAST_NAMES) if random.random() > 0.4 else ""
    full = f"{first} {middle} {last}".strip() if middle else f"{first} {last}"
    return full, first, middle, last


def rand_cif() -> str:
    return "CIF" + "".join([str(random.randint(0, 9)) for _ in range(7)])


def rand_reg_number() -> str:
    return "REG" + "".join([str(random.randint(0, 9)) for _ in range(8)])


def rand_id_number() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def rand_amount_eft() -> float:
    # EFT: some below threshold (750k), some above
    if random.random() < 0.4:
        return round(random.uniform(800_000, 5_000_000), 2)
    return round(random.uniform(50_000, 749_000), 2)


def rand_amount_ift() -> float:
    if random.random() < 0.5:
        return round(random.uniform(800_000, 10_000_000), 2)
    return round(random.uniform(100_000, 749_000), 2)


def rand_amount_ctr() -> float:
    # CTR: cash, mostly above 250k threshold
    if random.random() < 0.7:
        return round(random.uniform(260_000, 2_000_000), 2)
    return round(random.uniform(100_000, 249_000), 2)


def rand_tx_number(prefix: str, i: int) -> str:
    return f"{prefix}{str(i).zfill(8)}"


# ── Generate customers ─────────────────────────────────────────────────────
def generate_customers(n: int) -> list:
    customers = []
    used_accounts = set()
    for i in range(n):
        account = rand_account_uba()
        while account in used_accounts:
            account = rand_account_uba()
        used_accounts.add(account)

        company_name = rand_company_name()
        nuib = "NUIB" + "".join([str(random.randint(0, 9)) for _ in range(10)])
        cif = rand_cif()
        province = random.choice(MOZAMBICAN_PROVINCES)
        business = random.choice(BUSINESS_TYPES)
        company_type = random.choice(COMPANY_TYPES)

        customers.append({
            "NUMERO DE CONTA": account,
            "CIF": cif,
            "NUIB": nuib,
            "Tipo de Conta": "E",                # E = Enterprise/Corporate
            "NOME DA EMPRESA": company_name,
            "NUIT EMPRESA": rand_nuit(),
            "DATA DE REGISTO DE EMPRESA": rand_date(2005, 2022),
            "CODIGO DO PAIS": "MZ",
            "ENDERECO EMPRESA": f"Av. {random.choice(COMPANY_LAST_NAMES)} n.{random.randint(1,999)}, {province}",
            "CONTACTO DA EMPRESA (INDICATIVO + NUMERO)": rand_phone(),
            "EMAIL EMPRESA": f"info@{company_name.split()[0].lower().replace(' ','')}.co.mz",
            "PROVINCIA DE REGISTO DA EMPRESA": province,
            "TIPO DE NEGOCIO": business,
            "NUMERO DE REGISTO": rand_reg_number(),
            "TIPO DE SOCIEDADE": company_type,
            "Numero de Assinante": i + 1,         # FK to signatories
        })
    return customers


# ── Generate signatories ───────────────────────────────────────────────────
def generate_signatories(customers: list) -> list:
    signatories = []
    for cus in customers:
        full_name, first, middle, last = rand_person_name()
        doc_type = random.choice(["BI", "Passaporte", "BI", "BI"])  # mostly BI
        dob = rand_date(1960, 1995)
        issue = rand_date(2010, 2022)
        expiry = rand_date(2025, 2032)
        nationality = random.choice(["MZ", "MZ", "MZ", "ZA", "PT", "MZ"])

        signatories.append({
            "Numero de Assinante": cus["Numero de Assinante"],
            "NOME DO ASSINANTE": full_name,
            "DATA DE NASCIMENTO DO ASSINANTE": dob,
            "TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE": doc_type,
            "NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE": rand_id_number(),
            "DATA DE EMISSAO DO DOCUMENTO": issue,
            "DATA EXPIRACAO DO DOCUMENTO": expiry,
            "CONTACTO": rand_phone(),
            "ENDERECO DO ASSINANTE": f"Rua {random.choice(COMPANY_LAST_NAMES)} n.{random.randint(1,200)}, {random.choice(MOZAMBICAN_PROVINCES)}",
            "NACIONALIDADE ASSINANTE": nationality,
            "NUIT DO ASSINANTE": rand_nuit(),
        })
    return signatories


# ── Generate EFT transactions ──────────────────────────────────────────────
def generate_eft_transactions(customers: list, n_us_on_us: int, n_us_on_them: int) -> list:
    txns = []
    accounts = [c["NUMERO DE CONTA"] for c in customers]
    names = {c["NUMERO DE CONTA"]: c["NOME DA EMPRESA"] for c in customers}
    cifs = {c["NUMERO DE CONTA"]: c["CIF"] for c in customers}

    # US ON US — both accounts are UBA
    for i in range(n_us_on_us):
        acc_from = random.choice(accounts)
        acc_to = random.choice([a for a in accounts if a != acc_from])
        amount = rand_amount_eft()
        txns.append({
            "NUMERO DA TRANSACAO": rand_tx_number("EFT-UU-", i + 1),
            "DATA DA TRANSACAO": rand_tx_date(),
            "MOEDA": "MZN",
            "BANCO BENEFICIARIO": "United Bank for Africa Mozambique S.A.",
            "MONTANTE DA TRANSACAO": amount,
            "NUMERO DE CONTA/NIB ORDENADOR": acc_from,
            "NUMERO DE CONTA/NIB BENEFICIARIO": acc_to,
            "NOME DO ORDENADOR/TITULAR DA CONTA": names[acc_from],
            "NOME DO BENEFICIARIO": names[acc_to],
            "TIPO DE TRANSACAO": "EFT",
            "TRANSMODE": "TMM2",
            "DESCRICAO": "Transferência Electrónica",
            "flow_type": "us_on_us",
        })

    # US ON THEM — one UBA account, one external
    for i in range(n_us_on_them):
        direction = random.choice(["debit", "credit"])
        uba_acc = random.choice(accounts)
        ext_acc = rand_account_external()
        ext_bank = random.choice(EXTERNAL_BANKS)
        _, _, _, ext_last = rand_person_name()
        ext_name = rand_company_name()
        amount = rand_amount_eft()

        if direction == "debit":  # UBA sends to external
            acc_from = uba_acc
            acc_to = ext_acc
            name_from = names[uba_acc]
            name_to = ext_name
        else:  # External sends to UBA
            acc_from = ext_acc
            acc_to = uba_acc
            name_from = ext_name
            name_to = names[uba_acc]

        txns.append({
            "NUMERO DA TRANSACAO": rand_tx_number("EFT-UT-", i + 1),
            "DATA DA TRANSACAO": rand_tx_date(),
            "MOEDA": "MZN",
            "BANCO BENEFICIARIO": ext_bank,
            "MONTANTE DA TRANSACAO": amount,
            "NUMERO DE CONTA/NIB ORDENADOR": acc_from,
            "NUMERO DE CONTA/NIB BENEFICIARIO": acc_to,
            "NOME DO ORDENADOR/TITULAR DA CONTA": name_from,
            "NOME DO BENEFICIARIO": name_to,
            "TIPO DE TRANSACAO": "EFT",
            "TRANSMODE": "TMM2",
            "DESCRICAO": "Transferência Electrónica",
            "flow_type": "us_on_them",
        })

    return txns


# ── Generate IFT transactions ──────────────────────────────────────────────
def generate_ift_transactions(customers: list, n: int) -> list:
    txns = []
    accounts = [c["NUMERO DE CONTA"] for c in customers]
    names = {c["NUMERO DE CONTA"]: c["NOME DA EMPRESA"] for c in customers}

    FOREIGN_COUNTRIES = ["ZA", "PT", "GB", "DE", "FR", "US", "AE", "CN", "BR", "IN"]

    for i in range(n):
        direction = random.choice(["outgoing", "incoming"])
        uba_acc = random.choice(accounts)
        foreign_acc = rand_account_foreign()
        foreign_bank = random.choice(FOREIGN_BANKS)
        foreign_country = random.choice(FOREIGN_COUNTRIES)
        foreign_name = rand_company_name()
        currency = random.choice(CURRENCIES_IFT)
        amount = rand_amount_ift()

        if direction == "outgoing":
            acc_from = uba_acc
            acc_to = foreign_acc
            name_from = names[uba_acc]
            name_to = foreign_name
            banco_ben = foreign_bank
        else:
            acc_from = foreign_acc
            acc_to = uba_acc
            name_from = foreign_name
            name_to = names[uba_acc]
            banco_ben = "United Bank for Africa Mozambique S.A."

        txns.append({
            "NUMERO DA TRANSACAO": rand_tx_number("IFT-", i + 1),
            "DATA DA TRANSACAO": rand_tx_date(),
            "MOEDA": currency,
            "BANCO BENEFICIARIO": banco_ben,
            "MONTANTE DA TRANSACAO": amount,
            "NUMERO DE CONTA/NIB ORDENADOR": acc_from,
            "NUMERO DE CONTA/NIB BENEFICIARIO": acc_to,
            "NOME DO ORDENADOR/TITULAR DA CONTA": name_from,
            "NOME DO BENEFICIARIO": name_to,
            "TIPO DE TRANSACAO": "IFT",
            "TRANSMODE": "TMM3",
            "DESCRICAO": "Transferência Internacional",
            "PAIS_ORIGEM": foreign_country if direction == "incoming" else "MZ",
            "PAIS_DESTINO": foreign_country if direction == "outgoing" else "MZ",
            "BANCO_CORRESPONDENTE": foreign_bank,
            "flow_type": direction,
        })

    return txns


# ── Generate CTR transactions ──────────────────────────────────────────────
def generate_ctr_transactions(customers: list, n: int) -> list:
    txns = []
    accounts = [c["NUMERO DE CONTA"] for c in customers]
    names = {c["NUMERO DE CONTA"]: c["NOME DA EMPRESA"] for c in customers}

    CTR_TYPES = ["CTR-C", "CTR-I", "CTR-E"]  # Cash, International cash, Electronic cash

    for i in range(n):
        direction = random.choice(["deposit", "withdrawal"])
        uba_acc = random.choice(accounts)
        amount = rand_amount_ctr()
        ctr_type = random.choice(CTR_TYPES)

        # For cash: external party is a person or company depositing/withdrawing
        _, depositor_first, _, depositor_last = rand_person_name()
        depositor_name = f"{depositor_first} {depositor_last}"

        if direction == "deposit":
            acc_from = "CASH"
            acc_to = uba_acc
            name_from = depositor_name
            name_to = names[uba_acc]
        else:
            acc_from = uba_acc
            acc_to = "CASH"
            name_from = names[uba_acc]
            name_to = depositor_name

        txns.append({
            "NUMERO DA TRANSACAO": rand_tx_number("CTR-", i + 1),
            "DATA DA TRANSACAO": rand_tx_date(),
            "MOEDA": "MZN",
            "BANCO BENEFICIARIO": "United Bank for Africa Mozambique S.A.",
            "MONTANTE DA TRANSACAO": amount,
            "NUMERO DE CONTA/NIB ORDENADOR": acc_from,
            "NUMERO DE CONTA/NIB BENEFICIARIO": acc_to,
            "NOME DO ORDENADOR/TITULAR DA CONTA": name_from,
            "NOME DO BENEFICIARIO": name_to,
            "TIPO DE TRANSACAO": "CTR",
            "TRANSMODE": "TMM1",
            "DESCRICAO": f"Depósito em Numerário" if direction == "deposit" else "Levantamento em Numerário",
            "CTR_TYPE": ctr_type,
            "flow_type": direction,
        })

    return txns


# ── Write to SQLite ────────────────────────────────────────────────────────
def create_database(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ── CUSTOMERS table (mirrors Cliente sheet) ──────────────────────────
    c.execute("DROP TABLE IF EXISTS customers")
    c.execute("""
        CREATE TABLE customers (
            id                                      INTEGER PRIMARY KEY AUTOINCREMENT,
            "NUMERO DE CONTA"                       TEXT NOT NULL UNIQUE,
            "CIF"                                   TEXT,
            "NUIB"                                  TEXT,
            "Tipo de Conta"                         TEXT DEFAULT 'E',
            "NOME DA EMPRESA"                       TEXT,
            "NUIT EMPRESA"                          TEXT,
            "DATA DE REGISTO DE EMPRESA"            TEXT,
            "CODIGO DO PAIS"                        TEXT DEFAULT 'MZ',
            "ENDERECO EMPRESA"                      TEXT,
            "CONTACTO DA EMPRESA (INDICATIVO + NUMERO)" TEXT,
            "EMAIL EMPRESA"                         TEXT,
            "PROVINCIA DE REGISTO DA EMPRESA"       TEXT,
            "TIPO DE NEGOCIO"                       TEXT,
            "NUMERO DE REGISTO"                     TEXT,
            "TIPO DE SOCIEDADE"                     TEXT,
            "Numero de Assinante"                   INTEGER
        )
    """)

    # ── SIGNATORIES table (mirrors Assinante sheet) ──────────────────────
    c.execute("DROP TABLE IF EXISTS signatories")
    c.execute("""
        CREATE TABLE signatories (
            id                                                      INTEGER PRIMARY KEY AUTOINCREMENT,
            "Numero de Assinante"                                   INTEGER NOT NULL UNIQUE,
            "NOME DO ASSINANTE"                                     TEXT,
            "DATA DE NASCIMENTO DO ASSINANTE"                       TEXT,
            "TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE"          TEXT,
            "NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE"     TEXT,
            "DATA DE EMISSAO DO DOCUMENTO"                          TEXT,
            "DATA EXPIRACAO DO DOCUMENTO"                           TEXT,
            "CONTACTO"                                              TEXT,
            "ENDERECO DO ASSINANTE"                                 TEXT,
            "NACIONALIDADE ASSINANTE"                               TEXT,
            "NUIT DO ASSINANTE"                                     TEXT
        )
    """)

    # ── TRANSACTIONS table (mirrors Sheet1) ──────────────────────────────
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute("""
        CREATE TABLE transactions (
            id                                      INTEGER PRIMARY KEY AUTOINCREMENT,
            "NUMERO DA TRANSACAO"                   TEXT NOT NULL UNIQUE,
            "DATA DA TRANSACAO"                     TEXT,
            "MOEDA"                                 TEXT,
            "BANCO BENEFICIARIO"                    TEXT,
            "MONTANTE DA TRANSACAO"                 REAL,
            "NUMERO DE CONTA/NIB ORDENADOR"         TEXT,
            "NUMERO DE CONTA/NIB BENEFICIARIO"      TEXT,
            "NOME DO ORDENADOR/TITULAR DA CONTA"    TEXT,
            "NOME DO BENEFICIARIO"                  TEXT,
            "TIPO DE TRANSACAO"                     TEXT,
            "TRANSMODE"                             TEXT,
            "DESCRICAO"                             TEXT,
            "CTR_TYPE"                              TEXT,
            "PAIS_ORIGEM"                           TEXT,
            "PAIS_DESTINO"                          TEXT,
            "BANCO_CORRESPONDENTE"                  TEXT,
            "flow_type"                             TEXT
        )
    """)

    # ── VIEWS to mirror your Excel sheet structure ────────────────────────
    # View for EFT us-on-us
    c.execute("DROP VIEW IF EXISTS v_eft_us_on_us")
    c.execute("""
        CREATE VIEW v_eft_us_on_us AS
        SELECT t.*, 
               c_from.CIF as debit_cif,
               c_from."NOME DA EMPRESA" as debit_name,
               c_to."NOME DA EMPRESA" as credit_name
        FROM transactions t
        LEFT JOIN customers c_from ON t."NUMERO DE CONTA/NIB ORDENADOR" = c_from."NUMERO DE CONTA"
        LEFT JOIN customers c_to   ON t."NUMERO DE CONTA/NIB BENEFICIARIO" = c_to."NUMERO DE CONTA"
        WHERE t."TIPO DE TRANSACAO" = 'EFT'
          AND t.flow_type = 'us_on_us'
    """)

    # View for EFT us-on-them
    c.execute("DROP VIEW IF EXISTS v_eft_us_on_them")
    c.execute("""
        CREATE VIEW v_eft_us_on_them AS
        SELECT t.*
        FROM transactions t
        WHERE t."TIPO DE TRANSACAO" = 'EFT'
          AND t.flow_type IN ('us_on_them', 'debit', 'credit')
    """)

    # View for IFT
    c.execute("DROP VIEW IF EXISTS v_ift")
    c.execute("""
        CREATE VIEW v_ift AS
        SELECT t.*
        FROM transactions t
        WHERE t."TIPO DE TRANSACAO" = 'IFT'
    """)

    # View for CTR
    c.execute("DROP VIEW IF EXISTS v_ctr")
    c.execute("""
        CREATE VIEW v_ctr AS
        SELECT t.*
        FROM transactions t
        WHERE t."TIPO DE TRANSACAO" = 'CTR'
    """)

    # Threshold summary view — useful for testing structured/smurfing detection
    c.execute("DROP VIEW IF EXISTS v_threshold_summary")
    c.execute("""
        CREATE VIEW v_threshold_summary AS
        SELECT
            "TIPO DE TRANSACAO"                     AS report_type,
            flow_type,
            COUNT(*)                                AS total_transactions,
            SUM("MONTANTE DA TRANSACAO")            AS total_amount,
            AVG("MONTANTE DA TRANSACAO")            AS avg_amount,
            MAX("MONTANTE DA TRANSACAO")            AS max_amount,
            MIN("MONTANTE DA TRANSACAO")            AS min_amount,
            SUM(CASE WHEN "TIPO DE TRANSACAO"='CTR' AND "MONTANTE DA TRANSACAO" >= 250000 THEN 1 ELSE 0 END) AS ctr_above_threshold,
            SUM(CASE WHEN "TIPO DE TRANSACAO" IN ('EFT','IFT') AND "MONTANTE DA TRANSACAO" >= 750000 THEN 1 ELSE 0 END) AS eft_ift_above_threshold
        FROM transactions
        GROUP BY "TIPO DE TRANSACAO", flow_type
    """)

    conn.commit()
    return conn


def seed(conn: sqlite3.Connection):
    c = conn.cursor()

    print("Generating 200 corporate customers...")
    customers = generate_customers(200)

    print("Generating signatories (1 per customer)...")
    signatories = generate_signatories(customers)

    print("Generating 750 EFT us-on-us transactions...")
    eft_uu = generate_eft_transactions(customers, n_us_on_us=750, n_us_on_them=0)

    print("Generating 250 EFT us-on-them transactions...")
    eft_ut = generate_eft_transactions(customers, n_us_on_us=0, n_us_on_them=250)

    print("Generating 500 IFT transactions...")
    ift = generate_ift_transactions(customers, 500)

    print("Generating 500 CTR transactions...")
    ctr = generate_ctr_transactions(customers, 500)

    all_transactions = eft_uu + eft_ut + ift + ctr

    # Insert customers
    for cus in customers:
        c.execute("""
            INSERT INTO customers (
                "NUMERO DE CONTA", "CIF", "NUIB", "Tipo de Conta",
                "NOME DA EMPRESA", "NUIT EMPRESA", "DATA DE REGISTO DE EMPRESA",
                "CODIGO DO PAIS", "ENDERECO EMPRESA",
                "CONTACTO DA EMPRESA (INDICATIVO + NUMERO)", "EMAIL EMPRESA",
                "PROVINCIA DE REGISTO DA EMPRESA", "TIPO DE NEGOCIO",
                "NUMERO DE REGISTO", "TIPO DE SOCIEDADE", "Numero de Assinante"
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            cus["NUMERO DE CONTA"], cus["CIF"], cus["NUIB"], cus["Tipo de Conta"],
            cus["NOME DA EMPRESA"], cus["NUIT EMPRESA"], cus["DATA DE REGISTO DE EMPRESA"],
            cus["CODIGO DO PAIS"], cus["ENDERECO EMPRESA"],
            cus["CONTACTO DA EMPRESA (INDICATIVO + NUMERO)"], cus["EMAIL EMPRESA"],
            cus["PROVINCIA DE REGISTO DA EMPRESA"], cus["TIPO DE NEGOCIO"],
            cus["NUMERO DE REGISTO"], cus["TIPO DE SOCIEDADE"], cus["Numero de Assinante"]
        ))

    # Insert signatories
    for sig in signatories:
        c.execute("""
            INSERT INTO signatories (
                "Numero de Assinante", "NOME DO ASSINANTE",
                "DATA DE NASCIMENTO DO ASSINANTE",
                "TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE",
                "NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE",
                "DATA DE EMISSAO DO DOCUMENTO", "DATA EXPIRACAO DO DOCUMENTO",
                "CONTACTO", "ENDERECO DO ASSINANTE",
                "NACIONALIDADE ASSINANTE", "NUIT DO ASSINANTE"
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            sig["Numero de Assinante"], sig["NOME DO ASSINANTE"],
            sig["DATA DE NASCIMENTO DO ASSINANTE"],
            sig["TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE"],
            sig["NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE"],
            sig["DATA DE EMISSAO DO DOCUMENTO"], sig["DATA EXPIRACAO DO DOCUMENTO"],
            sig["CONTACTO"], sig["ENDERECO DO ASSINANTE"],
            sig["NACIONALIDADE ASSINANTE"], sig["NUIT DO ASSINANTE"]
        ))

    # Insert transactions
    for tx in all_transactions:
        c.execute("""
            INSERT INTO transactions (
                "NUMERO DA TRANSACAO", "DATA DA TRANSACAO", "MOEDA",
                "BANCO BENEFICIARIO", "MONTANTE DA TRANSACAO",
                "NUMERO DE CONTA/NIB ORDENADOR", "NUMERO DE CONTA/NIB BENEFICIARIO",
                "NOME DO ORDENADOR/TITULAR DA CONTA", "NOME DO BENEFICIARIO",
                "TIPO DE TRANSACAO", "TRANSMODE", "DESCRICAO",
                "CTR_TYPE", "PAIS_ORIGEM", "PAIS_DESTINO",
                "BANCO_CORRESPONDENTE", "flow_type"
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tx["NUMERO DA TRANSACAO"], tx["DATA DA TRANSACAO"], tx["MOEDA"],
            tx["BANCO BENEFICIARIO"], tx["MONTANTE DA TRANSACAO"],
            tx["NUMERO DE CONTA/NIB ORDENADOR"], tx["NUMERO DE CONTA/NIB BENEFICIARIO"],
            tx["NOME DO ORDENADOR/TITULAR DA CONTA"], tx["NOME DO BENEFICIARIO"],
            tx["TIPO DE TRANSACAO"], tx["TRANSMODE"], tx["DESCRICAO"],
            tx.get("CTR_TYPE"), tx.get("PAIS_ORIGEM"), tx.get("PAIS_DESTINO"),
            tx.get("BANCO_CORRESPONDENTE"), tx["flow_type"]
        ))

    conn.commit()


def print_summary(conn: sqlite3.Connection):
    c = conn.cursor()
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)

    c.execute('SELECT COUNT(*) FROM customers')
    print(f"Customers:    {c.fetchone()[0]:>6}")

    c.execute('SELECT COUNT(*) FROM signatories')
    print(f"Signatories:  {c.fetchone()[0]:>6}")

    c.execute('SELECT COUNT(*) FROM transactions')
    print(f"Transactions: {c.fetchone()[0]:>6}")

    print("\nTransaction breakdown:")
    c.execute("""
        SELECT "TIPO DE TRANSACAO", flow_type, COUNT(*), 
               ROUND(AVG("MONTANTE DA TRANSACAO"),2)
        FROM transactions 
        GROUP BY "TIPO DE TRANSACAO", flow_type
        ORDER BY "TIPO DE TRANSACAO", flow_type
    """)
    for row in c.fetchall():
        print(f"  {row[0]:<6} {row[1]:<15} {row[2]:>5} txns  avg: {row[3]:>14,.2f} MZN")

    print("\nThreshold analysis:")
    c.execute("""
        SELECT report_type, 
               ctr_above_threshold,
               eft_ift_above_threshold,
               total_transactions
        FROM v_threshold_summary
    """)
    for row in c.fetchall():
        print(f"  {row[0]}: {row[3]} total | "
              f"CTR ≥250k: {row[1]} | EFT/IFT ≥750k: {row[2]}")

    print(f"\nDatabase saved to: {DB_PATH}")
    print("="*60)


if __name__ == "__main__":
    print(f"Creating database: {DB_PATH}")
    conn = create_database(DB_PATH)
    seed(conn)
    print_summary(conn)
    conn.close()
    print("\nDone. Connect with:")
    print(f"  sqlite3 {DB_PATH}")
    print(f"  or in Python: sqlite3.connect('{DB_PATH}')")
    print(f"  or in DuckDB: duckdb.connect('{DB_PATH}')")
