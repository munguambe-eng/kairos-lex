"""
xml_generator.py
================
Two generation modes:

  mode="excel"    — reads an uploaded .xlsx workbook
                    handles us_on_us / us_on_them / them_on_us
                    For us_on_us: joins BOTH sides with full customer+signatory data

  mode="database" — reads from kairos_banking.db (or any SQLite path)
                    filtered by report_type + date range

Both modes produce a DataFrame where every row has:
  from_{field}  — the debit/sending side customer fields
  to_{field}    — the credit/receiving side customer fields

This mirrors the pattern in your original us-on-us script exactly.
The internal customer builder reads from a column prefix ('from_' or 'to_')
so the same function builds both sides — only the prefix changes.
"""

import sys, os, logging, datetime, re, warnings, traceback
import xml.etree.ElementTree as ET

import pandas as pd
import duckdb
import pycountry
from lxml import etree
from dateutil import parser as _duparser
from seed_banking_db import KAIROS_BANK_CODE
warnings.filterwarnings("ignore")

# ── Path setup ─────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from obj import (
    TransactionReport, Transaction,
    TFrom, TTo, TFromMyClient, TToMyClient,
    Person, Account, TAddress, TPhone,
    TPersonIdentification, TEntity, Signatory, Pep,
)
import schemaActions
import helper_teste as hp

logger = logging.getLogger("kairos.generator")

# Internal account prefix — change per bank
INTERNAL_PREFIX = os.getenv("INTERNAL_ACCOUNT_PREFIX", "008301")
# INTERNAL_PREFIX = os.getenv("INTERNAL_ACCOUNT_PREFIX", "0042")
# ── Transmode / funds codes per report type ────────────────────────────────
TRANSMODE = {"EFT": "TMM4", "IFT": "TMM4", "CTR": "TMM2"}
FUNDS_CODE = {"EFT": "FTM19", "IFT": "FTM19", "CTR": "FTM7"}
REPORT_CODE = {"EFT": "DEFT", "IFT": "DIFT", "CTR": "DCTR"}



# ═══════════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════════════════════

_EXPLICIT_FMTS = [
    '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%m/%d/%Y', '%m-%d-%Y',
    '%Y-%m-%d', '%Y/%m/%d', '%d-%b-%Y', '%d %b %Y', '%b %d, %Y',
]
_SENTINEL = pd.Timestamp('1900-01-01')


def _parse_dob(val):
    if pd.isna(val) or str(val).strip() in ('', 'nan', 'NaT', 'None'):
        return _SENTINEL
    s = str(val).strip()
    for fmt in _EXPLICIT_FMTS:
        try:
            return pd.Timestamp(datetime.datetime.strptime(s, fmt))
        except ValueError:
            pass
    try:
        return pd.Timestamp(_duparser.parse(s, dayfirst=True))
    except Exception:
        pass
    digits = re.sub(r'\D', '', s)
    if len(digits) == 8:
        for fmt in ('%d%m%Y', '%m%d%Y', '%Y%m%d'):
            try:
                return pd.Timestamp(datetime.datetime.strptime(digits, fmt))
            except ValueError:
                pass
    return _SENTINEL


def _norm_key(series: pd.Series) -> pd.Series:
    return (
        series.astype('string').str.strip()
        .str.replace(r'\.0+$', '', regex=True)
        .str.replace(r'\D', '', regex=True)
        .fillna('')
    )


