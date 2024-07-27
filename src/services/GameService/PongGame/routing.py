# your_app/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # re_path(r'ws/pong/(?P<game_id>\d+)/$', consumers.GameConsumer.as_asgi()),
    re_path(r'ws/pong/(?P<game_id>\d+)/(?P<token>\w+)/(?P<UserId>\d+)$', consumers.GameConsumer.as_asgi()),
]