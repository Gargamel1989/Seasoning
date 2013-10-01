from django.test import TestCase
import ingredients.models
from ingredients.models import Unit, Country, Ingredient, AvailableInCountry, TransportMethod, AvailableIn, CanUseUnit, AvailableInSea
import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django_dynamic_fixture import G
from ingredients.tests import test_datetime

# All calls to datetime.date.today within ingredients.models will
# return 2013-05-05 as the current date
ingredients.models.datetime = test_datetime.TestDatetime()

class UnitModelTestCase(TestCase):
    pass

class SynonymModelTestcase(TestCase):
    pass

class CountryModelTestcase(TestCase):
    pass

class SeaModelTestcase(TestCase):
    pass

class TransportMethodModelTestcase(TestCase):
    pass

class CanUseUnitModelTestcase(TestCase):
    pass

class AvailableInModelTestCase(TestCase):
        
    def test_save(self):
        ing = G(Ingredient, base_footprint=5)
        country = G(Country, distance=10)
        tpm = G(TransportMethod, emission_per_km=20)
        avail = G(AvailableInCountry, location=country, transport_method=tpm,
                  extra_production_footprint=30, ingredient=ing,
                  date_from=datetime.date(2013, 2, 2),
                  date_until=datetime.date(2013, 7, 7))
        
        self.assertEqual(avail.date_from.year, AvailableIn.BASE_YEAR)
        self.assertEqual(avail.date_until.year, AvailableIn.BASE_YEAR)
        self.assertEqual(avail.footprint, 5 + 10*20 + 30)
    
    def test_is_active(self):
        avail = G(AvailableInCountry,
                  date_from=datetime.date(2013, 2, 2),
                  date_until=datetime.date(2013, 7, 7))
        self.assertTrue(avail.is_active())
        self.assertTrue(avail.is_active(test_datetime.TestDatetime().date.today()))
        
        avail = G(AvailableInCountry, 
                  date_from=datetime.date(2013, 6, 6),
                  date_until=datetime.date(2013, 7, 7))
        self.assertFalse(avail.is_active())
        
        avail = G(AvailableInCountry, 
                  date_from=datetime.date(2013, 2, 2),
                  date_until=datetime.date(2013, 3, 3))
        self.assertFalse(avail.is_active())
        
        avail = G(AvailableInCountry, 
                  date_from=datetime.date(2013, 4, 4),
                  date_until=datetime.date(2013, 1, 1))
        self.assertTrue(avail.is_active())
        
        avail = G(AvailableInCountry, 
                  date_from=datetime.date(2013, 9, 9),
                  date_until=datetime.date(2013, 7, 7))
        self.assertTrue(avail.is_active())
        
        avail = G(AvailableInCountry, 
                  date_from=datetime.date(2013, 9, 9),
                  date_until=datetime.date(2013, 1, 1))
        self.assertFalse(avail.is_active())
    
    def test_is_active_extension(self):
        avail = G(AvailableInCountry,
                  date_from=datetime.date(2013, 2, 2),
                  date_until=datetime.date(2013, 5, 1))
        self.assertTrue(avail.is_active(date_until_extension=4))
        self.assertTrue(avail.is_active(date_until_extension=40))
        self.assertTrue(avail.is_active(date_until_extension=400))
        
        avail = G(AvailableInCountry,
                  date_from=datetime.date(2013, 12, 10),
                  date_until=datetime.date(2013, 12, 15))
        self.assertTrue(avail.is_active(date_until_extension=200))
        self.assertTrue(avail.is_active(date_until_extension=400))
        
        avail = G(AvailableInCountry,
                  date_from=datetime.date(2013, 12, 10),
                  date_until=datetime.date(2013, 5, 1))
        self.assertTrue(avail.is_active(date_until_extension=4))
        self.assertTrue(avail.is_active(date_until_extension=40))
        self.assertTrue(avail.is_active(date_until_extension=400))

