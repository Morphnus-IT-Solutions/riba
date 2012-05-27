from django.db import models

# Create your models here.
class WhiteLabelStore(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    # Template customizations
    header = models.CharField(max_length=20, choices=(
        ('none','Do not show header'),
        ('custom','Use customized header')),
        default = 'none',
        help_text = 'Customized header will require a custom template')
    footer = models.CharField(max_length=20, choices=(
        ('none','Do not show footer'),
        ('custom','Use customized footer')),
        default = 'none',
        help_text = 'Customized footer will require a custom template')
    order_on_phone = models.CharField(max_length=20, choices=(
        ('none','Do not show order on phone'),
        ('custom','Show customized order on phone')),
        default = 'none',
        help_text = 'Custom order on phone will require a custom template')

    # Home page customizations
    home_page = models.CharField(max_length=200,
        help_text = 'Canned url for the home page of the store')

    # Browse page customizations
    category_specific_filters = models.CharField(max_length=20, choices=(
        ('hide', 'Hide category specific filters'),
        ('show', 'Show category specific filters')),
        default = 'hide')
    brand_filter = models.CharField(max_length=20, choices=(
        ('hide', 'Hide brand filter'),
        ('show', 'Show brand filter')),
        default = 'hide')
    category_filter = models.CharField(max_length=20, choices=(
        ('hide', 'Hide category filter'),
        ('show', 'Show category filter')),
        default = 'hide')
    breadcrumb = models.CharField(max_length=20, choices=(
        ('hide','Hide breadcrumb'),
        ('show','Show breadcrumb')),
        default='hide')

    # Product page customizations
    brand_link = models.CharField(max_length=20, choices=(
        ('hide','Hide brand link'),
        ('show','Show brand link')),
        default = 'hide')
    sold_by = models.CharField(max_length=20, choices=(
        ('hide','Hide sold by'),
        ('show','Show sold by')),
        default = 'hide')
    similar_products = models.CharField(max_length=20, choices=(
        ('hide','Hide similar products'),
        ('show','Show similar products')),
        default = 'hide')

    # Shipping page customizations
    delivery_instructions = models.CharField(max_length=20, choices=(
        ('hide','Hide delivery info'),
        ('show','Show delivery info')),
        default = 'show')
    gift_message = models.CharField(max_length=20, choices=(
        ('hide','Hide gift message'),
        ('show','Show gift message')),
        default = 'show')
