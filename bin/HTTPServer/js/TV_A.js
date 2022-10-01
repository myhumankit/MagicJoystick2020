function load_TV_A()
{  
    // Put the unknown button on red background when TV_A.html page is loaded
    function get_and_update_buttons() {
        AjaxHelper.get("/TV_A/buttons",
            (result) => {
                for (let i = 0; i < result["BUTTONS"].length; i++){
                    if (!result.BUTTONS[i]) {
                        if (!($("#TV_A_"+i).hasClass("no"))) {
                            $("#TV_A_"+i).addClass("no");
                        }
                    } else if (result.VALIDATE[i]) {
                        if ($("#TV_A_"+i).hasClass("no")) {
                            $("#TV_A_"+i).removeClass("no");
                        }
                    } else if (!result.VALIDATE[i]) {
                        if (!($("#TV_A_"+i).hasClass("no"))) {
                            $("#TV_A_"+i).addClass("no");
                        }
                        AjaxHelper.post("/TV_A/delete", {"id": i});
                    }
                }
            },
            (errMsg) => {
                console.log("function get and update buttons error"),
                console.log(errMsg)
            }
        );
    }

    // send the command if the raw command exists, or write the command is a text file
    function send_or_get_TV_A(id) {
        TV_A_id_2 = id;

        if ($("#TV_A_"+id).hasClass("no")) {
            popup = window.open("timer.html");
            $("#TV_A_" + id).removeClass("no");
            $("#TV_A_" + id).addClass("to_check");

            AjaxHelper.post(
                "/TV_A/get",
                {"id": id},
                (result) => {
                    popup.close();
                    if (window.confirm("Commande enregistée, vérifier la nouvelle commande ?")) {
                        popup = window.open("IR_check_command.html");
                    }
                },
                (errMsg) => {
                    popup.close();
                    alert("La commande n'a pas pu être enregistrée");
                    window.location.reload();
                }
            );
        } else if ($("#TV_A_"+id).hasClass("to_check")) {
            window.location = "IR_check_command.html";
        } else {
            AjaxHelper.post("/TV_A/control", {"id": id});
        };
    }

    get_and_update_buttons()
    $("#button_back_ir").on("click", function() {window.location = "IR.html";})

    // TV IR learning buttons
    $("#TV_A_0").on("click", function() {send_or_get_TV_A(0)})
    $("#TV_A_1").on("click", function() {send_or_get_TV_A(1)})
    $("#TV_A_2").on("click", function() {send_or_get_TV_A(2)})
    $("#TV_A_3").on("click", function() {send_or_get_TV_A(3)})
    $("#TV_A_4").on("click", function() {send_or_get_TV_A(4)})
    $("#TV_A_5").on("click", function() {send_or_get_TV_A(5)})
    $("#TV_A_6").on("click", function() {send_or_get_TV_A(6)})
    $("#TV_A_7").on("click", function() {send_or_get_TV_A(7)})
    $("#TV_A_8").on("click", function() {send_or_get_TV_A(8)})
    $("#TV_A_9").on("click", function() {send_or_get_TV_A(9)})
    $("#TV_A_10").on("click", function() {send_or_get_TV_A(10)})
    $("#TV_A_11").on("click", function() {send_or_get_TV_A(11)})
    $("#TV_A_12").on("click", function() {send_or_get_TV_A(12)})
    $("#TV_A_27").on("click", function() {send_or_get_TV_A(27)})
    $("#TV_A_22").on("click", function() {send_or_get_TV_A(22)})
    $("#TV_A_20").on("click", function() {send_or_get_TV_A(20)})
    $("#TV_A_24").on("click", function() {send_or_get_TV_A(24)})
    $("#TV_A_26").on("click", function() {send_or_get_TV_A(26)})
    $("#TV_A_23").on("click", function() {send_or_get_TV_A(23)})
    $("#TV_A_25").on("click", function() {send_or_get_TV_A(25)})
    $("#TV_A_16").on("click", function() {send_or_get_TV_A(16)})
    $("#TV_A_21").on("click", function() {send_or_get_TV_A(21)})
    $("#TV_A_18").on("click", function() {send_or_get_TV_A(18)})
    $("#TV_A_13").on("click", function() {send_or_get_TV_A(13)})
    $("#TV_A_17").on("click", function() {send_or_get_TV_A(17)})
    $("#TV_A_14").on("click", function() {send_or_get_TV_A(14)})
}