class IngredientModelTestCase(TestCase):
    
    def setUp(self):
        # Units
        unit = G(Unit)
        G(Unit, parent_unit=unit)
    
    def test_primary_unit(self):
        ing = G(Ingredient)
        self.assertEqual(ing.primary_unit, None)
        
        G(CanUseUnit, ingredient=ing)
        self.assertEqual(ing.primary_unit, None)
        
        pu = G(CanUseUnit, ingredient=ing, is_primary_unit=True).unit
        self.assertEqual(ing.primary_unit, pu)
    
    def test_can_use_unit(self):
        punit = G(Unit) # More like G(Unot) amirite?
        unit = G(Unit, parent_unit=punit)
        ing = G(Ingredient)
        self.assertFalse(ing.can_use_unit(punit))
        
        G(CanUseUnit, ingredient=ing, unit=punit)
        self.assertTrue(ing.can_use_unit(punit))
        self.assertTrue(ing.can_use_unit(unit))
        
    def test_get_available_ins(self):
        bing = G(Ingredient, type=Ingredient.BASIC)
        
        sing = G(Ingredient, type=Ingredient.SEASONAL)
        self.assertEqual(len(sing.get_available_ins()), 0)
        
        G(AvailableInCountry, ingredient=sing)
        G(AvailableInCountry, ingredient=sing)
        
        ssing = G(Ingredient, type=Ingredient.SEASONAL_SEA)
        self.assertEqual(len(ssing.get_available_ins()), 0)
        
        G(AvailableInSea, ingredient=ssing)
        G(AvailableInSea, ingredient=ssing)
        G(AvailableInSea, ingredient=ssing)
        
        self.assertRaises(Ingredient.BasicIngredientException, bing.get_available_ins)
        self.assertEqual(len(sing.get_available_ins()), 2)
        self.assertEqual(len(ssing.get_available_ins()), 3)
        
    def test_get_active_available_ins(self):
        ing = G(Ingredient, type=Ingredient.SEASONAL, preservability=0)
        self.assertEqual(len(ing.get_active_available_ins()), 0)
                
        G(AvailableInCountry, ingredient=ing,
          date_from=datetime.date(2013, 2, 2),
          date_until=datetime.date(2013, 3, 3))
        self.assertEqual(len(ing.get_active_available_ins()), 0)
                
        G(AvailableInCountry, ingredient=ing,
          date_from=datetime.date(2013, 2, 2),
          date_until=datetime.date(2013, 7, 7))
        self.assertEqual(len(ing.get_active_available_ins()), 1)
    
    def test_get_available_in_with_smallest_footprint(self):
        ing = G(Ingredient, type=Ingredient.SEASONAL, preservability=50,
                base_footprint=5, preservation_footprint=10)
        country = G(Country, distance=10)
        tpm = G(TransportMethod, emission_per_km=20)
        avail1 = G(AvailableInCountry, ingredient=ing, location=country,
                   transport_method=tpm, extra_production_footprint=500,
                   date_from=datetime.date(2013, 2, 2),
                   date_until=datetime.date(2013, 7, 7))
        self.assertEqual(ing.get_available_in_with_smallest_footprint(), avail1)
        
        G(AvailableInCountry, ingredient=ing, location=country,
          transport_method=tpm, extra_production_footprint=501,
          date_from=datetime.date(2013, 2, 2),
          date_until=datetime.date(2013, 7, 7))
        self.assertEqual(ing.get_available_in_with_smallest_footprint(), avail1)
        
        avail2 = G(AvailableInCountry, ingredient=ing, location=country,
                   transport_method=tpm, extra_production_footprint=499,
                   date_from=datetime.date(2013, 2, 2),
                   date_until=datetime.date(2013, 7, 7))
        self.assertEqual(ing.get_available_in_with_smallest_footprint(), avail2)
        
        # preservation footprint makes it higher than previous
        G(AvailableInCountry, ingredient=ing, location=country,
          transport_method=tpm, extra_production_footprint=499,
          date_from=datetime.date(2013, 2, 2),
          date_until=datetime.date(2013, 4, 4))
        self.assertEqual(ing.get_available_in_with_smallest_footprint(), avail2)
        
        # preservation footprint makes it higher, but reduced extra_production_footprint
        # makes it lower than avail2
        avail3 = G(AvailableInCountry, ingredient=ing, location=country,
                   transport_method=tpm, extra_production_footprint=100,
                   date_from=datetime.date(2013, 2, 2),
                   date_until=datetime.date(2013, 4, 4))
        self.assertEqual(ing.get_available_in_with_smallest_footprint(), avail3)
        
    def test_always_available(self):
        ing = G(Ingredient, type=Ingredient.SEASONAL, preservability=50)
        self.assertFalse(ing.always_available())
        
        G(AvailableInCountry, ingredient=ing,
          date_from=datetime.date(2013, 2, 2),
          date_until=datetime.date(2013, 10, 2))
        self.assertFalse(ing.always_available())
        
        G(AvailableInCountry, ingredient=ing,
          date_from=datetime.date(2013, 10, 3),
          date_until=datetime.date(2013, 2, 1))
        self.assertTrue(ing.always_available())
    
    def test_footprint(self):
        bing = G(Ingredient, type=Ingredient.BASIC)
        self.assertEqual(bing.footprint(), bing.base_footprint)
        
        sing = G(Ingredient, type=Ingredient.SEASONAL, preservability=200,
                 preservation_footprint=10)
        country = G(Country, distance=10)
        tpm = G(TransportMethod, emission_per_km=20)
        avail1 = G(AvailableInCountry, ingredient=sing, location=country,
                   transport_method=tpm, extra_production_footprint=5000,
                   date_from=datetime.date(2013, 2, 2),
                   date_until=datetime.date(2013, 7, 7))        
        self.assertEqual(sing.footprint(), avail1.footprint)
        
