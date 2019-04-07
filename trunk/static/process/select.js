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
function processor(){
    temp1 = $('#cordData').val()
    var binWidth = $('#binWidth').val();
    if ($('#sel1 > tbody > tr').length == 1){
        var ses = localStorage.getItem('usingSes');
        localStorage.setItem('previous3', this.value);
        $.post('/SDproc/process', { idnext: this.value, output: 1, binWidth: binWidth},
        function(data){
            $('#process_plot').html( $(data).find('#process_plot').html());
            $('#cordData').val( $(data).find('#cordHolder').html());
            $('#idnum').val(localStorage.getItem('previous3'));
            $('#outType').val(4);
            $('#DBSave').val(0);
            $('#output-form').attr('action', '/SDproc/generateOutput')
            $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                $.post('/SDproc/setDAT', {DAT: data})
            })
        })

        $.post('/SDproc/show_comment', { idnext: this.value, format: 1, ses: ses},
        function(data){
            $('#comment').text(data);
        })
    }
    else{
        var ses = localStorage.getItem('usingSes');
        var ids = []
        $('#sel1 > tbody > tr.highlight').each(function(){
            ids.push($(this).data('value'));
        })
        var jIds = JSON.stringify(ids);
        localStorage.setItem('previous3', jIds);

        $.post('/SDproc/process', {idList: jIds, output: 1, binWidth: binWidth},
        function(data){
            $('#process_plot').html( $(data).find('#process_plot').html());
            $('#cordData').val( $(data).find('#cordHolder').html());
            $('#idnum').val(localStorage.getItem('previous3'));
            $('#outType').val(5);
            $('#DBSave').val(0);
            $('#output-form').attr('action', '/SDproc/generateOutput')
            $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                $.post('/SDproc/setDAT', {DAT: data})
            })
        });
    }
}

function startProc(){
    processor();
    $('#settingsBtn').show();
    $('#outputBtn').prop('disabled', false);
    $('#continue').prop('disabled', false);
    $('#logbook').prop('disabled', false);
    //setcDAT();
}


$(document).ready( function() {
    asynchOnLoad()
    $('#settingsBtn').hide();
    $('#outputBtn').prop('disabled', true);
    $('#continue').prop('disabled', true);
    $('#logbook').prop('disabled', true);
    $('#linearRad').prop("checked", true)
    $('#binWidth').attr('placeholder', 'Input width of bins');
    $('#binWidth').prop('disabled', true);
    $('#logbtn').prop('disabled', false);
    if (!localStorage.getItem('previous3') === null)
        localStorage.removeItem("previous3");
    if (localStorage.getItem('pltStat') === null)
        localStorage.setItem('pltStat', 1);
})

function asynchOnLoad(){
    var deferred = new $.Deferred(), completed = deferred.then(function(){
        $('#sel1 > tbody > tr > td > input').each(function(){
            if ($(this).is(':checked')){
                $(this).parent().parent().addClass('highlight');
            }
        });
        sortTable($('#sel1'));
        return 1;
    });
    if (localStorage.getItem('use_files')){
        $.post("/SDproc/make_name", {ids: localStorage.getItem('use_files')},
        function(data){
            data = JSON.parse(data)
            for(i = 0; i < data.length; i++){
                if (data[i][1] == true){
                    $('#sel1 > tbody:last-child')
                    .append('<tr style="cursor: pointer;" data-value="'+data[i][2]+'" class="file"><td class="fileNameCell">' + data[i][0] + '<td><input onclick="updateSumCheck(this)" checked type="checkbox"></td></tr>')
                }
                else{
                    $('#sel1 > tbody:last-child')
                    .append('<tr style="cursor: pointer;" data-value="'+data[i][2]+'" class="file"><td class="fileNameCell">' + data[i][0] + '<td><input onclick="updateSumCheck(this)" type="checkbox"></td></tr>')
                }
            }
            $('#pane').show();
            deferred.resolve();
        })
    }
    return deferred.promise()
}

