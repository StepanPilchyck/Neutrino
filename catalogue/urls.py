from django.conf.urls import url
from catalogue import views as views

urlpatterns = [
     url('^(\w+)/(\d+)?$', view=views.catalogue_category, name='catalogue_category'),
     url('^(\w+)/(\w+)$', view=views.catalogue_item, name='catalogue_item'),
]
