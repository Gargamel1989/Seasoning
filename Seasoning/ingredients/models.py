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
from django.db import models
import time
from imagekit.models.fields import ProcessedImageField
from imagekit.processors.resize import ResizeToFill
import datetime


def get_image_filename(instance, old_filename):
    """
    Return a new unique filename for an ingredient image
    
    """
    filename = str(time.time()) + '.png'
    return 'images/ingredients/' + filename

class Ingredient(models.Model):
    """
    This is the base class for ingredients. It is not an abstract class, as simple
    Ingredients can be represented by it. This includes meat, which is not 
    dependent on time and has no special attributes
    
    """    
    class Meta:
        db_table = 'ingredient'
    
    class BasicIngredientException(Exception):
        pass
    
    # Choices
    VEGETABLES, FRUIT, TUBERS, NUTS_AND_SEEDS, CEREAL_PRODUCTS, HERBS, SPICES, OILS_AND_VINEGARS, MEAT, FISH, DAIRY_PRODUCTS, DRINKS = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
    CATEGORIES = ((VEGETABLES,u'Groenten'),
                  (FRUIT,u'Fruit'),
                  (TUBERS,u'Knollen'),
                  (NUTS_AND_SEEDS,u'Noten en Zaden'),
                  (CEREAL_PRODUCTS,u'Graanproducten'),
                  (HERBS,u'Kruiden'),
                  (SPICES,u'Specerijen'),
                  (OILS_AND_VINEGARS,u'Olies en Azijnen'),
                  (MEAT,u'Vlees'),
                  (FISH,u'Vis'),
                  (DAIRY_PRODUCTS,u'Zuivelproducten'),
                  (DRINKS,u'Dranken'))
    NON_VEGETARIAN, VEGETARIAN, VEGAN  = 0, 1, 2
    VEGANISMS = ((VEGAN,u'Veganistisch'),
                 (VEGETARIAN,u'Vegetarisch'),
                 (NON_VEGETARIAN,u'Niet-Vegetarisch'))
    BASIC, SEASONAL, SEASONAL_SEA = 0, 1, 2
    TYPES = ((BASIC, u'Basis'),
             (SEASONAL, u'Seizoensgebonden'),
             (SEASONAL_SEA,  u'Seizoensgebonden Zee'))
    
    name = models.CharField(max_length=50L, unique=True)
    plural_name = models.CharField(max_length=50L, blank=True)
    
    type = models.PositiveSmallIntegerField(choices=TYPES, default=BASIC)
    
    category = models.PositiveSmallIntegerField(choices=CATEGORIES)
    veganism = models.PositiveSmallIntegerField(choices=VEGANISMS, default=VEGAN)
    
    description = models.TextField(blank=True)
    conservation_tip = models.TextField(blank=True)
    preparation_tip = models.TextField(blank=True)
    properties = models.TextField(blank=True)
    source = models.TextField(blank=True)
    
    # Following ingredients are only used for Seasonal Ingredients
    # The amount of days an ingredient can be preserved
    preservability = models.IntegerField(default=0)
    preservation_footprint = models.FloatField(default=0)
    
    base_footprint = models.FloatField()
    
    image = ProcessedImageField(processors=[ResizeToFill(350, 350)], format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    image_source = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    
    @property
    def primary_unit(self):
        return CanUseUnit.objects.get(ingredient=self, is_primary_unit=True)
    
    def get_available_ins(self):
        """
        Returns a queryset for all the available in objects belonging to this ingredient
        
        """
        if self.type == Ingredient.BASIC:
            raise self.BasicIngredientException
        elif self.type == Ingredient.SEASONAL:
            return self.available_in_country.all()
        elif self.type == Ingredient.SEASONAL_SEA:
            return self.available_in_sea.all()
    
    def get_active_available_ins(self):
        """
        Returns a queryset of the available in objects belonging to this ingredient
        that are currently available (The current date is between the from and until
        date)
        
        The until date is extended with the preservability of the ingredient
        
        """
        extended_date_sql = 'DATE_ADD(date_until,INTERVAL ' + str(self.preservability) + ' DAY)'
        extended_until_date_added = self.get_available_ins().extra(select={'extended_date_until': extended_date_sql})
        
        today = datetime.date.today()
        before_filtered = extended_until_date_added.filter(ingredient=self,
                                                           date_from__lte=datetime.date(2000, today.month, today.day))
        return before_filtered.extra(where={'"extended_date_until" >= ' + today.strftime('2000-%m-%d')})
    
    def footprint(self):
        """
        Return the current (minimal available) footprint of this ingredient
        
        If this is a basic ingredient, the footprint is just the base_footprint of the
        object
        
        If this is a Seasonal ingredient, the footprint is the base_footprint of the
        object, plus the minimal of the currently available AvailableIn* objects.
        
        """
        # TODO: maybe move the smallest availablein searching to its own function, and
        # make this just self.get_smallest_footprint_availablein().footprint
        # Neen, want dan moet ge weer de preservation footprint erbij tellen... Iets zoeken
        # om die informatie mee in het model te krijgen
        try:
            smallest_footprint = None
            for available_in in self.get_active_available_ins():
                today_normalized = datetime.date.today().replace(year=2000)
                if today_normalized > available_in:
                    # This means this available in is currently under preservation
                    footprint = available_in.footprint + (today_normalized - available_in.date_until)*self.preservation_footprint
                else:
                    footprint = available_in.footprint
                if not footprint or smallest_footprint > footprint:
                    smallest_footprint = footprint
            return smallest_footprint
        except self.BasicIngredientException:
            return self.base_footprint
    
    def __unicode__(self):
        return self.name
    
class Synonym(models.Model):
    """
    Represents a synonym for an ingredient, these will be displayed when viewing
    ingredients, and can be searched for.
    
    """    
    class Meta:
        db_table = 'synonym'
    
    name = models.CharField(max_length=50L, unique=True)
    plural_name = models.CharField(max_length=50L, blank=True)
    
    ingredient = models.ForeignKey(Ingredient, related_name='synonym', null=True, db_column='ingredient', blank=True)
    
    def __unicode__(self):
        return self.name
    
class Unit(models.Model):
    """
    Represent a unit
    
    A unit can be dependent on a parent unit. This means that the
    ratio between these units is independent of the ingredient.
    
    If a unit does has a parent unit, it cannot be selected as a
    unit useable by any ingredient. It will, however, automatically
    be available to any ingredient that can use its parent unit
    
    A unit with a parent unit can itself not be used as a parent unit,
    to prevent infinite recursion and other nasty stuff
    
    The ratio is defined as follows:
        1 this_unit = ratio parent_unit
        
    """
    class Meta:
        db_table = 'unit'
        
    name = models.CharField(max_length=30L, unique=True)
    short_name = models.CharField(max_length=10L, blank=True)
    
    parent_unit = models.ForeignKey('self', related_name="base_unit", null=True, blank=True, limit_choices_to=models.Q(parent_unit__exact=None))
    ratio = models.FloatField(null=True, blank=True)
    
    def __unicode__(self):
        return self.name
        
    def short(self):
        if self.short_name:
            return self.short_name
        return self.name
    
class CanUseUnit(models.Model):
    """
    Relates a unit to an ingredient.
    
    The conversion factor defines how this unit relates to the ingredients primary unit in
    the following way:
        1 this_unit = conversion_factor primary_unit
    
    """    
    class Meta:
        db_table = 'canuseunit'
        
    ingredient = models.ForeignKey('Ingredient', db_column='ingredient', related_name='useable_units')
    unit = models.ForeignKey('Unit', db_column='unit', limit_choices_to=models.Q(parent_unit__exact=None))
    
    is_primary_unit = models.BooleanField()
    
    conversion_factor = models.FloatField()
    
    def __unicode__(self):
        return self.ingredient.name + ' can use ' + self.unit.name


class Country(models.Model):
    """
    This class represent countries. Each country is a certain distance away from Belgium
    
    """
    class Meta:
        db_table = 'country'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L)
    distance = models.IntegerField()
    
    def __unicode__(self):
        return self.name


