"""
    >>> from gae_wiki.templatetags.wiki_tags import parse_wiki

    >>> text = 'maria [% wiki:all(published,tag=destaque):5 %] vai com as outras'
    >>> parse_wiki(text)
"""
