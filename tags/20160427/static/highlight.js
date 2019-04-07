$(function()
{
    var rows = $('tr.item');
    rows.on('click', function(e)
    {
        var row = $(this);
        if((e.ctrlKey || e.metaKey) || e.shiftKey)
        {
            row.addClass('highlight');
        }
        else
        {
            rows.removeClass('highlight');
            rows.removeClass('lightlight');
            row.addClass('highlight');
        }
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