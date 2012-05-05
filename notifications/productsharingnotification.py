from notifications.notification import Notification
from notifications.email import Email
from notifications.sms import SMS
from orders.models import  *
from catalog.models import *
from django.template import Context, Template
from django.template.loader import get_template
from utils.utils import *
from django.utils.safestring import mark_safe

class ProductSharingNotification(Notification):
    def __init__(self,seller_rate_chart,profile,*args,**kwargs):
        self.seller_rate_chart = seller_rate_chart
        self.profile = profile

    def fillAttributes(self,seller_rate_chart,profile,body_st, subject_st):
        product = seller_rate_chart.product
        name = "Customer"
        if profile.full_name:
            name = profile.full_name
        if seller_rate_chart.gift_title:
            subject_st['product_name'] = mark_safe("%s + %s" % (product.title, seller_rate_chart.gift_title))
            body_st['product_name'] = mark_safe("%s + %s" % (product.title, seller_rate_chart.gift_title))
        else:
            subject_st['product_name'] = mark_safe(product.title)
            body_st['product_name'] = mark_safe(product.title)
        body_st['customer_name'] = name
        if seller_rate_chart.seller.is_exclusive:
            product_link = seller_rate_chart.get_external_product_link()
        else:
            prefix = "http://www.chaupaati.in/"
            product_link = "%s%s" % (prefix, product.url())
        body_st['product_link'] = product_link
    
    def getNotifications(self):
        notifications = []
        t_body = get_template('products/share_product.email')
        t_sub = get_template('products/share_product_sub.email')
        product_body = {}
        product_sub = {}
        self.fillAttributes(self.seller_rate_chart,self.profile,product_body,product_sub)
        if self.profile.primary_email:
            pemail = Email()
            c_body = Context(product_body)
            c_sub = Context(product_sub)
            pemail.body = t_body.render(c_body)
            pemail.subject = t_sub.render(c_sub)
            pemail.to = self.profile.primary_email
            pemail._from = self.seller_rate_chart.seller.share_product_email #"Chaupaati Bazaar<share@chaupaati.com>"
            images = ProductImage.objects.filter(product=self.seller_rate_chart.product)
            if images:
                thumbnail = images[0]
                pemail.isAttachment = True
                pemail.attachment = thumbnail.image.path
            notifications.append(pemail)
        return notifications
