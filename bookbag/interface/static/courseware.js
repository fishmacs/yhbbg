function query_state() {
    $('[id^=courseware_state]').each(function() {
        var cid = $(this).attr('id').replace('courseware_state', '');
        var action = $('#courseware_action');
        if (action.find('img').length > 0) {
            $.get('/ajax/courseware_state/' + cid + '/', 
                  success = function(data) {
                      var state = data.split(',');
                      if (state.length > 0) {
                          $('#courseware_state'+cid).text(state[0]);
                          if (state.length > 2) {
                              if (state[1].length > 0)
                                  action.html("<a href='".concat(state[2], "'>", state[1], "</a>"));
                          }
                          else
                              action.html('');
                      }
                      var i = state.length > 2 ? 3 : 1;
                      if (state[i] > 0)
                          $('#reconvert_url').show();
                      else
                          $('#reconvert_url').hide();
                  });
        }
    });
}

function reconvert_confirm(courseware_id) {
    if (confirm('本功能是对上一次转换不成功的PDF文件进行强制转换\n可能导致课件中某些内容不能搜索\n您确定要继续吗？'))
        $.ajax({
            url: '/courseware_convert/' + courseware_id +'/?reconvert&ajax',
            async: false,
            success: function(result) {
                var state = $('#courseware_state'+courseware_id)
                state.text('格式转换中...');
                state.next().html('');
                state.next().next().html('');
            }
        });
}

function basename(path) {
    return path.replace(/\\/g, '/').replace(/.*\//, '');
}

function file_change() {
    var filename = basename($('#id_file').val());
    if($('#newware').val() == 'True' && $('#id_title').val().replace(/\\s+/g, '').length==0)
        $('#id_title').val(filename.replace(/\.\w+$/, ''));
    $('#filename').text(filename);
}

function update_progress(progbar) {
    var upload_id = $('#upload_id').text();
    $.getJSON('/ajax/courseware/upload/progress/'+upload_id+'/', 
              {}, 
              function(data, status) {
                  if (data && data.length>1) {
                      var progress = data[0] * 100 / data[1];
                      progbar.progressbar({value: progress});
                      progbar.children('.ui-progressbar-value').text(Math.round(progress)+'%');
                      if (data[0] >= data[1])
                          progbar.timer('stop');
                  }
              });
}

function on_submit() {
    var progbar = $('#progressbar');
    progbar.progressbar({value: 0});
    progbar.show();
    progbar.timer({delay: 1000, repeat: true, callback: function() {
        update_progress(progbar);
    }});
}

$(document).ready(function () {
    $('#id_file').change(file_change);
    window.setInterval(query_state, 5000);
    $('#upload_form').submit(function() {
        $('#upload_form').timer({delay: 1000, callback: on_submit});
    });
    if ($('#courseware_reconvert').text() == 'True')
        $('#reconvert_url').show();
});
