import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import xlrd
from catalog.models import Tag, ProductTags, SellerRateChart
from django.template.defaultfilters import slugify

wb = xlrd.open_workbook('/home/saumil/tinla/feeds/data/futurebazaar/new_clearance_products.xls')
count,heading_map = 0,{}
s = wb.sheet_by_index(0)
for col in range(s.ncols):
    heading_map[s.cell(0,col).value.lower().encode('ascii','ignore')] = col
    
for row_num in range(1,s.nrows):
    row = s.row(row_num)
    
    if row[heading_map['article id']].ctype in (2,3):
        article_id = str(int(row[heading_map['article id']].value))
    else:
        article_id = str(row[heading_map['article id']].value)

    tag_label = str(row[heading_map['tag']].value.strip())
    tag_value = slugify(tag_label)

    src = SellerRateChart.objects.filter(article_id=article_id)
    if src:
        src = src[0]
        try:
            tag = Tag.objects.using("default").get(tag=tag_value, type = "clearance")
        except Tag.DoesNotExist:
            tag = Tag(tag=tag_value, display_name=tag_label, type = "clearance")
            tag.save(using="default")

        try:
            p = ProductTags.objects.using("default").get(tag=tag, type="new_clearance_sale", product=src.product)
        except ProductTags.DoesNotExist:
            p = ProductTags(tag=tag, type="new_clearance_sale", product=src.product)
            p.save(using='default')
        src.product.update_solr_index()
