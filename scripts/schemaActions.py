from scripts.obj import *
from lxml import etree as ET
# import pdb
import traceback


def generateReportXML(report):
    root = ET.Element("report")
    generateHeaders(root,report)
    
    # encoding='ISO-8859-1'
    return ET.tostring(root,method="xml",xml_declaration=False,encoding='utf-8',pretty_print=True)

def generateHeaders(root,report):
    add(root,"schema_version",report.schema_version)
    add(root,"rentity_id",report.rentity_id)
    add(root,"rentity_branch",report.rentity_branch)
    add(root,"submission_code",report.submission_code)
    add(root,"report_code",report.report_code)
    add(root,"entity_reference",report.entity_reference)
    add(root,"fiu_ref_number",report.fiu_ref_number)
    add(root,"submission_date",report.submission_date)
    add(root, "report_date", report.report_date)
    add(root,"currency_code_local",report.currency_code_local)
    
    # reporting_person = addEmpty(root,"reporting_person")

    # addReportingPerson(reporting_person,report.reporting_person)
    add(root, "reporting_user_code", report.reporting_user_code)

    if(report.location):
        location = addEmpty(root,"location")
        addAddress(location,report.location)
    add(root,"reason",report.reason)
    add(root,"action",report.action)

    if(isinstance(report,TransactionReport)):
        for transaction in report.transactions:
            addTransaction(root,transaction)
        
        

    if(isinstance(report,ActivityReport)):
        addActivity(root,report)

    # report_indicators = addEmpty(root,"report_indicators")
    # addReportIndicators(report_indicators,report.report_indicators)
    
def add(parent,tag,value):
    if(value):
        # print(value)
        newTag = ET.SubElement(parent,tag).text = str(value)
        return newTag
    else:
        return None

def addEmpty(parent,tag):
    newTag = ET.SubElement(parent,tag)
    return newTag

def addReportingPerson(parent,reportPerson):
    if(reportPerson):
        add(parent,"gender",reportPerson.gender)
        add(parent,"title",reportPerson.title)
        add(parent,"first_name",reportPerson.first_name)
        add(parent,"middle_name",reportPerson.middle_name)
        add(parent,"prefix",reportPerson.prefix)
        add(parent,"last_name",reportPerson.last_name)
        add(parent,"birthdate",reportPerson.birthdate)
        add(parent,"birth_place",reportPerson.birth_place)
        add(parent,"mothers_name",reportPerson.mothers_name)
        add(parent,"alias",reportPerson.alias)
        add(parent,"ssn",reportPerson.ssn)
        add(parent,"passport_number",reportPerson.passport_number)
        add(parent,"passport_country",reportPerson.passport_country)
        add(parent,"id_number",reportPerson.id_number)
    
        #AddPhones
        addPhones(parent,reportPerson.phones)

        #Add Address
        addAddresses(parent,reportPerson.addresses)
        
        add(parent,"nationality1",reportPerson.nationality1)
        add(parent,"nationality2",reportPerson.nationality2)
        add(parent,"nationality3",reportPerson.nationality3)
        add(parent,"residence",reportPerson.residence)
        add(parent,"email",reportPerson.email)
        add(parent,"occupation",reportPerson.occupation)
        add(parent,"employer_name",reportPerson.employer_name)
        if(reportPerson.employer_address_id):
            employer_address_id = addEmpty(parent,"employer_address_id")
            addAddress(employer_address_id,reportPerson.employer_address_id)

        if(reportPerson.employer_phone_id):
            employer_phone_id = addEmpty(parent,"employer_phone_id")
            addPhone(employer_phone_id,reportPerson.employer_phone_id)
        if(reportPerson.identification):
            addIdentification(parent,reportPerson.identification)

        add(parent,"deceased",reportPerson.deceased)
        add(parent,"tax_number",reportPerson.tax_number)
        add(parent,"tax_reg_number",reportPerson.tax_reg_number)
        add(parent,"source_of_wealth",reportPerson.source_of_wealth)
        add(parent,"comments",reportPerson.comments)

def addAddress(parent,address,othertag=None):
    if(address):
        ad = None
        if(othertag is not None):
            ad = othertag
        else:
            ad = addEmpty(parent,"address")
        add(ad,"address_type",address.address_type)
        add(ad,"address",address.address)
        add(ad,"town",address.town)
        add(ad,"city",address.city)
        add(ad,"zip",address.zip)   
        add(ad,"country_code",address.country_code)
        add(ad,"state",address.state)
        add(ad,"comments",address.comments)

def addIdentification(parent,identification):
    if(identification):
        id = addEmpty(parent,"identification")
        add(id,"type",identification.type)
        add(id,"number",identification.number)
        add(id,"issue_date",identification.issue_date)
        add(id,"expiry_date",identification.expiry_date)
        add(id,"issued_by",identification.issued_by)
        add(id,"issue_country",identification.issue_country)
        add(id,"comments",identification.comments)

