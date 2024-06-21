from . import views
from django.urls import path
from .views import delete_all_data


urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_results, name='search_results'),
    path('delete/', views.delete_all_data, name='delete_all_data'),

]