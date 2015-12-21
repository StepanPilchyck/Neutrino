from django.conf.urls import url
from static_page import views as views

urlpatterns = [
     url('^(\w+)$', view=views.static_page, name='static_page'),
     url('^$', view=views.index_page, name='index_page'),
]