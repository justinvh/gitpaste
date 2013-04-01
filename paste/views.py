from django.shortcuts import render_to_response as _render_to_response
from django.shortcuts import redirect, get_object_or_404
from django.template import RequestContext

from paste.forms import PasteMetadataForm, PasteFormSet
from paste.models import Paste


def render_to_response(tmpl, ctxt, request_ctxt):
    return _render_to_response("paste/{0}".format(tmpl), ctxt, request_ctxt)


def random_name():
    import uuid
    return str(uuid.uuid4())


def paste_new(request):
    owner = request.user if request.user.is_authenticated() else None
    metadata_form = PasteMetadataForm(prefix='metadata')
    paste_formset = PasteFormSet(prefix='formset')
    data = {'metadata_form': metadata_form, 'paste_formset': paste_formset}

    if request.method == 'POST':
        metadata_form = PasteMetadataForm(request.POST, prefix='metadata')
        paste_formset = PasteFormSet(request.POST, prefix='formset')
        data = {'metadata_form': metadata_form,
                'paste_formset': paste_formset}

        if metadata_form.is_valid() and paste_formset.is_valid():
            description = metadata_form.cleaned_data['description']
            paste = Paste(owner=owner,
                          description=description,
                          private='Private' in request.POST.get('submit'))

            # We have to explicitly save here since objects.create()
            # seems to do something else fancy with the relation manager
            paste.save()

            # Add all the new files to the paste
            for paste_form in paste_formset:
                filename = paste_form.cleaned_data['filename'] or random_name()
                content = paste_form.cleaned_data['paste']
                paste.add_file(filename, content)

            return redirect(paste.get_absolute_url())

    return render_to_response("paste_new.html", data, RequestContext(request))


def paste_view(request, pk, secret_key=None):
    from django.http import HttpResponseForbidden
    paste = get_object_or_404(Paste, pk=pk)
    if paste.private and secret_key != paste.private_key:
        raise HttpResponseForbidden
    data = {'paste': paste}
    return render_to_response("paste_view.html", data, RequestContext(request))
