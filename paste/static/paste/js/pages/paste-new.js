$(document).ready(function () {
    var ace_pos = 0;

    // Load the ACE editor and cache the binding between the
    // element and the mode for later reference.
    var editors = {};
    var ace = require(['ace/ace'], function (ace) {
        $('div.paste > pre').each(function () {
            var editor = ace.edit(this);
            editor.setTheme('ace/theme/textmate');
            editor.getSession().setMode('ace/mode/javascript');
            editors[this] = editor;
        });
    });

    // Logic for building an entry in the paste
    var build_row = function (li) {
        var $li = $(li);
        var $pre = $('div.paste > pre', $li);
        var $delete_row = $('a.delete-row', $li);

        $('div.close', $li).click(function () {
            $delete_row.click();
        });

        $('div.title', $li).each(function () {
            var $this = $(this);
            var $select = $('select', $this);
            var $input = $('input', $this);
            var split = [];
            var $chosen = $select.attr('data-placeholder', 'Choose a language').chosen();

            $('option', $this).each(function () {
                var value = $(this).val().split('|');
                var regexp = new RegExp(value[1]);
                $(this).val(value[0]);
                split.push([regexp, value[0]]);
            });

            var active_timer = null;
            $input.keyup(function () {
                clearTimeout(active_timer);
                var input_text = $(this).val();
                active_timer = setTimeout(function () {
                    for (var i = 0; i < split.length; i++) {
                        var s = split[i];
                        var re = s[0];
                        var element = s[1];
                        if (re.test(input_text)) {
                            $chosen.val(element).trigger("liszt:updated");
                            var editor = editors[$pre[0]];
                            editor.getSession().setMode('ace/mode/' + element);
                            return;
                        }
                    }
                }, 250);
            }).blur(function () {
                $(this).keyup();
            });

            $chosen.val('text').trigger('liszt:updated');
        });
    };

    // jquery.formset for integration with Django
    $('ul.pastes > li').formset({
        prefix: 'formset',
        addText: '',
        deleteText: '',
        added: function (e) {
            build_row(e);
        }
    });

    // Rebind the click-event handling
    $('#add-paste').click(function () {
        $('ul.pastes .add-row').click();
    });

    // Initial construction of the pages.
    $('ul.pastes > li').each(function (e) {
        build_row(this);
    });
});
