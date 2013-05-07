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
from django.core.validators import MaxValueValidator


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
        recipe_ingredients = UsesRecipe.objects.select_related('recipe_used').filter(recipe=recipe)
        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient.recipe_used.ingredients = self.get_ingredients(recipe_ingredient)
        return recipe_ingredients
    
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
    
    rating = models.FloatField(null=True, blank=True, default=None)
    number_of_votes = models.PositiveIntegerField(default=0)
    
    ingredient_ingredients = models.ManyToManyField(ingredients.models.Ingredient, through='UsesIngredient')
    recipe_ingredients = models.ManyToManyField('self', through='UsesRecipe', symmetrical=False, related_name='r_ingredients')
    extra_info = models.TextField(default='')
    instructions = models.TextField()
    
    image = ProcessedImageField(format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    thumbnail = ImageSpecField([ResizeToFit(250, 250), AddBorder(2, 'Black')], image_field='image', format='PNG')
    
    accepted = models.BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        super(Recipe, self).__init__(*args, **kwargs)
        self._current_portions = self.portions
        self._total_footprint_cache = None
    
    # Make sure the 'ingredient' property is set! This should be a list containing all usesIngredients and usesRecipes
    # of the recipe (including the recipes)
    @property
    def total_footprint(self):
        if not self._total_footprint_cache:
            total_footprint = 0
            for uses in self.ingredients:
                total_footprint += uses.ingredient.total_footprint
            self._total_footprint_cache = total_footprint
            return total_footprint
        return self._total_footprint_cache
    
    def total_footprint_pp(self):
        return self.total_footprint / self.current_portions
    
    @property
    def current_portions(self):
        return self._current_portions
    
    @current_portions.setter
    def current_portions(self, value):
        self._current_portions = value
        self._total_footprint_cache = None
    
    # Make sure the 'ingredient' property is set! This should be a list containing all usesIngredients and usesRecipes
    # of the recipe (including the recipes)
    def recalculate_footprints(self, portions):
        if self.current_portions == portions:
            return
        for uses in self.ingredients:
            if isinstance(uses, UsesIngredient):
                uses.ingredient.total_footprint = uses.ingredient.total_footprint * portions / self.portions
                uses.amount = uses.amount * portions / self.portions
            else:
                uses.recipe_used.recalculate_footprints(portions)
        self.current_portions = portions


class UsesIngredient(models.Model):
    
    class Meta:
        db_table = 'usesingredient'
    
    recipe = models.ForeignKey(Recipe, related_name='uses_ingredient', db_column='recipe')
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
    
    @property
    def ingredient(self):
        return self.recipe_used
    
    # TODO: Build in check that when an instance of this is saved, no circular dependencies exist
    

class Vote(models.Model):
    
    recipe = models.ForeignKey(Recipe)
    user = models.ForeignKey(User)
    score = models.PositiveIntegerField(validators=[MaxValueValidator(5)])
    date_added = models.DateTimeField(default=datetime.datetime.now, editable=False)
    date_changed = models.DateTimeField(default=datetime.datetime.now, editable=False)
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            # This is a new vote
            if self.recipe.rating:
                old_rating = self.recipe.rating
            else:
                old_rating = 0
            self.recipe.rating = (old_rating * self.recipe.number_of_votes) + self.score / (self.recipe.number_of_votes + 1)
            self.recipe.number_of_votes = self.recipe.number_of_votes + 1
        else:
            # This is an existing vote getting updated
            # Get the old score
            old_score = Vote.objects.get(pk=self.pk).score
            self.recipe.rating = (self.recipe.rating * self.recipe.number_of_votes) - old_score + self.score / self.recipe.number_of_votes
            self.date_changed = datetime.datetime.now()
        self.recipe.save()
        super(Vote, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.recipe.number_of_votes <= 1:
            self.recipe.rating = None
        else:
            self.recipe.rating = (self.recipe.rating * self.recipe.number_of_votes) - self.score / (self.recipe.number_of_votes - 1)
        self.recipe.number_of_votes = max(0, self.recipe.number_of_votes - 1)
        self.recipe.save()
        super(Vote, self).delete(*args, **kwargs)