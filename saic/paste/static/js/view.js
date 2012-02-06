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

    $diff = $('#diff');
    $diff_toggle = $('#diff-toggle');
    $diff_toggle.click(function () {
        if ($diff.is(":visible")) {
            $diff_toggle.html('show diff');
            $diff.hide();
        } else {
            $diff_toggle.html('hide diff');
            $diff.show();
        }
    });

    // jQuery is used for this example, but JavaScript Linkify doesn't require
    // any third-party libraries.

    $('pre span').each(function(){
        var that = $(this),
        txt = that.html(),
        options = {
            callback: function( text, href ) {
                href && console.log([ text, href ]);
                return href ? '<a target="_blank" href="' + href + '" title="' + href + '">' + text + '</a>' : text;
            }
        };
        that.html(linkify( txt, options )); 
    });

    // yuk yuk yuk
    $(window).ready(function () {
        $(window).resize(function () {
            $('table.highlighttable div.highlight pre').width($('div.entryless:first').width() - 90);
        }).resize();
    });
});
