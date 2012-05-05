from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

register = template.Library()

class FacebookScriptNode(template.Node):
        def render(self, context):
            return """
            <script src="http://connect.facebook.net/en_US/all.js"></script>
            <script>
              FB.init({
                    appId  : '135919719809925',
                    status : true, // check login status
                    cookie : true, // enable cookies to allow the server to access the session
                    xfbml  : true  // parse XFBML
                    });
                FB.ui(
                {
                method: 'permissions.request',
                perms: 'email, user_birthday',
                display: 'iframe'
                },
                function(response) {
                console.log(response); //includes session OBJECT not string AND and an access_token!
                FB.api('/me', function(response){
                alert(response.id);
                alert(response.name);
                alert(response.email);
                fb_connect_ajax(userid, username, email);
                });
                }
                ); 
                function fb_connect_ajax(userid, username, email) {
        
                    var post_string = 'userid=' + userid;
                    post_string = post_string + '&username=' + username;
                    post_string = post_string + '&email=' + email;
    
                    $.ajax({
                        type: "POST",
                        url: "%s",
                        data: post_string,
                        success: function(msg) {
                            window.location = '%s'; //.reload()
                        }
                    });
                } 
              </script>

    
            <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
    
            <script type="text/javascript">
                function login(){
                    url = 'https://www.facebook.com/dialog/oauth?client_id=135919719809925&redirect_uri=http://tinla.chaupaati.in:8000';
                    window.open(url);
                }
            </script>"""       


def facebook_connect_script(parser, token): return FacebookScriptNode()

register.tag(facebook_connect_script)

class FacebookLoginNode(template.Node):
    def render(self, context): 
        return "<div id='fb-root'></div><fb:login-button></fb:login-button>"

def facebook_connect_login_button(parser, token): return FacebookLoginNode()

register.tag(facebook_connect_login_button)
