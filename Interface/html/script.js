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

    /* Clock */
    display_time();
    setInterval(display_time, 1000);

    /* Register button callbacks */
    $("#wheelchair").on("click", function() {window.location = "wheelchair.html";})
    $("#back").on("click", function() {window.location = "index.html";})
    $("#light").on("click", change_light)
    $("#speed").on("click", change_speed)
    $("#drive").on("click", function() {$.post("/action/drive")})
    $("#horn").on("click", function() {$.post("/action/horn")})
})()
