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
from recipes.models import Recipe, Vote, UsesIngredient, UnknownIngredient
from recipes.forms import AddRecipeForm, UsesIngredientForm, SearchRecipeForm,\
    IngredientInRecipeSearchForm, EditRecipeBasicInfoForm,\
    EditRecipeIngredientsForm, EditRecipeInstructionsForm
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
import json
from django.core.serializers.json import DjangoJSONEncoder
from recipes.forms import IngredientsFormSet
from django.core.mail import send_mail
import datetime
import ingredients
from django.db.models.aggregates import Max, Min
from django.contrib.formtools.wizard.views import SessionWizardView
from django.utils.decorators import method_decorator
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings
from django import forms
from general.forms import FormContainer

def browse_recipes(request):
    """
    Browse or search through recipes
    
    """
    # This is a formset for inputting ingredients to be included or excluded in the recipe search
    IngredientInRecipeFormset = formset_factory(IngredientInRecipeSearchForm, extra=1)
    
    if request.method == 'POST':
        search_form = SearchRecipeForm(request.POST)
        try:
            include_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='include')
            exclude_ingredients_formset = IngredientInRecipeFormset(request.POST, prefix='exclude')
            if search_form.is_valid() and include_ingredients_formset.is_valid() and exclude_ingredients_formset.is_valid():
                data = search_form.cleaned_data
                include_ingredient_names = [form.cleaned_data['name'] for form in include_ingredients_formset if 'name' in form.cleaned_data]
                exclude_ingredient_names = [form.cleaned_data['name'] for form in exclude_ingredients_formset if 'name' in form.cleaned_data]
                recipes_list = Recipe.objects.query(search_string=data['search_string'], advanced_search=data['advanced_search'],
                                                    sort_field=data['sort_field'], sort_order=data['sort_order'], ven=data['ven'], 
                                                    veg=data['veg'], nveg=data['nveg'], cuisines=data['cuisine'], courses=data['course'], 
                                                    include_ingredients_operator=data['include_ingredients_operator'],
                                                    include_ingredient_names=include_ingredient_names, exclude_ingredient_names=exclude_ingredient_names)
            else:
                recipes_list = []
        except ValidationError:
            # A simple search with only the recipe name was done (from the homepage)
            search_form.is_valid()
            if 'search_string' in search_form.cleaned_data:
                recipes_list = Recipe.objects.filter(name__icontains=search_form.cleaned_data['search_string'], accepted=True).order_by('footprint')
            else:
                recipes_list = []
            search_form = SearchRecipeForm()
            include_ingredients_formset = IngredientInRecipeFormset(prefix='include')
            exclude_ingredients_formset = IngredientInRecipeFormset(prefix='exclude')
            
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
    
    if request.method == 'POST' and request.is_ajax():
        return render(request, 'includes/recipe_summaries.html', {'recipes': recipes})
        
    return render(request, 'recipes/browse_recipes.html', {'search_form': search_form,
                                                           'include_ingredients_formset': include_ingredients_formset,
                                                           'exclude_ingredients_formset': exclude_ingredients_formset,
                                                           'recipes': recipes})

def view_recipe(request, recipe_id):
    
    recipe = Recipe.objects.select_related('author', 'cuisine').get(pk=recipe_id)
    usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe).order_by('-group', 'ingredient__name')
    
    user_vote = None
    if request.user.is_authenticated():
        try:
            user_vote = Vote.objects.get(recipe_id=recipe_id, user=request.user)
        except ObjectDoesNotExist:
            pass
    
    total_time = recipe.active_time + recipe.passive_time
    active_time_perc = (float(recipe.active_time) / total_time) * 100
    passive_time_perc = 100 - active_time_perc
    
    comments = Comment.objects.filter(content_type=ContentType.objects.get_for_model(Recipe), object_pk=recipe.id, is_removed=False, is_public=True).select_related('user')
    
    return render(request, 'recipes/view_recipe.html', {'recipe': recipe,
                                                        'usess': usess,
                                                        'user_vote': user_vote,
                                                        'active_time_perc': active_time_perc,
                                                        'passive_time_perc': passive_time_perc,
                                                        'total_time': total_time,
                                                        'comments': comments})

