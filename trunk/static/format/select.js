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
$(function (){
    $('#sel1').on('click', 'tr.file', function(e){
        var rows = $('tr.file');
        rows.removeClass('highlight');
        $(this).addClass('highlight');
        var ses = localStorage.getItem('usingSes');
        $('#fileName').text($('td:first', $(this)).text());
        if (localStorage.getItem('previous2') === null)
        {
            localStorage.setItem('previous2', $(this).data('value'));
            $.post('/SDproc/data', { idnext: $(this).data('value') , plot: 1},
            function(data){
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                $('#currentAE').html( $(data).find('#currentAE').html());
                $.post('/SDproc/show_comment', { idnext: localStorage.getItem('previous2'), format: 1, ses: ses},
                function(data){
                    $('#comment').val(data)
                    setPlotAgainst();
                })
            })
        }
        else
        {
            var nextID = $(this).data('value')
            previous = localStorage.getItem('previous2');
            $('#idnum').val(previous);
            localStorage.setItem('previous2', $(this).data('value'));
            $('#meta-form').submit();
            $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: 1},
            function(){
                $.post('/SDproc/show_comment', { idnext: nextID, format: 1, ses: ses},
                function(data){
                    $('#comment').val(data)
                    setPlotAgainst();
                })
            })
        }
    })
})


/*
$(function (){
        var rows = $('tr.file').not(':first');
        rows.on('click', function(event){
        var ses = localStorage.getItem('usingSes');
        $('#fileName').text($('td:first', $(this)).text());
        if (localStorage.getItem('previous2') === null)
        {
            localStorage.setItem('previous2', this.value);
            $.post('/SDproc/data', { idnext: this.value , plot: 1},
            function(data){
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                $('#currentAE').html( $(data).find('#currentAE').html());
                $.post('/SDproc/show_comment', { idnext: localStorage.getItem('previous2'), format: 1, ses: ses},
                function(data){
                    $('#comment').val(data)
                    setPlotAgainst();
                })
            })
        }
        else
        {
            var nextID = this.value
            previous = localStorage.getItem('previous2');
            $('#idnum').val(previous);
            localStorage.setItem('previous2', this.value);
            $('#meta-form').submit();
            $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: 1},
            function(){
                $.post('/SDproc/show_comment', { idnext: nextID, format: 1, ses: ses},
                function(data){
                    $('#comment').val(data)
                    setPlotAgainst();
                })
            })
        }
    });

    $('#sel1').on('dblclick', function(){
        if (this.previousElementSibling !== null)
        {
            var prevID = this.previousSibling.value
            $.post
        }
    })

})
*/


$(document).ready( function() {
    $('#unit').val('meV');
    setPlotAgainst();
    asynchOnLoad()
    $('#pane').hide();
    if (!localStorage.getItem('previous2') === null)
        localStorage.removeItem("previous2");
    $('#fitType').text('Fit around max');
    $('#fitType').append("<span class='caret'></span>");
    $('#peakLocation').attr('placeholder', 'Peak found automatically');
    $('#peakLocation').prop('disabled', true);
    $('#pWInput').prop('disabled', false);
    $('#logbtn').text('Add to Logbook');
    $('#logbtn').prop('disabled', false);
    $('#commentGroup').removeClass('logCommentGroup');
    $('#commentGroup').addClass('commentGroup');
    $('#fitBtn').removeClass('fitBtnShifted');
    $('#fitBtn').addClass('fitBtn');
    sortTable($('#filePicker'));
    localStorage.setItem('justPeakFit', 0);
});

$(document).keypress( function(event) {
     if (event.which == '13') {
        event.preventDefault();
        if ("activeElement" in document) {
            document.activeElement.blur();
        }
      }
});

