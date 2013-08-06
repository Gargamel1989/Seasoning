"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
# Based on django-ajax-selects from crucialfelix
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from ingredients.models import Ingredient
from django.forms.widgets import Widget, Select
from django.utils.safestring import mark_safe
import calendar

class MonthWidget(Widget):
        
    month_field = '%s_month'
    
    def render(self, name, value, attrs=None):
        try:
            month_val = value.month
        except AttributeError:
            month_val = None
        
        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        month_choices = ((0, '---'),
                         (1, 'Januari'), (2, 'Februari'), (3, 'Maart'), (4, 'April'), (5, 'Mei'), (6, 'Juni'),
                         (7, 'Juli'), (8, 'Augustus'), (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'December'))
        local_attrs = self.build_attrs(id=self.month_field % id_)
        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)
        
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        m = data.get(self.month_field % name)
        if m == "0":
            return None
        if m:
            return '%s-%s-%s' % (2000, m, 1)
        return data.get(name, None)

class LastOfMonthWidget(MonthWidget):
    def value_from_datadict(self, data, files, name):
        m = data.get(self.month_field % name)
        if m == "0":
            return None
        if m:
            return '%s-%s-%s' % (2000, m, calendar.monthrange(2000, int(m))[1])
        return data.get(name, None)
    
class AutoCompleteSelectIngredientWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
        value = value or ''
        if value:
            try:
                ingredient_pk = int(value)
                value = Ingredient.objects.get(pk=ingredient_pk).name
            except ValueError:
                # If we cannot cast the value into an int, it's probably the name of
                # the ingredient already, so we don't need to do anything
                pass
            except ObjectDoesNotExist:
                raise Exception("Cannot find ingredient with id: %s" % value)
        return super(AutoCompleteSelectIngredientWidget, self).render(name, value, attrs)
    
class AutoCompleteSelectIngredientField(forms.fields.CharField):

    """
    Form field to select a model for a ForeignKey db field
    """

    def __init__(self, *args, **kwargs):
        widget = kwargs.get('widget', False)
        if not widget or not isinstance(widget, AutoCompleteSelectIngredientWidget):
            kwargs['widget'] = AutoCompleteSelectIngredientWidget(attrs={'class': 'autocomplete-ingredient'})
        super(AutoCompleteSelectIngredientField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        if value:
            try:
                ingredient = Ingredient.objects.get(name__exact=value)
            except ObjectDoesNotExist:
                raise forms.ValidationError(u"No ingredient found with name: %s" % value)
            return ingredient
        else:
            if self.required:
                raise forms.ValidationError(u"This field is required.")
            return None