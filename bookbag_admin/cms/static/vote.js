function add_option() {
    var count = parseInt($('#option_count').text());
    var html = count % 2 ? "<td style='padding-left:40px'>" : '<tr><td>';
    var id = 'option' + (count + 1);
    html = html.concat('选项', count + 1, ":</td><td><textarea id='", id,
                       "' name='", id, "' rows='3' cols='20'></textarea></td>");
    html += count % 2 ? '' : '</tr>';
    if (count % 2)
        $('#option' + count).parent().after(html);
    else
        $('#option' + count).parent().parent().after(html);
    count += 1;
    $('#option_count').text(count);
    var option = '<option value="' + count + '">' + count + '</option>';
    $('#min_choice').append(option);
    $('#max_choice').append(option);
    $('#max_choice :nth-child(' + count + ')').attr('selected', 1);
}

function check_vote_type(type) {
    if (type == 'single') {
        $('#choice_number').hide();
    } else {
        $('#choice_number').show();
    }
    // $('.votetype').removeAttr('checked');
    // $('.votetype').filter('[value=' + type + ']').attr('checked', 1);
}

$(document).ready(function() {
    // var n = parseInt($('#option_count').text());
    // for (var i = 1; i <= n; i++) {
    //     var option = '<option value="' + i + '">' + i + '</option>';
    //     $('#min_choice').append(option);
    //     $('#max_choice').append(option);
    // }
    // $('#max_choice :nth-child(' + n + ')').attr('selected', 1);
    var type = $('.votetype').filter('[checked]').val();
    check_vote_type(type);
});
