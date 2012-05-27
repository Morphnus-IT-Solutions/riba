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

from catalog.models import Product
def main():
    counter = 0
    total = Product.objects.count()
    f = '{:>%s}' % len(str(total))
    for product in Product.objects.iterator():
       product.update_solr_index()
       counter += 1
       sys.stderr.write("\rindexed: %s of %s" % (
           f.format(counter),
           f.format(total))
           )
       sys.stderr.flush()
    sys.stderr.write("\n")

if __name__ == '__main__':
    main()
