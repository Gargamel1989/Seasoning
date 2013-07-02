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
import os, time
from django.db import models
from authentication.models import User
from imagekit.models.fields import ProcessedImageField, ImageSpecField
from imagekit.processors.resize import ResizeToFit, AddBorder
import ingredients
from ingredients.models import AvailableInCountry, AvailableInSea, CanUseUnit,\
    Ingredient
import datetime
from django.db.models import Q
from django.core.validators import MaxValueValidator
from django.db.models.fields import FloatField
from django.core.exceptions import ValidationError

class RecipeManager(models.Manager):
    
    def get_everything(self, recipe_id):
        recipe = self.select_related().get(pk=recipe_id)
        return recipe
    
    # Get everything used by the recipe
    # Returns a list of UsesIngredient and UsesRecipe objects!
    def get_ingredients(self, recipe):
        ingredients = self.get_ingredient_ingredients(recipe)
        ingredients_list = list(ingredients)
        ingredients_list = sorted(ingredients_list, key=lambda ingredient: ingredient.group + ingredient.ingredient.name)
        return ingredients_list
    
    # Get all the ingredients used by the recipe
    # Returns a list of UsesIngredient objects!
    def get_ingredient_ingredients(self, recipe):
        uses = UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe)
        ings = {}
        # Build a dictionary of ingredients, mapping ids to the ingredient objects
        for use in uses:
            ings[use.ingredient.pk] = use.ingredient, use
            
        # Query database for available_in objects of the found ingredients that are available now
        current_month = datetime.date.today().month
        date_filter = (Q(date_from__lte=datetime.date(2000, current_month, 1)) & Q(date_until__gte=datetime.date(2000, current_month, 1)))
        avails_in_c = AvailableInCountry.objects.select_related('country', 'transport_method').filter(date_filter, ingredient__in=ings.keys())
        avails_in_s = AvailableInSea.objects.select_related('sea', 'transport_method').filter(ingredient__in=ings.keys())
        
        # Map available_in objects to their ingredients
        for avail in avails_in_c:
            ingredient = ings[avail.ingredient_id][0]
            avail.ingredient = ingredient
            if hasattr(ingredient, 'available_ins'):
                ingredient.available_ins.append(avail)
            else:
                ingredient.available_ins = [avail]
        
        for avail in avails_in_s:
            ingredient = ings[avail.ingredient_id][0]
            avail.ingredient = ingredient
            if hasattr(ingredient, 'available_ins'):
                ingredient.available_ins.append(avail)
            else:
                ingredient.available_ins = [avail]
        
        # Query the can_use_unit informations of all ingredients
        units = CanUseUnit.objects.raw('SELECT * FROM canuseunit JOIN usesingredient ON canuseunit.ingredient = usesingredient.ingredient WHERE usesingredient.recipe = %s', [recipe.id])
        
        # Each unit in this list corresponds to an ingredient
        for unit in units:
            ingredient, use = ings[unit.ingredient_id]
            if ingredient.type == 'VE' or ingredient.type == 'FI':
                ingredient.available_ins = sorted(ingredient.available_ins, key=lambda avail: avail.total_footprint())
                unweighted_footprint = ingredient.available_ins[0].total_footprint()
            else:
                unweighted_footprint = ingredient.base_footprint
            ingredient.unit_footprint = unweighted_footprint * unit.conversion_factor
            ingredient.total_footprint = ingredient.unit_footprint * use.amount
            
        return uses

def get_image_filename(instance, old_filename):
    extension = os.path.splitext(old_filename)[1]
    filename = str(time.time()) + extension
    return 'images/recipes/' + filename

