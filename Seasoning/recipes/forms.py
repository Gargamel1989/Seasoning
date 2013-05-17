from django import forms
from recipes.models import Recipe

class AddRecipeForm(forms.ModelForm):
    
    class Meta:
        model = Recipe
        fields = ['name', 'course', 'cuisine',
                  'description', 'portions', 'active_time',
                  'passive_time', 'extra_info',  'instructions',
                  'image']
