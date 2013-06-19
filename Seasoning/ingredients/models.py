from django.db import models
import time
from imagekit.models.fields import ProcessedImageField
from imagekit.processors.resize import ResizeToFill
import datetime


def get_image_filename(instance, old_filename):
    filename = str(time.time()) + '.png'
    return 'images/ingredients/' + filename

class Ingredient(models.Model):
    '''
    This is the base class for ingredients. It is not an abstract class, as simple
    Ingredients can be represented by it. This includes meat, which is not 
    dependent on time and has no special attributes
    '''
    
    class Meta:
        db_table = 'ingredient'
    
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
    
    base_footprint = models.FloatField()
    
    image = ProcessedImageField(processors=[ResizeToFill(350, 350)], format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    image_source = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    
    @property
    def primary_unit(self):
        return CanUseUnit.objects.get(ingredient=self, is_primary_unit=True)
    
    def footprint(self):
        """
        Return the current (minimal available) footprint of this ingredient
        """
        if self.type == Ingredient.BASIC:
            return self.base_footprint
        elif self.type == Ingredient.SEASONAL:
            today = datetime.date.today()
            available_in_countrys = AvailableInCountry.objects.filter(ingredient=self,
                                                                      date_from__lte=datetime.date(2000, today.month, today.day),
                                                                      date_until__gte=datetime.date(2000, today.month, today.day))
            min_availinc = available_in_countrys.order_by('footprint')[0]
            return min_availinc.footprint
        elif self.type == Ingredient.SEASONAL_SEA:
            today = datetime.date.today()
            available_in_seas = AvailableInSea.objects.filter(ingredient=self,
                                                              date_from__lte=datetime.date(2000, today.month, today.day),
                                                              date_until__gte=datetime.date(2000, today.month, today.day))
            min_availins = available_in_seas.order_by('footprint')[0]
            return min_availins.footprint
        
        raise Exception('Unknown ingredient type: ' + self.type)
    
class Synonym(models.Model):
    
    class Meta:
        db_table = 'synonym'
    
    name = models.CharField(max_length=50L, unique=True)
    plural_name = models.CharField(max_length=50L, blank=True)
    
    ingredient = models.ForeignKey(Ingredient, related_name='synonym', null=True, db_column='ingredient', blank=True)
    
    
class Unit(models.Model):
    
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
    
    class Meta:
        db_table = 'canuseunit'
        
    ingredient = models.ForeignKey('Ingredient', db_column='ingredient', related_name='can_use_units')
    unit = models.ForeignKey('Unit', db_column='unit', limit_choices_to=models.Q(parent_unit__exact=None))
    
    is_primary_unit = models.BooleanField()
    
    conversion_factor = models.FloatField()
    
    def __unicode__(self):
        return self.ingredient.name + ' can use ' + self.unit.name


class VegetalIngredient(models.Model):
    '''
    This class represents vegetal ingredients. Their sustainability factor depends
    on the current date and thus they require a more complicated model.
    These ingredients are available in certain countries during certain time periods.
    Each country uses a certain transportation method to get the ingredient to belgium,
    and is a certain distance from Belgium.
    '''
    
    class Meta:
        db_table = 'vegetalingredient'
    
    ingredient = models.OneToOneField(Ingredient, primary_key=True, db_column='ingredient', related_name='vegetal_ingredient')
    preservability = models.IntegerField()
    preservation_footprint = models.FloatField(null=True)

class Country(models.Model):
    '''
    This class represent countries. Each country is a certain distance away from Belgium
    '''
    
    class Meta:
        db_table = 'country'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L)
    distance = models.IntegerField()
    
    def __unicode__(self):
        return self.name
    
class TransportMethod(models.Model):
    '''
    This class represents a transport method. A transport method has a mean carbon emission
    per km
    '''
    
    class Meta:
        db_table = 'transportmethod'
        
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20L)
    emission_per_km = models.FloatField()
    
    def __unicode__(self):
        return self.name
    
class AvailableInCountry(models.Model):

    class Meta:
        db_table = 'availableincountry'
    
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_country', db_column='ingredient')
    country = models.ForeignKey('Country', db_column='country')
    transport_method = models.ForeignKey('Transportmethod', db_column='transport_method')
    
    production_type  = models.CharField(max_length=10, blank=True)
    extra_production_footprint = models.FloatField(default=0)
    
    date_from = models.DateField()
    date_until = models.DateField()
    
    # This field will contain the amount of CO2 per primary unit of this ingredient when it
    # is available under the parameters of this object.
    footprint = models.FloatField(editable=False)
    
    def month_from(self):
        return self.date_from.strftime('%B')
    
    def month_until(self):
        return self.date_until.strftime('%B')
    
    def save(self, *args, **kwargs):
        self.footprint = self.ingredient.base_footprint + self.extra_production_footprint + self.country.distance*self.transport_method.emission_per_km
        
        models.Model.save(self, *args, **kwargs)
    


class Sea(models.Model):
    
    class Meta:
        db_table = 'Sea'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L)
    distance = models.IntegerField()
    
    def __unicode__(self):
        return self.name
    
class AvailableInSea(models.Model):
    
    class Meta:
        db_table = 'availableinsea'
    
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_sea', db_column='ingredient')
    sea = models.ForeignKey('Sea', db_column='sea')
    transport_method = models.ForeignKey('Transportmethod', db_column='transport_method')
    
    date_from = models.DateField()
    date_until = models.DateField()
    
    # This field will contain the amount of CO2 per primary unit of this ingredient when it
    # is available under the parameters of this object.
    footprint = models.FloatField(editable=False)
    
    def month_from(self):
        return self.date_from.strftime('%B')
    
    def month_until(self):
        return self.date_until.strftime('%B')
    
    def save(self, *args, **kwargs):
        self.footprint = self.ingredient.base_footprint + self.extra_production_footprint + self.sea.distance*self.transport_method.emission_per_km
        
        models.Model.save(self, *args, **kwargs)
