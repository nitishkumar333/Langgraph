from django.urls import path
from .views import node_list_create, node_detail, chat_ai, chat_history, delete_history, get_node_and_edges

urlpatterns = [
    path('nodes/', node_list_create, name='node-list-create'),
    path('nodes/<int:pk>/', node_detail, name='node'),
    path('get-nodes-edges/', get_node_and_edges, name='get-all'),
    path('chat-ai/', chat_ai, name='chat-ai'),
    path('chat-history/', chat_history, name='get-messages'),
    path('delete-history/', delete_history, name='delete-history'),
]

# email node
# first message appear in chatbot