/*
-    Copyright (c) UChicago Argonne, LLC. All rights reserved.
-
-    Copyright UChicago Argonne, LLC. This software was produced
-    under U.S. Government contract DE-AC02-06CH11357 for Argonne National
-    Laboratory (ANL), which is operated by UChicago Argonne, LLC for the
-    U.S. Department of Energy. The U.S. Government has rights to use,
-    reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR
-    UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR
-    ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is
-    modified to produce derivative works, such modified software should
-    be clearly marked, so as not to confuse it with the version available
-    from ANL.
-
-    Additionally, redistribution and use in source and binary forms, with
-    or without modification, are permitted provided that the following
-    conditions are met:
-
-        * Redistributions of source code must retain the above copyright
-          notice, this list of conditions and the following disclaimer.
-
-        * Redistributions in binary form must reproduce the above copyright
-          notice, this list of conditions and the following disclaimer in
-          the documentation and/or other materials provided with the
-          distribution.
-
-        * Neither the name of UChicago Argonne, LLC, Argonne National
-          Laboratory, ANL, the U.S. Government, nor the names of its
-          contributors may be used to endorse or promote products derived
-          from this software without specific prior written permission.
-
-    THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS
-    AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
-    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
-    FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago
-    Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
-    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
-    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
-    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
-    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
-    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
-    ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
-    POSSIBILITY OF SUCH DAMAGE.
*/
$(document).ready(function(){
    localStorage.removeItem('previous_upload');
    var rows = $('tr.item');
    rows.removeClass("highlight")
    rows.removeClass("lightlight")
    $('#uploadBtn').prop('disabled', true);
    resetForm();
    setupRows();
    setupClick();
    sortTable($('#filePicker'));

    if(localStorage.getItem("usingDAT") == 1){
        $("#navData").addClass('disabled');
        $('#navProcess').addClass('disabled');
    }
    else{
        $('#navData').removeClass('disabled');
        $('#navProcess').removeClass('disabled');
    }
});


function setupRows(){
    $('#ssName').keyup(function(e){

        /* Ignore tab key */
        var code = e.keyCode || e.which;
        if (code == '9') return;
        /* Useful DOM data and selectors */
        var input = $(this);
        inputContent = input.val().toLowerCase();
        model = input.parents();
        table = model.find('#nameTable');
        rows = table.find('tbody tr');
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        var filteredRows = rows.filter(function(){
            var value = $(this).find('td').text().toLowerCase();
            return value.indexOf(inputContent) === -1;
        });
        /* Clean previous no-result if exist */
        table.find('tbody .no-result').remove();
        /* Show all rows, hide filtered ones */
        rows.show();
        filteredRows.hide();
        /* Prepend no-result row if all rows are filtered */
        if (filteredRows.length === rows.length) {
            table.find('tbody').prepend($('<tr class="no-result text-center"><td colspan="'+ ('#ssName').length +'">No result found</td></tr>'));
        }
        if (filteredRows.length === rows.length-1){
            $(table.find('tbody tr:visible').addClass('highlight'));
	    $(table.find('tbody tr:visible').trigger('click'));
        }
    });

    $('#navName').keyup(function(e){

        /* Ignore tab key */
        var code = e.keyCode || e.which;
        if (code == '9') return;
        /* Useful DOM data and selectors */
        var input = $(this);
        inputContent = input.val().toLowerCase();
        model = input.parents();
        table = model.find('#navTable');
        rows = table.find('tbody tr');
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        var filteredRows = rows.filter(function(){
            var value = $(this).find('td').text().toLowerCase();
            return value.indexOf(inputContent) === -1;
        });
        /* Clean previous no-result if exist */
        table.find('tbody .no-result').remove();
        /* Show all rows, hide filtered ones */
        rows.show();
        filteredRows.hide();
        /* Prepend no-result row if all rows are filtered */
        if (filteredRows.length === rows.length) {
            table.find('tbody').prepend($('<tr class="no-result text-center"><td colspan="'+ ('#navName').length +'">No result found</td></tr>'));
        }
        if (filteredRows.length === rows.length-1){
            $(table.find('tbody tr:visible').addClass('highlight'));
            $(table.find('tbody tr:visible').trigger("click"));
        }
    });
}


$( "#fileForm" ).submit(function(event){
    event.preventDefault();
    sendfileForm();
});


$(window).on('unload', function(){
    if (localStorage.getItem('previous_upload') === null)
    {
        return;
    }
    else
    {
        previous = localStorage.getItem('previous_upload');
        $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val()})
    }
})

function resetForm()
{
    $('#fileForm')[0].reset();
    $('#uploadBtn').prop('disabled', true);
}

$(function(){
    $("input:file").change(function(){
        $('#uploadBtn').prop('disabled', false);
    });
})

function sendfileForm()
{
    var fFormData = new FormData();
    var fileData = $('input[type="file"]')[0].files;
    for (var i = 0; i < fileData.length; i++){
        fFormData.append("file_"+i, fileData[i]);
    }
    fFormData.append('formatType', $.trim($('#formatType').text()))
    fFormData.append('formatDelim', $('#formatDelim').val())
    $.ajax({
        url: '/SDproc/addf',
        type: 'POST',
        data: fFormData,
        contentType: false,
        cache: false,
        processData: false,
        async: false,
        success: function (){
            $('#navTable').load("/SDproc/upload #navTable>*", function(){
                setupRows();
                setupClick();
                resetForm();
                sortTable($('#filePicker'));
                return;
            })
        },
        error: function(request){
            console.log(request);
            return;
        }
    });
}

