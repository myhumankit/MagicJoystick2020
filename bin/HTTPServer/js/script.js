function load()
{
    var interval = 0;

    /* Display time every second */
    function pad(n)
    {
        return ("0" + n).slice(-2)
    }

    function display_time_battery()
    {   
        let now = new Date();
        $.ajax({
            type: "GET",
            url: "/current/time-battery",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(result){
                str = "" + pad(now.getHours()) +":" + pad(now.getMinutes());
                $("#time").html(str);
                str = "" + result.BATTERY_LEVEL.toFixed() + "%";
                $("#battery").html(str);
            },
            error: function(errMsg){
                console.log(errMsg)
            }
            })
    }

    
    /* Clock and battery every 10 seconds */
    display_time_battery()
    setInterval(display_time_battery, 10000);

    /* html change pages */
    $("#actuator").on("click", function() {window.location = "actuator.html";})
    $("#button_wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#IR").on("click", function() {window.location = "IR.html";})
    $("#TV").on("click", function() {window.location = "TV.html";})
    $("#TV_A").on("click", function() {window.location = "TV_A.html";})
    $("#button_back_index").on("click", function() {window.location = "index.html";})
    $("#button_back").on("click", function() {window.location = "wheelchair.html";})
    $("#button_light").on("click", function() {window.location = "light.html";})

}