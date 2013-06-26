from django.test import TestCase

class IngredientModelsTestCase(TestCase):
    fixtures = ['ingredients.json']
    
    def test_available_in_model(self):
        