function updateSumCheck(checkbox){
    if ($(checkbox).is(':checked')){
        idnum = $(checkbox).parent().parent().data('value');
        $(checkbox).parent().parent().addClass('highlight');
        $.post('/SDproc/updateSumCheck', {id: idnum, check: "True"});
    }
    else{
        idnum = $(checkbox).parent().parent().data('value');
        $(checkbox).parent().parent().removeClass('highlight');
        $.post('/SDproc/updateSumCheck', {id: idnum, check: "False"});
    }
}

function removeID(id, idArray){
    var result = $.grep(idArray, function(n, i){
        return (n !== id);
    })
    return result;
}


$(window).on('unload', function(){
    $.post('/SDproc/close_plots');
    if (localStorage.getItem('previous3') === null)
    {
        return;
    }
    else
    {
        localStorage.removeItem('previous3');
    }
})

function log(){
    $.post('/SDproc/add_entry', {process: 1},
    function(){
        $('#log_add').text('Added');
        $('#log_add').fadeOut(1000);
        $('#logbtn').prop('disabled', true);
    })
}

function saveSettings(){
    if ($('#binRad').is(':checked')){
        var id = JSON.parse(localStorage.getItem('previous3'));
        var binWidth = $('#binWidth').val();
        if ($.isNumeric(binWidth)){
            if (id.length > 1){
                var id = JSON.stringify(id);
                $.post('/SDproc/process', { idList: id , binWidth: binWidth},
                    function(data){
                        $('#process_plot').html( $(data).find('#process_plot').html());
                        $('#maxes').html( $(data).find('#maxes').html());
                        $('#maxVal').html( $(data).find('#maxVal').html());
                    })
                $('#ssModal').modal('hide');
            }
            else{
                $.post('/SDproc/process', { idnext: id , binWidth: binWidth},
                    function(data){
                        $('#process_plot').html( $(data).find('#process_plot').html());
                        $('#maxes').html( $(data).find('#maxes').html());
                        $('#maxVal').html( $(data).find('#maxVal').html());
                    })
                $('#ssModal').modal('hide');
            }
            $('#logbtn').prop('disabled', false);
        }
        else
        {
            alert('Please enter a bin width')
        }
    }
    else
    {
        processor();
    }
}


$(function (){
    $('input[type=radio][name=methodRad]').on('change', function(event){
        if ($('#binRad').is(':checked')){
            $('#binWidth').prop('disabled', false);
        }
        if ($('#linearRad').is(':checked')){
            $('#binWidth').prop('disabled', true);
        }
    })
})

function setcDAT(){
    id = localStorage.getItem('previous3');
    var binWidth = $('#binWidth').val();
    temp1 = $('#cordData').val()
    if ($('#sel1').val().length == 1){
        $.post('/SDproc/process', {idnext: id , output: 1, binWidth: binWidth}, function(data){
            $('#idnum').val(id);
            temp = $('#cordData').val()
            $('#cordData').val(data);
            $('#outType').val(4);
            $('#DBSave').val(0);
            $('#output-form').attr('action', '/SDproc/generateOutput')
            $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                $.post('/SDproc/setDAT', {DAT: data})
            })
        })
    }
    else{
        $.post('/SDproc/process', {idList: id , output: 1, binWidth: binWidth}, function(data){
            $('#idnum').val(id);
            $('#cordData').val(data);
            $('#outType').val(5);
            $('#DBSave').val(0);
            $('#output-form').attr('action', '/SDproc/generateOutput')
            $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                $.post('/SDproc/setDAT', {DAT: data})
            })
        })
    }
}

function sortTable(table){
    tbody = table.find('tbody')
    tbody.find('tr').sort(function(a, b){
        return $('td:first', a).text().localeCompare($('td:first', b).text());
    }).appendTo(tbody);
}


function advance(){
    window.location.href = ("modifyDAT");
}

