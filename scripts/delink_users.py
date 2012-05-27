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

from users.models import *
from integrations.fbapi import users as apiuser, orders, fbapiutils



ls = [u'dead2kbirth@gmail.com', u'durgavajhula@gmail.com', u'bhaveshtalera@yahoo.com', u'martinjkochumury@gmail.com', u'mitesh_jain_mba@yahoo.com', u'Shano.S@rediffmail.com', u'taurusblues@gmail.com', u'manish.gaur38@yahoo.com', u'phindupur@yahoo.com', u'patwaam@gmail.com', u'shwetaranjan26@rediffmail.com', u'kr_dhanani113@yahoo.com', u'nangaliavinay@hotmail.com', u'patle.nitin@gmail.com', u'pritbhanot@in.com', u'ganesh.sh@saint-gobain.com', u'tarun_samridhi@rediffmail.com', u'findkshp@live.com', u'raviparwal@hotmail.com', u'babugoma@mailinator.com', u'a_pundhir@indiatimes.com', u'shahkr1@yahoo.com', u'sudhirjs@sify.com', u'a.bhambhani@rediffmail.com', u'vijay.panwar@gmail.com', u'saamrocks@gmail.com', u'rajibk2008@gmail.com', u'nishantdhawan@gmail.com', u'stanzin.pradhan@gmail.com', u'gowri.dgr@gmail.com', u'jeetmakhijani@rediff.com', u'somparnaxsarkar@gmail.com', u'sam.manchali@gmail.com', u'kasia_wyszynska@o2.pl', u'sylvesterdomingo@gmail.com', u'vsowmyanarayanan@alkhaliji.com', u'skt51125@hotmail.com', u'yashwantkambli@gmail.com', u'dixitmadhav907@gmail.com', u'chandramoulys1@gmail.com', u'saurabhtiwari1982@gmail.com', u'luizdegomez@gmail.com', u'medha.chugh23@gmail.com', u'pktcontacts@gmail.com', u'abcd@hotmail.com', u'psudhakar23@gmail.com', u'bp_201@hotmail.com', u'crmuk1@gmail.com', u'ad.bs@gm.com', u'rhlmjn@gmail.com', u'manojarunkumar1984@gmail.com', u'khan.reshmaa@gmail.com', u'simrit.khurana@nielsen.com', u'roshanlaluk@yahoo.co.uk', u'hrithik_yadav@rediffmail.com', u'ashlesh.pareek25@gmail.com', u'dhaivatrshah@gmail.com', u'luvug@indiatimes.com', u'noida@ymail.com', u'vaasu.devarala@gmail.com', u'ratishvaid@yahoo.in', u'rakeshh29@rediffmail.com', u'abhirde@gmail.com', u'atulpost@gmail.com', u'jerinmathewk@gmail.com', u'lawlegit@yahoo.com', u'sh_pande@yahoo.co.in', u'anilpillai78@yahoo.com', u'neil.redbull@gmail.com', u'garf_sj@yahoo.com', u'yugandhar2k6@gmail.com', u'smadhu1979@gmail.com', u'gaurav299@rediffmail.com', u'bp_rahul@yahoo.com', u'yugpurush02@hotmail.com', u'rmaratha9@gmail.com', u'madhok22@yahoo.com', u'jeyanthisjeyanthi@yahoo.co.in', u'aaaaa@j.com', u'amusementbd@in.com', u'fareedansari@indiatimes.com', u'gajarch123@rediffmail.com', u'anjitha.bit@gmail.com', u'kishanhv@yahoo.co.in', u'0000000@gmail.com', u'vainavee@yahoo.co.in', u'desaicm@yahoo.com', u'gudwani.gaurav@gmail.com', u'vijay.ingulkar1418@gmail.com', u'mmanish4@hotmail.com', u'vijaymalhotra865@rediffmail.com', u'rvs_1101@yahoo.com', u'www@ww.com', u'000000000@00.com', u'sanshet1@rediffmail.com', u'teresa.chettiar@yahoo.co.in', u'sani.maheshbabu@bt.co.in.com', u'mohd.masood4u@gmail.com', u'aseem95@rediff.com', u'kiranmp2003@gmail.com', u'ravikantjagdale04@gmail.com', u'ras8477@gmail.com', u'yogesh.mujumdar@gmail.com', u'manojna.perumalla1@gmail.com', u'vishakadishakha_dasu@yahoo.com', u'prasant_chet0209@yahoo.co.in', u'diyuti@techmahindra.com', u'bunty.jayant123@gmail.com', u'madhu0476@yahoo.co.in', u'innocenttanvi@gmail.com', u'sheven@rediffmail.com', u'asdfs@ffsddds.com', u'rinky4840@yahoo.co.in', u'rajupatil1947@rediffmail.com', u'arun.jhunjhunwala@gmail.com', u'bhatiaamol@yahoo.com', u'rawthers@gmail.com', u'janvi098@gamil.com', u'uselesspop@ezone1.com', u'sudhikumar@gmail.com', u'lakara.alka@gmail.com', u'dummy@yahoo.com', u'fuckoff@NIGGER.COM', u'rajeshv.cv@gmail.com']

for email in ls:
    e = Email.objects.get(email=email)
    #print e._meta.get_all_related_objects()
    e.delete()
