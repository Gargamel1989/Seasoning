from django import template
from markdown import markdown as markdown_lib

register = template.Library()

@register.filter
def markdown(text):
    return markdown_lib(text, safe_mode='escape')