def _strip(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.select_dtypes(include='object').columns:
        df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def _fmt_dt(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return pd.Timestamp(val).strftime('%Y-%m-%dT%H:%M:%S')
    except Exception:
        return str(val)


def _valid_country(code) -> str | None:
    if not code:
        return None
    try:
        c = str(code).strip().upper()
        return c if pycountry.countries.get(alpha_2=c) else None
    except Exception:
        return None


def _make_phone(val) -> TPhone | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    ph = TPhone()
    ph.tph_contact_type = 'B'
    s = str(val).strip()
    ph.tph_communication_type = 'L' if s.startswith('21') else 'M'
    ph.tph_number = s
    return ph


def _make_id(id_type, id_number, issue_country, issue_date, expiry_date):
    obj = TPersonIdentification()
    # Normalize: BI → B, Passport → E
    normalized = str(id_type or '').strip().upper()
    if normalized in ('BI', 'BILHETE', 'BILHETE DE IDENTIDADE'):
        obj.type = 'B'
    elif normalized in ('PASSPORT', 'C', 'PASSAPORTE'):
        obj.type = 'C'
    elif normalized in ('DIR', 'DIRE'):
        obj.type = 'E'
    elif normalized in ('Carta de Conducao', 'Driver License', 'A'):
        obj.type = 'A'
    elif normalized in ('NUIT'):
        obj.type = 'D'
    else:
        obj.type = 'B'  # fallback to original if unrecognized
    
    obj.number = id_number
    obj.issue_date = issue_date or '2020-01-01T00:00:00'
    obj.expiry_date = expiry_date
    obj.issue_country = issue_country
    return obj

def _split_name(full_name):
    if not full_name:
        return ("", "", "")
    parts = re.findall(r'\S+', str(full_name))
    if len(parts) == 0: return ("", "", "")
    if len(parts) == 1: return (parts[0], "", "")
    if len(parts) == 2: return (parts[0], "", parts[1])
    return (parts[0], ' '.join(parts[1:-1]), parts[-1])


def _validate_email(email) -> str | None:
    if not email: 
        return None
    s = str(email).strip().lower()
    
    # Split on @ to separate local and domain
    if '@' not in s:
        return None
    
    local, domain = s.split('@', 1)
    
    # Clean local part: remove consecutive dots, remove leading/trailing dots
    local = re.sub(r'\.+', '.', local)  # replace consecutive dots (e.g., s.a. → s.a)
    local = local.strip('.')  # remove leading/trailing dots
    
    # Reconstruct cleaned email
    s = f"{local}@{domain}"
    
    # Validate against RFC 5322 simplified pattern
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return s if re.match(pattern, s) else None


def _g(r, *names, default=None):
    """getattr with multiple fallback names."""
    for name in names:
        v = getattr(r, name, None)
        if v is not None and str(v).strip() not in ('', 'None', 'nan', '<NA>'):
            return v
    return default


# ── Row validation ─────────────────────────────────────────────────────────
REQUIRED = {
    "EFT": ["internal_ref_number", "transaction_amount",
            "transaction_date", "from_account_number", "transaction_currency"],
    "IFT": ["internal_ref_number", "transaction_amount",
            "transaction_date", "from_account_number", "transaction_currency"],
    "CTR": ["internal_ref_number", "transaction_amount",
            "transaction_date", "from_account_number"],
}


def _validate_row(r, report_type: str) -> list[str]:
    errors = []
    for field in REQUIRED.get(report_type, []):
        v = getattr(r, field, None)
        if v is None or str(v).strip() in ('', 'None', 'nan', '<NA>'):
            errors.append(f"Missing: {field}")
    amt = getattr(r, 'transaction_amount', None)
    try:
        if amt is not None and float(amt) <= 0:
            errors.append(f"Invalid amount: {amt}")
    except (ValueError, TypeError):
        errors.append(f"Non-numeric amount: {amt}")
    return errors


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL CUSTOMER BUILDER  (prefix-based — same function for from_ and to_)
# ═══════════════════════════════════════════════════════════════════════════

def _build_my_client(r, prefix: str, is_to: bool,
                     report_type: str,
                     institution_name: str,
                     institution_code: str) -> TToMyClient | TFromMyClient:
    """
    Build a TToMyClient (is_to=True) or TFromMyClient (is_to=False)
    from prefixed columns.

    Column naming convention (prefix = 'from_' or 'to_'):
      {prefix}account_number          — account number / NIB
      {prefix}cif                     — CIF / client number
      {prefix}name                    — customer full name
      {prefix}nuit                    — NUIT (tax number)
      {prefix}registration_date       — incorporation / opening date
      {prefix}country_code            — country (MZ etc)
      {prefix}address                 — street address
      {prefix}contact                 — phone number
      {prefix}email                   — email
      {prefix}province                — province / city
      {prefix}business_type           — industry / business
      {prefix}registration_number     — company registration number
      {prefix}account_type            — E=entity, P=person
      {prefix}balance                 — current balance
      {prefix}signatory_name          — signatory full name
      {prefix}signatory_dob           — signatory date of birth
      #{prefix}signatory_id_type       — B=BI, E=Passport
      {prefix}signatory_id_type       — B=BI, E=Passport

      {prefix}signatory_id_number     — ID number
      {prefix}signatory_issue_date    — document issue date
      {prefix}signatory_expiry_date   — document expiry date
      {prefix}signatory_contact       — signatory phone
      {prefix}signatory_address       — signatory address
      {prefix}signatory_nuit          — signatory NUIT
      {prefix}signatory_nationality   — signatory nationality code
      {prefix}pep_flag                — PEP indicator
    """
    p = prefix  # shorthand

    my_client = TToMyClient() if is_to else TFromMyClient()
    funds = FUNDS_CODE.get(report_type, 'FTM19')
    if is_to:
        my_client.to_funds_code   = funds
    else:
        my_client.from_funds_code = funds
        my_client.from_funds_comment = 'Funds Transfer'

    # ── Account ────────────────────────────────────────────────────────
    acc = Account()
    acc.institution_name    = institution_name
    acc.institution_code    = institution_code
    acc.institution_country = 'MZ'
    acc.account_category    = 'ACM1'
    acc.account             = str(_g(r, p+'account_number', p+'NIB', default='') or '')
    acc.iban                = _g(r, p+'iban', p+'IBAN')
    acc.client_number       = str(_g(r, p+'cif', p+'client_number', p+'cus_n', default='') or '')
    acc.currency_code       = _g(r, 'transaction_currency', p+'currency', p+'CURRENCY')
    acc.balance             = str(_g(r, p+'balance', p+'Working_balance', default='0') or '0')
    acc.date_balance        = _g(r, p+'INSERT_DATE')
    acc.account_name        = _g(r, p+'name', p+'cus_full_name')
    acc.account_type        = 'ATM2' if str(_g(r, p+'account_type', p+'cus_type', default='') or '') == 'P' else 'ATM1'
    acc.branch              = _g(r, p+'branch', p+'COMPANY', default='Branch')
    acc.status_code         = 'AS1'
    acc.beneficiary         = _g(r, p+'name', p+'cus_full_name')
    acc.opened              = _fmt_dt(_g(r, p+'registration_date', p+'OPENING_DATE'))


    # ── Entity (corporate account) ─────────────────────────────────────
    acct_type = str(_g(r, p+'account_type', p+'cus_type', default='E') or 'E')

    if acct_type == 'E':
        ent = TEntity()
        ent.name                      = _g(r, p+'name', p+'cus_full_name')
        ent.commercial_name           = ent.name
        ent.incorporation_number      = _g(r, p+'registration_number', p+'incorporation_number')
        ent.business                  = _g(r, p+'business_type', p+'CUS_Industry')
        ent.tax_number                = str(_g(r, p+'nuit', p+'cus_nuit', default='000000000') or '000000000')
        ent.tax_reg_number            = str(_g(r, p+'registration_number', p+'client_number', default='') or '')
        ent.incorporation_country_code = _g(r, p+'country_code', p+'residence_country', p+'cus_country_c', default='MZ')
        ent.incorporation_state       = _g(r, p+'province', p+'cus_town')
        ent.email                     = _validate_email(_g(r, p+'email', p+'cus_email_1_1'))

        ph = _make_phone(_g(r, p+'contact', p+'cus_tel_no1'))
        if ph:
            ent.phones = [ph]

        addr = TAddress()
        addr.address_type = 'B'
        addr.address      = _g(r, p+'address', p+'cus_address_1', p+'cus_address',p+'province', p+'cus_town')
        addr.city         = _g(r, p+'province', p+'cus_town')
        addr.country_code = _g(r, p+'country_code', p+'residence_country', default='MZ')
        ent.addresses     = [addr]
        acc.t_entity      = ent

        # Signatory / director
        sig_name = _g(r, p+'signatory_name', p+'director_name')
        if sig_name:
            try:
                dfn, dmn, dln = _split_name(sig_name)
                director = Person()
                director.first_name   = dfn
                director.middle_name  = dmn or None
                director.last_name    = dln
                director.gender       = _g(r, p+'signatory_gender', p+'director_gender')

                director.birthdate = _fmt_dt(_g(r, p+'signatory_dob', p+'director_birthdate', p+'signatory_date_of_birth'))
                # director.birthdate    = _g(r, p+'signatory_dob', p+'director_birthdate', p+'signatory_date_of_birth')
                director.nationality1 = _valid_country(
                    _g(r, p+'signatory_nationality', p+'director_nationality', p+'country_code', default='MZ')
                )
                director.birth_place  = _g(r, p+'signatory_birth_place', p+'director_place_birth', p+'country_code')
                director.residence    = _g(r, p+'signatory_nationality', p+'director_residence_country', p+'country_code', default='MZ')
                director.occupation   = _g(r, p+'signatory_occupation', p+'director_occupation')
                director.employer_name = _g(r, p+'employer_name', p+'director_employer_name')
                director.tax_number   = str(_g(r, p+'signatory_nuit', p+'director_id_nuit', default='000000000') or '000000000')
                director.tax_reg_number = str(_g(r, p+'signatory_nuit', p+'director_tax_reg_number', default='') or '')

                director.identification = _make_id(
                    _g(r, p+'signatory_id_type', p+'director_id_type'),
                    _g(r, p+'signatory_id_number', p+'director_id_number'),
                    _g(r, p+'country_code', p+'director_id_issue_country', default='MZ'),
                    _g(r, p+'signatory_issue_date', p+'director_id_issue_date'),
                    _g(r, p+'signatory_expiry_date', p+'director_id_exp_date'),
                )

                d_addr = TAddress()
                d_addr.address_type = 'P'
                d_addr.address      = _g(r, p+'signatory_address', p+'director_address', p+'director_address_1',p+'province', p+'director_city', p+'cus_town')
                d_addr.city         = _g(r, p+'province', p+'director_city', p+'cus_town')
                d_addr.country_code = _g(r, p+'country_code', p+'director_residence_country', default='MZ')
                director.addresses  = [d_addr]

                sph = _make_phone(_g(r, p+'signatory_contact', p+'director_phone'))
                if sph:
                    director.phones = [sph]

                emp_addr = TAddress()
                emp_addr.address_type = 'B'
                emp_addr.address    = _g(r, p+'director_employer_address', p+'address', p+'cus_address_1',p+'director_employer_city', p+'province', p+'cus_town')
                emp_addr.city       = _g(r, p+'director_employer_city', p+'province', p+'cus_town')
                emp_addr.country_code = _g(r, p+'director_employer_country', p+'country_code', default='MZ')
                # director.employer_address_id = emp_addr

                pep_flag = _g(r, p+'pep_flag', p+'Cus_PEP')
                if pep_flag and str(pep_flag) not in ('0', 'N', 'False', 'None', ''):
                    pep = Pep()
                    pep.pep_country = 'MZ'
                    pep.function_description = _g(r, p+'director_occupation', p+'Cus_occupation')
                    director.peps = pep

                sign = Signatory()
                sign.t_person = director
                acc.signatory = sign

            except Exception:
                logger.exception("Error building signatory for prefix=%s", prefix)

    else:
        # PERSON account — build person as signatory of their own account
        try:
            cus_name = _g(r, p+'name', p+'cus_full_name')
            fn, mn, ln = _split_name(cus_name)
            person = Person()
            person.first_name   = fn
            person.middle_name  = mn or None
            person.last_name    = ln
            person.gender       = _g(r, p+'gender', p+'cus_gender')
            person.birthdate    = _fmt_dt(_g(r, p+'dob', p+'cus_dob'))
            person.nationality1 = _valid_country(
                _g(r, p+'nationality', p+'cus_nationality', default='MZ')
            )
            person.birth_place  = _g(r, p+'birth_place', p+'cus_country_c', p+'country_code')
            person.residence    = _g(r, p+'country_code', p+'residence_country', default='MZ')
            person.occupation   = _g(r, p+'occupation', p+'Cus_occupation')
            person.employer_name = _g(r, p+'employer_name', p+'cus_employer_name')
            person.tax_number   = str(_g(r, p+'nuit', p+'cus_nuit', default='000000000') or '000000000')
            person.tax_reg_number = str(_g(r, p+'cif', p+'client_number', default='') or '')

            person.identification = _make_id(
                _g(r, p+'signatory_id_type', p+'id_type'),
                _g(r, p+'signatory_id_number', p+'CUS_ID_N'),
                _g(r, p+'country_code', p+'cus_country_c', default='MZ'),
                _g(r, p+'signatory_issue_date', p+'cus_legal_doc_issue_dte'),
                _g(r, p+'signatory_expiry_date', p+'cus_legal_doc_exp_dte'),
            )

            p_addr = TAddress()
            p_addr.address_type = 'P'
            p_addr.address      = _g(r, p+'address', p+'cus_address_1', p+'cus_address',p+'province', p+'cus_town')
            p_addr.city         = _g(r, p+'province', p+'cus_town')
            p_addr.country_code = _g(r, p+'country_code', p+'residence_country', default='MZ')
            person.addresses    = [p_addr]

            ph = _make_phone(_g(r, p+'contact', p+'cus_tel_no1'))
            if ph:
                person.phones = [ph]

            pep_flag = _g(r, p+'pep_flag', p+'Cus_PEP')
            if pep_flag and str(pep_flag) not in ('0', 'N', 'False', 'None', ''):
                pep = Pep()
                pep.pep_country = 'MZ'
                pep.function_description = _g(r, p+'occupation', p+'PROF_desc')
                person.peps = pep

            sign = Signatory()
            sign.t_person = person
            acc.signatory = sign

        except Exception:
            logger.exception("Error building person account for prefix=%s", prefix)

    if is_to:
        my_client.to_account  = acc
        my_client.to_country  = _g(r, p+'country_code', p+'residence_country', default='MZ')
    else:
        my_client.from_account = acc
        my_client.from_country = _g(r, p+'country_code', p+'residence_country', default='MZ')

    return my_client


def _build_external(r, is_from: bool, report_type: str) -> TFrom | TTo:
    """
    Build TFrom or TTo for the external / counterparty side.
    Reads from outside_* columns (Excel) or counterparty_* columns (DB).
    """
    ext   = TFrom() if is_from else TTo()
    funds = FUNDS_CODE.get(report_type, 'FTM19')
    if is_from:
        ext.from_funds_code = funds
    else:
        ext.to_funds_code = funds

    act = Account()
    act.institution_name    = _g(r, 'outside_customer_bank', 'counterparty_bank', 'bank_name')
    act.institution_code    = str(_g(r, 'outside_institution_code', 'counterparty_swift', 'bank', default='001') or '001')
    act.institution_country = _g(r, 'outside_customer_country', 'counterparty_country',
                                    'country_trans', 'from_country_code', default='MZ')
    act.account             = str(_g(r, 'outside_customer_account_number',
                                      'counterparty_account', 'outside_bank_acct', default='') or '')
    act.account_name        = str(_g(r, 'outside_customer_name', 'counterparty_name',
                                      'ft_debit_their_ref', default='') or '')
    act.beneficiary         = act.account_name

    ent = TEntity()
    ent.name                       = act.account_name
    ent.commercial_name            = act.account_name
    ent.incorporation_country_code = act.institution_country
    act.t_entity = ent

    if is_from:
        ext.from_account = act
        ext.from_country = act.institution_country
    else:
        ext.to_account = act
        ext.to_country = act.institution_country

    return ext


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTION OBJECT BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def build_transaction_objects(df: pd.DataFrame, report_type: str,
                               institution_name: str, institution_code: str,
                               config: dict) -> tuple[list, list]:
    """
    Convert DataFrame rows into Transaction objects.
    Returns (valid_transactions, exceptions_list).

    Every row MUST have:
      internal_ref_number, transaction_date, transaction_amount,
      transaction_currency, flow_type

    For us_on_us rows, BOTH sides must be present as from_* and to_* columns.
    For all other flows, from_* columns describe the internal side.

    flow_type values:
      us_on_us          — both internal: from_ = debit side, to_ = credit side
      us_on_them_debit  — internal sends to external
      us_on_them_credit — external sends to internal
      them_on_us        — alias for us_on_them_credit
      ift_outgoing      — internal -> foreign
      ift_incoming      — foreign  -> internal
      ctr_deposit       — cash deposit into internal account
      ctr_withdrawal    — cash withdrawal from internal account
    """
    transactions_out = []
    exceptions_out   = []
    transmode        = TRANSMODE.get(report_type, 'TMM2')

    for r in df.itertuples(index=False):
        internal_ref = getattr(r, 'internal_ref_number', None)
        try:
            errors = _validate_row(r, report_type)
            if errors:
                exceptions_out.append({
                    "transaction_id": str(internal_ref),
                    "error_reason":   "; ".join(errors),
                    "error_type":     "validation_error",
                    "raw_data": {
                        "amount":    str(getattr(r, 'transaction_amount', None)),
                        "date":      str(getattr(r, 'transaction_date', None)),
                        "flow_type": str(getattr(r, 'flow_type', None)),
                    }
                })
                continue

            flow = str(getattr(r, 'flow_type', '') or '').lower()

            tx = Transaction()
            tx.transactionnumber       = internal_ref
            tx.internal_ref_number     = internal_ref
            tx.transaction_description = str(
                _g(r, 'DESC', 'remittance_information', 'transaction_description', default='') or ''
            )
            tx.transaction_type  = 'TTM1'
            tx.transmode_code    = transmode
            tx.amount_local      = str(getattr(r, 'transaction_amount', ''))
            tx.date_transaction  = _fmt_dt(getattr(r, 'transaction_date', None))
            tx.value_date        = tx.date_transaction
            tx.transaction_location = _g(r, 'from_branch', 'from_COMPANY')

            # ── US ON US — both sides internal, full data for both ─────
            if flow == 'us_on_us':
                tx.t_from_my_client = _build_my_client(
                    r, 'from_', is_to=False,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )
                tx.t_to_my_client = _build_my_client(
                    r, 'to_', is_to=True,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )

            # ── US ON THEM — internal debit, external credit ───────────
            elif flow in ('us_on_them_debit', 'debit'):
                tx.t_from_my_client = _build_my_client(
                    r, 'from_', is_to=False,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )
                tx.t_to = _build_external(r, is_from=False, report_type=report_type)

            # ── THEM ON US — external debit, internal credit ───────────
            elif flow in ('us_on_them_credit', 'credit', 'them_on_us'):
                tx.t_from = _build_external(r, is_from=True, report_type=report_type)
                tx.t_to_my_client = _build_my_client(
                    r, 'from_', is_to=True,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )

            # ── IFT OUTGOING ──────────────────────────────────────────
            elif flow == 'ift_outgoing':
                tx.t_from_my_client = _build_my_client(
                    r, 'from_', is_to=False,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )
                tx.t_to = _build_external(r, is_from=False, report_type=report_type)

            # ── IFT INCOMING ──────────────────────────────────────────
            elif flow == 'ift_incoming':
                tx.t_from = _build_external(r, is_from=True, report_type=report_type)
                tx.t_to_my_client = _build_my_client(
                    r, 'from_', is_to=True,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )

            # ── CTR DEPOSIT ───────────────────────────────────────────
            elif flow == 'ctr_deposit':
                tx.t_from = _build_external(r, is_from=True, report_type=report_type)
                tx.t_to_my_client = _build_my_client(
                    r, 'from_', is_to=True,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )

            # ── CTR WITHDRAWAL ────────────────────────────────────────
            elif flow == 'ctr_withdrawal':
                tx.t_from_my_client = _build_my_client(
                    r, 'from_', is_to=False,
                    report_type=report_type,
                    institution_name=institution_name,
                    institution_code=institution_code,
                )
                tx.t_to = _build_external(r, is_from=False, report_type=report_type)

            else:
                exceptions_out.append({
                    "transaction_id": str(internal_ref),
                    "error_reason":   f"Unknown flow_type: '{flow}'",
                    "error_type":     "unknown_flow",
                    "raw_data":       {"flow_type": flow}
                })
                continue

            transactions_out.append(tx)

        except Exception as exc:
            logger.exception("Error building tx ref=%s", internal_ref)
            exceptions_out.append({
                "transaction_id": str(internal_ref),
                "error_reason":   str(exc),
                "error_type":     "processing_error",
                "raw_data":       {}
            })

    return transactions_out, exceptions_out


# ═══════════════════════════════════════════════════════════════════════════
# MODE: EXCEL
# ═══════════════════════════════════════════════════════════════════════════

def extract_excel(filepath: str):
    mtr = pd.read_excel(filepath, sheet_name='Sheet1', dtype={
        'NUMERO DE CONTA/NIB ORDENADOR': 'string',
        'NUMERO DE CONTA/NIB BENEFICIARIO': 'string',
    })
    mtr = mtr.rename(columns={
        'NUMERO DA TRANSACCAO':  'NUMERO DA TRANSACAO',
        ' DATA DA TRANSACÇÃO':   'DATA DA TRANSACAO',
        'MONTANTE DA TRANSACÇÃO':'MONTANTE DA TRANSACAO',
    })
    assinante = pd.read_excel(filepath, sheet_name='Assinante')
    customer  = pd.read_excel(filepath, sheet_name='Cliente', dtype={
        'NUMERO DE CONTA': 'string', 'NUIB': 'string', 'CIF': 'string',
    })
    customer = customer.rename(columns={
        'NÚMERO DE REGISTO': 'NUMERO DE REGISTO',
        'ENDEREÇO EMPRESA': 'ENDERECO EMPRESA',
        'PROVÍNCIA DE REGISTO DA EMPRESA': 'PROVINCIA DE REGISTO DA EMPRESA',
        'CODIGO DO PAÍS': 'CODIGO DO PAIS',
    })
    assinante = assinante.rename(columns={
        'TIPO DE DOCUMENTO DE IDENTIFICÇÃO ASSINANTE': 'TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE',
        'Nº DO DOCUMENTO DE IDENTIFICAÇÃO DO ASSINANTE': 'NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE',
        'DATA DE EMISSÃO DO DOCUMENTO': 'DATA DE EMISSAO DO DOCUMENTO',
        'ENDEREÇO DO ASSINANTE': 'ENDERECO DO ASSINANTE',
        ' NACIONALIDADE ASSINANTE': 'NACIONALIDADE ASSINANTE',
        ' NUIT DO ASSINANTE': 'NUIT DO ASSINANTE',
    })
    dob_col = 'DATA DE NASCIMENTO DO ASSINANTE'
    if dob_col in assinante.columns:
        assinante[dob_col] = assinante[dob_col].apply(_parse_dob)

    mtr       = _strip(mtr)
    assinante = _strip(assinante)
    customer  = _strip(customer)

    customer['NUIT EMPRESA'] = (
        customer['NUIT EMPRESA'].astype('string').str.strip()
        .str.replace(r'\.0+$', '', regex=True).replace({'0': '00000000'})
    )
    return mtr, assinante, customer


def build_excel_dataframe(mtr: pd.DataFrame, assinante: pd.DataFrame,
                           customer: pd.DataFrame,
                           report_type: str, internal_prefix: str) -> pd.DataFrame:
    """
    Join the three Excel sheets and produce a unified DataFrame with
    from_ and to_ prefixed columns for every transaction.

    For us_on_us: BOTH the debit and credit customer rows are joined
    so that _build_my_client() has full data on both sides.

    For us_on_them / them_on_us: only the internal side is joined;
    the external side is captured from the raw mtr columns.
    """
    mtr['join_account_key']     = _norm_key(mtr['NUMERO DE CONTA/NIB ORDENADOR'])
    mtr['join_beneficiary_key'] = _norm_key(mtr['NUMERO DE CONTA/NIB BENEFICIARIO'])
    customer['join_account_key']= _norm_key(customer['NUMERO DE CONTA'])
    pfx = internal_prefix

    mtr_work   = mtr.copy()

    # ── US ON US — join BOTH sides with full customer + signatory data ──
    uu_df = duckdb.sql(f"""
        SELECT DISTINCT
            mtr."NUMERO DA TRANSACAO"       AS internal_ref_number,
            mtr."DATA DA TRANSACAO"         AS transaction_date,
            mtr.MOEDA                       AS transaction_currency,
            mtr."MONTANTE DA TRANSACAO"     AS transaction_amount,
            'us_on_us'                      AS flow_type,

            -- FROM side (ordering / debit)
            from_cus.CIF                    AS from_cif,
            from_cus."NUMERO DE CONTA"      AS from_account_number,
            from_cus.NUIB                   AS from_iban,
            mtr."NOME DO ORDENADOR/TITULAR DA CONTA" AS from_name,
            from_cus."NUIT EMPRESA"         AS from_nuit,
            from_cus."DATA DE REGISTO DE EMPRESA"    AS from_registration_date,
            from_cus."CODIGO DO PAIS"       AS from_country_code,
            from_cus."ENDERECO EMPRESA"     AS from_address,
            from_cus."CONTACTO DA EMPRESA (INDICATIVO + NUMERO)" AS from_contact,
            from_cus."EMAIL EMPRESA"        AS from_email,
            from_cus."PROVINCIA DE REGISTO DA EMPRESA" AS from_province,
            from_cus."TIPO DE NEGOCIO"      AS from_business_type,
            from_cus."Tipo de Conta"        AS from_account_type,
            from_cus."NUMERO DE REGISTO"    AS from_registration_number,
            from_ass."NOME DO ASSINANTE"    AS from_signatory_name,
            from_ass."DATA DE NASCIMENTO DO ASSINANTE" AS from_signatory_dob,
            CASE WHEN from_ass."TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE"='Passaporte'
                 THEN 'E' ELSE 'B' END      AS from_signatory_id_type,
            from_ass."NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE" AS from_signatory_id_number,
            from_ass."DATA DE EMISSAO DO DOCUMENTO"  AS from_signatory_issue_date,
            from_ass."DATA EXPIRACAO DO DOCUMENTO"   AS from_signatory_expiry_date,
            from_ass."CONTACTO"             AS from_signatory_contact,
            from_ass."ENDERECO DO ASSINANTE" AS from_signatory_address,
            from_ass."NUIT DO ASSINANTE"    AS from_signatory_nuit,
            from_ass."NACIONALIDADE ASSINANTE" AS from_signatory_nationality,

            -- TO side (beneficiary / credit)
            to_cus.CIF                      AS to_cif,
            to_cus."NUMERO DE CONTA"        AS to_account_number,
            to_cus.NUIB                     AS to_iban,
            mtr."NOME DO BENEFICIARIO"      AS to_name,
            to_cus."NUIT EMPRESA"           AS to_nuit,
            to_cus."DATA DE REGISTO DE EMPRESA"    AS to_registration_date,
            to_cus."CODIGO DO PAIS"         AS to_country_code,
            to_cus."ENDERECO EMPRESA"       AS to_address,
            to_cus."CONTACTO DA EMPRESA (INDICATIVO + NUMERO)" AS to_contact,
            to_cus."EMAIL EMPRESA"          AS to_email,
            to_cus."PROVINCIA DE REGISTO DA EMPRESA" AS to_province,
            to_cus."TIPO DE NEGOCIO"        AS to_business_type,
            to_cus."Tipo de Conta"          AS to_account_type,
            to_cus."NUMERO DE REGISTO"      AS to_registration_number,
            to_ass."NOME DO ASSINANTE"      AS to_signatory_name,
            to_ass."DATA DE NASCIMENTO DO ASSINANTE" AS to_signatory_dob,
            CASE WHEN to_ass."TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE"='Passaporte'
                 THEN 'E' ELSE 'B' END      AS to_signatory_id_type,
            to_ass."NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE" AS to_signatory_id_number,
            to_ass."DATA DE EMISSAO DO DOCUMENTO"  AS to_signatory_issue_date,
            to_ass."DATA EXPIRACAO DO DOCUMENTO"   AS to_signatory_expiry_date,
            to_ass."CONTACTO"               AS to_signatory_contact,
            to_ass."ENDERECO DO ASSINANTE"  AS to_signatory_address,
            to_ass."NUIT DO ASSINANTE"      AS to_signatory_nuit,
            to_ass."NACIONALIDADE ASSINANTE" AS to_signatory_nationality,

            -- No outside customer for us_on_us
            NULL AS outside_customer_account_number,
            NULL AS outside_customer_name,
            NULL AS outside_customer_bank

        FROM mtr_work mtr
        JOIN customer from_cus ON mtr.join_account_key     = from_cus.join_account_key
        JOIN assinante from_ass ON from_cus."Numero de Assinante" = from_ass."Numero de Assinante"
        JOIN customer to_cus   ON mtr.join_beneficiary_key = to_cus.join_account_key
        JOIN assinante to_ass  ON to_cus."Numero de Assinante"   = to_ass."Numero de Assinante"
        WHERE mtr.join_account_key    LIKE '{pfx}%'
          AND mtr.join_beneficiary_key LIKE '{pfx}%'
    """).df()

    # ── US ON THEM / THEM ON US — one internal side + external counterparty
    ut_df = duckdb.sql(f"""
        SELECT DISTINCT
            mtr."NUMERO DA TRANSACAO"       AS internal_ref_number,
            mtr."DATA DA TRANSACAO"         AS transaction_date,
            mtr.MOEDA                       AS transaction_currency,
            mtr."MONTANTE DA TRANSACAO"     AS transaction_amount,

            CASE
                WHEN mtr.join_account_key    LIKE '{pfx}%' THEN 'us_on_them_debit'
                ELSE 'us_on_them_credit'
            END                             AS flow_type,

            -- FROM side (always the internal customer)
            cus.CIF                         AS from_cif,
            cus."NUMERO DE CONTA"           AS from_account_number,
            cus.NUIB                        AS from_iban,
            CASE
                WHEN mtr.join_account_key LIKE '{pfx}%'
                    THEN mtr."NOME DO ORDENADOR/TITULAR DA CONTA"
                ELSE mtr."NOME DO BENEFICIARIO"
            END                             AS from_name,
            cus."NUIT EMPRESA"              AS from_nuit,
            cus."DATA DE REGISTO DE EMPRESA" AS from_registration_date,
            cus."CODIGO DO PAIS"            AS from_country_code,
            cus."ENDERECO EMPRESA"          AS from_address,
            cus."CONTACTO DA EMPRESA (INDICATIVO + NUMERO)" AS from_contact,
            cus."EMAIL EMPRESA"             AS from_email,
            cus."PROVINCIA DE REGISTO DA EMPRESA" AS from_province,
            cus."TIPO DE NEGOCIO"           AS from_business_type,
            cus."Tipo de Conta"             AS from_account_type,
            cus."NUMERO DE REGISTO"         AS from_registration_number,
            ass."NOME DO ASSINANTE"         AS from_signatory_name,
            ass."DATA DE NASCIMENTO DO ASSINANTE" AS from_signatory_dob,
            CASE WHEN ass."TIPO DE DOCUMENTO DE IDENTIFICACAO ASSINANTE"='Passaporte'
                 THEN 'E' ELSE 'B' END      AS from_signatory_id_type,
            ass."NUMERO DO DOCUMENTO DE IDENTIFICACAO DO ASSINANTE" AS from_signatory_id_number,
            ass."DATA DE EMISSAO DO DOCUMENTO"  AS from_signatory_issue_date,
            ass."DATA EXPIRACAO DO DOCUMENTO"   AS from_signatory_expiry_date,
            ass."CONTACTO"                  AS from_signatory_contact,
            ass."ENDERECO DO ASSINANTE"     AS from_signatory_address,
            ass."NUIT DO ASSINANTE"         AS from_signatory_nuit,
            ass."NACIONALIDADE ASSINANTE"   AS from_signatory_nationality,

            -- No to_ internal side for us_on_them
            NULL AS to_cif,
            NULL AS to_account_number,
            NULL AS to_iban,
            NULL AS to_name,
            NULL AS to_nuit,
            NULL AS to_registration_date,
            NULL AS to_country_code,
            NULL AS to_address,
            NULL AS to_contact,
            NULL AS to_email,
            NULL AS to_province,
            NULL AS to_business_type,
            NULL AS to_account_type,
            NULL AS to_registration_number,
            NULL AS to_signatory_name,
            NULL AS to_signatory_dob,
            NULL AS to_signatory_id_type,
            NULL AS to_signatory_id_number,
            NULL AS to_signatory_issue_date,
            NULL AS to_signatory_expiry_date,
            NULL AS to_signatory_contact,
            NULL AS to_signatory_address,
            NULL AS to_signatory_nuit,
            NULL AS to_signatory_nationality,

            -- External side
            CASE
                WHEN mtr.join_account_key LIKE '{pfx}%'
                    THEN mtr.join_beneficiary_key
                ELSE mtr.join_account_key
            END                             AS outside_customer_account_number,
            CASE
                WHEN mtr.join_account_key LIKE '{pfx}%'
                    THEN mtr."NOME DO BENEFICIARIO"
                ELSE mtr."NOME DO ORDENADOR/TITULAR DA CONTA"
            END                             AS outside_customer_name,
            mtr."BANCO BENEFICIARIO"        AS outside_customer_bank

        FROM mtr_work mtr
        JOIN customer cus ON (
            CASE
                WHEN mtr.join_account_key LIKE '{pfx}%' THEN mtr.join_account_key
                ELSE mtr.join_beneficiary_key
            END
        ) = cus.join_account_key
        JOIN assinante ass ON cus."Numero de Assinante" = ass."Numero de Assinante"
        WHERE (
            mtr.join_account_key    LIKE '{pfx}%'
            OR mtr.join_beneficiary_key LIKE '{pfx}%'
        )
        AND NOT (
            mtr.join_account_key    LIKE '{pfx}%'
            AND mtr.join_beneficiary_key LIKE '{pfx}%'
        )
    """).df()

    # Combine both
    df = pd.concat([uu_df, ut_df], ignore_index=True)

    # Post-processing
    _skip = ('int', 'float', 'datetime', 'timedelta', 'bool')
    for col in df.columns:
        if not any(str(df[col].dtype).lower().startswith(p) for p in _skip):
            df[col] = df[col].astype('string').str.slice(0, 50)

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors='coerce')
            if df[col].notna().any():
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

    if report_type == 'EFT':
        df = df[df['from_account_type'] == 'E']

    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip() if hasattr(c, 'str') else c)

    logger.info("Excel dataframe: %d rows | flows: %s",
                len(df), df['flow_type'].value_counts().to_dict())
    return df


