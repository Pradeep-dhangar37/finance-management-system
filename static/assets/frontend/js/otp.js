function clickEvent(first,last){
    if(first.value.length){
        document.getElementById(last).focus();
    }
    var one = $('#ist').val();
    var two = $('#sec').val();
    var three = $('#third').val();
    var four = $('#fourth').val();
    var otp = one + two + three + four;
    console.log(otp);
    $('#otp').val(otp);

} 