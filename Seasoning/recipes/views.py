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
from django.http.response import Http404, HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

class Group:
    
    def __init__(self, name):
        self.name = name
        self.usess = []
    
    def append(self, uses):
        self.usess.append(uses)

def browse_recipes(request):
    """
    Browse or search through recipes
    
    """
    # This is a formset for inputting ingredients to be included or excluded in the recipe search
    IngredientInRecipeFormset = formset_factory(IngredientInRecipeSearchForm, extra=1)
    
    if request.method == 'POST':
        search_form = SearchRecipeForm(request.POST)
        include_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='include')
        exclude_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='exclude')
        if search_form.is_valid() and include_ingredients_formset.is_valid() and exclude_ingredients_formset.is_valid():
            data = search_form.cleaned_data
            recipes_list = Recipe.objects.query(search_string=data['search_string'], advanced_search=data['advanced_search'],
                                                sort_field=data['sort_field'], sort_order=data['sort_order'],
                                                ven=data['ven'], veg=data['veg'], nveg=data['nveg'],
                                                cuisines=data['cuisine'], courses=data['course'])
        else:
            recipes_list = []
    else:
        search_form = SearchRecipeForm()
        include_ingredients_formset = IngredientInRecipeFormset(prefix='include')
        exclude_ingredients_formset = IngredientInRecipeFormset(prefix='exclude')
        recipes_list = Recipe.objects.query()
    
    # Split the result by 12
    paginator = Paginator(recipes_list, 12)
    
    page = request.GET.get('page')
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
        
    return render(request, 'recipes/browse_recipes.html', {'search_form': search_form,
                                                           'include_ingredients_formset': include_ingredients_formset,
                                                           'exclude_ingredients_formset': exclude_ingredients_formset,
                                                           'recipes': recipes})
    

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

def view_recipe(request, recipe_id):
    
    recipe = Recipe.objects.select_related('author', 'cuisine').get(pk=recipe_id)
    usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe).order_by('group', 'ingredient__name')
    
    groups = {}
    for uses in usess:
        group_name = uses.group or None
        if not group_name in groups:
            groups[group_name] = Group(group_name)
        groups[group_name].append(uses)
    if len(groups) > 1 and None in groups:
        groups[None].name = _('Remaining Ingredients')
    
    ingredient_groups = sorted(groups.values(), key=lambda x: x.name)

    user_vote = None
    if request.user.is_authenticated():
        try:
            user_vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        except ObjectDoesNotExist:
            pass
    
    total_time = recipe.active_time + recipe.passive_time
    active_time_perc = (float(recipe.active_time) / total_time) * 100
    passive_time_perc = 100 - active_time_perc
    
    comments = Comment.objects.filter(content_type=ContentType.objects.get_for_model(Recipe), object_pk=recipe.id).select_related('user')
    
    return render(request, 'recipes/view_recipe.html', {'recipe': recipe,
                                                        'ingredient_groups': ingredient_groups,
                                                        'user_vote': user_vote,
                                                        'active_time_perc': active_time_perc,
                                                        'passive_time_perc': passive_time_perc,
                                                        'total_time': total_time,
                                                        'comments': comments})


@login_required
def edit_recipe(request, recipe_id=None):
    context = {}
    if recipe_id:
        recipe = Recipe.objects.select_related().prefetch_related('uses__unit').get(pk=recipe_id)
        if (not request.user == recipe.author_id) and not request.user.is_staff:
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
        print request.POST
        
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
                        raise ValidationError('Something went wrong...')
                    # All uses_ingredient forms should be valid when ingredients are added
                    if usesingredient_formset.is_valid():
                        # No ingredients have to be added, everything is fine!
                        recipe_form.save(author=request.user)
                        usesingredient_formset.save(commit=False)
                        recipe.save()
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
    
    context['new_recipe'] = new
    context['recipe_form'] = recipe_form
    context['usesingredient_formset'] = usesingredient_formset
    return render(request, 'recipes/edit_recipe.html', context)

@login_required
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    
    if recipe.author == request.user:
        recipe.delete()
        messages.add_message(request, messages.INFO, 'Uw recept \'' + recipe.name + '\' werd met succes uit onze databank verwijderd.')
        return redirect('home')
        
        
    raise PermissionDenied
    

"""
Ajax calls
"""

@csrf_exempt
@login_required
def vote(request):
    
    if request.is_ajax() and request.method == 'POST':
        recipe_id = request.POST.get('recipe', None)
        score = request.POST.get('score', None)
        
        if recipe_id and score:
            try:
                recipe = Recipe.objects.select_related().get(pk=recipe_id)
            except Recipe.DoesNotExist:
                raise Http404
            recipe.vote(user=request.user, score=int(score))
            data = simplejson.dumps({'new_rating': recipe.rating,
                                     'new_novotes': recipe.number_of_votes})
            return HttpResponse(data)
        
    raise PermissionDenied
    

@csrf_exempt
@login_required
def remove_vote(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe.unvote(user=request.user)

@csrf_exempt
def get_recipe_portions(request):
    
    if request.is_ajax() and request.method == 'POST':
        recipe_id = request.POST.get('recipe', None)
        portions = request.POST.get('portions', None)
        
        if recipe_id and portions:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe).order_by('group', 'ingredient__name')
            except Recipe.DoesNotExist, UsesIngredient.DoesNotExist:
                raise Http404
            
            ratio = float(portions)/recipe.portions
            new_footprint = ratio * recipe.footprint
            
            for uses in usess:
                uses.save_allowed = False
                uses.amount = ratio * uses.amount
                uses.footprint = ratio * uses.footprint
            
            groups = {}
            for uses in usess:
                group_name = uses.group or None
                if not group_name in groups:
                    groups[group_name] = Group(group_name)
                groups[group_name].append(uses)
            if len(groups) > 1 and None in groups:
                groups[None].name = _('Remaining Ingredients')
            
            ingredient_groups = sorted(groups.values(), key=lambda x: x.name)
            
            data = {'ingredient_list': render_to_string('includes/ingredient_list.html', {'ingredient_groups': ingredient_groups}),
                    'new_footprint': new_footprint}
            json_data = simplejson.dumps(data);
            
            return HttpResponse(json_data)
    
    raise PermissionDenied

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
    