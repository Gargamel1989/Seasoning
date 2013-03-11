from django.db import models
import time
from imagekit.models.fields import ProcessedImageField


def get_image_filename(instance, old_filename):
    filename = str(time.time()) + '.png'
    return 'images/ingredients/' + filename

class Ingredient(models.Model):
    '''
    This is the base class for ingredients. It is not an abstract class, as simple
    Ingredients can be represented by it. This includes meat, which is not 
    dependent on time and has no special attributes
    '''
    
    CATEGORIES = ((u'GO',u'Groenten'),
                     (u'FR',u'Fruit'),
                     (u'KN',u'Knollen'),
                     (u'NZ',u'Noten en Zaden'),
                     (u'GA',u'Graanproducten'),
                     (u'KR',u'Kruiden'),
                     (u'SP',u'Specerijen'),
                     (u'OA',u'Olies en Azijnen'),
                     (u'VL',u'Vlees'),
                     (u'VI',u'Vis'),
                     (u'ZU',u'Zuivelproducten'),
                     (u'DR',u'Dranken'))
    VEGANISMS = ((u'VN',u'Veganistisch'),
                 (u'VG',u'Vegetarisch'),
                 (u'NV',u'Niet-Vegetarisch'))
    
    type = models.CharField(10)
    
    category = models.CharField(max_length=2, choices=CATEGORIES)
    veganism = models.CharField(max_length=2, choices=VEGANISMS)
    
    description = models.TextField()
    conservation_tip = models.TextField()
    preperation_tip = models.TextField()
    properties = models.TextField()
    source = models.TextField()
    
    base_footprint = models.FloatField()
    
    image = ProcessedImageField(format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    
    accepted = models.BooleanField(default=False)

class Synonym(models.Model):
    
    name = models.CharField(max_length=50, unique=True)
    plural_name = models.CharField(max_length=50, unique=True)
    
    ingredient = models.ForeignKey(Ingredient)
    
class Unit(models.Model):
    
    name = models.CharField(max_length=30, unique=True)
    short_name = models.CharField(max_length=10)
    
class CanUseUnit(models.Model):
    ingredient = models.ForeignKey(Ingredient)
    unit = models.ForeignKey(Unit)
    
    conversion_factor = models.FloatField()



class VegetalIngredient(models.Model):
    '''
    This class represents vegetal ingredients. Their sustainability factor depends
    on the current date and thus they require a more complicated model.
    These ingredients are available in certain countries during certain time periods.
    Each country uses a certain transportation method to get the ingredient to belgium,
    and is a certain distance from Belgium.
    '''
    
    ingredient = models.ForeignKey(Ingredient, primary_key=True)
    preservability = models.PositiveIntegerField()
    preservation_footprint = models.FloatField()

class Country(models.Model):
    '''
    This class represent countries. Each country is a certain distance away from Belgium
    '''
    
    name = models.CharField(max_length=50)
    distance = models.PositiveIntegerField()
    
class TransportMethod(models.Model):
    '''
    This class represents a transport method. A transport method has a mean carbon emission
    per km
    '''
    name = models.CharField(max_length=30)
    emission_per_km = models.FloatField()

class AvailableInCountry(models.Model):
    
    ingredient = models.ForeignKey(VegetalIngredient)
    country = models.ForeignKey(Country)
    transport_method = models.ForeignKey(TransportMethod)
    
    date_from = models.DateField()
    date_until = models.DateField()
    


class FishIngredient(models.Model):
    '''
    This class represents Fish ingredients.
    '''
    
    ingredient = models.ForeignKey(Ingredient, primary_key=True)
    
class Sea(models.Model):
    
    name = models.CharField(max_length=30)
    distance = models.PositiveIntegerField()

class AvailableInSea(models.Model):
    
    ingredient = models.ForeignKey(VegetalIngredient)
    sea = models.ForeignKey(Sea)
    transport_method = models.ForeignKey(TransportMethod)
    
    date_from = models.DateField()
    date_until = models.DateField()

