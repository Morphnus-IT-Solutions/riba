if (typeof(Ch) == 'undefined') {
    Ch = {};
}
Ch.Utils = {
    helpPopup : function(url) {
        var helpWindow = window.open(
            url,
            'InlineHelp',
            'width=500,height=400,resizable=1,scrollbars=1,status=1,toolbar=0,left='+((screen.width/2)-250)+',top='+((screen.height/2)-200));
            helpWindow.focus();
            return false;
    },

    tgd_on_focus : function() {
        var v = this.value;
        //if(this.tagName.toLowerCase() == 'textarea')
        //    v = this.innerHTML;
        if(v == $(this).attr('default_value')) {
            $(this).removeClass('fdgray');
            this.value = '';
            //if(this.tagName.toLowerCase() == 'textarea')
            //    this.innerHTML = '';
        }
    },

    tgd_on_blur : function() {
        var v = this.value;
        //if(this.tagName.toLowerCase() == 'textarea'){
        //    v = this.innerHTML;
        //}
        if(!v) {
            $(this).addClass('fdgray');
            //if(this.tagName.toLowerCase() == 'textarea') {
            //    this.innerHTML = $(this).attr('default_value');
            //}
            this.value = $(this).attr('default_value');
        }
    },

    enable_new_delivery : function() {
        $('div#delivery_address_block input').removeAttr('disabled');
        $('div#delivery_address_block textarea').removeAttr('disabled');
    },

    disable_new_delivery : function() {
        $('div#delivery_address_block input').attr('disabled', true);
        $('div#delivery_address_block textarea').attr('disabled', true);
    }
};
