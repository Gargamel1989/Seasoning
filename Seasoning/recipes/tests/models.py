from django.test import TestCase
from recipes.models import Recipe, Vote, UsesIngredient
from authentication.models import User
from django.db.utils import IntegrityError
from ingredients.models import Ingredient, Unit, CanUseUnit
from django.core.exceptions import ValidationError

class RecipeModelsTestCase(TestCase):
    fixtures = ['users.json', 'ingredients.json', 'recipes.json', ]
    
    def test_vote(self):
        recipe = Recipe.objects.get(pk=1)
        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)
        
        # New votes must be added correctly
        vote1 = Vote(user=user1, recipe=recipe, score=5)
        vote1.save()
        self.assertEqual(len(recipe.votes.all()), 1)
        self.assertEqual(recipe.rating, 5)
        
        # New votes must trigger rating recalculation
        Vote(user=user2, recipe=recipe, score=4).save()
        self.assertEqual(len(recipe.votes.all()), 2)
        self.assertEqual(recipe.rating, (4 + 5)/2.0)
        
        # Deleted votes must trigger rating recalculation
        vote1.delete()
        self.assertEqual(len(recipe.votes.all()), 1)
        self.assertEqual(recipe.rating, 4)
        
        # A user cannot vote twice on the same recipe
        self.assertRaises(IntegrityError, Vote(user=user2, recipe=recipe, score=4).save)
    
    def test_uses_ingredient(self):
        recipe = Recipe.objects.get(pk=1)
        ing = Ingredient.objects.get(pk=2)
        unit = Unit.objects.get(pk=1)
        
        # Can only use useable units
        usesing = UsesIngredient(recipe=recipe, ingredient=ing, amount=10, unit=unit)
        self.assertRaises(ValidationError, usesing.save)
        
        # Footprint is calculated correctly
        unit2 = Unit.objects.get(pk=3)
        usesing.unit = unit2
        usesing.save()
        self.assertEqual(usesing.footprint(), 5)
        
        # Unit conversion ratio is applied correctly
        # 1 this_unit = 0.5 primary_unit
        CanUseUnit(ingredient=ing, unit=unit, conversion_factor=0.5, is_primary_unit=False).save()
        usesing = UsesIngredient(recipe=recipe, ingredient=ing, amount=10, unit=unit)
        usesing.save()
        self.assertEqual(usesing.footprint(), 2.5)
    
    def test_recipe(self):
        recipe = Recipe.objects.get(pk=1)
        
        # Check recipe with no ingredients
        recipe.save()
        self.assertEqual(recipe.footprint, 0)
        self.assertEqual(recipe.veganism, Ingredient.VEGAN)
        
        # Check recipe with one Vegetarian ingredient
        ing = Ingredient.objects.get(pk=2)
        unit = Unit.objects.get(pk=3)
        UsesIngredient(recipe=recipe, ingredient=ing, amount=10, unit=unit).save()
        recipe.save()
        self.assertEqual(recipe.footprint, 5)
        self.assertEqual(recipe.veganism, Ingredient.VEGETARIAN)
        
        # Check recipe with Vegetarian and non-vegetarian ingredient
        ing.pk = 3
        ing.name = ing.name + '2'
        ing.veganism = Ingredient.NON_VEGETARIAN
        ing.base_footprint = 2
        ing.save()
        CanUseUnit(ingredient=ing, unit=unit, conversion_factor=1, is_primary_unit=True).save()
        UsesIngredient(recipe=recipe, ingredient=ing, amount=10, unit=unit).save()
        recipe.save()
        self.assertEqual(recipe.footprint, 25)
        self.assertEqual(recipe.veganism, Ingredient.NON_VEGETARIAN)