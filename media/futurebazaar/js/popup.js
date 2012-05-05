$(document).ready(function() { 					 
    $('.popup').click(function(e) {	
        e.preventDefault();
        var href = $(this).attr('href');  
        var onError = function(){};
        var onSuccess = function(html){	
            show_popup(html);
        };
        $.ajax({		  
            url: href,
            cache: false,
            success: onSuccess,
            error : onError,
            type : 'GET'
        });			
    });		
});

show_popup = function(html){
    $("#lightbox").css('display','block');	  
    var left="<script> var pageWidth=1004; var winWidth=$(window).width();  var leftMar=(winWidth - pageWidth)/2 ; var conWidth=$(\".popup_con\").width(); var pos= (pageWidth - conWidth)/2 ; var leftPos=(leftMar + pos + 'px'); $(\".popup_con\").css(\'left\', leftPos); $(\".popup_close\").css(\'left\', leftMar + pos + conWidth - 40 + 'px' ); <\/script>"	;					   
    var top="<script> var winHeight=$(window).height();  var conHeight=$(\".popup_con\").height(); var topMar= ((winHeight - conHeight)/2); if (topMar < 80) { topMar= 80;}  var topPos=(topMar + 'px');  $(\".popup_con\").css(\'top\', topPos); $(\".popup_close\").css(\'top\', topMar + 14 + 'px'); <\/script>"	;
    var close_button="<div class=\"popup_close f11\">close x</div> <script>$('.popup_close').click(function() {$(\"#lightbox\").empty(); });</script>";
    var popup_overlay="<div class=\"popup_overlay\"></div> <script>var winWidth=$(document).width(); var docHeight=$(document).height(); $(\".popup_overlay\").css(\'width\', winWidth + 'px'); $(\".popup_overlay\").css(\'height\', docHeight + 'px'); <\/script>";
    $("#lightbox").append(popup_overlay + close_button + html + left + top);	
}
