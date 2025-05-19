from django.urls import path
from .views import node_list_create, node_detail

urlpatterns = [
    path('nodes/', node_list_create, name='node-list-create'),
    path('nodes/<int:pk>/', node_detail, name='node-detail'),
]