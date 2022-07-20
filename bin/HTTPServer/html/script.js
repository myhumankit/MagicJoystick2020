(function()
{
    var interval = 0;
    var actuatorWatchdogTime = 500 // in ms

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

    function synchro_lights_speed_driveMode()
    {
        $.ajax({
            type: "GET",
            url: "/current/lights-speed-driveMode",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(result){
                if(result.DRIVE_MODE === true) {
                    if (!($("#button_drive_mode").hasClass("on"))) {
                        $("#button_drive_mode").addClass("on");
                    }
                } else {
                        if($("#button_drive_mode").addClass("on")) {
                            $("#button_drive_mode").removeClass("on");
                        }
                }

                str = "" + result.CHAIR_SPEED.toFixed(1) + " km/h";
                $("#current_speed").html(str);

                for ( var i=0 ; i<result["LIGHTS"].length ; i++ ) {
                    light = "light_" + (i+1)
                    if(result["LIGHTS"][i] === true) {
                        sessionStorage.setItem(light, "true")
                        if (!($("#" + light).hasClass("on"))) {
                            $("#" + light).addClass("on");
                        }
                    } else {
                        sessionStorage.setItem(light, "false")
                        if($("#" + light).hasClass("on")) {
                            $("#" + light).removeClass("on");
                        }
                    }
                              
                }
            },
            error: function(errMsg){
                console.log(errMsg)
            }
            })
    }

    function send_light(light_id)
    {
        $.ajax({
            type: "POST",
            url: "/action/light", 
            data: JSON.stringify({"light_id": light_id}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }

    function change_light(light_id)
    {
        let light = 'light_' + light_id;
        if($("#" + light).hasClass("on"))
        {
            sessionStorage.setItem(light, "false")
            $("#" + light).removeClass("on");
        }
        else
        {
            sessionStorage.setItem(light, "true")
            $("#" + light).addClass("on");
        }
        if(light_id<5)
            send_light(light_id)
        else if(light=5)
            $.post("/action/auto_light")
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
            sessionStorage.setItem("power", "false")
            $("#power").removeClass("on");
            send_power("/action/poweroff");
        }
        else
        {
            sessionStorage.setItem("power", "true")
            $("#power").addClass("on");
            send_power("/action/poweron");
        }
    }

    function change_speed()
    {
        let level = 0;

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

    function change_max_speed(level)
    {
        $.ajax({
            type: "POST",
            url: "/action/max_speed", 
            data: JSON.stringify({max_speed: level}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){
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
            },
            error: function(errMsg){}
        });
    }


    function get_max_speed()
    {
        $.ajax({
            type: "GET",
            url: "/action/max_speed", 
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(result){
                for(var i = 1; i <= 5; i++)
                {
                    if(i <= result.MAX_SPEED)
                    {
                        $("#lvl" + i).addClass("on");
                    }
                    else
                    {
                        $("#lvl" + i).removeClass("on");
                    }
                }
            },
            error: function(errMsg){
                console.log(errMsg)
            }
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
        interval = setInterval(send_actuator_ctrl, actuatorWatchdogTime, actuator_num, direction)
    }

    function set_icons_status()
    {
        if (sessionStorage.getItem('power') === 'true') {
            $("#power").addClass("on");
        }
        for (let step = 1; step < 5; step++) {
            let light = "light_" + step
            if (sessionStorage.getItem(light) === "true") {
                $("#" + light).addClass("on");
            }
        }
    }

    /* Clock */
    // setInterval(display_time_battery, 2000);
    // setInterval(synchro_lights_speed_driveMode, 500);

    get_max_speed()
    

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
    $("#button_wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#button_back_index").on("click", function() {window.location = "index.html";})
    $("#button_back").on("click", function() {window.location = "wheelchair.html";})
    $("#button_light").on("click", function() {window.location = "light.html";})
    $("#light_1").on("click", function() {change_light(1);})
    $("#light_2").on("click", function() {change_light(2);})
    $("#light_3").on("click", function() {change_light(3);})
    $("#light_4").on("click", function() {change_light(4);})
    $("#light_5").on("click", function() {change_light(5);})
    $("#lvl1").on("click", function() {change_max_speed(1)})
    $("#lvl2").on("click", function() {change_max_speed(2)})
    $("#lvl3").on("click", function() {change_max_speed(3)})
    $("#lvl4").on("click", function() {change_max_speed(4)})
    $("#lvl5").on("click", function() {change_max_speed(5)})
    $("#power").on("click", change_power)
    $("#button_speed").on("click", change_speed)
    $("#button_drive_mode").on("click", function() {$.post("/action/drive")})
    $("#button_horn").on("click", function() {$.post("/action/horn")})
    $(window).on("load", set_icons_status)


})()
