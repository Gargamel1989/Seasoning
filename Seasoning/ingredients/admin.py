from django.contrib import admin
from ingredients.models import Country, Sea, Unit, Ingredient, TransportMethod,\
    Synonym, CanUseUnit, AvailableInCountry, AvailableInSea
from ingredients.fields import LastOfMonthWidget, MonthWidget
from django.db import models
from authentication.forms import ShownImageInput

class SynonymInline(admin.TabularInline):
    model = Synonym
    extra = 1

class CanUseUnitInline(admin.TabularInline):
    model = CanUseUnit
    extra = 1

class AvailableInCountryInline(admin.TabularInline):
    model = AvailableInCountry
    extra = 1
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'date_from':
            kwargs['widget'] = MonthWidget()
        elif db_field.name == 'date_until':
            kwargs['widget'] = LastOfMonthWidget()
        return super(AvailableInCountryInline, self).formfield_for_dbfield(db_field, **kwargs)
    
class AvailableInSeaInline(admin.TabularInline):
    model = AvailableInSea
    extra = 1
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'date_from':
            kwargs['widget'] = MonthWidget()
        elif db_field.name == 'date_until':
            kwargs['widget'] = LastOfMonthWidget()
        return super(AvailableInSeaInline, self).formfield_for_dbfield(db_field, **kwargs)
    
class IngredientAdmin(admin.ModelAdmin):
    inlines = [ SynonymInline,
                CanUseUnitInline,
                AvailableInCountryInline,
                AvailableInSeaInline ]
    
    formfield_overrides = {
        models.ImageField: {'widget': ShownImageInput}}
    
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Country)
admin.site.register(Sea)
admin.site.register(TransportMethod)
admin.site.register(Unit)