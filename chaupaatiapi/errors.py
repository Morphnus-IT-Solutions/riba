class ChaupaatiError(Exception):
    '''Base class for chaupaati errors'''
    pass

class APIError(ChaupaatiError):
    '''Error during api conversation'''
    pass

class APIParseError(ChaupaatiError):
    '''Error parsing API response. Server responded with 200, but not valid JSON'''

class APINotFoundError(APIError):
    '''API responded with 404'''
    pass

class APIBadReqError(APIError):
    '''API responded with 400'''
    ErrorMsg = ''
    chaupaatiCode = ''

class APIUnauthenticatedError(APIError):
    '''API responded with 401'''

class APIUnauthorizedError(APIError):
    '''API responded with 403'''

class APIServerError(APIError):
    '''API responded with 5xx'''

class ComponentError(ChaupaatiError):
    '''Base class for component errors'''

class ValidationError(ChaupaatiError):
    '''Base classs for validation errors'''
