from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms.formsets import formset_factory

from django.forms import ValidationError

from forms import PasteForm
from models import Set, Paste

import settings

PasteSet = formset_factory(PasteForm)

def paste(request):
    try:
        forms = PasteSet(request.POST)
        return HttpResponse("good!")
    except ValidationError, e:
        print e
        forms = PasteSet()
        return render_to_response('paste.html', {
            'forms': forms
            }, RequestContext(request))
