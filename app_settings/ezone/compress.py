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
            'css/daily_deals.css',
            'css/footer.css',
            'css/topdeals.css',
            'css/rupee/font.css',
            'css/buttons.css',
            'css/cart.css',
            'css/pages.css',
            'css/topdeals.css',
            'css/my_account.css',
            'css/forgot_password.css',
            'css/pop_up.css',
            'css/feedback.css',
            'css/cc_panel.css',
            'css/confirmation.css',
            'css/jq/jquery-ui-1.8.10.custom.css',
            'js/fancybox/jquery.fancybox-1.3.4.css',
            'js/jsonSuggest/jsonSuggest.css',
            'css/jquery.rating.css',
        ),
        'output_filename': 'c/?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },

    'ie6': {
        'source_filenames': (
            'css/ie6.css',
        ),
        'output_filename': 'c/ie6-?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
    'ie7': {
        'source_filenames': (
            'css/ie7.css',
        ),
        'output_filename': 'c/ie7-?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
    'ie8': {
        'source_filenames': (
            'css/ie8.css',
        ),
        'output_filename': 'c/ie8-?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

COMPRESS_JS = {
    'all': {
        'source_filenames': (
            'jq/js/jquery.min.js',
            'jq/js/jquery-ui.min.js',
            'js/jquery.hoverIntent.minified.js',
            'js/jq/jquery.tools.min.js',
            'js/jq/jquery-ui-timepicker-addon.js',
            'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            'js/fancybox/jquery.fancybox-1.3.4.pack.js',
            'js/jsonSuggest/jquery.jsonSuggest-dev.js', # TODO Remove this dev thing
            'js/jsonSuggest/json2.js', # TODO Why are we using this?
            'js/jquery.metadata.js',
            'js/jquery.rating.js',
        ),
        'output_filename': 'c/js-?.js',
    },
    'ie': {
        'source_filenames': (
            #'js/jquery.pngFix.js',
        ),
        'output_filename': 'c/ie-?.js',
    }

}
