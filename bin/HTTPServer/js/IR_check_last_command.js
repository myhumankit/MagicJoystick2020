function load_IR_check()
{   
    // List of all the supported TV icon
    let button_TV = [
        "svg_icon/button_power.svg", "svg_icon/button_1.svg", "svg_icon/button_2.svg", "svg_icon/button_3.svg", 
        "svg_icon/mute.svg", "svg_icon/button_4.svg", "svg_icon/button_5.svg", "svg_icon/button_6.svg", 
        "svg_icon/volume_up.svg", "svg_icon/button_7.svg", "svg_icon/button_8.svg", "svg_icon/button_9.svg", 
        "svg_icon/volume_down.svg", "svg_icon/up.svg", "svg_icon/button_0.svg", "",
        "svg_icon/left.svg", "svg_icon/ok.svg", "svg_icon/right.svg", "",
        "svg_icon/TV_info.svg", "svg_icon/down.svg", "svg_icon/TV_home.svg", "svg_icon/TV_source.svg", 
        "svg_icon/TV_menu.svg", "svg_icon/TV_tools.svg", "svg_icon/TV_return.svg", "svg_icon/TV_exit.svg"
    ]
 
    // Change the background image of the last recorded command (or -1 if none)
    function last_command_id() {   
        $.ajax({
            type: "POST",
            url: "TV_A/last-get",
            success: function(data) {
                document.getElementById("last_command_id").style.backgroundImage = data !== -1
                    ? `url(${button_TV[data]})`
                    : "url(svg_icon/-1.svg)";
            },
            error: function(errMsg) {
            }
        });
    }

    // Delete the last recorded command
    function delete_command() {   
        alert("Voulez-vous vraiment supprimer la commande ?")
        // Condition ?
        AjaxHelper.post("/TV_A/delete",
            {},
            (result) => { window.location = "TV_A.html"; },
            (errMsg) => { window.location = "TV_A.html"; }
        );
        
    }
    
    // Modify the last recorded command
    function modify_command() {
        popup = window.open("timer.html");

        AjaxHelper.post(
            "/TV_A/last-modify",
            (data) => {
                popup.close();
                alert("Commande enregistée, vérifier la nouvelle commande ?")
            },
            (errMsg) => {
                popup.close();
                alert("La commande n'a pas pu être enregistrée");
            }
        );
    }

    // Validate the last recorded command and register it in "database"
    function validate_command() {
        AjaxHelper.post(
            "TV_A/last-validate",
            (data) => {
                $("#TV_A_" + data).removeClass("to_check");
                window.location = "TV_A.html"
            }
        );
    }


    last_command_id();

    // IR check command buttons 
    $("#launch").on("click", function() {$.post("/TV_A/last-launch")})
    $("#delete").on("click", delete_command)
    $("#modify").on("click", modify_command)
    $("#validate").on("click", validate_command)
}