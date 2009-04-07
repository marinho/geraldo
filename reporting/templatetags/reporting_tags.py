from django import template
from django.template import Library, Node
from django.core.urlresolvers import reverse

from reporting import site

register = Library()

class ReportUrlNode(template.Node):
    report_path = None

    def __init__(self, report_path):
        self.report_path = template.Variable(report_path)

    def render(self, context):
        report_path = self.report_path.resolve(context)

        root_url = reverse('reporting_root', args=[''])
        report_url = site.get_report_by_path(report_path)['url']
        request = context['request']
        
        return root_url + report_url + '?' + request.META['QUERY_STRING']

def do_get_report_url(parser, token):
    try:
        parts = token.split_contents()

        report_path = parts[1]
    except KeyError:
        raise template.TemplateSyntaxError, "You must inform report path"

    return ReportUrlNode(report_path)

register.tag('get_report_url', do_get_report_url)


