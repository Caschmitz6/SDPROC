$( "#fileForm" ).submit(function(event){
    event.preventDefault();
    sendfileForm();
});

$(document).ready(function(){
    localStorage.clear();
})

$(window).on('unload', function(){
    var files = [];
    if (localStorage.getItem('previous') === null)
    {
        $('#sel1 > option').each(function(){
            files.push(this.value);
        });
        localStorage.setItem('use_files', JSON.stringify(files));
        return;
    }
    else
    {
        previous = localStorage.getItem('previous');
        $.post( "/save_comment", { idprev: previous, comment: $('#comment').val()});
        $('#sel1 > option').each(function(){
            files.push(this.value);
        });
        localStorage.setItem('use_files', JSON.stringify(files));
        return;
    }
})

function resetForm()
{
    $('#fileForm')[0].reset();
}

function sendfileForm()
{
    var formData = new FormData($('#fileForm')[0]);
    $.ajax({
        url: '/addf',
        type: 'POST',
        data: formData,
        contentType: false,
        cache: false,
        processData: false,
        async: false,
        success: function (){
            $('#navTable').load(location.href+" #navTable>*","");
            $.getScript( "/static/highlight.js" );
            resetForm();
            return;
        },
        error: function(error){
            console.log(error);
            return;
        }
    });
}

function delFile()
{
        var found = 0;
        $("tr.item").each(function(){
        var row = $(this);
        if ($(row).hasClass( "highlight" ))
        {
            found = 1;
            var fid = $('td:first', $(row)).attr('id')
            $.post( "/delete", { id: fid, table: "File"},
            function(){
            $('#navTable').load(location.href+" #navTable>*","");
            $.getScript( "/static/highlight.js" );
            $('#sel1 > option').each(function(){
                if (this.value == fid)
                {
                    if (this.previousElementSibling !== null)
                    {
                        var prevID = this.previousElementSibling.value
                        $.post('/show_comment', { idnext: prevID },
                        function(data){
                            $('#comment').val(data)
                        })
                        $(this.previousSibling).prop('selected', 'True');
                        $(this).remove();
                        localStorage.setItem('previous', prevID);
                    }
                    else if (this.nextElementSibling !== null)
                    {
                        var nextID = this.nextElementSibling.value
                        $.post('/show_comment', { idnext: nextID},
                        function(data){
                            $('#comment').val(data)
                        })
                        $(this.nextSibling).prop('selected', 'True');
                        $(this).remove();
                        localStorage.setItem('previous', nextID);
                    }
                    else
                    {
                        $('#comment').val('')
                        $(this).remove();
                        localStorage.clear();
                        $('#finito').prop('disabled', true);
                    }
                }
            })
            })
            return;
        }

        });
        if (found == 0)
        {
            alert('No File Selected')
        }
}