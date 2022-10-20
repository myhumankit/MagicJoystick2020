function load_TV()
{
    // Change volume
    function change_TV_volume(type) {
        AjaxHelper.post("/TV/volume", {type: type});
    }

    // Change other command
    function change_TV_param(type) {
        AjaxHelper.post("/TV/param", {type: type});
    }

    // Change direction
    function change_TV_direction(type) {
        AjaxHelper.post("/TV/direction", {type: type});
    }

    // Change channel number
    function change_TV_number(nb) {
        AjaxHelper.post("/TV/number", {nb: nb});
    }
    

    $("#button_back_ir").on("click", function() {window.location = "IR.html";})

    /* TV IR buttons */
    $("#TV_power").on("click", function() {$.post("/TV/power")})

    $("#TV_mute").on("click", function() {change_TV_volume("mute")})
    $("#TV_volume_up").on("click", function() {change_TV_volume("up")})
    $("#TV_volume_down").on("click", function() {change_TV_volume("down")})

    $('.TV_param').on("click", (e) => {
        e.preventDefault();
        let param = $(e.target).data("param") || $(e.target.parentNode).data("param");
        if (param)
            change_TV_param(param);
        else
            console.log('nop')
    });

    $('.TV_direction').on("click", (e) => {
        e.preventDefault();
        let direction = $(e.target).data("direction") || $(e.target.parentNode).data("direction");
        if (direction)
            change_TV_direction(direction);
        else
            console.log('nop')
    });

    $(".TV_number").on("click", (e) =>{
        e.preventDefault();
        let nb = $(e.target).data("number") || $(e.target.parentNode).data("number");
        if (nb)
            change_TV_number(nb);
        else 
            console.log('nop')
    });
}