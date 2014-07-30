function hide_image_clear () {
    $('[id=image-clear_id]').each(function () {
        $(this).hide();
        $(this).next().hide();
    });
}

$(document).ready(function () {
    hide_image_clear()
});