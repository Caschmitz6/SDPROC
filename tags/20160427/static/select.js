$(document).ready( function() {
    populateView()

})

function populateView()
{
    var saved_files = JSON.parse(localStorage.getItem('use_files'));
    $(saved_files).each(function(){
        var temp = this
        $.post("/make_name", {id: this},
        function(data){
        //idval = parseInt(temp);
        $('#sel1')
            .append($('<option></option')
            .text(data)
            .attr('value', temp))
        })
    })
}

function log(){
    previous = localStorage.getItem('previous2');
    $.post('/add_entry', {id : previous},
    function(){
        $('#log_add').text('Added');
        $('#log_add').fadeOut(1000);
    })
}
/*
$(function(){
    $('#againstE').on('change', function(){
        $('#meta-form').trigger('change');
    })
})
*/

function hitAgaE(){
    var temp = $('#againstE').prop('checked');
    if (temp == false)
    {
        $('#againstE').bootstrapToggle('on');
    }
    else
    {
        $('#againstE').bootstrapToggle('off');
    }
    $('#againstE').promise().done(function(){
        $('#meta-form').trigger('change');
    });
}




$(function(){
    $('#meta-form').on('submit', function(event){
        event.preventDefault();
        $.post('/save_graph', $(this).serialize(),
        function(){
            nextID = localStorage.getItem('previous2');
            $.post('/data', { idnext: nextID , plot: 1},
            function(data){
                $.getScript( "https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js" );
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                var hidden = $(data).find('#agaE').val();
                if (hidden === 'true' || hidden === 'True')
                {
                    $('#againstE').prop('checked', true);
                    $('#againstE').bootstrapToggle('on');
                    $('#agaE').val(true);
                }
                else
                {
                    $('#againstE').prop('checked', false);
                    $('#againstE').bootstrapToggle('off');
                    $('#agaE').val(false);
                }
            })
        });
    });
})

//.change(function(event){
//                    event.preventDefault();
//                });
$(function(){
    $('#meta-form').on('change', function(event){
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        var temp = $('#againstE').prop('checked');
        $('#agaE').val(temp);
        $.post('/save_graph', $('#meta-form').serialize(),
        function(){
            $.post('/data', { idnext: previous , plot: 1},
            function(data){
                $.getScript( "https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js" );
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                var hidden = $('#agaE').val();
                if (hidden === 'true' || hidden === 'True')
                {
                    $('#againstE').prop('checked', true);
                }
                else
                {
                    $('#againstE').prop('checked', false);
                }
            })
        })
    })
})

$(function(){
    $('#comment').on('change', function(){
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        $.post('/save_comment', {idprev: previous, comment: $('#comment').val(), format: 1});
    })
})



$(function ()
{
        $('#sel1').on('change', function(event){
        var temp = event.target.value;
        if (localStorage.getItem('previous2') === null)
        {
            localStorage.setItem('previous2', this.value);
            $.post('/data', { idnext: this.value , plot: 1},
            function(data){
                $.getScript( "https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js" );
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                var hidden = $(data).find('#agaE').val();
                if (hidden === 'true' || hidden === 'True')
                {
                    $('#againstE').prop('checked', true);
                    $('#againstE').bootstrapToggle('on');
                    $('#agaE').val(true);
                }
                else
                {
                    $('#againstE').prop('checked', false);
                    $('#againstE').bootstrapToggle('off');
                    $('#agaE').val(false);
                }
            })

            $.post('/show_comment', { idnext: this.value },
            function(data){
            $('#comment').val(data)
            })
        }
        else
        {
            var nextID = this.value
            previous = localStorage.getItem('previous2');
            $('#idnum').val(previous);
            $.post( "/save_comment", { idprev: previous, comment: $('#comment').val()},
            function(){
                $.post('/show_comment', { idnext: nextID },
                function(data){
                    $('#comment').val(data)
                })
            })
            localStorage.setItem('previous2', this.value);
            $('#meta-form').submit();
        }
    });
})
