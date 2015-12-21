from django.conf.urls import url
from localization import views

urlpatterns = [
     url('^language/(\w{2})$', view=views.lang),
     url('^currency/(\w{3})$', view=views.currency),
]
