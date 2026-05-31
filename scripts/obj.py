class Report:
     def __init__(self):
         self.schema_version= None
         self.rentity_id = None
         self.rentity_branch = None
         self.submission_code = None
         self.report_code = None
         self.entity_reference = None
         self.fiu_ref_number = None
         self.submission_date = None
         #added report_date for the schemma5.0
         self.report_date = None
         self.currency_code_local = None
         self.reporting_person = None
         #added reporting_user_code for the schemma 5.0
         self.reporting_user_code = None
         self.location = None
         self.reason = None
         self.action = None
         self.report_indicators = None

class TransactionReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.transactions = None

class Transaction:
    def __init__(self):
        self.transactionnumber = None
        #Added Transaction is suspicious for schemma 5.0
        self.transaction_is_suspicious = None
        self.internal_ref_number = None
        self.transaction_location = None
        self.transaction_description = None
        self.date_transaction = None 
        self.teller = None
        self.authorized = None
        self.late_deposit = None
        self.date_posting = None
        self.value_date = None
        #added Transaction_Type for the schema 5.0
        self.transaction_type = None
        self.transmode_code = None
        self.transmode_comment = None
        self.amount_local = None
        self.t_from_my_client = None
        self.t_from = None
        self.t_to_my_client = None
        self.t_to = None
        self.party = None
        self.goods_services = None
        self.comments = None 


class ActivityReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.report_parties = None
        self.goods_services = None


class ReportIndicator:
    def __init__(self,report_indicator):
        self.report_indicator = report_indicator

class From:
    def __init__(self):
        self.from_funds_code = None
        self.from_funds_comment = None
        self.from_foreign_currency = None
        #Added conductor_is_suspected for schemma 5.0
        self.conductor_is_suspected = None
        self.t_conductor = None
        self.from_account = None
        self.from_person = None
        self.from_entity = None
        self.from_country = None 

class TFromMyClient(From):
    pass

class TFrom(From):
    pass

class To:
    def __init__(self):
        self.to_funds_code = None
        self.to_funds_comment = None
        self.to_foreign_currency = None
        self.to_account = None
        self.to_person = None
        self.to_entity = None
        self.to_country = None 

class TToMyClient(To):
    pass

class TTo(To):
    pass

#Goods_Services Item
class Item:
    def __init__(self):
        self.item_type = None
        self.item_make = None
        self.description = None
        self.previously_registered_to = None
        self.presently_registered_to = None
        self.estimated_value = None
        self.status_code = None
        self.status_comments = None
        self.disposed_value = None
        self.size = None
        self.size_uom = None
        self.address = None
        self.registration_date = None
        self.registration_number = None
        self.identification_number = None
        self.comments = None

class Account:
    def __init__(self):
        self.institution_name = None
        self.institution_code = None
        self.institution_country= None
        self.swift = None
        self.non_banking_institution = None
        self.branch = None
        #added Account Category for schemma 5.0
        self.account_category = None
        self.account = None
        self.currency_code = None
        self.account_name = None
        self.iban = None
        self.client_number = None
        self.personal_account_type = None
        # Added account_type for schemma 5.0
        self.account_type = None
        self.t_entity = None
        self.signatory = None
        self.opened = None
        self.closed = None
        self.balance = None
        self.date_balance = None
        self.status_code = None
        self.beneficiary = None
        self.beneficiary_comment = None
        self.comments = None

class TAccountMyClient(Account):
    pass

class TAccount(Account):
    pass
   

class Entity:
    def __init__(self):
        self.name = None
        self.commercial_name = None
        self.incorporation_legal_form = None
        self.incorporation_number = None
        self.fincorporation_number = None
        self.business = None
        self.phones = None
        self.addresses = None
        self.email = None
        self.url = None
        self.incorporation_state = None
        self.incorporation_country_code = None
        self.director_id = None
        # Added related_persons for schemma 5.0 to replace director_id
        self.related_persons = None
        self.incorporation_date = None
        self.business_closed = None
        self.date_business_closed = None
        self.tax_number = None
        self.tax_reg_number = None
        self.comments = None

class TEntityMyClient(Entity):
    pass

class TEntity(Entity):
    pass

class Person:
    def __init__(self):
        self.gender = None
        self.title = None
        self.first_name = None
        self.middle_name = None
        self.prefix = None
        self.last_name = None
        self.birthdate  = None
        self.birth_place = None
        self.mothers_name = None
        self.alias = None
        self.ssn = None
        self.passport_number = None
        self.passport_country = None
        self.id_number = None
        self.phones = None
        self.addresses = None
        self.nationality1 = None
        self.nationality2 = None
        self.nationality3 = None
        self.residence = None 
        self.email = None
        self.occupation = None
        self.employer_name = None
        self.employer_address_id = None
        self.employer_phone_id = None
        self.identification = None
        self.deceased = None
        self.deceased_date = None
        self.tax_number = None
        self.tax_reg_number = None
        self.peps = None
        self.source_of_wealth = None
        self.comments = None

class TPersonMyClient(Person):
    pass

class TPerson(Person):
    pass
        
class TParty:
    def __init__(self):
        self.role = None
        self.person = None
        self.person_my_client = None
        self.account = None
        self.account_my_client = None
        self.entity = None
        self.entity_my_client = None
        self.funds_code = None
        self.funds_comment = None
        self.to_foreign_currency = None
        self.country = None
        self.significance = None
        self.comments = None

class TAddress:
    def __init__(self):
        self.address_type = None
        self.address = None
        self.town = None
        self.city = None
        self.zip = None
        self.country_code = None
        self.state = None 
        self.comments = None

class TPhone:
    def __init__(self):
        self.tph_contact_type = None
        self.tph_communication_type = None
        self.tph_country_prefix = None
        self.tph_number  =  None
        self.tph_extension = None
        self.comments = None

class TForeinCurrency:
    def __init__(self,foreign_currency_code=None,foreign_amount=None,foreign_exchange_rate=None):
        self.foreign_currency_code = foreign_currency_code
        self.foreign_amount = foreign_amount
        self.foreign_exchange_rate = foreign_exchange_rate

class TPersonIdentification:
    def __init__(self):
        self.type = None
        self.number = None
        self.issue_date = None
        self.expiry_date = None
        self.issued_by = None
        self.issue_country = None
        self.comments = None

class ReportPartyType:
    def __init__(self):
        self.person = None
        self.account = None
        self.entity = None
        self.significance = None
        self.reason = None
        self.comments = None

class Signatory:
    def __init__(self):
        self.is_primary = None
        self.t_person = None
        self.t_person_my_client = None
        self.role = None
         
         
class RelatedPerson:
    def __init__(self):
        self.t_person = None
        self.t_person_my_client = None
        self.role = None

class Pep:
    def __init__(self):
        self.pep_country = None
        self.function_description = None