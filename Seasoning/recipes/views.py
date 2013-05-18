from django.shortcuts import render, redirect
from recipes.models import Recipe, Vote, UsesIngredient, UsesRecipe
from recipes.forms import AddRecipeForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.forms.models import modelform_factory, inlineformset_factory

def search_recipes(request):
    recipes_list = Recipe.objects.all()
    paginator = Paginator(recipes_list, 10)
    
    page = request.GET.get('page')
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
        
    return render(request, 'recipes/search_recipes.html', {'recipes': recipes})

def view_recipe(request, recipe_id):
    recipe = Recipe.objects.get_everything(recipe_id=recipe_id)
    
    try:
        portions = int(request.GET.get('portions', recipe.portions))
    except ValueError:
        portions = recipe.portions
    recipe.recalculate_footprints(portions)
    
    user_vote = None
    if request.user.is_authenticated():
        try:
            user_vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        except ObjectDoesNotExist:
            pass
    
    return render(request, 'recipes/view_recipe.html', {'recipe': recipe,
                                                        'user_vote': user_vote})

@login_required
def vote(request, recipe_id, new_score):
    new_score = int(new_score)
    try:
        vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        # This user has already voted in the past
        vote.score = new_score
    except ObjectDoesNotExist:
        # This user has not voted on this recipe yet
        vote = Vote(recipe_id=recipe_id, user=request.user, score=new_score)
    vote.save()
    return redirect(view_recipe, recipe_id)

@login_required
def remove_vote(request, recipe_id):
    try:
        vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        vote.delete()
        return redirect(view_recipe, recipe_id)
    except ObjectDoesNotExist:
        raise Http404()

def edit_recipe(request, recipe_id=None):
    if recipe_id:
        recipe = Recipe.objects.get(pk=recipe_id)
        new = False
    else:
        recipe = Recipe()
        new = True
    
    UsesIngredientInlineFormSet = inlineformset_factory(Recipe, UsesIngredient, extra=1)
    
    if request.method == 'POST':
        recipe_form = AddRecipeForm(request.POST, instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(request.POST, instance=recipe)
        
        if recipe_form.is_valid():
            recipe_form.save(author=request.user)
            redirect(edit_recipe_succes, recipe, new)
    else:
        recipe_form = AddRecipeForm(instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(instance=recipe)
    
    return render(request, 'recipes/edit_recipe.html', {'new': new,
                                                        'recipe_form': recipe_form,
                                                        'usesingredient_formset': usesingredient_formset})

def edit_recipe_succes(request, recipe, new=False):
    return render(request, 'recipes/edit_recipe_succes.html', {'new': new,
                                                               'recipe': recipe})
