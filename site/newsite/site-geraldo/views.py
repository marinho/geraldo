# -*- coding: utf-8 -*-
from google.appengine.api import mail, memcache

from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from utils.decorators import page, admin_required
from utils.users import post_message

@page('admin_user_required.html')
def admin_user_required(request):
    return locals()

@login_required
@admin_required
@page('admin/index.html')
def admin_index(request):
    return locals()

class FormContact(forms.Form):
    name = forms.CharField(max_length=50, label='Your name')
    email = forms.EmailField(label='E-mail address')
    message = forms.Field(widget=forms.Textarea, label='Message body')

    def send(self):
        body = """Name: %(name)s
E-mail: %(email)s

Message:
%(message)s"""%self.cleaned_data

        mail.send_mail(
                sender="%s <%s>"%settings.MANAGERS[0],
                to="%s <%s>"%settings.MANAGERS[0],
                subject=settings.CONTACT_SUBJECT,
                body=body,
                )
        return True

@page('contact.html')
def contact(request):
    if request.method == 'POST':
        form = FormContact(request.POST)

        if form.is_valid():
            if form.send():
                post_message(request, u'Mensagem enviada com sucesso! Obrigado!')
                return HttpResponseRedirect(reverse('wiki_index'))
            
            post_message(request, u'Ocorreu um erro ao tentar enviar mensagem. Verifique se sua mensagem é muito curta')
    else:
        form = FormContact()

    return locals()

@login_required
@admin_required
def admin_update_cache(request):
    memcache.flush_all()
    post_message(request, u'All cache items deleted to be updated.')

    return HttpResponseRedirect(reverse('views.admin_index'))

def robots_txt(request):
    ret = render_to_string('robots.txt')
    return HttpResponse(ret, mimetype='text/plain')

