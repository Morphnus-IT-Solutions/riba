
$('#test').click(function() {
    alert($('#id_feature'));
    alert('test');
    var action = "/catalog/test";
    var data = "featureId=1&test=true";
    var onSuccess = function(status,data){
        alert(status);
        alert(data);
    };
    var onError = function(xhr, textStatus,error){
        alert('fail');
    };
    $.ajax({ url:action,
        data : data,
        success : onSuccess,
        error : onError,
        type : 'POST'
        });
});

$('#id_feature').change(function(){
    var action = "/catalog/feature";
    var data = "featureId=" + $(this).val()
    var onSuccess = function(status,data){
        alert(data);
    };
    var onError = function(){
        alert('fail');
    };
    $.ajax({url:action,
        data : data,
        success : onSuccess,
        error : onError,
        type : 'GET'
    });
});
