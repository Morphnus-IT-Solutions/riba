from bl.errors import ComponentError
from django.utils import simplejson

class User:
    '''Represents a search object in the system.
       The field map is a map of the attributes to
       the json keys
    '''

    FIELDS_MAP = {\
            'ID':'id',\
            'MOBILE': 'mobile',\
            'PHONE1': 'phone2',\
            'PHONE2': 'phone3',\
            'NAME': 'name',\
            'EMAIL': 'email',\
            'ADDRESS': 'address',\
            'LOCALITY': 'locality',\
            'LAST_LOCATION': 'lastLocation',\
            'LOCATIONS': 'locations',\
            'DEAL_ALERTS': 'dealAlerts',\
            'CONN_USER_TYPE_PREF': 'connUserTypePref',\
            'CONN_LOCATION_PREF':'connLocationPref',\
            'SECONDARY_LOCATIONS':'secondaryLocations',\
            'TIMESTAMP': 'timestamp',\
            'TYPE': 'type',\
            'DOB': 'dob',\
            'BLOOD_GROUP': 'bloodGroup',\
            'WILL_DONATE_NOW':'willDonateNow',\
            'LAST_DONATED_DATE':'lastDonatedDate',\
            'MODIFICATION_TIME' : 'modificationTime',\
            'CONTACTS_SENT': 'noOfConnections',\
            'NO_OF_LISTINGS': 'noOfListings',\
            'NO_OF_SEARCHES': 'noOfSearches',\
            'BALANCE': 'balance',\
            'UNPAID_CONTACTS': 'unpaidContacts',\
            'UNBILLED_AMOUNT': 'unbilledAmount',\
            'SALT': 'salt',\
            'HAS_PASSCODE':'hasPasscode',\
            'ALERT_PREF':'deliveryPreferences',\
            'SHOP_NAME':'shopName',\
            'SHOP_DESC':'remarks',\
            'SHOW_REFERRAL_OPTION':'showReferralOption',\
            'NO_OF_FEEDBACKS':'noOfFeedbacks',\
            'IS_SUSPENDED':'isSuspended',\
            'ELIGIBLE_FOR_FREE': 'eligibleForFree',\
            'MEDIUM':'medium',\
            'CITY':'city',\
            'PINCODE':'pincode',\
            'STATE':'state',\
            'DELIVERY_NAME':'deliveryName',\
            'DELIVERY_PHONE':'deliveryPhone',\
            'ADDRESS2':'address2',\
            'LOCALITY2':'locality2',\
            'CITY2':'city2',\
            'STATE2':'state2',\
            'PINCODE2':'pincode2',\
            'DELIVERY_NOTES':'deliveryNotes',\
            'GIFT_NOTES':'giftNotes',\
            'OLD_PASSCODE':'oldPasscode',\
            'NEW_PASSCODE':'newPasscode',\
            'CONFIRM_PASSCODE':'confirmPasscode',\
            'GENDER':'gender',\
            'REFERRER':'referrer',\
            'AGE':'age',\
            'LANGUAGES':'languages',\
            'RATING':'rating',\
            'CREDIT_LIMIT':'creditLimit',\
            'WARNINGS':'warnings',\
            'PAYMENT_PREFERENCES':'paymentPreferences',\
            'PAYMENT_DETAILS':'paymentDetails',\
            'IS_BLACKLISTED':'isBlacklisted',\
            'IS_VERIFIED':'isVerified',\
            'REFERRED_USER_DETAILS':'referredUserDetails',\
            'REFERRED_BY_MOBILE':'referredByMobile',\
            'REFERRED_BY_NAME':'referredByName',\
            'REFERRED_USERS':'referredUsers',\
            'PENDING_REFERRAL_COUNT':'pendingReferralCount',\
            'CONNECTION_LOCATION_PREF':'connectionLocationPref',\
            'CONNECTION_USER_TYPE_PREF':'connectionUserTypePref',\
            'CALL_CENTER_AGENT':'callCenterAgent',\
            'COLLECTION_AGENT':'collectionAgent',\
            'MAX_CONTACTS_PER_DAY':'maxContactsPerDay',\
            'OWNER_CONTACTS':'ownerContacts',\
            'SUB_CATEGORIES':'subCategories',\
            'SERVICE_OPTIONS':'serviceOptions',\
            'OWNER_USER_TYPE_PREF':'ownerUserTypePref',\
            'FREE_BUYER_ALERTS':'freeBuyerAlerts',\
            'SUBSCRIPTION_PLANS':'subscriptionPlans',\
            'USER_REFERRALS':'referrals',\
            'DEAL_ALERTS':'dealAlerts',\
            'CATEGORY':'category',\
            'KEYWORDS':'keywords',\
            'COUNTRY':'country',\
            'COUNTRY2':'country2',\
            'LOCK_ACCOUNT_REASON':'lockAccountReason',\
            'SERVICE_CITY_ID':'serviceCityId',\
            'EMAIL2':'email2',\
            'LEAD_EMAIL':'leadEmail',\
            'ORDER_EMAIL':'orderEmail',\
            'NOTIFICATION_EMAIL':'notificationEmail',\
            'PLAN':'plan',\
            'NO_OF_CALLS':'noOfCalls',\
            'OCCUPATION':'occupation',\
            'LAST_SERVICE_LOCATIONS':'lastServiceLocations',\
            'SERVICE_AREA_IDS':'serviceAreaIds',\
            'SERVICE_CITY_IDS':'serviceCityIds',\
            'SERVICE_STATE_IDS':'serviceStateIds',\
            'SERVICE_COUNTRY_IDS':'serviceCountryIds',\
            'SERVICE_LOCALITY_IDS':'serviceLocalityIds',\
            'LOCALITY_ID':'localityId',\
            'LOCALITY_TYPE':'localityType',\
            'LEAD_CONTACT_PREFS':'leadContactPrefs',\
            'ORDER_CONTACT_PREFS':'orderContactPrefs',\
            'NOTIFICATION_CONTACT_PREFS':'notificationContactPrefs',\
            'DEAL_ALERT_CONTACT_PREFS':'dealAlertContactPrefs',\
            'SERVICE_LOCATIONS':'serviceLocations',\
            'SERVICE_LOCALITY':'serviceLocality',\
            'ADDED_BY_BRAND': 'addedByBrand',\
            'ASSOCIATED_TO_BRANDS': 'associatedToBrands',\
            }

    JSON_BLACK_LIST = ['TIMESTAMP','CONTACTS_SENT', 'NO_OF_SEARCHES', 'NO_OF_LISTINGS', 'UNPAID_CONTACTS','UNBILLED_AMOUNT','IS_ACTIVE','BALANCE','MODIFICATION_TIME', 'SALT', 'HAS_PASSCODE', 'LAST_LOCATION', 'NO_OF_FEEDBACKS', 'IS_SUSPENDED', 'ELIGIBLE_FOR_FREE', 'LAST_SERVICE_LOCATIONS']

    def __init__(self, **dict):
        '''Constructs a search instance. Sets the attributes and their default values'''

        # our attribute names are the keys of FIELDS_MAP converted to lower case
        self.id = None
        self.mobile = ''
        self.phone1 = ''
        self.phone2 = ''
        self.name = ''
        self.email = ''
        self.address = ''
        self.blood_group = ''
        self.will_donate_now = False
        self.dob = ''
        self.last_donated_date = ''
        self.locality = ''
        self.city = ''
        self.state = ''
        self.pincode = ''
        self.last_location = ''
        self.locations = []
        self.contacts_sent = 0
        self.is_active = True
        self.type = 'individual'
        self.timestamp = None
        self.modification_time = '' 
        self.no_of_listings = 0
        self.no_of_serches = 0
        self.balance = 0
        self.unpaid_contacts = 0
        self.unbilled_amount = 0
        self.has_passcode = False
        self.salt = ''
        self.deal_alerts = 'neutral'
        self.conn_user_type_pref = ''
        self.conn_location_pref = 0
        self.secondary_locations = [] 
        self.alert_pref = ''
        self.show_referral_option = ''
        self.shop_name = ''
        self.shop_desc = ''
        self.is_suspended = False
        self.eligible_for_free = False
        self.medium = ''
        self.address2= ''
        self.locality2 = ''
        self.city2 = ''
        self.state2 = ''
        self.pincode2 = ''
        self.delivery_name=''
        self.delivery_phone=''
        self.delivery_notes=''
        self.gift_notes=''
        self.old_passcode = ''
        self.new_passcode = ''
        self.confirm_passcode = ''
        self.gender = ''
        self.referrer = ''
        self.age = ''
        self.languages = []
        self.rating = 0
        self.credit_limit = 0
        self.warnings = 0
        self.payment_preferences = ''
        self.payment_details = ''
        self.is_blacklisted = False
        self.is_verified = False
        self.referred_user_details = []
        self.referred_by_mobile = ''
        self.referred_by_name = ''
        self.referred_users = ''
        self.pending_referral_count = 0
        self.connection_location_pref = 0
        self.connection_user_type_pref = ''
        self.call_center_agent = ''
        self.collection_agent = ''
        self.max_contacts_per_day = ''
        self.owner_contacts = False
        self.sub_categories = []
        self.service_options = []
        self.owner_user_type_pref = ''
        self.free_buyer_alerts = False
        self.subscription_plans = ''
        self.user_referrals = 'referrals'
        self.deal_alerts = 'neutral'
        self.category = ''
        self.keywords = ''
        self.country = ''
        self.country2 = ''
        self.lock_account_reason = ''
        self.service_city_id = ''
        self.email2 = ''
        self.lead_email = ''
        self.order_email = ''
        self.notification_email = ''
        self.plan = ''
        self.no_of_calls = 0
        self.occupation = ''
        self.last_service_locations = []
        self.service_city_ids = ''
        self.service_state_ids = ''
        self.service_area_ids = ''
        self.service_country_ids = ''
        self.service_locality_ids = ''
        self.locality_id = ''
        self.locality_type = ''
        self.lead_contact_prefs = ''
        self.order_contact_prefs = ''
        self.notification_contact_prefs = ''
        self.deal_alert_contact_prefs = ''
        self.service_locations = ''
        self.service_locality = ''
        self.added_by_brand = ''
        self.associated_to_brands = []


        # handle no dict
        if not dict:
            dict = {}

        # fill the values from dict
        for key in User.FIELDS_MAP.keys():
            if key in dict.keys():
                setattr(self, key.lower(), dict[key])

    def fromJSONObj(self, jsonObj):
        '''the json keys we understand are the values of the FIELDS_MAP
           the jsonObj parameter is a misnomer. it is a python dict object.
           the naming has been chosen to indicate that this function can
           take the decoded json representation and and construct the instance of search
        '''
        for key in User.FIELDS_MAP.keys():
            jsonKey = User.FIELDS_MAP[key]
            if jsonKey in jsonObj.keys():
                setattr(self, key.lower(), jsonObj[jsonKey])

    def fromJSONStr(self, jsonStr):
        '''takes a json string and constructs a search instance'''
        jsonObj = simplejson.JSONDecoder.decode(jsonStr)
        self.fromJSONObj(jsonObj)

    def toJSONObject(self):
        '''returns a dict'''
        # FIXME we should implement JSON serializable
        o = {}
        blacklist = User.JSON_BLACK_LIST[:]
        try:
            if not self['ID']:
                blacklist.append('ID')
            if not self['SHOW_REFERRAL_OPTION']:
                blacklist.append('SHOW_REFERRAL_OPTION')
            if self['CONN_LOCATION_PREF'] == -1:
                blacklist.append('CONN_LOCATION_PREF')
            if self['CONN_USER_TYPE_PREF'] == 'unknown':
                blacklist.append('CONN_USER_TYPE_PREF')
            if not self['LAST_DONATED_DATE']:
                blacklist.append('LAST_DONATED_DATE')
            if not self['SERVICE_LOCALITY']:
                blacklist.append('SERVICE_LOCALITY')
            if not self['DOB']:
                blacklist.append('DOB')

            if (not self['NEW_PASSCODE']) or (not self['CONFIRM_PASSCODE']):
                blacklist.append('NEW_PASSCODE')
                blacklist.append('CONFIRM_PASSCODE')

            if not self['OLD_PASSCODE']:
                blacklist.append('OLD_PASSCODE')
            if not self['SERVICE_LOCATIONS']:
                blacklist.append('SERVICE_LOCATIONS')
            if not self['SERVICE_CITY_ID']:
                blacklist.append('SERVICE_CITY_ID')
            if not self['MAX_CONTACTS_PER_DAY']:
                blacklist.append('MAX_CONTACTS_PER_DAY')
            if not self['OCCUPATION']:
                blacklist.append('OCCUPATION')
            if not self['SERVICE_AREA_IDS']:
                blacklist.append('SERVICE_AREA_IDS')
            if not self['SERVICE_CITY_IDS']:
                blacklist.append('SERVICE_CITY_IDS')
            if not self['SERVICE_STATE_IDS']:
                blacklist.append('SERVICE_STATE_IDS')
            if not self['SERVICE_COUNTRY_IDS']:
                blacklist.append('SERVICE_COUNTRY_IDS')
            if not self['SERVICE_LOCALITY_IDS']:
                blacklist.append('SERVICE_LOCALITY_IDS')
            if not self['LOCALITY_ID']:
                blacklist.append('LOCALITY_ID')
            if not self['LOCALITY_TYPE']:
                blacklist.append('LOCALITY_TYPE')
            if not self['ADDED_BY_BRAND']:
                blacklist.append('ADDED_BY_BRAND')
            if not self['ASSOCIATED_TO_BRANDS']:
                blacklist.append('ASSOCIATED_TO_BRANDS')
        except Exception, e:
            print '##Error' + repr(e) + 'attribute:' 

        for key in User.FIELDS_MAP.keys():
            if key not in blacklist:
                try:
                    o[User.FIELDS_MAP[key]] = self[key]
                except Exception, e:
                    print '##Error' + repr(e) + 'field:' + key
        return o

    def toJSONStr(self, all_attributes=False):
        '''returns a json string of the instance
           the optional parameter forces all attributes to be included in the json string.
           it defaults to false in which case it honors a list of attributes which are not
           encoded to json
        '''
        encoder = simplejson.JSONEncoder()
        return encoder.encode(self.toJSONObject())

    def getField(self, field_name):
        if field_name in User.FIELDS_MAP.keys():
            return getattr(self, field_name.lower())
        else:
            raise ComponentError('cannot read. no such field %s' % field_name)

    def setField(self, field_name, value):
        if field_name in User.FIELDS_MAP.keys():
            setattr(self, field_name.lower(), value)
        else:
            raise ComponentError('cannot write. no such field %s' % field_name)

    def allow_owners(self):
        return self.getField('CONN_USER_TYPE_PREF') != "agent"

    def allow_dealers(self):
        return self.getField('CONN_USER_TYPE_PREF') != "individual"

    def isNew(self):
        '''returns true if this has an id.'''
        if self.getField('ID'):
            return False
        return True

    def __getitem__(self, f):
        # heck, django templates again. they do dict lookup first.
        # this breaks the template lookup for properties
        if f not in User.FIELDS_MAP.keys():
            raise KeyError, f
        return self.getField(f)

    def __setitem__(self, f, value):
        self.setField(f, value)

    def isFirstAd(self):
        if not self['ID']:
            return True
        if self['NO_OF_LISTINGS'] == 0:
            return True
        return False

    def hasFreeAd(self):
        return self.isFirstAd() and self['ELIGIBLE_FOR_FREE']

    def getGreeting(self):
        if not self['NAME']:
            return ''
        return 'Hi %s. ' % self['NAME']

    def getUserInfo(self):
        if self['TYPE'] == 'agent':
            return self['NAME'] + ' (Dealer)'
        else:
            return self['NAME'] + ' (Owner)'

    def clone(self):
        u = User()
        for f in User.FIELDS_MAP.keys():
            try:
                u[f] = self[f]
            except Exception, e:
                print '##Error' + repr(e) + 'field:' + f
        return u
