COMPRESS_CSS = {
    'all': {
        'source_filenames': (
            'css/common.css',
            'css/imagerotator.css',
            'css/category.css',
            'css/product.css',
            'css/buttons.css',
            'css/my_account.css',
            'css/cart.css',
            'css/popup.css',
            'css/pop_up.css',
            'css/demo.css',
            'css/rupee/font.css',
            'css/cc_panel.css',
            'css/movingboxes.css',
            'js/fancybox/jquery.fancybox-1.3.4.css',
    	    'css/jq/jquery-ui-1.8.10.custom.css',
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
            'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            'js/fancybox/jquery.fancybox-1.3.4.pack.js',
        ),
        'output_filename': 'c/js-?.js',
    },

}
