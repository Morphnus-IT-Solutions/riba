from django.db import models

# Create your models here.

class RestAPI:
    server = "127.0.0.1"
    port = '8080'

    def getPromotionsById(orderId):
        path = '/colada/promotions?order_id=' + orderId
        httpServ = httplib.HTTPConnection(server, port)
        httpServ.connect()

        httpServ.request('GET', path)

        response = httpServ.getresponse()

        s = '<b>Making API call to get promotions from :</b> <br><br>'
        if response.status == httplib.OK:
            s = s + server + ':' + port +  path + '<br>'
            s = s + '<br> <b>Response: </b><br><br> '+response.read()

	return s
        httpServ.close()
