from chaupaatiapi.errors import ComponentError
from django.utils import simplejson

class Payment:
    '''Represents a search object in the system.
       The field map is a map of the attributes to
       the json keys
    '''

    FIELDS_MAP = {\
            'ID':'id',\
            'CHANNEL': 'channel',\
            'ORDER_ID': 'orderId',\
            'TYPE': 'type',\
            'AMOUNT': 'amount',\
            'PARAM': 'param',\
            'ACTION': 'action',\
            'STATUS': 'status',\
            'RESPONSE': 'response',\
            'RESPONSE_DESC': 'responseDesc',\
            'USER_ID':'userId',\
            'TIMESTAMP':'timestamp',\
            'MODIFICATION_TIME':'modifiedOn',\
            }

    JSON_BLACK_LIST = ['TIMESTAMP', 'STATUS', 'MODIFICATION_TIME']

    def __init__(self, **dict):
        '''Constructs a search instance. Sets the attributes and their default values'''

        # our attribute names are the keys of FIELDS_MAP converted to lower case
        self.id = None
        self.user_id = None
        self.timestamp = None
        self.modification_time = None
        self.order_id = ''
        self.channel = ''
        self.amount = 0
        self.response = ''
        self.response_desc = ''
        self.param = ''
        self.status = 'new'
        self.action = ''
        self.type = ''
        # handle no dict
        if not dict:
            dict = {}

        # fill the values from dict
        for key in Payment.FIELDS_MAP.keys():
            if key in dict.keys():
                setattr(self, key.lower(), dict[key])

    def fromJSONObj(self, jsonObj):
        '''the json keys we understand are the values of the FIELDS_MAP
           the jsonObj parameter is a misnomer. it is a python dict object.
           the naming has been chosen to indicate that this function can
           take the decoded json representation and and construct the instance of search
        '''
        for key in Payment.FIELDS_MAP.keys():
            jsonKey = Payment.FIELDS_MAP[key]
            if jsonKey in jsonObj.keys():
                setattr(self, key.lower(), jsonObj[jsonKey])

    def fromJSONStr(self, jsonStr):
        '''takes a json string and constructs a search instance'''
        jsonObj = simplejson.JSONDecoder.decode(jsonStr)
        self.fromJSONObj(jsonObj)

    def toJSONObj(self):
        '''returns a dict with allowed JSON keys and values'''
        o = {}
        black_list = Payment.JSON_BLACK_LIST
        if not self['ID']:
            black_list.append('ID')
        if not self['USER_ID']:
            black_list.append('USER_ID')
        if not self['ORDER_ID']:
            black_list.append('ORDER_ID')

        for key in Payment.FIELDS_MAP.keys():
            if key not in Payment.JSON_BLACK_LIST:
                # add to dict with json key
                o[Payment.FIELDS_MAP[key]] = self[key]
        return o

    def toJSONStr(self, all_attributes=False):
        '''returns a json string of the instance
           the optional parameter forces all attributes to be included in the json string.
           it defaults to false in which case it honors a list of attributes which are not
           encoded to json
        '''
        # FIXME we should implement JSON serializable
        o = self.toJSONObj()
        encoder = simplejson.JSONEncoder()
        return encoder.encode(o)

    def getField(self, field_name):
        if field_name in Payment.FIELDS_MAP.keys():
            return getattr(self, field_name.lower())
        else:
            raise ComponentError('cannot read. no such field %s' % field_name)

    def setField(self, field_name, value):
        if field_name in Payment.FIELDS_MAP.keys():
            setattr(self, field_name.lower(), value)
        else:
            raise ComponentError('cannot write. no such field %s' % field_name)

    def __getitem__(self, f):
        # heck, django templates again. they do dict lookup first.
        # this breaks the template lookup for properties
        if f not in Payment.FIELDS_MAP.keys():
            raise KeyError, f
        return self.getField(f)

    def __setitem__(self, f, value):
        self.setField(f, value)
