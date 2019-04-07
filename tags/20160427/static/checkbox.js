$(document).ready(updateBoxes())


//Maybe use this for client-side only sessions later?
//$(window).unload(rememberBoxes())
/*
function rememberBoxes()
{
    var checkboxes = $(":checkbox")
    '<%session["checkboxes"] = "' + checkboxes + '"; %>';
}
*/


function updateBoxes()
{
    var checkboxes = document.getElementById("checkboxes")
    status = checkboxes.getAttribute("status")
    status = status.toString();
    status = status.replace(/u/gi, '')
    status = status.replace(/'/gi, '')
    status = status.replace(/\"/gi, '')
    status = status.replace(/\[/gi, '')
    status = status.replace(/\]/gi, '')
    var checkboxes = status.split(", ")
    $(":checkbox").each(function()
    {
        if ($.inArray($(this).attr('value'), checkboxes) == -1)
        {
            $(this).attr('checked', false);
        }
        else
        {
            $(this).attr('checked', true);
        }
    })
}