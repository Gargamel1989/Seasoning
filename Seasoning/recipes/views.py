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
from django.shortcuts import render, redirect, get_object_or_404
from recipes.models import Recipe, Vote, UsesIngredient
from recipes.forms import AddRecipeForm, UsesIngredientForm, SearchRecipeForm,\
    IngredientInRecipeSearchForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied,\
    ValidationError
from django.contrib.auth.decorators import login_required
from django.forms.models import inlineformset_factory
from django.contrib import messages, comments
from django.db.models import Q
from ingredients.models import Ingredient
from django.forms.formsets import formset_factory
from django.contrib.comments.views.moderation import perform_delete
from general.views import home

def browse_recipes(request):
    """
    Browse through recipes
    
    """
    recipes = Recipe.objects.all()
    
    return render(request, 'recipes/browse_recipes.html', {'recipes': recipes})

def search_recipes(request, sort_field=None):
    """"
    Enables searching for recipes
    
    """
    # This is a formset for inputting ingredients to be included in the recipe search
    IngredientInRecipeFormset = formset_factory(IngredientInRecipeSearchForm, extra=2)
    
    if request.method == 'POST':
        # Process the search
        
        search_form = SearchRecipeForm(request.POST)
        include_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='include')
        exclude_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='exclude')
        if search_form.is_valid() and include_ingredients_formset.is_valid() and exclude_ingredients_formset.is_valid():
            search_string = search_form.cleaned_data['search_string']
            ven, veg, nveg = search_form.cleaned_data['ven'], search_form.cleaned_data['veg'], search_form.cleaned_data['nveg']
            course = search_form.cleaned_data['course']
            sort_field = search_form.cleaned_data['sort_order'] + search_form.cleaned_data['sort_field']
        
            recipe_name = Q(name__icontains=search_string)
            
            veg_filter = Q()
            if ven:
                veg_filter = veg_filter | Q(veganism=Ingredient.VEGAN)
            if veg:
                veg_filter = veg_filter | Q(veganism=Ingredient.VEGETARIAN)
            if nveg:
                veg_filter = veg_filter | Q(veganism=Ingredient.NON_VEGETARIAN)
            
            additional_filters = Q()
            if course:
                additional_filters = additional_filters & Q(course=course)
            
            recipes_list = Recipe.objects.filter((recipe_name) & veg_filter & additional_filters)
            
            if 'tot_time' in sort_field:
                recipes_list = recipes_list.extra(select={'tot_time': 'active_time + passive_time'})
            
            if search_form.cleaned_data['include_ingredients_operator'] == 'and':
                for ingredient_form in include_ingredients_formset:
                    if not 'name' in ingredient_form.cleaned_data:
                        continue
                    recipes_list = recipes_list.filter(ingredients__name__icontains=ingredient_form.cleaned_data['name'])
            elif search_form.cleaned_data['include_ingredients_operator'] == 'or':
                q = Q()
                for ingredient_form in include_ingredients_formset:
                    if not 'name' in ingredient_form.cleaned_data:
                        continue
                    q = q | Q(ingredients__name__icontains=ingredient_form.cleaned_data['name'])
                recipes_list = recipes_list.filter(q)
            
            for ingredient_form in exclude_ingredients_formset:
                if not 'name' in ingredient_form.cleaned_data:
                    continue
                recipes_list = recipes_list.exclude(ingredients__name__icontains=ingredient_form.cleaned_data['name'])
            
            recipes_list = recipes_list.distinct().order_by(sort_field)
            
        else:
            recipes_list = []
    else:
        # Create a new search form
        search_form = SearchRecipeForm()
        include_ingredients_formset = IngredientInRecipeFormset(prefix='include')
        exclude_ingredients_formset = IngredientInRecipeFormset(prefix='exclude')
        recipes_list = Recipe.objects.all()
    
    # Split the result by 10
    paginator = Paginator(recipes_list, 10)
    
    page = request.GET.get('page')
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
        
    return render(request, 'recipes/search_recipes.html', {'search_form': search_form,
                                                           'include_ingredients_formset': include_ingredients_formset,
                                                           'exclude_ingredients_formset': exclude_ingredients_formset,
                                                           'recipes': recipes})

