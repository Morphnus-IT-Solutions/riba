/**
 * jQuery Plugin for creating AJAX auto-suggest textfield
 * @requires jQuery 1.2 or later
 *
 * Copyright (c) 2010 Lucky
 * Licensed under the GPL license:
 *   http://www.gnu.org/licenses/gpl.html
 */

(function($) {
	function suggestion(callBackUrl, textFieldId){
		var divId="holder_" + textFieldId;
		this.divId="#" + divId;
		
		this.textFieldId="#" + textFieldId;
		this.shield=null;
		this.callBackUrl=callBackUrl;
		
		var width=$(this.textFieldId).width() + 3;
		var minChars=1;
		var currRow=0;
		var suggestRow="suggest_row";
		var suggestItem="suggest_item";
		
		if($.browser.msie){
			if(parseInt($.browser.version)<7){
				var iframeId="shield_" + textFieldId;
				
				$(this.textFieldId).after('<iframe frameborder="0" id="' + iframeId + '"></iframe>');
				$("#" + iframeId).hide();
				
				this.shield="#" + iframeId;
			}
		}
		
		if(this.shield==null){
			var element=$(this.textFieldId);
		}
		else{
			var element=$(this.shield);
		}
		
		element.after('<div class="suggestions" id="' + divId + '"></div>');
		
		$(this.textFieldId).attr("autocomplete", "off");
		
		$(this.divId).hide();
		
		var me=this;
		$(this.textFieldId).keyup(
			function(e){
				if(e.keyCode!=37 && e.keyCode!=38 && e.keyCode!=39 && e.keyCode!=40 && e.keyCode!=13){
					if($(this).val().length>=minChars){
						$.ajax({
							url:me.callBackUrl + $(this).val(),
							success:function(data){
								var arr=eval(data);
								var html="";
								
								currRow=0;
								
								if(arr.length>0){
									for(i=0;i<arr.length;i++){
										cssClass=suggestItem;
										
										if(i==0){
											cssClass+=" first";
										}
										if(i==(arr.length-1)){
											cssClass+=" last";
										}
										
										html+='<div id="' + suggestRow + (i+1) + '" class="' + cssClass + '">' + arr[i].replace(new RegExp('(' + $(me.textFieldId).val() + ')', 'gi'), "<b>$1</b>") + '</div>';
									}
									
									$(me.divId).html(html);
									
									for(i=1;i<=arr.length;i++){
										$(me.divId + " #" + suggestRow + i).mouseover(function(e){
											me.unSelectAll(this);
											$(this).addClass("selected");
											$(me.textFieldId).val($(this).text());
										});
										
										$(me.divId + " #" + suggestRow + i).mouseout(function(e){
											$(this).removeClass("selected");
										});
										
										$(me.divId + " #" + suggestRow + i).click(function(e){
											me.hide();
										});
									}
									
									me.show($(me.divId + " ." + suggestItem).height() * arr.length);
								}
								else{
									me.hide();
								}
							},
							error: function(xhr, status, ex){
								alert('There is an error with the request');
							}
						});
					}
					else{
						me.hide();
					}
				}
				else{
					if($(me.divId).css("display")!="none"){
						checkKey(e);
					}
				}
			}
		);
		
		$(this.textFieldId).keypress(
			function(e){
				if(e.keyCode==13){
					return false;
				}
				
				return true;
			}
		);
		
		$(this.textFieldId).bind(
			"blur",
			function(e){
				me.hide();
			}
		);
		
		this.show=function(height){
			$(this.divId).css({
				"position":"absolute",
				"left":$(this.textFieldId).position().left + "px",
				"top":$(this.textFieldId).position().top + $(this.textFieldId).height() + 5 + "px",
				"height":height + "px"
			});
			
			$(this.divId).css({
				"width":width + "px"
			});
			
			$(this.divId + " ." + suggestItem).css({
				"width":width + "px",
				"overflow":"hidden"
			});
			
			$(this.divId).show();
			
			if(this.shield!=null && this.shield!=undefined && this.shield!=""){
				$(this.shield).css({
					"position":"absolute",
					"width":$(this.divId).width() + "px",
					"height":$(this.divId).height() - 2 + "px",
					"left":$(this.divId).position().left - 2 + "px",
					"top":$(this.divId).position().top + "px"
				});
				
				$(this.shield).show();
			}
		}
		
		this.hide=function(){
			if(this.shield!=null && this.shield!=undefined && this.shield!=""){
				$(this.shield).hide();
			}
			
			$(this.divId).hide();
		}
		
		this.unSelectAll=function(div){
			var id=$(div).attr("id");
			var rows=$(me.divId + " ." + suggestItem).get().length;
			
			for(i=1;i<=rows;i++){
				$(me.divId + " #" + suggestRow + i).removeClass("selected");
			}
			
			currRow=parseInt(id.replace(suggestRow, ""));
			var rgx=/^[0-9]+$/;
			if(!rgx.test(currRow)){
				currRow=0;
			}
		}
		
		this.setWidth=function(w){
			width=w;
		}
		
		this.setMinChars=function(c){
			minChars=c;
		}
		
		function checkKey(e){
			if($(me.divId).css("display")!="none"){
				var rows=$(me.divId  + " ." + suggestItem).get().length;
				if(e.keyCode==40){
					currRow++;
					if(currRow<=rows){
						if(currRow>0){
							$(me.divId + " #" + suggestRow + (currRow-1)).removeClass("selected");
						}
						
						$(me.divId + " #" + suggestRow + currRow).addClass("selected");
						$(me.textFieldId).val($(me.divId + " #" + suggestRow + currRow).text());
					}
					else{
						currRow=rows;
					}
				}
				else if(e.keyCode==38){
					currRow--;
					if(currRow>0){
						if(currRow<rows){
							$(me.divId + " #" + suggestRow + (currRow+1)).removeClass("selected");
						}
						
						$(me.divId + " #" + suggestRow + currRow).addClass("selected");
						$(me.textFieldId).val($(me.divId + " #" + suggestRow + currRow).text());
					}
					else{
						currRow=1;
					}
				}
				else if(e.keyCode==13){
					me.hide();
				}
			}
			
			return true;
		}
	}
	
	$.fn.suggestion = function(options) {
		var defaultOptions = {
			width: null,
			minChars: null
		};
		$.extend(defaultOptions, options);
		
		$(this).each(function() {
			var obj = new suggestion(options.url, $(this).attr('id'));
			
			if(options.width!=null){
				obj.setWidth(options.width);
			}
			
			if(options.minChars!=null){
				obj.setMinChars(options.minChars);
			}
		});
	}
})(jQuery);