def addAddresses(parent,addresses):
    if(addresses):
        # if(len(addresses)==1):
        #     addAddress(parent,addresses[0])
        # elif(len(addresses)>0):
        ad = addEmpty(parent,"addresses")
        for address in addresses:
            addAddress(ad,address)

def addPhones(parent,phones):
    if(phones):
        # if(len(phones)==1):
        #     addPhone(parent,phones[0])
        # elif(len(phones)>1):
        ph= addEmpty(parent,"phones")
        for phone in phones:
            addPhone(ph,phone)

def addPhone(parent,phone,othertag=None):
    if(phone):
        ph = None
        if(othertag is not None):
            ph = othertag
        else:
            ph = addEmpty(parent,"phone")

        add(ph,"tph_contact_type",phone.tph_contact_type)
        add(ph,"tph_communication_type",phone.tph_communication_type)
        add(ph,"tph_country_prefix",phone.tph_country_prefix)
        add(ph,"tph_number",phone.tph_number)
        add(ph,"tph_extension",phone.tph_extension)
        add(ph,"comments",phone.comments)

def  addReportIndicators(parent,report_indicators):
    if(report_indicators):
        for ind in report_indicators:
            add(parent,"indicator",ind.report_indicator)

def addActivity(parent,report):
    activity = addEmpty(parent,"activity")
    addReportParties(activity,report.report_parties)
    if(report.goods_services):
        gs = addEmpty(activity,"goods_services")
        for item in report.goods_services:
            good = addEmpty(gs,"good_service")
            add(good,"item_type",item.item_type)
            add(good,"item_make",item.item_make)
            add(good,"description",item.description)
            add(good,"previously_registered_to",item.previously_registered_to)
            add(good,"presently_registered_to",item.presently_registered_to)
            add(good,"estimated_value",item.estimated_value)
            add(good,"status_code",item.status_code)
            add(good,"status_comments",item.status_comments)
            add(good,"disposed_value",item.disposed_value)
            add(good,"size",item.size)
            add(good,"size_uom",item.size_uom)
            add(good,"address",item.address)
            add(good,"registration_date",item.registration_date)
            add(good,"registration_number",item.registration_number)
            add(good,"identification_number",item.identification_number)
            add(good,"comments",item.comments)


