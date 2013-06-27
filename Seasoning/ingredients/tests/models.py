from django.test import TestCase
from ingredients.models import Unit, Country, Ingredient, AvailableInCountry, TransportMethod
import datetime
from django.conf import settings
from Seasoning.ingredients.models import AvailableIn

class IngredientModelsTestCase(TestCase):
    fixtures = ['ingredients.json']
    
    def setUp(self):
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            raise Exception('Please use a MySQL Database for this test')
        TestCase.setUp(self)
        # TODO: add tests for get_smallest_available_in
        raise NotImplementedError
        
    def test_unit_model(self):
        unit = Unit.objects.get(pk=3)
        self.assertEqual(unit.short(), unit.name)
    
    def test_available_in_model(self):
        avail_in_here = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                           location=Country.objects.get(pk=1),
                                           transport_method=TransportMethod.objects.get(pk=1),
                                           extra_production_footprint=2,
                                           date_from=datetime.date.today() - datetime.timedelta(days=31),
                                           date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_here.save()
        avail_in_other = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                            location=Country.objects.get(pk=2),
                                            transport_method=TransportMethod.objects.get(pk=1),
                                            extra_production_footprint=2,
                                            date_from=datetime.date.today() - datetime.timedelta(days=31),
                                            date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_other.save()
        self.assertEqual(avail_in_here.footprint, 12)
        self.assertEqual(avail_in_other.footprint, 5012)
        
        self.assertEqual(avail_in_here.date_from.year, 2000)
        self.assertEqual(avail_in_here.date_from.month, (datetime.date.today() - datetime.timedelta(days=31)).month)
        self.assertEqual(avail_in_here.date_from.day, (datetime.date.today() - datetime.timedelta(days=31)).day)
        
        self.assertEqual(avail_in_here.date_until.year, 2000)
        self.assertEqual(avail_in_here.date_until.month, (datetime.date.today() + datetime.timedelta(days=31)).month)
        self.assertEqual(avail_in_here.date_until.day, (datetime.date.today() + datetime.timedelta(days=31)).day)
    
    def test_basic_ingredient_model(self):
        # Test normal ingredient available_ins + footprint
        basic_ing = Ingredient.objects.get(pk=2)
        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_available_ins)
        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_active_available_ins)
        self.assertEqual(basic_ing.footprint(), basic_ing.base_footprint)
        
        # Insert faulty available_in
        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=2),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in.save()
        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_available_ins)
        self.assertRaises(Ingredient.BasicIngredientException, basic_ing.get_active_available_ins)
        self.assertEqual(basic_ing.footprint(), basic_ing.base_footprint)
        
    def test_seasonal_ingredient_no_availins(self):
        """
        Test Seasonal Ingredients
        If no available in object is present, an error should be thrown
        because something is wrong
        
        """
        seasonal_ing = Ingredient.objects.get(pk=1)
        self.assertEqual(len(seasonal_ing.get_available_ins()), 0)
        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 0)
        self.assertRaises(IndexError, seasonal_ing.footprint)
        
    def test_seasonal_ingredient_no_active_availins(self):
        """
        Test Seasonal Ingredients
        If no available in object is currently active, an error should be thrown
        because something is wrong
        
        """
        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() - datetime.timedelta(days=10))
        avail_in_1.save()
        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() + datetime.timedelta(days=10),
                                      date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_2.save()
        seasonal_ing = Ingredient.objects.get(pk=1)
        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 0)
        self.assertRaises(AvailableIn.DoesNotExist, seasonal_ing.footprint)
        
    def test_seasonal_ingredient_active_availin(self):
        """
        Test Seasonal Ingredients
        Only 1 available in is active. This should be used to calculate footprint
        
        """
        # We don't want to worry about preservability in this test, so set it to 0
        seasonal_ing = Ingredient.objects.get(pk=1)
        seasonal_ing.preservability = 0
        seasonal_ing.save()
        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_1.save()
        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() - datetime.timedelta(days=10))
        avail_in_2.save()
        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 1)
        self.assertEqual(seasonal_ing.get_active_available_ins()[0].pk, avail_in_1.pk)
        self.assertEqual(seasonal_ing.footprint(), 12)
        
    def test_seasonal_ingredient_active_availin_outer_date_interval(self):
        """
        Test Seasonal Ingredients
        Only 1 available in is active with an outer date interval (date_until < date_from).
        This should be used to calculate footprint
        
        If this test fails, make sure today is not an edge date of the year (What the
        hell are you doing testing a django app during the Holiday of Parties?!?),
        because this will make the outer dates generation fail. This is a feature.
        
        """
        # We don't want to worry about preservability in this test, so set it to 0
        seasonal_ing = Ingredient.objects.get(pk=1)
        seasonal_ing.preservability = 0
        seasonal_ing.save()
        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today(),
                                      date_until=datetime.date.today() - datetime.timedelta(days=2))
        avail_in.save()
        self.assertEqual(seasonal_ing.footprint(), 12)
        
        # Test other type of outer interval
        avail_in.date_from = datetime.date.today() + 2
        avail_in.date_until = datetime.date.today()
        avail_in.save()
        self.assertEqual(seasonal_ing.footprint(), 12)
        
    def test_seasonal_ingredient_multiple_availins(self):
        """
        Test Seasonal Ingredients
        Multiple available ins are active. Make sure the one with a minimal footprint
        is used.
        
        """
        # We don't want to worry about preservability in this test, so set it to 0
        seasonal_ing = Ingredient.objects.get(pk=1)
        seasonal_ing.preservability = 0
        seasonal_ing.save()
        avail_in_1 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_1.save()
        avail_in_2 = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=0,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() + datetime.timedelta(days=31))
        avail_in_2.save()
        self.assertEqual(len(seasonal_ing.get_available_ins()), 2)
        self.assertEqual(len(seasonal_ing.get_active_available_ins()), 2)
        self.assertEqual(seasonal_ing.footprint(), 12)
        
        # Test with other available in being the lowest
        avail_in_2.location=Country.objects.get(pk=1)
        avail_in_2.save()
        self.assertEqual(seasonal_ing.footprint(), 10)
        
    def test_seasonal_ingredient_with_preservation(self):
        """
        Test Seasonal Ingredients
        Only 1 available in is active, it is currently in preservation. Make sure
        the footprint holds the preservation footprint in account.
        
        """
        seasonal_ing = Ingredient.objects.get(pk=1)
        seasonal_ing.preservability = 20
        seasonal_ing.preservation_footprint = 2
        seasonal_ing.save()
        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today() - datetime.timedelta(days=31),
                                      date_until=datetime.date.today() - datetime.timedelta(days=10))
        avail_in.save()
        # Ingredient must be preserved for 10 days
        self.assertEqual(seasonal_ing.footprint(), 12 + 2*10)
     
    def test_seasonal_ingredient_with_preservation_outer_date_interval(self):
        """
        Test Seasonal Ingredients
        Only 1 available in is active, it is currently in preservation and the available
        has an outer date interval. Make sure the footprint holds the preservation footprint in account.
        
        If this test fails, make sure today is not an edge date of the year (What the
        hell are you doing testing a django app during the Holiday of Parties?!?),
        because this will make the outer dates generation fail. This is a feature.
        
        """
        raise NotImplementedError
        seasonal_ing = Ingredient.objects.get(pk=1)
        seasonal_ing.preservability = 20
        seasonal_ing.preservation_footprint = 2
        seasonal_ing.save()
        avail_in = AvailableInCountry(ingredient=Ingredient.objects.get(pk=1),
                                      location=Country.objects.get(pk=2),
                                      transport_method=TransportMethod.objects.get(pk=1),
                                      extra_production_footprint=2,
                                      date_from=datetime.date.today(),
                                      date_until=datetime.date.today() - datetime.timedelta(days=2))
        
        