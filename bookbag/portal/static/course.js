var processing = false;

var page_info = {
    total_page: 0,
    curr_page: 0,
    count_per_page: 6,
};

var json_courseware = null;

function switchdetail(courseid, category) {
    if(processing) return;

    processing = true;
	// $('#courselist').fadeTo(50, 0.2);
	// $('[id^=cate]').hide();
	// $('[id^=cate_'+cid+']').show();
	// $('#detail'+tid).show(500);
    var detail_id = '#coursedetail' + courseid + category;
    var courselist = $('#courselist')
    var detail = $('#coursedetail')

    courselist.fadeTo(50, 0.2);
    if ($(detail_id).length > 0) {
        $(detail_id).show(500);        
        //processing = false;
    } else {
        // detail.show(500);
        // $.ajax({
        //     url: '/courseware/' + courseid + '/' + category + '/',
        //     //async: false, // only/necessary for chrome, otherwise success would never be called
        //     success: function(result) {
        //         detail.after(result);
        //         detail.hide(500);
        //         $(detail_id).show(500);
        //         processing = false;
        //     },
        //     error: function(req, status, err) {
        //         detail.hide(500);
        //         courselist.fadeTo(50, 1.0);
        //         processing = false;
        //     }
        // });
        if(json_courseware) {
            detail.after(detail.clone().removeAttr('id').attr('id', 'coursedetail'+courseid+category));
            obj = {
                courseid: courseid,
                category: category,
                coursewares: json_courseware[courseid][category],
            };
            $('#courseware_template').tmpl(obj).appendTo(detail_id);
            $(detail_id).show(500);
        }
    }
    processing = false
}

function switchcourse(courseid, category) {
    var id = '#coursedetail';
    if (courseid && category) {
        id += courseid;
        id += category;
    }
	$(id).hide(100);
	$('#courselist').fadeTo(50, 1.0);
}

function download_ok(cid, cwid, cat) {
    var is_new = $('#download_new_' + cwid).is(':visible');
    if (is_new) {
        $('#download_new_' + cwid).hide();
        var node = $('#update_number'+cid+'_'+cat);
        var span = node.find('span');
        var n = span.text()/*.replace(/\s+/g, '')*/ - 1;
        if(n)
            span.text(String(n));
        else
            node.hide();
    }
    $('#downloaded_' + cwid).show();
    $.get('/download_ok/' + cwid + '/' + (is_new ? 1 : 0) + '/');
}

// function align_number(n) {
//     var nbsps = ['&nbsp;', '&nbsp;', '&nbsp;']
//     var prefix = nbsps.slice(0, Math.min(nbsps.length-n.length, 0)).join('')
//     return prefix + n;
// }

// function decorate_update_number() {
//     $('[id ^= update_number]').each(function() {
//         var span = $(this).find('span')
//         var n = span.text().replace(/\s+/g, '');
//         span.html(align_number(n));
//     });
// }

function setup_page_info() {
    var total_count = $('[id ^= course_item_]').size();
    page_info.total_page = Math.ceil(total_count / page_info.count_per_page);
    // alert(String(page_info.total_page) + ',' + total_count);
    var total_width = $('.lesson').width() * page_info.total_page;
    $('.les_mid').width(total_width + 'px');
    var idx = 0;
    var les_fy = $('.les_fy');
    for (var i=0; i<page_info.total_page; i++) {
        $('#course_pages').append("<td><ul id='course_page_" + i + "'></ul></td>");
        var page = $('#course_page_' + i);
        for(var j=0; j<page_info.count_per_page; j++) {
            $('#course_item_'+idx).clone().appendTo(page);
            idx++;
        }
        les_fy.append('<span></span>');
    }
    $('.les_fy :nth-child(1)').addClass('active');
    $('#all_course_items').remove();
    $('.les_mid').css('-webkit-transition-duration', '500ms');
    $('.les_mid').css('-webkit-transform', 'translate3d(0, 0, 0)');
    // var course_page1 = $('#course_page1');
    // course_page1.css('position', 'absolute');
    // course_page1.css('left', course_page1.width()+'px');
    // course_page1.css('top', '0');
}

$(document).ready(function () {
    //decorate_update_number();
    setup_page_info();
    courseware_from_json();
});

function prev_page() {
    if(page_info.curr_page > 0) {
        //window.setTimeout('change_page(-1)', 1000);
        change_page(-1);
        //$('.les_mid').css('-webkit-transition-duration', '0ms');
    }
}   

function next_page() {
    if(page_info.curr_page < page_info.total_page-1) {
        //$('.les_mid').css('-webkit-transition-duration', '1000ms');
        //window.setTimeout('change_page(1)', 1000);
        change_page(1);
        //$('.les_mid').css('-webkit-transition-duration', '0ms');
    }
}

