from django import forms
from recipes.models import Recipe, UsesIngredient
from django.forms import widgets
from recipes.fields import AutoCompleteSelectIngredientForm

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