class Cuisine(models.Model):
    
    class Meta:
        db_table = 'cuisine'
    
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Recipe(models.Model):
    
    objects = RecipeManager()
    
    class Meta:
        db_table = 'recipe'
    
    ENTRY, BREAD, BREAKFAST, DESERT, DRINK, MAIN_COURSE, SALAD, SIDE_DISH, SOUP, MARINADE_AND_SAUCE = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    COURSES = ((ENTRY,u'Voorgerecht'),
               (BREAD,u'Brood'),
               (BREAKFAST,u'Ontbijt'),
               (DESERT,u'Dessert'),
               (DRINK,u'Drank'),
               (MAIN_COURSE,u'Hoofdgerecht'),
               (SALAD,u'Salade'),
               (SIDE_DISH,u'Bijgerecht'),
               (SOUP,u'Soep'),
               (MARINADE_AND_SAUCE,u'Marinades en Sauzen'))
    
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, editable=False)
    time_added = models.DateTimeField(auto_now_add=True, editable=False)
    
    course = models.PositiveSmallIntegerField(choices=COURSES)
    cuisine = models.ForeignKey(Cuisine, db_column='cuisine')
    description = models.TextField()
    portions = models.PositiveIntegerField()
    active_time = models.IntegerField()
    passive_time = models.IntegerField()
    
    rating = models.FloatField(null=True, blank=True, default=None, editable=False)
    number_of_votes = models.PositiveIntegerField(default=0, editable=False)
    
    ingredients = models.ManyToManyField(ingredients.models.Ingredient, through='UsesIngredient', editable=False)
    extra_info = models.TextField(default='')
    instructions = models.TextField()
    
    image = ProcessedImageField(format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    thumbnail = ImageSpecField([ResizeToFit(250, 250), AddBorder(2, 'Black')], image_field='image', format='PNG')
    
    # Derived Parameters
    footprint = FloatField(null=True, editable=False)
    veganism = models.CharField(max_length=2L, choices=Ingredient.VEGANISMS, editable=False)
    
    accepted = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Calculate and set the recipes footprint
        self.footprint = 0
        # And find an set the recipes veganism
        veganism = Ingredient.VEGAN
        for uses in self.uses.all():
            used_unit = uses.unit
            used_ingredient = uses.ingredient
            useable_units = uses.ingredient.useable_units
            primary_unit = None
            used_unit_properties = None
            for useable_unit in useable_units.all():
                if useable_unit.is_primary_unit:
                    primary_unit = useable_unit
                if used_unit.pk == useable_unit.unit.pk:
                    used_unit_properties = useable_unit
                if primary_unit and used_unit_properties:
                    break
            if not primary_unit:
                raise Exception('No primary unit found for ingredient: ' + used_ingredient.name)
            if not used_unit_properties:
                raise Exception('Unit ' + used_unit.name + ' is not useable for ingredient ' + used_ingredient.name)
            if used_ingredient.veganism < veganism:
                veganism = used_ingredient.veganism
            
            self.footprint += uses.amount * used_unit_properties.conversion_factor * used_ingredient.footprint()
        self.veganism = veganism
        super(Recipe, self).save(*args, **kwargs)
        
    def footprint_pp(self):
        return self.footprint / self.portions
    
    def vote(self, user, score):
        try:
            # Check if the user already voted on this recipe
            vote = self.votes.get(user=user)
            vote.score = score
        except Vote.DoesNotExist:
            # The given user has not voted on this recipe yet
            vote = Vote(recipe=self, user=user, score=score)
        vote.save()
    
    def unvote(self, user):
        vote = self.votes.get(user=user)
        vote.delete()
    
    def calculate_and_set_rating(self):
        new_rating = self.votes.all().aggregate(models.Avg('score'))
        self.rating = new_rating['score__avg']
        self.save()
        
    

class UsesIngredient(models.Model):
    
    class Meta:
        db_table = 'usesingredient'
    
    recipe = models.ForeignKey(Recipe, related_name='uses', db_column='recipe')
    ingredient = models.ForeignKey(ingredients.models.Ingredient, db_column='ingredient')
    
    group = models.CharField(max_length=100, blank=True)
    amount = models.FloatField(default=0)
    unit = models.ForeignKey(ingredients.models.Unit, db_column='unit')
    
    def footprint(self):
        unit_properties = CanUseUnit.objects.get(ingredient=self.ingredient, unit=self.unit)
        return (self.amount * unit_properties.conversion_factor * self.ingredient.footprint())
    
    def clean(self):
        if not self.unit in [useable_unit.unit for useable_unit in self.ingredient.useable_units.all()]:
            raise ValidationError('This unit cannot be used for measuring this Ingredient.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super(UsesIngredient, self).save(*args, **kwargs)

class Vote(models.Model):
    class Meta:
        unique_together = (("recipe", "user"),)
    
    recipe = models.ForeignKey(Recipe, related_name='votes')
    user = models.ForeignKey(User)
    score = models.PositiveIntegerField(validators=[MaxValueValidator(5)])
    date_added = models.DateTimeField(default=datetime.datetime.now, editable=False)
    date_changed = models.DateTimeField(default=datetime.datetime.now, editable=False)
    
    def save(self, *args, **kwargs):
        self.date_changed = datetime.datetime.now()
        super(Vote, self).save(*args, **kwargs)
        self.recipe.calculate_and_set_rating()
    
    def delete(self, *args, **kwargs):
        super(Vote, self).delete(*args, **kwargs)
        self.recipe.calculate_and_set_rating()
    