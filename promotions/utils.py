# Utils file for promotions

PROMOTION_TYPES_MAP = {'Item Discount - Percent Off':{'applies_to':'product_offer_price','discount_type':'percentage'},
            'Item Discount - Amount Off':{'applies_to':'product_offer_price','discount_type':'fixed'},
            'Item Discount - Fixed Price':{'applies_to':'product_offer_price','discount_type':'fixed'},
            'Shipping Discount - Percent Off':{'applies_to':'order_shipping_charge','discount_type':'percentage'},
            'Shipping Discount - Amount Off':{'applies_to':'order_shipping_charge','discount_type':'fixed'},
            'Shipping Discount - Fixed Price':{'applies_to':'order_shipping_charge','discount_type':'fixed'},
            'Order Discount - Percent Off':{'applies_to':'order_total','discount_type':'percentage'},
            'Order Discount - Amount Off':{'applies_to':'order_total','discount_type':'fixed'},
            'Order Discount - Fixed Price':{'applies_to':'order_total','discount_type':'fixed'}, 
            }

PROMOTION_REPONSE_MAP = {'OM_APPLIED_COUPON': 'Coupon Applied',
            'OM_OM_COUPON_DISC_NOT_ADJ': 'Oops! This coupon is not applicable on this purchase',
            'OM_APPLY_COUPON_FAILED': 'Invalid Coupon',
            }

