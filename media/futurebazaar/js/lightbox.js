var overlay_dim="<script> var docHeight=$(document).height(); $(\".overlay\").css(\'height\', docHeight); var winWidth=$(window).width(); $(\".overlay\").css(\'height\', docHeight); $(\".overlay\").css(\'width\', winWidth);<\/script>";
var overlay="<div class=\"overlay\"> <div class=\"overlay_loader\"></div></div>";
function refresh_lightbox(){
    $(".cart_lightbox").click(function(e){
        e.preventDefault();
        var href = $(this).attr("href"); 
        open_popup(href);
    });
}
$(".lightbox").click(function(e){	
    e.preventDefault();
    var href = $(this).attr("href"); 
    open_popup(href);
});
document.onkeyup = lightbox_keycheck;
function lightbox_keycheck(e)
{
    try{
        var KeyID = e.keyCode;
        if(KeyID == 27){
            $(".lightbox_close").trigger("click");
        }
    }
    catch(e){}
}

refresh_lightbox();
$('.lightbox_overlay').click(function(e) {	
    show_overlay();
});
function open_popup(href){
    $("#lightbox").css("display","block");	  
    show_overlay();
    var data = '';
    var onSuccess = function(html){	
        show_lightbox(html);
	//commented to fix ie8 issue
        //show_subscription_lightbox(html);
    };
    var onError = function(){
    };
    $.ajax({		  
        url: href,
        cache: false,
        data:data,
        type:"GET",
        success:onSuccess,
        error:onError
    });
};
function show_lightbox(html){
    show_overlay();
    append_lightbox(html);
};
function append_lightbox(html){
    var left = "<script> var pageWidth=980; var winWidth=$(window).width();  var leftMar=(winWidth - pageWidth)/2 ; var conWidth=$(\".con\").width(); var pos= (pageWidth - conWidth)/2 ; var leftPos=(leftMar + pos + 'px'); $(\".con\").css(\'left\', leftPos); $(\".lightbox_close\").css(\'left\', leftMar + pos + conWidth - 48 + 'px' ); <\/script>"	;					   
    var top = "<script> var winHeight=$(window).height();  var conHeight=$(\".con\").height(); var topMar= ((winHeight - conHeight)/8); if (topMar < 60) { topMar= 60;}  var topPos=(topMar + 'px');  $(\".con\").css(\'top\', topPos); $(\".lightbox_close\").css(\'top\', topMar + 15 + 'px'); <\/script>"	;
    var close_button = "<div class=\"lightbox_close f11\">Close x</div> <script>$('.lightbox_close').click(function() {close_lightbox()});</script>";
    $("#lightbox").append(close_button + html + left + top);	
};
function show_overlay(){
    $("#lightbox").html(overlay_dim + overlay);							   
};
function append_overlay(){
    $(".overlay").css("z-index","1006");
};
function reset_overlay(){
    $(".overlay").css("z-index","1000");
};
function close_lightbox(){
    $("#lightbox").empty();
    $("#lightbox").css('display','none'); 
    /*
    var href = "/get_cart_info/";
    var data = '';
    var onSuccess = function(response){	
        var response_htmls = $.parseJSON(response);
        $("#header_cart").html(response_htmls.cart_html);
        $("#rightpanel_cart").html(response_htmls.order_info_html);
        refresh_header_cart();
        refresh_lightbox();
    };    		
    $.ajax({		  
        url: href,
        cache: false,
        data:data,
        type:"GET",
        success:onSuccess
    });*/
}

function show_subscription_lightbox(html){
    var left="<script> var pageWidth=1004; var winWidth=$(window).width();  var leftMar=(winWidth - pageWidth)/2 ; var conWidth=$(\".popup_con\").width(); var pos= (pageWidth - conWidth)/2 ; var leftPos=(leftMar + pos + 'px'); $(\".popup_con\").css(\'left\', leftPos); $(\".popup_close\").css(\'left\', leftMar + pos + conWidth - 40 + 'px' ); <\/script>"	;
					   
	var top="<script> var winHeight=$(window).height();  var conHeight=$(\".popup_con\").height(); var topMar= ((winHeight - conHeight)/2); if (topMar < 80) { topMar= 80;}  var topPos=(topMar + 'px');  $(\".popup_con\").css(\'top\', topPos); $(\".popup_close\").css(\'top\', topMar + 14 + 'px'); <\/script>"	;


    var close_button="<div class=\"popup_close f11\">close x</div> <script>$('.popup_close').click(function() {$(\"#lightbox\").empty(); });</script>";
    var popup_overlay="<div class=\"popup_overlay\"></div> <script>var winWidth=$(document).width(); var docHeight=$(document).height(); $(\".popup_overlay\").css(\'width\', winWidth + 'px'); $(\".popup_overlay\").css(\'height\', docHeight + 'px'); <\/script>";

    $("#lightbox").append(popup_overlay + close_button + html  + left + top);	
}