def view_recipe(request, recipe_id, portions=None):
    recipe = Recipe.objects.select_related('author', 'cuisine').get(pk=recipe_id)
    usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe)

    if portions:
        ratio = float(portions)/recipe.portions
        recipe.footprint = ratio * recipe.footprint
        for uses in usess:
            uses.amount = ratio * uses.amount
        
    user_vote = None
    if request.user.is_authenticated():
        try:
            user_vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        except ObjectDoesNotExist:
            pass
    
    return render(request, 'recipes/view_recipe.html', {'recipe': recipe,
                                                        'usess': usess,
                                                        'user_vote': user_vote})


@login_required
def edit_recipe(request, recipe_id=None):
    context = {}
    if recipe_id:
        recipe = Recipe.objects.get(pk=recipe_id)
        if (not request.user == recipe.author) and not request.user.is_staff:
            raise PermissionDenied
        new = False
    else:
        recipe = Recipe()
        new = True
    
    UsesIngredientInlineFormSet = inlineformset_factory(Recipe, UsesIngredient, extra=1,
                                                        form=UsesIngredientForm)
    
    if request.method == 'POST':
        recipe_form = AddRecipeForm(request.POST, request.FILES, instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(request.POST, instance=recipe)
        
        if 'stop-submit' in request.POST or 'normal-submit' in request.POST or 'ingrequest-submit' in request.POST:
            # User pressed a valid submit button
            if 'stop-submit' in request.POST:
                # User wants to discard all progress
                return redirect(home)
            
            try: 
                if recipe_form.is_valid():
                    # Recipe form is valid
                    ok = True
                    for usesingredient_form in usesingredient_formset:
                        # Check if all uses_ingredient forms would be valid if their used ingredients would be present in
                        # the database
                        if not usesingredient_form.is_valid_before_ingrequest():
                            ok = False
                    if not ok:
                        raise ValidationError
                    # All uses_ingredient forms should be valid when ingredients are added
                    if usesingredient_formset.is_valid():
                        # No ingredients have to be added, everything is fine!
                        recipe_form.save(author=request.user)
                        usesingredient_formset.save()
                        if new:
                            messages.add_message(request, messages.INFO, 'Het recept werd met succes toegevoegd aan onze databank')
                        else:
                            messages.add_message(request, messages.INFO, 'Het recept werd met succes aangepast')
                        return redirect('/recipes/' + str(recipe.id) + '/')
                    else:
                        # Unknown ingredients were used
                        unknown_ingredients = []
                        for usesingredient_form in usesingredient_formset:
                            if not usesingredient_form.uses_existing_ingredient():
                                unknown_ingredients.append(usesingredient_form['ingredient'].value())
                        
                        if 'ingrequest-submit' in request.POST:
                            # Only when this button is pressed, should we add all the ingredients, otherwise, just show the dialog
                            # about the unknown ingredients
                            for ingredient in unknown_ingredients:
                                # FIXME: request the ingredient -> send a mail to admins with all needed information
                                pass
                        elif 'normal-submit' in request.POST:
                            context['unknown_ingredients'] = unknown_ingredients
            
            except ValidationError:
                pass
    else:
        recipe_form = AddRecipeForm(instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(instance=recipe)
    
    context['recipe_form'] = recipe_form
    context['usesingredient_formset'] = usesingredient_formset
    return render(request, 'recipes/edit_recipe.html', context)


@login_required
def vote(request, recipe_id, score):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe.vote(user=request.user, score=int(score))
    return redirect(view_recipe, recipe_id)

@login_required
def remove_vote(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe.unvote(user=request.user)

@login_required
def delete_recipe_comment(request, recipe_id, comment_id):
    comment = get_object_or_404(comments.get_model(), pk=comment_id)
    if comment.user == request.user:
        perform_delete(request, comment)
        return redirect(view_recipe, recipe_id)
    else:
        raise PermissionDenied

@login_required
def my_recipes(request):
    recipes = request.user.recipes.all()
    
    return render(request, 'recipes/my_recipes.html', {'recipes': recipes})
