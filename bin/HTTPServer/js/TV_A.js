function load_TV_A() {  
    // Put the unknown button on red background when TV_A.html page is loaded
    function get_and_update_buttons() {
        AjaxHelper.get("/TV_A/buttons",
            (result) => {
                for (let i = 0; i < result["BUTTONS"].length; i++){
                    if (!result.BUTTONS[i]) {
                        if (!($(`#TV_A_${i}`).hasClass("no"))) {
                            $(`#TV_A_${i}`).addClass("no");
                        }
                    } else if (result.VALIDATE[i]) {
                        if ($(`#TV_A_${i}`).hasClass("no")) {
                            $(`#TV_A_${i}`).removeClass("no");
                        }
                    } else if (!result.VALIDATE[i]) {
                        if (!($(`#TV_A_${i}`).hasClass("no"))) {
                            $(`#TV_A_${i}`).addClass("no");
                        }
                        AjaxHelper.post("/TV_A/delete", {id: i});
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

        if ($(`#TV_A_${id}`).hasClass("no")) {
            popup = window.open("timer.html");
            $(`#TV_A_${id}`).removeClass("no");
            $(`#TV_A_${id}`).addClass("to_check");

            AjaxHelper.post(
                "/TV_A/get",
                {id: id},
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
        } else if ($(`#TV_A_${id}`).hasClass("to_check")) {
            window.location = "IR_check_command.html";
        } else {
            AjaxHelper.post("/TV_A/control", {id: id});
        };
    }

    get_and_update_buttons()
    $("#button_back_ir").on("click", function() {window.location = "IR.html";})

    // TV IR learning buttons
    $(".TV_A").on("click", (e) => {
        e.preventDefault();
        let nb = $(e.target).data("number");
        send_or_get_TV_A(nb);
    });
}