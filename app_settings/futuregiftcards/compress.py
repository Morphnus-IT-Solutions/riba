COMPRESS_CSS = {
    'all': {
        'source_filenames': (
            'css/menu.css',
            'css/content.css',
            'css/category.css',
            'css/product.css',
            'css/rupee/font.css',
            'css/buttons.css',
            'css/cart.css',
            'css/my_account.css',
            'css/forgot_password.css',
            'css/confirmation.css',
            'css/jq/jquery-ui-1.8.10.custom.css',
            'js/fancybox/jquery.fancybox-1.3.4.css',
            'js/jsonSuggest/jsonSuggest.css',
            'css/base.css',
            'css/common.css',
            'css/header.css',
            'css/footer.css',
            'css/home.css'
        ),
        'output_filename': 'c/?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

COMPRESS_JS = {
    'ext': {
        'external_urls': (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.10/jquery-ui.min.js',
            'https://connect.facebook.net/en_US/all.js',
        ),
        'source_filenames': (),
        'output_filename': 'c/ext-?.js',
    },
    'all': {
        'source_filenames': (
            'js/jquery.hoverIntent.minified.js',
            'js/jq/jquery.tools.min.js',
            'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            'js/fancybox/jquery.fancybox-1.3.4.pack.js',
            'js/cookie.js',
            'js/popup.js',
            'js/jsonSuggest/jquery.jsonSuggest-dev.js', # TODO Remove this dev thing
            'js/jsonSuggest/json2.js', # TODO Why are we using this?
            'js/timer.js',
			'js/jquery.hoverIntent.minified.js'
        ),
        'output_filename': 'c/js-?.js',
    },
    'ie': {
        'source_filenames': (
            'js/jquery.pngFix.js',
        ),
        'output_filename': 'c/ie-?.js',
    }

}
