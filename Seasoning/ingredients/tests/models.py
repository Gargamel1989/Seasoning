from django.test import TestCase
from ingredients.models import Ingredient, AvailableInCountry

class IngredientModelsTestCase(TestCase):
    fixtures = ['ingredients.json']
    
    def test_ingredient_model(self):
        avail_in = AvailableInCountry.objects.get(pk=2)
        # Update footprint
        avail_in.save()
        ing = Ingredient.objects.get(id=1)
        print ing.footprint()
        self.assertEqual(5001, avail_in.footprint)
        