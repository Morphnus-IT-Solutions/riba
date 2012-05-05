        $.fn.get_book_button = function(payment_option){
            var onSuccess = function(html) {
                $('#book_button').html(html);
            };
            var onError = function() {
                alert('error');
            };
            var action = '/orders/book_button'
            var data = 'payment_option=' + payment_option;
            $.ajax({ url:action,
                data : data,
                success : onSuccess,
                error : onError,
                type : 'POST'
                });
        };
        $.fn.get_payment_page = function(payment_option,order_id){
            var onSuccess = function(html) {
                $('#payment_option_page').html(html);
            };
            var onError = function() {
                $('#payment_option_page').empty();
            };
            var action = '/orders/payment_option_page'
            var data = 'payment_option=' + payment_option + '&order_id=' + order_id;
            $.ajax({ url:action,
                data : data,
                success : onSuccess,
                error : onError,
                type : 'POST'
                });
        };
        $('.payment_mode').click(function(){
            var list = $(this).attr('val').split('#');
            var payment_mode = list[0];
            var payment_option = list[1];
            var order_id = $('#order_id').val();
            $('#selected_payment_mode').val(payment_mode);
            $.fn.get_payment_page(payment_option,order_id);
            $.fn.get_book_button(payment_option);
            $('.payment_mode').each(function(){
                $(this).removeClass('selected');
            });
            $(this).addClass('selected');
            $('#id_payment_mode').val($(this).attr('val'));
            return false;
        });
        var first_mode = $('.payment_mode')[0];
        var list = $(first_mode).attr('val').split('#');
        var payment_mode = list[0];
        var payment_option = list[1];
        var order_id = $('#order_id').val();
        $.fn.get_payment_page(payment_option,order_id);
        $.fn.get_book_button(payment_option);
        $("<style type='text/css'>.pm_min_height{min-height:" + $('#payment_options_length').val() + ";}</style>").appendTo("head");
        $('.payment_actions').addClass("pm_min_height");
