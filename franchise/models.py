from django.db import models
# Create your models here.

class Network(models.Model):
    user = models.OneToOneField('auth.User',null=True, blank=True)
    name = models.CharField(max_length=200, unique=True)
    share = models.FloatField(max_length=30,blank=False,null=False)
    parent_network = models.ForeignKey('self', related_name='parent_Network',blank=True,null=True)
    clients = models.ForeignKey('accounts.Client', null=True, blank=True)#client = models.ForeignKey(Client)
    
    def __unicode__(self):
        return self.name

class Franchise(models.Model):
    user = models.OneToOneField('auth.User')
    network = models.ForeignKey(Network,blank=False,null=False)
    dealer_id = models.CharField(max_length=20, blank=False, null=False, default="Itzdl20000")
    dealer_code = models.CharField(max_length=20, blank=False, null=False, default="D000032000")
    role = models.CharField(max_length=30, db_index=True, choices=(
        ('fb','Future Bazaar'),
        ('franchises','Franchises'),
        ('network','Networks')),blank=True,null=True, default="franchises")
    is_active = models.BooleanField(('active'), default=True, help_text=("Network can deactivate franchise using this field. Default - Active."))
    
    def __unicode__(self):
        return self.user.username

class MerchantTypeKey(models.Model):
    percentage = models.FloatField(max_length=200, blank=False,null=False, unique=True)
    key = models.CharField(max_length=100, blank=False,null=False, unique=True)
    network = models.ForeignKey(Network,blank=False,null=False)
    
    def __unicode__(self):
        return '%s - %s (%s)' % (self.percentage, self.key, self.network)

class CommisionOn(models.Model):
    class Meta:
        unique_together = ('network','seller_rate_chart')

    network = models.ForeignKey(Network,blank=False,null=False)
    commision = models.ForeignKey(MerchantTypeKey,blank=False,null=False)
    seller_rate_chart = models.ForeignKey('catalog.SellerRateChart', null=True)
    timestamp = models.DateTimeField(blank=True,null=True, auto_now_add=True)

    def __unicode__(self):
        return self.seller_rate_chart.sku #network.name

class FranchiseOrder(models.Model):
    franchise = models.ForeignKey(Franchise,blank=False,null=False)
    order = models.ForeignKey('orders.Order', null=False, blank=False)
    franc_commission_amnt = models.FloatField(max_length=50,blank=True,null=True, db_index=True)
    network_commission_amnt = models.FloatField(max_length=50,blank=True,null=True, db_index=True)
    booking_timestamp = models.DateTimeField(blank=True,null=True, verbose_name='Booking Date')
    confirming_timestamp = models.DateTimeField(blank=True,null=True, verbose_name='Confirming Date')
    
    def __unicode__(self):
        return str(self.order.id)

class FranchiseCommissionOnItem(models.Model):
    franchise_order = models.ForeignKey(FranchiseOrder,blank=False,null=False)
    order_item = models.ForeignKey('orders.OrderItem', null=False, blank=False)
    franc_commission_amnt = models.FloatField(max_length=50,blank=True,null=True)
    network_commission_amnt = models.FloatField(max_length=50,blank=True,null=True)
    
    def __unicode__(self):
        return str(self.order_item.id)

'''
class CommisionPriorities(models.Model):
    name = models.CharField(max_length=200)
    priority = models.CharField(max_length=5, unique=True)

    def __unicode__(self):
        return self.name

class FranchiseCommision(models.Model):
    franchise = models.ForeignKey(Franchise,blank=False,null=False)
    commissionAmnt = models.FloatField(max_length=50,blank=True,null=True)
    franchiseOrder = models.ForeignKey(FranchiseOrder,blank=True,null=True)
    
    def __unicode__(self):
        return self.franchise.user.username

class NetworkCommision(models.Model):
    network = models.ForeignKey(Network,blank=False,null=False)
    commissionAmnt = models.FloatField(max_length=50,blank=True,null=True)
    franchiseOrder = models.ForeignKey(FranchiseOrder,blank=True,null=True)

    def __unicode__(self):
        return self.network.name
        
    
    #commision_priorities = models.ForeignKey(CommisionPriorities,blank=True,null=True)    
    #commision = models.FloatField(max_length=30,blank=False,null=False)
    #referencing_id = models.CharField(max_length=50)
    #commisionType = models.CharField(max_length=30, choices=(
    #    ('fixed','Fixed Commision'),
    #    ('percentage','Percentage Commision')),blank=True,null=True)
    
'''
