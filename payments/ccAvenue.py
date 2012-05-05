import zlib
import logging

log = logging.getLogger('request')


__workingKey = '0je8kkhlysr3dfp1ynqkxf5vgqyuhdz8'
__merchantId = 'M_fbril_4674'
__action_url = 'https://www.ccavenue.com/servlet/new_txn.PaymentIntegration'

def getMerchantId():
    return __merchantId

def getWorkingKey():
    return __workingKey

def getActionUrl():
    return __action_url

def getChecksum(order_id, amount, redirectUrl):
    chkstr = __merchantId + '|' + str(order_id) + '|' + str(amount) + '|' + redirectUrl + '|' + __workingKey
    adler = 1
    checksum = adler32(adler, chkstr)
    #log.info('request','info','generated checksum ' + str(checksum))
    return checksum

def veriyChecksum(order_id, amount, auth_desc, checksum):
    chkstr = __merchantId + '|' + str(order_id) + '|' + str(amount) + '|' + auth_desc + '|' + __workingKey
    adler = 1
    computed_cheksum = adler32(adler, chkstr)
    log.info('request','info','matching checksums ' + str(computed_cheksum) + ':' + str(checksum))
    if computed_cheksum == checksum:
        return True
    else:
        return False

def testChecksum():
    print getChecksum('5e101b0cff7bba1b0294d185fb644c5e', 1000, 'http://www.chaupaati.in/post/payment_confirmation')

def adler32(adler, str_pattern):
    return customAdler32(adler, str_pattern)

def customAdler32(adler,str_pattern):
    '''creates checksum'''
    # algo in php
    '''$BASE =  65521 ;

        $s1 = $adler & 0xffff ;
        $s2 = ($adler >> 16) & 0xffff;
        for($i = 0 ; $i < strlen($str) ; $i++)
        {
                $s1 = ($s1 + Ord($str[$i])) % $BASE ;
                $s2 = ($s2 + $s1) % $BASE ;
                        //echo "s1 : $s1 <BR> s2 : $s2 <BR>";

        }
         return leftshift($s2 , 16) + $s1;
    '''
    base = 65521
    s1 = adler & 0xffff
    s2 = (adler >> 16) & 0xffff
    for i in range(len(str_pattern)):
        s1 = (s1 + ord(str_pattern[i])) % base
        s2 = (s2 + s1) % base
    return (s2<<16) + s1

def createCCAvenuePaymentForm(request, **kwargs):
    bank = kwargs.get('bank')
    order = kwargs.get('order')
    payment_attempt = kwargs.get('payment_attempt')
    redirect_url = kwargs.get('redirect_url')
    
    user = order.user
    form = {}
    try:
        delivery_address = order.get_address(request, type='delivery').address
        billing_address = order.get_address(request, type='billing').address
        
        checksum = getChecksum(payment_attempt.transaction_id, payment_attempt.amount, redirect_url)
        
        form['action'] = getActionUrl()  
        fields = {
                'Merchant_Id': getMerchantId(),
                'Amount': '%s' % payment_attempt.amount,
                'Order_Id': payment_attempt.transaction_id,
                'Redirect_Url': redirect_url, 
                'Checksum': str(checksum),
                'billing_cust_name':user.full_name,
                'billing_cust_address':billing_address.address,
                'billing_cust_country':'India',
                'billing_cust_state':billing_address.state.name,
                'billing_zip_code':billing_address.pincode,
                'billing_cust_tel':user.get_primary_phones()[0].phone if user.get_primary_phones() else '',
                'billing_cust_email':user.get_primary_emails()[0].email if user.get_primary_emails() else '',
                'billing_cust_city':billing_address.city,
                'billing_cust_zip_code':billing_address.pincode,
                'billing_cust_notes':order.get_id(),
                'delivery_cust_name':delivery_address.first_name,
                'delivery_cust_address':delivery_address.address,
                'delivery_cust_country':'India',
                'delivery_cust_state':delivery_address.state.name,
                'delivery_cust_city':delivery_address.city.name,
                'delivery_zip_code':delivery_address.pincode,
                'delivery_cust_tel':delivery_address.phone,
                'cardOption':'netBanking',
                'netBankingCards':bank,
                'Merchant_Param':payment_attempt.transaction_id,
                }
        form['fields'] = fields
    
    except Exception, e:
        pass
    return form


def create_request(request, **kwargs):
    bank = kwargs.get('bank')
    order = kwargs.get('order')
    payment_attempt = kwargs.get('payment_attempt')
    redirect_url = kwargs.get('redirect_url')
            
    return createCCAvenuePaymentForm(request, bank=bank, payment_attempt=payment_attempt, order=order, redirect_url=redirect_url)
#def process_response(request, **kwargs):
