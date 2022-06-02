(function()
{
    var interval = 0;
    /* Display time every second */
    function pad(n)
    {
        return ("0" + n).slice(-2)
    }

    function display_time()
    {   
        var now = new Date();

        str = "" + pad(now.getHours()) +":" + pad(now.getMinutes());
        $("#time").html(str);
    }

    function change_light()
    {
        var on;

        if($("#light").hasClass("on"))
        {
            $("#light").removeClass("on");
            on = false;
        }
        else
        {
            $("#light").addClass("on");
            on = true;
        }

        $.ajax({
            type: "POST",
            url: "/action/light", 
            data: JSON.stringify({on: (on?1:0)}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }

    function send_power(url)
    {

        $.ajax({
            type: "POST",
            url: url, 
            success: function(data){},
            error: function(errMsg){}
        });
    }
    
    
    function change_power()
    {
        if($("#power").hasClass("on"))
        {
            $("#power").removeClass("on");
            send_power("/action/poweroff");
        }
        else
        {
            $("#power").addClass("on");
            send_power("/action/poweron");
        }
    }

    function change_speed()
    {
        var level = 0;

        for(var i = 1; i <= 5; i++)
        {
            if($("#lvl" + i).hasClass("on"))
            {
                level++;
            }
        }

        if(level == 5)
        {
            level = 1;
        }
        else
        {
            level++;
        }
        
        for(var i = 1; i <= 5; i++)
        {
            if(i <= level)
            {
                $("#lvl" + i).addClass("on");
            }
            else
            {
                $("#lvl" + i).removeClass("on");
            }
        }

        $.ajax({
            type: "POST",
            url: "/action/max_speed", 
            data: JSON.stringify({max_speed: level}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }

    
    function send_actuator_ctrl(actuator_num, direction)
    {
        $.ajax({
            type: "POST",
            url: "/action/actuator_ctrl", 
            data: JSON.stringify({"actuator_num": actuator_num, "direction": direction}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }
    
    function actuator_ctrl(actuator_num, direction)
    {
        if (interval) {
            /* clear existing periodic send_actuator_ctrl in case we missed a mouse up */
            clearInterval(interval)   
        }
        /* TODO: set frequency with a static variable -> command must be sent every 500 ms as a safety measure */
        interval = setInterval(send_actuator_ctrl, 500, actuator_num, direction)
    }

    /* Clock */
    display_time();
    setInterval(display_time, 1000);

    /* Register button callbacks */
    $("#actuator").on("click", function() {window.location = "actuator.html";})
    $("#actuator_0_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_0_0").mousedown(function() {actuator_ctrl(0, 0);})
    $("#actuator_0_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_0_1").mousedown(function() {actuator_ctrl(0, 1);})
    $("#actuator_1_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_1_0").mousedown(function() {actuator_ctrl(1, 0);})
    $("#actuator_1_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_1_1").mousedown(function() {actuator_ctrl(1, 1);})
    $("#actuator_2_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_2_0").mousedown(function() {actuator_ctrl(2, 0);})
    $("#actuator_2_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_2_1").mousedown(function() {actuator_ctrl(2, 1);})
    $("#actuator_3_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_3_0").mousedown(function() {actuator_ctrl(3, 0);})
    $("#actuator_3_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_3_1").mousedown(function() {actuator_ctrl(3, 1);})
    $("#actuator_4_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_4_0").mousedown(function() {actuator_ctrl(4, 0);})
    $("#actuator_4_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_4_1").mousedown(function() {actuator_ctrl(4, 1);})
    $("#actuator_5_0").mouseup(function() {clearInterval(interval);})
    $("#actuator_5_0").mousedown(function() {actuator_ctrl(5, 0);})
    $("#actuator_5_1").mouseup(function() {clearInterval(interval);})
    $("#actuator_5_1").mousedown(function() {actuator_ctrl(5, 1);})
    $("#wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#back").on("click", function() {window.location = "index.html";})
    $("#back-wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#light").on("click", change_light)
    $("#power").on("click", change_power)
    $("#speed").on("click", change_speed)
    $("#drive").on("click", function() {$.post("/action/drive")})
    $("#horn").on("click", function() {$.post("/action/horn")})


})()
