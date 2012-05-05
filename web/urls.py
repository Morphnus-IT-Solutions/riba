from django.conf.urls.defaults import *
from django.contrib.auth.views import password_change, password_change_done 
import socket

# XXX this is a lot of time. we should build more aggressive timeouts
# and retries rather than blocking calls
socket.setdefaulttimeout(5*60)

urlpatterns = patterns('web.views',
    
    # home page. no url params
    url(r'^$', 'home.index'),
    url(r'^home$', 'home.index'),
    url(r'^customer-testimonials/', 'home.testimonials'),
    url(r'^suggest','home.suggest'),
    url(r'^info/sitemap/','home.sitemap'),
    
    # help system
    url(r'^help/(?P<slug>[a-zA-Z0-9-]+)/', 'help_views.show_help'),
    
    # Menu Offer urls
    #url(r'^popularity/most-viewed/', 'sbf_views.most_viewed_products', name="most-viewed-detail-page"),    
    #url(r'^popularity/most-bought/', 'sbf_views.most_bought_products', name="most-bought-detail-page"),    
    #url(r'^popularity/recently-bought/', 'sbf_views.recently_bought_products', name="recenlty-bought-detail-page"),    
    

    # static pages
    url(r'^(?P<section1>[a-zA-Z]+)/(?P<section2>[a-zA-Z]+)/(?P<page>[a-zA-Z0-9-_]+).html', 'static.double_section_page'),
    url(r'^(?P<section>[a-zA-Z]+)/(?P<page>[a-zA-Z0-9-_]+).html', 'static.section_page'),
    url(r'^(?P<page>[a-zA-Z0-9-]+).html', 'static.page'),
    url(r'^about/contact_us/', 'static.contact_us'),


    # category page. allows url params
    #url(r'^(?P<slug>[a-zA-Z0-9-]+)/ch/(?P<id>\d+)/compare/(?P<id1>\d+)/(?P<id2>\d+)/(?P<id3>\d+)/(?P<id4>\d+)/', 'sbf_views.category_compare'),
    #url(r'^(?P<slug>[a-zA-Z0-9-]+)/ch/(?P<id>\d+)/compare/(?P<id1>\d+)/(?P<id2>\d+)/(?P<id3>\d+)/', 'sbf_views.category_compare'),
    #url(r'^(?P<slug>[a-zA-Z0-9-]+)/ch/(?P<id>\d+)/compare/(?P<id1>\d+)/(?P<id2>\d+)/', 'sbf_views.category_compare'),
    #url(r'^(?P<slug>[a-zA-Z0-9-]+)/ch/(?P<id>\d+)/', 'sbf_views.category_home',name='category-home-url'),
    #url(r'^shop-by-price/', 'sbf_views.shop_by_price',name='category-shop_by_price-url'),
    #url(r'^shop-by-discount/', 'sbf_views.shop_by_discount',name='category-shop_by_discount-url'),
    url(r'^collections','product_views.get_parent_products'),
    

    # category page for whitelabel store
    #url(r'^w/([a-zA-Z0-9]+)/(?P<slug>[a-zA-Z0-9-]+)/ch/(?P<id>\d+)/', 'sbf_views.category_home'),

    # category page for mobile
    url(r'^category-menu/', 'home.category_menu'),

    # search views
    #url(r'^search/t/(?P<tag>[a-zA-Z0-9-]+)/(?P<tag_filter>[a-zA-Z0-9-_()]+)/','sbf_views.search_tag'),
    #url(r'^search/t/(?P<tag>[a-zA-Z0-9-]+)/','sbf_views.search_tag'),
    #url(r'^search/', 'sbf_views.search'),

    #urls for brand pages
    #url(r'^(?P<slug>[a-zA-Z0-9-]+)/bd/(?P<id>\d+)/','sbf_views.brand_home',name='brand-home-url'),
    
    #url(r'^promotion_offer/(?P<slug>[a-zA-Z0-9-]+)/(?P<id>\d+)/', 'list_views.promotion_offer_detail', name='promotion-offer-detail-url'),
    #url(r'^promotion/offers/', 'list_views.promotions_detail', name='promotions-detail-url'),

    # product page. allows url params
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/pd/(?P<id>\d+)/all-reviews/$','product_views.all_reviews_page',name='read_reviews_page'), 
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/pd/(?P<id>\d+)/', 'product_views.product_detail',name='product-detail-url'),
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/pd/(?P<id>\d+)', 'product_views.product_detail',name='product-detail-alt-url'),
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/quick-look/(?P<id>\d+)/', 'product_views.product_quick_look',name='product-quick-look-url'),
    # Review Model
    url(r'^product/helpful-yes/','product_views.update_helpful_yes'),
    url(r'^product/helpful-no/','product_views.update_helpful_no'),
    url(r'^product/helpful-cancel/','product_views.update_helpful_cancel'),
    url(r'^product/read-reviews/','product_views.paginate_read_reviews'),
    url(r'^review/write/(?P<review_id>\d+)/thanks/$','product_views.thanks_page',name='thanks_page'), 
    url(r'^review/write/(?P<id>\d+)/$','product_views.review_page',name='enter_review_page'), 
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/review/(?P<review_id>\d+)$','product_views.review_display',name='permalink'),

    # url for users
    url(r'^auth/fbsignin/','user_views.facebook_authenticate'),
    url(r'^auth/signin/','user_views.login'),
    url(r'^auth/signup/','user_views.login'),
    url(r'^auth/signout','user_views.logout'),
    url(r'^auth/link_dialog/', 'user_views.link_dialog'),
    url(r'^auth/link/', 'user_views.link'),
    url(r'^auth/sms-verification/', 'user_views.user_sms_verification'),
    url(r'^user/sms-verification/', 'user_views.new_user_sms_verification'),
    url(r'^ppd/auth/signout','user_views.logout'),
    url(r'^user/checkuser','user_views.check_user'),
    url(r'^forgotpassword/single/','user_views.forgot_password_single'),
    url(r'^forgotpassword','user_views.user_forgot_password'),
    url(r'^password_info_sent','user_views.user_password_info_sent'),
    url(r'^user/resetpassword','user_views.reset_password'),
    url(r'^user/checkcode','user_views.check_code'),
    url(r'^user/add_contact','user_views.add_contact'),
    url(r'^user/newsletter','user_views.newsletter'),
    url(r'^user/start-referring','user_views.refer_friend'),
    
    # TINLA order summary
    url(r'^user/orders/(?P<order_id>[0-9]+)','user_views.user_order_details'),
    url(r'^user/orders/','user_views.show_user_orders'),
    url(r'^order/track_order','user_views.track_order'),
    url(r'^user/wishlist/','user_views.wishlist_actions'),
    url(r'^user/wishlists/(?P<slug>[0-9]+)/','user_views.wishlists'),
    url(r'^seller/orders/(?P<order_id>[0-9]+)/','user_views.seller_order_details'),
    url(r'^seller/orders/','user_views.show_seller_orders'),
    url(r'^seller/update_shipping_info/(?P<order_item_id>[0-9]+)/','user_views.update_shipping_info'),
    url(r'^seller/payment_option_on_or_off/','ppd_views.payment_option_on_or_off'),
    url(r'^seller/second_factor_auth', 'ppd_views.second_factor_auth'),
    url(r'^seller/order_taking_option', 'ppd_views.order_taking_option'),
    url(r'^seller/activate_payment_option', 'ppd_views.activate_payment_option'),
    url(r'^user/profile/','user_views.user_profile'),
    url(r'^user/address/','user_views.show_address'),
    url(r'^user/notification/','user_views.user_notification'),
    url(r'^user/change_password/', password_change, {'template_name':'user/change_password.html','post_change_redirect':'user/password_change_done'}),
    url(r'^user/password_change_done$',password_change_done, {'template_name':'user/password_change_done.html'}),
    url(r'^user/help/','user_views.user_help'),
    url(r'^user/help_status/','user_views.user_help_status'),
    url(r'^user/order_confirmation/','user_views.user_order_confirmation'),
    url(r'^user/popup/','user_views.user_editaddress'),                  
    url(r'^user/delete_address/','user_views.user_deleteaddress'),
    url(r'^user/get_address_info/','user_views.get_address_info'),
    url(r'^reviews/approve_or_disapprove_review/','ppd_views.approve_or_disapprove_review'),
                       
    #payouts
    url(r'^payouts$','payout_view.home'),
    url(r'^payouts/calculate$','payout_view.calculate'),

    # MyCart urls
    url(r'^get_cart_info/$','order_view.render_cart_info'),
    url(r'^orders/cart_popup/$','order_view.show_cart_popup'),
   
    url(r'^orders/cvv_info', 'order_view.get_cvv_info'),
    url(r'^orders/RMSID_sendData', 'order_view.ebs_data'),
    url(r'^w/[a-zA-Z0-9]+/orders/signin','order_view.signin'),
    url(r'^feedback/','user_views.feedback'),
    url(r'^feedback_popup/','user_views.feedback_popup'),
    url(r'^user_verification/email_verification', 'user_views.user_email_verification'),

    url(r'^bulk-order','user_views.bulk_order'),

    # Webmaster URLS
    url(r'^web/cache-moderate/','webmaster.cache_moderate'),
)

