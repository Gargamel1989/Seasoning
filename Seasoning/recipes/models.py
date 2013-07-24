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
from ingredients.models import CanUseUnit, Ingredient
import datetime
from django.core.validators import MaxValueValidator
from django.db.models.fields import FloatField
from django.core.exceptions import ValidationError

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
    author = models.ForeignKey(User, related_name='recipes', editable=False, null=True)
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
        """
        Calculate the recipes footprint by adding the footprint
        of every used ingredient
        Calculate the recipes veganism by searching for the ingredient
        with the lowest veganism.
        
        """
        self.footprint = 0
        self.veganism = Ingredient.VEGAN
        
        for uses in self.uses.all():
            # Add the footprint for this used ingredient to the total
            self.footprint += uses.footprint()
            
            # Check the veganism of this ingredient
            if uses.ingredient.veganism < self.veganism:
                self.veganism = uses.ingredient.veganism
            
            # Check the state of this ingredient
            if not uses.ingredient.accepted:
                self.accepted = False
                
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

class UnknownIngredient(models.Model):
    class Meta:
        db_table = 'unknown_ingredient'
    
    name = models.CharField(max_length=50L)
    requested_by = models.ForeignKey(User)
    for_recipe = models.ForeignKey(Recipe)
    
    real_ingredient = models.ForeignKey(Ingredient)
    
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
    