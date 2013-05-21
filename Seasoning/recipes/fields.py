# Based on django-ajax-selects from crucialfelix
from django import forms
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from ingredients.models import Ingredient

class AutoCompleteSelectIngredientWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
        value = value or ''
        if value:
            try:
                ingredient = Ingredient.objects.get(pk=value)
            except ObjectDoesNotExist:
                raise Exception("Cannot find ingredient with id: %s" % value)
            return ingredient.name
        return value
    
class AutoCompleteSelectIngredientField(forms.fields.CharField):

    """
    Form field to select a model for a ForeignKey db field
    """

    def __init__(self, *args, **kwargs):
        widget = kwargs.get('widget', False)
        if not widget or not isinstance(widget, AutoCompleteSelectIngredientWidget):
            kwargs['widget'] = AutoCompleteSelectIngredientWidget()
        super(AutoCompleteSelectIngredientField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        if value:
            try:
                ingredient = Ingredient.objects.get(name__exact=value)
            except MultipleObjectsReturned:
                raise forms.ValidationError(u"Multiple result returned for ingredient name: %s" % value)
            except ObjectDoesNotExist:
                raise forms.ValidationError(u"No ingredient found with name: %s" % value)
            return ingredient
        else:
            if self.required:
                raise forms.ValidationError(self.error_message['required'])
            return None

    def bound_data(self, data, initial):
        return Ingredient.objects.get(pk=data).name