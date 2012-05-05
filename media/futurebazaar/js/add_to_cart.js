$(".add_product_to_cart").click(function(e){
    $("#lightbox").css('display','block');
    e.preventDefault();
    var prod_id = $(this).attr("value")
    var href = "/orders/mycart"; 
    var form = $("#add_product_to_cart_form_"+prod_id);
    var form_data = form.serialize();
    show_overlay();
    var onSuccess = function(mycart_html){
        get_cart_popup(mycart_html);
    };  
    var onError = function(){
    };  
    $.ajax({          
        url: href,
        cache: false,
        data:form_data,
        type:"POST",
        success:onSuccess,
        error:onError
   });
});
function get_cart_popup(mycart_html){
    var href = "/orders/cart_popup/?dont_update_cart=1"; 
    var onSuccess = function(html){
        append_lightbox(html)
        $("#cart_popup").html(mycart_html);
        refresh_mycart_js();
        reset_overlay();
    };
    var onError = function(){
    };  
    $.ajax({          
        url: href,
        data:'',
        type:"GET",
        success:onSuccess,
        error:onError
   });
};
