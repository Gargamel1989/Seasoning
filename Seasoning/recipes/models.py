import os, time
from django.db import models
from authentication.models import User
from imagekit.models.fields import ProcessedImageField, ImageSpecField
from imagekit.processors.resize import ResizeToFit, AddBorder
import ingredients
import itertools
from ingredients.models import AvailableInCountry, AvailableInSea, CanUseUnit
import datetime
from django.db.models import Q


class RecipeManager(models.Manager):
    
    def get_everything(self, recipe_id):
        recipe = self.select_related().get(pk=recipe_id)
        recipe.ingredients = self.get_ingredients(recipe)
        return recipe
    
    # Get everything used by the recipe
    # Returns a list of UsesIngredient and UsesRecipe objects!
    def get_ingredients(self, recipe):
        ingredients = self.get_ingredient_ingredients(recipe)
        recipes = self.get_recipe_ingredients(recipe)
        ingredients_list = list(itertools.chain(ingredients, recipes))
        ingredients_list = sorted(ingredients_list, key=lambda ingredient: ingredient.group + ingredient.ingredient.name)
        return ingredients_list
    
    # Get all the recipes used by the recipe
    # Returns a list of UsesRecipe objects!
    def get_recipe_ingredients(self, recipe):
        recipe_ingredients = UsesRecipe.objects.select_related('ingredient').filter(recipe=recipe)
        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient.ingredients = self.get_ingredients(recipe_ingredient)
        return recipe_ingredients
    
    # Get all the ingredients used by the recipe
    # Returns a list of UsesIngredient objects!
    def get_ingredient_ingredients(self, recipe):
        uses = UsesIngredient.objects.select_related('ingredient__primary_unit__unit', 'unit').filter(recipe=recipe)
        ings = {}
        # Build a dictionary of ingredients, mapping ids to the ingredient objects
        for use in uses:
            ings[use.ingredient.pk] = use.ingredient, use
            
        # Query database for available_in objects of the found ingredients that are available now
        current_month = datetime.date.today().month
        date_filter = (Q(date_from__lte=datetime.date(2000, current_month, 1)) & Q(date_until__gte=datetime.date(2000, current_month, 1)))
        avails_in_c = AvailableInCountry.objects.select_related('country', 'transport_method').filter(date_filter, ingredient__in=ings.keys())
        avails_in_s = AvailableInSea.objects.select_related('sea', 'transport_method').filter(ingredient__in=ings.keys())
        
        # Map available_in objects to their ingredients and calculate the total_footprint of each available_in
        for avail in avails_in_c:
            ingredient = ings[avail.ingredient_id][0]
            avail.total_footprint = ingredient.base_footprint + \
                                    avail.extra_production_footprint + \
                                    avail.country.distance * avail.transport_method.emission_per_km
            if hasattr(ingredient, 'available_ins'):
                ingredient.available_ins.append(avail)
            else:
                ingredient.available_ins = [avail]
        
        for avail in avails_in_s:
            ingredient = ings[avail.ingredient_id][0]
            avail.total_footprint = ingredient.base_footprint + \
                                    avail.extra_production_footprint + \
                                    avail.sea.distance * avail.transport_method.emission_per_km
            if hasattr(ingredient, 'available_ins'):
                ingredient.available_ins.append(avail)
            else:
                ingredient.available_ins = [avail]
        
        # Query the can_use_unit informations of all ingredients
        units = CanUseUnit.objects.raw('SELECT * FROM canuseunit JOIN usesingredient ON canuseunit.ingredient = usesingredient.ingredient WHERE usesingredient.recipe = %s', [recipe.id])
        
        # Each unit in this list corresponds to an ingredient
        for unit in units:
            ingredient, use = ings[unit.ingredient_id]
            if ingredient.type == 'Veggie' or ingredient.type == 'Fish':
                ingredient.available_ins = sorted(ingredient.available_ins, key=lambda avail: avail.total_footprint)
                unweighted_footprint = ingredient.available_ins[0].total_footprint
            else:
                unweighted_footprint = ingredient.base_footprint
            ingredient.total_footprint = unweighted_footprint * use.amount * unit.conversion_factor
            
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
    
    COURSES = ((u'VO',u'Voorgerecht'),
               (u'BR',u'Brood'),
               (u'ON',u'Ontbijt'),
               (u'DE',u'Dessert'),
               (u'DR',u'Drank'),
               (u'HO',u'Hoofdgerecht'),
               (u'SA',u'Salade'),
               (u'BI',u'Bijgerecht'),
               (u'SO',u'Soep'),
               (u'MA',u'Marinades en Sauzen'))
    
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    time_added = models.DateTimeField(auto_now_add=True)
    
    course = models.CharField(max_length=2, choices=COURSES)
    cuisine = models.ForeignKey(Cuisine, db_column='cuisine')
    description = models.TextField()
    portions = models.PositiveIntegerField()
    active_time = models.IntegerField()
    passive_time = models.IntegerField()
    
    ingredient_ingredients = models.ManyToManyField(ingredients.models.Ingredient, through='UsesIngredient')
    recipe_ingredients = models.ManyToManyField('self', through='UsesRecipe', symmetrical=False, related_name='r_ingredients')
    extra_info = models.TextField(default='')
    instructions = models.TextField()
    
    image = ProcessedImageField(format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    thumbnail = ImageSpecField([ResizeToFit(250, 250), AddBorder(2, 'Black')], image_field='image', format='PNG')
    
    accepted = models.BooleanField(default=False)
    
    # Make sure the 'ingredient' property is set! This should be a list containing all usesIngredients and usesRecipes
    # of the recipe (including the recipes)
    @property
    def total_footprint(self):
        total_footprint = 0
        for uses in self.ingredients:
            total_footprint += uses.ingredient.total_footprint
        return total_footprint
    


class UsesIngredient(models.Model):
    
    class Meta:
        db_table = 'usesingredient'
    
    recipe = models.ForeignKey(Recipe, db_column='recipe')
    ingredient = models.ForeignKey(ingredients.models.Ingredient, db_column='ingredient')
    
    group = models.CharField(max_length=100, blank=True)
    amount = models.FloatField(default=0)
    unit = models.ForeignKey(ingredients.models.Unit, db_column='unit')
    
    # TODO: Build in check that every instance of this model can only have units that the ingredient 
    # can use

class UsesRecipe(models.Model):
    
    class Meta:
        db_table = 'usesrecipe'
    
    recipe = models.ForeignKey(Recipe, db_column='recipe', related_name='recipe')
    recipe_used = models.ForeignKey(Recipe, db_column='ingredient', related_name='ingredient')
    
    group = models.CharField(max_length=100, blank=True)
    portions = models.IntegerField()
    
    def ingredient(self):
        return self.recipe_used
    
    # TODO: Build in check that when an instance of this is saved, no circular dependencies exist