function delFile()
{
        BootstrapDialog.show({
            title: 'Delete File?',
            message: 'Are you sure you want to delete this file?\n\nAfter deletion, sessions that contain this file will likely have problems.',
            buttons: [{
                label: 'Yes',
                action: function(dialogItself){
                        dialogItself.close();
                        var found = 0;
                        $("tr.item").each(function(){
                        var row = $(this);
                        if ($(row).hasClass( "highlight" ))
                        {
                            found = 1;
                            var fid = $('td:first', $(row)).attr('id')
                            $.post( "/SDproc/delete", { id: fid, table: "File"},
                            function(){
                            $('#navTable').load("/SDproc/upload #navTable>*", function(){
                                setupRows();
                                setupClick();
                                $('#comment').val('')
                                localStorage.removeItem('previous_upload');
                            })
                            })
                        }
                        });
                        if (found == 0)
                        {
                            alert('No File Selected')
                        }
                    }
                }, {
                label: 'No',
                action: function(dialogItself){
                    dialogItself.close();
                }
            }]
        });
}

function shareFile(){
        BootstrapDialog.show({
            title: 'Share File?',
            message: 'Are you sure you want to share this file?',
            buttons: [{
                label: 'Yes',
                action: function(dialogItself){
                        dialogItself.close();
                        var found = 0;
                        $("#navTable tr.item").each(function(){
                        var row = $(this);
                        if ($(row).hasClass( "highlight" ))
                        {
                            found = 1;
                            var fid = $('td:first', $(row)).attr('id');
			    $.post( "/SDproc/save_comment", { idprev: fid, comment: $('#comment').val()}, function(){
			    	var nameTable = $('#nameTable');
                            	var toUser = $.trim($(table.find('tbody tr.highlight')).text())
                            	$.post( "/SDproc/shareFile", { id: fid, toUser: toUser})
			    });
                        }
                        });
                        if (found == 0)
                        {
                            alert('No File Selected')
                        }
                    }
                }, {
                label: 'No',
                action: function(dialogItself){
                    dialogItself.close();
                }
            }]
        });
}

$(function()
{
    table = $('#nameTable');
    rows = table.find('tbody tr');
    rows.on('click', function(e)
    {
        var row = $(this);
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        row.addClass('highlight');
    })

    rows.on('mouseenter', function(e)
    {
        var row = $(this);
        if ($(row).hasClass( "highlight" ))
        {
            rows.removeClass('lightlight');
        }
        else
        {
            rows.removeClass('lightlight');
            row.addClass('lightlight');
        }
    })

    $(document).on('selectstart dragstart', function(e)
    {
        e.preventDefault();
        return false;
    })
})

function txtFile()
{
    $('#formatDelim').prop('disabled', false);
    $('#formatDelim').attr('placeholder', 'Comment character');
    $('#formatType').text('txt')
    $('#formatType').append("<span class='caret'></span>");
}

function mdaFile()
{
    $('#formatDelim').prop('disabled', true);
    $('#formatDelim').attr('placeholder', 'Nothing needed for MDA');
    $('#formatType').text('mda')
    $('#formatType').append("<span class='caret'></span>");
}

function datFile(){
    $('#formatDelim').prop('disabled', false);
    $('#formatDelim').attr('placeholder', 'Comment character');
    $('#formatType').text('dat');
    $('#formatType').append("<span class='caret'></span>");
}

function proceed()
{
    window.location.href = ("select");
}

function setupClick()
{
    var rows = $('tr.item');
    rows.on('click', function(e)
    {
        var row = $(this);
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        row.addClass('highlight');
        comment($('td:first', $(row)).attr('id'));
    })

    rows.on('mouseenter', function(e)
    {
        var row = $(this);
        if ($(row).hasClass( "highlight" ))
        {
            rows.removeClass('lightlight');
        }
        else
        {
            rows.removeClass('lightlight');
            row.addClass('lightlight');
        }
    })

    $(document).on('selectstart dragstart', function(e)
    {
        e.preventDefault();
        return false;
    })
}

function comment(id)
{
        if (localStorage.getItem('previous_upload') === null)
        {
            localStorage.setItem('previous_upload', id)
            $.post('/SDproc/show_comment', { idnext: id },
            function(data){
            $('#comment').val(data);
            return redirect(url_for('modifyDAT'));
            })
        }
        else
        {
            var nextID = id
            previous = localStorage.getItem('previous_upload');
            $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val()},
            function(){
                $.post('/SDproc/show_comment', { idnext: nextID },
                function(data){
                    $('#comment').val(data)
                })
            })
            localStorage.setItem('previous_upload', id);
        }
}

function logout(){
    if (localStorage.getItem('previous_upload') === null){
        window.location.href = ("logout");
    }
    else{
        previous = localStorage.getItem('previous_upload');
        $.post("/SDproc/save_comment", { idprev: previous, comment: $('#comment').val()}, function(){
            window.location.href = ("logout")
        });
    }
}

function sortTable(table){
    tbody = table.find('tbody')
    tbody.find('tr').sort(function(a, b){
        return $('td:first', a).text().localeCompare($('td:first', b).text());
    }).appendTo(tbody);
}

function linkGlobus(){
    $('#globusModal').modal('show');
    $.post("/SDproc/linkGlobus", function(data){
        window.open(data);
    });
}

function connectGlobus(){
    $.post("/SDproc/connectGlobus", {authURL: $('#globusAuth').val()}, function(data){
        $('#navTable').load("/SDproc/upload #navTable>*", function(){
            setupRows();
            setupClick();
            $('#comment').val('')
        })
    });
}