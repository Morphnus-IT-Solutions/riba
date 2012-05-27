import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from catalog.models import Tag, ProductTags

pt = ProductTags.objects.select_related('tag').filter(type='clearance_sale')
for d in pt:
    tag_field = '%s-clearance'%d.tag.tag
    try:
        t = Tag.objects.using("default").get(tag=tag_field, type="clearance")
    except Tag.DoesNotExist:
        t = Tag(tag=tag_field, type="clearance")
        t.display_name = d.tag.display_name
        t.save(using='default')
    try:
        p = ProductTags.objects.using("default").get(tag=t, type="new_clearance_sale", product=d.product)
    except ProductTags.DoesNotExist:
        p = ProductTags(tag=t, type="new_clearance_sale", product=d.product)
        p.save(using='default')
    p.product.update_solr_index()
