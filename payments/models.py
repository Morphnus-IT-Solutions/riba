from decimal import Decimal
from django.db import models
from django.db.models import Sum
from datetime import datetime
import hashlib
#from payments import (icicipg, hdfcpg, axispg, iciciemipg, citibankpg, paybackpg, 
#        ccAvenue as ccavenue, innovitipg, axispg, itzpg, amexpg)
from django.http import Http404
from settings import *
from django.utils import simplejson
from settings import PAYMENT_PAGE_PROTOCOL
from utils import utils
import logging
from django.db import transaction
from indexer import indexer

log = logging.getLogger('fborder')

DEFAULT_REVERSAL_REASON = 'Item(s) Removed'

# Create your models here.
class PaymentAttempt(models.Model):
    class Meta:
        unique_together = ('gateway','transaction_id')

    # These should change.. should contain only bank codes
    GATEWAY_CHOICES=(
        ('icici', 'ICICI'),
        ('paypal', 'Pay Pal'),
        ('cc_avenue', 'CC Avenue'),
        ('moto', 'Moto'),
        ('cheque', 'Cheque'),
        ('deposit','Deposit'),
        ('transfer', 'Online Transfer'),
        ('mail','mail'),
        ('cod','cod'),
        ('atom_ivr', 'Atom IVR'),
        ('hdfc-emi','hdfc-emi'),
        ('hdfc-card','hdfc-card'),
        ('payback', 'Payback'),
        ('citi-emi','citi-emi'),
        ('citi-card','citi-card'),
        ('citi-rewards','citi-rewards'),
        ('icici-emi','icici-emi'),
    )
    
    PAYMENT_MODES = (
        ('credit-card','Credit Card'),
        ('credit-card-emi-web','Credit Card EMI'),
        ('card-ivr','Credit Card (IVR)'),
        ('credit-card-emi-ivr','Credit Card EMI (IVR)'),
        ('debit-card','Debit Card'),
        ('netbanking','Net Banking'),
        ('cheque','Cheque/DD'),
        ('deposit-transfer','Deposit/Transfer'),
        ('card-at-store','Card at Store'),
        ('cash-at-store','Cash at Store'),
        ('cash-at-office','Cash at Office'),
        ('cash-collection','Cash Collection'),
        ('cod','Cash On Delivery'),
        ('payback','Payback'),
        ('atom','ATOM'),
        ('paymate','Paymate'))
    
    PAYMENT_MODES_FOR_SUPPORT = (
        ('cheque','Cheque/DD'),
        ('cash-collection','Cash Collection'),
        ('cod','Cash On Delivery'),
        ('atom','Atom'), 
        ('paymate', 'Paymate'))
    
    PAYMENT_MODES_MAP = {'credit-card':'Credit Card',
        'credit-card-emi-web':'Credit Card EMI',
        'card-ivr':'Credit Card (IVR)',
        'credit-card-emi-ivr':'Credit Card EMI (IVR)',
        'debit-card':'Debit Card',
        'netbanking':'Net Banking',
        'cheque':'Cheque/DD',
        'deposit-transfer':'Deposit/Transfer',
        'card-at-store':'Card at Store',
        'cash-at-store':'Cash at Store',
        'cash-at-office':'Cash at Office',
        'cash-collection':'Cash',
        'cod':'Cash On Delivery',
        'payback':'Payback',
        'atom':'ATOM',
        'paymate':'Paymate',
        'itz':'Itz Cash',
    }
    
    #for support only
    PAYMENT_MODES_GROUP = {'credit-card':1,
        'credit-card-emi-web':1,
        'card-ivr':1,
        'credit-card-emi-ivr':1,
        'debit-card':1,
        'netbanking':1,
        'cheque':2,
        'deposit-transfer':3,
        'card-at-store':1,
        'cash-at-store':3,
        'cash-at-office':3,
        'cash-collection':3,
        'cod':4,
        'payback':5,
        'itz':5,
        'atom':5,
        'paymate':5,
    }

    PAYMENT_GATEWAYS_MAP = {
        'SUVI':'Suvidha',
        'ICCA':'ICICICash',
        'EBIL':'EasyBill',
        'PAYB':'PAYBACK',
        'ITZC':'Itz Cash',
        'COD':'Cash On Delivery',
        'PAYM':'Paymate',
        'ATOM':'Atom',
        'ICIC':'ICICI',
        'ICI3':'ICICI 3 EMI',
        'ICI6':'ICICI 6 EMI',
        'ICI9':'ICICI 9 EMI',
        'HDFC':'HDFC',
        'HDF3':'HDFC 3 EMI',
        'HDF6':'HDFC 6 EMI',
        'HDF9':'HDFC 9 EMI',
        'INN3':'Innoviti 3 EMI',
        'INN6':'Innoviti 6 EMI',
        'INN9':'Innoviti 9 EMI',
        'INN12':'Innoviti 12 EMI',
    }

    #payment modes (cod, cheque, credit card, netbanking, deposit etc.)
    payment_mode = models.CharField(max_length=50, db_index=True, choices=PAYMENT_MODES)
    #gateway codes where payment was initiated
    gateway = models.CharField(max_length=50, choices=GATEWAY_CHOICES,
        db_index=True, null=True, blank=True)
    #bank names where payment is done
    bank = models.CharField(max_length=50, null=True, blank=True)

    #new payment attempt status
    status = models.CharField(max_length=50, db_index=True, default='unpaid', choices=(
        ('unpaid','Unpaid'),
        ('pending realization','Pending Realization'),
        ('in verification','In Verification'),
        ('paid','Paid'),
        ('rejected','Rejected'),
        ('refunded','Refunded'),
        ('info received','Info Received'),
        ))
    
    # transaction id with the gateway
    transaction_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    pg_transaction_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    
    #For cheque/dd
    instrument_no = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    instrument_issue_bank = models.CharField(max_length=100, null=True, blank=True)
    instrument_recv_date = models.DateField(null=True, blank=True)
    instrument_received_by = models.ForeignKey('users.Profile', null=True, blank=True, related_name='+')

    #how much was the amount paid
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')
    #date when amount is credited to our account
    payment_realized_on = models.DateTimeField(null=True, blank=True)
    
    # to which order (if any) does this payment belong
    order = models.ForeignKey('orders.Order', null=True, blank=True)
    fraud_status = models.CharField(max_length=25, blank=True,null=True,default='')

    # what response we got from the gateway
    response = models.CharField(max_length=100, blank=True, null=True)
    response_detail = models.TextField(blank=True, null=True)
    redirect_url = models.CharField(max_length=500, blank=True, default='')
    
    emi_plan = models.CharField(max_length=2, blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_on = models.DateTimeField(auto_now=True)

    action = models.CharField(max_length=25, db_index=True, default='fulfil')
    notes = models.TextField(null=True, blank=True)
    
    #Additional Exceptions
    InvalidOperation = type('InvalidOperation', (Exception,), {})
    InsufficientData = type('InsufficientData', (Exception,), {})
    NoResponseFromPG = type('NoResponseFromPG', (Exception, ), {})

    def index(self, **kw):
        ''' Indexes the payment object in solr '''
        from utils import solrutils 
        payment_doc = self.get_payment_solr_doc()

        order_doc = kw.get('order_doc')
        if not order_doc:
            order_doc = self.order.get_order_solr_doc()

        payment_doc.update(order_doc)
        payment_doc['doc_type'] = 'payment'
        payment_doc['unique_key'] = '%s%s' % (payment_doc['doc_type'], self.id)

        solrutils.order_add_data(payment_doc)

    def get_payment_solr_doc(self):
        payment_doc = {
            'order_id': self.order.id,
            'doc_type': 'payment',
            'payment_pk': self.id,
            'payment_amount': '%.2f' % self.amount,
            'payment_transaction_id': self.transaction_id,
            'payment_payment_mode': self.payment_mode,
            }
        if self.gateway:
            payment_doc['payment_gateway'] = self.gateway
        if self.emi_plan:
            payment_doc['payment_emi_plan'] = self.emi_plan
        if self.bank:
            payment_doc['payment_bank'] = self.bank
        if self.status:
            payment_doc['payment_status'] = self.status
        if self.fraud_status:
            payment_doc['payment_fraud_status'] = self.fraud_status 
        if self.instrument_no:
            payment_doc['payment_instrument_no'] = self.instrument_no 
        if self.instrument_issue_bank:
            payment_doc[
                'payment_instrument_issue_bank'] = self.instrument_issue_bank
        if self.instrument_recv_date:
            payment_doc[
                'payment_instrument_recv_date'] = self.instrument_recv_date 
        if self.created_on:
            payment_doc['payment_created_on'] = self.created_on,
        if self.payment_realized_on:
            payment_doc[
                'payment_payment_realized_on'] = self.payment_realized_on

        return payment_doc

    def create_transaction_id(self, request, **kwargs):
        #timestamp = datetime.now().strftime('%x %X %f')
        #data = '%s %s %s' % (self.order.id, timestamp, self.amount)
        #data = '%s %s' % (data, str(request.META))
        #md5 = hashlib.md5(data).hexdigest()
        #collisions = PaymentAttempt.objects.filter(gateway='icici', transaction_id=md5)
        #if collisions:
        #    md5 = hashlib.md5('%s %s' % (md5, datetime.now().strftime('%x %X %f')))
        #    self.transaction_id = md5
        #else:
        #    self.transaction_id = md5 
        order_id = kwargs.get('order_id', None)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%s')
        self.transaction_id = '%s%s' %(timestamp, order_id)
    
    def get_citibanktracenumber(self):
        try:
            return self.citibanktracenumber.trace_number
        except:
            raise Http404

    def check_risk(self, request, **kwargs):
        card_details = kwargs.get('card_details')
        card_type = kwargs.get('card_type')
        user_ip = kwargs.get('user_ip')
        order = self.order

        order_id = order.get_id() 
        delivery_info = order.get_address(request, type='delivery')
        billing_info = order.get_address(request, type='billing')
        
        # EBS check Rest API parameters.
        shipping_name = '%s %s' % (delivery_info.address.first_name,delivery_info.address.last_name)
        billing_name = '%s %s' % (billing_info.address.first_name,billing_info.address.last_name)
        
        product_info=''
        for oi in order.get_order_items(request, exclude=dict(state__in=['cancelled','bundle_item'])):
            if product_info=='':
                product_info += str(oi.qty) + ' X ' + str(oi.item_title)
            else:
                product_info += '|' +  str(oi.qty) + ' X ' + str(oi.item_title)

        rmsRiskBox_param = None
        if 'rmsID' in request.session:
            rmsRiskBox_param = request.session['rmsID']
        ebs_check_params = {'profileId':order.user_id,
                'cardNumber':card_details.get('card_no'),
                'ipAddress':user_ip,
                'headerValue':'',
                'userAgent':'',
                'orderId': order.reference_order_id,
                'cardType':card_type,
                'cardBillingName':billing_name,
                'totalAmount':str(order.payable_amount),
                'billingCurrencyCode':'',
                'billingAddress': billing_info.address.address,
                'billingCity': billing_info.address.city.name,
                'billingState':billing_info.address.state.name,
                'billingPostalCode':billing_info.address.pincode,
                'billingCountry':'IN',
                'billingEmail': billing_info.address.email,
                'billingPhone':billing_info.address.phone,
                'shippingName':shipping_name,
                'shippingAddress':delivery_info.address.address,
                'shippingCity':delivery_info.address.city.name,
                'shippingState':delivery_info.address.state.name,
                'shippingPostalCode':delivery_info.address.pincode,
                'shippingCountry':'IN',
                'shippingEmail':delivery_info.address.email,
                'shippingPhone':delivery_info.address.phone,
                'txnId':'',
                'productInformation':product_info,
                'rmsRiskBox': rmsRiskBox_param,
                }
        
        log.info(" Ebs Request Data %s" % ebs_check_params)
        try:
            ebs_info = simplejson.dumps(ebs_check_params)
            response = simplejson.loads(APIManager.ebs_check(ebs_info))
            log.info(" Ebs Response Data %s" % response)
            fraud_status = response.get('Status', 'Approved')
        except Exception, e:
            fraud_status = 'Approved'
        self.fraud_status = fraud_status
        self.save()
        return fraud_status


    def get_gateway_request(self, request, **kwargs):
        self.gateway = kwargs.get('gateway')
        bank = kwargs.get('bank')
        card_details = kwargs.get('card_details') 
        
        gateway_request = None
        gateway_error = None
        order = self.order
        self.status = 'pending realization'
        
        if self.gateway in ('citi-emi', 'citi-card'):
            trace_number_obj = CitiBankTraceNumber.get_or_create(payment_attempt=self)
            json = citibankpg.create_request(self,request)
            if json:
                if not 'error' in json:
                    self.emi_plan = request.POST.get('emi_plan','')
                    self.redirect_url = json.get('redirectUrl','')
                    self.transaction_id = json.get('trace_no')
                    self.gateway = 'CIT%s' % self.emi_plan
                    self.bank = 'citi'
                    self.save()
                    gateway_request = json

            else:
            	json = {'error':'No Response from PG'}    
            return dict(payment_attempt=self,json=json)

        elif self.gateway in ('axis-emi', 'axis-card'):
            json =  axispg.create_request(request, payment_attempt=self)
            if json:
                self.redirect_url = json.get('bankUrl','')
                self.bank = 'axis'
                if self.gateway == 'axis-emi':
                    self.gateway = 'AXI%s' % self.emi_plan
                else:
                  self.gateway = 'AXIS'
                self.save()
                gateway_request = json
        
        elif self.gateway == 'amex-card':
            json =  amexpg.create_request(request, payment_attempt=self, gateway=self.gateway)
            if json:
                self.redirect_url = json.get('bankUrl','')
                self.bank = 'amex'
                self.gateway = 'AMEX'
                self.save()
                gateway_request = json
        
        elif self.gateway in ('icici-emi', 'icici-card'):
            json =  icicipg.create_request(self, request)
            redirect_url = json.get('redirectUrl')
            if json and redirect_url:
                self.bank = bank
                self.redirect_url = redirect_url
                if self.gateway == 'icici-emi':
                    self.gateway = 'ICI%s' % self.emi_plan
                else:
                  self.gateway = 'ICIC'
                self.save()
                gateway_request = self.redirect_url
        
        elif self.gateway in ('hdfc-emi', 'hdfc-card'):
            json = hdfcpg.create_request(request, card_details=card_details, payment_attempt=self)
            if json:
                if not 'error' in json:
                    self.bank = 'hdfc'
                    self.redirect_url = json.get('redirectUrl','')
                    self.transaction_id = json.get('payment_id')
                    #self.transaction_id = json.get('track_id')
                    if self.gateway == 'hdfc-emi':
                        self.gateway = 'HDF%s' % self.emi_plan
                    else:
                        self.gateway = 'HDFC'
                    self.save()
                    #gateway_request = json
                    #gateway_request = self.redirect_url
        
        elif self.gateway == 'payback':
            json = paybackpg.create_request(self,request)
            if json:
                if not 'error' in json:
                    self.redirect_url = json.get('redirectUrl')
                    self.transaction_id = self.id
                    self.bank = 'payback'
                    self.gateway = 'PAYB'
                    self.save()
                gateway_request = self.redirect_url

        elif self.gateway == 'cc_avenue':
            redirect_url = '%s://%s/orders/process_payment_ccavanue' % (PAYMENT_PAGE_PROTOCOL, request.client.domain)           
            cc_avenue_request = ccavenue.create_request(request, bank=bank, payment_attempt=self, 
                    order=order, redirect_url=redirect_url)
            log.info('CC_AVENUE REQUEST %s' % cc_avenue_request)
            
            if cc_avenue_request and bank:
                self.redirect_url = cc_avenue_request.get('action','')
                self.bank = bank
                self.gateway = 'CCAV'
                self.save()
                gateway_request = cc_avenue_request
        
        elif self.gateway == 'innoviti':
            json = innovitipg.create_request(request, payment_attempt=self, order=order, bank=bank)
            if json:
                if not 'error' in json:
                    self.bank = bank
                    self.transaction_id = json.get('orderId', self.transaction_id)
                    self.emi_plan = request.POST.get('emi_plan','')
                    self.redirect_url = json.get('innovitiUrl', '')
                    self.bank = bank
                    self.gateway = 'INN%s' % self.emi_plan 
                    self.save()
                    gateway_request = json
        
        elif self.gateway == 'itz':
            json = itzpg.create_request(request, payment_attempt=self, order=order)
            if json:
                if not 'error' in json:
                    self.gateway = 'ITZ'
                    self.redirect_url = json.get('redirect_url', '')
                    self.save()
                    gateway_request = json
        
        elif self.gateway in ('ATOM', 'PAYM'):
            self.bank = bank
            self.save()
            gateway_request = self
        
        if not gateway_request:
            log.info(" No response from PG")
            e = self.NoResponseFromPG
            e.message = utils.DEFAULT_PAYMENT_PAGE_ERROR
            raise e
        return gateway_request


    def process_response(self, request, **kwargs):
        action = 'approved'
        payment_mode_code = self.order.payment_mode
        params = kwargs.get('params')
        
        if self.gateway in ('ICIC', 'ICI3', 'ICI6', 'ICI9'):
            # status = icicipg.process_response(self, request)
            if params.get('RespCode',None) == "0":
                pg_response = 'captured'
            if params.get('RespCode',None) in ["1","2"]:
                pg_response = 'rejected' 
            self.response = params.get('RespCode','')
            self.response_detail = params.get('Message','')
            self.pg_transaction_id = params.get('ePGTxnID','')

        elif self.gateway.endswith('CCAV'): #BankName-CCAV
            resp = params.get('AuthDesc','')
            self.response = resp
            self.response_detail = resp
            checksum = params['Checksum']
            if not ccavenue.veriyChecksum(self.transaction_id,self.amount,resp,int(checksum)):
                pg_response = 'rejected'
            else:
                if resp == 'Y':
                    pg_response = 'captured'
                if resp == 'N':
                    pg_response = 'rejected'

        elif self.gateway.startswith('PAYB'):
            json = paybackpg.process_response(self, params)
            status = json.get('status')
            if status == 'success':
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.response_detail = json.get('message')
            self.pg_transaction_id = self.id

        elif self.gateway in ('HDFC', 'HDF3', 'HDF6', 'HDF9'):
            json = hdfcpg.process_response(self, params)
            log.info("Json is %s" % json)
            response_code = json.get('responseCode')
            if response_code == 0:
                result = json['result']
                if result == 'CAPTURED':
                    pg_response = 'captured'
                else:
                    pg_response = 'rejected'
            else:
                pg_response = 'rejected'
            self.response_detail = json.get('result')
            self.response = response_code
            
            #This is for HDFC SSL 
            #self.pg_transaction_id = json.get('tranid', '')
            #result = json.get('result')
            #if 'error' not in json:
            #    if result == 'CAPTURED':
            #        pg_response = 'captured'
            #        self.response = json.get('auth_code')
            #        self.response_detail = json.get('ref_no')
            #    else:
            #        pg_response = 'rejected'
            #        self.response = result
            #else:
            #    pg_response = 'rejected'
            #    self.response = json.get("error_no");
            #    self.response_detail = json.get("error");
               

        elif self.gateway in ('CITI', 'CIT3', 'CIT6', 'CIT9'):
            json = citibankpg.process_response(self, params)
            status = json.get('status')
            if status in ('approved','captured'):
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.response = params.get('authCode','')
            self.response_detail = params.get('message','')

        elif self.gateway in ('INN3', 'INN6', 'INN9', 'INN12'):
            json = innovitipg.process_response(self, params)
            respCode = json.get('respCode')
            if respCode == '00':
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.response = json.get('respCode','')
            self.response_detail = json.get('respMsg','')
            self.pg_transaction_id = json.get('uniPayId','')
        
        elif self.gateway == 'AMEX':
            json = amexpg.process_response(request, payment_attempt=self, params=params)
            if json.get('respCode') == "0":
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.response = json.get('respCode','')
            self.response_detail = json.get('message','')
            self.pg_transaction_id = json.get('transactionNo','')
        
        elif self.gateway in ('AXIS', 'AXI3', 'AXI6', 'AXI9'):
            json = axispg.process_response(request, payment_attempt=self, params=params)
            if json.get('respCode') == "0":
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.response = json.get('respCode','')
            self.response_detail = json.get('message','')
            self.pg_transaction_id = json.get('transactionNo','')
        
        elif self.gateway == 'ITZ':
            json = itzpg.process_response(request, payment_attempt=self, params=params)
            status = json.get('responseCode', '')
            if status == '0':
                pg_response = 'captured'
                itzpg.save_franchise_commissions(request, payment_attempt=self)
            else:
                pg_response = 'rejected'
            self.response = status
            self.response_detail = json.get('description','')

        elif self.payment_mode == 'atom':
            self.gateway='ATOM'
            response_code = params.get('ResCode')
            if response_code == '00':
                self.amount = self.order.payable_amount
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.pg_transaction_id = params.get('PgTxId')
            self.transaction_id = params.get('AtomTxId')
            self.response = response_code
            self.response_detail = params.get('TranStatus')

        elif self.payment_mode == 'paymate':
            self.gateway='PAYM'
            response_code = params.get('TranStatus')
            if response_code == '400':
                self.amount = self.order.payable_amount
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.pg_transaction_id = params.get('PgTxId')
            self.response = response_code
        
        elif self.gateway == 'ITZC':
            response_code = params.get('ResCode')
            if response_code == '400':
                self.amount = self.order.payable_amount
                pg_response = 'captured'
            else:
                pg_response = 'rejected'
            self.pg_transaction_id = params.get('PgTxId')
            self.response = response_code
            self.response_detail = params.get('ITZTxId')

        self.save()

        with transaction.commit_on_success():
            self.move_payment_state(request, payment_mode_code=payment_mode_code, action=action, pg_response=pg_response)


    def move_payment_state(self, request, **kwargs):
        action = kwargs.get('action', None)
        agent = kwargs.get('agent')
        new_state = kwargs.get('new_state')
        is_paid = kwargs.get('is_paid', False)
        o_log = kwargs.get('order_log')
        
        order = self.order
        from orders.models import OrderLog
        if not o_log:
            o_log = OrderLog(order=order, profile=agent, action='payment')

        payment_log = PaymentLog(payment=self)

        #mark status as paid for call center interface
        if is_paid and request.is_auth:
            data = kwargs.get('data', {})
            self.status = new_state
            self.pg_transaction_id = data.get('pg_transaction_id')
            self.notes = data.get('notes')
            self.amount = data.get('amount')
            self.payment_realized_on = datetime.now()

        elif self.payment_mode == 'cod':
            self.move_cod_state(request, payment_log=payment_log, **kwargs)

        elif self.payment_mode in ('credit-card-emi-web', 'credit-card', 'card-at-store',
                'debit-card', 'netbanking'):
            self.move_card_state(request, payment_log=payment_log, order_log=o_log, **kwargs)
        
        elif self.payment_mode in ('payback', 'itz'):
            self.move_payback_state(request, payment_log=payment_log, **kwargs)
       
        #action != 'booked' is required - prady
        elif self.payment_mode in ('cash-at-store', 'cash-collection',
            'cash-at-office') and action != 'booked':
            self.move_cash_state(request, payment_log=payment_log, **kwargs)
        
        #action != 'booked' is required - prady
        elif self.payment_mode == 'cheque' and action != 'booked':
            self.move_cheque_state(request, payment_log=payment_log, **kwargs)
       
        elif self.payment_mode in ('atom', 'paymate') and action != 'booked':
            self.move_ivr_state(request, payment_log=payment_log, **kwargs)

        elif self.payment_mode == 'card-moto':
            self.move_moto_state(request, payment_log=payment_log, **kwargs)
        
        if is_paid and self.order.medium == 'support':
            if self.payment_mode == 'cod':
                self.status = 'pending realization'
            else:
                self.status = 'paid'
        
        self.save()
        payment_log.status = self.status
        
        if order.support_state == 'cancelled' and self.status == 'paid':
            o_log.save()
            order.openRefund(request, profile=agent, amount=self.amount, earn_reveral=False,
                notes='Payment realized after order cancellation', order_log=o_log)
            payment_log.order_log = o_log
            payment_log.save()
            return
        
        if order.support_state not in ['booked','cancelled','paid'] and (self.status == 'paid') and \
            (self.payment_mode != 'cod'):
            o_log.save()
            order.openRefund(request, profile=agent, amount=self.amount, earn_reveral=False,
                notes='Excess Payment', order_log=o_log)
            payment_log.order_log = o_log
            payment_log.save()
            return
        
        confirm_allowed = False
        if (self.status == 'paid') or (self.payment_mode == 'cod'):
            confirm_allowed, delta = order.is_confirm_allowed(request)
            #earn payback points for cod orders
            if (self.status == 'paid') and (self.payment_mode == 'cod') and \
                confirm_allowed and order.payback_id:
                points_header = PointsHeader(order=order)
                points_header.earn_points(request)
                o_log.earn_points = order.get_payback_earn_points()
        
        o_log.save()
        payment_log.order_log = o_log
        payment_log.save()
        if (self.payment_mode == 'cod' and self.status == 'pending realization') or \
            (self.payment_mode != 'cod' and self.status == 'paid'):
            if (order.support_state in ['booked','paid']):
                if confirm_allowed:
                    exception = None
                    if utils.get_chaupaati_marketplace() != order.client:
                        log.info("Depleting Inventory For order - %s, payment_mode: %s" % (order.id, self.payment_mode))
                        try:
                            order.update_inventory(request, action='deplete')
                        except order.InventoryError, e:
                            log.info('Move payment: stock not available for order (%s) - %s' %
                                (order.id, e.errors))
                            exception = e
                    if not exception:
                        order.confirm(request, profile=agent, payment_mode=self.payment_mode,
                            payment_date=self.payment_realized_on, order_log=o_log)
                    elif order.support_state == 'booked':
                        order.support_state = 'paid'
                        order.save()
                        o_log.status = 'paid'
                        o_log.save()
                        raise exception
 

    def move_cod_state(self, request, **kwargs):
        action = kwargs.get('action','')
        new_state = kwargs.get('new_state')
        payment_log = kwargs.get('payment_log')
        
        if self.order.support_state == 'cancelled' and (new_state != 'rejected'):
            raise self.InvalidOperation

        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['in verification','rejected']
        elif self.status.lower() == 'in verification':
            valid_states = ['pending realization','rejected']
        elif self.status.lower() == 'pending realization':
            valid_states = ['paid','rejected']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            else:
                if new_state == 'paid':
                    if self.order.support_state != 'delivered':
                        raise self.InvalidOperation
                    else:
                        self.payment_realized_on = datetime.now()
                self.status = new_state
        elif action == 'booked':
            self.status = 'pending realization'
        else:
            self.status = 'rejected'


    def move_card_state(self, request, **kwargs):
        action = kwargs.get('action','')
        pg_response = kwargs.get('pg_response','')
        new_state = kwargs.get('new_state')
        payment_log = kwargs.get('payment_log')
        o_log = kwargs.get('order_log')

        if self.order.support_state == 'cancelled' and (new_state not in ['paid',
            'rejected','refunded']):
            raise self.InvalidOperation

        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['pending realization','rejected']
        elif self.status.lower() == 'pending realization':
            valid_states = ['in verification','rejected','paid']
        elif self.status.lower() == 'in verification':
            valid_states = ['paid','refunded']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            else:
                self.status = new_state
                if new_state in ['paid','in verification']:
                    self.payment_realized_on = datetime.now()
                return
        
        if self.status.lower() == 'pending realization' and pg_response == 'captured':
            if self.fraud_status == 'Review':
                self.status = 'in verification'
                if self.order.payable_amount >= self.amount and \
                    self.order.support_state == 'booked':
                    self.order.support_state = 'paid'
                    o_log.status = 'paid'
                    self.order.save()
            else:
                self.status = 'paid'
            if not self.payment_realized_on:
                self.payment_realized_on = datetime.now()
        else:
            self.status = 'rejected'


    def move_payback_state(self, request, **kwargs):
        pg_response = kwargs.get('pg_response','')
        new_state = kwargs.get('new_state')
        payment_log = kwargs.get('payment_log')

        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['rejected','pending realization','paid']
        elif self.status.lower() == 'pending realization':
            valid_states = ['rejected','paid']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            else:
                self.status = new_state
                if new_state == 'paid':
                    self.payment_realized_on = datetime.now()
                return
        
        if self.status.lower() == 'pending realization' and pg_response == 'captured':
            self.status = 'paid'
            self.payment_realized_on = datetime.now()
        else:
            self.status = 'rejected'


    def move_cash_state(self, request, **kwargs):
        pg_response = kwargs.get('pg_response','')
        action = kwargs.get('action','')
        new_state = kwargs.get('new_state')
        data = kwargs.get('data',{})
        from_suvidha = kwargs.get('suvidha',False)
        payment_log = kwargs.get('payment_log')

        amount = data.get('amount')
        pg_transaction_id = data.get('pg_transaction_id','')
        payment_realized_on = data.get('payment_realized_on')
        notes = data.get('notes')
        
        if self.order.support_state == 'cancelled' and (new_state not in ['paid',
            'rejected']):
            raise self.InvalidOperation

        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['info received','rejected']
            if from_suvidha:
                valid_states.append('paid')
        elif self.status.lower() == 'info received':
            valid_states = ['paid','rejected']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            if new_state == 'paid':
                if not ((pg_transaction_id or from_suvidha) and payment_realized_on):
                    raise self.InsufficientData
                self.pg_transaction_id = pg_transaction_id
                self.payment_realized_on = payment_realized_on
                payment_log.pg_transaction_id = pg_transaction_id
            if new_state != 'rejected':
                self.amount = amount
                self.notes = notes
                payment_log.amount = amount
                payment_log.notes = notes
            self.status = new_state
            return
        
        elif self.status != 'paid' and pg_response == 'captured':
            self.status = 'paid'
        else:
            self.status = 'rejected'


    def move_cheque_state(self, request, **kwargs):
        action = kwargs.get('action','')
        agent = kwargs.get('agent')
        data = kwargs.get('data',{})
        new_state = kwargs.get('new_state')
        payment_log = kwargs.get('payment_log')
        
        instrument_no = data.get('instrument_no')
        instrument_issue_bank = data.get('instrument_issue_bank')
        instrument_recv_date = data.get('instrument_recv_date')
        amount = data.get('amount')
        payment_realized_on = data.get('payment_realized_on')
        gateway = data.get('gateway')
        notes = data.get('notes')

        if self.order.support_state == 'cancelled' and (new_state not in ['paid',
            'rejected']):
            raise self.InvalidOperation

        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['info received','pending realization','rejected']
        elif self.status.lower() == 'info received':
            valid_states = ['pending realization','rejected']
        elif self.status.lower() == 'pending realization':
            valid_states = ['paid','rejected']
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            if new_state in ['info received','pending realization']:
                if (not (instrument_no and instrument_issue_bank and amount)) or \
                    (new_state == 'pending_realization' and not instrument_recv_date):
                    raise self.InsufficientData
            if new_state == 'paid':
                if not payment_realized_on:
                    raise self.InsufficientData
                self.payment_realized_on = payment_realized_on
            if new_state != 'rejected':
                self.amount = amount
                self.instrument_no = instrument_no
                self.instrument_issue_bank = instrument_issue_bank
                self.instrument_recv_date = instrument_recv_date
                self.gateway = gateway
                self.instrument_received_by = agent
                self.notes = notes
                payment_log.amount = amount
                payment_log.notes = notes
                payment_log.instrument_no = instrument_no
                payment_log.instrument_issue_bank = instrument_issue_bank
                payment_log.instrument_recv_date = instrument_recv_date
            self.status = new_state
            return
        
        elif self.order.medium == 'support':
            self.status = 'info received'
        else:
            self.status =  'rejected'

    def move_ivr_state(self, request, **kwargs):
        payment_log = kwargs.get('payment_log')
        pg_response = kwargs.get('pg_response')
        new_state = kwargs.get('new_state')
        
        valid_states = []
        if self.status.lower() == 'unpaid':
            valid_states = ['rejected','pending realization','paid']
        if self.status.lower() == 'pending realization':
            valid_states = ['rejected','paid']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            else:
                self.status = new_state
                if new_state == 'paid':
                    self.payment_realized_on = datetime.now()
                return

        if self.status in ['unpaid','pending realization'] and pg_response == 'captured':
            self.status = 'paid'
            self.payment_realized_on = datetime.now()
        else:
            self.status = 'rejected'

    def move_moto_state(self, request, **kwargs):
        payment_log = kwargs.get('payment_log')
        order = kwargs.get('pending_order','')
        pg_transaction_id = request.POST.get('transaction_no')
        notes = request.POST.get('transaction_notes')
        amount = None
        if order:
            amount = order.payable_amount

        if self.order.support_state == 'cancelled':
            raise self.InvalidOperation

        if not (pg_transaction_id  and notes):
            raise self.InsufficientData
        self.pg_transaction_id = pg_transaction_id
        self.payment_realized_on = datetime.now()
        self.notes = notes
        payment_log.pg_transaction_id = pg_transaction_id
        self.status = 'paid'
        self.save()
        payment_log.status = self.status
        payment_log.pg_transaction_id = pg_transaction_id
        payment_log.amount = amount
        payment_log.notes = notes

   
    #Will be called from a template. Do not pass request to this function - prady
    def printable_payment_mode(self):
        return self.PAYMENT_MODES_MAP.get(self.payment_mode, self.payment_mode)

    #Will be called from a template. Do not pass request to this function - prady
    def printable_payment_gateway(self):
        return self.PAYMENT_GATEWAYS_MAP.get(self.gateway, self.gateway)
    
    #Will be called from a template. Do not pass request to this function - prady
    def printable_payment_bank(self):
        return self.PAYMENT_GATEWAYS_MAP.get(self.bank, self.bank)
    
    def get_burn_points(self):
        if self.payment_mode != 'payback':
            return 0
        factor = Decimal(PointsHeader.BURN_POINTS_MAP.get(self.order.client.name,0))
        points = int(round(self.amount*factor))
        return points
    
    #used for support only - prady
    def get_payment_group(self):
        return self.PAYMENT_MODES_GROUP.get(self.payment_mode, 1)
models.signals.post_save.connect(indexer.post_save_handler, sender=PaymentAttempt)


class PaymentLog(models.Model):
    payment = models.ForeignKey(PaymentAttempt, related_name='payment_log')
    order_log = models.OneToOneField('orders.OrderLog', related_name='payment_log')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    pg_transaction_id = models.CharField(max_length=100, null=True, blank=True, default=None)
    instrument_no = models.CharField(max_length=10, null=True, blank=True, default=None)
    instrument_issue_bank = models.CharField(max_length=100, null=True, blank=True, default=None)
    instrument_recv_date = models.DateField(null=True, blank=True, default=None)
    notes = models.TextField(null=True, blank=True, default=None)
    
    def get_class_name(self):
        return 'PaymentLog'

class PointsHeader(models.Model):

    MERCHANT_ID = {
            'Futurebazaar':'90012970',
            'Future Bazaar':'90012970',
            'ezoneonline':'90012999',
            }
    TERMINAL_ID = {
            'Futurebazaar':'64217418',
            'Future Bazaar':'64217418',
            'ezoneonline':'64127466',
            }
    EARN_POINTS_MAP = {
            'Futurebazaar':'0.03',
            'Future Bazaar':'0.03',
            'ezoneonline':'0.015',
            }
    BURN_POINTS_MAP = {
            'Futurebazaar':'4',
            'Future Bazaar':'4',
            'ezoneonline':'',
            }

    order = models.ForeignKey('orders.Order', null=False, blank=False)
    reference_id = models.CharField(max_length=20)
    loyalty_card = models.CharField(max_length=16, null=True, blank=True)
    partner_merchant_id = models.CharField(max_length=10)
    partner_terminal_id = models.CharField(max_length=10)
    txn_action_code = models.CharField(max_length=50)
    txn_classification_code = models.CharField(max_length=20)
    txn_payment_type = models.CharField(max_length=20, default='OTHERS')
    txn_date = models.DateField(null=True, blank=True)
    settlement_date = models.DateField(null=True, blank=True)
    txn_timstamp = models.DateTimeField(default = datetime.now())
    txn_value = models.IntegerField(max_length=10, null=True, blank=True)
    marketing_code = models.CharField(max_length=10, default='DEFAULT')
    branch_id = models.CharField(max_length=10, default='ONLINE')
    txn_points = models.IntegerField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='FRESH')
    reason = models.TextField(null=True, blank=True)
    burn_ratio = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('4'))
    earn_ratio = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.03'))

    def earn_points(self, request, **kwargs):
        order = self.order
        client_name = order.client.name
        self.reference_id = order.reference_order_id
        self.loyalty_card = order.payback_id
        self.partner_merchant_id = self.MERCHANT_ID.get(client_name)
        self.partner_terminal_id = self.TERMINAL_ID.get(client_name)
        self.txn_date = datetime.date(order.modified_on)
        self.txn_action_code = 'PREALLOC_EARN'
        self.txn_classification_code = 'CASH_CASH'
        self.settlement_date = datetime.date(datetime.now())   
        self.txn_value = order.payable_amount
        self.txn_points = order.get_payback_earn_points()
        self.earn_ratio = self.get_earn_ratio(client_name=client_name)
        self.burn_ratio = self.get_burn_ratio(client_name=client_name)
        log.info("EARN POINTS to jcaps order: %s -- %s" % (order, self.txn_points))
        self.reason = 'Order Confirmed'
        self.save()


        order_items = order.get_order_items(request, select_related=('seller_rate_chart__product',
            'seller_rate_chart'), exclude=dict(state__in=['cancelled','bundle_item']))
        
        for item in order_items:
            points_item = PointsItems(points_header=self, order_item=item)
            points_item.department_code = item.seller_rate_chart.product.id
            points_item.department_name = item.seller_rate_chart.product.title
            points_item.article_id = item.seller_rate_chart.article_id
            points_item.action_code = 'PREALLOC_EARN'
            points_item.item_amount = item.payable_amount()
            points_item.quantity = item.qty
            points_item.save()

        day = order.timestamp.strftime("%A")
        if day != 'Friday':
            from django.conf import settings
            payback_date = getattr(settings, 'PAYBACK_OFFER_DATE', 'Apr 9 2012')
            end_datetime = datetime.strptime('%s' % payback_date, '%b %d %Y')
            if self.order.timestamp < end_datetime and order.payable_amount >= getattr(settings, 'PAYBACK_OFFER_PRICE', 2000):
                # offer limited till 31st Mar
                cloned = self.clone()
                cloned.txn_points = order.get_payback_offer_earn_points()
                cloned.txn_payment_type = 'NO_PAYMENT'
                cloned.txn_value = 0
                cloned.txn_classification_code = 'BONUS_POINTS'
                cloned.save()
                log.info("EARN BONUS POINTS to jcaps order: %s -- %s" % (order, cloned.txn_points))
                # Creating xtra PointsItem for cloned BONUS_POINT header
                points_item = PointsItems(points_header=cloned, order_item_id=80000)
                points_item.department_code = 100 
                points_item.department_name = 'BONUS'
                points_item.article_id = 1111
                points_item.action_code = 'PREALLOC_EARN'
                points_item.item_amount = 0
                points_item.quantity = 0
                points_item.save()
    
    def earn_reversal(self, request, **kwargs):
        refund_items = kwargs.get('refund_items')
        amount = kwargs.get('amount')
        order = self.order
        notes = kwargs.get('notes', DEFAULT_REVERSAL_REASON)
        
        client_name = order.client.name

        self.reference_id = order.get_id()
        self.loyalty_card = order.payback_id
        self.partner_merchant_id = self.MERCHANT_ID.get(client_name)
        self.partner_terminal_id = self.TERMINAL_ID.get(client_name)
        self.txn_date = datetime.date(order.modified_on)
        self.txn_action_code = 'EARN_REVERSAL'
        self.txn_classification_code = 'RECONCILIATION'
        self.txn_payment_type = 'NO_PAYMENT'
        self.settlement_date = datetime.date(datetime.now())   
        self.txn_value = amount
        earn_ratio = self.get_earn_reversal_ratio(client_name=client_name)
        self.txn_points = int(round(Decimal(earn_ratio)*amount))
        log.info("Earn Reversal to jcaps order -- %s -- %s" % (order, self.txn_points))
        self.earn_ratio = self.get_earn_ratio(client_name=client_name)
        self.burn_ratio = self.get_burn_ratio(client_name=client_name)
        self.reason = notes
        self.save()
        
        for item in refund_items:
            order_item = item['order_item']
            points_items = PointsItems(points_header=self, order_item=order_item)
            points_items.department_code = order_item.seller_rate_chart.product.id
            points_items.department_name = order_item.seller_rate_chart.product.title
            points_items.article_id = order_item.seller_rate_chart.article_id
            points_items.action_code = 'EARN_REVERSAL'
            points_items.item_amount = item['amount']
            points_items.quantity = item['qty']
            points_items.save()
        
        from django.conf import settings
        if order.payable_amount < getattr(settings, 'PAYBACK_OFFER_PRICE', 2000) or order.support_state == 'cancelled':
            # Check for Earn reversal of BONUS_POINTS
            points_header = PointsHeader.objects.filter(txn_classification_code='BONUS_POINTS', order=order,\
                            txn_action_code='PREALLOC_EARN')
            if points_header:
                try:
                    cloned_header = PointsHeader.objects.get(txn_classification_code='BONUS_POINTS', order=order,\
                                    txn_action_code='EARN_REVERSAL')
                except PointsHeader.DoesNotExist:
                    # EarnReversal for BONUS should br created for once
                    # Do earn reversal of BOUNS_POINTS
                    points_header = points_header[0]
                    cloned_reversal = points_header.clone()
                    cloned_reversal.txn_action_code = 'EARN_REVERSAL'
                    cloned_reversal.txn_payment_type = 'NO_PAYMENT'
                    cloned_reversal.save()
                    log.info("Earn Reversal of BONUS_POINTS to jcaps order -- %s -- %s" % (order, cloned_reversal.txn_points))
                    # Creating xtra PointsItem for cloned_reversal BONUS_POINT header
                    points_item = PointsItems(points_header=cloned_reversal, order_item_id=80000)
                    points_item.department_code = 100
                    points_item.department_name = 'BONUS'
                    points_item.article_id = 1111
                    points_item.action_code = 'EARN_REVERSAL'
                    points_item.item_amount = 0
                    points_item.quantity = 0
                    points_item.save()
        
    def burn_reversal(self, request, **kwargs):
        order = self.order
        notes = kwargs.get('notes', DEFAULT_REVERSAL_REASON)
        refund_items = kwargs.get('refund_items')
        amount = kwargs.get('amount')
        client_name = order.client.name

        payment_attempt = order.get_payments(request, filter=dict(payment_mode='payback'))
        if payment_attempt:
            payment_attempt = payment_attempt[0]
            log.info("Payment Found %s :" % payment_attempt.amount)
                
            #Payback Transaction Id
            self.reference_id = payment_attempt.pg_transaction_id 
            
            self.partner_merchant_id = self.MERCHANT_ID.get(client_name)
            self.partner_terminal_id = self.TERMINAL_ID.get(client_name)
            self.txn_value = amount
            burn_ratio = self.get_burn_reversal_ratio(client_name=client_name)
            self.txn_points = int(round(Decimal(burn_ratio)*amount))
            log.info("Burn Reversal to jcaps -- %s" % self.txn_points)
            self.txn_action_code = 'BURN_REVERSAL'
            self.txn_payment_type = 'NO_PAYMENT'
            self.txn_classification_code = 'RECONCIALIATION'
            self.txn_date = datetime.date(payment_attempt.created_on)
            self.settlement_date = datetime.date(datetime.now())  
            self.reason = notes
            self.earn_ratio = self.get_earn_ratio(client_name=client_name)
            self.burn_ratio = self.get_burn_ratio(client_name=client_name)
            self.save()
        else:
            log.info("No Payment Attempt Found  :" )
            return
    
    def get_burn_ratio(self, **kwargs):
        client_name = kwargs.get('client_name', self.order.client.name)
        return self.BURN_POINTS_MAP.get(client_name)
    
    def get_earn_ratio(self, **kwargs):
        client_name = kwargs.get('client_name', self.order.client.name)
        earn_ratio = Decimal(str(self.EARN_POINTS_MAP.get(client_name)))
        day = self.order.timestamp.strftime("%A")
        if day == 'Friday' and self.order.is_valid_payback_promotion():
            # Payback Friday offer
            # Earn points will be 2X
            earn_ratio *= Decimal('2')
        return earn_ratio

    def get_burn_reversal_ratio(self, **kwargs):
        client_name = kwargs.get('client_name', self.order.client.name)
        order = self.order
        points_header = PointsHeader.objects.filter(order=order, txn_action_code='PREALLOC_EARN',\
                        txn_classification_code='CASH_CASH')
        if points_header:
            point_header = points_header[0]
            return point_header.burn_ratio
        else:
            return self.get_burn_ratio(client_name=client_name)

    def get_earn_reversal_ratio(self, **kwargs):
        client_name = kwargs.get('client_name', self.order.client.name)
        order = self.order
        points_header = PointsHeader.objects.filter(order=order, txn_action_code='PREALLOC_EARN',\
                        txn_classification_code='CASH_CASH')
        if points_header:
            point_header = points_header[0]
            return point_header.earn_ratio
        else:
            return self.get_earn_ratio(client_name=client_name)

    def clone(self):
        cloned = PointsHeader()
        cloned.order = self.order
        cloned.reference_id = self.reference_id
        cloned.loyalty_card = self.loyalty_card
        cloned.partner_merchant_id = self.partner_merchant_id
        cloned.partner_terminal_id = self.partner_terminal_id
        cloned.txn_date = self.txn_date
        cloned.txn_action_code = self.txn_action_code
        cloned.txn_classification_code = self.txn_classification_code
        cloned.settlement_date = self.settlement_date
        cloned.txn_value = self.txn_value
        cloned.txn_points = self.txn_points
        cloned.earn_ratio = self.earn_ratio
        cloned.burn_ratio = self.burn_ratio
        cloned.reason = self.reason
        cloned.save()
        return cloned

