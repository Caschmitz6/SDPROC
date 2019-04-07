function deleteEntry(id)
{
    $.post( "/del_entry", { id: id },
    function(){
        location.reload();
    })
}

function deleteAll(){
    $.post( "/del_entry", { id: -1 },
    function(){
        location.reload();
    })
}