class Sea(models.Model):
    """
    Same as the ``Country`` model, but for fish ingredients
    
    """    
    class Meta:
        db_table = 'Sea'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L)
    distance = models.IntegerField()
    
    def __unicode__(self):
        return self.name
    
class TransportMethod(models.Model):
    """
    This class represents a transport method. A transport method has a mean carbon emission
    per km
    
    """
    class Meta:
        db_table = 'transportmethod'
        
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20L)
    emission_per_km = models.FloatField()
    
    def __unicode__(self):
        return self.name
    
class AvailableIn(models.Model):
    """
    Seasonal ingredients are available in different parts of the world at
    different time. Their footprint depends on where they come from.
    
    This model expresses where a seasonal ingredient can come from between
    certain times of the year, how it is transported to Belgium and what the
    additional footprint is during the production in this location (eg. because of
    greenhouse production)
    
    """
    class Meta:
        abstract = True
    
    # This field must be overriden by implementing models
    location = None
    
    transport_method = models.ForeignKey('Transportmethod', db_column='transport_method')
    
    production_type  = models.CharField(max_length=10, blank=True)
    extra_production_footprint = models.FloatField(default=0)
    
    date_from = models.DateField()
    date_until = models.DateField()
    
    # This is the added footprint when an ingredient is available with this AvailableIn object,
    # it is calculated when the model is saved
    footprint = models.FloatField(editable=False)
    
    def month_from(self):
        return self.date_from.strftime('%B')
    
    def month_until(self):
        return self.date_until.strftime('%B')
    
    def save(self, *args, **kwargs):
        self.footprint = self.ingredient.base_footprint + self.extra_production_footprint + self.location.distance*self.transport_method.emission_per_km
        
        self.date_from = self.date_from.replace(year=2000)
        self.date_until = self.date_until.replace(year=2000)
        
        models.Model.save(self, *args, **kwargs)
    

    
class AvailableInCountry(AvailableIn):
    """
    An implementation of the AvailableIn model for vegetal ingredients
    
    """
    class Meta:
        db_table = 'availableincountry'
    
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_country', db_column='ingredient')
    location = models.ForeignKey('Country', db_column='country')
    
    def country(self):
        return self.location
    
class AvailableInSea(AvailableIn):
    """
    An implementation of the AvailableIn model for fish ingredients
    
    """    
    class Meta:
        db_table = 'availableinsea'
    
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_sea', db_column='ingredient')
    location = models.ForeignKey('Sea', db_column='sea')
    
    endangered = models.BooleanField()
    
    def sea(self):
        return self.location
    