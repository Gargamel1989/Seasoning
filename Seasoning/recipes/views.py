from django.shortcuts import render, redirect
from recipes.models import Recipe, Vote
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import Http404

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