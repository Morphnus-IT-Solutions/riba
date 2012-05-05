function DigitalTimer(day_div, hour_div, min_div, sec_div, start_day,
        start_hr, start_min, start_sec, type, friday_deal_id ) {
    this.day_div = $(day_div);
    this.hour_div =$(hour_div);
    this.min_div = $(min_div);
    this.sec_div = $(sec_div);
    this.type = type;

    this.start_day = start_day;
    this.start_hr = start_hr;
    this.start_min = start_min;
    this.start_sec = start_sec;
    this.friday_deal_id = friday_deal_id;
    this.status = "on";
};

DigitalTimer.prototype.stop = function() {
    this.start_sec = 0;
    this.start_min = 0;
    this.start_hr = 0;
    this.start_day = 0;
    if(this.friday_deal_id != 0 && this.status == "on"){
        this.status = "off";
        location.reload();
    }
};

DigitalTimer.prototype.display = function() {
    if(this.type == 'battle'){
	if($.browser.mozilla){
	this.day_div.animate({backgroundPosition: "-3px -" + this.start_day * 28 + "px"});
	this.hour_div.animate({backgroundPosition: "-3px -" + this.start_hr * 28 + "px"});
	this.min_div.animate({backgroundPosition: "-3px -" + this.start_min * 28 + "px"});
	this.sec_div.animate({backgroundPosition: "-3px -" + this.start_sec * 28 + "px"});
	}
	else{
        this.day_div.animate({backgroundPositionX: -3, backgroundPositionY: this.start_day * -28});
        this.hour_div.animate({backgroundPositionX: -3, backgroundPositionY:  this.start_hr * -28});
        this.min_div.animate({backgroundPositionX: -3, backgroundPositionY:  this.start_min * -28});
        this.sec_div.animate({backgroundPositionX: -3, backgroundPositionY:  this.start_sec * -28});
	}
    }
    if(this.type == 'steal'){
        this.day_div.html(this.start_day);
        this.hour_div.html(this.start_hr);
        this.min_div.html(this.start_min);
        this.sec_div.html(this.start_sec);
    }
};

DigitalTimer.prototype.tick = function() {
    this.start_sec = this.start_sec -1;
    if(this.start_sec == -1) {
        this.start_min = this.start_min -1;
        this.start_sec = 59;
        if(this.start_min == -1) {
            this.start_hr = this.start_hr -1;
            this.start_min = 59;
            if(this.start_hr == -1) {
                this.start_day = this.start_day -1;
                if(this.start_day != -1) {
                    this.start_hr = 23;
                } else {
                    this.stop();
                }
            }
        }
    }
    this.display();
};

Timers = {
    battleTimer : new DigitalTimer('div.battle_timer div.hr', 
            'div.battle_timer div.min', 'div.battle_timer div.sec'),

    stealTimer : new DigitalTimer('div.steal_timer span.hr', 
            'div.steal_timer span.min', 'div.steal_timer span.sec'),

    tick : function() {
        Timers.battleTimer.tick();
        Timers.stealTimer.tick();
    },


    initBT : function(start_day, start_hr, start_min, start_sec) {
        Timers.battleTimer = new DigitalTimer('div.battle_timer div.day', 'div.battle_timer div.hr', 
                'div.battle_timer div.min', 'div.battle_timer div.sec',
                start_day, start_hr, start_min, start_sec,'battle', 0)
    },

    initST : function(start_day, start_hr, start_min, start_sec) {
        Timers.stealTimer = new DigitalTimer('div.steal_timer span.day', 'div.steal_timer span.hr', 
                'div.steal_timer span.min', 'div.steal_timer span.sec',
                start_day, start_hr, start_min, start_sec,'steal', 0)
    },

    start : function() {
        setInterval('Timers.tick()', 1000);
    }
};
