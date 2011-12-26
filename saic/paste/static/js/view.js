$(document).ready(function () {
    $('#favorite-toggle').click(function () {
        var $this = $(this);
        $.get('/paste/' + set + '/favorite/');
        var $img = $('img', $this);
        if ($this.attr('favorite') == "True") {
            $img.attr('src', '/static/img/not-favorite.png');
            $this.removeAttr('favorite');
        } else {
            $img.attr('src', '/static/img/favorite.png');
            $this.attr('favorite', "True");
        }
    });
});
