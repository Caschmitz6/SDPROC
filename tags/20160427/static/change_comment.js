$(function ()
{
        $('#sel1').on('change', function(){
        if (localStorage.getItem('previous') === null)
        {
            localStorage.setItem('previous', this.value)
            $.post('/show_comment', { idnext: this.value },
            function(data){
            $('#comment').val(data)
            })
        }
        else
        {
            var nextID = this.value
            previous = localStorage.getItem('previous');
            $.post( "/save_comment", { idprev: previous, comment: $('#comment').val()},
            function(){
                $.post('/show_comment', { idnext: nextID },
                function(data){
                    $('#comment').val(data)
                })
            $.getScript( "/static/add_file.js" );
            })
            localStorage.setItem('previous', this.value);
        }
    });

    $('#sel1').on('dblclick', 'option', function(){
        if (this.previousElementSibling !== null)
        {
            var prevID = this.previousSibling.value
            $.post( "/save_comment", { idprev: this.value, comment: $('#comment').val()},
            function(){
                $.post('/show_comment', { idnext: prevID },
                function(data){
                    $('#comment').val(data)
                })
            })
            $(this.previousSibling).prop('selected', 'True');
            $(this).remove();
            localStorage.setItem('previous', prevID);
            $.getScript( "/static/add_file.js" );
        }
        else if (this.nextElementSibling !== null)
        {
            var nextID = this.nextElementSibling.value
            $.post( "/save_comment", { idprev: this.value, comment: $('#comment').val()},
            function(){
                $.post('/show_comment', { idnext: nextID },
                function(data){
                    $('#comment').val(data)
                })
            })
            $(this.nextSibling).prop('selected', 'True');
            $(this).remove();
            localStorage.setItem('previous', nextID);
            $.getScript( "/static/add_file.js" );
        }
        else
        {
            $.post( "/save_comment", { idprev: this.value, comment: $('#comment').val()})
            $('#comment').val('')
            $(this).remove();
            localStorage.clear();
            $('#finito').prop('disabled', true);
        }
    })
})
