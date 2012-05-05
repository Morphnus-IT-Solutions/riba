from django.db import models

class Complaint(models.Model):
    CATEGORY_TAT_MAP = {'requests - add': 1,
        'requests - can': 1,
        'requests -pr': 7,
        'requests rep': 7,
        'open orders - ons': 5,
        'orders not in SAP - onf': 2,
        'orders not in SAP - se': 2,
        'orders not shipped - dis': 2,
        'orders not shipped - whs': 2,
        'orders not shipped - ps': 4,
        'orders not delivered - os': 4,
        'orders not delivered - rto': 2,
        'orders not delivered - pod': 5,
        'orders not delivered - oct': 7,
        'Product issue - pd': 7,
        'Product issue - wpd': 7,
        'others - gv': 2,
        'others - oth': 4,
        'payment / refund lost - pay': 2,
    }

    CATEGORY_CHOICES = ( 
        ('requests - add','Requests - ADD'),
        ('requests - can','Requests - CAN'),
        ('requests -pr','Requests - PR'),
        ('requests rep','Requests REP'),
        ('open orders - ons','Open Orders - ONS'),
        ('orders not in SAP - onf','Orders not in SAP - ONF'),
        ('orders not in SAP - se','Orders not in SAP - SE'),
        ('orders not shipped - dis', 'Orders not Shipped - DIS'),
        ('orders not shipped - whs', 'Orders not Shipped - WHS'),
        ('orders not shipped - ps', 'Orders not Shipped - PS'),
        ('orders not delivered - os', 'Orders not Delivered - OS'),
        ('orders not delivered - rto', 'Orders not Delivered - RTO'),
        ('orders not delivered - pod', 'Orders not Delivered - POD'),
        ('orders not delivered - oct', 'Orders not Delivered - OCT'),
        ('Product issue - pd', 'Product Issue - PD'),
        ('Product issue - wpd', 'Product Issue - WPD'),
        ('others - gv', 'Others - GV'),
        ('others - oth', 'Others - OTH'),
        ('payment / refund lost - pay', 'Payment / Refund Lost - PAY'))
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('followup','Followup'),
        ('closed','Closed'))
    
    LEVEL_CHOICES = (
    ('green','Green'),
    ('blue','Blue'),
    ('yellow','Yellow'),
    ('orange','Orange'),
    ('red','Red'))
    
    SOURCE_CHOICES = (
    ('email','Email'),
    ('chat','Chat'),
    ('call','Call'),
    ('institutional','Institutional'))

    order = models.ForeignKey('orders.Order', blank=True, null=True, related_name='order_complaints')
    products  = models.ManyToManyField('catalog.Product', blank=True, null=True, related_name='product_complaint')
    user = models.ForeignKey('users.Profile', related_name='user_complaints')
    status = models.CharField(max_length=15,blank=True, null=True, db_index=True, choices=STATUS_CHOICES)
    category = models.CharField(max_length=50,blank=True, null=True, db_index=True, choices=CATEGORY_CHOICES)
    level = models.CharField(max_length=15, null=True, blank=True, db_index=True, choices=LEVEL_CHOICES)
    source = models.CharField(max_length=20, null=True, blank=True, db_index=True, choices=SOURCE_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    moved_to_followup = models.DateTimeField(null=True, blank=True)
    closed_on = models.DateTimeField(blank=True, null=True)
    TAT = models.DateTimeField(blank=True, null=True)
   
class Update(models.Model):
    complaint = models.ForeignKey(Complaint, related_name='updates')
    category = models.CharField(max_length=50,blank=True, null=True)
    level = models.CharField(max_length=20,blank=True, null=True)
    notes = models.TextField(blank=True, null=True, default=None)
    added_by = models.ForeignKey('users.Profile', blank=True, null=True, related_name='+')
    timestamp = models.DateTimeField(auto_now_add=True)
