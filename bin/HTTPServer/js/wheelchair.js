function load_wheelchair() {
    let actuatorWatchdogTime = 500 // in ms

    /* Get the current values of drive mode, speed and if lights are on */
    function synchro_lights_speed_driveMode() {
        AjaxHelper.get("/current/lights-speed-driveMode",
            (result) => {
                if(result.DRIVE_MODE === true) {
                    if (!($("#button_drive_mode").hasClass("on"))) {
                        $("#button_drive_mode").addClass("on");
                    }
                } else {
                    if($("#button_drive_mode").addClass("on")) {
                        $("#button_drive_mode").removeClass("on");
                    }
                }

                str = `${result.CHAIR_SPEED.toFixed(1)} km/h`;
                $("#current_speed").html(str);

                for (let i = 0; i < result["LIGHTS"].length; i++) {
                    light = `light_${i + 1}`;
                    if (result["LIGHTS"][i]) {
                        sessionStorage.setItem(light, "true")
                        if (! $(`#${light}`).hasClass("on")) {
                            $(`#${light}`).addClass("on");
                        }
                    } else {
                        sessionStorage.setItem(light, "false")
                        if($(`#${light}`).hasClass("on")) {
                            $(`#${light}`).removeClass("on");
                        }
                    }
                }
            },
            (errMsg) => {
                console.log(errMsg)
            }
        );
    }

    // Send the light on/off command
    function send_light(light_id) {
        AjaxHelper.post("/action/light", {light_id: light_id});
    }

    // Change the light on/off command on web
    function change_light(light_id) {
        let light = `light_${light_id}`;

        if ($(`#${light}`).hasClass("on")) {
            sessionStorage.setItem(light, "false")
            $(`#${light}`).removeClass("on");
        } else {
            sessionStorage.setItem(light, "true")
            $(`#${light}`).addClass("on");
        }

        if (light_id < 5) {
            send_light(light_id);
        } else if(light = 5) {
            $.post("/action/auto_light");
        }
    }

    /* Send power command to wheelchair */
    function send_power(url) {
        AjaxHelper.post(url);
    }

    // Set speed bar to the provide speed
    function setSpeed(speed) {
        for(let i = 1; i <= 5; i++) {
            if(i <= speed) {
                $(`#lvl${i}`).addClass("on");
            } else {
                $(`#lvl${i}`).removeClass("on");
            }
        }
    }
    
    /* Change power on/off command on web */
    function change_power() {
        if($("#power").hasClass("on")) {
            sessionStorage.setItem("power", "false")
            $("#power").removeClass("on");
            send_power("/action/poweroff");
        } else {
            sessionStorage.setItem("power", "true")
            $("#power").addClass("on");
            send_power("/action/poweron");
        }
    }

    /* Speed +1 */
    function add_speed() {   
        let level = 0;

        for (let i = 1; i <= 5; i++) {
            if (!$(`#lvl${i}`).hasClass("on")) {
                level = i;
                break;
            }
        }

        level = level === 0 ? 1 : level

        setSpeed(level);
        AjaxHelper.post("/action/max_speed", {max_speed: level});
    }

    // Change the max speed level directly on web
    function change_max_speed(level) {
        AjaxHelper.post(
            "/action/max_speed",
            {max_speed: level},
            (result) => {
                setSpeed(level);
            }
        );
    }

    // Get the max speed level on load
    function get_max_speed() {
        AjaxHelper.get(
            "/action/max_speed",
            (result) => {
                setSpeed(result.MAX_SPEED);
            },
            (errMsg) => {
                console.log(errMsg)
            }
        );
    }

    // Send actuator command 
    function send_actuator_ctrl(actuator_num, direction) {
        AjaxHelper.post(
            "/action/actuator_ctrl",
            {actuator_num: actuator_num, direction: direction}
        );
    }
    
    /* Timer actuator command */
    function actuator_ctrl(actuator_num, direction) {
        if (interval) {
            /* clear existing periodic send_actuator_ctrl in case we missed a mouse up */
            clearInterval(interval)   
        }
        /* TODO: set frequency with a static variable -> command must be sent every 500 ms as a safety measure */
        interval = setInterval(send_actuator_ctrl, actuatorWatchdogTime, actuator_num, direction)
    }


    function set_icons_status() {
        if (sessionStorage.getItem('power') === 'true') {
            $("#power").addClass("on");
        }

        for (let step = 1; step < 5; step++) {
            let light = `light_${step}`
            if (sessionStorage.getItem(light) === "true") {
                $(`#${light}`).addClass("on");
            }
        }
    }

    get_max_speed()
    setInterval(synchro_lights_speed_driveMode, 500);
    $(window).on("load", set_icons_status)

    // Wheelchair buttons
    $('.actuator').mouseup(() => { clearInterval(interval) });
    $('.actuator').mousedown((e) => {
        let id = e.target.id,
            exploded = id.split("_");
        actuator_ctrl(exploded[1], exploded[2]);
    });

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
    $("#button_speed").on("click", add_speed)
    $("#button_drive_mode").on("click", function() {$.post("/action/drive")})
    $("#button_horn").on("click", function() {$.post("/action/horn")})

}