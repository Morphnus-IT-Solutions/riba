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

from django.contrib.auth.models import *

usernames_list = [
('8082293347', 'Savita Kamble'),
('8976204519', 'Azam Shaikh'),
('9594791122', 'Tushar Bhuvad'),
('9833037406', 'Kashif Ansari'),
('9930521699', 'Aditya Pathak'),
('aartip', 'Aarti Patil'),
('akanksha.mishra@futuregroup.in', 'Akanksha Mishra'),
('amit.karanje.fb', 'Amit Karanje'),
('anandkumar.nagesh.lokre.fb', 'Anandkumar Lokre'),
('asif', 'Asif Shaikh'),
('brijesh.waghela', 'Brijesh Waghela'),
('Brijesh.Waghela@futuregroup.in', 'Brijesh Waghela'),
('dinesh.mudhliyar@futuregroup.in', 'Dinesh Mudhliyar'),
('farhana.kazi@futuregroup.in', 'Farhana Kazi'),
('franklint', 'Franklin Thomas'),
('gaurav.suryawanshi.fb', 'Gaurav Suryawanshi'),
('goldie.creado@gmail.com', 'Goldie Creado'),
('grishmat', 'Grishma Talati'),
('haris.pathan1.fb', 'Haris Pathan'),
('harshada.kamble.fb', 'Harshada Kamble'),
('jitendra.tripathi@futuregroup.in', 'Jitendra Tripathi'),
('kais', 'kais Birajdar'),
('kunal.chavan.fb', 'Kunal Chavan'),
('laxmip', 'Laxmi Muthupadi'),
('leena.pachare@futuregroup.in', 'Leena Pachare'),
('mareshlinga.kattimani.fb', 'Mareshlinga Kattimani'),
('mohd.elyas.fb', 'Mohamed Iliyas'),
('Muin', 'Muin Abbas'),
('nasreen.siddiqui', 'Nasreen Siddiqui'),
('nazia.afroz@futuregroup.in', 'Nazia Afroz'),
('nikhil.vaity', 'Nikhi Vaity'),
('Nikhil.vaity@futuregroup.in', 'Nikhi Vaity'),
('nikunj.shah.fb', 'Nikunj Shah'),
('Raheel.Ansari@futuregroup.in', 'Raheel Ansari'),
('rahil', 'Rahil Ansari'),
('rahil.cb', 'Rahil Shaikh'),
('Rahil.Shaikh@futuregroup.in', 'Rahil Shaikh'),
('sachin', 'Sachin Chikane'),
('sachin.chikane@futuregroup.in', 'Sachin Chikane'),
('sakshi.kamerkar', 'Sakshi Kamerkar'),
('salman.maniar.fb', 'Salman Maniar'),
('sameer.virani.fb', 'Sameer Virani'),
('shama.mukri.fb', 'Shama Mukri'),
('sohela.noora@futuregroup.in', 'Sohela Noora'),
('sujeet.dubey', 'Sujeet Dubey'),
('Sujeet.Dubey@futuregroup.in', 'Sujeet Dubey'),
('tanuj.singh.fb', 'Tanuj Singh'),
('ubaid.ibrahim.fb', 'Ubaid Ibrahim'),
('vijay_viju05@yahoo.co.in', 'Vijay Iyer'),
('vinitam', 'Vinita Malusare'),
('vinod.pandey.fb', 'Vinod Pandey'),
('Viraj', 'Viraj Bane'),
('yogita.gaikwad.fb', 'Yogita Gaikwad')
]

for username_tuple in usernames_list:
    username = username_tuple[0]
    name = username_tuple[1]    
    users = User.objects.filter(username=username)
    if users:
        user = users[0]
        user.first_name = name
        user.save()
    else:
        print username, "not saved" 
