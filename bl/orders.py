from bl.api import APIRequest, APIResponse, getApiResponse, makeAPIUrl
from bl.errors import *
import logging

log = logging.getLogger('ccc')
def getOrdersByCallId(call_id, state, *args, **kwargs):
    '''gets the order by user orderid'''
    try:
        components = ['*', '*', '*', '*', '*', '*', '*',\
                '*', '*', '*', '*', '*', '*', '*', '*', '*']
        url = makeAPIUrl(components, dict(callid=call_id,state=state, apiuser='hemanth',admin='yes'))
        req = APIRequest(url, None)
        res = getApiResponse(req)
        if res.getStatus() == 200:
           items = res.getJSONData().get('items',[])
           if not items:
               return []
           return [dict(id=item['id'],status=item['state']) for item in items]
        else:
            return []
    except APINotFoundError:
        return []
    except APIError, e:
        log.exception('error polling bl api get orders for call %s ' % repr(e))
        return []
