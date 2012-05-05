from orders.models import Order, OrderItem
from orders.models import DeliveryInfo, BillingInfo
from catalog.models import SellerRateChart, Product
from promotions.manager import PromotionsManager
from fulfillment.manager import FulfillmentManager
from django.conf import settings
from decimal import Decimal
import logging

log = logging.getLogger('order')

class OrderManager():
    ''' Defines the manager class for orders. This class holds
        all the business logic for cart, booking order
    '''

    def __init__(self):
        # Initiate other managers
        self.CART_STATES = ('cart', 'guest_cart', 'unassigned_cart',
            'temporary_cart')
        self.PAID_STATES = ('confirmed',)
        self.promo_mgr = PromotionsManager()
        self.fulfill_mgr = FulfillmentManager()


    def get_users_cart(self, user, client, **kwargs):
        ''' Returns the user's cart for a client. Ideally a user
            will have only one cart per client. But as this rule has not been
            followed for a while, the DB might have multiple carts per client
        '''
        return self.__get_latest_cart_by_state(user, client, 'cart')

    def get_users_guest_cart(self, user, client, **kwargs):
        ''' Returns the user's guest_cart for a client. Ideally a user
            will have only one guest_cart per client. But as this rule has
            not been followed for a while, the DB might have multiple
            guest_carts per client
        '''
        return self.__get_latest_cart_by_state(user, client,
            'guest_cart')

    def convert_to_temporary_cart(order):
        if order.state != self.UNASSIGNED_CART_ORDER_STATE:
            raise Order.InvalidOperation(
                'Only unassigned cart can be converted to temporary cart') 
        self.__change_order_state(order,
            self.TEMPORARY_CART_ORDER_STATE)
            

    def _get_cart_for_signed_in_checkout(self, user, client,
        current_cart):
        # Signed in checkout should be used if the user is signed in
        # before adding item to cart
        if not user:
            raise Order.InvalidOperation(
                'Empty user supplied for signed_in checkout')
            return self.get_users_cart(user, client)

    def _get_cart_for_registered_user_as_guest(self, user, client,
        current_cart):
        # Registered user as guest checkout flow should be used
        # when a registered user supplies only the username (email/mobile)
        # and not a password during checkout. However, there will be a cart
        # which the user has already added items into. We should take
        # the items from cart and put them into user's temporary
        # cart, flush any other items in guest cart and proceed.

        # There is a user data loss risk here if we flush users's guest
        # cart based on username. There can be an attack which add items,
        # supplies username and real user's guest cart is lost.
        # To take care of this, we cannot use guest cart.
        # We will use a temporary cart instead.
        if not user:
            raise Order.InvalidOperation(
                'Empty user supplied for registered_user_as_guest checkout')
        if not current_cart:
            raise Order.InvalidOperation(
                'Current cart cannot be None for registered_user_as_guest')
        if current_cart.state == 'unassigned_cart':
            # Convert this unassgined cart into a temporary cart and proceed
            temporary_cart = self.convert_to_temporary_cart(
                current_cart, user, client)
            return temporary_cart
        else:
            return current_cart

    def _get_cart_for_signed_in_user_as_guest(self, user, client,
        current_cart):
        # This case is very similar to above case, except that user
        # supplied password along with user name and has successfully
        # signed in. We can be more confident of changing user's carts
        # here as the user is signed in. Get user's guest cart, flush it
        # add the new items and proceed.
        if not user:
            raise Order.InvalidOperation(
                'Empty user supplied for signed_in_user_as_guest checkout')
        if not current_cart:
            raise Order.InvalidOperation(
                'Current cart cannot be None for signed_in_user_as_guest')
        guest_cart = self.get_users_guest_cart(user, client)
        if guest_cart.id != current_cart.id:
            # Flush only if the guest cart is different from current cart
            self.flush_order(guest_cart)
            self.copy_order_into(current_cart, guest_cart)
        return guest_cart

    def _get_cart_for_new_user_as_guest(self, user, client, current_cart):
        # This case is similar to above cases except that the user is a
        # new user. We should not have any guest carts for this user.
        # Create a guest cart, fill it with items from current cart
        # and proceed.
        if not user:
            raise Order.InvalidOperation(
                'Empty user supplied for new_user_as_guest checkout')
        if not current_cart:
            raise Order.InvalidOperation(
                'Current cart cannot be None for new_user_as_guest')
        # Guest cart should not be present ideally, but no harm if we
        # flush the guest cart. Can perhaps happen due to race conditions
        # or bugs in the calling code.
        guest_cart = self.get_users_guest_cart(user, client)
        if not guest_cart:
            # Expected case, create a new guest cart for this user
            guest_cart = self.create_cart('guest_cart', user, client)
        if guest_cart.id != current_cart.id:
            # Flush only if the guest cart is different from current cart
            self.flush_order(guest_cart)
            self.copy_order_into(current_cart, guest_cart)
        return guest_cart

    def _get_cart_for_no_user_checkout(self, user, client, current_cart):
        if user:
            raise Order.InvalidOperation(
                'User supplied for no_user checkout. User should be none')
        # No user checkout should be used when the user is not known yet.
        # We should create a unassigned_cart and send it across. All
        # unassinged carts should be destroyed on session expiry or logout
        # The uassigned carts get destroyed in the next steps when the
        # checkout type changes to registered_user_as_guest or
        # signed_in_user_as_guest or new_user_as_guest
        if current_cart:
            # Current cart is present, not the first call to get cart
            return current_cart
        else:
            # No current cart, first call to get cart
            return self.create_cart('unassigned_cart', user, client)


    def get_cart_for_checkout(self, user, client, checkout_type, current_cart):
        ''' Returns the cart of the user for checkout. This can either be a
            cart or a guest_cart. If the user is not known yet, this
            will be an unassigned_cart. The unassigned_cart should be
            destroyed and the items should be put in the guest cart once
            user is attached to unassigned_cart.
            See http://corp.futurebazaar.com/index.php/Cart_Flow
        '''
        if checkout_type == 'signed_in':
            return self._get_cart_for_signed_in_checkout(user, client,
                current_cart)
        if checkout_type == 'registered_user_as_guest':
            return self._get_cart_for_registered_user_as_guest(user, client,
                current_cart)
        if checkout_type == 'signed_in_user_as_guest':
            return self._get_cart_for_signed_in_user_as_guest(user, client,
                current_cart)
        if checkout_type == 'new_user_as_guest':
            return self._get_cart_for_new_user_as_guest(user, client,
                current_cart)
        if checkout_type == 'no_user':
            return self._get_cart_for_no_user_checkout(user, client,
                current_cart)
        raise Order.InvalidOperation('Invalid checkout type %s' % checkout_type)

    def add_update_item(self, order, rate_chart, qty, channel, op='add'):
        ''' Adds the given item to order. channel is the client domain.
            Returns the order with item added
        '''
        if rate_chart.seller.client_id != order.client_id:
            raise order.ClientMismatch

        if rate_chart.product.status != 'active':
            raise rate_chart.ProductInactive

        # Check item stock availability
        stock_available = self.fulfill_mgr.check_inventory(
            rate_chart, qty)
        if not stock_available:
            raise Order.OutOfStock

        try:
            order_item = order.get_order_items(None).get(
                seller_rate_chart = rate_chart)
        except OrderItem.DoesNotExist:
            order_item = OrderItem(order = order,
                seller_rate_chart = rate_chart,
                item_title = rate_chart.product.title,
                gift_title = rate_chart.gift_title
                qty=0)

        # Get applicable prices
        if op == 'add':
            # Adding an item, rate chart prices are source of truth
            prices = rate_chart.get_price_for_domain(channel)
            prices['shipping_charges'] = rate_chart.shipping_charges
        if op == 'update' and order.support_state:
            # Modifying an existing item, we should honour committed prices
            prices = {
                'list_price': order_item.list_price/order_item.qty,
                'sale_price': order_item.sale_price/order_item.qty,
                'cashback_amount': order_item.cashback_amount/order_item.qty,
                'shipping_charges': order_item.shipping_charges/order_item.qty
                }

        if op == 'add':
            # Increase the item's qty
            order_item.qty += qty
        elif op == 'update':
            if order_item.qty > 0 and order_item.qty < qty:
                if order.support_state:
                    # If order is not a cart, then qty cannot be increased
                    raise Order.InvalidOperation(
                        'Cannot increase qty of an item in paid order')
            order_item.qty = qty
        else:
            # Not a valid case, but for completeness
            raise Order.InvalidOperation

        # Set prices
        order_item.list_price = prices['list_price']*order_item.qty
        order_item.sale_price = prices['offer_price']*order_item.qty
        order_item.cashback_amount = prices.get('cashback_amount',
            Decimal('0.0')) * order_item.qty
        order_item.shipping_charges = prices['shipping_charges']*order_item.qty
        # total = sale price + shipping - cashback
        order_item.total_amount = order_item.sale_price
        order_item.total_amount += order_item.shipping_charges
        order_item.total_amount -= order_item.cashback_amount
        # Save order item
        self.__save_order_item(order_item)

        # Reprice order
        self.reprice_order(order)
        return order

    def add_item(self, order, rate_chart, qty, channel):
        ''' Adds the given item to order. channel is the client domain.
            Returns the order with item added
        '''
        if order.support_state:
            # Cannot add items to order if its not a cart
            raise Order.InvalidOperation('Can add items only to cart')
        return self.add_update_item(order, rate_chart, qty, channel, 'add')


    def update_item_qty(self, order, rate_chart, qty, channel):
        ''' Updates the qty of a rate_chart in an order to given qty.
            Returns the order with updated item
        '''
        return self.add_update_item(order, rate_chart, qty, channel, 'update')

    def remove_item(self, order, order_item_id, item_info):
        ''' Remove given item from order. All item info is passed as dict
            Returns the updated order
        '''
        order_item = self.get_order_item_by_id(order_item_id)
        if order_item.order_id != order.id:
            raise Order.InvalidOperation(
                'Order item %s does not belong to order %s' % (order_item_id,
                order.id))
        # An item can be removed from order if its a cart without much fuss
        if order.state in self.CART_STATES:
            self.remove_order_item(order_item)
        else:
            return self.cancel_order_item(order, order_item)
        # Reprice order
        self.reprice_order(order)
        return order

    def cancel_order_item(self, order, order_item):
        if order_item.order_id != order.id:
            raise Order.InvalidOperation(
                'Order item %s does not belong to order %s' % (order_item_id,
                order.id))
        if order.state == self.ORDER_BOOKED:
            # An item can be removed if order is not paid for.
            # This is not the normal case however. The case is allowed for
            # deferred payments.

            # TODO Decide if we want to make booked orders immutable till
            #      payment. Any modifications at item level should perhaps
            #      be treated as a new order

            # Change the state of order_item
            self.__change_order_item_state(order_item,
                self.ORDER_ITEM_CANCELLED_STATE)
            # log the cancel action
            self.log_cancel_order_item(order_item)
            # release the locked inventory
            self.fulfill_mgr.release_inventory(order_item)
        elif order.state in self.PAID_STATES:
            # if order item is already cancelled or if it is awaiting
            # shipment cancellation, raise error
            if order_item.state in self.ORDER_ITEM_CANCELLED_STATES:
                raise Order.InvalidOperation(
                    'Order item is already cancelled or awaiting cancellation')

            shipments = self.fulfill_mgr.get_shipment(order, order_item)
            # TODO A bunch of this cancellation logic should perhaps be put
            # in the fulfillment manager.

            # Get shipments for the order item
            # a. If all shipments are deleted, we can cancel order item
            # b. If no shipments are detected, we are waiting for shipments
            #    to be created. We cannot cancel
            if not shipments:
                raise Order.InvalidOperation(
                    'Cannot cancel this item. Waiting for shipment info')

            can_cancel = True
            any_shipment_delievered = False
            for shipment in shipments:
                if shipment.state != self.fulfill_mgr.DELETED_STATE:
                    can_cancel = False
                if shipment.state == self.fulfill_mgr.DELIVERED_STATE:
                    any_shipment_delievered = True

            if can_cancel:
                # If we've sucessfully cancelled shipment, then we can go
                # ahead and cancel the order item
                self.__change_order_item_state(order_item,
                    self.ORDER_ITEM_CANCELLED_STATE)
                # log the cancel action
                self.log_cancel_order_item(order_item)
                # release the locked inventory
                self.fulfill_mgr.release_inventory(order_item)
                # reprice order
                current_payable = order.payable_amount
                self.reprice_order(order)
                payable_now = order.payable_amount
                amount_refundable = current_payable - payable_now
                self.payments_manager.open_refund([order_item], amount_refundable)
                # TODO notify cancellation
            else:
                # Cannot cancel. Raise proper error message or register a
                # request for cancellation
                if any_shipment_delievered:
                    # TODO Ideally we should register cancellation request even
                    # for delivered cases. Till we implement that stuff, fail
                    raise Order.InvalidOperation(
                        'Some shipments are already delivered, cannot cancel')
                else:
                    # Save the cancellation request.
                    for shipment in shipments:
                        # This call will raise an exception and fail if request
                        # to cancel shipment has failed
                        self.fulfill_mgr.cancel_shipment(shipment)
                    # Mark the order item as awaiting shipment deletion
                    # We should listen to shipment deletion events and process
                    # this cancellation
                    self.__change_order_item_state(order_item,
                        self.ORDER_ITEM_AWAITING_SHIPMENT_DELETION_STATE)

    def apply_coupon(self, order, coupon_info):
        ''' Applies the given coupon code to order. Checks coupon rules for
            application. Returns the updated order
        '''
        # Reprice order
        self.reprice_order(order)
        pass

    def attach_loyalty_card(self, order, loyalty_info):
        ''' Adds the given loyalty card to order. An order can have multiple
            loyalty cards attached right now
        '''
        pass

    def add_delivery_address_to_order(self, order, delivery_address):
        pass

    def reprice_order(self, order, **kwargs):
        ''' Reprices order. Responsibile for applying all applicable promotions
            and computing the final payable amount by the customer. This
            amount is sent to the payments service. Payments service might
            charge a different amount (payment based promotions, extra charges
            per payment gateway etc)
        '''
        # During repricing order, we should compute the totals for
        # a. list price: Sum of list prices of non cancelled order items
        # b. sale price: Sum of sale prices of non cancelled order items
        # c. cashback: Sum of cashback total of non cancelled order items
        # d. shipping: Total applicable shipping charges
        # e. payment: Total applicable payment charges
        # f. discounts: TODO Various discounts of applicable promotions
        # g. taxes: TODO Taxes applicable for each item and for order
        # h. payable amount: The amount payable by the customer

        list_price_total = Decimal(0)
        sale_price_total = Decimal(0)
        cashback_amount_total = Decimal(0)
        shipping_charges_total = Decimal(0)
        taxes = Decimal(0)
        transaction_charges = Decimal(0)
        payable_amount = Decimal(0)

        order_items = order.get_order_items(None,
            exclude=dict(state='cancelled'))

        # Compute list price, sale price and cashback totals
        for item in order_items:
            list_price_total += item.list_price
            sale_price_total += item.sale_price
            shipping_charges_total += item.shipping_charges
            if item.cashback_amount:
                cashback_amount_total += item.cashback_amount

        order.list_price_total = list_price_total
        # order's sale price total is called total
        order.total = sale_price_total
        order.cashback_amount_total = cashback_amount_total
        shipping_charges_total = shipping_charges_total.quantize(
            Decimal('1'), rounding=ROUND_HALF_UP).quantize(Decimal('0.01'))

        # payable = total + taxes + shipping + payment - cashback - discounts
        # subtract cashback
        order.payable_amount = order.total - order.cashback_amount_total

        # get all the applicable promotions for this order to compute discounts
        applicable_promotions = self.promo_mgr.get_applicable_promotions(order)
        # iterate and try to apply each promotion
        for promotion in applicable_promotions:
            self.apply_promotion(order, promotion)
            discount += promotion.discount

        # remove any promotions applied to order which are not part of
        # applicable_promotions. this step is required to clean up the
        # stale links for alreay applied promotions
        applied_promotions = self.promo_mgr.get_applied_promotions(order)
        for promotion in applied_promotions:
            if promotion not in applied_promotions:
                self.remove_promotion(order, promotion)

        # subtract total discount
        order.payable_amount -= discount

        # For futurebazaar, if payable < 1000, add shipping charges of Rs.100
        # TODO This should be treated like a promotion. Waive of shipping
        # charges if order value is above Rs. 1000
        additional_shipping_charges = Decimal('0')
        if utils.is_futurebazaar_client(self.client):
            if (self.payable_amount < Decimal('1000')) and (
                shipping_charges_total == Decimal('0')) and order_items:
                additional_shipping_charges = Decimal('100')

        shipping_charges_total += additional_shipping_charges
        order.shipping_charges = shipping_charges_total
        order.payable_amount += order.shipping_charges
        self.__save_order(order)

    def book_order(self, order, **kwargs):
        ''' Books an order, sends out notifications, raises order booked signal '''
        pass

    def cancel_order(self, order_id):
        ''' Cancelling entire order '''
        order = self.get_order_by_id(order_id)

    
    # Util functions to interact with the data interface and get the 
    # business objects

    def get_order_by_id(self, order_pk):
        return self.__get_order_by_pk(order_pk)

    def get_order_item_by_id(self, order_item_pk):
        return self.__get_order_item_by_pk(order_item_pk)

    # The functions below have django orm usage. Not suitable for direct
    # translation.

    def __get_order_item_by_pk(self, order_item_id):
        try:
            return OrderItem.objects.get(pk=order_item_id)
        except OrderItem.DoesNotExist:
            pass
        return None

    def __get_order_by_pk(self, order_id):
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            pass
        return None

    def __save_order(self, order):
        order.save()

    def __save_order_item(self, order_item):
        order_item.save()

    def __change_order_item_state(self, order_item, state):
        order_item.state = state
        order_item.save()

    def __change_order_state(self, order, state):
        order.state = state
        order.save()

    def __get_latest_cart_by_state(self, user, client, state):
        ''' Return user's latest cart (state supplied as argument) for a client
            Returns None if cart is not found
        '''
        # Limit to two so that we check if multiple carts are found in DB
        # Can mine this log later and delete them.
        qs = Order.objects.filter(user=user, client=client,
            state = state).order_by('-id')[:2]
        if qs:
            if len(qs) > 1:
                log.debug(
                    'Multiple %s carts found for user: %s, client: %s' % (
                    state, user.id, client.id))
            return qs[0]
        return None
