function load_TV()
{
    // Change volume
    function change_TV_volume(type) {
        $.ajax({
            type: "POST",
            url: "/TV/volume",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {},
            error: function(errMsg) {}
        });
    }

    // Change other command
    function change_TV_param(type) {
        $.ajax({
            type: "POST",
            url: "/TV/param",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {},
            error: function(errMsg) {}
        });
    }

    // Change direction
    function change_TV_direction(type) {
        $.ajax({
            type: "POST",
            url: "/TV/direction",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {},
            error: function(errMsg) {}
        });
    }

    // Change channel number
    function change_TV_number(nb) {
        $.ajax({
            type: "POST",
            url: "/TV/number",
            data: JSON.stringify({"nb": nb}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {},
            error: function(errMsg) {}
        });
    }
    

    $("#button_back_ir").on("click", function() {window.location = "IR.html";})

    /* TV IR buttons */
    $("#TV_power").on("click", function() {$.post("/TV/power")})
    $("#TV_mute").on("click", function() {change_TV_volume("mute")})
    $("#TV_volume_up").on("click", function() {change_TV_volume("up")})
    $("#TV_volume_down").on("click", function() {change_TV_volume("down")})
    $("#TV_exit").on("click", function() {change_TV_param("exit")})
    $("#TV_home").on("click", function() {change_TV_param("home")})
    $("#TV_info").on("click", function() {change_TV_param("info")})
    $("#TV_menu").on("click", function() {change_TV_param("menu")})
    $("#TV_return").on("click", function() {change_TV_param("return")})
    $("#TV_source").on("click", function() {change_TV_param("source")})
    $("#TV_tools").on("click", function() {change_TV_param("tools")})
    $("#TV_left").on("click", function() {change_TV_direction("left")})
    $("#TV_down").on("click", function() {change_TV_direction("down")})
    $("#TV_right").on("click", function() {change_TV_direction("right")})
    $("#TV_up").on("click", function() {change_TV_direction("up")})
    $("#TV_ok").on("click", function() {change_TV_direction("ok")})
    $("#TV_0").on("click", function() {change_TV_number("0")})
    $("#TV_1").on("click", function() {change_TV_number("1")})
    $("#TV_2").on("click", function() {change_TV_number("2")})
    $("#TV_3").on("click", function() {change_TV_number("3")})
    $("#TV_4").on("click", function() {change_TV_number("4")})
    $("#TV_5").on("click", function() {change_TV_number("5")})
    $("#TV_6").on("click", function() {change_TV_number("6")})
    $("#TV_7").on("click", function() {change_TV_number("7")})
    $("#TV_8").on("click", function() {change_TV_number("8")})
    $("#TV_9").on("click", function() {change_TV_number("9")})
}