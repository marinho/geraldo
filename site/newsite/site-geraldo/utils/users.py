#messages_pool = []

def post_message(request, msg):
    #global messages_pool
    #messages_pool.append(msg)
    try:
        if not 'messages_pool' in request.session:
            request.session['messages_pool'] = []

        request.session['messages_pool'] = request.session['messages_pool'] + [msg]
    except:
        pass

