from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('save-story/', views.save_story, name='save_story'),
    path('my-stories/', views.my_stories, name='my_stories'),
    path('story/<slug:slug>/', views.story_detail, name='story_detail'),
    path('story/<slug:slug>/add-player-stats/', views.add_player_stats, name='add_player_stats'),
    path('api/clubs/<int:club_id>/players/', views.api_club_players, name='api_club_players'),
    path('api/seasons/<int:season_id>/player-stats/', views.api_season_player_stats, name='api_season_player_stats'),
]
