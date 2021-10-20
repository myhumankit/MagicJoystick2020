(function()
{
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

    display_time();
    setInterval(display_time, 1000);

    /* Register button callbacks */
    $("#wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#back").on("click", function() {window.location = "index.html";})
    $("#light").on("click", function() {$.post("/action/light");})
})()