urlpatterns += patterns('orders.views',
    (r'^orders/mycart','cart_actions'),
    (r'^orders/shipping', 'shipping_detail'),
    (r'^orders/payment_mode','payment_mode'),
    (r'^orders/get_payment_page','render_online_payment_page'),
    (r'^orders/validate_billing_info_form', 'validate_billing_info'),
    #(r'^w/[a-zA-Z0-9]+/orders/mycart','cart_actions'),
    #(r'^w/[a-zA-Z0-9]+/orders/shipping','shipping_detail'),
    (r'^fb/apply-fb-coupon','apply_coupon'),
    (r'^orders/signin','signin'),
    #(r'^orders/signup','signup'),
    (r'^orders/payment_option_page', 'render_online_payment_page'),
    (r'^orders/get_emi_options/', 'get_emi_options'),
    #(r'^orders/book_button', 'get_book_button'),
    (r'^orders/book','payment_mode'),
    (r'^orders/initialize_ivr','initialize_ivr'),
    (r'^orders/auth/(?P<admin_order_id>[0-9]+)/mycart','cart_actions'),
    (r'^orders/auth/(?P<admin_order_id>[0-9]+)/shipping','shipping_detail'),
    #(r'^orders/auth/(?P<admin_order_id>[0-9]+)/cancelled','order_view.admin_cancelled'),
)

