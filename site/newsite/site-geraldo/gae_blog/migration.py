import re, datetime

from google.appengine.ext import db

from django.utils import simplejson

from models import Entry

def import_from_json(data, show=False):
    ret = []

    if show:
        print len([i for i in Entry.all()])

    # Deserialize
    objects = simplejson.loads(data)

    for obj in objects:
        if obj['model'] != 'blog.entry':
            continue

        #if obj['fields']['media_type'] == 'I':
        #    print "'%s': %s"%(obj['fields']['slug'], obj['pk'])
        #continue

        if obj['fields']['media_type'] != 'P' or not obj['fields']['published']:
            continue

        msg = '%d %s'%(obj['pk'], obj['fields']['title'])
        if show:
            print msg
        else:
            ret.append(msg)

        # Blog entry
        try:
            entry = Entry.all().filter('old_id =', int(obj['pk']))[0]
        except IndexError:
            entry = Entry()

        entry.old_id = obj['pk']

        m = RE_DATETIME.match(obj['fields']['pub_date'])
        groups = [int(i) for i in m.groups()]
        entry.pub_date = datetime.datetime(*groups)

        entry.title = obj['fields']['title']
        entry.description = obj['fields']['description']
        entry.format = obj['fields']['format']
        entry.published = True
        entry.show_in_rss = False
        entry.slug = obj['fields']['slug']
        entry.tags = [db.Category(TAGS[tag]) for tag in obj['fields']['tags']]

        text = obj['fields']['content']
        text = text.replace('http://media.marinhobrandao.com/','/')

        f = RE_IMG_URL.findall(text)
        rep = []

        for url in f:
            m = RE_IMG_URL2.match(url)
            new_url = '/media/img/upload/%s'%IMAGES[m.group(1)]

            if show:
                print '\t', new_url

            text = text.replace(url, new_url)

        entry.text = text

        entry.save()

        # Gallery image

    msg = [i.slug for i in Entry.all()]
    if show:
        print msg
    else:
        ret.append(' '.join([i for i in msg]))

TAGS = {2: 'web',
 3: 'linux',
 4: 'apple',
 5: 'windows',
 6: 'python',
 7: 'blogosfera',
 8: 'java',
 9: 'net',
 10: 'opiniao',
 11: 'rails',
 12: 'software-livre',
 13: 'django',
 14: 'turbogears',
 15: 'publicidade',
 16: 'zope',
 17: 'screencast',
 18: 'emprego',
 19: 'tron',
 20: 'adoradores',
 21: 'seguranca',
 22: 'inovacao',
 24: 'projetos',
 25: 'banco-de-dados',
 26: 'religiao',
 27: 'cristaos',
 28: 'microsoft',
 29: 'google',
 30: 'musica',
 31: 'familia',
 32: 'yadsel',
 33: 'ajax',
 34: 'brasil',
 35: 'android',
 36: 'opensocial',
 37: 'tdd',
 38: 'gadgets',
 39: 'livros',
 40: 'lua'}

RE_DATETIME = re.compile('(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})')
RE_IMG_URL = re.compile('(/blog/p/[\w_-]+/\?img=1)')
RE_IMG_URL2 = re.compile('/blog/p/([\w_-]+)/\?img=1')

IMAGES = {
'geraldo-tutorial-imagem-4': '192.png',
'geraldo-tutorial-imagem-3': '191.png',
'geraldo-tutorial-imagem-2': '190.png',
'geraldo-tutorial-imagem-1': '189.png',
'aprendendo-django-ilustracao': '187.png',
'tela_mysql_proxypng': '173.png',
'diagrama_mysql_proxypng_172': '172.png',
'diagrama_mysql_proxypng': '171.png',
'diagrama_apache_wsgi_djangopng': '170.png',
'tempo_de_resposta_por_requisicaopng': '169.png',
'teste_wsgigif': '168.gif',
'rss_memoria_ocupadapng': '167.png',
'requisicoes_por_segundopng': '166.png',
'percentual_da_cpupng': '165.png',
'load_de_5_minutospng': '164.png',
'load_de_1_minutopng': '163.png',
'ajax-many2manyfield-widget-screenshot_152': '152.gif',
'152': '152.gif',
'vivixvideo1': '150.png',
'150': '150.png',
'screenshot-do-2e2': '139.png',
'screenshot-do-blog': '138.png',
'screenshot-xmlswf-charts': '134.png',
'134': '134.png',
'screenshot-djangobrasilorg': '132.png',
'132': '132.png',
}
