"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
from django import template
import re

register = template.Library()

paths = {'RECEPTEN': ['/recipes/.*'],
         'INFORMATIE': ['/ingredients/', '/ingredients/\d*/', '/information/'],
         'ADMIN': ['/ingredients/list/', '/ingredients/add/', '/ingredients/edit/(\d*)/', 
                   '/ingredients/units/.*', '/authentication/users/'],
         'ReceptenZoeken': ['/recipes/search/'],
         'ReceptToevoegen': ['/recipes/add/'],
         'MijnRecepten': ['/accounts/recipes/'],
         'Ingredienten': ['/ingredients/'],
         'Nieuws': ['/news/'],
         'OverSeasoning': ['/about/'],
         'GebruikersAdmin': ['/authentication/users/'],
         'IngredientenAdmin': ['/ingredients/list/', '/ingredients/add/', '/ingredients/edit/(\d*)/'],
         'Units': ['/ingredients/units/.*'],
         'StaticAdmin': ['/admin/static/.*'],}

@register.simple_tag
def active(request, link_name):
    for pattern in paths[link_name]:
        if re.match('^' + pattern + '$', request.path):
            return 'active'
    return ''