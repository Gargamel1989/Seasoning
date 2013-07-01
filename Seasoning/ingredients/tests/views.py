from django.test import TestCase
from django.conf import settings

class IngredientsViewsTestCase(TestCase):
    fixtures = ['ingredients.json']
    
    def setUp(self):
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.mysql':
            raise Exception('Please use a MySQL Database for this test')
        TestCase.setUp(self)
        
    def test_ajax_ingredient_name_list(self):
        # get requests shouldn't be answered
        resp = self.client.get('/ingredients/ing_list/a/')
        self.assertEqual(resp.status_code, 404)
        
        resp = self.client.post('/ingredients/ing_list/a/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        # TODO: check response: 2 ingredients, right order
        raise NotImplementedError