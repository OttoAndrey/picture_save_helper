from django.urls import path
from picture_save_helper.settings import VK_BOT_TOKEN

from . import views

urlpatterns = [
    path(f'{VK_BOT_TOKEN}/', views.picture_save_help)
]