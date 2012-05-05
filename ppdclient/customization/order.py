from utils import utils

def sync_cart(request, cart):
    item_found_msg = []
    #cart sync for future ecommerce
    #if cart.client == utils.get_future_ecom() and request.path.startswith('/cc/'):
    if utils.is_future_ecom(cart.client):
        id  = request.call['id']
        if id not in request.session:
            from web.views.user_views  import user_context
            user_context(request)
        cart.sync_with_fb(request)

        if 'item_found_msg' in request.session[id]:
            is_synced = request.session[id]['is_synced']
            if not is_synced:
                item_found_msg = request.session[id]['item_found_msg']

    #no syncing required for other clients as of now
    return item_found_msg
