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

from lists.models import List, ListItem
from catalog.models import SellerRateChart

list_id = 3426
client_id = 5
list = List.objects.get(id=list_id, type="promotions")

skus = """2590740
2590748
2590744
2590741
2590749
2590745
2590742
2590750
2590746
2590743
2590751
2590747
2590652
2590668
2590656
2590700
2590784
2590780
2590716
2590756
2590757
2590758
2590759
2590688
2590788
2590664
2590764
2590768
2590704
2590708
2590752
2590772
2590736
2590660
2590672
2590712
2590732
2590728
2590692
2590776
2590680
2590684
2590676
2590760
2590696
2590669
2590657
2590701
2590653
2590785
2590781
2590717
2590689
2590789
2590665
2590765
2590769
2590705
2590709
2590753
2590773
2590737
2590661
2590673
2590713
2590733
2590729
2590693
2590777
2590681
2590685
2590677
2590761
2590697
2590670
2590658
2590702
2590654
2590786
2590782
2590718
2590690
2590790
2590666
2590766
2590770
2590706
2590710
2590754
2590774
2590738
2590662
2590674
2590714
2590734
2590730
2590694
2590778
2590682
2590686
2590678
2590762
2590698
2590671
2590659
2590703
2590655
2590787
2590783
2590719
2590691
2590791
2590667
2590767
2590707
2590771
2590711
2590755
2590775
2590739
2590663
2590675
2590715
2590735
2590679
2590731
2590695
2590779
2590683
2590687
2590763
2590699
2590720
2590724
2590721
2590725
2590722
2590726
2590723
2590727""".split("\n")

msgs = []
count = 0

for s in skus:
    count += 1
    try:
        src = SellerRateChart.objects.get(sku=s, seller__client=client_id)
    except Exception,e:
        msgs.append("ERROR @ row: %s for SKU: %s -- %s" % (count, s, repr(e)))

count = 0
if msgs:
    for msg in msgs:
        print msg
else:
    for s in skus:
        count += 1
        listitem = ListItem(list=list)
        src = SellerRateChart.objects.get(sku=s, seller__client=client_id)
        listitem.sku = src
        listitem.sequence = count
        listitem.status = 'active'
        listitem.save()
        msgs.append("SKU added: %s" % s)
    for msg in msgs:
        print msg
