from payouts.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from payouts.forms import  *
from orders.models import OrderItem
import calendar
from decimal import Decimal

def home(request):
    payout_home_form = PayoutHomeForm() 
    if request.method == 'POST':
        pass
    response = render_to_response('payout/home.html', 
            {'payout_home_form':payout_home_form},
            context_instance=RequestContext(request))
    return response

def calculate(request):
    if request.method == 'POST':
        payout_home_form = PayoutHomeForm(request.POST)
        if payout_home_form.is_valid():
            seller = payout_home_form.cleaned_data['seller']
            month = payout_home_form.cleaned_data['month']
            year = payout_home_form.cleaned_data['year']
            c = calendar.monthrange(int(year),int(str(month)))
            last_day = c[1]
            gte_date = '%s-%s-01' % (str(year),str(month))
            lte_date = '%s-%s-%s' % (str(year),str(month),last_day)
            order_items = OrderItem.objects.filter(seller_rate_chart__seller=seller,order__payment_realized_on__gte=gte_date,order__payment_realized_on__lte=lte_date,state__in=['confirmed','shipped','delivered',None])

            seller_configurations = SellerConfigurations.objects.get(seller=seller)
            percentage_commission = seller_configurations.percentage_commission
            collected_by = seller_configurations.amount_collected_by
            if collected_by == 'chaupaati':
                pass
            else:
                pass
            #calculate transfer price based on percentage commission
            configurations = Configurations.objects.all()
            service_tax = configurations[0].service_tax / Decimal("100")
            #payout components
            total_sale_price = Decimal(0)
            total_shipping_charges = Decimal(0)
            total_payment_gateway_charges = Decimal(0)
            chaupaati_discount = Decimal(0)
            seller_discount = Decimal(0)
            total_collected_amount = Decimal(0)
            total_applicable_amount = Decimal(0)
            commission_in_amount = Decimal(0)
            gross_payout = Decimal(0)
            chaupaati_commision_invoice = Decimal(0)
            net_payout = Decimal(0)

            seller_payout_details = SellerPayoutDetails.objects.filter(month=month,year=year,seller=seller)
            seller_payout_details.delete(using='default')

            for order_item in order_items:
                #item wise payout details
                total_sale_price += order_item.sale_price
                total_shipping_charges += order_item.shipping_charges
                discount = Decimal("%.15g" % order_item.spl_discount())
                chaupaati_discount += discount
                #seller_discount +=
                #total_payment_gateway_charges += order_item.
                payable_amount = Decimal("%.15g" % order_item.payable_amount())
                total_collected_amount += payable_amount
                total_applicable_amount += ( payable_amount + discount)
                commission_in_amount += (order_item.seller_rate_chart.transfer_price)

                #save payout details for each item
                seller_payout_details = SellerPayoutDetails()
                seller_payout_details.year = year
                seller_payout_details.month = month
                seller_payout_details.order_item = order_item
                seller_payout_details.seller = seller
                seller_payout_details.sale_price = order_item.sale_price
                seller_payout_details.shipping_charges = order_item.shipping_charges
                #seller_payout_details.gateway_charges
                seller_payout_details.chaupaati_discount = Decimal("%.15g" % order_item.spl_discount())
                #seller_payout_details.seller_discount =
                seller_payout_details.collected_amount = Decimal("%.15g" % order_item.payable_amount())
                seller_payout_details.applicable_amount = seller_payout_details.collected_amount + seller_payout_details.chaupaati_discount
                seller_payout_details.commision_amount = order_item.seller_rate_chart.transfer_price
                seller_payout_details.gross_payout = seller_payout_details.collected_amount - seller_payout_details.commission_amount
                seller_payout_details.commission_invoice_amount = seller_payout_details.commission_amount + (seller_payout_details.commission_amount * service_tax)
                seller_payout_details.net_payout = seller_payout_details.applicable_amount - seller_payout_details.commission_invoice_amount
                seller_payout_details.save()


            gross_payout = total_applicable_amount - commission_in_amount
            chaupaati_commision_invoice = commission_in_amount + (commission_in_amount * service_tax)
            net_payout = total_applicable_amount - chaupaati_commision_invoice

            #payout totals
            try:
                seller_payout = SellerPayout.objects.get(month=month,year=year,seller=seller)
                seller_payout.delete(using='default')
                seller_payout = SellerPayout()
            except:
                seller_payout = SellerPayout()
            seller_payout.seller = seller
            seller_payout.month = month
            seller_payout.year = year
            seller_payout.sale_price = total_sale_price
            seller_payout.shipping_charges = total_shipping_charges
            seller_payout.gateway_charges = total_payment_gateway_charges
            seller_payout.chaupaati_discount = chaupaati_discount
            seller_payout.seller_discount = seller_discount
            seller_payout.collected_amount = total_collected_amount
            seller_payout.applicable_amount = total_collected_amount + chaupaati_discount
            seller_payout.commission_amount = commission_in_amount
            seller_payout.gross_payout = gross_payout
            seller_payout.commission_invoice_amount = chaupaati_commision_invoice
            seller_payout.net_payout = net_payout
            seller_payout.save()

            response = render_to_response('payout/details.html',
                    {'seller_payout':seller_payout,
                    'month':month,
                    'year':year,
                    'seller':seller},
                    context_instance = RequestContext(request))
            return response
            
        else:
            response = render_to_response('payout/home.html', 
                    {'payout_home_form':payout_home_form},
                    context_instance=RequestContext(request))
            return response