function asynchOnLoad(){
    var deferred = new $.Deferred(), completed = deferred.then(function(){
        sortTable($('#sel1'));
        $('#sel1 tr.file:first').trigger('click');
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

function removeID(id, idArray){
    var result = $.grep(idArray, function(n, i){
        return (n !== id);
    })
    return result;
}


$(window).on('unload', function(){
    $.post('/SDproc/close_plots');
    if (localStorage.getItem('previous2') === null)
    {
        return;
    }
    else
    {
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: 1})
        $.post('/SDproc/save_graph', $('#meta-form').serialize())
        localStorage.removeItem('previous2');
    }
})

$(function()
{
    var rows = $('tr.item');
    rows.on('click', function(e)
    {
        var row = $(this);
        rows.removeClass('highlight');
        rows.removeClass('lightlight');
        row.addClass('highlight');
        $('#sel1 > tbody:last-child')
            .append('<tr style="cursor: pointer;" data-value="'+$('td:first', $(row)).attr('id')+'" class="file"><td class="fileNameCell">' + $('td:first', $(row)).text() + '</td><td><input checked onclick="updateSumCheck(this)" type="checkbox"></td></tr>')
        $('#pane').show()
        row.removeClass('highlight');
        if (localStorage.getItem('use_files') === null)
        {
            var files = [];
            files.push($('td:first', $(row)).attr('id'));
            localStorage.setItem('use_files', JSON.stringify(files));
        }
        else
        {
            var files = JSON.parse(localStorage.getItem('use_files'));
            files.push($('td:first', $(row)).attr('id'));
            localStorage.setItem('use_files', JSON.stringify(files));
        }
        $('#fileModal').modal('toggle');
        $('#sel1 tr:last').addClass('highlight');
        $('#sel1 tr:last').trigger('click');
        sortTable($('#sel1'));
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

function populateName(){
    if ($('#sesName').text() != 'None'){
        $('#ssName').val($('#sesName').text());
    }
}

function saveSes(){
    if (localStorage.getItem('previous2') === null)
    {
        return;
    }
    else
    {
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        $.post( "/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: 1});
        $.post('/SDproc/save_graph', $('#meta-form').serialize());
    }
    $.post('/SDproc/save_ses',{name: $('#ssName').val(), comment: $('#ssComment').val(), checked: 0}, function(data){
        var data = JSON.parse(data)
        if (data.status == null){
            BootstrapDialog.show({
                title: 'Overwrite Session?',
                message: 'A session with this name already exists, would you like to overwrite it?',
                buttons: [{
                    label: 'Yes',
                    action: function(dialogItself){
                        $.post('/SDproc/delete',{ id: data, table: "Session"});
                        $.post('/SDproc/save_ses',{name: $('#ssName').val(), comment: $('#ssComment').val(), checked: 1}, function(data){
                            $('#sesName').html(data);
                            dialogItself.close();
                        });
                        }
                    }, {
                    label: 'No',
                    action: function(dialogItself){
                        dialogItself.close();
                        $('#ssModal').modal('show');
                    }
                }]
            });
        }
        $('#sesName').html(data.name);
    });
}

function log(){
    previous = localStorage.getItem('previous2');
    $.post('/SDproc/add_entry', {id : previous},
    function(){
        $('#logbtn').text('Added');
        $('#logbtn').prop('disabled', true);
        $('#commentGroup').removeClass('commentGroup');
        $('#commentGroup').addClass('logCommentGroup');
    })
}

function updateSumCheck(checkbox){
    if ($(checkbox).is(':checked')){
        idnum = $(checkbox).parent().parent().data('value')
        $.post('/SDproc/updateSumCheck', {id: idnum, check: "True"})
    }
    else{
        idnum = $(checkbox).parent().parent().data('value')
        $.post('/SDproc/updateSumCheck', {id: idnum, check: "False"})
    }
}

function deleteCmeta(){
    if (localStorage.getItem('previous2') === null){
        alert("No file selected")
    }
    else{
        selected = localStorage.getItem('previous2')
        $.post('/SDproc/clearPart_cmeta', {id: selected}, function(){
            $('#sel1 > tbody > tr').each(function(){
                if (!$(this).hasClass('highlight')){
                    return true;
                }
                localStorage.removeItem('previous2');
                var sel = parseInt(selected);
                if (this.previousElementSibling !== null){
                    var newSelected = this.previousSibling;
                    $(newSelected).addClass('highlight');
                    $(this).remove();
                    var saved_files = JSON.parse(localStorage.getItem('use_files'));
                    var result = $.grep(saved_files, function(n,i){
                        return (n !== String(sel));
                    })
                    localStorage.setItem('use_files', JSON.stringify(result));
                    $(newSelected).trigger('click');
                }
                else if (this.nextElementSibling !== null){
                    var newSelected = this.nextSibling;
                    $(newSelected).addClass('highlight');
                    $(this).remove();
                    var saved_files = JSON.parse(localStorage.getItem('use_files'));
                    var result = $.grep(saved_files, function(n,i){
                        return (n !== String(sel));
                    })
                    localStorage.setItem('use_files', JSON.stringify(result));
                    $(newSelected).trigger("click");
                }
                else{
                    $('#comment').val('');
                    $(this).remove();
                    var saved_files = JSON.parse(localStorage.getItem('use_files'));
                    var result = $.grep(saved_files, function(n,i){
                        return (n !== String(sel));
                    })
                    localStorage.setItem('use_files', JSON.stringify(result));
                }
            })
        })
    }
}


$(function(){
    $('#meta-form').on('submit', function(event){
        event.preventDefault();
        $.post('/SDproc/save_graph', $(this).serialize(),
        function(){
            nextID = localStorage.getItem('previous2');
            $.post('/SDproc/data', { idnext: nextID , plot: 1},
            function(data){
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                $('#currentAE').html( $(data).find('#currentAE').html());
                setPlotAgainst();
                localStorage.setItem('justPeakFit', 0);
            })
        });
        $('#logbtn').text('Add to Logbook');
        $('#logbtn').prop('disabled', false);
        $('#commentGroup').removeClass('logCommentGroup');
        $('#commentGroup').addClass('commentGroup');
    });
})

$(function(){
    $('#meta-form').on('change', function(event){
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        $.post('/SDproc/save_graph', $('#meta-form').serialize(),
        function(){
            var unit = $('#unit').val();
            $.post('/SDproc/data', { idnext: previous , plot: 1, unit: unit},
            function(data){
                $('#metaForm_id').html( $(data).find('#metaForm_id').html());
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                localStorage.setItem('justPeakFit', 0);
            })
        })
        $('#logbtn').text('Add to Logbook');
        $('#logbtn').prop('disabled', false);
        $('#commentGroup').removeClass('logCommentGroup');
        $('#commentGroup').addClass('commentGroup');
    })
})

$(function(){
    $('#comment').on('change', function(){
        previous = localStorage.getItem('previous2');
        $('#idnum').val(previous);
        $.post('/SDproc/save_comment', {idprev: previous, comment: $('#comment').val(), format: 1});
    })
})

function aroundMax(){
    $('#fitType').text('Fit around max');
    $('#fitType').append("<span class='caret'></span>");
    $('#peakLocation').val('');
    $('#peakLocation').attr('placeholder', 'Peak found automatically');
    $('#peakLocation').prop('disabled', true);
    $('#peakGroup').removeClass('splitInput');
    $('#localRange').hide();
}

function atPoint(){
    $('#fitType').text('Peak at Point');
    $('#fitType').append("<span class='caret'></span>");
    $('#peakLocation').attr('placeholder', 'Energy Value (meV)');
    $('#peakLocation').prop('disabled', false);
    $('#peakGroup').removeClass('splitInput');
    $('#localRange').hide();
}

function nearestPeak(){
    $('#fitType').text('Fit around point');
    $('#fitType').append("<span class='caret'></span>");
    $('#peakLocation').attr('placeholder', 'Energy Value (meV)');
    $('#localRange').prop('placeholder', 'Range (meV)');
    $('#peakLocation').prop('disabled', false);
    $('#peakGroup').addClass('splitInput');
    $('#localRange').show();
}

var waitPeak = $.Deferred();
function fitPeak(sendOut){
    $('#fitBtn').removeClass('fitBtn');
    $('#fitBtn').addClass('fitBtnShifted');
    temp = $('#peakSignalType').text();
    previous = localStorage.getItem('previous2');
    $('#metaForm_id input').each(function(){
        $(this).removeProp('checked');
    })
    var unit = $('#unit').val();
    if ($('#fitType').text() == 'Fit around max'){
        var range = $('#pWInput').val()
        if ($.isNumeric(range)){
            $.post('/SDproc/peakFit', {idnum: previous, fitType: 'AtMax', inputRange: range, sendOut: sendOut, unit: unit,
            signal: $('#peakSignalType').text(), energy: $('#peakEnergyType').text()}, function(data){
                if (sendOut == 1){
                    localStorage.setItem('peakData', data);
                    waitPeak.resolve();
                }
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                $('#shiftVal').html( $(data).find('#shiftVal').html());
                localStorage.setItem('justPeakFit', 1);
            });
        }
        else{
            $('#meta-form').trigger('change');
            alert('Please enter a valid range')
        }
    }
    else if ($('#fitType').text() == 'Peak at Point'){
        var cord = $('#peakLocation').val()
        var range = $('#pWInput').val()
        if ($.isNumeric(cord)){
            if ($.isNumeric(range)){
                $.post('/SDproc/peakFit', {idnum: previous, fitType: 'AtPoint', inputCord: cord, inputRange: range,
                sendOut: sendOut, unit: unit, signalType: $('#peakSignalType').text(),
                energyType: $('#peakEnergyType').text()}, function(data){
                if (sendOut == 1){
                    localStorage.setItem('peakData', data);
                    waitPeak.resolve();
                }
                $('#plot_spot').html( $(data).find('#plot_spot').html());
                $('#shiftVal').html( $(data).find('#shiftVal').html());
                localStorage.setItem('justPeakFit', 1);
                })
            }
            else{
                $('#meta-form').trigger('change');
                alert('Please enter a valid range');
            }
        }
        else{
            $('#meta-form').trigger('change');
            alert('Please enter a valid point');
        }
    }
    else{
        var cord = $('#peakLocation').val()
        var range = $('#pWInput').val()
        var localRange = $('#localRange').val()
        if ($.isNumeric(cord)){
            if ($.isNumeric(range)){
                if ($.isNumeric(localRange)){
                    $.post('/SDproc/peakFit', {idnum: previous, fitType: 'AroundPoint', inputCord: cord, inputRange: range,
                    localRange: localRange, sendOut: sendOut, unit: unit, signalType: $('#peakSignalType').text(),
                    energyType: $('#peakEnergyType').text()}, function(data){
                        if (sendOut == 1){
                            localStorage.setItem('peakData', data);
                            waitPeak.resolve();
                        }
                        $('#plot_spot').html( $(data).find('#plot_spot').html());
                        $('#shiftVal').html( $(data).find('#shiftVal').html());
                        localStorage.setItem('justPeakFit', 1);
                    })
                }
                else{
                    $('#meta-form').trigger('change');
                    alert('Please enter a valid peak range');
                }
            }
            else{
                $('#meta-form').trigger('change');
                alert('Please enter a valid range');
            }
        }
        else{
            $('#meta-form').trigger('change');
            alert('Please enter a valid energy value');
        }
    }
}

$(function (){
    $('#HRMdd li a').on('click', function(event){
        var hrm = event.target.text;
        previous = localStorage.getItem('previous2');
        $.post('/SDproc/updateHRM', {idnum: previous, hrm: hrm}, function(data){
            $('#HRM').text(data)
            $('#HRM').append("<span class='caret'></span>");
            $('#meta-form').trigger('change');
        })
    })
})

function advance(){
    window.location.href = ("process");
}

function outputFile(){
    waitPeak = $.Deferred();
    if (localStorage.getItem('previous2') === null){
        alert('No file loaded');
    }
    else if (localStorage.getItem('justPeakFit') == 1){
        fitPeak(1)
        $.when(waitPeak).done(function(){
            $('#idnum').val(localStorage.getItem('previous2'));
            var cords = localStorage.getItem('peakData');
            $('#outType').val(2);
            $('#cordData').val(cords);
            $('#meta-form').attr('action', '/SDproc/generateOutput')
            $('#meta-form')[0].submit()
            $('#meta-form').attr('action', '');
        });
        return waitPeak.promise()
    }
    else{
        $('#idnum').val(localStorage.getItem('previous2'));
        $('#outType').val(1);
        $('#meta-form').attr('action', '/SDproc/generateOutput')
        $('#meta-form')[0].submit()
        $('#meta-form').attr('action', '');
    }
}

function setAE(event){
    if (event.target.text == 'Energy'){
        $('#againstE').text('Energy');
        $('#againstE').append("<span class='caret'></span>");
        $('#agaE').val('Energy');
    }
    else if (event.target.text == 'Energy xtal'){
        $('#againstE').text('Energy xtal');
        $('#againstE').append("<span class='caret'></span>");
        $('#agaE').val('Energy xtal');
    }
    else if (event.target.text == 'Energy xtal w/T'){
        $('#againstE').text('Energy xtal w/T');
        $('#againstE').append("<span class='caret'></span>");
        $('#agaE').val('Energy xtal w/T');
    }
    else if (event.target.text == 'Energy Fitted'){
        $('#againstE').text('Energy Fitted');
        $('#againstE').append("<span class='caret'></span>");
        $('#agaE').val('Energy Fitted');
    }
    else {
        $('#againstE').text('Point #');
        $('#againstE').append("<span class='caret'></span>");
        $('#agaE').val('Point #');
    }
    $('#meta-form').trigger('change');
}

function setPeakSignal(event){
    if (event.target.text == 'Signal Normalized'){
        $('#peakSignalType').text('Signal Normalized');
        $('#peakSignalType').append("<span class='caret'></span>");
    }
    else{
        $('#peakSignalType').text('Signal');
        $('#peakSignalType').append("<span class='caret'></span>");
    }
}

function setPeakEnergy(event){
    if (event.target.text == 'Energy Fitted'){
        $('#peakEnergyType').text('Energy Fitted');
        $('#peakEnergyType').append("<span class='caret'></span>");
    }
    else if (event.target.text == 'Energy xtal'){
        $('#peakEnergyType').text('Energy xtal');
        $('#peakEnergyType').append("<span class='caret'></span>");
    }
    else if (event.target.text == 'Energy xtal w/T'){
        $('#peakEnergyType').text('Energy xtal w/T');
        $('#peakEnergyType').append("<span class='caret'></span>");
    }
    else{
        $('#peakEnergyType').text('Energy');
        $('#peakEnergyType').append("<span class='caret'></span>");
    }
}

function setUnit(event){
    if (event.target.text == 'meV'){
        $('#unitBtn').text('meV');
        $('#unitBtn').append("<span class='caret'></span>");
        $('#unit').val('meV');
    }
    else{
        $('#unitBtn').text('keV');
        $('#unitBtn').append("<span class='caret'></span>");
        $('#unit').val('keV');
    }
    $('#meta-form').trigger('change');
}

function setPlotAgainst(){
    var currentAE = $('#currentAE').text();
    $('#againstE').text(currentAE);
    $('#againstE').append("<span class='caret'></span>");
    $('#agaE').val(currentAE);
}

function headerFile(){
    previous = localStorage.getItem('previous2');
    $.post("/SDproc/headerFile", {id: previous}, function(data){
        var header = $('<div>').text(JSON.parse(data)).text();
        $('#headerText').html(header.replace(/\n/g, '<br />'));
        $('#headerModal').modal('show');
    });
}

function logout(){
    if (localStorage.getItem('previous2') === null){
        window.location.href = ("logout");
    }
    else{
        previous = localStorage.getItem('previous2');
        $.post("/SDproc/save_comment", { idprev: previous, comment: $('#comment').val(), format: 1}, function(){
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


/*        if (hrm == 'Fe-inline-1meV'){
            var hrm = {};
            hrm['hrm_e0'] = 14412500.0
            hrm['hrm_bragg1'] = 18.4704
            hrm['hrm_bragg2'] = 77.5328
            hrm['hrm_geo'] = '++'
            hrm['hrm_alpha1'] = 2.6e-6
            hrm['hrm_alpha2'] = 2.6e-6
            hrm['hrm_theta1_sign'] = -1
            hrm['hrm_theta2_sign'] = 1
            $('#HRM').text('Fe-inline-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
        else if (hrm == 'Sn-nested-1meV'){
            var hrm = {};
            hrm['hrm_e0'] = 23880000.0
            hrm['hrm_bragg1'] = 19.3395
            hrm['hrm_bragg2'] = 83.4616
            hrm['hrm_geo'] = '++'
            hrm['hrm_alpha1'] = 2.6e-6
            hrm['hrm_alpha2'] = 2.6e-6
            hrm['hrm_theta1_sign'] = 1
            hrm['hrm_theta2_sign'] = 1
            $('#HRM').text('Sn-nested-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
        else if (hrm == 'Eu-nested-1meV'){
            alert('Not yet implemented')
            $('#HRM').text('Eu-nested-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
        else if (hrm == 'Dy-nested-1meV'){
            alert('Not yet implemented')
            $('#HRM').text('Dy-nested-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
        else if (hrm == 'IXS-cryo-1meV'){
            alert('Not yet implemented')
            $('#HRM').text('IXS-cryo-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
        else if (hrm == 'Sn-cryo-1meV'){
            var hrm = {};
            hrm['hrm_e0'] = 23880000.0
            hrm['hrm_bragg1'] = 9.122
            hrm['hrm_bragg2'] = 81.107
            hrm['hrm_geo'] = '++'
            hrm['hrm_alpha1'] = 2.6e-6
            hrm['hrm_alpha2'] = 0.0
            hrm['hrm_theta1_sign'] = -1
            hrm['hrm_theta2_sign'] = -1
            $('#HRM').text('Sn-cryo-1meV')
            $('#HRM').append("<span class='caret'></span>");
        }
*/