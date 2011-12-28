$(document).ready(function (doc) {
    $("input").live("focus", function (e) {
        var $this = $(this);
        if ($this.val() == $this.attr('default')) {
            $this.removeClass('default-input');
            $this.val('');
        }
    }).live("blur", function (e) {
        var $this = $(this);
        if ($this.val() == "") {
            $this.val($this.attr('default'));
            $this.addClass('default-input');
        }
    });

    var languages = [
        ['.cc', '.cpp;CppLexer'],
        ['.cxx', '.cpp;CppLexer'],
        ['.C', '.cpp;CppLexer'],
        ['.C', '.c;CLexer'],
        ['.h', '.c;CLexer'],
        ['.hpp', '.cpp;CppLexer'],
        ['.hxx', '.cpp;CppLexer'],
        ['.java', '.java;JavaLexer']
    ];

    var $options = $('div.language:first select > option')
    for (var i = 0; i < $options.length; i++) {
        languages.push([$options[i].value.split(';')[0], $options[i].value]);
    }

    $("input").blur();

    $('input.filename').live('keyup', function (e) {
        var $this = $(this);
        var $parent = $this.parents('div.entry');
        var $lang = $('div.language select', $parent);
        var val = $this.val();
        var ext = val.split('.')
        ext = '.' + ext[ext.length - 1];

        for (var i = 0; i < languages.length; i++) {
            if (languages[i][0] == ext) {
                $lang.val(languages[i][1]);
                return;
            }
        }
        $lang.val('.txt');
    });

    $('#paste-form > div.entry').formset({
        'addText': 'add another file to this paste',
        'deleteText': 'delete this file',
        'added': function () {
            $('div.entry:last div.anonymous').remove();
            $('textarea').tabby({'tabString': '    '});
            $('div.entry:last input').val('');
            $('div.entry:last select').val('');
            $('div.entry:last textarea').html('');
            $('input').blur();
        }
    })

    $('textarea').tabby({'tabString': '    '});
});
