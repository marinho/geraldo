"""
    >>> from gae_blog.templatetags.blog_tags import parse_blog

    >>> text = 'maria [% blog:recent():5 %] vai com as outras'
    >>> parse_blog(text)
"""
