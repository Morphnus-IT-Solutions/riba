from integrations.omsapi import omsapiutils as outils

    
def create_ticket(ticket_type, order_id, ticket_info):
    json = outils.get_api_response('create_ticket', 'post', {}, {
            'ticket_type': ticket_type,
            'order_id': order_id,
            'ticket_info': ticket_info
            })
    return json
