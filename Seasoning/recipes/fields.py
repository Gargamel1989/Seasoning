# Based on django-ajax-selects from crucialfelix
from django import forms
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from ingredients.models import Ingredient

class AutoCompleteSelectIngredientField(forms.fields.CharField):

    """
    Form field to select a model for a ForeignKey db field
    """

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
