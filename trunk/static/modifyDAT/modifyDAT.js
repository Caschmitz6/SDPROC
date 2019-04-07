$(document).ready( function() {
    if (jQuery.trim($('#process_plot').text()) == "No DAT selected"){
        alert('Please select or generate a DAT file');
    }
    else{
        $.post('/SDproc/show_comment', {format: 3}, function(data){
            $('#comment').val(data)
        })
    }
    if ($('#flatRad').is(':checked')){
        $('#flatVal').prop('disabled', false);
        $('#leftX').prop('disabled', true);
        $('#leftY').prop('disabled', true);
        $('#rightX').prop('disabled', true);
        $('#rightY').prop('disabled', true);
    }
    if ($('#linearRad').is(':checked')){
        $('#flatVal').prop('disabled', true);
        $('#leftX').prop('disabled', false);
        $('#leftY').prop('disabled', false);
        $('#rightX').prop('disabled', false);
        $('#rightY').prop('disabled', false);
    }
    if ($('#avRad').is(':checked')){
        $('#leftX').prop('disabled', true);
        $('#leftY').prop('disabled', true);
        $('#rightX').prop('disabled', true);
        $('#rightY').prop('disabled', true);
        $('#flatVal').prop('disabled', true);
    }
    $('#calcLeftYLabel').hide()
    $('#calcRightYLabel').hide()

    if(localStorage.getItem("usingDAT") == 1){
        $("#navData").addClass('disabled');
        $('#navProcess').addClass('disabled');
    }
    else{
        $('#navData').removeClass('disabled');
        $('#navProcess').removeClass('disabled');
    }
})

function showLine(){
    if ($('#flatRad').is(':checked')){
        var flatVal = $('#flatVal').val()
        $.post('/SDproc/showLineDAT', {flatVal: flatVal}, function(data){
            $('#process_plot').html($(data).find('#process_plot').html())
        })
    }
    else if ($('#calcRad').is(':checked')){
        var leftIn = $('#leftIn').val()
        var rightIn = $('#rightIn').val()
        $.post('/SDproc/showLineDAT', {right: rightIn, left: leftIn}, function(data){
            var data = JSON.parse(data)
            $('#process_plot').html(data[0])
            localStorage.setItem('averageLin', data[1])
            $('#calcLeftY').text('Left Y: ');
            $('#calcRightY').text('Right Y: ');
        })
    }
    else if ($('givRad').is(':checked')){
        var lX = $('#leftX').val()
        var lY = $('#leftY').val()
        var rX = $('#rightX').val()
        var rY = $('#rightY').val()
    }
    else{
        alert('Please select an option to show.');
    }
}

function remBackground(show){
    if ($('#flatRad').is(':checked')){
        var flatVal = $('#flatVal').val()
        $.post('/SDproc/remBackDAT', {show: show, flatVal: flatVal}, function(data){
            if (show == 0){
                $('#process_plot').html($(data).find('#process_plot').html())
            }
            else{
                $('#process_plot').html($(data))
            }
        })
    }
    else if ($('#givRad').is(':checked')){
        var lX = $('#leftX').val()
        var lY = $('#leftY').val()
        var rX = $('#rightX').val()
        var rY = $('#rightY').val()
        $.post('/SDproc/remBackDAT', {show: show, leftX : lX, leftY : lY, rightX: rX, rightY: rY}, function(data){
            if (show == 0){
                $('#process_plot').html($(data).find('#process_plot').html())
            }
            else{
                $('#process_plot').html($(data))
            }
        })
    }
    else if ($('#calcRad').is(':checked')){
        var leftIn = $('#calcLeftX').val()
        var rightIn = $('#calcRightX').val()
        $.post('/SDproc/remBackDAT', {show: show, leftIn: leftIn, rightIn: rightIn}, function(data){
        if (show == 0){
            $('#process_plot').html($(data).find('#process_plot').html())
        }
        else{
            var data = JSON.parse(data)
            $('#process_plot').html($(data[0]))
            $('#calcLeftY').text(data[1])
            $('#calcRightY').text(data[2])
            $('#calcLeftYLabel').show()
            $('#calcRightYLabel').show()
        }
        })
    }
}

function resetPlot(){
    $.post('/SDproc/resetDAT', function(data){
        $('#process_plot').html($(data).find('#process_plot').html())
    })
}

$(function (){
    $('input[type=radio][name=methodRad]').on('change', function(event){
        if ($('#flatRad').is(':checked')){
            $('#flatVal').prop('disabled', false);
            $('#leftX').prop('disabled', true);
            $('#leftY').prop('disabled', true);
            $('#rightX').prop('disabled', true);
            $('#rightY').prop('disabled', true);
            $('#calcLeftX').prop('disabled', true);
            $('#calcRightX').prop('disabled', true);
        }
        if ($('#calcRad').is(':checked')){
            $('#flatVal').prop('disabled', true);
            $('#calcLeftX').prop('disabled', false);
            $('#calcRightX').prop('disabled', false);
            $('#leftX').prop('disabled', true);
            $('#leftY').prop('disabled', true);
            $('#rightX').prop('disabled', true);
            $('#rightY').prop('disabled', true);
        }
        if ($('#givRad').is(':checked')){
            $('#leftX').prop('disabled', false);
            $('#leftY').prop('disabled', false);
            $('#rightX').prop('disabled', false);
            $('#rightY').prop('disabled', false);
            $('#flatVal').prop('disabled', true);
            $('#calcLeftX').prop('disabled', true);
            $('#calcRightX').prop('disabled', true);
        }
    })
})

function outputFile(){
    BootstrapDialog.show({
        title: 'Save Options',
        message: function(dialog){
            if (jQuery.trim($('#sesName').text()) == 'None'){
                var $content = $('<input type="text" id="DATname" placeholder="Name of DAT file">')
            }
            else{
                var temp = jQuery.trim($('#sesName').text())
                var $content = $('<input type="text" id="DATname">')
                $content[0].value = temp
            }
            return $content
        },
        buttons: [{
            label: 'Save to Server',
            action: function(dialogItself){
                $.post('/SDproc/generateOutput', {outType: 7, datFName: $('#DATname').val()}, function(data){
                    alert('Saved');
                    $('#sesName').html(data);
                    dialogItself.close();
                })
            }
        }, {
            label: 'Save Locally',
            action: function(dialogItself){
                $('#output-form').attr('action', '/SDproc/generateOutput')
                $('#outType').val(6);
                $('#datFName').val($('#DATname').val())
                $('#output-form')[0].submit();
                dialogItself.close();
            }
        }]
    })
}

$(window).on('unload', function(){
    if (jQuery.trim($('#process_plot').text()) == "No DAT selected"){
        return;
    }
    else{
        $.post( "/SDproc/save_comment", {comment: $('#comment').val(), format: 3})
    }
})