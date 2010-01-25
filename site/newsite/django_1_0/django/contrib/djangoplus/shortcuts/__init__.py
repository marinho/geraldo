from django.shortcuts import render_to_response
from django.core.mail import EmailMessage, SMTPConnection
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.http import HttpResponse

def render_to_json(obj):
    response = HttpResponse(obj)
    response['mimetype'] = "text/javascript"
    response['Pragma'] = "no cache"
    response['Cache-Control'] = "no-cache, must-revalidate"

    return response

def render_to_mail(template_path, params, subject, from_email=None, recipient_list=[], auth_user=None, auth_password=None, fail_silently=False, content_subtype=None, attachments=[], **kwargs): 
    """ 
    Sends a e-mail message with content parsed from a template. The syntax is  
    the same of render_to_response function. 
    Returns then boolean of mail sending, using core.mail.send_mail function. 
    """ 
    content_subtype = content_subtype or getattr(settings, 'DEFAULT_EMAIL_CONTENT_SUBTYPE', 'html') 
    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None) 
    
    if not recipient_list:
        return False 

    # Loads template for mail content 
    t = get_template(template_path) 
    
    # Render content 
    message = t.render(Context(params)) 

    # SMTP connection
    connection = SMTPConnection(username=auth_user, password=auth_password, fail_silently=fail_silently)

    # Email object 
    email_obj = EmailMessage(subject, message, from_email, [r.strip() for r in recipient_list], connection=connection)
    
    email_obj.content_subtype = content_subtype 
    
    if attachments: 
        for att in attachments:
            email_obj.attach_file(att) 
    
    return email_obj.send() 

