$(document).ready(function () {
    var ace_pos = 0;

    // Load the ACE editor and cache the binding between the
    // element and the mode for later reference.
    var editors = {};
    var ace_loaded = false;
    var ace;

    require(['ace/ace'], function (ace_build) {
        ace = ace_build;
        $('ul.pastes > li').each(function (i, e) {
            build_ace(e);
        });
        ace_loaded = true;
    });

    var build_ace = function (e) {
        var $pre = $('pre', e);
        console.log($pre);
        var $textarea = $('textarea', e);
        var editor = ace.edit($pre[0]);
        editor.setTheme('ace/theme/textmate');
        editor.getSession().setMode('ace/mode/javascript');
        editor.getSession().setUseSoftTabs(true);
        editor.setKeyboardHandler('ace/keyboard/vim');
        editor.getSession().on('change', function() {
              $textarea.val(editor.getSession().getValue());
        });

        $('span.editor_mode > select', e).change(function () {
            editor.setKeyboardHandler('ace/keyboard/' + this.value);
            editor.focus();
        }).change();

        $('span.tab_size > select', e).change(function () {
            editor.getSession().setTabSize(this.value);
            editor.focus();
        }).change();

        $('span.hard_tab > select', e).change(function () {
            if (e.value == 'soft') {
                editor.getSession().setUseSoftTabs(true);
            } else {
                editor.getSession().setUseSoftTabs(false);
            }
            editor.focus();
        }).change();

        editors[$pre[0]] = editor;
    };

    // Reconstruct the priority list.
    var build_priority = function () {
        $('ul.pastes > li').each(function (i, e) {
            $('.priority', e).html(i + 1);
        });
    };

    // Logic for building an entry in the paste
    var build_row = function (li) {
        var $li = $(li);
        var $pre = $('div.paste > pre', $li);
        var $delete_row = $('a.delete-row', $li);

        $('div.close', $li).click(function () {
            $delete_row.click();
        });

        $('select', $li).chosen();

        $('div.title', $li).each(function () {
            var $this = $(this);
            var $select = $('select', $this);
            var $input = $('input', $this);
            var split = [];
            var $chosen = $select.attr('data-placeholder', 'Choose a language').chosen();

            $('option', $this).each(function () {
                var value = $(this).val().split('|');
                var regexp = new RegExp(value[1]);
                split.push({'regex': regexp,
                            'value': $(this).val(),
                            'editor': value[0]});
            });

            var active_timer = null;
            $input.keyup(function () {
                clearTimeout(active_timer);
                var input_text = $(this).val();
                active_timer = setTimeout(function () {
                    for (var i = 0; i < split.length; i++) {
                        var data = split[i];
                        if (data.regex.test(input_text)) {
                            console.log(data);
                            var mode = 'ace/mode/' + data.editor;
                            $chosen.val(data.value).trigger("liszt:updated");
                            editors[$pre[0]].getSession().setMode(mode);
                            return;
                        }
                    }
                }, 250);
            }).blur(function () {
                $(this).keyup();
            });

            $chosen.val('text|\\.txt$').trigger('liszt:updated');
        });

        build_priority();
        if (ace_loaded)
            build_ace($li);
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

    $('ul.pastes').sortable({
        cursor: 'move',
        distance: 5,
        helper: 'clone',
        handle: '.title',
        start: function (event, ui) {
             ui.placeholder.height(40);
            $('ul.pastes > li, .ui-sortable-helper').addClass('resize');
        },
        stop: function (event, ui) {
            $('ul.pastes > li, .ui-sortable-helper').removeClass('resize');
        },
        update: function (event, ui) {
            build_priority();
        }
    });
});