class PointsItems(models.Model):
    points_header = models.ForeignKey(PointsHeader)
    order_item = models.ForeignKey('orders.OrderItem')
    quantity = models.IntegerField(max_length=10)
    department_code = models.IntegerField(max_length=20)
    department_name = models.CharField(max_length=100)
    item_amount = models.IntegerField(max_length=10)
    article_id = models.CharField(max_length=20)
    action_code = models.CharField(max_length=20)
    status = models.CharField(max_length=10, default='FRESH')


class CitiBankTraceNumber(models.Model):
    payment_attempt = models.OneToOneField(PaymentAttempt)

    def __unicode__(self):
        return "CitiBank Trace Number: %s" % self.id

    @property
    def trace_number(self):
        if self.id:
            if not (self.id % 999999):
                return "999999"
            else:
                return "%06.0f" % (self.id % 999999,)
        else:
            return None


class Refund(models.Model):
    """
    Table to store the refunds given to each order
    """
    order = models.ForeignKey('orders.Order', related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=(
        ('open','Open'),
        ('failed','Failed'),
        ('closed','Closed')), default='open')
    notes = models.TextField(null=True, blank=True)
    opened_by = models.ForeignKey('users.Profile', related_name='+')
    closed_by = models.ForeignKey('users.Profile', null=True, blank=True, related_name='+')

    InvalidOperation = type('InvalidOperation', (Exception,), {})
    InsufficientData = type('InsufficientData', (Exception,), {})

    def index(self, **kw):
        ''' Indexes the refund object in solr '''
        from utils import solrutils 
        refund_doc = self.get_refund_solr_doc()

        order_doc = kw.get('order_doc')
        if not order_doc:
            order_doc = self.order.get_order_solr_doc()

        refund_doc.update(order_doc)
        refund_doc['doc_type'] = 'refund'
        refund_doc['unique_key'] = '%s%s' % (refund_doc['doc_type'], self.id)

        solrutils.order_add_data(refund_doc)

    def get_refund_solr_doc(self):
        refund_doc = {
            'order_id': self.order.id,
            'doc_type': 'refund',
            'refund_pk': self.id,
            'refund_amount': '%.2f' % self.amount,
            'refund_status': self.status,
            'refund_opened_by_id': self.opened_by_id,
            'refund_created_on': self.created_on,
            'refund_modified_on': self.modified_on,
            'refund_notes': self.notes or '',
            }

        if self.closed_by_id:
            refund_doc['refund_closed_by_id'] = self.closed_by_id

        return refund_doc
    
    def move_refund_state(self, request, **kwargs):
        agent = kwargs.get('agent')
        data = kwargs.get('data',{})
        new_state = kwargs.get('new_state')
        o_log = kwargs.get('order_log')

        amount = data.get('amount')
        notes = data.get('notes')
        
        from orders.models import OrderLog
        if not o_log:
            o_log = OrderLog(order=self.order, profile=agent, action='refund')

        refund_log = RefundLog(refund=self)

        valid_states = []
        if self.status.lower() == 'open':
            valid_states = ['closed','failed']
        
        if new_state:
            if new_state not in valid_states:
                raise self.InvalidOperation
            if not amount:
                raise self.InsufficientData
            self.amount = amount
            refund_log.amount = amount
            self.notes = notes
            self.status = new_state
            refund_log.status = new_state
            refund_log.notes = notes
            if new_state in ['closed','failed']:
                self.closed_by = agent
            self.save()
            
            o_log.save()
            refund_log.order_log = o_log
            refund_log.save()
        return
models.signals.post_save.connect(indexer.post_save_handler, sender=Refund)


class RefundItem(models.Model):
    refund = models.ForeignKey(Refund, related_name='refund_items')
    order_item = models.ForeignKey('orders.OrderItem')
    qty = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ('refund', 'order_item')


class RefundLog(models.Model):
    refund = models.ForeignKey(Refund, related_name='refund_log')
    order_log = models.OneToOneField('orders.OrderLog', related_name='refund_log')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    notes = models.TextField(null=True, blank=True, default=None)
    
    def get_class_name(self):
        return 'RefundLog'

class StoreValue(models.Model):
    ''' Store Credit limits for an exchanged order '''
    profile = models.OneToOneField('users.Profile')
    credit_available = models.DecimalField(max_digits=12, decimal_places=2)

class StoreValueLog(models.Model):
    store_value = models.ForeignKey(StoreValue)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