# ═══════════════════════════════════════════════════════════════════════════
# MODE: DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def build_db_dataframe(db_path: str, report_type: str,
                       date_from: str, date_to: str,
                       period_type: str = 'single') -> pd.DataFrame:
    """
    Query kairos_banking.db and return a unified DataFrame with
    from_ and to_ prefixed columns, matching the same structure
    as build_excel_dataframe() so the same Transaction builder works
    for both modes.

    For us_on_us, both accounts are in our DB so we join BOTH sides.
    """
    conn = duckdb.connect(db_path)

    structuring_filter = "AND t.structuring_flag = 1" if period_type in ('weekly', 'monthly') else ""
    rt_filter          = f"AND t.report_type = '{report_type}'"

    query = f"""
        SELECT
            t.transaction_reference         AS internal_ref_number,
            t.transaction_date              AS transaction_date,
            t.currency_code                 AS transaction_currency,
            t.local_currency_amount         AS transaction_amount,
            t.flow_type                     AS flow_type,
            t.remittance_information        AS "DESC",
            t.suspicious_flag,
            t.structuring_flag,

            -- FROM side — always the Kairos internal account
            from_c.customer_id               AS from_cif,
            from_a.account_number           AS from_account_number,
            from_a.iban                     AS from_iban,
            from_c.customer_name            AS from_name,
            from_c.tax_number               AS from_nuit,
            from_c.onboarding_date          AS from_registration_date,
            COALESCE(from_c.nationality_code, 'MZ') AS from_country_code,
            from_ca.address_line1           AS from_address,
            from_c.phone_number             AS from_contact,
            from_c.email                    AS from_email,
            from_ca.province                AS from_province,
            from_c.industry                 AS from_business_type,
            'E'                             AS from_account_type,
            from_c.id_number                AS from_registration_number,
            from_a.available_balance        AS from_balance,

            -- FROM signatory
            from_s.full_name                AS from_signatory_name,
            from_s.date_of_birth            AS from_signatory_dob,
            from_s.id_type                  AS from_signatory_id_type,
            from_s.id_number                AS from_signatory_id_number,
            NULL                            AS from_signatory_issue_date,
            NULL                            AS from_signatory_expiry_date,
            from_s.phone_number             AS from_signatory_contact,
            NULL                            AS from_signatory_address,
            NULL                            AS from_signatory_nuit,
            from_s.nationality_code         AS from_signatory_nationality,

            -- TO side — for us_on_us, join the credit account; else NULL
            CASE WHEN t.flow_type='us_on_us' THEN to_c.tax_number     ELSE NULL END AS to_cif,
            CASE WHEN t.flow_type='us_on_us' THEN to_a.account_number ELSE NULL END AS to_account_number,
            CASE WHEN t.flow_type='us_on_us' THEN to_a.iban           ELSE NULL END AS to_iban,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.customer_name  ELSE NULL END AS to_name,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.tax_number     ELSE NULL END AS to_nuit,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.onboarding_date ELSE NULL END AS to_registration_date,
            CASE WHEN t.flow_type='us_on_us' THEN COALESCE(to_c.nationality_code,'MZ') ELSE NULL END AS to_country_code,
            CASE WHEN t.flow_type='us_on_us' THEN to_ca.address_line1 ELSE NULL END AS to_address,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.phone_number   ELSE NULL END AS to_contact,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.email          ELSE NULL END AS to_email,
            CASE WHEN t.flow_type='us_on_us' THEN to_ca.province      ELSE NULL END AS to_province,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.industry       ELSE NULL END AS to_business_type,
            CASE WHEN t.flow_type='us_on_us' THEN 'E'                 ELSE NULL END AS to_account_type,
            CASE WHEN t.flow_type='us_on_us' THEN to_c.id_number      ELSE NULL END AS to_registration_number,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.full_name      ELSE NULL END AS to_signatory_name,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.date_of_birth  ELSE NULL END AS to_signatory_dob,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.id_type        ELSE NULL END AS to_signatory_id_type,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.id_number      ELSE NULL END AS to_signatory_id_number,
            NULL AS to_signatory_issue_date,
            NULL AS to_signatory_expiry_date,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.phone_number   ELSE NULL END AS to_signatory_contact,
            NULL AS to_signatory_address,
            NULL AS to_signatory_nuit,
            CASE WHEN t.flow_type='us_on_us' THEN to_s.nationality_code ELSE NULL END AS to_signatory_nationality,

            -- External counterparty
            t.counterparty_account          AS outside_customer_account_number,
            t.counterparty_name             AS outside_customer_name,
            t.counterparty_bank             AS outside_customer_bank,
            t.counterparty_swift            AS outside_institution_code,
            t.counterparty_country          AS outside_customer_country

        FROM transactions t

        -- FROM (internal) side
        JOIN accounts from_a  ON t.account_id        = from_a.account_id
        JOIN customers from_c ON from_a.customer_id  = from_c.customer_id
        LEFT JOIN customer_addresses from_ca
                              ON from_c.customer_id  = from_ca.customer_id
                             AND from_ca.address_type = 'BUSINESS'
        LEFT JOIN corporate_account_signatories from_cas
                              ON from_a.account_id   = from_cas.account_id
        LEFT JOIN signatories from_s
                              ON from_cas.signatory_id = from_s.signatory_id

        -- TO (internal) side for us_on_us — join by counterparty_account
        LEFT JOIN accounts to_a
                              ON t.flow_type = 'us_on_us'
                             AND to_a.account_number = t.counterparty_account
        LEFT JOIN customers to_c
                              ON to_a.customer_id    = to_c.customer_id
        LEFT JOIN customer_addresses to_ca
                              ON to_c.customer_id    = to_ca.customer_id
                             AND to_ca.address_type  = 'BUSINESS'
        LEFT JOIN corporate_account_signatories to_cas
                              ON to_a.account_id     = to_cas.account_id
        LEFT JOIN signatories to_s
                              ON to_cas.signatory_id = to_s.signatory_id

        WHERE t.transaction_date >= '{date_from}'
          AND t.transaction_date <= '{date_to} 23:59:59'
          {rt_filter}
          {structuring_filter}
        ORDER BY t.transaction_date
    """

    df = conn.execute(query).df()
    conn.close()

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors='coerce')
            if df[col].notna().any():
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

    logger.info("DB dataframe: %d rows | flows: %s",
                len(df), df['flow_type'].value_counts().to_dict())
    return df


