import os, time
from django.db import models
from authentication.models import User
from imagekit.models.fields import ProcessedImageField, ImageSpecField
from imagekit.processors.resize import ResizeToFit, AddBorder
import ingredients
import itertools


class RecipeManager(models.Manager):
    
    def get_everything(self, recipe_id):
        '''
        This method returns the recipe and all models related to it. They related models are
        put in the following fields if they exist:
            - Cuisine:           cuisine
            - UsesIngredient:    ingredients
            - UsesRecipe:        ingredients
        '''
        recipe = self.select_related().get(pk=recipe_id)
        recipe.ingredients = self.get_ingredients(recipe)
        return recipe
    
    def get_ingredients(self, recipe):
        ingredients = self.get_ingredient_ingredients(recipe)
        recipes = self.get_recipe_ingredients(recipe)
        ingredients_list = list(itertools.chain(ingredients, recipes))
        print ingredients_list
        # TODO: sort ingredients_list by group, then by category and then alphabettically
        return ingredients_list
    
    def get_recipe_ingredients(self, recipe):
        recipe_ingredients = UsesRecipe.objects.select_related('ingredient').filter(recipe=recipe)
        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient.ingredients = self.get_ingredients(recipe_ingredient)
        return recipe_ingredients
    
    def get_ingredient_ingredients(self, recipe):
        return UsesIngredient.objects.select_related('ingredient', 'unit').filter(recipe=recipe)
    
    

def get_image_filename(instance, old_filename):
    extension = os.path.splitext(old_filename)[1]
    filename = str(time.time()) + extension
    return 'images/recipes/' + filename

class Cuisine(models.Model):
    
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Recipe(models.Model):
    
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
    cuisine = models.ForeignKey(Cuisine)
    description = models.TextField()
    portions = models.IntegerField()
    active_time = models.IntegerField()
    passive_time = models.IntegerField()
    ingredients = models.ManyToManyField(ingredients.models.Ingredient, through='UsesIngredient')
    recipe_ingredients = models.ManyToManyField('self', through='UsesRecipe', symmetrical=False, related_name='r_ingredients')
    extra_info = models.TextField()
    instructions = models.TextField()
    rating = models.FloatField()
    
    image = ProcessedImageField(format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    thumbnail = ImageSpecField([ResizeToFit(250, 250), AddBorder(2, 'Black')], image_field='image', format='PNG')
    
    accepted = models.BooleanField()
    


class UsesIngredient(models.Model):
    
    recipe = models.ForeignKey(Recipe)
    ingredient = models.ForeignKey(ingredients.models.Ingredient)
    
    group = models.CharField(max_length=100, blank=True)
    amount = models.FloatField()
    unit = models.ForeignKey(ingredients.models.Unit)
    
    # TODO: Build in check that every instance of this model can only have units that the ingredient 
    # can use

class UsesRecipe(models.Model):
    
    recipe = models.ForeignKey(Recipe, related_name='recipe')
    recipe_used = models.ForeignKey(Recipe, related_name='ingredient')
    
    group = models.CharField(max_length=100, blank=True)
    portions = models.IntegerField()
    
    # Build in check that when an instance of this is saved, no circular dependencies exist