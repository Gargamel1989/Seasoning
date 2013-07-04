from django.test import TestCase

class RecipeViewsTestCase(TestCase):
    fixtures = ['users.json', 'ingredients.json', 'recipes.json', ]
    
    def test_view_recipe(self):
        resp = self.client.get('/recipes/1/')
        self.assertEqual(resp.status_code, 200)
        
        self.assertNumQueries(4, lambda: self.client.get('/recipes/1/'))