function outputFile(){
    if (localStorage.getItem('previous3') === null){
        alert('No file loaded');
    }
    else{
        BootstrapDialog.show({
            title: 'Save Options',
            message: function(dialog){
                var $content = $('<input type="text" id="DATname" placeholder="Name of DAT file">')
                return $content
            },
            buttons: [{
                label: 'Save to Server',
                action: function(dialogItself){
                    if ($('#binRad').is(':checked')){
                        var binWidth = $('#binWidth').val();
                        if ($('#sel1').val().length == 1){
                            id = localStorage.getItem('previous3');
                            $.post('/SDproc/process', {idnext: id , output: 1, binWidth: binWidth}, function(data){
                                $('#idnum').val(id);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(4);
                                $('#DBSave').val(1);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                                        $.post('/SDproc/setDAT', {DAT: data, DName: $('#DATname').val()}, function(){
                                            dialogItself.close();
                                            alert('Saved');
                                        });
                                    });
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                        else{
                            var ids = []
                            $('#sel1 > tbody > tr.highlight').each(function(){
                                ids.push($(this).data('value'));
                            })
                            var jIds = JSON.stringify(ids);
                            $.post('/SDproc/process', {idList: jIds, output: 1, binWidth: binWidth}, function(data){
                                $('#idnum').val(jIds);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(5);
                                $('#DBSave').val(1);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                                        $.post('/SDproc/setDAT', {DAT: data, DName: $('#DATname').val()}, function(){
                                            dialogItself.close();
                                            alert('Saved');
                                        });
                                    });
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                    }
                    else{
                        if ($('#sel1').val().length == 1){
                            id = localStorage.getItem('previous3');
                            $.post('/SDproc/process', {idnext: id , output: 1}, function(data){
                                $('#idnum').val(id);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(4);
                                $('#DBSave').val(1);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                                        $.post('/SDproc/setDAT', {DAT: data, DName: $('#DATname').val()}, function(){
                                            dialogItself.close();
                                            alert('Saved');
                                        });
                                    });
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                        else{
                            var ids = []
                            $('#sel1 > tbody > tr.highlight').each(function(){
                                ids.push($(this).data('value'));
                            })
                            var jIds = JSON.stringify(ids);
                            $.post('/SDproc/process', {idList: jIds, output: 1}, function(data){
                                $('#idnum').val(jIds);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(5);
                                $('#DBSave').val(1);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $.post('/SDproc/generateOutput', $('#output-form').serialize(), function(data){
                                        $.post('/SDproc/setDAT', {DAT: data, DName: $('#DATname').val()}, function(){
                                            dialogItself.close();
                                            alert('Saved');
                                        });
                                    });
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                    }
                }
            }, {
                label: 'Save Locally',
                action: function(dialogItself){
                    if ($('#binRad').is(':checked')){
                        var binWidth = $('#binWidth').val();
                        if ($('#sel1').val().length == 1){
                            id = localStorage.getItem('previous3');
                            $.post('/SDproc/process', {idnext: id , output: 1, binWidth: binWidth}, function(data){
                                $('#idnum').val(id);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(2);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $('#output-form')[0].submit();
                                    dialogItself.close();
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                        else{
                            var ids = []
                            $('#sel1 > tbody > tr.highlight').each(function(){
                                ids.push($(this).data('value'));
                            })
                            var jIds = JSON.stringify(ids);
                            $.post('/SDproc/process', {idList: jIds, output: 1, binWidth: binWidth}, function(data){
                                $('#idnum').val(jIds);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(3);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $('#output-form')[0].submit();
                                    dialogItself.close();
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                    }
                    else{
                        if ($('#sel1').val().length == 1){
                            id = localStorage.getItem('previous3');
                            $.post('/SDproc/process', {idnext: id , output: 1}, function(data){
                                $('#idnum').val(id);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(2);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $('#output-form')[0].submit();
                                    dialogItself.close();
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            });
                        }
                        else{
                            var ids = []
                            $('#sel1 > tbody > tr.highlight').each(function(){
                                ids.push($(this).data('value'));
                            })
                            var jIds = JSON.stringify(ids);
                            $.post('/SDproc/process', {idList: jIds, output: 1}, function(data){
                                $('#idnum').val(jIds);
                                $('#cordData').val($(data).find('#cordHolder').html());
                                $('#outType').val(3);
                                $('#output-form').attr('action', '/SDproc/generateOutput')
                                $('#datFName').val($('#DATname').val())
                                if (jQuery.type($('#DATname').val()) === "string" && $('#DATname').val().length > 0){
                                    $('#output-form')[0].submit();
                                    dialogItself.close();
                                }
                                else{
                                    alert('Enter a name for the DAT file')
                                }
                            })
                        }
                    }
                }
            }]
        })
    }
}