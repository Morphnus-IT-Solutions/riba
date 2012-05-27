from integrations.futurebazaar import fbapiutils as futils
from lxml import etree

def get_order_by_id(order_id):
    get_order_client = futils.get_client('commerce','getOrderAsXML')
    xml = get_order_client.service.getOrderAsXML(order_id)
    print xml

def get_order_status(order_id):
    get_order_status_client = futils.get_client('commerce','getOrderStatus')
    obj = get_order_status_client.service.getOrderStatus(order_id)
    print obj

def get_order_by_user(profile_id):
    get_order_client = futils.get_client('commerce','getCurrentOrderId')
    order_id = get_order_client.service.getCurrentOrderId()
    return order_id

def create_order_for_user(profile_id):
    create_order_client = futils.get_client('commerce','createOrderForUser')
    order_id = create_order_client.service.createOrderForUser(
            None,profile_id)
    return order_id

def add_item_to_order(product_id, sku_id, qty=1, order_id=None):
    add_item_to_order_client = futils.get_client('commerce','addItemToOrder')
    item_id = add_item_to_order_client.service.addItemToOrder(order_id, product_id, sku_id, qty)
    print 'item added', item_id

def update_item_quantity(sku_id, qty, order_id):
    pass

def remove_item_from_order(sku_id, order_id):
    pass

def add_edit_order_shipping_info(shipping_info, order_id):
    pass

def add_edit_order_payment_info(payment_info, order_id):
    pass

def apply_coupon(order_id, coupon):
    pass

def book_order(order_id):
    pass

def confirm_order(order_id):
    pass

def cancel_order(order_id):
    pass

def refund_order(order_id):
    pass

def add_shipping_address_to_order(order_id, address):
    shipping_address_client = futils.get_client('commerce','addShippingAddressToOrder')
    contact_info = shipping_address_client.factory.create('ns4:ContactInfo')
    contact_info.state = address['state']
    contact_info.phoneNumber = address['phoneNumber']
    contact_info.postalCode = address['postalCode']
    contact_info.country = address['country']
    contact_info.city = address['city']
    contact_info.address1 = address['address1']
    shipping_group_id = shipping_address_client.service.addShippingAddressToOrder(order_id,contact_info)
    print 'shipping address added', shipping_group_id

def default_payment_group_id_for_order(order_id):
    payment_group_client = futils.get_client('commerce', 'getDefaultPaymentGroupId')
    pg_id = payment_group_client.service.getDefaultPaymentGroupId(order_id)
    print pg_id

def default_shipping_group_id_for_order(order_id):
    shipping_group_client = futils.get_client('commerce', 'getDefaultShippingGroupId')
    shipping_group_id = shipping_group_client.service.getDefaultShippingGroupId(order_id)
    print shipping_group_id