# ═══════════════════════════════════════════════════════════════════════════
# XML WRITER
# ═══════════════════════════════════════════════════════════════════════════

def build_report_header(config: dict) -> TransactionReport:
    report = hp.tag_report(config)
    report.report_code = config.get("report_code", "DEFT")
    return report


def save_xml_chunk(transactions: list, report: TransactionReport,
                   output_dir: str, entity_name: str,
                   report_code: str, date_str: str, chunk_index: int) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    prefix = f"{entity_name}.{report_code}."
    fname  = f"{prefix}{date_str}_000{chunk_index}.xml"
    fpath  = os.path.join(output_dir, fname)

    report.entity_reference = (
        f"{prefix}{date_str}_000{chunk_index}.xml+{date_str}+000{chunk_index}"
    )
    report.transactions = transactions

    xml_bytes = schemaActions.generateReportXML(report)
    with open(fpath, "wb") as f:
        f.write(xml_bytes)

    # Location element fix (from original script)
    try:
        tree     = ET.parse(fpath)
        root     = tree.getroot()
        loc_elem = root.find('location')
        if loc_elem is not None:
            addr_elem = loc_elem.find('address')
            if addr_elem is not None:
                loc_elem.extend(addr_elem)
                loc_elem.remove(addr_elem)
        xml_fixed = ET.tostring(root, method="xml", xml_declaration=True, encoding='ISO-8859-1')
        with open(fpath, "wb") as f:
            f.write(xml_fixed)
    except Exception:
        logger.warning("Location fix failed for %s", fname)

    return {
        "filename": fname, "path": fpath,
        "size": os.path.getsize(fpath),
        "transactions": len(transactions),
    }


