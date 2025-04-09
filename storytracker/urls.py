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
    path('api/seasons/<int:season_id>/', views.get_season_data, name='get_season_data'),
    path('api/seasons/<int:season_id>/awards/', views.get_season_awards, name='get_season_awards'),
    path('api/seasons/<int:season_id>/transfers/', views.get_season_transfers, name='get_season_transfers'),
    path('stories/<slug:slug>/update-awards/', views.update_season_awards, name='update_season_awards'),
    path('api/player-stats/update/', views.update_player_stat, name='update_player_stat'),
    path('api/transfers/add/', views.add_transfer, name='add_transfer'),
    path('api/transfers/delete/', views.delete_transfer, name='delete_transfer'),
    path('api/seasons/add/', views.add_season, name='add_season'),
    path('api/player-stats/delete/', views.delete_player_stat, name='delete_player_stat'),

]
