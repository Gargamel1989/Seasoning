from django import forms
from recipes.models import Recipe, UsesIngredient
from django.forms import widgets
from recipes.fields import AutoCompleteSelectIngredientField
from ingredients.models import Unit

class AddRecipeForm(forms.ModelForm):
    
    class Meta:
        model = Recipe
        exclude = ['author', 'time_added',
                   'rating', 'number_of_votes',
                   'ingredient_ingredients',
                   'thumbnail', 'accepted']
        
    def save(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        kwargs['commit'] = False
        recipe = super(AddRecipeForm, self).save(*args, **kwargs)
        recipe.author = author
        return recipe.save()

class UsesIngredientForm(forms.ModelForm):

    ingredient = AutoCompleteSelectIngredientField()
    
    class Meta:
        model = UsesIngredient

    def clean(self):
        cleaned_data = super(UsesIngredientForm, self).clean()
        ingredient = cleaned_data.get('ingredient')
        unit = cleaned_data.get('unit')

        if not CanUseUnit.objects.filter(ingredient=ingredient, unit=unit).exists():
            self._errors['unit'] = self.error_class(['Deze eenheid kan niet gebruikt worden voor het gekozen ingredient...'])
            del cleaned_data['unit']
        return cleaned_data

