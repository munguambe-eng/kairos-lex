import pandas as pd
import datetime
from datetime import timedelta
import re
import warnings
warnings.filterwarnings('ignore')
import xml.etree.ElementTree as ET
from scripts.obj import * 
import scripts.schemaActions as schemaActions
import logging
import os
import sys
import traceback


today=datetime.date.today()

def helo():
    print('helo world')

def tag_report(config=None):
    """
    Build a TransactionReport header.
    If config dict is provided, its values override the defaults.
    This allows the Kairos portal to pass per-upload configuration
    while keeping backward compatibility with direct script usage.
    """
    today = datetime.date.today()
    cfg = config or {}

    location = TAddress()
    location.address_type = 'B'
    location.address = cfg.get('location_address', 'Praca 25 de Junho')
    location.city = cfg.get('location_city', 'Maputo')
    location.country_code = cfg.get('location_country', 'MZ')
    location.state = cfg.get('location_state', 'Maputo')

    report = TransactionReport()
    report.rentity_id = str(cfg.get('rentity_id', '44'))
    report.rentity_branch = cfg.get('rentity_branch', 'HEAD-OFFICE')
    report.submission_code = cfg.get('submission_code', 'E')
    report.schema_version = cfg.get('schema_version', '5.0.2')
    report.report_date = cfg.get('report_date', today.strftime('%Y-%m-%dT%H:%M:%S'))
    report.reporting_user_code = cfg.get('reporting_user_code', 'Alfredo')
    report.currency_code_local = cfg.get('currency_code_local', 'MZN')
    report.location = location
    report.reason = ""
    report.action = 'N/A'
    return report

def convert_int(x):
    if x=='':
        return 0
    else:
        return float(x)

