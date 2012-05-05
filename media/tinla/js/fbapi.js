$(document).ready(function() {
    var is_hide_cookie_set = ($.cookie('fbrfd') == "v1");
    var set_hide_cookie = function() {
        $.cookie('fbrfd', "v1", { path: '/', expires: 3650 });
    };
    if (is_hide_cookie_set === false) {
        $('body').append('<div style="display:none"><a href="http://www.chaupaati.in/fb/register" class="register-for-deals">Register for deals</a></div>');
        var dialog = $('a.register-for-deals').fancybox({
            'type':'iframe',
            'onClosed': set_hide_cookie,
            'callbackOnClose': set_hide_cookie,
            'width': 300,
            'height': 200
        });
        $('a.register-for-deals').trigger('click');
    }
});