def validate_xml(xml_path: str, xsd_path: str) -> tuple:
    errors = []
    try:
        with open(xsd_path, 'rb') as f:
            schema = etree.XMLSchema(etree.parse(f))
        valid = schema.validate(etree.parse(xml_path))
        if not valid:
            for e in schema.error_log:
                errors.append({"line": e.line, "column": e.column,
                                "message": e.message, "type": e.type_name})
        return valid, errors
    except Exception as exc:
        return False, [{"line": 0, "column": 0, "message": str(exc), "type": "ParseError"}]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def run_generation(config: dict) -> dict:
    result = {
        "status": "completed",
        "mode": config.get("mode", "excel"),
        "total_transactions": 0,
        "reported_count": 0,
        "exception_count": 0,
        "xml_files": [],
        "exceptions": [],
        "log": [],
    }

    def log(msg):
        logger.info(msg)
        result["log"].append(msg)

    try:
        mode         = config.get("mode", "excel")
        report_type  = config.get("report_type", "EFT").upper()
        output_dir   = config.get("output_dir", "./xml_output")
        xsd_path     = config.get("xsd_path")
        chunk_size   = int(config.get("chunk_size", 2700))
        entity_name  = config.get("entity_name", "KAIROS")
        inst_name    = config.get("institution_name", "Kairos Bank Mozambique S.A.")
        inst_code    = config.get("institution_code", KAIROS_BANK_CODE)
        report_code  = REPORT_CODE.get(report_type, "DEFT")
        config["report_code"]  = report_code
        internal_pfx = config.get("internal_prefix", INTERNAL_PREFIX)

        # Load data
        if mode == "excel":
            filepath = config["filepath"]
            log(f"Mode: Excel — {os.path.basename(filepath)}")
            mtr, assinante, customer = extract_excel(filepath)
            log(f"Read {len(mtr)} raw rows from Sheet1")
            df = build_excel_dataframe(mtr, assinante, customer, report_type, internal_pfx)

        elif mode == "database":
            db_path     = config["db_path"]
            date_from   = config["date_from"]
            date_to     = config["date_to"]
            period_type = config.get("period_type", "single")
            log(f"Mode: Database — {report_type} | {date_from}→{date_to} | {period_type}")
            df = build_db_dataframe(db_path, report_type, date_from, date_to, period_type)

        else:
            raise ValueError(f"Unknown mode: {mode}")

        log(f"Loaded {len(df)} rows | flows: {df['flow_type'].value_counts().to_dict()}")
        result["total_transactions"] = len(df)

        if len(df) == 0:
            log("No transactions found.")
            return result

        # Build Transaction objects
        log("Building Transaction objects...")
        transactions, exceptions = build_transaction_objects(
            df, report_type, inst_name, inst_code, config
        )

        result["exceptions"]      = exceptions
        result["exception_count"] = len(exceptions)

        if exceptions:
            log(f"{len(exceptions)} excluded (exceptions):")
            for ex in exceptions[:5]:
                log(f"  {ex['transaction_id']}: {ex['error_reason']}")
            if len(exceptions) > 5:
                log(f"  ... and {len(exceptions)-5} more")

        log(f"{len(transactions)} valid transactions to report")

        if not transactions:
            result["status"] = "completed_with_exceptions"
            return result

        # Generate XML
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        report   = build_report_header(config)
        chunks   = [transactions[i:i+chunk_size]
                    for i in range(0, len(transactions), chunk_size)]
        log(f"Splitting into {len(chunks)} chunk(s) of max {chunk_size}")

        for i, chunk in enumerate(chunks):
            log(f"Chunk {i+1}/{len(chunks)} — {len(chunk)} transactions...")
            meta = save_xml_chunk(chunk, report, output_dir, entity_name,
                                  report_code, date_str, i+1)
            result["xml_files"].append(meta)
            result["reported_count"] += len(chunk)

            if xsd_path and os.path.exists(xsd_path):
                valid, errs = validate_xml(meta["path"], xsd_path)
                meta["is_valid"]          = valid
                meta["validation_errors"] = errs
                log(f"  XSD: {'✓ valid' if valid else f'{len(errs)} error(s)'}")
            else:
                meta["is_valid"]          = None
                meta["validation_errors"] = []

        result["xml_files_generated"] = len(result["xml_files"])
        log(f"Done — {result['reported_count']} reported | {result['exception_count']} exceptions")

    except Exception as exc:
        result["status"] = "failed"
        result["log"].append(f"FATAL: {str(exc)}")
        result["log"].append(traceback.format_exc())
        logger.exception("Generation failed")

    return result


# Backward compat alias
def run_eft_generation(filepath, output_dir, config, xsd_path=None, chunk_size=2700):
    config["mode"]       = "excel"
    config["filepath"]   = filepath
    config["output_dir"] = output_dir
    config["xsd_path"]   = xsd_path
    config["chunk_size"] = chunk_size
    return run_generation(config)
