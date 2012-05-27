
class FulfillmentManager():

    def __init__(self):
        pass

    def get_order_serviceability(self, order, **kwargs):
        ''' Checks if an order is serviceable. There are several constraints
            which define serviceability of the order. The level of checking
            can be controlled by the flags in kwargs. Available flags are

            a. stock (always true, not a flag really)
            b. pincode_covered - check if order can be shipped to pincode
            c. cod - check if order qualifies for cod

            Serviceability checks include - 
            1. SKUs should be in stock/in virutal inventory
            2. SKUs should be shippable to given pincode
            3. COD should be supported if customer chooses COD

            The function returns expected stock dates and delivery dates
            for each of the order items. Delivery dates are computed if
            pincode is attached to an order and pincode_covered flag is on.
        '''
        pass
