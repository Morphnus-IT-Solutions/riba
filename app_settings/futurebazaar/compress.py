COMPRESS_CSS = {
    'all': {
        'source_filenames': (
            'css/common.css',
            'css/header.css',
            'css/menu.css',
            'css/home.css',
            'css/content.css',
            'css/popup.css',
            'css/category.css',
            'css/battle.css',
            'css/product.css',
            #'css/daily_deals.css',
            'css/footer.css',
            #'css/topdeals.css',
            'css/rupee/font.css',
            'css/buttons.css',
            'css/cart.css',
            'css/pages.css',
            #'css/topdeals.css',
            'css/my_account.css',
            'css/forgot_password.css',
            'css/feedback.css',
            'css/cc_panel.css',
            #'css/confirmation.css',
            'css/jq/jquery-ui-1.8.10.custom.css',
            'js/fancybox/jquery.fancybox-1.3.4.css',
            'js/jsonSuggest/jsonSuggest.css',
            'css/jquery.rating.css',
            'css/lightbox.css',
            'css/payback.css',
            'css/fb-zoom.css',
            'css/promo.css',
            #'css/about_us.css',
            'css/aboutus.css',
            #'css/promo.css',
        ),
        'output_filename': 'c/?.css',
        'extra_context': {
            'media': 'all',
        },
    },

    'ie6': {
        'source_filenames': (
            'css/ie6.css',
        ),
        'output_filename': 'c/ie6-?.css',
        'extra_context': {
            'media': 'all',
        },
    },
    'ie7': {
        'source_filenames': (
            'css/ie7.css',
        ),
        'output_filename': 'c/ie7-?.css',
        'extra_context': {
            'media': 'all',
        },
    },
    'ie8': {
        'source_filenames': (
            'css/ie8.css',
        ),
        'output_filename': 'c/ie8-?.css',
        'extra_context': {
            'media': 'all',
        },
    },
}

COMPRESS_JS = {
    'all': {
        'source_filenames': (
            'jq/js/jquery-1.7.2.min.js',
            'jq/js/jquery-ui.min.js',
            'js/jquery.hoverIntent.minified.js',
            'js/jq/jquery.tools.min.js',
            'js/jq/jquery-ui-timepicker-addon.js',
            'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            'js/fancybox/jquery.fancybox-1.3.4.pack.js',
            'js/cookie.js',
            'js/timer.js',
            'js/jquery.metadata.js',
            'js/jquery.rating.js',
            'js/lightbox.js',
            'js/social.js',
            'js/popup.js',
            #'js/add_to_cart.js',
            'js/fb-zoom.js',
        ),
        'output_filename': 'c/js-?.js',
    },
}
