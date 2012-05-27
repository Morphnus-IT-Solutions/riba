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

import shutil
path1 = "/media/3591C444194B89A6/iksula/large/" #path to large folder
path2 = "/media/3591C444194B89A6/iksula/medium/"# path to medium folder
path3 = "/media/3591C444194B89A6/iksula/small/"#path to small folder
dir_list1 = list(set(os.listdir(path1)))
dir_list2 = list(set(os.listdir(path2)))
dir_list3 = list(set(os.listdir(path3)))

for ele in dir_list1:
    print ele[:-4]
    if not os.path.exists("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4]):
        os.makedirs("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4])
    shutil.copyfile(path1+ele,"/media/3591C444194B89A6/iksula_images/"+ele[:-4]+"/L1.jpg") #path where to place the folders with name as article id

for ele in dir_list2:
    print ele[:-4]
    if not os.path.exists("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4]):
        os.makedirs("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4])
    shutil.copyfile(path2+ele,"/media/3591C444194B89A6/iksula_images/"+ele[:-4]+"/M1.jpg")

for ele in dir_list3:
    print ele[:-4]
    if not os.path.exists("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4]):
        os.makedirs("/media/3591C444194B89A6/iksula_images/%s"%ele[:-4])
    shutil.copyfile(path3+ele,"/media/3591C444194B89A6/iksula_images/"+ele[:-4]+"/T1.jpg")
