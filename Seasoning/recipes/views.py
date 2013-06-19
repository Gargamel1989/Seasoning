from django.shortcuts import render, redirect
from recipes.models import Recipe, Vote, UsesIngredient
from recipes.forms import AddRecipeForm, UsesIngredientForm, SearchRecipeForm,\
    IngredientInRecipeSearchForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.forms.models import inlineformset_factory
from django.contrib import messages
from django.db.models import Q
from ingredients.models import Ingredient
from django.forms.formsets import formset_factory

def search_recipes(request, sort_field=None):
    IngredientInRecipeFormset = formset_factory(IngredientInRecipeSearchForm, extra=2)
    if request.method == 'POST':
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
        search_form = SearchRecipeForm()
        include_ingredients_formset = IngredientInRecipeFormset(prefix='include')
        exclude_ingredients_formset = IngredientInRecipeFormset(prefix='exclude')
        recipes_list = Recipe.objects.all()
    
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
    recipe = Recipe.objects.select_related().get(pk=recipe_id)
    usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe)

    if portions:
        ratio = int(portions)/recipe.portions
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

@login_required
def edit_recipe(request, recipe_id=None):
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
        recipe_form = AddRecipeForm(request.POST, instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(request.POST, instance=recipe)
        
        if recipe_form.is_valid() and usesingredient_formset.is_valid():
            recipe_form.save(author=request.user)
            usesingredient_formset.save()
            if new:
                messages.add_message(request, messages.INFO, 'Het recept werd met succes toegevoegd aan onze databank')
            else:
                messages.add_message(request, messages.INFO, 'Het recept werd met succes aangepast')
            return redirect('/recipes/' + str(recipe.id) + '/')
    else:
        recipe_form = AddRecipeForm(instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(instance=recipe)
    
    return render(request, 'recipes/edit_recipe.html', {'new': new,
                                                        'recipe_form': recipe_form,
                                                        'usesingredient_formset': usesingredient_formset})
