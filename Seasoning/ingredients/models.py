from django.db import models
import time
from imagekit.models.fields import ProcessedImageField
from django.db.models.fields.related import OneToOneField
from imagekit.processors.resize import ResizeToFill


class IngredientManager(models.Manager):
    
    def all_info(self, pk):
        '''
        This function fetches the required ingredient, and all related models. The various
        related models are put into the following fields (if they exist):
            - VegetalIngredient:  vegetal_ingredient
            - Synonym:            synonyms
            - CanUseUnit:         units
            - AvailableInCountry: available_in_c
            - AvailableInSea:     available_in_s
        '''
        ingredient = self.select_related('vegetal_ingredient').get(pk=pk)
        ingredient.synonyms = Synonym.objects.filter(ingredient=ingredient)
        ingredient.units = CanUseUnit.objects.select_related('unit').filter(ingredient=ingredient)
        for unit in ingredient.units:
            if unit.id == ingredient.primary_unit_id:
                ingredient.primary_unit = unit
                break
            raise Exception('No Primary Unit for Ingredient: %s' % ingredient.name)
        if ingredient.type == 'Veggie':
            ingredient.available_in_c = AvailableInCountry.objects.select_related('country', 'transport_method').filter(ingredient=ingredient)
        elif ingredient.type == 'Fish':
            ingredient.available_in_s = AvailableInSea.objects.select_related('country', 'transport_method').filter(ingredient=ingredient)
        
        return ingredient
    

def get_image_filename(instance, old_filename):
    filename = str(time.time()) + '.png'
    return 'images/ingredients/' + filename

class Ingredient(models.Model):
    '''
    This is the base class for ingredients. It is not an abstract class, as simple
    Ingredients can be represented by it. This includes meat, which is not 
    dependent on time and has no special attributes
    '''
    
    objects = IngredientManager()
    
    class Meta:
        db_table = 'ingredient'
    
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
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L, unique=True)
    plural_name = models.CharField(max_length=50L, blank=True)
    type = models.CharField(max_length=10L)
    
    category = models.CharField(max_length=2L, choices=CATEGORIES)
    veganism = models.CharField(max_length=2L, choices=VEGANISMS)
    
    description = models.TextField(blank=True)
    conservation_tip = models.TextField(blank=True)
    preparation_tip = models.TextField(blank=True)
    properties = models.TextField(blank=True)
    source = models.TextField(blank=True)
    
    base_footprint = models.FloatField()
    
    primary_unit = OneToOneField('CanUseUnit', related_name='primary_unit')
    
    image = ProcessedImageField(processors=[ResizeToFill(350, 350)], format='PNG', upload_to=get_image_filename, default='images/ingredients/no_image.png')
    accepted = models.BooleanField(default=False)
    
    def normalized_footprint(self):
        '''
        This method return the current mimimal available footprint if the
        ingredient in kgCO2/self.primary_unit
        '''
        normalized_footprint = self.base_footprint
        if self.type == 'Veggie':
            try:
                avails = sorted(self.available_ins, key=lambda avail: avail.extra_footprint)
            except AttributeError:
                print 'Warning: Doing more queries than supposed to methinks'
                avails = sorted(self.available_in_country, key=lambda avail: avail.extra_footprint)
                       
            normalized_footprint += avails[0]
        elif self.type == 'Fish':
            avails = sorted(self.available_in_sea, key=lambda avail: avail.extra_footprint)
            normalized_footprint += avails[0]
        
        return normalized_footprint

class Synonym(models.Model):
    
    class Meta:
        db_table = 'synonym'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L, unique=True)
    plural_name = models.CharField(max_length=50L, blank=True)
    
    ingredient = models.ForeignKey(Ingredient, null=True, db_column='ingredient', blank=True)
    
    
class Unit(models.Model):
    
    class Meta:
        db_table = 'unit'
        
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30L, unique=True)
    short_name = models.CharField(max_length=10L, blank=True)
    
    def short(self):
        if self.short_name:
            return self.short_name
        return self.name
    
class CanUseUnit(models.Model):
    
    class Meta:
        db_table = 'canuseunit'
        
    id = models.IntegerField(primary_key=True)
    ingredient = models.ForeignKey('Ingredient', db_column='ingredient', related_name='can_use_unit')
    unit = models.ForeignKey('Unit', db_column='unit')
    
    conversion_factor = models.FloatField()


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
    
class AvailableInCountry(models.Model):
    
    class Meta:
        db_table = 'availableincountry'
    
    id = models.IntegerField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_country', db_column='ingredient')
    country = models.ForeignKey('Country', db_column='country')
    transport_method = models.ForeignKey('Transportmethod', db_column='transport_method')
    
    production_type  = models.CharField(max_length=10, blank=True)
    extra_production_footprint = models.FloatField(default=0)
    
    date_from = models.DateField()
    date_until = models.DateField()
    
    def month_from(self):
        return self.date_from.strftime('%B')
    
    def month_until(self):
        return self.date_until.strftime('%B')
    
    def extra_footprint(self):
        return self.extra_production_footprint + self.country.distance*self.transport_method.emission_per_km
    
    def total_footprint(self):
        return self.ingredient.base_footprint + self.extra_footprint()


class Sea(models.Model):
    
    class Meta:
        db_table = 'Sea'
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50L)
    distance = models.IntegerField()
    
class AvailableInSea(models.Model):
    
    class Meta:
        db_table = 'availableinsea'
    
    id = models.IntegerField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, related_name='available_in_sea', db_column='ingredient')
    sea = models.ForeignKey('Sea', db_column='sea')
    transport_method = models.ForeignKey('Transportmethod', db_column='transport_method')
    
    date_from = models.DateField()
    date_until = models.DateField()
    
    def month_from(self):
        return self.date_from.strftime('%B')
    
    def month_until(self):
        return self.date_until.strftime('%B')
    
    def extra_footprint(self):
        return self.extra_production_footprint + self.sea.distance*self.transport_method.emission_per_km
    
    def total_footprint(self):
        return self.ingredient.base_footprint + self.extra_footprint()
