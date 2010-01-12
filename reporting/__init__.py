"""
"django-reporting" is a pluggable application to connect Django to Geraldo.

You must register a Report class, relating it to a model class inside a Django
application and use the template tags to take advantage on its power.
"""

VERSION = (0, 1, 'incomplete')

def get_version():
    return '%d.%d-%s'%VERSION

__author__ = 'Marinho Brandao'
__license__ = 'GNU Lesser General Public License (LGPL)'
__url__ = 'http://geraldo.sourceforge.net/'
__version__ = get_version()
#------------------------------------------------------------

import re, sets, imp

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings

from geraldo.generators import PDFGenerator

exp_report = re.compile('^(?P<app>[\w_]+)/(?P<model>[\w_]+)/(?P<name>[\w_-]+)/$')

LOADING = False
def autodiscover():
    global LOADING
    if LOADING:
        return
    LOADING = True

    for app in settings.INSTALLED_APPS:
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('reports', app_path)
        except ImportError:
            continue

        __import__("%s.reports" % app)
    
    LOADING = False

class ReportSite(object):
    reports = []

    def root(self, request, path):
        # Report path
        m = exp_report.match(path)
        if m:
            app, model, name = m.groupdict().values()

            return self.report_view(request, app, model, name)

        return render_to_response(
                'reporting/index.html',
                {
                    'title': _('Reports'),
                    'reports': self.reports,
                    },
                context_instance=RequestContext(request),
                )

    def report_view(self, request, app, model, name):
        # Find the registered report for this URL
        registered = self.get_report_by_url(request)

        # Initialize the reponse object
        resp = HttpResponse(mimetype='application/pdf')
        resp['Content-Disposition'] = 'filename=%s.pdf'%'-'.join([app, model, name])

        # Get the queryset
        queryset = self.get_queryset(request, registered['model'])

        # Initialize the report instance
        report = registered['report'](queryset=queryset)

        # Generate report into response object
        report.generate_by(PDFGenerator, filename=resp)

        return resp

    def get_adminmodel(self, model):
        from django.contrib.admin import site
        modeladmin = site._registry[model]
        
        return modeladmin

    def get_queryset(self, request, model):
        modeladmin = self.get_adminmodel(model)

        # Get ordering field and direction
        if modeladmin and 'o' in request.GET:
            order = modeladmin.list_display[int(request.GET['o'])]

            if request.GET.get('ot', None) == 'desc':
                order = '-'+order
        else:
            order = None

        # Get filters
        filter = dict([(str(k),v) for k,v in request.GET.items()\
            if not k in ('o','ot','q','p')])
        
        # Get the queryset
        queryset = model.objects.all()
        
        if filter:
            queryset = queryset.filter(**filter)

        # Sets the ordering
        if order:
            queryset = queryset.order_by(order)

        return queryset

    def register(self, report, model, name):
        path = '.'.join([model._meta.app_label, model.__name__, name]).lower()

        self.reports.append({
            'report': report,
            'model': model,
            'name': name,

            'app_label': model._meta.app_label,
            'model_label': model._meta.verbose_name_plural,
            'path': path,
            'url': path.replace('.', '/') + '/',
            })

        self.reports.sort(lambda a,b: cmp(a['path'], b['path']))

    def get_apps(self):
        return sets.Set([report['model']._meta.app_label for report in self.reports])

    def get_report_by_url(self, request=None, url=None):
        if not url and request:
            url = '/'.join(request.path_info.split('/')[2:])

        return [report for report in self.reports if report['url'] == url][0]

    def get_report_by_path(self, path):
        return [report for report in self.reports if report['path'] == path][0]

site = ReportSite()