def addTransaction(parent,report):
    try:
        if(report):
            transaction = addEmpty(parent,"transaction")

            add(transaction,"transactionnumber",report.transactionnumber)
            #added for schemma 5.0
            add(transaction,"transaction_is_suspicious", report.transaction_is_suspicious)
            add(transaction,"internal_ref_number",report.internal_ref_number)
            add(transaction,"transaction_location",report.transaction_location)
            add(transaction,"transaction_description",report.transaction_description)
            add(transaction,"date_transaction",report.date_transaction)
            add(transaction,"teller",report.teller)
            add(transaction,"authorized",report.authorized)
            add(transaction,"late_deposit",report.late_deposit)
            add(transaction,"date_posting",report.date_posting)
            add(transaction,"value_date",report.value_date)
            #added for schemma 5.0
            add(transaction,"transaction_type_code",report.transaction_type)
            add(transaction,"transmode_code",report.transmode_code)
            add(transaction,"transmode_comment",report.transmode_comment)
            add(transaction,"amount_local",report.amount_local)

            if(report.t_from):
                tfrom = addEmpty(transaction,"t_from")
                add(tfrom,"from_funds_code",report.t_from.from_funds_code)
                add(tfrom,"from_funds_comment",report.t_from.from_funds_comment)

                addForeignCurrency(tfrom,report.t_from.from_foreign_currency,"from_foreign_currency")
                
                #added for schemma 5.0
                add(tfrom,"conductor_is_suspected", report.t_from.conductor_is_suspected)
                
                # print(report.t_from.from_person,'Person')
                # print(report.t_from.t_conductor)
                # print('reachs this point')
                addConductor(tfrom,report.t_from.t_conductor)
                addAccount(tfrom,"from_account",report.t_from.from_account)
                addPerson(tfrom,"from_person",report.t_from.from_person)
                addEntity(tfrom,"from_entity",report.t_from.from_entity)

                add(tfrom,"from_country",report.t_from.from_country)

            if(report.t_from_my_client):
                tfromMy = addEmpty(transaction,"t_from_my_client")
                add(tfromMy,"from_funds_code",report.t_from_my_client.from_funds_code)
                add(tfromMy,"from_funds_comment",report.t_from_my_client.from_funds_comment)
                add(tfromMy,"conductor_is_suspected", report.t_from_my_client.conductor_is_suspected)

                addForeignCurrency(tfromMy,report.t_from_my_client.from_foreign_currency,"from_foreign_currency")
                addAccount(tfromMy,"from_account",report.t_from_my_client.from_account)
                addPerson(tfromMy,"from_person",report.t_from_my_client.from_person)
                addEntity(tfromMy,"from_entity",report.t_from_my_client.from_entity)

                add(tfromMy,"from_country",report.t_from_my_client.from_country)

            if(report.t_to):
                tto= addEmpty(transaction,"t_to")
                add(tto,"to_funds_code",report.t_to.to_funds_code)
                add(tto,"to_funds_comment",report.t_to.to_funds_comment)

                addForeignCurrency(tto,report.t_to.to_foreign_currency,"to_foreign_currency")
                addAccount(tto,"to_account",report.t_to.to_account)
                addPerson(tto,"to_person",report.t_to.to_person)
                addEntity(tto,"to_entity",report.t_to.to_entity)

                add(tto,"to_country",report.t_to.to_country)

            if(report.t_to_my_client):
                ttoMy = addEmpty(transaction,"t_to_my_client")
                add(ttoMy,"to_funds_code",report.t_to_my_client.to_funds_code)
                add(ttoMy,"to_funds_comment",report.t_to_my_client.to_funds_comment)

                addForeignCurrency(ttoMy,report.t_to_my_client.to_foreign_currency,"to_foreign_currency")
                addAccount(ttoMy,"to_account",report.t_to_my_client.to_account)
                addPerson(ttoMy,"to_person",report.t_to_my_client.to_person)
                addEntity(ttoMy,"to_entity",report.t_to_my_client.to_entity)

                add(ttoMy,"to_country",report.t_to_my_client.to_country)

            if(report.party):
                party= addEmpty(transaction,"party")
                addPerson(party,"person",report.party.person)
                addPerson(party,"person_my_client",report.party.person_my_client)
                addAccount(party,"account",report.party.account)
                addAccount(party,"account_my_client",report.party.account_my_client)
                addEntity(party,"entity",report.party.entity)
                addEntity(party,"entity_my_client",report.party.entity_my_client)
                add(party,"funds_code",report.party.funds_code)
                add(party,"funds_comment",report.party.funds_comment)

                addForeignCurrency(party,report.party.to_foreign_currency,"t_foreign_currency")

                add(party,"country",report.party.country)
                add(party,"significance",report.party.significance)
                add(party,"comments",report.party.comments)

            if(report.goods_services):
                gs = addEmpty(transaction,"goods_services")
                for item in report.goods_services:
                    good = addEmpty(gs,"good_service")
                    add(good,"item_type",item.item_type)
                    add(good,"item_make",item.item_make)
                    add(good,"description",item.description)
                    add(good,"previously_registered_to",item.previously_registered_to)
                    add(good,"presently_registered_to",item.presently_registered_to)
                    add(good,"estimated_value",item.estimated_value)
                    add(good,"status_code",item.status_code)
                    add(good,"status_comments",item.status_comments)
                    add(good,"disposed_value",item.disposed_value)
                    add(good,"size",item.size)
                    add(good,"size_uom",item.size_uom)
                    add(good,"address",item.address)
                    add(good,"registration_date",item.registration_date)
                    add(good,"registration_number",item.registration_number)
                    add(good,"identification_number",item.identification_number)
                    add(good,"comments",item.comments)

            add(transaction,"comments",report.comments)
    except:
        print(traceback.format_exc())

def addForeignCurrency(parent,foreign_currency,name):
    if(foreign_currency):
        fc = addEmpty(parent,name)
        add(fc,"foreign_currency_code",foreign_currency.foreign_currency_code)
        add(fc,"foreign_amount",foreign_currency.foreign_amount)
        add(fc,"foreign_exchange_rate",foreign_currency.foreign_exchange_rate)

def addConductor(parent,t_conductor):
    if(t_conductor):
        addPerson(parent,"t_conductor",t_conductor)
        
def addAccount(root,tag,account):
    
    if(account):
        parent = addEmpty(root,tag)
        add(parent,"institution_name",account.institution_name)
        add(parent,"institution_code",account.institution_code)
        add(parent,"institution_country",account.institution_country)
        add(parent,"swift",account.swift)
        add(parent,"non_banking_institution",account.non_banking_institution)
        add(parent,"branch",account.branch)
        #added for schemma 5.0
        add(parent,"account_category", account.account_category)
        add(parent,"account",account.account)
        add(parent,"currency_code",account.currency_code)
        add(parent,"account_name",account.account_name)
        add(parent,"iban",account.iban)
        add(parent,"client_number",account.client_number)
        add(parent,"personal_account_type",account.personal_account_type)
        #added for schemma 5.0
        add(parent,"account_type", account.account_type)

        addEntity(parent,"t_entity",account.t_entity)
        addSignatory(parent,account.signatory)

        add(parent,"opened",account.opened)
        add(parent,"closed",account.closed)
        add(parent,"balance",account.balance)
        add(parent,"date_balance",account.date_balance)
        add(parent,"status_code",account.status_code)
        add(parent,"beneficiary",account.beneficiary)
        add(parent,"beneficiary_comment",account.beneficiary)
        add(parent,"comments",account.comments)
        
