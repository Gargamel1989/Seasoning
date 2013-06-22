from django.core.management.base import BaseCommand
from recipes.models import Recipe

class Command(BaseCommand):
    def handle(self):
        """
        By invoking the save method on a recipe, it's current footprint
        is recalculated
        
        """
        for recipe in Recipe.objects.all():
            recipe.save()