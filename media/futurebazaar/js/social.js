// Refer http://developers.facebook.com/docs/reference/javascript/
$(".fb-login-button").click(function(e){
    var linkfbdialog = null;
    var letfbdlialogclose = false;
    var via_checkout = $(this).hasClass('via_checkout');

    function showLinkDialog(username, email, id, retry, new_login) {
        var url = "/auth/link_dialog/";
        url = url + "?fe=" + encodeURI(email);
        url = url + "&un=" + encodeURI(username);
        url = url + "&id=" + encodeURI(id)
        if(retry){
            url += "&retry="+retry;
        }
        if (via_checkout) {
            url += "&via_checkout=true";
        }
        var xhr = $.get(url, function(html) {
            
            if (xhr.status == 200) {
                show_popup(html);
            }
            if (xhr.status == 205) {
                if ( new_login === true) {
                    window.location.reload();
                }
            }
        });
    }
    // User denied linking
    // now he wants to login through facebook, so his
    // linking denied flag shud be reset

    // auth.login Event
    // This event is fired when your app notices that there is no longer a 
    // valid user (in other words, it had a session but 
    // can no longer validate the current user).
    FB.Event.subscribe('auth.login', function(response) {
        get_facebook_status(retry='login_clicked');
    });

    // Additional initialization code here
    FB.UIServer.setLoadedNode = function (a, b) { 
        FB.UIServer._loadedNodes[a.id] = b; 
    };
    get_facebook_status();
    function get_facebook_status(retry){
        FB.getLoginStatus(function(response) {
            /* Sample response object
            {
                status: 'connected',
                authResponse: {
                    accessToken: '...',
                    expiresIn:'...',
                    signedRequest:'...',
                    userID:'...'
                }
            }
            */
            if (response.authResponse && response.authResponse.userID) {
                // logged in and connected user, someone you know
                FB.api("/me/", function(userInfo) {
                    var name = userInfo.first_name + " " + userInfo.last_name;
                    var email = userInfo.email;
                    var id = userInfo.id;
                    if ( typeof(id) == "undefined" )
                        return;
                    showLinkDialog(name, email, id, retry=retry, new_login=true)
                    /*if(retry){
                        showLinkDialog(name, email, id, retry=retry, new_login=true)
                    }
                    else{
                        showLinkDialog(name, email, id, new_login=true)
                    }*/
                }); 
            } else {
                // no user session available, someone you dont know
                $('#fbsignin_header').removeClass('hidden'); 
            }
        }); 
    };
    $(".flogin_retry").click(function(){
        FB.api("/me/", function(userInfo) {
            var name = userInfo.first_name + " " + userInfo.last_name;
            var email = userInfo.email;
            var id = userInfo.id;
            if ( typeof(id) == "undefined" )
                return;
            showLinkDialog(name, email, id, retry=true, new_login=true);
        }); 
    });
});
