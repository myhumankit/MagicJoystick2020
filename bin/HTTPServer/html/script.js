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


    function get_and_update_buttons()
    {
        $.ajax({
            type: "GET",
            url: "/TV_A/buttons",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(result){
                console.log("function get and update buttons 2"),
                console.log(result)
                for ( var i=0 ; i<result["BUTTONS"].length ; i++ ){
                    if(result.BUTTONS[i] === false) {
                        //console.log(i, result.BUTTONS[i], "je dois changer de bg")
                        if (!($("#TV_A_"+i).hasClass("no"))) {
                            $("#TV_A_"+i).addClass("no");
                        }
                    } else {
                        if ($("#TV_A_"+i).hasClass("no")) {
                            $("#TV_A_"+i).removeClass("no");
                        }
                    }
                }
            },
            error: function(errMsg){
                console.log("function get and update buttons error"),
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


    /* TV */
    function change_TV_volume(type)
    {
        $.ajax({
            type: "POST",
            url: "/TV/volume",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }

    function change_TV_param(type)
    {
        $.ajax({
            type: "POST",
            url: "/TV/param",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }

    function change_TV_direction(type)
    {
        $.ajax({
            type: "POST",
            url: "/TV/direction",
            data: JSON.stringify({"type": type}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    
    }

    function change_TV_number(nb)
    {
        $.ajax({
            type: "POST",
            url: "/TV/number",
            data: JSON.stringify({"nb": nb}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        });
    }


    /* TV_A */
    function change_TV_A(id)
    {
        if ($("#TV_A_"+id).hasClass("no")){
            //alert("Veuiller enregistrer la commande puis appuyer sur ok")
            $.ajax({
                type: "POST",
                url: "/TV_A/get",
                data: JSON.stringify({"id": id}),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(data){},
                error: function(errMsg){}
            })
        }
        
        else {
            $.ajax({
            type: "POST",
            url: "/TV_A/control",
            data: JSON.stringify({"id": id}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){},
            error: function(errMsg){}
        })
        };
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
    get_and_update_buttons()

    /* html change pages */
    $("#actuator").on("click", function() {window.location = "actuator.html";})
    $("#button_wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#IR").on("click", function() {window.location = "IR.html";})
    $("#TV").on("click", function() {window.location = "TV.html";})
    $("#A").on("click", function() {window.location = "TV_A.html";})
    $("#button_back_index").on("click", function() {window.location = "index.html";})
    $("#button_back").on("click", function() {window.location = "wheelchair.html";})
    $("#button_back_ir").on("click", function() {window.location = "IR.html";})
    $("#button_light").on("click", function() {window.location = "light.html";})

    /* Wheelchair buttons */
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
    $("#light_1").on("click", function() {change_light(1);})
    $("#light_2").on("click", function() {change_light(2);})
    $("#light_3").on("click", function() {change_light(3);})
    $("#light_4").on("click", function() {change_light(4);})
    $("#light_5").on("click", function() {change_light(5);})
    $("#power").on("click", change_power)
    $("#button_speed").on("click", change_speed)
    $("#button_drive_mode").on("click", function() {$.post("/action/drive")})
    $("#button_horn").on("click", function() {$.post("/action/horn")})


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

    /* TV IR learning buttons */
    $("#TV_A_0").on("click", function() {change_TV_A(0)})
    $("#TV_A_4").on("click", function() {change_TV_A(4)})
    $("#TV_A_8").on("click", function() {change_TV_A(8)})
    $("#TV_A_12").on("click", function() {change_TV_A(12)})
    $("#TV_A_27").on("click", function() {change_TV_A(27)})
    $("#TV_A_22").on("click", function() {change_TV_A(22)})
    $("#TV_A_20").on("click", function() {change_TV_A(20)})
    $("#TV_A_24").on("click", function() {change_TV_A(24)})
    $("#TV_A_26").on("click", function() {change_TV_A(26)})
    $("#TV_A_23").on("click", function() {change_TV_A(23)})
    $("#TV_A_25").on("click", function() {change_TV_A(25)})
    $("#TV_A_16").on("click", function() {change_TV_A(16)})
    $("#TV_A_21").on("click", function() {change_TV_A(21)})
    $("#TV_A_18").on("click", function() {change_TV_A(18)})
    $("#TV_A_13").on("click", function() {change_TV_A(13)})
    $("#TV_A_17").on("click", function() {change_TV_A(17)})
    $("#TV_A_14").on("click", function() {change_TV_A(14)})
    $("#TV_A_1").on("click", function() {change_TV_A(1)})
    $("#TV_A_2").on("click", function() {change_TV_A(2)})
    $("#TV_A_3").on("click", function() {change_TV_A(3)})
    $("#TV_A_5").on("click", function() {change_TV_A(5)})
    $("#TV_A_6").on("click", function() {change_TV_A(6)})
    $("#TV_A_7").on("click", function() {change_TV_A(7)})
    $("#TV_A_9").on("click", function() {change_TV_A(9)})
    $("#TV_A_10").on("click", function() {change_TV_A(10)})
    $("#TV_A_11").on("click", function() {change_TV_A(11)})

    $(window).on("load", set_icons_status)


})()
