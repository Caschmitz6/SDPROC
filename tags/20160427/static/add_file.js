function moveFile()
{
    var found = 0;
    $("tr.item").each(function(){
        var row = $(this);
        if ($(row).hasClass( "highlight" ))
        {
            found = 1;
            $.post( "/make_name" , {id : $('td:first', $(row)).attr('id')},
            function(data){
                var temp = data;
                $('#sel1')
                    .append($('<option></option>')
                    .text(data)
                    .attr('value', $('td:first', $(row)).attr('id')))
            })
            $('#finito').prop('disabled', false);
        }
    })
    if (found == 0)
    {
        alert('No File Selected')
    }
}




function proceed()
{
    window.location.replace("http://cleo.aps.anl.gov:5000/data")
}