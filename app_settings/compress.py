# This file stores all the settings related to js/css compression

COMPRESS_VERSIONING = 'compress.versioning.hash.SHA1Versioning'
COMPRESS_AUTO = False
COMPRESS_VERSION = True
COMPRESS_CSS_FILTERS = ('compress.filters.yui.YUICompressorFilter',)
COMPRESS_JS_FILTERS = ('compress.filters.yui.YUICompressorFilter',)

COMPRESS_YUI_BINARY = 'java -jar yuicompressor-2.4.2.jar'

COMPRESS_YUI_CSS_ARGUMENTS = '--type CSS --nomunge --preserve-semi --disable-optimizations '
COMPRESS_YUI_JS_ARGUMENTS = '--type JS --nomunge --preserve-semi --disable-optimizations '
