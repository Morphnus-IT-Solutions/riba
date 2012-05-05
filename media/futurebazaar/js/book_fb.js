        $.fn.get_book_button = function(payment_mode){
            var onSuccess = function(html) {
                $('#book_button').html(html);
            };
            var onError = function() {
            };
            var action = '/orders/book_button'
            var data = 'payment_mode_code=' + payment_mode;
            $.ajax({ url:action,
                data : data,
                success : onSuccess,
                error : onError,
                type : 'POST'
                });
        };
        $.fn.get_payment_page = function(payment_mode,order_id){
            var onSuccess = function(html) {
                $('#payment_option_page').html(html);
            };
            var onError = function() {
                $('#payment_option_page').empty();
            };
            var action = '/orders/payment_option_page'
            var data = 'payment_mode_code=' + payment_mode + '&order_id=' + order_id;
            $.ajax({ url:action,
                data : data,
                success : onSuccess,
                error : onError,
                type : 'POST'
                });
        };
        $('.payment_mode').click(function(){
            var payment_mode = $(this).attr('val');
            var order_id = $('#order_id').val();
            $('#selected_payment_mode').val(payment_mode);
            $.fn.get_payment_page(payment_mode,order_id);
            $.fn.get_book_button(payment_mode);
            $('.payment_mode').each(function(){
                $(this).removeClass('selected');
            });
            $(this).addClass('selected');
            $('#id_payment_mode').val($(this).attr('val'));
            return false;
        });
        var first_mode = $('.payment_mode')[0];
        var payment_mode = $(first_mode).attr('val');
        var order_id = $('#order_id').val();
        $.fn.get_payment_page(payment_mode,order_id);
        $.fn.get_book_button(payment_mode);
