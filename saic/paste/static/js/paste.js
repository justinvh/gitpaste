$(document).ready(function (doc) {
    $("input").live("focus", function (e) {
        var $this = $(this);
        if ($this.val() == $this.attr('default')) {
            $this.val('');
        }
    }).live("blur", function (e) {
        var $this = $(this);
        if ($this.val() == "") {
            $this.val($this.attr('default'));
        }
    });

    $("input").blur();

    $('#paste-form > div.entry').formset({
        'addText': 'add another file',
        'deleteText': 'delete this file',
        'added': function () {
            $('input').blur();
        }
    })
});
