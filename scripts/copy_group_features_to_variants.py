import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from categories.models import *

category = Category.objects.get(name='Magazines')
features = Feature.objects.filter(category=category)

c_category = Category.objects.get(name='Health & Fitness')

for feature in features:
    c_feature = Feature()
    c_feature.category = c_category
    c_feature.name = feature.name
    c_feature.type = feature.type
    c_feature.group = feature.group
    c_feature.allow_multiple_select = feature.allow_multiple_select
    c_feature.unit = feature.unit
    c_feature.is_visible = feature.is_visible
    c_feature.min = feature.min
    c_feature.max = feature.max
    c_feature.sort_order = feature.sort_order
    c_feature.use_for_icons  = feature.use_for_icons
    c_feature.use_as_key_features = feature.use_as_key_features
    c_feature.save()
    feature_choices = FeatureChoice.objects.filter(feature=feature)
    for choice in feature_choices:
        c_choice = FeatureChoice()
        c_choice.name = choice.name
        c_choice.feature = c_feature
        c_choice.icon = choice.icon
        c_choice.save()