class EditRecipeWizard(SessionWizardView):
    
    FORMS = [('basic_info', EditRecipeBasicInfoForm),
             ('ingredients', EditRecipeIngredientsForm),
             ('instructions', EditRecipeInstructionsForm)]
    
    TEMPLATES = {'basic_info': 'recipes/edit_recipe_basic_info.html',
                 'ingredients': 'recipes/edit_recipe_ingredients.html',
                 'instructions': 'recipes/edit_recipe_instructions.html'}
    
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'tmp_recipe_imgs'))
    
    instance = None
    
    def get_form_instance(self, step):
        return self.instance

    def get_form(self, step=None, data=None, files=None):
        """
        We need to overwrite this, because otherwise 'instance' is not passed
        to the FormContainer
        
        """
        if step is None:
            step = self.steps.current
        # prepare the kwargs for the form instance.
        kwargs = self.get_form_kwargs(step)
        kwargs.update({
            'data': data,
            'files': files,
            'prefix': self.get_form_prefix(step, self.form_list[step]),
            'initial': self.get_form_initial(step),
        })
        if issubclass(self.form_list[step], forms.ModelForm) or issubclass(self.form_list[step], FormContainer):
            # If the form is based on ModelForm, add instance if available
            # and not previously set.
            kwargs.setdefault('instance', self.get_form_instance(step))
        elif issubclass(self.form_list[step], forms.models.BaseModelFormSet) or issubclass(self.form_list[step], FormContainer):
            # If the form is based on ModelFormSet, add queryset if available
            # and not previous set.
            kwargs.setdefault('queryset', self.get_form_instance(step))
        return self.form_list[step](**kwargs)
        
    def get_template_names(self):
        return self.TEMPLATES[self.steps.current]
    
    def get_context_data(self, form, **kwargs):
        context = SessionWizardView.get_context_data(self, form, **kwargs)
        # Check if we are adding a new or editing an existing recipe
        if 'recipe_id' in self.kwargs:
            context['new_recipe'] = False
        else:
            context['new_recipe'] = True
        return context
    
    # Make sure login is required for every view in this class
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if 'recipe_id' in self.kwargs:
            try:
                self.instance = Recipe.objects.select_related().prefetch_related('uses__unit').get(pk=self.kwargs['recipe_id'])
            except Recipe.DoesNotExist:
                raise Http404
            if (not self.request.user == self.instance.author_id) and not self.request.user.is_staff:
                raise PermissionDenied
        else:
            self.instance = Recipe()
        return SessionWizardView.dispatch(self, *args, **kwargs)
    
    def done(self, form_list, **kwargs):
        if not self.instance.author:
            self.instance.author = self.request.user
        # recipe has not been saved yet
        self.instance.save()
        # TODO: change image cropping to values in the form before save
        # save the usesingredient formset
        form_list[1].forms['ingredients'].save()
        # And save the recipe again to update the footprint
        recipe = Recipe.objects.select_related().prefetch_related('uses__unit').get(pk=self.instance.pk)
        recipe.save()   
        messages.add_message(self.request, messages.INFO, 'Gelukt')
        return redirect('/recipes/%d/' % self.instance.id)


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
                                                        form=UsesIngredientForm, formset=IngredientsFormSet)
    
    if request.method == 'POST' and ('stop-submit' in request.POST or 'normal-submit' in request.POST or 'ingrequest-submit' in request.POST):
        recipe_form = AddRecipeForm(request.POST, request.FILES, instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(request.POST, instance=recipe, queryset=UsesIngredient.objects.filter(recipe=recipe).order_by('group'))
        
        if 'stop-submit' in request.POST:
            # User wants to discard all progress
            return redirect(home)
        elif 'normal-submit' in request.POST or 'ingrequest-submit' in request.POST:
            # User tried to submit a new recipe
            if  recipe_form.is_valid() & usesingredient_formset.is_valid():
                if new:
                    messages.add_message(request, messages.INFO, 'Het recept werd met succes toegevoegd aan onze databank.')
                else:
                    messages.add_message(request, messages.INFO, 'Het recept werd met succes aangepast.')
                recipe_form.save(author=request.user)
                usesingredient_formset.save()
                recipe = Recipe.objects.select_related().prefetch_related('uses__unit').get(pk=recipe_form.instance.pk)
                recipe.save()
                
                return redirect('/recipes/' + str(recipe.id) + '/')
            elif not usesingredient_formset.is_valid():
                # Recipe input is fine, check if the ingredient input is fine. If this is the case,
                # the user has tried to add an unknown ingredient
                invalid_ingredient = False
                for usesingredient_form in usesingredient_formset:
                    if not usesingredient_form.is_valid_after_ingrequest():
                        invalid_ingredient = True
                        break
                if not recipe_form.is_valid() or invalid_ingredient:
                    # There was an invalid ingredient, so remove all 'unknown_ingredient' errors
                    for usesingredient_form in usesingredient_formset:
                        if 'ingredient' in usesingredient_form._errors :
                            if 'ingredient was not found' in ''.join(usesingredient_form._errors['ingredient']):
                                for i in range(len(usesingredient_form._errors['ingredient'])):
                                    if 'ingredient was not found' in usesingredient_form._errors['ingredient'][i]:
                                        del usesingredient_form._errors['ingredient'][i]
                else:
                    # All ingredient input was valid. Find the unknown ingredients
                    unknown_ingredients = []
                    for usesingredient_form in usesingredient_formset:
                        if not usesingredient_form.uses_existing_ingredient():
                            unknown_ingredients.append({'name': usesingredient_form['ingredient'].value(),
                                                        'unit': usesingredient_form.cleaned_data['unit']})
                    if 'ingrequest-submit' in request.POST:
                        # The user wants to request new ingredients
                        request_string = 'Aangevraagd door %s:\n' % request.user.email
                        for ingredient_info in unknown_ingredients:
                            request_string += 'Naam ingredient: %s\nGevraagde eenheid: %s\n\n' % (ingredient_info['name'], ingredient_info['unit'])
                            ingredient = Ingredient(name=ingredient_info['name'], category=Ingredient.DRINKS, base_footprint=0)
                            ingredient.save()
                            unknowningredient = UnknownIngredient(name=ingredient_info['name'], requested_by=request.user, real_ingredient=ingredient)
                            ingredient_info['unknown_ingredient_model'] = unknowningredient
                        # Force form revalidation
                        usesingredient_formset = UsesIngredientInlineFormSet(request.POST, instance=recipe, queryset=UsesIngredient.objects.filter(recipe=recipe).order_by('group'))
                        if usesingredient_formset.is_valid():
                            # Send mail
                            send_mail('Aanvraag voor Ingredienten', render_to_string('emails/request_ingredients_email.txt', {'user': request.user,
                                                                                                                       'request_string': request_string}), 
                                      request.user.email,
                                      ['info@seasoning.be'], fail_silently=True)
            
                            # Save recipe
                            recipe_form.save(author=request.user)
                            usesingredient_formset.save()
                            recipe = Recipe.objects.select_related().prefetch_related('uses__unit').get(pk=recipe_form.instance.pk)
                            recipe.save()
                            
                            # Save unknown ingredients
                            for ingredient_info in unknown_ingredients:
                                unknowningredient = ingredient_info['unknown_ingredient_model']
                                unknowningredient.for_recipe = recipe
                                unknowningredient.save() 
                            return redirect('/recipes/' + str(recipe.id) + '/')
                        else:
                            # Delete temp ingredients
                            for ingredient_info in unknown_ingredients:
                                ingredient = Ingredient.objects.get(name=ingredient_info['name'])
                                ingredient.delete()                                 
                            # Raise exception
                            raise Exception('Unknown error occured during ingredient validation: %s' % request.POST)
                            
                    elif 'normal-submit' in request.POST:
                        # Ask the user if he would like to request the new ingredients
                        context['unknown_ingredients'] = unknown_ingredients
    else:
        recipe_form = AddRecipeForm(instance=recipe)
        usesingredient_formset = UsesIngredientInlineFormSet(instance=recipe, queryset=UsesIngredient.objects.filter(recipe=recipe).order_by('group'))
    
    context['new_recipe'] = new
    context['recipe_form'] = recipe_form
    context['usesingredient_formset'] = usesingredient_formset
    return render(request, 'recipes/edit_recipe.html', context)

@login_required
def delete_recipe_comment(request, recipe_id, comment_id):
    comment = get_object_or_404(comments.get_model(), pk=comment_id)
    if comment.user == request.user:
        perform_delete(request, comment)
        messages.add_message(request, messages.INFO, 'Je reactie werd succesvol verwijderd.')
        return redirect(view_recipe, recipe_id)
    else:
        raise PermissionDenied
                    

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
        
        if recipe_id is not None and portions is not None and portions > 0:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                usess = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe).order_by('group', 'ingredient__name')
            except Recipe.DoesNotExist, UsesIngredient.DoesNotExist:
                raise Http404
            
            ratio = float(portions)/recipe.portions
            new_footprint = ratio * recipe.total_footprint()
            
            for uses in usess:
                uses.save_allowed = False
                uses.amount = ratio * uses.amount
                uses.footprint = ratio * uses.footprint
            
            data = {'ingredient_list': render_to_string('includes/ingredient_list.html', {'usess': usess}),
                    'new_footprint': new_footprint}
            json_data = simplejson.dumps(data)
            
            return HttpResponse(json_data)
    
    raise PermissionDenied

