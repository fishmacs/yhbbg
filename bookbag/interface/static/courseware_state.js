function query_state() {
    $('[id^=courseware_state]').each(function() {
        var cid = $(this).attr('id').replace('courseware_state', '');
        var elem = $('#courseware_state'+cid)
        var next = elem.next();
        if (next.find('img').length > 0) {
            $.get('/interface/courseware/state/' + cid + '/', 
                  success = function(data) {
                      var state = data.split(',');
                      if (state.length > 0) {
                          elem.text(state[0]);
                          if (state.length > 2) {
                              if (state[1].length > 0)
                                  next.html("<a href='".concat(state[2], "'>", state[1], "</a>"));
                          }
                          else
                              next.html('');
                      }
                  });
        }
    });
}

$(document).ready(function () {
    window.setInterval(query_state, 5000);
});
