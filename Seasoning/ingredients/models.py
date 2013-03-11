from django.db import models


class Ingredient(models.Model):
    '''
    This is the base class for ingredients. It is not an abstract class, as simple
    Ingredients can be represented by it. This includes meat, which is not 
    dependent on time and has no special attributes
    '''
    pass

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
    
    jan, feb, mar = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    apr, may, jun = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    jul, aug, sep = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    okt, nov, dec = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    
    MONTH_FIELDS = {'Januari': 'jan', 'Februari': 'feb', 'Maart': 'mar', 'April': 'apr', 'Mei': 'may', 'Juni': 'jun',
                    'Juli': 'jul', 'Augustus': 'aug', 'September': 'sep', 'Oktober': 'okt', 'November': 'nov', 'December': 'dec'}



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
    
    jan, feb, mar = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    apr, may, jun = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    jul, aug, sep = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    okt, nov, dec = models.BooleanField(default=False), models.BooleanField(default=False), models.BooleanField(default=False)
    
    MONTH_FIELDS = {'Januari': 'jan', 'Februari': 'feb', 'Maart': 'mar', 'April': 'apr', 'Mei': 'may', 'Juni': 'jun',
                    'Juli': 'jul', 'Augustus': 'aug', 'September': 'sep', 'Oktober': 'okt', 'November': 'nov', 'December': 'dec'}