@csrf_exempt
def get_recipe_footprint_evolution(request):
    
    if request.is_ajax() and request.method == 'POST':
        recipe_id = request.POST.get('recipe', None)
    
        if recipe_id is not None:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                usess = UsesIngredient.objects.select_related('ingredient', 'unit__parent_unit').prefetch_related('ingredient__available_in_country', 'ingredient__available_in_sea', 'ingredient__canuseunit_set__unit__parent_unit').filter(recipe=recipe).order_by('group', 'ingredient__name')
                # One footprint per month
                footprints = [0] * 12
                dates = [datetime.date(day=1, month=month, year=ingredients.models.AvailableIn.BASE_YEAR) for month in range(1, 13)]
                for uses in usess:
                    for i in range(12):
                        footprints[i] += uses.normalized_footprint(uses.ingredient.footprint(date=dates[i]))
                footprints = [float('%.2f' % (4*footprint/recipe.portions)) for footprint in footprints]
                footprints.append(footprints[-1])
                footprints.insert(0, footprints[0])
                data = {'footprints': footprints,
                        'doy': datetime.date.today().timetuple().tm_yday}
                json_data = simplejson.dumps(data)
            
                return HttpResponse(json_data)
            except Recipe.DoesNotExist, UsesIngredient.DoesNotExist:
                raise Http404
        
    raise PermissionDenied

