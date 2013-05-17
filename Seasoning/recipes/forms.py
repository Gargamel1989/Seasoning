from django import forms

class AddRecipeForm(forms.Form):
    
    name = forms.CharField(max_length=100)
    
    course = forms.ChoiceField(choices=recipe.models.COURSES)
    cuisine = forms.ChoiceField(choices=recipe.models.Cuisine.objects.all())
    
    description = forms.CharField(widget=forms.TextArea)
    portions = forms.IntegerField()

    active_time = forms.IntegerField()
    passive_time = forms.IntegerField()

    extra_info = models.CharField(widget=forms.TextArea)
    instructions = models.CharField(widget=forms.TextArea)
    
    image = forms.ImageField()