function change_page(n) {
    // $('#all_course_items').fadeOut('slow', function() {
    var i = page_info.curr_page+1;
    $('.les_fy :nth-child(' + i + ')').removeClass('active');

    page_info.curr_page += n;
    var x = -page_info.curr_page * $('.lesson').width();
    $('.les_mid').css('-webkit-transform', 'translate3d(' + x + 'px, 0, 0)');

    i = page_info.curr_page+1;
    $('.les_fy :nth-child(' + i + ')').addClass('active');
    // });
    // $('#all_course_items').fadeIn('slow');
   // $('ul').css('-webkit-transition-duration', '0ms');
}

function checkload() {
    return document.getElementById('coursedetail') != null ? 'YES' : 'NO';
    //return $('#coursedetail').length > 0 ? 'YES' : 'NO';
}

function checknewitem() {
    var sum = 0;
    $('.update_mark').each(function() {
        var span = $(this).find('span');
        var n = parseInt(span.text());
        if(isNaN(n)) n = 0;
        sum += n;
    });
    return sum;
}

function courseware_from_json() {
    json_courseware = json_data;//$.parseJSON(json_data);
}

function decorate_url(courseid, category, courseware) {
    return courseware.url.replace(/getfile\?/, 'getfile?coursename='.concat(courseware.course_name, '&coursename_en=', courseware.course_name_en, '&courseid=', courseid, '&category=', get_category(category), '&category_id=', category, '&category_name=', courseware.category_name, '&category_name_en=', courseware.category_name_en, '&bookname=', courseware.name, '&'));
}

function get_category(category) {
    switch (category) {
    case 2: return 'preread'
    case 5: return 'handout'
    default: return 'binder'
    }
}
        
function get_course_name(courseware) {
    if(courseware.lang=='en' && courseware.course_name_en != '')
        return courseware.course_name_en
    return courseware.course_name;
}

function get_category_name(courseware) {
    if(courseware.lang=='en' && courseware.category_name_en != '')
        return courseware.category_name_en
    return courseware.category_name;
}

function confirm_download(courseware_id, downloaded) {
    if(downloaded) {
        var dlg = $('#confirm_dialog');
        //dlg.html('该课件已经下载过，重新下载将覆盖旧的课件，确定要下载吗？');
        dlg.dialog({
            open: function() {
                $(this).parents('.ui-dialog-buttonpane button:eq(1)').focus(); 
            },
            title: '注意',
            model: true,
            buttons: {
                "　取　消　": function () {
                    $(this).dialog('close');
                    return false;
                },
                "　确　定　": function () {
                    $(this).dialog('close');
                    var url = $('#courseware_url_'+courseware_id).attr('href');
                    window.location.href = url;
                }
            }
        });
        return false;
    } else
        return true;
}

function show_password_form() {
    $('#courselist').fadeTo(500, 0.2);
    $('#password_form').show(500);    
}

function cancel_passwd() {
    $('#password_form').hide(500);
    $('#courselist').fadeTo(500, 1.0);
    $('#loading_image').hide();
    $('#passwd_form').fadeTo(50, 1.0);
    $('#passwd_error').hide();
}

function check_password() {
    var oldpass = $('#old_passwd').val();
    if (!oldpass)
        return '请输入当前密码';
    else if(oldpass.length < 6)
        return '当前密码至少为6位!';

    var newpass = $('#new_passwd').val();
    if (!newpass)
        return '请输入新密码';
    else if(newpass.length < 6)
        return '新密码至少为6位!';

    if (newpass == oldpass)
        return '新密码必须与当前密码不同！';

    var newpass1 = $('#new_passwd1').val();
    if (newpass != newpass1)
        return '两次输入的密码不匹配！';
}

function commit_passwd_change() {
    if (processing) return;
    processing = true;

    var errmsg = check_password();
    if (errmsg) {
        var error = $('#passwd_error');
        error.text(errmsg);
        error.show(200);
    } else {
        var form = $('#passwd_form');
        form.fadeTo(50, 0.2);

        var loading = $('#loading_image');
        loading.css('top', form.height()/2 + 'px');
        loading.css('left', $('#password_form').width()/2-16 + 'px');    
        loading.show(500);
        
        $.ajax({
            url: '/ajax/user/prof/edit_passwd/',
            type: 'POST',
            data: { 
                old_passwd: $('#old_passwd').val(), 
                new_passwd: $('#new_passwd').val() 
            },
            success: passwd_success,
            error: passwd_fail,
            async: false,
        });
    }
    processing = false;
}

function passwd_success(data) {
    if (data) {
        $('#loading_image').hide();
        $('#passwd_form').fadeTo(50, 1.0);
        var error = $('#passwd_error');
        error.text(data);
        error.show(200);
    } else {
        cancel_passwd();
    }
}

function passwd_fail(req, status, err) {
    $('#loading_image').hide();
    $('#passwd_form').fadeTo(50, 1.0);

    var errmsg = '';
    if (req.status < 100)
        errmsg = '服务器无法连接';
    else
        errmsg = '服务端错误：' + req.status;

    var error = $('#passwd_error');
    error.text(errmsg);
    error.show(200);
}