def addPerson(root,tag,person):
    if(person):

        parent = addEmpty(root,tag)

        add(parent,"gender",person.gender)
        add(parent,"title",person.title)
        add(parent,"first_name",person.first_name)
        add(parent,"middle_name",person.middle_name)
        add(parent,"prefix",person.prefix)
        add(parent,"last_name",person.last_name)
        add(parent,"birthdate",person.birthdate)
        add(parent,"birth_place",person.birth_place)
        add(parent,"mothers_name",person.mothers_name)
        add(parent,"alias",person.alias)
        add(parent,"ssn",person.ssn)
        add(parent,"passport_number",person.passport_number)
        add(parent,"passport_country",person.passport_country)
        add(parent,"id_number",person.id_number)
        add(parent,"nationality1",person.nationality1)
        add(parent,"nationality2",person.nationality2)
        add(parent,"nationality3",person.nationality3)
        add(parent,"residence",person.residence)
    
        #AddPhones
        addPhones(parent,person.phones)

        #Add Address
        addAddresses(parent,person.addresses)
        
        add(parent,"email",person.email)
        add(parent,"occupation",person.occupation)
        add(parent,"employer_name",person.employer_name)

        if(person.employer_address_id):
            employer_address_id = addEmpty(parent,"employer_address_id")
            addAddress(employer_address_id,person.employer_address_id,othertag=employer_address_id)

        if(person.employer_phone_id):
            employer_phone_id = addEmpty(parent,"employer_phone_id")
            addPhone(employer_phone_id,person.employer_phone_id,othertag=employer_phone_id)

        if(person.identification):    
            addIdentification(parent,person.identification)

        add(parent,"deceased",person.deceased)
        add(parent,"tax_number",person.tax_number)
        add(parent,"tax_reg_number",person.tax_reg_number)

        if(person.peps):
            addPeps(parent,person.peps)


        add(parent,"source_of_wealth",person.source_of_wealth)
        add(parent,"comments",person.comments)

def addEntity(root,tag,entity):
    if(entity):
        parent = addEmpty(root,tag)
        add(parent,"name",entity.name)
        add(parent,"commercial_name",entity.commercial_name)
        add(parent,"incorporation_legal_form",entity.incorporation_legal_form)
        add(parent,"incorporation_number",entity.incorporation_number)
        add(parent,"incorporation_number",entity.fincorporation_number)
        add(parent,"business",entity.business)

        addPhones(parent,entity.phones)
        addAddresses(parent,entity.addresses)

        add(parent,"email",entity.email)
        add(parent,"incorporation_state",entity.incorporation_state)
        add(parent,"incorporation_country_code",entity.incorporation_country_code)
        
        if(entity.director_id):
            addPerson(parent,"director_id",entity.director_id)

        addRelatedPersons(parent,entity.related_persons)

        add(parent,"incorporation_date",entity.incorporation_date)
        add(parent,"business_closed",entity.business_closed)
        add(parent,"date_business_closed",entity.date_business_closed)
        add(parent,"tax_number",entity.tax_number)
        add(parent,"tax_reg_number",entity.tax_reg_number)
        add(parent,"comments",entity.comments)
    
def addSignatory(parent,signatory):

    if(signatory):
        sg = addEmpty(parent,"signatory")
        add(sg,"is_primary",signatory.is_primary)
        addPerson(sg,"t_person",signatory.t_person)
        addPerson(sg,"t_person",signatory.t_person_my_client)
        add(sg,"role",signatory.role)

def addRelatedPersons(parent,related_persons):

    if(related_persons):
        sg = addEmpty(parent,"related_persons")
        addPerson(sg,"t_person",related_persons.t_person)
        addPerson(sg,"t_person",related_persons.t_person_my_client)
        add(sg,"role",related_persons.role)

def addPeps(parent,peps):
    if(peps):
        pep = addEmpty(parent,"peps")
        add(pep,"pep_country",peps.pep_country)
        add(pep,"function_description",peps.function_description)
        
def addReportParties(parent,report_parties):
    for rp in report_parties:
        rep = addEmpty(parent,"report_party")

        addPerson(rep,"person",rp.person)
        addAccount(rep,"account",rp.account)
        addEntity(rep,"entity",rp.entity)
        add(rep,"significance",rp.significance)
        add(rep,"reason",rp.reason)
        add(rep,"comments",rp.comments)
