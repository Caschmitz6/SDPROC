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
    $('#finito').prop('disabled', true);
    localStorage.removeItem('previous');
    var rows = $('tr.item');
    rows.removeClass("highlight");
    rows.removeClass("lightlight");
    sortTable($('#sesPicker'));
    setupClick();

    if(localStorage.getItem("usingDAT") == 1){
        $("#navData").addClass('disabled');
        $('#navProcess').addClass('disabled');
    }
    else{
        $('#navData').removeClass('disabled');
        $('#navProcess').removeClass('disabled');
    }

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
        rows.show();
        filteredRows.hide();
        /* Prepend no-result row if all rows are filtered */
        if (filteredRows.length === rows.length) {
            table.find('tbody').prepend($('<tr class="no-result text-center"><td colspan="'+ ('#ssName').length +'">No result found</td></tr>'));
        }
        if (filteredRows.length === rows.length-1){
            $(table.find('tbody tr:visible').addClass('highlight'))
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
});

$(window).on('unload', function(){
    if (localStorage.getItem('previous') === null)
    {
        return;
    }
    else
    {
        previous = localStorage.getItem('previous');
        type = localStorage.getItem('previousType');
        if (type == 'dat'){
            var format = 1;
        }
        else{
            var format = 2;
        }
        $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: format});
    }
})

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

function newSession()
{
    localStorage.clear();
    $.post('/SDproc/clear_rowa',function(){
        $.post('/SDproc/clear_cmeta', function(){
            window.location.href = ("data");
        })
    });
}


function proceed()
{
    previous = localStorage.getItem('previous');
    type = localStorage.getItem('previousType');
    if (type == 'dat'){
        var format = 1;
    }
    else{
        var format = 2;
    }
    $.post("/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: format}, function(){
        $.post('/SDproc/clear_rowa',function(){
            $.post('/SDproc/clear_cmeta', function(){
                sesID = localStorage.getItem('previous');
                type = localStorage.getItem('previousType');
                localStorage.clear();
                $.post('/SDproc/set_ses', {id: sesID, type: type}, function(data){
                    if (type == 'dat'){
                        localStorage.setItem("usingDAT", 1);
                        window.location.href = ("modifyDAT");
                    }
                    else{
                        localStorage.setItem("usingDAT", 0);
                        var parsed = $.parseJSON(data);
                        var files = [];
                        $(parsed).each(function(){
                            files.push(this);
                        })
                        localStorage.setItem('use_files', JSON.stringify(files));
                        localStorage.setItem('usingSes', 1);
                        window.location.href = ("data");
                    }
                })
            })
        });
    });
}

function delFile()
{
        BootstrapDialog.show({
            title: 'Delete Session?',
            message: 'Are you sure you want to delete this session?',
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
                            var type = $('td:first', $(row)).attr('data-type')
                            if (type == 'dat'){
                                var table = 'File'
                            }
                            else{
                                var table = 'Session'
                            }
                            $.post( "/SDproc/delete", { id: fid, table: table},
                            function(){
                            $('#navTable').load("/SDproc/select #navTable>*",function(){
                                setupClick();
                            });
                            $('#comment').val('')
                            localStorage.removeItem('previous');
                            $('#finito').prop('disabled', true);
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


function setupClick()
{
    var rows = $('tr.item');
    rows.on('click', function(e)
    {
        var row = $(this);
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        row.addClass('highlight');
        comment($('td:first', $(row)).attr('id'), $('td:first', $(row)).attr('data-type'));
        $('#finito').prop('disabled', false);
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

function comment(id, type)
{
        if (localStorage.getItem('previous') === null)
        {
            localStorage.setItem('previous', id)
            localStorage.setItem('previousType', type)
            if (type == 'dat'){
                var format = 1;
            }
            else{
                var format = 2;
            }
            $.post('/SDproc/show_comment', { idnext: id, format: format},
            function(data){
            $('#comment').val(data)
            })
        }
        else
        {
            var nextID = id
            previous = localStorage.getItem('previous');
            var prevType = localStorage.getItem('previousType');
            if (prevType == 'dat'){
                var format = '';
            }
            else{
                var format = 2;
            }
            $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: format},
            function(){
                if (type == 'dat'){
                    var format = 1;
                }
                else{
                    var format = 2;
                }
                $.post('/SDproc/show_comment', { idnext: nextID, format: format},
                function(data){
                    $('#comment').val(data)
                })
            })
            localStorage.setItem('previous', id);
            localStorage.setItem('previousType', type)
        }
}

function shareSes(){
        BootstrapDialog.show({
            title: 'Share Session?',
            message: 'Are you sure you want to share this session?',
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
                            var type = $('td:first', $(row)).attr('data-type');
                            var nameTable = $('#nameTable');
                            var toUser = $.trim($(table.find('tbody tr.highlight')).text())
                            $.post( "/SDproc/shareSes", { id: fid, toUser: toUser, type: type});
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

function logout(){
    if (localStorage.getItem('previous') === null){
        window.location.href = ("logout");
    }
    else{
        previous = localStorage.getItem('previous');
        type = localStorage.getItem('previousType');
        if (type == 'dat'){
            var format = 1;
        }
        else{
            var format = 2;
        }
        $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: format});
    }
}

function sortTable(table){
    tbody = table.find('tbody')
    tbody.find('tr').sort(function(a, b){
        return $('td:first', a).text().localeCompare($('td:first', b).text());
    }).appendTo(tbody);
}
