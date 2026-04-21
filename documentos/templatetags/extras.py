from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acessar um dicionário por chave em templates Django"""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None