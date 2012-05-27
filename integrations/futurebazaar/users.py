from integrations.futurebazaar import fbapiutils as futils
from lxml import etree

def get_user_by_mobile(mobile):
    pass

def get_user_by_login(login):
    print '@@calling fuser', login
    profile_id_client = futils.get_client('user', 'getProfileId')
    profile_id = profile_id_client.service.getProfileId(login)

    profile_client = futils.get_client('user', 'getProfile')
    profile_xml = profile_client.service.getProfile(profile_id)

    xml = etree.fromstring(profile_xml)
    ns = {
            'user': 'http://www.atg.com/ns/UserProfiles/user',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'enc': 'http://schemas.xmlsoap.org/soap/encoding/',
            }
    first_name = futils.xpath_s(xml, ns, '/user:user/user:user.firstName', '')
    last_name = futils.xpath_s(xml, ns, '/user:user/user:user.lastName', '')
    mobile = futils.xpath_s(xml, ns, '/user:user/user:user.mobileNumber', '')
    email = futils.xpath_s(xml, ns, '/user:user/user:user.email', '')
    print profile_id, first_name, last_name, mobile, email
    return profile_id

def get_user_by_email(email):
    pass

def create_user(user):
    pass

def set_contact_info(user):
    pass

def update_user(user):
    pass