#        avail2 = G(AvailableInCountry, ingredient=sing, location=country,
#                   transport_method=tpm, extra_production_footprint=0,
#                   date_from=datetime.date(2013, 7, 1),
#                   date_until=datetime.date(2013, 12, 1))
#        self.assertEqual(sing.footprint(), avail2.footprint + 156*sing.preservation_footprint)
        
        avail3 = G(AvailableInCountry, ingredient=sing, location=country,
                   transport_method=tpm, extra_production_footprint=100,
                   date_from=datetime.date(2013, 2, 2),
                   date_until=datetime.date(2013, 5, 1))
        self.assertEqual(sing.footprint(), avail3.footprint + 4*sing.preservation_footprint)
        
    
    def test_save(self):
        bing = G(Ingredient, type=Ingredient.BASIC, preservability=10,
                 preservation_footprint=100)
        self.assertEqual(bing.preservability, 0)
        self.assertEqual(bing.preservation_footprint, 0)
    
        
    

#class IngredientModelsTestCase(TestCase):
#    fixtures = ['ingredients.json']
#    
#    def setUp(self):
##        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.mysql':
##            raise Exception('Please use a MySQL Database for this test')
#        TestCase.setUp(self)
#        
#    def test_unit_model(self):
#        unit = Unit.objects.get(pk=3)
#        self.assertEqual(unit.short(), unit.name)
#    
#    def test_available_in_model(self):
#        avail_in_here = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                           location=Country.objects.get(pk=1),
#                                           transport_method=TransportMethod.objects.get(pk=1),
#                                           extra_production_footprint=2,
#                                           date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                           date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in_here.save()
#        avail_in_other = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                            location=Country.objects.get(pk=2),
#                                            transport_method=TransportMethod.objects.get(pk=1),
#                                            extra_production_footprint=2,
#                                            date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                            date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in_other.save()
#        self.assertEqual(avail_in_here.footprint, 12)
#        self.assertEqual(avail_in_other.footprint, 5012)
#        
#        self.assertEqual(avail_in_here.date_from.year, 2000)
#        self.assertEqual(avail_in_here.date_from.month, (datetime.date.today() - datetime.timedelta(days=1)).month)
#        self.assertEqual(avail_in_here.date_from.day, (datetime.date.today() - datetime.timedelta(days=1)).day)
#        
#        self.assertEqual(avail_in_here.date_until.year, 2000)
#        self.assertEqual(avail_in_here.date_until.month, (datetime.date.today() + datetime.timedelta(days=1)).month)
#        self.assertEqual(avail_in_here.date_until.day, (datetime.date.today() + datetime.timedelta(days=1)).day)
#    
#    def test_basic_ingredient_model(self):
#        # Test normal ingredient available_ins + footprint
#        basic_ing = Ingredient.objects.get(pk=2)
#        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_available_ins)
#        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_active_available_ins)
#        self.assertEqual(basic_ing.footprint(), basic_ing.base_footprint)
#        
#        # Insert faulty available_in
#        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=2),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in.save()
#        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_available_ins)
#        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_active_available_ins)
#        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_available_in_with_smallest_footprint)
#        self.assertEqual(basic_ing.base_footprint, basic_ing.footprint())
#        
#    def test_seasonal_ingredient_no_availins(self):
#        """
#        Test Seasonal Ingredients
#        If no available in object is present, an error should be thrown
#        because something is wrong
#        
#        """
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        self.assertEqual(len(seasonal_ing.get_available_ins()), 0)
#        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 0)
#        self.assertRaises(ObjectDoesNotExist, seasonal_ing.get_available_in_with_smallest_footprint)
#        self.assertRaises(ObjectDoesNotExist, seasonal_ing.footprint)
#        
#    def test_seasonal_ingredient_no_active_availins(self):
#        """
#        Test Seasonal Ingredients
#        If no available in object is currently active, an error should be thrown
#        because something is wrong
#        
#        """
#        # We don't want to worry about preservability in this test, so set it to 0
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 0
#        seasonal_ing.save()
#        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=2),
#                                      date_until=datetime.date.today() - datetime.timedelta(days=1))
#        avail_in_1.save()
#        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() + datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() + datetime.timedelta(days=2))
#        avail_in_2.save()
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
#        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 0)
#        self.assertRaises(ObjectDoesNotExist, seasonal_ing.get_available_in_with_smallest_footprint)
#        self.assertRaises(ObjectDoesNotExist, seasonal_ing.footprint)
#        
#    def test_seasonal_ingredient_active_availin(self):
#        """
#        Test Seasonal Ingredients
#        Only 1 available in is active. This should be used to calculate footprint
#        
#        """
#        # We don't want to worry about preservability in this test, so set it to 0
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 0
#        seasonal_ing.save()
#        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in_1.save()
#        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=2),
#                                      date_until=datetime.date.today() - datetime.timedelta(days=1))
#        avail_in_2.save()
#        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
#        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 1)
#        self.assertEqual(seasonal_ing.get_active_available_ins()[0].pk, avail_in_1.pk)
#        self.assertEqual(seasonal_ing.get_available_in_with_smallest_footprint().pk, avail_in_1.pk)
#        self.assertEqual(seasonal_ing.footprint(), 5012)
#        
#    def test_seasonal_ingredient_active_availin_outer_date_interval(self):
#        """
#        Test Seasonal Ingredients
#        Only 1 available in is active with an outer date interval (date_until < date_from).
#        This should be used to calculate footprint
#        
#        If this test fails, make sure today is not an edge date of the year (What the
#        hell are you doing testing a django app during the Holidays?!?),
#        because this will make the outer dates generation fail. This is a feature.
#        
#        """
#        # We don't want to worry about preservability in this test, so set it to 0
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 0
#        seasonal_ing.save()
#        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today(),
#                                      date_until=datetime.date.today() - datetime.timedelta(days=2))
#        avail_in.save()
#        self.assertEqual(seasonal_ing.footprint(), 5012)
#        
#        # Test other type of outer interval
#        avail_in.date_from = datetime.date.today() + datetime.timedelta(days=2)
#        avail_in.date_until = datetime.date.today()
#        avail_in.save()
#        self.assertEqual(seasonal_ing.get_available_in_with_smallest_footprint().pk, avail_in.pk)
#        self.assertEqual(seasonal_ing.footprint(), 5012)
#        
#    def test_seasonal_ingredient_multiple_availins(self):
#        """
#        Test Seasonal Ingredients
#        Multiple available ins are active. Make sure the one with a minimal footprint
#        is used.
#        
#        """
#        # We don't want to worry about preservability in this test, so set it to 0
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 0
#        seasonal_ing.save()
#        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=1),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in_1.save()
#        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=0,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() + datetime.timedelta(days=1))
#        avail_in_2.save()
#        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
#        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 2)
#        self.assertEqual(seasonal_ing.get_available_in_with_smallest_footprint().pk, avail_in_2.pk)
#        self.assertEqual(seasonal_ing.footprint(), 5010)
#        
#        # Test with other available in being the lowest
#        avail_in_1.location=Country.objects.get(pk=1)
#        avail_in_1.save()
#        self.assertEqual(seasonal_ing.get_available_in_with_smallest_footprint().pk, avail_in_1.pk)
#        self.assertEqual(seasonal_ing.footprint(), 12)
#        
#    def test_seasonal_ingredient_with_preservation(self):
#        """
#        Test Seasonal Ingredients
#        Only 1 available in is active, it is currently in preservation. Make sure
#        the footprint holds the preservation footprint in account.
#        
#        """
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 20
#        seasonal_ing.preservation_footprint = 2
#        seasonal_ing.save()
#        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() - datetime.timedelta(days=2),
#                                      date_until=datetime.date.today() - datetime.timedelta(days=1))
#        avail_in.save()
#        # Ingredient must be preserved for 10 days
#        self.assertEqual(seasonal_ing.footprint(), 5012 + 2*1)
#     
#    def test_seasonal_ingredient_with_preservation_outer_date_interval(self):
#        """
#        Test Seasonal Ingredients
#        Only 1 available in is active, it is currently in preservation and the available
#        has an outer date interval. Make sure the footprint holds the preservation footprint in account.
#        
#        If this test fails, make sure today is not an edge date of the year (What the
#        hell are you doing testing a django app during the Holidays?!?),
#        because this will make the outer dates generation fail. This is a feature.
#        
#        """
#        seasonal_ing = Ingredient.objects.get(pk=1)
#        seasonal_ing.preservability = 0
#        seasonal_ing.preservation_footprint = 2
#        seasonal_ing.save()
#        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
#                                      location=Country.objects.get(pk=2),
#                                      transport_method=TransportMethod.objects.get(pk=1),
#                                      extra_production_footprint=2,
#                                      date_from=datetime.date.today() + datetime.timedelta(days=1),
#                                      date_until=datetime.date.today() - datetime.timedelta(days=1))
#        avail_in.save()
#        self.assertRaises(ObjectDoesNotExist, seasonal_ing.footprint)
#        seasonal_ing.preservability = 1
#        seasonal_ing.save()
#        self.assertEqual(seasonal_ing.footprint(), 5012 + 2*1)
#        # preservability overlaps to inner interval
#        seasonal_ing.preservability = 20
#        seasonal_ing.save()
#        self.assertEqual(seasonal_ing.footprint(), 5012 + 2*1)
        
        
        
