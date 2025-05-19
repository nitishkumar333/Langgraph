from django.urls import path
from .views import node_list_create, node_detail, chat_ai, chat_history

urlpatterns = [
    path('nodes/', node_list_create, name='node-list-create'),
    path('nodes/<int:pk>/', node_detail, name='node'),
    path('chat-ai/', chat_ai, name='chat-ai'),
    path('chat-history/', chat_history, name='get-messages'),
]