urlpatterns += patterns('payments.views', 
    url(r'^orders/process_payment_payback', 'process_payment_payback'),
    url(r'^orders/process_payment_ccavanue', 'process_payment_ccavanue'),
    url(r'^orders/process_payment_hdfc', 'process_payment_hdfc'),
    url(r'^orders/process_payment_axis', 'process_payment_axis'),
    url(r'^orders/process_payment_amex', 'process_payment_amex'),
    url(r'^orders/process_payment_icici', 'process_payment_icici'),
    url(r'^orders/process_payment_innoviti', 'process_payment_innoviti'),
    url(r'^orders/process_parameters_itz', 'process_parameters_itz'),
    url(r'^orders/process_payment_itz', 'process_payment_itz'),
    url(r'^orders/process_request_itzcash', 'process_request_itzcash'),
    url(r'^orders/process_response_itzcash', 'process_response_itzcash'),
    url(r'^orders/process_request_atom', 'process_request_atom'),
    url(r'^orders/process_response_atom', 'process_response_atom'),
    url(r'^orders/process_request_paymate', 'process_request_paymate'),
    url(r'^orders/process_response_paymate', 'process_response_paymate'),
    
    url(r'^orders/process_payment_suvidha', 'process_payment_suvidha'),
    
    url(r'^w/[a-zA-Z0-9]+/orders/process_payment', 'process_payment_icici'),
    url(r'^orders/process_payment', 'process_payment_icici'),
    url(r'^orders/(?P<order_id>[0-9]+)/confirmation','confirmation'),
    url(r'^orders/auth/(?P<order_id>[0-9]+)/confirmation','confirmation'),

)

urlpatterns += patterns('',(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}))

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
    urlpatterns += patterns('',(r'^adminmedia/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.ADMIN_MEDIA_PREFIX}) )
