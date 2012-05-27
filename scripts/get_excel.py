
#!/usr/bin/python

import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)
import xlrd
from locations.models import *

book = xlrd.open_workbook("/home/saumil/tinla/excel.xls") #Open excel file
s=book.sheet_by_index(0)    #Read data from file
heading_map = {}
return_dict = {}
for col in range(s.ncols):
	heading_map[s.cell(0,col).value.lower()] = col
for row_num in range(1,s.nrows):
	row = s.row(row_num)
	sku = str(int(row[heading_map['sku id']].value))
	lob = str(row[heading_map['lob']].value.encode('ascii', 'ignore'))
	sub_lob = str(row[heading_map['sub lob']].value.encode('ascii', 'ignore'))
	return_dict[sku]={'lob':lob, 'sub_lob':sub_lob}
print return_dict
