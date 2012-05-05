COMPRESS_CSS = {
    'all': {
        'source_filenames': (
            'css/common.css',
            'css/buttons.css',
            'css/category.css',
            'css/hometown.css',
            'css/header.css',
            'css/home.css',
            'css/content.css',
            'css/product.css',
            'css/footer.css',
            'css/rupee/font.css',
            'css/product-zoom.css',
           'css/ht-home-style.css',
            'css/jq/jquery-ui-1.8.10.custom.css',
            'js/fancybox/jquery.fancybox-1.3.4.css',
        ),
        'output_filename': 'c/?.css',
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
            #'js/jquery.hoverIntent.minified.js',
            #'js/jq/jquery.tools.min.js',
            #'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            #'js/fancybox/jquery.fancybox-1.3.4.pack.js',
            #'js/cookie.js',
            #'js/popup.js',
            #'js/jsonSuggest/jquery.jsonSuggest-dev.js', # TODO Remove this dev thing
            #'js/jsonSuggest/json2.js', # TODO Why are we using this?
            #'js/timer.js',
            'js/fancybox/jquery.easing-1.3.pack.js',
            'js/fancybox/jquery.fancybox-1.3.1.js',
            'js/fancybox/jquery.fancybox-1.3.1.pack.js',
            'js/fancybox/jquery.fancybox-1.3.4.js',
            'js/fancybox/jquery.fancybox-1.3.4.pack.js',
            'js/fancybox/jquery.mousewheel-3.0.4.pack.js',
            'js/jquery-ui.min.js',
            'js/jquery.easing.1.3.js',
            'js/jquery.fancybox-1.3.4.pack.js',
            'js/jquery.min.js',
            'js/product-zoom.js',
            'js/ht-home-javascript.js',
        ),
        'output_filename': 'c/js-?.js',
    },

}