@csrf_exempt
def get_relative_footprint(request):
    
    if request.is_ajax() and request.method == 'POST':
        recipe_id = request.POST.get('recipe', None)
    
        if recipe_id is not None:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
                bounds = Recipe.objects.aggregate(Max('footprint'), Min('footprint'))
                min_fp = 4*bounds['footprint__min']
                max_fp = 4*bounds['footprint__max']
                interval_count = 10
                interval_length = (max_fp-min_fp)/interval_count
                recipes = Recipe.objects.values('footprint', 'course', 'veganism').all().order_by('footprint')
                
                intervals = [min_fp+i*interval_length for i in range(interval_count+1)]
                all_footprints = []
                category_footprints = []
                veganism_footprints = []
                
                footprint_index = 0
                for upper_bound in intervals[1:]:
                    # Don't check the first value in the intervals, because we only need upper bounds
                    # of intervals
                    all_footprints.append(0)
                    category_footprints.append(0)
                    veganism_footprints.append(0)
                    while 4*recipes[footprint_index]['footprint'] <= upper_bound:
                        all_footprints[-1] += 1
                        if recipe.course == recipes[footprint_index]['course']:
                            category_footprints[-1] += 1
                        if recipe.veganism == recipes[footprint_index]['veganism']:
                            veganism_footprints[-1] += 1
                        footprint_index += 1
                        if footprint_index >= len(recipes):
                            break
                data = {'all_fps': all_footprints,
                        'cat_fps': category_footprints,
                        'veg_fps': veganism_footprints,
                        'min_fp': min_fp,
                        'max_fp': max_fp,
                        'interval_length': interval_length,
                        'fp': 4*recipe.footprint}
                json_data = simplejson.dumps(data)
            
                return HttpResponse(json_data)
            
            except Recipe.DoesNotExist:
                raise Http404
        
    raise PermissionDenied