from django import template
import markdown as markdown_lib

register = template.Library()

@register.filter
def markdown(text):
    return markdown_lib.markdown(text)