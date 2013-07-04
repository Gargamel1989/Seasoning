from django.test import TestCase
from django.conf import settings
from django.utils import simplejson

class IngredientsViewsTestCase(TestCase):
    fixtures = ['ingredients.json']
    
    def setUp(self):
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.mysql':
            raise Exception('Please use a MySQL Database for this test')
        TestCase.setUp(self)
    
    def test_view_ingredient(self):
        resp = self.client.get('/ingredients/100/')
        self.assertEqual(resp.status_code, 404)
        
        resp = self.client.get('/ingredients/1/')
        self.assertEqual(resp.status_code, 200)
        
        self.assertNumQueries(4, lambda: self.client.get('/ingredients/1/'))
        
    def test_ajax_ingredient_name_list(self):
        # get requests shouldn't be answered
        resp = self.client.get('/ingredients/ing_list/a/')
        self.assertEqual(resp.status_code, 404)
        
        resp = self.client.post('/ingredients/ing_list/a/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        ings = simplejson.loads(resp.content)
        self.assertEqual(len(ings), 2)
        self.assertEqual(ings[0][0], 2)
        self.assertEqual(ings[1][0], 1)