def initialize_dataframes(conn):
    # if today_dt!=creation_date:
    if 1==1:
        print('execute querys')
        bank_query = open("bank.sql", "r").read()
        bank=pd.read_sql(bank_query,conn)
        bank.to_csv('swift_bank.csv')


        customers_query = open("customers.sql", "r").read()
        customers=pd.read_sql(customers_query,conn)
        customers.to_csv('customers.csv',index=False)


        branch_query=open('branch.sql','r').read()

        branch=pd.read_sql(branch_query,conn)
        branch.to_csv('branch.csv')

        # branch=pd.read_csv('branch.csv')

        transaction_code_query=open('transaction_code.sql','r').read()

        transaction_code=pd.read_sql(transaction_code_query,conn)
        transaction_code.to_csv('transaction_code.csv')


        balances_query=open('balances.sql','r').read()

        balances=pd.read_sql(balances_query,conn)


        balances.to_csv('balances.csv')

        signatory_query=open('signatory.sql','r').read()

        signatory=pd.read_sql(signatory_query,conn)

    # signatory=pd.read_csv('signatory.csv')

        signatory.to_csv('signatory.csv')

        industry_query=open('industry.sql','r').read()

        industry=pd.read_sql(industry_query,conn)
        industry.to_csv('industry.csv')
        
        country_sql=open('country.sql','r').read()
        country=pd.read_sql(country_sql,conn)
        country.to_csv('country.csv')
        
    else:
        bank=pd.read_csv('swift_bank.csv')
        customers_query = open("customers.sql", "r").read()
        # customers=pd.read_sql(customers_query,conn)
        # customers.to_csv('customers.csv',index=False)
        customers=pd.read_csv('customers.csv')
        branch_query=open('branch.sql','r').read()
        # branch=pd.read_sql(branch_query,conn)
        branch=pd.read_csv('branch.csv')
        transaction_code=pd.read_csv('transaction_code.csv')
        balances=pd.read_csv('balances.csv')
        # signatory_query=open('signatory.sql','r').read()
        signatory=pd.read_csv('signatory.csv')
        # signatory=pd.read_sql(signatory_query,conn)
        signatory=signatory.dropna()
        # signatory.to_csv('signatory.csv')
        
        industry=pd.read_csv('industry.csv')
        country=pd.read_csv('country.csv')
        
    
    
    #converting datatypes  
    customers=customers[customers['cus_n']!=90000]
    balances['DTL_acct_n']=balances['DTL_acct_n'].astype('str')
    industry['indu_c']=industry['indu_c'].astype('int')
    customers['CUS_Industry']=customers['CUS_Industry'].fillna(0)
    customers=customers[customers['cus_n']!=90000]
    # customers['CUS_Industry']=customers['CUS_Industry'].astype(int) 
    customers['CUS_Industry'] = pd.to_numeric(customers['CUS_Industry'], errors='coerce').fillna(0).astype(int)
    industry['indu_C']=industry['indu_c'].astype(int)
    customers=customers[~pd.isna(customers['cus_target'])]
    customers['cus_target'] = pd.to_numeric(customers['cus_target'], errors='coerce').fillna(0).astype(int)
    # customers['cus_target']=customers['cus_target'].astype(int)
    customers['cus_n']=pd.to_numeric(customers['cus_n'], errors='coerce').fillna(0).astype(int)
    signatory=signatory.dropna()
    signatory['cus_n_rel']=signatory['cus_n_rel'].apply(convert_int).astype(int)
    # customers['cus_n']=customers['cus_n'].astype(int)
    customers['cus_n'] = pd.to_numeric(customers['cus_n'], errors='coerce').fillna(0).astype(int)

    balances['CRB_DTE']=pd.to_datetime(balances['CRB_DTE'])
    balances['DTL_Date_Opened']=pd.to_datetime(balances['DTL_Date_Opened'])
    balances['CRB_DTE']=balances['CRB_DTE'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    balances['DTL_Date_Opened']=balances['DTL_Date_Opened'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    balances['CRB_Balance_LCY'].replace('nan',0,inplace=True)
    customers=customers.applymap(str)
    balances=balances.applymap(str)
    signatory=signatory[pd.isna(signatory['cus_n_rel'])==False]
    # signatory=signatory[signatory['cus_n_rel'].isin(customers['cus_n'])]
    customers['cus_town']=customers['cus_town'].fillna('-')
    
    customers['cus_tel_no1'].fillna('258',inplace=True)
    balances=balances.applymap(str)
    branch=branch.applymap(str)
    signatory=signatory.applymap(str)
    customers[customers['cus_town']=='']['cus_town']='-'

    return bank, customers, branch, transaction_code,balances,signatory,industry,country




# today=today.strftime('%Y-%m-%d')

def create_dir():
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Daily Structured"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')


def report_date_month(hoje):
    # from datetime import datetime 

    # hoje=datetime.now()
    primeiro_dia=hoje.replace(day=1)-timedelta(days=hoje.day)
    primeiro_dia=primeiro_dia.replace(day=1)
    ultimo_dia=hoje.replace(day=1)-timedelta(days=1)
    return hoje, 'between '+"'"+str(primeiro_dia.strftime('%Y-%m-%d'))+"'"+' and '+"'"+str(ultimo_dia.strftime('%Y-%m-%d'))+"'"

def report_date_Week(today):
    monday=today-datetime.timedelta(days=today.weekday()+7)
    friday=today-datetime.timedelta(days=today.weekday()+3)
    return today,' between '+"'"+str(monday)+"'"+' and '+"'"+str(friday)+"'" 

def converttoint(x):
    if x!='':
        cleaned_str=''.join(c for c in
                        x.split()[0] if c.isdigit())
    else:
        cleaned_str=0
    return int(cleaned_str)

def is_valid_email(email):
    pattern=r'^[\w\.-]+@[\w\.-]+\.w+'
    if re.match(pattern,email):
        return True
    else:
        return False
    
def id_type(x):
    if x==2:
        return 'B'
    elif x==1:
        return 'C'
    elif x==11:
        return 'A'
    
def bran(valor):
    return valor[:3]
    

def convert_cards_types(ACF2,ACF2UT_nacionais,ACF2UT_internacionais,balances):
    ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
    ACF2['ft_debit_acct_no']=ACF2['ft_debit_acct_no'].astype(str)

    ACF2['ft_data_transacao']=pd.to_datetime(ACF2['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    ACF2UT_nacionais['ft_credit_acct_no']=ACF2UT_nacionais['outside_bank_acct'].astype('str')
    ACF2UT_nacionais['ft_debit_acct_no']=ACF2UT_nacionais['ft_debit_acct_no'].astype(str)
    ACF2UT_nacionais['ft_data_transacao']=pd.to_datetime(ACF2UT_nacionais['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    
    ACF2['codigo_balcao']=ACF2['ft_debit_acct_no'].apply(bran)
    ACF2UT_nacionais['codigo_balcao']=ACF2UT_nacionais['ft_debit_acct_no'].apply(bran)
    ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2UT_nacionais=ACF2UT_nacionais[ACF2UT_nacionais['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
    ACF2UT_internacionais['ft_credit_acct_no']=ACF2UT_internacionais['outside_bank_acct'].astype('str')
    ACF2UT_internacionais['ft_debit_acct_no']=ACF2UT_internacionais['ft_debit_acct_no'].astype(str)

    ACF2UT_internacionais['ft_data_transacao']=pd.to_datetime(ACF2UT_internacionais['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')


    ACF2UT_internacionais['codigo_balcao']=ACF2UT_internacionais['ft_debit_acct_no'].apply(bran)
    ACF2UT_internacionais=ACF2UT_internacionais[ACF2UT_internacionais['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2=ACF2[ACF2['outside_bank_acct'].isin(balances['DTL_acct_n'].astype(str))]
    
    print(ACF2.shape[0],' ACF2')
    print(ACF2.shape[0],' ACF2')
    return ACF2,ACF2UT_nacionais,ACF2UT_internacionais
    
def convert_cards_MEFT(ACF2,ACF2UT_nacionais,balances):
    ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
    ACF2['ft_debit_acct_no']=ACF2['ft_debit_acct_no'].astype(str)

    ACF2['ft_data_transacao']=pd.to_datetime(ACF2['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    ACF2UT_nacionais['ft_credit_acct_no']=ACF2UT_nacionais['outside_bank_acct'].astype('str')
    ACF2UT_nacionais['ft_debit_acct_no']=ACF2UT_nacionais['ft_debit_acct_no'].astype(str)
    ACF2UT_nacionais['ft_data_transacao']=pd.to_datetime(ACF2UT_nacionais['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    
    ACF2['codigo_balcao']=ACF2['ft_debit_acct_no'].apply(bran)
    ACF2UT_nacionais['codigo_balcao']=ACF2UT_nacionais['ft_debit_acct_no'].apply(bran)
    ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2UT_nacionais=ACF2UT_nacionais[ACF2UT_nacionais['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
    ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2=ACF2[ACF2['outside_bank_acct'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    ACF2=ACF2[ACF2['outside_bank_acct'].isin(balances['DTL_acct_n'].astype(str))]
    
    print('us on us ',ACF2.shape[0])
    print('us on them ',ACF2UT_nacionais.shape[0])
   
    return ACF2,ACF2UT_nacionais
    
    
def convert_cards_MIFT(ACF2UT_internacionais,balances):
    
    ACF2UT_internacionais['ft_credit_acct_no']=ACF2UT_internacionais['outside_bank_acct'].astype('str')
    ACF2UT_internacionais['ft_debit_acct_no']=ACF2UT_internacionais['ft_debit_acct_no'].astype(str)

    ACF2UT_internacionais['ft_data_transacao']=pd.to_datetime(ACF2UT_internacionais['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')


    ACF2UT_internacionais['codigo_balcao']=ACF2UT_internacionais['ft_debit_acct_no'].apply(bran)
    ACF2UT_internacionais=ACF2UT_internacionais[ACF2UT_internacionais['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
    print(ACF2UT_internacionais.shape[0])
    return ACF2UT_internacionais


# def convert_cards_MEFT(ACF2,ACF2UT_nacionais,balances):
    
#     ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
#     ACF2['ft_debit_acct_no']=ACF2['ft_debit_acct_no'].astype(str)

#     ACF2['ft_data_transacao']=pd.to_datetime(ACF2['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
#     ACF2UT_nacionais['ft_credit_acct_no']=ACF2UT_nacionais['outside_bank_acct'].astype('str')
#     ACF2UT_nacionais['ft_debit_acct_no']=ACF2UT_nacionais['ft_debit_acct_no'].astype(str)
#     ACF2UT_nacionais['ft_data_transacao']=pd.to_datetime(ACF2UT_nacionais['ft_data_transacao']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    
#     ACF2['codigo_balcao']=ACF2['ft_debit_acct_no'].apply(bran)
#     ACF2UT_nacionais['codigo_balcao']=ACF2UT_nacionais['ft_debit_acct_no'].apply(bran)
#     ACF2=ACF2[ACF2['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
#     ACF2UT_nacionais=ACF2UT_nacionais[ACF2UT_nacionais['ft_debit_acct_no'].isin(balances['DTL_acct_n'].astype(str))]
#     ACF2['outside_bank_acct']=ACF2['outside_bank_acct'].astype('str')
    
#     return ACF2UT_nacionais
    
def convert_credit_cards(credit_card,balances):
    
    credit_card['BCM_DDA_ACCOUNT_NUMBER'].value_counts()
    credit_card['date_transaction']=pd.to_datetime(credit_card['date_transaction']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    credit_card['value_date']=pd.to_datetime(credit_card['value_date']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    credit_card['transaction_number']=credit_card['transaction_number'].astype(int)
    credit_card['internal_ref_number']=credit_card['internal_ref_number'].astype(int)
    credit_card['transaction_number']=credit_card['transaction_number'].astype(str)
    credit_card['internal_ref_number']=credit_card['internal_ref_number'].astype(str)
    credit_card=credit_card[credit_card['BCM_CARDHOLDER_NBR'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    credit_card_copy=credit_card.copy()
    credit_card_copy=credit_card_copy[~pd.isna(credit_card_copy['BCM_CARDHOLDER_NBR'])]

    print(credit_card_copy.shape[0], 'Credit cards')
    return credit_card_copy
     
def convert_cash_deposits(cash_deposits,pagamentos_copy,venda_de_moeda,levantamento_de_cheques,balances,customer_sign,customers_personal,engine,today):
    cash_deposits=cash_deposits[~pd.isna(cash_deposits['DEPOSITOR'])]
    cash_deposits=cash_deposits.drop_duplicates()
    cash_deposits_copy=cash_deposits.copy()

    cash_deposits_not_in_accts=cash_deposits[~cash_deposits['account_2'].isin(balances['DTL_acct_n'].astype(str))]
    cash_deposits_cus=cash_deposits[~cash_deposits['CHARGE_CUSTOMER'].astype(str).isin(balances['CUSTOMER'].astype(str))]

    cash_deposits=cash_deposits_copy[cash_deposits_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    cash_deposits=cash_deposits[cash_deposits['CHARGE_CUSTOMER'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    cash_deposits['ISSUE.COUNTRY']=cash_deposits['ISSUE.COUNTRY'].fillna('MZ')
    cash_deposits_copy['ISSUE.COUNTRY']=cash_deposits_copy['ISSUE.COUNTRY'].fillna('MZ')

    cash_deposits_without_sign=cash_deposits[~cash_deposits['CUSTOMER_2'].isin(customer_sign['CUSTOMER']) ]
    cash_deposits_without_sign=cash_deposits_without_sign[~cash_deposits_without_sign['CUSTOMER_2'].isin(customers_personal['cus_n'])]
    cash_deposits_without_sign=cash_deposits_without_sign[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    cash_deposits_without_sign['reason']='No Signatory'
    cash_deposits=cash_deposits[~cash_deposits['CUSTOMER_2'].isin(cash_deposits_without_sign['CUSTOMER_2'])]
    cash_deposits_not_in_accts=pd.concat([cash_deposits_cus,cash_deposits_not_in_accts])
    cash_deposits_not_in_accts=cash_deposits_not_in_accts[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    cash_deposits_not_in_accts['reason']='Account not in balance'
    cash_deposits_exceptions=pd.concat([cash_deposits_without_sign,cash_deposits_not_in_accts])
    cash_deposits_exceptions['report_date']=today
    
    # if cash_deposits_exceptions.shape[0]>0:
        # cash_deposits_exceptions.to_sql("Cash Deposits Exceptions", con=engine, if_exists="replace")

    
    print(len(cash_deposits), 'Cash deposits total transactions')
    print(len(cash_deposits_exceptions), 'Cash deposits total transactions exception')
    cash_deposits.to_excel('Cash deposits.xlsx')
    cash_deposits_exceptions.to_excel('Exceptions Cash Deposits.xlsx')


    pagamentos_copy_submit=pagamentos_copy.copy()
    pagamentos_copy=pagamentos_copy[~pd.isna(pagamentos_copy['DEPOSITOR'])]
    pagamentos_copy=pagamentos_copy.drop_duplicates()
    pagamentos_copy=pagamentos_copy.copy()

    pagamentos_copy_not_in_accts=pagamentos_copy[~pagamentos_copy['account_2'].isin(balances['DTL_acct_n'].astype(str))]
    pagamentos_copy_cus=pagamentos_copy[~pagamentos_copy['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]

    pagamentos_copy=pagamentos_copy[pagamentos_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    pagamentos_copy=pagamentos_copy[pagamentos_copy['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    pagamentos_copy['ISSUE.COUNTRY']=pagamentos_copy['ISSUE.COUNTRY'].fillna('MZ')
    pagamentos_copy_submit['ISSUE.COUNTRY']=pagamentos_copy_submit['ISSUE.COUNTRY'].fillna('MZ')

    pagamentos_copy_without_sign=pagamentos_copy[~pagamentos_copy['CUSTOMER_2'].isin(customer_sign['CUSTOMER']) ]
    pagamentos_copy_without_sign=pagamentos_copy_without_sign[~pagamentos_copy_without_sign['CUSTOMER_2'].isin(customers_personal['cus_n'])]
    pagamentos_copy_without_sign=pagamentos_copy_without_sign[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    pagamentos_copy_without_sign['reason']='No Signatory'

    pagamentos_copy=pagamentos_copy[~pagamentos_copy['CUSTOMER_2'].isin(pagamentos_copy_without_sign['CUSTOMER_2'])]
    pagamentos_copy_not_in_accts=pd.concat([pagamentos_copy_cus,pagamentos_copy_not_in_accts])
    pagamentos_copy_not_in_accts=pagamentos_copy_not_in_accts[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    pagamentos_copy_not_in_accts['reason']='Account not in Balance'

    pagamentos_copy_exceptions=pd.concat([pagamentos_copy_without_sign,pagamentos_copy_not_in_accts])
    pagamentos_copy_exceptions['report_date']=today

    # if pagamentos_copy_exceptions.shape[0]>0:
        # pagamentos_copy_exceptions.to_sql("Cash Deposits Exceptions", con=engine, if_exists="append")


    print(len(pagamentos_copy), 'Pagamentos total transactions')
    print(len(pagamentos_copy_exceptions), 'pagamentos total transactions exception')
    pagamentos_copy.to_excel('Pagamento de cheque.xlsx')
    pagamentos_copy_exceptions.to_excel('Exceptions Pagamento de Cheques.xlsx')


    
    
    levantamento_de_cheques=levantamento_de_cheques[~pd.isna(levantamento_de_cheques['DEPOSITOR'])]
    levantamento_de_cheques=levantamento_de_cheques.drop_duplicates()
    levantamento_de_cheques_copy=levantamento_de_cheques.copy()
    levantamento_de_cheques_copy['ISSUE.COUNTRY']=levantamento_de_cheques_copy['ISSUE.COUNTRY'].fillna('MZ')


    levantamento_de_cheques_not_in_accts=levantamento_de_cheques[~levantamento_de_cheques['account_2'].isin(balances['DTL_acct_n'].astype(str))]
    levantamento_de_cheques_cus=levantamento_de_cheques[~levantamento_de_cheques['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]

    levantamento_de_cheques=levantamento_de_cheques_copy[levantamento_de_cheques_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    levantamento_de_cheques=levantamento_de_cheques[levantamento_de_cheques['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    levantamento_de_cheques['ISSUE.COUNTRY']=levantamento_de_cheques['ISSUE.COUNTRY'].fillna('MZ')

    levantamento_de_cheques_without_sign=levantamento_de_cheques[~levantamento_de_cheques['CUSTOMER_2'].isin(customer_sign['CUSTOMER']) ]
    levantamento_de_cheques_without_sign=levantamento_de_cheques_without_sign[~levantamento_de_cheques_without_sign['CUSTOMER_2'].isin(customers_personal['cus_n'])]
    levantamento_de_cheques_without_sign=levantamento_de_cheques_without_sign[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    levantamento_de_cheques_without_sign['reason']='No Signatory'
    levantamento_de_cheques=levantamento_de_cheques[~levantamento_de_cheques['CUSTOMER_2'].isin(levantamento_de_cheques_without_sign['CUSTOMER_2'])]
    levantamento_de_cheques_not_in_accts=pd.concat([levantamento_de_cheques_cus,levantamento_de_cheques_not_in_accts])
    levantamento_de_cheques_not_in_accts=levantamento_de_cheques_not_in_accts[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    levantamento_de_cheques_not_in_accts['reason']='Account not in Balance'

    levantamento_de_cheques_exceptions=pd.concat([levantamento_de_cheques_without_sign,levantamento_de_cheques_not_in_accts])
    
    
    levantamento_de_cheques_exceptions['report_date']=today
    # if levantamento_de_cheques_exceptions.shape[0]>0:
        # levantamento_de_cheques_exceptions.to_sql("Cash Deposits Exceptions", con=engine, if_exists="append")

    print(len(levantamento_de_cheques), 'Levantamento de cheques total transactions')
    print(len(levantamento_de_cheques_exceptions), 'Levantamento de cheques total transactions exception')
    levantamento_de_cheques.to_excel('Levantamento de cheques.xlsx')
    levantamento_de_cheques_exceptions.to_excel('Exceptions Levantamento de cheques.xlsx')

    
    venda_de_moeda=venda_de_moeda[~pd.isna(venda_de_moeda['DEPOSITOR'])]
    venda_de_moeda=venda_de_moeda.drop_duplicates()
    venda_de_moeda_copy=venda_de_moeda.copy()
    venda_de_moeda_copy['ISSUE.COUNTRY']=venda_de_moeda_copy['ISSUE.COUNTRY'].fillna('MZ')

    venda_de_moeda_not_in_accts=venda_de_moeda[~venda_de_moeda['account_2'].isin(balances['DTL_acct_n'].astype(str))]
    venda_de_moeda_cus=venda_de_moeda[~venda_de_moeda['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]

    venda_de_moeda=venda_de_moeda_copy[venda_de_moeda_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    venda_de_moeda=venda_de_moeda[venda_de_moeda['CUSTOMER_2'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    venda_de_moeda['ISSUE.COUNTRY']=venda_de_moeda['ISSUE.COUNTRY'].fillna('MZ')

    venda_de_moeda_without_sign=venda_de_moeda[~venda_de_moeda['CUSTOMER_2'].isin(customer_sign['CUSTOMER']) ]
    venda_de_moeda_without_sign=venda_de_moeda_without_sign[~venda_de_moeda_without_sign['CUSTOMER_2'].isin(customers_personal['cus_n'])]
    venda_de_moeda_without_sign=venda_de_moeda_without_sign[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    venda_de_moeda_without_sign['reason']='No Signatory'
    venda_de_moeda=venda_de_moeda[~venda_de_moeda['CUSTOMER_2'].isin(venda_de_moeda_without_sign['CUSTOMER_2'])]
    venda_de_moeda_not_in_accts=pd.concat([venda_de_moeda_cus,venda_de_moeda_not_in_accts])
    venda_de_moeda_not_in_accts=venda_de_moeda_not_in_accts[['transactionnumber','internal_ref_number','value_date','account_2','CUSTOMER_2','net_amount_check','AMOUNT_LOCAL_1','transaction_description','DEPOSITOR','ID.TYPE','TELEPHONE NUMBER']]
    venda_de_moeda_not_in_accts['reason']='Account not in Balance'

    venda_de_moeda_exceptions=pd.concat([venda_de_moeda_without_sign,venda_de_moeda_not_in_accts])
    
    
    venda_de_moeda_exceptions['report_date']=today
    # if venda_de_moeda_exceptions.shape[0]>0:
        # venda_de_moeda_exceptions.to_sql("Cash Deposits Exceptions", con=engine, if_exists="append")
    
    print(len(venda_de_moeda), 'Venda de moedas total transactions')
    venda_de_moeda.to_excel('venda de moedas.xlsx')
    print(len(venda_de_moeda_exceptions), 'Venda de moedas total transactions exception')
    venda_de_moeda_exceptions.to_excel('Exceptions venda de moedas.xlsx')


    cash_deposits_copy.to_excel('cash to validate.xlsx')
    pagamentos_copy_submit.to_excel('pagamentos to validate.xlsx')
    venda_de_moeda_copy.to_excel('vendas to validate.xlsx')
    levantamento_de_cheques_copy.to_excel('Levantamentos to validate.xlsx')

    # return cash_deposits,pagamentos_copy,venda_de_moeda,levantamento_de_cheques
    cash_deposits_copy=cash_deposits_copy[cash_deposits_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    cash_deposits_copy.to_excel('Mapped Cash deposits.xlsx')
    pagamentos_copy_submit=pagamentos_copy_submit[pagamentos_copy_submit['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    pagamentos_copy_submit.to_excel('Mapped Pagamentos.xlsx')

    venda_de_moeda_copy=venda_de_moeda_copy[venda_de_moeda_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]

    venda_de_moeda_copy.to_excel('Mapped venda de moedas.xlsx')
    levantamento_de_cheques_copy=levantamento_de_cheques_copy[levantamento_de_cheques_copy['account_2'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    levantamento_de_cheques_copy.to_excel('Mapped levantamentos.xlsx')


    return cash_deposits_copy,pagamentos_copy_submit,venda_de_moeda_copy,levantamento_de_cheques_copy


def convert_ITT_OTT(ITT,OT03,balances,customer_sign,customers_personal,engine,today):
    ITT=ITT.drop_duplicates()
    
    print(len(ITT),'ITT no duplicates')
    ITT_swift=ITT[pd.isna(ITT['IN.SWIFT.MSG10'])]
    ITT=ITT[~pd.isna(ITT['IN.SWIFT.MSG10'])]


    ITT_not_in_accts=ITT[~ITT['CREDIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]

    ITT=ITT[ITT['CREDIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]

    ITT_without_sign=ITT[~ITT['credit_customer'].astype(str).isin(customer_sign['CUSTOMER'].astype(str)) ]
    ITT_without_sign=ITT_without_sign[~ITT_without_sign['credit_customer'].isin(customers_personal['cus_n'])]
    ITT=ITT[~ITT['credit_customer'].isin(ITT_without_sign['credit_customer'])]
    ITT_without_sign=ITT_without_sign[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    ITT_without_sign['reason']='No Signatory'

    ITT_not_in_accts=ITT_not_in_accts[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    ITT_not_in_accts['reason']='Account not in balance'
    
    ITT_swift=ITT_swift[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    ITT_swift['reason']='IN.SWIFT.MSG10 is null'

    ITT_exceptions=pd.concat([ITT_without_sign,ITT_not_in_accts,ITT_swift])
    ITT_exceptions=ITT_exceptions.drop_duplicates()
    ITT_exceptions['report_date']=today
    
    
    # if ITT_exceptions.shape[0]>0:
        # ITT_exceptions.to_sql("ITT Exceptions", con=engine, if_exists="replace")

    
    print(len(ITT), 'ITT total transactions')
    print(len(ITT_exceptions), 'ITT total transactions exception')
    
    OT03=OT03.drop_duplicates()

    OT03_not_in_accts=OT03[~OT03['DEBIT_ACCT_NO'].isin(balances['DTL_acct_n'].astype(str))]

    OT03_cus=OT03_not_in_accts[~OT03_not_in_accts['debit_customer'].astype(str).isin(balances['CUSTOMER'].astype(str))]
    OT03=OT03[OT03['DEBIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    OT03=OT03[OT03['debit_customer'].astype(str).isin(balances['CUSTOMER'].astype(str))]

    OT03_without_sign=OT03[~OT03['debit_customer'].isin(customer_sign['CUSTOMER']) ]
    OT03_without_sign=OT03_without_sign[~OT03_without_sign['debit_customer'].isin(customers_personal['cus_n'])]
    OT03_without_sign=OT03_without_sign[['transactionnumber','internal_ref_number','credit_value_date','BEN_ACCT_NO','debit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    OT03_without_sign['reason']='No Signatory'
    OT03_not_in_accts=OT03_not_in_accts[['transactionnumber','internal_ref_number','credit_value_date','BEN_ACCT_NO','debit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    OT03_not_in_accts['reason']='Account not in balance'
    OT03_exceptions=pd.concat([OT03_without_sign,OT03_not_in_accts])
    OT03_exceptions['report_date']=today
    OT03=OT03[~OT03['debit_customer'].isin(OT03_exceptions['debit_customer'])]

    # if OT03_exceptions.shape[0]>0:
        # OT03_exceptions.to_sql("OTT Exceptions", con=engine, if_exists="replace")


    print(len(OT03), 'OT03 total transactions')
    print(len(OT03_exceptions), 'OT03 total transactions exception')
    
    return ITT,OT03

def convert_bol(eft,balances,customer_sign,customers_personal,engine,today):
    eft=eft.drop_duplicates()
    
    
    credit_account_not_present=eft[~eft['ft_credit_acct_no'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    debit_account_not_present=eft[~eft['ft_debit_acct_no'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    missing_balances=pd.concat([credit_account_not_present,debit_account_not_present])
    eft_copy=eft[eft['ft_credit_acct_no'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    eft=eft_copy[eft_copy['ft_debit_acct_no'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    missing_balances=missing_balances[['transactionnumber','credit_value_date','ft_credit_acct_no','FT_Credit_Customer','ft_debit_customer','sum_amt','ft_Amount_debited','ft_debit_their_ref','ft_debit_acct_no']]
    missing_balances['reason']='Account not in Balance'
    
    
    eft_without_sign=eft[~eft['FT_Credit_Customer'].astype(str).isin(customer_sign['CUSTOMER'].astype(str)) ]
    eft_without_sign=eft_without_sign[~eft_without_sign['FT_Credit_Customer'].astype(str).isin(customers_personal['cus_n'].astype(str))]
    eft=eft[~eft['FT_Credit_Customer'].isin(eft_without_sign['FT_Credit_Customer'])]
    eft_without_sign_credit=eft_without_sign[['transactionnumber','credit_value_date','ft_credit_acct_no','FT_Credit_Customer','ft_debit_customer','sum_amt','ft_Amount_debited','ft_debit_their_ref','ft_debit_acct_no']]
    eft_without_sign_credit['reason']='No Signatory'
    
    eft_without_sign=eft[~eft['ft_debit_customer'].astype(str).isin(customer_sign['CUSTOMER'].astype(str)) ]
    eft_without_sign=eft_without_sign[~eft_without_sign['ft_debit_customer'].astype(str).isin(customers_personal['cus_n'].astype(str))]
    eft=eft[~eft['ft_debit_customer'].isin(eft_without_sign['ft_debit_customer'])]
    eft_without_sign_debit=eft_without_sign[['transactionnumber','credit_value_date','ft_credit_acct_no','FT_Credit_Customer','ft_debit_customer','sum_amt','ft_Amount_debited','ft_debit_their_ref','ft_debit_acct_no']]
    eft_without_sign_debit['reason']='No Signatory'
    
    eft_exceptions=pd.concat([eft_without_sign_debit,eft_without_sign_credit,missing_balances])
    eft_exceptions=eft_exceptions.drop_duplicates()
    eft_exceptions['report_date']=today
    
    
    # if eft_exceptions.shape[0]>0:
    #     eft_exceptions.to_sql("bol Exceptions", con=engine, if_exists="replace")

    
    print(len(eft), 'bol total transactions')
    print(len(eft_exceptions), 'bol total transactions exception')
    
    return eft


def convert_eft(eft,balances,customer_sign,customers_personal,engine,today):
    eft=eft.drop_duplicates()
    
    credit_account_not_present=eft[~eft['CREDIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    debit_account_not_present=eft[~eft['DEBIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    missing_balances=pd.concat([credit_account_not_present,debit_account_not_present])
    eft_copy=eft[eft['CREDIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    eft=eft_copy[eft_copy['DEBIT_ACCT_NO'].astype(str).isin(balances['DTL_acct_n'].astype(str))]
    missing_balances=missing_balances[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','debit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    missing_balances['reason']='Account not in Balance'
    
    
    eft_without_sign=eft[~eft['credit_customer'].astype(str).isin(customer_sign['CUSTOMER'].astype(str)) ]
    eft_without_sign=eft_without_sign[~eft_without_sign['credit_customer'].astype(str).isin(customers_personal['cus_n'].astype(str))]
    eft=eft[~eft['credit_customer'].isin(eft_without_sign['credit_customer'])]
    eft_without_sign_credit=eft_without_sign[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','debit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    eft_without_sign_credit['reason']='No Signatory'
    
    eft_without_sign=eft[~eft['debit_customer'].astype(str).isin(customer_sign['CUSTOMER'].astype(str)) ]
    eft_without_sign=eft_without_sign[~eft_without_sign['debit_customer'].astype(str).isin(customers_personal['cus_n'].astype(str))]
    eft=eft[~eft['debit_customer'].isin(eft_without_sign['debit_customer'])]
    eft_without_sign_debit=eft_without_sign[['transactionnumber','internal_ref_number','credit_value_date','CREDIT_ACCT_NO','credit_customer','debit_customer','net_amount_check','LOC_AMT_DEBITED','transaction_description','DEBIT_ACCT_NO']]
    eft_without_sign_debit['reason']='No Signatory'
    
    eft_exceptions=pd.concat([eft_without_sign_debit,eft_without_sign_credit,missing_balances])
    eft_exceptions=eft_exceptions.drop_duplicates()
    eft_exceptions['report_date']=today
    
    
    # if eft_exceptions.shape[0]>0:
    #     eft_exceptions.to_sql("eft Exceptions", con=engine, if_exists="replace")

    
    print(len(eft), 'eft total transactions')
    print(len(eft_exceptions), 'eft total transactions exception')
    
    return eft
    
    
def createTransactionus_on_us(ACF2,customers, branch,balances,signatory,industry):
    import datetime

    transaction_lista=[]
    trans_1=None
    for index, row in ACF2.iterrows():
        director_id=pd.DataFrame()
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.ft_rec
        transaction.internal_ref_number=trans_1.ft_rec
        
        transaction.transaction_type='TTM3'
        transaction.transaction_description='Transações com cartão de débito'#trans_1.ft_debit_their_ref
        pref=trans_1.branch[:3]
        transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1.ft_data_transacao
        # transaction.teller=trans_1.INPUTTER
        # transaction.authorized=trans_1.AUTHORISER
        transaction.value_date=trans_1.ft_data_transacao
        transaction.transmode_code='TMM4'
        
        #remove tag 
        # 
        transaction.amount_local=str(trans_1.ft_Amount_debited)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        #remove tag 
        # 
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['ft_debit_acct_no'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
        
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=str(bal['NIB'].values[0])
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        
        if str(customer['cus_target'].values[0])[:2]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
    
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].values[0])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
        
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
    
#here
        

            director_id=signatory[signatory['CUS_N']==str(customer['cus_n'].values[0])]
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
            
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)==2:
                    director.first_name=names[0]
                    director.middle_name=names[1]
                elif len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    director.middle_name=' '.join(names[1:-1])    
                else:
                    director.first_name=names[0]
    
                # director.birthdate=director_data['cus_dob'].iloc[0]
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                    
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
            
            
                phone2=TPhone()
                phone2.tph_contact_type='P'
    
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                director.phones=[phone2]
    # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
     
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            
                phone3=TPhone()
                phone3.tph_contact_type='B'
    

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
            # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                
               
                
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
        
            
                if director is not None:
                    entity.director_id=director
        
        
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

    
    
        director=Person()
        sign=Signatory()
    # director_id=pd.DataFrame()
    
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
    
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.middle_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])
        else:
            director.first_name=names[0]

        
        
        director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    
    
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        # director.phones=[phone2]
    
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # id.comments=str(director_data['id_comment'].iloc[0])
    
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
                
    
        director.identification=id
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
        
        if director is not None:
            sign.t_person=director
        from_account.signatory=sign
    
    
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
    
    
            
        
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
    
    #TO My CLient
    
        ttomy=TToMyClient()
        ttomy.to_funds_code='-'
        # 
        ttoaccountmy=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['outside_bank_acct'])]
        # print(trans_1['outside_bank_acct'])
        ttoaccountmy.institution_name='STANDARD BANK, SA.'
        ttoaccountmy.institution_code='0003'
        ttoaccountmy.institution_country='MZ'
        # print(bal)
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        ttoaccountmy.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        ttoaccountmy.account=bal['NIB'].values[0]
        ttoaccountmy.account_category='ACM1'
        
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        ttoaccountmy.currency_code=bal['dtl_cur'].values[0]
        ttoaccountmy.account_name=customer['cus_full_name'].values[0]
        ttoaccountmy.iban=bal['iban'].values[0]
        
        
        ttoaccountmy.client_number=str(customer['cus_n'].values[0])
        if str(customer['cus_target'].values[0])[:2]=='22':
            ttoaccountmy.account_type='ATM2'
        else:
            ttoaccountmy.account_type='ATM1'
        ttomy.to_account=ttoaccountmy
    # 
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'
# 
            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]
# 
            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'
# 
            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]
# 
            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
        # 
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        # 
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
        
        
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
                # print(director_id)
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
            #     director
            # str(director_data['cus_gender'].iloc[0])
            #     if director_data['cus_gender'].iloc[0]=='M':
            #         director.title='SR'
            #     else:
            #         director.title='SRA'
            # # 
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)==2:
                    director.first_name=names[0]
                    director.middle_name=names[1]
                elif len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    director.middle_name=' '.join(names[1:-1])
                else:
                    director.first_name=names[0]

                # 
                # director.birthdate=director_data['cus_dob'].iloc[0]
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
            # 
            # 
                phone2=TPhone()
                phone2.tph_contact_type='P'
    # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                # director.phones=[phone2]
    # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
    #  
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            # 
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            # 
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            # 
                phone3=TPhone()
                phone3.tph_contact_type='B'
    # 
# 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            # 
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
            # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
        # 
            # # 
            #     if director is not None:
            #         entity.director_id=director
        # 
        # 
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                ttoaccountmy.t_entity=entity    
# 
    # 
    # 
        director=Person()
        sign=Signatory()
    # 
    
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
        
        else:
            director_data=customer
        # print(director_id)
        
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
        
    #     director.gender=str(director_data['cus_gender'].iloc[0])
    #     if director_data['cus_gender'].iloc[0]=='M':
    #         director.title='SR'
    #     else:
    #         director.title='SRA'
    # # 
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.middle_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])
        
        else:
            director.first_name=names[0]

        # 
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    # 
    # 
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        # director.phones=[phone2]
    # 
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'
# 
        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    # 
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    # 
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    # 
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    # 
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
            
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # id.comments=str(director_data['id_comment'].iloc[0])
    
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.identification=id
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
        # 
        if director is not None:
            sign.t_person=director
    # 
        ttoaccountmy.signatory=sign
    # 
    # 
        ttoaccountmy.opened=bal['DTL_Date_Opened'].iloc[0]
        ttoaccountmy.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        ttoaccountmy.date_balance=bal['CRB_DTE'].iloc[0]
        ttoaccountmy.status_code='AS1'
        ttoaccountmy.beneficiary=customer['cus_full_name'].iloc[0]
    # 
    # 
            # 
        # 
        ttomy.to_country=customer['residence_country'].iloc[0]
    
    

 
    
    
    
    

        transaction.t_to_my_client=ttomy      
    
    
        transaction_lista.append(transaction)
    return transaction_lista


def create_credit_cards(Credit_card_copy_nacional, customers, branch,balances,signatory,industry):
    
    trans_1=None
    bal=None

    transaction_lista=[]
    for index, row in Credit_card_copy_nacional.iterrows():
        trans_1=row
        director_id=pd.DataFrame()
        transaction = Transaction()
        transaction.transactionnumber=trans_1.transaction_number
        transaction.internal_ref_number=trans_1.transaction_number
        transaction.transaction_type='TTM3'
    
        transaction.transaction_description='Transacoes com Cartoes de Credito' #trans_1['t_to/to_account/beneficiary']
        pref='S95'
        transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1.date_transaction
    
        transaction.value_date=trans_1.value_date
        transaction.transmode_code='TMM6'
        
        transaction.amount_local=str(trans_1.amount_local)                                      
        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        # 
        from_account=Account()
        bal=balances[balances.CUSTOMER.astype(str)==str(trans_1.BCM_CARDHOLDER_NBR)]
        # print(trans_1.BCM_CARDHOLDER_NBR)
        # print(bal.shape)
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
    # print(bal['branch'], 'show me this')
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
    # print(pref)
        from_account.branch=branch[(branch['MNEMONIC']==str(pref))]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
    
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
    
    
        if str(customer['cus_target'].values[0])[:2]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
    
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]


            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
        
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
    
#here        
            director_id=signatory[signatory['CUS_N']==str(customer['cus_n'].values[0])]
        # print('================================================')
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
                # director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
            
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                else:
                    director.first_name=names[0]
                    director.last_name=names[1]
                
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                # director.birthdate=director_data['cus_dob'].iloc[0]
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
            
            
                phone2=TPhone()
                phone2.tph_contact_type='P'
            
    
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                # director.phones=[phone2]
    # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
     
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            
                address3=TAddress()
                address3.address_type='P'
                dir_d=director_data['cus_employer_address'].iloc[0]
            
                if dir_d=='None':
                    address3.address=customer['cus_address_1'].values[0]
                else:
                    address3.address=str(director_data['cus_employer_address'].values[0])
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            
                phone3=TPhone()
                phone3.tph_contact_type='B'
    

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
            # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
        
                # if director is not None:
                #     entity.director_id=director
        
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity  


        director=Person()
        sign=Signatory()
    
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer   
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                 
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
    
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]



        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        # director.phones=[phone2]
    
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    
        address3=TAddress()
        address3.address_type='P'
    
        dir_d=director_data['cus_employer_address'].iloc[0]
        if dir_d=='None':
            address3.address=customer['cus_address_1'].values[0]
        else:
            address3.address=str(director_data['cus_employer_address'].values[0])

        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
            
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
        
        if director is not None:
            sign.t_person=director
    
        from_account.signatory=sign
    
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
    
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
    
        tto=TTo()
        tto.to_funds_code='-'
        
    
    
        tto_act=Account()

        tto_act.institution_name=trans_1['t_to/to_account/institution_name']
   
        tto_act.institution_code=str(trans_1['t_to/to_account/institution_code'])
        tto_act.account='-'
        tto_act.institution_country=str(trans_1['t_to/to_country'])
        tto_act.account_name=str(trans_1['t_to/to_account/account_name'])
        tto_entity=TEntity()
        tto_entity.name=str(trans_1['t_to/to_account/account_name'])
        tto_entity.commercial_name=str(trans_1['t_to/to_account/account_name'])
        tto_entity.incorporation_country_code=trans_1['t_to/to_account/t_entity/incorporation_country_code']
        
        tto_act.t_entity=tto_entity
        tto_act.beneficiary=trans_1['t_to/to_account/account_name']
        tto.to_account=tto_act
 
        tto.to_country=trans_1['t_to/to_country']
        
        transaction.t_to=tto
    
        transaction_lista.append(transaction)
    return transaction_lista

def create_us_on_them(ACF2UT_nacionais,customers, branch,balances,signatory,industry):
    trans_1=None
    bal=None
    transaction_lista=[]
    for index, row in ACF2UT_nacionais.iterrows():
        director_id=pd.DataFrame()
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.ft_rec
        transaction.internal_ref_number=trans_1.ft_rec
        transaction.transaction_description='Transações com cartão de débito'#trans_1.ft_debit_their_ref
        transaction.transaction_type='TTM3'
        pref=trans_1.branch[:3]
        transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1.ft_data_transacao
    # transaction.teller=trans_1.INPUTTER
    # transaction.authorized=trans_1.AUTHORISER
        transaction.value_date=trans_1.ft_data_transacao
        transaction.transmode_code='TMM4'
        # 
        transaction.amount_local=str(trans_1.ft_Amount_debited)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['ft_debit_acct_no'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        from_account.account_category='ACM1'
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if str(customer['cus_target'].values[0])[:2]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
    
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
        
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
    
#here
        

            director_id=signatory[signatory['CUS_N']==str(customer['cus_n'].values[0])]
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
                # director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
            
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)==2:
                    director.first_name=names[0]
                    director.middle_name=names[1]
                elif len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    director.middle_name=' '.join(names[1:-1])    
                else:
                    director.first_name=names[0]
    

                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                # director.birthdate=director_data['cus_dob'].iloc[0]
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
            
            
                phone2=TPhone()
                phone2.tph_contact_type='P'
    
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                # director.phones=[phone2]
    # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
     
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            
                phone3=TPhone()
                phone3.tph_contact_type='B'
    

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
            # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
        
            
                # if director is not None:
                #     entity.director_id=director
        
        
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

    
    
        director=Person()
        sign=Signatory()
    # director_id=pd.DataFrame()
    
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'    
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
    
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.middle_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])
        else:
            director.first_name=names[0]

        
        
        
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    
    
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        # director.phones=[phone2]
    
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
        
        if director is not None:
            sign.t_person=director
    
        from_account.signatory=sign
    
    
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
    
    
            
        
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
    
    
        tto=TTo()
        tto.to_funds_code='-'
        
    

       
        tto_act=Account()

        tto_act.institution_name=trans_1['bank_name']
   
        tto_act.institution_code=str(trans_1['bank'])
        tto_act.account=str(trans_1['outside_bank_acct'])
        tto_act.account_name=str(trans_1['ft_debit_their_ref'])
        tto_act.institution_country=trans_1['country_trans']
        tto_entity=TEntity()
        tto_entity.name=str(trans_1['ft_debit_their_ref'])
        tto_entity.commercial_name=str(trans_1['ft_debit_their_ref'])
        if trans_1.Typee=='P24':
            tto_entity.incorporation_country_code='MZ'
        elif trans_1.Typee=='VISA':
            tto_entity.incorporation_country_code=trans_1['country_trans']
        
        tto_act.t_entity=tto_entity
        tto_act.beneficiary=trans_1['ft_debit_their_ref']
        tto.to_account=tto_act
        if trans_1.Typee=='P24':
            tto.to_country='MZ'
        elif trans_1.Typee=='VISA':
            tto.to_country=trans_1['country_trans']
        transaction.t_to=tto
    
        transaction_lista.append(transaction)
    return  transaction_lista


def logConfigurations():
    # Get current date details
    today = datetime.datetime.now()
    logFilename = "Log Cards transactions - "+today.strftime("%Y-%m-%d")+".log"

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        filename=logFilename, level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)


def createTransaction_cash_deposits(cash_deposits,customers, branch,balances,signatory,industry):
    logConfigurations()
    logging.info("Starting Map Cash Deposits...")

    
    trans_1=None
    bal=None
    transaction_lista=[]    
    for index, row in cash_deposits.iterrows():
        trans_1=row
        # transaction_lista=[]
        transaction = Transaction()
    
        transaction.transactionnumber=trans_1.internal_ref_number
        logging.info(str(trans_1.internal_ref_number))
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_description=str(trans_1.transaction_description)
        
        transaction.transaction_type='TTM1'

       
       

        try:
            pref=str(trans_1.internal_ref_number)[:3]
            transaction.transaction_location=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        except IndexError as e:
            logging.info(f"IndexError: {e}")
        
        transaction.date_transaction=trans_1.value_date_2
    # transaction.teller=str(trans_1.INPUTTER)
    # transaction.authorized=str(trans_1.authorized)
        transaction.value_date=trans_1.value_date_2
        transaction.transmode_code='TMM2'
        
        transaction.amount_local=str(trans_1.amount_local_2) 
    
# 
        mine=TFrom()
    
        
        mine.from_funds_code='FTM15'
    # 
    # 
    # breakpoint()
    # if trans_1.CONDUCTOR=='NO': # only report Person 
        mine_person=Person()
        mine_person.gender=trans_1.gender
        name=trans_1.DEPOSITOR
        names=re.findall(r'\S+',name)
        if len(names)>2:
            mine_person.first_name=names[0]
            mine_person.middle_name=' '.join(names[1:-1])
            mine_person.last_name=names[-1]
        elif len(names)==2:
            mine_person.first_name=names[0]
            mine_person.last_name=names[1]
        else:
            mine_person.first_name=names[0]
        
        
        phone3=TPhone()
        mine_person.id_number=trans_1['ID.NUMBER']
        if trans_1['TELEPHONE NUMBER'] is not None:
        # phone3=TPhone()
            phone3.tph_contact_type='B'
            if str(trans_1['TELEPHONE NUMBER'])[:2]=='21':
                phone3.tph_communication_type='L'
            else:
                phone3.tph_communication_type='M'
                
            phone3.tph_number=str(trans_1['TELEPHONE NUMBER'])
        
        id=TPersonIdentification()
        id.type=trans_1['id_type']
        id.number=trans_1['ID.NUMBER']
        
        
        id.issue_country=trans_1['ISSUE.COUNTRY']
        # mine_person.phones=[phone3]
        id.issue_date='2020-01-01T00:00:00'
        mine_person.identification=id
        mine.from_person=mine_person

        enti=Entity()
        ent_name=trans_1['PAYER.NAME']
        enti.name=ent_name
    # mine.from_entity=enti
        # 
        # 
        if pd.isna(trans_1['ISSUE.COUNTRY']):
            mine.from_country='MZ'
        else:    
            mine.from_country=trans_1['ISSUE.COUNTRY']
        
        mine.from_country='MZ'
#   
    
    
    
    #TO My CLient
    
        ttomy=TToMyClient()
        ttomy.to_funds_code='FTM15'
        
        ttoaccountmy=Account()
        bal=balances[(balances['DTL_acct_n']==str(trans_1['account_2'])) & (balances['CUSTOMER']==trans_1['CUSTOMER_2'])]
        ttoaccountmy.institution_name='STANDARD BANK, SA.'
        ttoaccountmy.institution_code='0003'
        ttoaccountmy.institution_country='MZ'
        ttoaccountmy.account_category='ACM1'
        
        print(str(trans_1['account_2']))
        
        
        try:
            pref=bal['branch'][:3].values[0]
            pref=pref[:3]
            ttoaccountmy.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
            
        except IndexError as e:
            logging.info(f"IndexError: {e}")
            continue
        ttoaccountmy.account=bal['NIB'].values[0]
    # 
        try:
            customer=customers[customers['cus_n'].astype(str)==str(bal['CUSTOMER'].values[0])]
            val = customer['cus_full_name'].iloc[0]
            ttoaccountmy.account_name = val
            
        except IndexError as e:
            logging.info(
                "Skipping transaction: no customer rows found for filter criteria. expected customer"+str(bal['CUSTOMER'].values[0],f"IndexError: {e}")
                
            )

            

       
        
        ttoaccountmy.currency_code=bal['dtl_cur'].values[0]
        
        # # if column is missing → skip
        # if 'cus_full_name' not in customer.columns:
        #     logging.info(
        #         "Skipping transaction: column 'cus_full_name' not found. "
        #         "Customer dataframe head:\n%s", customer.head()
        #     )
        #     return None   # skip transaction

        # # if dataframe is empty → skip
        # if customer.empty:
        #     logging.info(
        #         "Skipping transaction: no customer rows found for filter criteria. expected customer"+str(bal['CUSTOMER'].values[0])
                
        #     )
        #     return None   # skip transaction

        # otherwise, safe to take value

        
        # ttoaccountmy.account_name=customer['cus_full_name'].values[0]
        ttoaccountmy.iban=bal['iban'].values[0]
        ttoaccountmy.client_number=str(customer['cus_n'].values[0])
    
        if str(customer['cus_target'].values[0])[:2]=='22':
            ttoaccountmy.account_type='ATM2'
        else:
            ttoaccountmy.account_type='ATM1'
        director_id=pd.DataFrame()
    

    
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=str(customer['cus_full_name'].values[0])
            entity.commercial_name=str(customer['cus_full_name'].values[0])
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].iloc[0])]

            if indu.shape[0]>0:
                entity.business=str(indu['Indu_desc'].values[0])
            else:
                entity.business=' '
            
            phone1=TPhone()
            if customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'
        # 
        
# 
            if str(customer['cus_tel_no1'].values[0])[:2]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=str(customer['cus_tel_no1'].values[0])
            phone_n=customer['cus_tel_no1'].iloc[0]
            #recently
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            entity.phones=[phone1]
        # 
        
# 
            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=str(customer['cus_address_1'].values[0])
            address1.city=str(customer['cus_town'].values[0])
            address1.country_code=str(customer['residence_country'].values[0])
            if address1 is not None:
                entity.addresses=[address1]
# 
            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=str(email)
        
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=str(customer['residence_country'].values[0])
        
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
        
            if director_id.shape[0]>0:
                
                
                    
                director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
                if not director_data.empty:
                    gender = str(director_data['cus_gender'].iloc[0])
                else:
                    print('director id',director_id.shape[0])
                    gender = "-"  # Or any default value

                if pd.isna(gender)==False:
                    print('has values',director_id['cus_n_rel'].values[0])
                    director.gender=gender
                    
                # gender=str(director_data['cus_gender'].iloc[0])
                if pd.isna(gender)==False:
                    director.gender=gender
                    # str(director_data['cus_gender'].iloc[0])
                    if gender=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'

            #     director.gender=str(director_data['cus_gender'].iloc[0])
            #     if director_data['cus_gender'].iloc[0]=='M':
            #         director.title='SR'
            #     else:
            #         director.title='SRA'
            # # 
            
                try:
                   
                    director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'])]
                
                except IndexError as e:
                    logging.info(f" Not working this thing{e}")
                    continue
                
                
                
                if 'cus_full_name' not in director_data.columns:
                    logging.info(
                    "Skipping transaction: column 'cus_full_name' not found. "
                    "Customer dataframe head:\n%s", director_data.head()
                )
                    return None   # skip transaction

                # if dataframe is empty → skip
                if director_data.empty:
                    logging.info(
                        "Skipping transaction: no customer rows found for filter criteria. expected customer "+str(director_id['cus_n_rel'].values[0])

                    )
                    return None   # skip transaction

                # otherwise, safe to take value
                name = director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=str(names[0])
                    director.last=str(names[-1])
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=str(names[0])
                    director.last_name=str(names[1])
                # 
                director.birthdate=str(director_data['cus_dob'].iloc[0])
                director.birth_place=str(director_data['CUS_Place_Birth'].iloc[0])
                director.nationality1=str(director_data['cus_nationality'].iloc[0])
                director.residence=str(director_data['residence_country'].iloc[0])
            
            
                phone2=TPhone()
                phone2.tph_contact_type='P'
    # 
                if str(director_data['cus_tel_no1'].iloc[0])[:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=str(director_data['cus_tel_no1'].iloc[0])
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                director.phones=[phone2]
    # 
                target=str(director_data['cus_target'].iloc[:2])
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
    #  
                address2.address=str(director_data['cus_address_1'].values[0])
                if str(director_data['cus_town'].values[0])!='':
                    address2.city=str(director_data['cus_town'].values[0])
                else:
                    address2.city='-'
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            # 
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                if str(director_data['cus_town'].values[0])!='':
                    address3.city=str(director_data['cus_town'].values[0])
                else:
                    address3.city='-'
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            
                phone3=TPhone()
                phone3.tph_contact_type='B'
    

                if str(director_data['cus_tel_no1'].iloc[0])[:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=str(director_data['cus_tel_no1'].iloc[0])
                
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            # 
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
          
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                    
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=str(email)
        
            # 
                # if director is not None:
                #     entity.director_id=director
        
            # 
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)

                entity.tax_number=customer['cus_nuit'].astype(str).iloc[0]
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
          
                ttoaccountmy.t_entity=entity
                

    
    # 
        director=Person()
        sign=Signatory()
    # 
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
        else:
        
            director_data=customer
    
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
    # 
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
        # 
        
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
            
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    # 
    # 
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if str(director_data['cus_tel_no1'].iloc[0])[:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=str(director_data['cus_tel_no1'].iloc[0])
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        director.phones=[phone2]
    
        target=str(director_data['cus_target'].iloc[:2])
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'
# 
        address2.address=director_data['cus_address_1'].values[0]
        if str(director_data['cus_town'].values[0])!='':
            address2.city=str(director_data['cus_town'].values[0])
        else:
            address2.city='-'
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    # 
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    # 
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    # 
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if str(director_data['cus_tel_no1'].iloc[0])[:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=str(director_data['cus_tel_no1'].iloc[0])
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    # 
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # 
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=str(email)
        # 
        if director is not None:
            sign.t_person=director
    # 
        ttoaccountmy.signatory=sign
    
        ttoaccountmy.opened=bal['DTL_Date_Opened'].iloc[0]
        ttoaccountmy.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        ttoaccountmy.date_balance=bal['CRB_DTE'].iloc[0]
        ttoaccountmy.status_code='AS1'
        ttoaccountmy.beneficiary=str(customer['cus_full_name'].iloc[0])
    # 
    # 
            # 
        # 
        ttomy.to_country=str(customer['residence_country'].iloc[0])
    # 
        ttomy.to_account=ttoaccountmy
 
    # pdb.set_trace()
    
    # adding parties to transaction
        transaction.t_from=mine
        transaction.t_to_my_client=ttomy
        transaction_lista.append(transaction)
    return transaction_lista    

def its_holiday(dia):
    import datetime

# %%
# lista de holidays em Moçambique para 2023
    holidays = [
    datetime.date(2025, 1, 1),  # Dia da Paz e Reconciliação
    datetime.date(2025, 2, 3),  # Dia dos Heróis Moçambicanos
    datetime.date(2025, 4, 7),  # Dia da Mulher Moçambicana
    datetime.date(2025, 5, 1),  # Dia do Trabalhador
    datetime.date(2025, 6, 25),  # Dia da Independência Nacional
    datetime.date(2025, 9, 7),  # Dia da Vitória
    datetime.date(2025, 9, 25),  # Dia das Forças Armadas de Libertação Nacional
    datetime.date(2025, 10, 4),  # Dia da Paz e da Reconciliação
    datetime.date(2025, 12, 25),  # Dia de Natal
]



# %%
    return dia in holidays

def report_date_day():
    import datetime

    hoje=datetime.date.today()
    # hoje=datetime.date(2024, 8, 16)
    # hoje=datetime.date(2024, 7, 12)
    todays_date=hoje
    if (todays_date-datetime.timedelta(days=1)).weekday()==6: #segunda feira
        if its_holiday(todays_date-datetime.timedelta(days=3)):
            report_date=todays_date-datetime.timedelta(days=4)
            # return report_date,'='
            return report_date,'='+"'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=4)):
            report_date=todays_date-datetime.timedelta(days=4)
            report_date1=todays_date-datetime.timedelta(days=3)
            return report_date1,' between '+"'"+str(report_date)+"'"+' and '+"'"+str(report_date1)+"'"
            # return todays_date-datetime.timedelta(days=4),'and following day, i must review the query and accomodate this scenario'
        else:
            report_date=todays_date-datetime.timedelta(days=3)
            # return todays_date-datetime.timedelta(days=3),'='
            return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==1:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=4)
            # return todays_date-datetime.timedelta(days=4),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:
            if its_holiday(todays_date-datetime.timedelta(days=4)):
                report_date=todays_date-datetime.timedelta(days=4)
                # return todays_date-datetime.timedelta(days=4),'>='
                return report_date,'>= '+"'"+str(report_date)+"'"
            else:
                report_date=todays_date-datetime.timedelta(days=1)
                # return todays_date-datetime.timedelta(days=3),'>='
                return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==2:
        if its_holiday(todays_date-datetime.timedelta(days=2)):
            report_date=todays_date-datetime.timedelta(days=4)
            
            # return todays_date-datetime.timedelta(days=4),'>='
            return report_date,'>='+ "'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:    
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='
            return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==3:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        
    elif todays_date.weekday()==4:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=2)):
            report_date=todays_date-datetime.timedelta(days=2)
            report_date1=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=2),'and following day, i must review the query and accomodate this scenario'
            return report_date1, ' between '+"'"+str(report_date)+"'"+' and '+"'"+str(report_date1)+"'"
        else:
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='            
            return report_date,'= '+"'"+str(report_date)+"'"

def safe_str_field(obj, field, default=""):
    """
    Return a safe string for obj[field] (obj can be Series or dict-like).
    Returns default if missing/NaN/None.
    """
    try:
        val = obj.get(field) if hasattr(obj, "get") else getattr(obj, field, None)
        if pd.isna(val) or val is None:
            return default
        return str(val)
    except Exception:
        logging.exception("safe_str_field failed for field=%s", field)
        return default

def createTransaction_Pagamentos(pagamentos_copy,customers, branch,balances,signatory,industry):
    
    trans_1=None
    bal=None
    transaction_lista=[]
    for index, row in pagamentos_copy.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.internal_ref_number
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_description=str(trans_1.transaction_description)
        
        transaction.transaction_type='TTM2'
        pref=str(trans_1.internal_ref_number[:3])
        # print('transaction ID', trans_1.internal_ref_number)
        # print('branch pagamentos',pref)
        transaction.transaction_location=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        transaction.date_transaction=trans_1.value_date_2
        # transaction.teller=str(trans_1.INPUTTER)
        # transaction.authorized=str(trans_1.authorized)
        transaction.value_date=trans_1.value_date_2
        transaction.transmode_code='TMM2'
        
        transaction.amount_local=str(trans_1.amount_local_2) 
        
        tfrom=TFromMyClient()
        tfrom.from_funds_code='FTM15'
        
        from_account=Account()
        bal=balances[balances.DTL_acct_n==str(trans_1.account_2)]
        
        # print(trans_1.account_2,'Contas')
        # print(bal,'balance')
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
        
        # print(trans_1.ft_debit_acct_no)
        # print(pref)
        # pref=bal['branch'][:3].values[0]
        # pref=pref[:3]
        # print(pref)
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==str(bal['CUSTOMER'].values[0])]
        from_account.currency_code=bal['dtl_cur'].values[0]
        
        
        if 'cus_full_name' not in customer.columns:
            logging.info(
                "Skipping transaction: column 'cus_full_name' not found. "
                "Customer dataframe head:\n%s", customer.head()
            )
            return None   # skip transaction

        # if dataframe is empty → skip
        if customer.empty:
            logging.info(
                "Skipping transaction: no customer rows found for filter criteria. expected customer"+str(bal['CUSTOMER'].values[0])
                
            )
            return None   # skip transaction

        # otherwise, safe to take value
        val = customer['cus_full_name'].iloc[0]
        from_account.account_name = str(val).strip() if pd.notna(val) else "UNKNOWN"
        from_account.account_name=customer['cus_full_name'].values[0]
        
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'].astype(str).str[:2].values[0]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
        
        director_id=pd.DataFrame()

            
        if customer['cus_type'].values[0]=='E':
            

            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        
    #here
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            # print('dados',customer['cus_n'],'cus_n')
            # if customer['cus_n'].values[0]=='220857':
                # print('shape start')
                # print(customer['cus_type'].values[0])
                # print(customer['cus_type'].values[0]=='E')
                # print(customer['cus_n'].values[0])
                # print(director_id)
                # print('shape end')
            if director_id.shape[0]>0:
                

                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                if 'cus_gender' not in director_data.columns:
                    logging.info(
                        "Skipping transaction: column 'cus_gender' not found. "
                        "Customer dataframe head:\n%s", director_data.head()
                    )
                    return None   # skip transaction

                # if dataframe is empty → skip
                if director_data.empty:
                    logging.info(
                        "Skipping transaction: no gender rows found for filter criteria. expected customer"

                    )
                    return None   # skip transaction
                
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                if director_data['cus_gender'].iloc[0]=='M':
                    director.title='SR'
                else:
                    director.title='SRA'
                
                # director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
                
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    
                # director.birthdate=director_data['cus_dob'].iloc[0]
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                
                
                phone2=TPhone()
                phone2.tph_contact_type='P'
                
        
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                
                address3=TAddress()
                address3.address_type='P'
                dir_d=director_data['cus_employer_address'].iloc[0]
                
                if dir_d=='None':
                    address3.address=customer['cus_address_1'].values[0]
                else:
                    address3.address=str(director_data['cus_employer_address'].values[0])
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                
                phone3=TPhone()
                phone3.tph_contact_type='B'
        

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
                
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
                
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            
                
                # if director is not None:
                #     entity.director_id=director
            
            
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

        
        
        
        director=Person()
        sign=Signatory()
        
        
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer    
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
        
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
            
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        director.phones=[phone2]
        
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        
        address3=TAddress()
        address3.address_type='P'
        
        dir_d=director_data['cus_employer_address'].iloc[0]
        if dir_d=='None':
            address3.address=customer['cus_address_1'].values[0]
        else:
            address3.address=str(director_data['cus_employer_address'].values[0])

        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
        
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
            
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            
        if director is not None:
            sign.t_person=director
        
        from_account.signatory=sign
        
        
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
        
        
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
        
        
        mine=TTo()
        
        mine.to_funds_code='FTM15'
        
        

        
        mine_person=Person()

        if pd.notna(trans_1.SEX):
            mine_person.gender=trans_1.SEX[:1]
        else:
            mine_person.gender='U'
        
        name = safe_str_field(trans_1, 'DEPOSITOR', default="")
        names=re.findall(r'\S+',name)
        if len(names)>2:
            mine_person.first_name=names[0]
            mine_person.last_name=names[-1]
            mine_person.middle_name=' '.join(names[-1])
        elif len(names)==2:
            mine_person.first_name=names[0]
            mine_person.last_name=names[-1]
        mine_person.id_number=trans_1['ID.NUMBER']
        if trans_1['TELEPHONE NUMBER'] is not None:
            phone3=TPhone()
            phone3.tph_contact_type='B'
            if str(trans_1['TELEPHONE NUMBER'])[:2]=='21':
                phone3.tph_communication_type='L'
            else:
                phone3.tph_communication_type='M'
                
            phone3.tph_number=trans_1['TELEPHONE NUMBER']
        
        
        id=TPersonIdentification()
        
        if trans_1['ID.TYPE']==2:
            ID_TYPE= 'B'
        elif trans_1['ID.TYPE']==1:
            ID_TYPE='C'
        elif trans_1['ID.TYPE']==11:
            ID_TYPE='A'
        else:
            ID_TYPE='-'
        id.type=ID_TYPE
        id.number=trans_1['ID.NUMBER']
        id.issue_country=trans_1['ISSUE.COUNTRY']
        id.issue_date='2020-01-01T00:00:00'
        # mine_person.phones=[phone3]
        mine_person.identification=id
        mine.to_person=mine_person

            
        if pd.isna(trans_1['ISSUE.COUNTRY']):
            mine.to_country='MZ'
            
        else:    
            mine.to_country=trans_1['ISSUE.COUNTRY']
            
        mine.to_country='MZ'
    #   
        transaction.t_to=mine
        
        transaction.t_from_my_client=tfrom
        transaction_lista.append(transaction)
    print('Finished Pagamentos')
    return transaction_lista


def createTransaction_levantamento(levantamento_de_cheques,customers, branch,balances,signatory,industry):
    
    transaction_lista=[]
    trans_1=None
    for index, row in levantamento_de_cheques.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.internal_ref_number
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_description=str(trans_1.transaction_description)
        
        transaction.transaction_type='TTM2'
        pref=str(trans_1.internal_ref_number[:3])

        transaction.transaction_location=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        transaction.date_transaction=trans_1.value_date_2
        # transaction.teller=str(trans_1.INPUTTER)
        # transaction.authorized=str(trans_1.authorized)
        transaction.value_date=trans_1.value_date_2
        transaction.transmode_code='TMM2'
        
        transaction.amount_local=str(trans_1.amount_local_2) 
        
        tfrom=TFromMyClient()
        tfrom.from_funds_code='FTM15'
        
        from_account=Account()
        bal=balances[balances.DTL_acct_n==str(trans_1.account_2)]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        
        # print(trans_1.ft_debit_acct_no)
        # print(pref)
        # pref=bal['branch'][:3].values[0]
        # pref=pref[:3]
        # print(pref)
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account_category='ACM1'
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==str(bal['CUSTOMER'].values[0])]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'].astype(str).str[:2].values[0]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
        director_id=pd.DataFrame()
        
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        
    #here
            

            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            # print('dados',customer['cus_n'],'cus_n')
            if director_id.shape[0]>0:
                
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                    
                #     director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
                
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                else:
                    director.first_name=names[0]
                    
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                # director.birthdate=director_data['cus_dob'].iloc[0]
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                
                
                phone2=TPhone()
                phone2.tph_contact_type='P'
                
        
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                
                address3=TAddress()
                address3.address_type='P'
                dir_d=director_data['cus_employer_address'].iloc[0]
                
                if dir_d=='None':
                    address3.address=customer['cus_address_1'].values[0]
                else:
                    address3.address=str(director_data['cus_employer_address'].values[0])
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                
                phone3=TPhone()
                phone3.tph_contact_type='B'
        

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
                
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            
                
                # if director is not None:
                #     entity.director_id=director
            
            
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

        
        
        
        director=Person()
        sign=Signatory()
        
        
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
        
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                        
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
        
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[0]
            
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
            
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        director.phones=[phone2]
        
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        
        address3=TAddress()
        address3.address_type='P'
        
        dir_d=director_data['cus_employer_address'].iloc[0]
        if dir_d=='None':
            address3.address=customer['cus_address_1'].values[0]
        else:
            address3.address=str(director_data['cus_employer_address'].values[0])

        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        director.employer_phone_id=phone3
        
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            
        if director is not None:
            sign.t_person=director
        
        from_account.signatory=sign
        
        
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
        
        
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
        
        
        mine=TTo()
        
        mine.to_funds_code='FTM15'
        
        

        
        mine_person=Person()
        mine_person.gender=trans_1.SEX[:1]
        name=trans_1.DEPOSITOR
        names=re.findall(r'\S+',name)
        if len(names)>2:
            mine_person.first_name=names[0]
            mine_person.last_name=names[-1]
            mine_person.middle_name=' '.join(names[-1])
        elif len(names)==2:
            mine_person.first_name=names[0]
            mine_person.last_name=names[-1]
        mine_person.id_number=trans_1['ID.NUMBER']
        if trans_1['TELEPHONE NUMBER'] is not None:
            phone3=TPhone()
            phone3.tph_contact_type='B'
            if str(trans_1['TELEPHONE NUMBER'])[:2]=='21':
                phone3.tph_communication_type='L'
            else:
                phone3.tph_communication_type='M'
                
            phone3.tph_number=trans_1['TELEPHONE NUMBER']
        
        
        id=TPersonIdentification()
        
        if trans_1['ID.TYPE']==2:
            ID_TYPE= 'B'
        elif trans_1['ID.TYPE']==1:
            ID_TYPE='C'
        elif trans_1['ID.TYPE']==11:
            ID_TYPE='A'
        else:
            ID_TYPE='-'
        id.type=ID_TYPE
        id.number=trans_1['ID.NUMBER']
        id.issue_country=trans_1['ISSUE.COUNTRY']
        # mine_person.phones=[phone3]
        mine_person.identification=id
        mine.to_person=mine_person

            
        if pd.isna(trans_1['ISSUE.COUNTRY']):
            mine.to_country='MZ'
        else:    
            mine.to_country=trans_1['ISSUE.COUNTRY']
            
        mine.to_country='MZ'
    #   
        transaction.t_to=mine
        
        transaction.t_from_my_client=tfrom
        transaction_lista.append(transaction)
    print('Finished Levantamentos')
    return transaction_lista


def create_us_on_them_cheques(us_on_them,customers, branch,balances,signatory,industry):
    trans_1=None
    bal=None
    transaction_lista=[]
    for index, row in us_on_them.iterrows():
        director_id=pd.DataFrame()
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1['Item Reference']
        transaction.internal_ref_number=trans_1['Item Reference']
        
        transaction.transaction_type='TTM1'
        transaction.transaction_description='Cheques Us on Them' 
        #trans_1.ft_debit_their_ref
        # pref=trans_1.branch[:3]
        # transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1['Value date']
        #trans_1.ft_data_transacao
    # transaction.teller=trans_1.INPUTTER
    # transaction.authorized=trans_1.AUTHORISER
        transaction.value_date=trans_1['Value date']
        transaction.transmode_code='TMM2'
        
        transaction.amount_local=str(trans_1.Amount	)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='FTM15'
        
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['Sender Account'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if str(customer['cus_target'].values[0])[:2]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
    
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==str(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
        
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
    
#here
        

            director_id=signatory[signatory['CUS_N']==str(customer['cus_n'].values[0])]
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                if director_data['cus_gender'].iloc[0]=='M':
                    director.title='SR'
                else:
                    director.title='SRA'
                
                # director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
            
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)==2:
                    director.first_name=names[0]
                    director.middle_name=names[1]
                elif len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    director.middle_name=' '.join(names[1:-1])    
                else:
                    director.first_name=names[0]
    
    
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                # director.birthdate=director_data['cus_dob'].iloc[0]
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
            
            
                phone2=TPhone()
                phone2.tph_contact_type='P'
    
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
                director.phones=[phone2]
    # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
     
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
            
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
            
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
            
                phone3=TPhone()
                phone3.tph_contact_type='B'
    

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
            
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
            # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
        
            
                # if director is not None:
                #     entity.director_id=director
        
        
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

    
    
        director=Person()
        sign=Signatory()
    # director_id=pd.DataFrame()
    
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
    
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.middle_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])
        else:
            director.first_name=names[0]

        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
    
    
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        director.phones=[phone2]
    
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
    
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
    
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
    
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
    
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] is not None:
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
    # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
        
        if director is not None:
            sign.t_person=director
    
        from_account.signatory=sign
    
    
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
    
    
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
    
    
        tto=TTo()
        tto.to_funds_code='FTM15'
        
    

       
        tto_act=Account()

        tto_act.institution_name=trans_1['INSTITUTION_NAME']
        tto_act.institution_country='MZ'
        tto_act.institution_country='MZ'
        tto_act.institution_code=str(trans_1['Receiver'])
        tto_act.account=str(trans_1['Receiver Account'])
        tto_act.account_name=str(trans_1['Receiver Name'])
        tto_act.beneficiary=trans_1['Receiver Name']
      
        tto.to_country='MZ'
      
        transaction.t_to=tto
    
        transaction_lista.append(transaction)
    return  transaction_lista

def createTransactionOTT(OT03,customers, branch,balances,signatory,industry,bank):
    transaction_lista=[]
    trans_1=None
    for index, row in OT03.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.transactionnumber
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_type='TTM3'
        transaction.transaction_description=trans_1.transaction_description
        pref=trans_1.PREFIX[:3]
        transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1.processing_date
        
        transaction.value_date=trans_1.credit_value_date
        transaction.transmode_code='TMM4'
        
        transaction.amount_local=str(trans_1.LOC_AMT_DEBITED)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['DEBIT_ACCT_NO'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
        # print(trans_1['DEBIT_ACCT_NO'])
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if str(customer['cus_target'].values[0])[:2]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
        director_id=pd.DataFrame()
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        
    #here
            

            # director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            print(director_id)
            if (director_id.shape[0]>0):
                if pd.isna(director_id['cus_n_rel'].iloc[0])==False:
                    print('-------------start---------')
                    print('cus_n_rel, director id ',director_id['cus_n_rel'])
                    director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                    print('cus_n, customer ', customer['cus_n'])
                    
                    print('cus_gender, director data',director_data['cus_gender'])
                    print('---')
                    
                    gender=str(director_data['cus_gender'].iloc[0])
                    if gender!='nan':
                        director.gender=str(director_data['cus_gender'].iloc[0])
                        if director_data['cus_gender'].iloc[0]=='M':
                            director.title='SR'
                        else:
                            director.title='SRA'
                
                    # director.gender=str(director_data['cus_gender'].iloc[0])
                    # if director_data['cus_gender'].iloc[0]=='M':
                    #     director.title='SR'
                    # else:
                    #     director.title='SRA'

                    name=director_data['cus_full_name'].iloc[0]
                    names=re.findall(r'\S+',name)
                    
                    
                    
                    if len(names)==2:
                        director.first_name=names[0]
                        director.middle_name=names[1]
                    elif len(names)>2:
                        director.first_name=names[0]
                        director.last_name=names[1]
                        director.middle_name=' '.join(names[1:-1])
                        
                    else:
                        director.first_name=names[0]

                    import datetime 
                    dir_birth_date=customer['cus_dob'].iloc[0]
                    if dir_birth_date!='nan':
                        director.birthdate=str(dir_birth_date)
                    else:
                        director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                    
                    # director.birthdate=director_data['cus_dob'].iloc[0]
                    director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                    director.nationality1=director_data['cus_nationality'].iloc[0]
                    director.residence=director_data['residence_country'].iloc[0]


                    phone2=TPhone()
                    phone2.tph_contact_type='P'

                    if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                        phone2.tph_communication_type='L'
                    else:
                        phone2.tph_communication_type='M'
                    phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                    phone_n=director_data['cus_tel_no1'].iloc[0]
                    if pd.isnull(phone_n)==False:
                        director.phones=[phone2]
                    director.phones=[phone2]
        #   
                    target=director_data['cus_target'].iloc[:2]
                    address2=TAddress()
                    if str(target)[:2]!='22':    
                        address2.address_type='B'
                    else:
                        address2.address_type='P'

                    address2.address=director_data['cus_address_1'].values[0]
                    address2.city=str(director_data['cus_town'].values[0])
                    address2.country_code=str(director_data['residence_country'].values[0])
                    if address2 is not None:
                        director.addresses=[address2]

                    director.occupation=str(director_data['Cus_occupation'].iloc[0])
                    director.employer_name=str(director_data['cus_employer_name'].iloc[0])

                    address3=TAddress()
                    address3.address_type='P'
                    address3.address=str(director_data['cus_employer_address'].values[0])
                    address3.city=str(director_data['cus_town'].values[0])
                    address3.country_code=str(director_data['residence_country'].values[0])
                    if address3 is not None:
                        director.employer_address_id=address3

                    phone3=TPhone()
                    phone3.tph_contact_type='B'


                    if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                        phone3.tph_communication_type='L'
                    else:
                        phone3.tph_communication_type='M'
                    phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                    phone_n=director_data['cus_tel_no1'].iloc[0]
                    if pd.isnull(phone_n)==False:
                        director.employer_phone_id=phone3
                    # director.employer_phone_id=phone3

                    id=TPersonIdentification()
                    id.type=director_data['id_type'].iloc[0]
                    id.number=director_data['CUS_ID_N'].iloc[0]
                    
                    if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                        id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                    if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                        id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                    
                    
                    id.issue_country=str(director_data['cus_country_c'].iloc[0])
                    # id.comments=str(director_data['id_comment'].iloc[0])
                    director.identification=id
                    if str(director_data['Cus_PEP'].iloc[0])=='Y':
                        pep=Pep()
                        pep.pep_country='MZ'
                        pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                        pep.function_description=str(director_data['PROF_desc'].iloc[0])
                        director.peps=pep
                    director.tax_number=str(director_data['cus_nuit'].iloc[0])
                    director.tax_reg_number=str(director_data['client_number'].iloc[0])
                    email=str(director_data['cus_email_1_1'].iloc[0])
                    if is_valid_email(email):
                        director.email=email


                    # if director is not None:
                    #     entity.director_id=director


                    incorp_date=customer['cus_dob'].iloc[0]
                    if incorp_date!='nan':
                        entity.incorporation_date=str(incorp_date)
                    entity.tax_number=str(customer['cus_nuit'].iloc[0])
                    entity.tax_reg_number=str(customer['client_number'].iloc[0])
                    from_account.t_entity=entity    

        
        
        director=Person()
        sign=Signatory()
        
        if director_id.shape[0]>0 and pd.isna(director_id['cus_n_rel'].iloc[0])==False:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
        
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])
            
        else:
            director.first_name=names[0]

        
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00').join('T00:00:00')
                    
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        director.phones=[phone2]
        
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # director.employer_phone_id=phone3
        
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            
        if director is not None:
            sign.t_person=director
        
        from_account.signatory=sign
        
        
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
        
        
                
            
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
        
        
        tto=TTo()
        tto.to_funds_code='-'
        
        fc=TForeinCurrency()
        fc.foreign_currency_code=str(trans_1['base_currency'])
        if pd.isna(trans_1['foreign_amount']):
            fc.foreign_amount=str(trans_1.LOC_AMT_DEBITED/trans_1['customer_rate'])
        else:
            fc.foreign_amount=str(trans_1['foreign_amount'])
        fc.foreign_exchange_rate=str(round(trans_1['customer_rate'],2))
        
        tto.to_foreign_currency=fc
        tto_act=Account()
        bank_df=bank[bank['RECID']==trans_1.institution_code]
        if bank_df.shape[0]>0:
            tto_act.institution_name=bank_df['INSTITUTION_NAME'].iloc[0]
        else:
            tto_act.institution_name='bank'

        tto_act.institution_code=trans_1['institution_code']
        tto_act.institution_country=trans_1['BEN_COUNTRY']

        tto_act.account=trans_1['BEN_ACCT_NO']
        tto_act.account_name=trans_1['account_name']
        tto_entity=TEntity()
        tto_entity.name=trans_1['account_name']
        tto_entity.commercial_name=trans_1['account_name']
        tto_entity.incorporation_country_code=trans_1['BEN_COUNTRY']
        tto_act.t_entity=tto_entity
        tto_act.beneficiary=trans_1['account_name']
        tto.to_account=tto_act
        tto.to_country=trans_1['BEN_COUNTRY']
        transaction.t_to=tto
        transaction_lista.append(transaction)
    return transaction_lista
        
        
        
        
def createTransactionITT(ITT_copy,customers, branch,balances,signatory,industry,bank,country):
    transaction_lista=[]
    trans_1=None
    for index, row in ITT_copy.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.transactionnumber
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_type='TTM3'
        transaction.transaction_description=str(trans_1.transaction_description)
        pref=str(trans_1.PREFIX[:3])
        transaction.transaction_location=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        transaction.date_transaction=trans_1.processing_date
        transaction.value_date=trans_1.credit_value_date
        transaction.transmode_code='TMM4'
        
        transaction.amount_local=str(trans_1.LOC_AMT_DEBITED) 
        
        # tfrom_act.beneficiary=trans_1['ordering_customer']
        # tfrom.to_account=tfrom_act
        # tfrom.to_country=trans_1['BEN_COUNTRY']
        mine=TFrom()
        
        mine.from_funds_code='-'
        fc=TForeinCurrency()
        fc.foreign_currency_code=str(trans_1['base_currency'])
        if pd.isna(trans_1['DEBIT_AMOUNT']):
            fc.foreign_amount=str(trans_1.LOC_AMT_DEBITED/trans_1['customer_rate'])
        else:
            fc.foreign_amount=str(trans_1['DEBIT_AMOUNT'])
        if pd.isna(trans_1['customer_rate']):
            fc.foreign_exchange_rate=str(round(trans_1.LOC_AMT_DEBITED/trans_1['DEBIT_AMOUNT'],2))
        else:
            fc.foreign_exchange_rate=str(round(trans_1['customer_rate'],2))
        
        mine_acc=Account()
        banc=bank[bank['RECID']==trans_1.institution_code]
        if banc.shape[0]>0:
            mine_acc.institution_name=str(banc['INSTITUTION_NAME'].iloc[0])
        else:
            mine_acc.institution_name='bank'
        ordering_swif=''
        
        
        if str(trans_1['institution_code']).isnumeric() or trans_1['institution_code'] is None: 
            ordering_swif=trans_1['IN.SWIFT.MSG10'][:13][5:]
            mine_acc.institution_code=str(ordering_swif)
        else:
            ordering_swif=trans_1['institution_code']
            mine_acc.institution_code=str(trans_1['institution_code'])
                        
        
        mine_acc.account=str(trans_1['ordering_account'])
        mine_acc.account_name=str(trans_1['ordering_customer'])
        
        tfrom_entity1=TEntity()
        tfrom_entity1.name=str(trans_1['ordering_customer'])
        tfrom_entity1.commercial_name=trans_1['ordering_customer']
        
        if str(trans_1['ordering_country']).isnumeric() or trans_1['ordering_country'] is None or pd.Series(trans_1['ordering_country']).astype(str).isin(country['CODE_2']).all()==False:
            tfrom_entity1.incorporation_country_code=str(trans_1['IN.SWIFT.MSG10'][:13][5:][4:6])
            mine.from_country=str(trans_1['IN.SWIFT.MSG10'][:13][5:][4:6])
            mine_acc.institution_country=str(trans_1['IN.SWIFT.MSG10'][:13][5:][4:6])
        else:    
            tfrom_entity1.incorporation_country_code=str(trans_1['ordering_country'])
            mine.from_country=str(trans_1['ordering_country'])
            mine_acc.institution_country=str(trans_1['ordering_country'])
    
        if mine.from_country is None:
            mine.from_country=str(trans_1['IN.SWIFT.MSG10'][:13][5:][4:6])
            
        mine_acc.t_entity=tfrom_entity1
        
        mine_acc.beneficiary=str(trans_1['ordering_customer'])
        

    
        
        mine.from_foreign_currency=fc
        mine.from_account=mine_acc
        
        ttomy=TToMyClient()
        ttomy.to_funds_code='-'
        
        ttoaccountmy=Account()
        bal=balances[balances['DTL_acct_n']==trans_1['CREDIT_ACCT_NO']]
        ttoaccountmy.institution_name='STANDARD BANK, SA.'
        ttoaccountmy.institution_code='0003'
        ttoaccountmy.institution_country='MZ'
        ttoaccountmy.account_category='ACM1'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        ttoaccountmy.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        ttoaccountmy.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        ttoaccountmy.currency_code=bal['dtl_cur'].values[0]
        ttoaccountmy.account_name=customer['cus_full_name'].values[0]
        ttoaccountmy.iban=bal['iban'].values[0]
        ttoaccountmy.client_number=str(customer['cus_n'].values[0])
        
        director_id=pd.DataFrame()

        if str(customer['cus_target'].values[0])[:2]=='22':
            ttoaccountmy.account_type='ATM2'
        else:
            ttoaccountmy.account_type='ATM1'
        ttomy.to_account=ttoaccountmy
        # 
        if customer['cus_type'].values[0]=='E':

            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'
    # 
            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            phone_n=customer['cus_tel_no1'].iloc[0]
            if pd.isnull(phone_n)==False:
                entity.phones=[phone1]
            # entity.phones=[phone1]
    # 
            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'
    # 
            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]
    # 
            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            # 
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
            # 
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
               
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
               
                # director.gender=str(director_data['cus_gender'].iloc[0])
                # if director_data['cus_gender'].iloc[0]=='M':
                #     director.title='SR'
                # else:
                #     director.title='SRA'
                # 
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)==2:
                    director.first_name=names[0]
                    director.middle_name=names[1]
                elif len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    director.middle_name=' '.join(names[1:-1])
                    
                else:
                    director.first_name=names[0]

                    # 
                # director.birthdate=director_data['cus_dob'].iloc[0]
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                
                
                if pd.Series(director_data['cus_nationality']).astype(str).isin(country['CODE_2']).all():
                    director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                # 
                # 
                phone2=TPhone()
                phone2.tph_contact_type='P'
        # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        #  
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                # 
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                # 
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                # 
                phone3=TPhone()
                phone3.tph_contact_type='B'
        # 
    # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                phone_n=director_data['cus_tel_no1'].iloc[0]
                if pd.isnull(phone_n)==False:
                    director.employer_phone_id=phone3
                # director.employer_phone_id=phone3
                # 
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                    
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            # 
                # # 
                # if director is not None:
                #     entity.director_id=director
            # 
            # 
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                ttoaccountmy.t_entity=entity    
    # 
        # 
        # 
        director=Person()
        sign=Signatory()
        # 

        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
                
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # if director_data['cus_gender'].iloc[0]=='M':
        #     director.title='SR'
        # else:
        #     director.title='SRA'
        # 
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
        elif len(names)>2:
            director.first_name=names[0]
            director.last_name=names[1]
            director.middle_name=' '.join(names[1:-1])    
        else:
            director.first_name=names[0]

            # 
        dir_birth_date=customer['cus_dob'].iloc[0]
        
        import datetime 
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
       
       
        # director.birthdate=director_data['cus_dob'].iloc[0]
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        # 
        # 
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.phones=[phone2]
        # 
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'
    # 
        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        # 
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        # 
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        # 
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        
        phone_n=director_data['cus_tel_no1'].iloc[0]
        if pd.isnull(phone_n)==False:
            director.employer_phone_id=phone3
        # 
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        
        # id.comments=str(director_data['id_comment'].iloc[0])
        
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            # 
        if director is not None:
            sign.t_person=director
        # 
        ttoaccountmy.signatory=sign
        # 
        # 
        ttoaccountmy.opened=bal['DTL_Date_Opened'].iloc[0]
        ttoaccountmy.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        ttoaccountmy.date_balance=bal['CRB_DTE'].iloc[0]
        ttoaccountmy.status_code='AS1'
        ttoaccountmy.beneficiary=customer['cus_full_name'].iloc[0]
        # 
        # 
                # 
            # 
        ttomy.to_country=customer['residence_country'].iloc[0]
        
        

    
        
        
        
        
        #adding parties to transaction
        transaction.t_from=mine
        transaction.t_to_my_client=ttomy      
        
    
        transaction_lista.append(transaction)
    return transaction_lista

def create_eft(eft_copy,customers, branch,balances,signatory,industry,bank):
    import logging

    logging.basicConfig(level=logging.INFO)
    transaction_lista=[]
    trans_1=None
    for index, row in eft_copy.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.transactionnumber
        transaction.internal_ref_number=trans_1.internal_ref_number
        transaction.transaction_description=trans_1.transaction_description
        transaction.transaction_type='TTM3'
        try:
            pref=trans_1.PREFIX[:3]
            transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        except IndexError as e:
            print(f"IndexError: {e}")
        
        transaction.date_transaction=trans_1.processing_date
        # transaction.teller=trans_1.INPUTTER
        # transaction.authorized=trans_1.AUTHORISER
        transaction.value_date=trans_1.credit_value_date
        transaction.transmode_code='TMM4'
        
        transaction.amount_local=str(trans_1.LOC_AMT_DEBITED)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['DEBIT_ACCT_NO'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        from_account.account_category='ACM1'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'].astype(str).str[:2].values[0]=='22':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
        
        director_id=pd.DataFrame()
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].values[0])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        
    #here
            # print(customer['cus_n'].values[0])
            # print(director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])])
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            
            if director_id.shape[0]>0:
                
                director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
                if director_data.empty:
                    raise Exception('breaking because director data is empty',director_id['cus_n_rel'].values[0],director_id['CUS_N'].values[0],customer['cus_n'].values[0])
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    
                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')    
            
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                
                
                phone2=TPhone()
                phone2.tph_contact_type='P'
        
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                
                phone3=TPhone()
                phone3.tph_contact_type='B'
        

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.employer_phone_id=phone3
                
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
               
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            
                
                # if director is not None:
                #     entity.director_id=director
            
            
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                
                
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

        
        
        director=Person()
        sign=Signatory()
        
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
        # director.gender=str(director_data['cus_gender'].iloc[0])
        # print(director_data.shape)
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
         
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
            
        
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.phones=[phone2]
        
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.employer_phone_id=phone3
        
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            
        if director is not None:
            sign.t_person=director
        
        from_account.signatory=sign
        
        
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
        
        
                
            
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
        
        #TO My CLient
        
        ttomy=TToMyClient()
        ttomy.to_funds_code='-'
        
        ttoaccountmy=Account()
        bal=balances[balances['DTL_acct_n']==str(trans_1['CREDIT_ACCT_NO'])]
        ttoaccountmy.institution_name='STANDARD BANK, SA.'
        ttoaccountmy.institution_code='0003'
        ttoaccountmy.institution_country='MZ'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        ttoaccountmy.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        ttoaccountmy.account=bal['NIB'].values[0]
        ttoaccountmy.account_category='ACM1'
        
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        ttoaccountmy.currency_code=bal['dtl_cur'].values[0]
        ttoaccountmy.account_name=customer['cus_full_name'].values[0]
        ttoaccountmy.iban=bal['iban'].values[0]
        ttoaccountmy.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'].astype(str).str[:2].values[0]=='22':
            ttoaccountmy.account_type='ATM2'
        else:
            ttoaccountmy.account_type='ATM1'
        ttomy.to_account=ttoaccountmy
        # 
        
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].values[0])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'
    # 
            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            entity.phones=[phone1]
    # 
            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'
    # 
            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]
    # 
            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            # 
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
            # 
            # director_id=pd.DataFrame()
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            # if director_id.shape[0]>0:
            #     director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
            
            if director_id.shape[0]>0 or pd.isna(director_id['cus_n_rel'].iloc[0])==False:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
            else:
                director_data=customer
                if director_data.empty:
                    raise Exception('breaking because director data is empty',director_id['cus_n_rel'].values[0],director_id['CUS_N'].values[0],customer['cus_n'].values[0])
                
                    
            # else:
            #     director_data=customer
               
                if director_data.shape[0]>0:
                   print(director_data['cus_gender'].iloc[0])
                else:
                    print(director_id.shape[0], 'shape')
                
                if not director_data.empty:
                    gender = str(director_data['cus_gender'].iloc[0])
                else:
                    gender = "-"  # Or any default value

                # gender=str(director_data['cus_gender'].iloc[0])
                if pd.isna(gender)==False:
                    director.gender=gender
                    if gender=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                # 
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=names[0]
                    director.last_name=names[1]
                    # 

                
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                # 
                # 
                phone2=TPhone()
                phone2.tph_contact_type='P'
        # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        #  
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                # 
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                # 
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                # 
                phone3=TPhone()
                phone3.tph_contact_type='B'
        # 
    # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.employer_phone_id=phone3
                # 
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            # 
                # 
                # if director is not None:
                #     entity.director_id=director
            # 
            # 
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                ttoaccountmy.t_entity=entity    
    # 
        # 
        # 
        director=Person()
        sign=Signatory()
        # 
        # if director_id.shape[0]>0:
        #     director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        # else:
        #     director_data=customer
            
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n'].astype(str)==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        if director_data.empty:
            raise Exception('breaking because director data is empty',director_id['cus_n_rel'].values[0],director_data.shape[0],director_id['CUS_N'].values[0],customer['cus_n'].values[0])
                
        
        # if director_id.shape[0]>0 or pd.isna(director_id['cus_n_rel'].iloc[0])==False:
        #     director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        # else:
        #     director_data=customer
        
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
        
        # 
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
            # 
        
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        # 
        # 
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.phones=[phone2]
        # 
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'
    # 
        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        # 
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        # 
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        # 
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.employer_phone_id=phone3
        # 
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            # 
        if director is not None:
            sign.t_person=director
        # 
        ttoaccountmy.signatory=sign
        # 
        # 
        ttoaccountmy.opened=bal['DTL_Date_Opened'].iloc[0]
        ttoaccountmy.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        ttoaccountmy.date_balance=bal['CRB_DTE'].iloc[0]
        ttoaccountmy.status_code='AS1'
        ttoaccountmy.beneficiary=customer['cus_full_name'].iloc[0]
        # 
        # 
                # 
            # 
        ttomy.to_country=customer['residence_country'].iloc[0]
        
        
        #adding parties to transaction
        # transaction.t_from=mine
        transaction.t_to_my_client=ttomy      
        

        transaction_lista.append(transaction)
    return transaction_lista
             
        
        
        
def create_bol(bol_copy,customers, branch,balances,signatory,industry,bank):
    transaction_lista=[]
    trans_1=None
    for index, row in bol_copy.iterrows():
        trans_1=row
        transaction = Transaction()
        transaction.transactionnumber=trans_1.transactionnumber
        transaction.internal_ref_number=trans_1.transactionnumber
        transaction.transaction_type='TTM3'
        transaction.transaction_description='Fix Transferencia'
        pref=trans_1.branch
        transaction.transaction_location=branch[branch['MNEMONIC']==pref]['Company'].values[0]
        transaction.date_transaction=trans_1.ft_data_transacao
        # transaction.teller=trans_1.INPUTTER
        # transaction.authorized=trans_1.AUTHORISER
        transaction.value_date=trans_1.credit_value_date
        transaction.transmode_code='TMM4'
        
        transaction.amount_local=str(trans_1.ft_Amount_debited)                                      

        tfrom=TFromMyClient()
        tfrom.from_funds_code='-'
        
        from_account=Account()
        bal=balances[balances['DTL_acct_n'].astype(str)==str(trans_1['ft_debit_acct_no'])]
        from_account.institution_name='STANDARD BANK, SA.'
        from_account.institution_code='0003'
        from_account.institution_country='MZ'
        
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        from_account.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        from_account.account=bal['NIB'].values[0]
        from_account.account_category='ACM1'
        customer=pd.DataFrame()
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        from_account.currency_code=bal['dtl_cur'].values[0]
        from_account.account_name=customer['cus_full_name'].values[0]
        from_account.iban=bal['iban'].values[0]
        from_account.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'][:1].values[0]=='2':
            from_account.account_type='ATM2'
        else:
            from_account.account_type='ATM1'
        tfrom.from_account=from_account
        
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].values[0])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'

            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            entity.phones=[phone1]

            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'

            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]

            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
        
    #here
            

            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
               
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                
                
                phone2=TPhone()
                phone2.tph_contact_type='P'
        
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                
                phone3=TPhone()
                phone3.tph_contact_type='B'
        

                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.employer_phone_id=phone3
                
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
               
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            
                
                # if director is not None:
                #     entity.director_id=director
            
            
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)
                
                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                from_account.t_entity=entity    

        
        
        director=Person()
        sign=Signatory()
        
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
        
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
            
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        
        
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.phones=[phone2]
        
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'

        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.employer_phone_id=phone3
        
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            
        if director is not None:
            sign.t_person=director
        
        from_account.signatory=sign
        
        
        from_account.opened=bal['DTL_Date_Opened'].iloc[0]
        from_account.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        from_account.date_balance=bal['CRB_DTE'].iloc[0]
        from_account.status_code='AS1'
        from_account.beneficiary=customer['cus_full_name'].iloc[0]
        
        
                
            
        tfrom.from_country=customer['residence_country'].iloc[0]
        transaction.t_from_my_client=tfrom
        
        #TO My CLient
        
        ttomy=TToMyClient()
        ttomy.to_funds_code='-'
        
        ttoaccountmy=Account()
        bal=balances[balances['DTL_acct_n']==str(trans_1['ft_credit_acct_no'])]
        ttoaccountmy.institution_name='STANDARD BANK, SA.'
        ttoaccountmy.institution_code='0003'
        ttoaccountmy.institution_country='MZ'
        pref=bal['branch'][:3].values[0]
        pref=pref[:3]
        ttoaccountmy.branch=branch[branch['MNEMONIC']==str(pref)]['Company'].values[0]
        ttoaccountmy.account=bal['NIB'].values[0]
        customer=customers[customers['cus_n']==bal['CUSTOMER'].values[0]]
        ttoaccountmy.currency_code=bal['dtl_cur'].values[0]
        ttoaccountmy.account_name=customer['cus_full_name'].values[0]
        ttoaccountmy.iban=bal['iban'].values[0]
        ttoaccountmy.account_category='ACM1'
        ttoaccountmy.client_number=str(customer['cus_n'].values[0])
        if customer['cus_target'][:1].values[0]=='2':
            ttoaccountmy.account_type='ATM2'
        else:
            ttoaccountmy.account_type='ATM1'
        ttomy.to_account=ttoaccountmy
        # 
        if customer['cus_type'].values[0]=='E':
            director=Person()
            entity=TEntity()
            entity.name=customer['cus_full_name'].values[0]
            entity.commercial_name=customer['cus_full_name'].values[0]
            entity.incorporation_number=str(customer['incorporation_number'].values[0])
            indu=industry[industry['indu_c']==int(customer['CUS_Industry'].values[0])]
            if indu.shape[0]>0:
                entity.business=indu['Indu_desc'].values[0]
            else:
                entity.business=' '
            phone1=TPhone()
            if  customer['cus_type'].values[0]=='E':    
                phone1.tph_contact_type='B'
            else:
                phone1.tph_contact_type='P'
    # 
            if customer['cus_tel_no1'][:2].values[0]=='21':
                phone1.tph_communication_type='L'
            else:
                phone1.tph_communication_type='M'
            phone1.tph_number=customer['cus_tel_no1'].values[0]
            entity.phones=[phone1]
    # 
            address1=TAddress()
            if  customer['cus_type'].values[0]=='E':    
                address1.address_type='B'
            else:
                address1.address_type='P'
    # 
            address1.address=customer['cus_address_1'].values[0]
            address1.city=customer['cus_town'].values[0]
            address1.country_code=customer['residence_country'].values[0]
            if address1 is not None:
                entity.addresses=[address1]
    # 
            email=str(customer['cus_email_1_1'].values[0])
            if is_valid_email(email):
                entity.email=email
            # 
            entity.incorporation_state=str(customer['cus_town'].values[0])
            entity.incorporation_country_code=customer['residence_country'].values[0]
            # 
            director_id=signatory[signatory['CUS_N'].astype(str)==str(customer['cus_n'].values[0])]
            if director_id.shape[0]>0:
                director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
                
                gender=str(director_data['cus_gender'].iloc[0])
                if gender!='nan':
                    director.gender=str(director_data['cus_gender'].iloc[0])
                    if director_data['cus_gender'].iloc[0]=='M':
                        director.title='SR'
                    else:
                        director.title='SRA'
                # 
                name=director_data['cus_full_name'].iloc[0]
                names=re.findall(r'\S+',name)
                if len(names)>2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    director.middle_name=' '.join(names[1:-1])
                elif len(names)==2:
                    director.first_name=names[0]
                    director.last_name=names[-1]
                    # 
                import datetime 
                dir_birth_date=customer['cus_dob'].iloc[0]
                if dir_birth_date!='nan':
                    director.birthdate=str(dir_birth_date)
                else:
                    director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
                
                
                director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
                director.nationality1=director_data['cus_nationality'].iloc[0]
                director.residence=director_data['residence_country'].iloc[0]
                # 
                # 
                phone2=TPhone()
                phone2.tph_contact_type='P'
        # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone2.tph_communication_type='L'
                else:
                    phone2.tph_communication_type='M'
                phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.phones=[phone2]
        # 
                target=director_data['cus_target'].iloc[:2]
                address2=TAddress()
                if str(target)[:2]!='22':    
                    address2.address_type='B'
                else:
                    address2.address_type='P'
        #  
                address2.address=director_data['cus_address_1'].values[0]
                address2.city=str(director_data['cus_town'].values[0])
                address2.country_code=str(director_data['residence_country'].values[0])
                if address2 is not None:
                    director.addresses=[address2]
                # 
                director.occupation=str(director_data['Cus_occupation'].iloc[0])
                director.employer_name=str(director_data['cus_employer_name'].iloc[0])
                # 
                address3=TAddress()
                address3.address_type='P'
                address3.address=str(director_data['cus_employer_address'].values[0])
                address3.city=str(director_data['cus_town'].values[0])
                address3.country_code=str(director_data['residence_country'].values[0])
                if address3 is not None:
                    director.employer_address_id=address3
                # 
                phone3=TPhone()
                phone3.tph_contact_type='B'
        # 
    # 
                if director_data['cus_tel_no1'].iloc[0][:2]=='21':
                    phone3.tph_communication_type='L'
                else:
                    phone3.tph_communication_type='M'
                phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
                director.employer_phone_id=phone3
                # 
                id=TPersonIdentification()
                id.type=director_data['id_type'].iloc[0]
                id.number=director_data['CUS_ID_N'].iloc[0]
                
                if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
                    id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
                if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
                    id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
                
               
                id.issue_country=str(director_data['cus_country_c'].iloc[0])
                # id.comments=str(director_data['id_comment'].iloc[0])
                director.identification=id
                if str(director_data['Cus_PEP'].iloc[0])=='Y':
                    pep=Pep()
                    pep.pep_country='MZ'
                    pep.function_name=str(director_data['Cus_occupation'].iloc[0])
                    pep.function_description=str(director_data['PROF_desc'].iloc[0])
                    director.peps=pep
                director.tax_number=str(director_data['cus_nuit'].iloc[0])
                director.tax_reg_number=str(director_data['client_number'].iloc[0])
                email=str(director_data['cus_email_1_1'].iloc[0])
                if is_valid_email(email):
                    director.email=email
            # 
                # 
                # if director is not None:
                #     entity.director_id=director
            # 
            # 
                incorp_date=customer['cus_dob'].iloc[0]
                if incorp_date!='nan':
                    entity.incorporation_date=str(incorp_date)

                entity.tax_number=str(customer['cus_nuit'].iloc[0])
                entity.tax_reg_number=str(customer['client_number'].iloc[0])
                ttoaccountmy.t_entity=entity    
    # 
        # 
        # 
        director=Person()
        sign=Signatory()
        # 
        if director_id.shape[0]>0:
            director_data=customers[customers['cus_n']==str(director_id['cus_n_rel'].values[0])]
        else:
            director_data=customer
            
        gender=str(director_data['cus_gender'].iloc[0])
        if gender!='nan':
            director.gender=str(director_data['cus_gender'].iloc[0])
            if director_data['cus_gender'].iloc[0]=='M':
                director.title='SR'
            else:
                director.title='SRA'
        # 
        name=director_data['cus_full_name'].iloc[0]
        names=re.findall(r'\S+',name)
        if len(names)>2:
            director.first_name=names[0]
            director.last_name=names[-1]
            director.middle_name=' '.join(names[1:-1])
        elif len(names)==2:
            director.first_name=names[0]
            director.last_name=names[1]
            # 
        import datetime 
        dir_birth_date=customer['cus_dob'].iloc[0]
        if dir_birth_date!='nan':
            director.birthdate=str(dir_birth_date)
        else:
            director.birthdate=str(datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d"))+('T00:00:00')
        
        director.birth_place=director_data['CUS_Place_Birth'].iloc[0]
        director.nationality1=director_data['cus_nationality'].iloc[0]
        director.residence=director_data['residence_country'].iloc[0]
        # 
        # 
        phone2=TPhone()
        phone2.tph_contact_type='P'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone2.tph_communication_type='L'
        else:
            phone2.tph_communication_type='M'
        phone2.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.phones=[phone2]
        # 
        target=director_data['cus_target'].iloc[:2]
        address2=TAddress()
        if str(target)[:2]!='22':    
            address2.address_type='B'
        else:
            address2.address_type='P'
    # 
        address2.address=director_data['cus_address_1'].values[0]
        address2.city=str(director_data['cus_town'].values[0])
        address2.country_code=str(director_data['residence_country'].values[0])
        if address2 is not None:
            director.addresses=[address2]
        # 
        director.occupation=str(director_data['Cus_occupation'].iloc[0])
        director.employer_name=str(director_data['cus_employer_name'].iloc[0])
        # 
        address3=TAddress()
        address3.address_type='P'
        address3.address=str(director_data['cus_employer_address'].values[0])
        address3.city=str(director_data['cus_town'].values[0])
        address3.country_code=str(director_data['residence_country'].values[0])
        if address3 is not None:
            director.employer_address_id=address3
        # 
        phone3=TPhone()
        phone3.tph_contact_type='B'
        if director_data['cus_tel_no1'].iloc[0][:2]=='21':
            phone3.tph_communication_type='L'
        else:
            phone3.tph_communication_type='M'
        phone3.tph_number=director_data['cus_tel_no1'].iloc[0]
        director.employer_phone_id=phone3
        # 
        id=TPersonIdentification()
        id.type=director_data['id_type'].iloc[0]
        id.number=director_data['CUS_ID_N'].iloc[0]
        
        if director_data['cus_legal_doc_issue_dte'].iloc[0] !='nan':
            id.issue_date=director_data['cus_legal_doc_issue_dte'].iloc[0]
        if director_data['cus_legal_doc_exp_dte'].iloc[0] !='nan':
            id.expiry_date=director_data['cus_legal_doc_exp_dte'].iloc[0]
        
        id.issue_country=str(director_data['cus_country_c'].iloc[0])
        # id.comments=str(director_data['id_comment'].iloc[0])
        director.identification=id
        if str(director_data['Cus_PEP'].iloc[0])=='Y':
            pep=Pep()
            pep.pep_country='MZ'
            pep.function_name=str(director_data['Cus_occupation'].iloc[0])
            pep.function_description=str(director_data['PROF_desc'].iloc[0])
            director.peps=pep
        director.tax_number=str(director_data['cus_nuit'].iloc[0])
        director.tax_reg_number=str(director_data['client_number'].iloc[0])
        email=str(director_data['cus_email_1_1'].iloc[0])
        if is_valid_email(email):
            director.email=email
            # 
        if director is not None:
            sign.t_person=director
        # 
        ttoaccountmy.signatory=sign
        # 
        # 
        ttoaccountmy.opened=bal['DTL_Date_Opened'].iloc[0]
        ttoaccountmy.balance=str(bal['CRB_Balance_LCY'].iloc[0])
        ttoaccountmy.date_balance=bal['CRB_DTE'].iloc[0]
        ttoaccountmy.status_code='AS1'
        ttoaccountmy.beneficiary=customer['cus_full_name'].iloc[0]
        # 
        # 
                # 
            # 
        ttomy.to_country=customer['residence_country'].iloc[0]
        
        

    
        
        
        
        
        #adding parties to transaction
        # transaction.t_from=mine
        transaction.t_to_my_client=ttomy      
        
        
        transaction_lista.append(transaction)
    return transaction_lista



        
 




def create_dir():
    today,operator=report_date_day()
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Daily Structured"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')
        
def create_dir_single(today):
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Cards Single Transactions Reports"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')


def create_dir_month(hoje):
    today,operator=report_date_month(hoje)
    subdir="\\"+str(today.strftime("%Y%m%d"))
    # path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Monthly Structured"
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Cards Single Transactions Reports"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')
        

def create_dir_month_structured(hoje):
    today,operator=report_date_month(hoje)
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Monthly Structured"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')


def create_dir_weekly_structured(hoje):
    today,operator=report_date_Week(hoje)
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Weekly Structured"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')

def create_dir_day_structured(hoje):
    today,operator=report_date_day(hoje)
    subdir="\\"+str(today.strftime("%Y%m%d"))
    path=r"\\10.245.10.81\shared directory\Direccao de Gestao de Risco\Departamento de Compliance\Geral\002 AML & KYC\002 AML MOZ\GIFiM\Structured Transactions Reported\Daily Structured"
    finalpath=path+subdir
    if not os.path.exists(finalpath):
        os.mkdir(finalpath)
        print('created')
    else:
        print('the path  already exists')
        


def report_date_day(hoje):
    # import datetime

    # hoje=datetime.date.today()
    # hoje=datetime.date(2024, 8, 16)
    # hoje=datetime.date(2024, 7, 12)
    todays_date=hoje
    if (todays_date-datetime.timedelta(days=1)).weekday()==6: #segunda feira
        if its_holiday(todays_date-datetime.timedelta(days=3)):
            report_date=todays_date-datetime.timedelta(days=4)
            # return report_date,'='
            return report_date,'='+"'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=4)):
            report_date=todays_date-datetime.timedelta(days=4)
            report_date1=todays_date-datetime.timedelta(days=3)
            return report_date1,' between '+"'"+str(report_date)+"'"+' and '+"'"+str(report_date1)+"'"
            # return todays_date-datetime.timedelta(days=4),'and following day, i must review the query and accomodate this scenario'
        else:
            report_date=todays_date-datetime.timedelta(days=3)
            # return todays_date-datetime.timedelta(days=3),'='
            return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==1:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=4)
            # return todays_date-datetime.timedelta(days=4),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:
            if its_holiday(todays_date-datetime.timedelta(days=4)):
                report_date=todays_date-datetime.timedelta(days=4)
                # return todays_date-datetime.timedelta(days=4),'>='
                return report_date,'>= '+"'"+str(report_date)+"'"
            else:
                report_date=todays_date-datetime.timedelta(days=1)
                # return todays_date-datetime.timedelta(days=3),'>='
                return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==2:
        if its_holiday(todays_date-datetime.timedelta(days=2)):
            report_date=todays_date-datetime.timedelta(days=4)
            
            # return todays_date-datetime.timedelta(days=4),'>='
            return report_date,'>='+ "'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:    
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='
            return report_date,'= '+"'"+str(report_date)+"'"
    elif todays_date.weekday()==3:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        else:
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        
    elif todays_date.weekday()==4:
        if its_holiday(todays_date-datetime.timedelta(days=1)):
            report_date=todays_date-datetime.timedelta(days=2)
            # return todays_date-datetime.timedelta(days=2),'='
            return report_date,'= '+"'"+str(report_date)+"'"
        elif its_holiday(todays_date-datetime.timedelta(days=2)):
            report_date=todays_date-datetime.timedelta(days=2)
            report_date1=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=2),'and following day, i must review the query and accomodate this scenario'
            return report_date1, ' between '+"'"+str(report_date)+"'"+' and '+"'"+str(report_date1)+"'"
        else:
            report_date=todays_date-datetime.timedelta(days=1)
            # return todays_date-datetime.timedelta(days=1),'='            
            return report_date,'= '+"'"+str(report_date)+"'"