import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse, HttpRequest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import os
from .models import Player, PlayerStats, Season, Story, Club
from .utils.story_generator import generate_all
from django.views.decorators.http import require_http_methods
from .models import Transfer
from django.core.exceptions import ValidationError
import re
from django.urls import reverse

def index(request: HttpRequest) -> HttpResponse:
    """
    Renders the index page.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        HttpResponse: The rendered index page.
    """
    return render(request, 'storytracker/index.html')

def generate_story(request: HttpRequest) -> JsonResponse:
    """
    Generates a new story but does NOT save it.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        JsonResponse: A JSON response with the generated story data or an error message.
    """
    if request.method == "POST":
        data = generate_all()  # Generate new story data

        return JsonResponse({
            "success": True,
            "club": data['club'],
            "formation": data['formation'],
            "challenge": data['challenge'],
            "background": data['background']
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

def register(request: HttpRequest) -> HttpResponse:
    """
    Handles user registration.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        HttpResponse: The registration page or a redirect to the login page upon successful registration.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page after registration
    else:
        form = UserCreationForm()
    
    return render(request, 'storytracker/register.html', {'form': form})

def custom_login(request: HttpRequest) -> HttpResponse:
    """
    Handles user login.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        HttpResponse: The login page or a redirect to the home page upon successful login.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')  # Redirect to home after successful login
        messages.error(request, "Invalid username or password.")  # Display error message

    else:
        form = AuthenticationForm()

    return render(request, 'storytracker/login.html', {'form': form})

def custom_logout(request: HttpRequest) -> HttpResponse:
    """
    Logs out the user and redirects to the login page.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        HttpResponse: A redirect to the login page.
    """
    logout(request)
    return redirect('/login/')

@login_required
def save_story(request: HttpRequest) -> JsonResponse:
    """
    Saves a story when the user explicitly clicks 'Save Story'.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    if request.method == "POST":
        club_name = request.POST.get("club")
        club_id = request.POST.get("club_id")
        formation = request.POST.get("formation")
        challenge = request.POST.get("challenge")
        background = request.POST.get("background")
        
        # Try to get club by ID first, then by name if ID not provided
        club = None
        if club_id:
            try:
                club = Club.objects.get(id=club_id)
            except Club.DoesNotExist:
                pass
        
        # Fallback to finding by name
        if not club and club_name:
            club = Club.objects.filter(name=club_name).first()
        
        # If we couldn't find the club, return error
        if not club:
            return JsonResponse({"error": "Club not found"}, status=400)
            
        if club and formation and challenge and background:
            # Create the story
            story = Story.objects.create(
                user=request.user,
                club=club,
                name=f"{request.user.username}'s {club.name} Career",  # Default name
                formation=formation,
                challenge=challenge,
                background=background
            )
            
            # Create initial season
            initial_season = Season.objects.create(
                story=story,
                season_number=1,
                name="24/25",
                is_current=True
            )
            
            return JsonResponse({
                "success": True, 
                "message": "Story saved!", 
                "story_id": story.id,
                "redirect_url": reverse('story_detail', kwargs={'slug': story.slug})
            })

    return JsonResponse({"error": "Failed to save story"}, status=400)

@login_required
def my_stories(request: HttpRequest) -> HttpResponse:
    """
    Displays all stories created by the logged-in user.
    
    Args:
        request (HttpRequest): The request object.
    
    Returns:
        HttpResponse: The rendered my stories page.
    """
    # Get all stories for the current user, ordered by most recently updated
    stories = Story.objects.filter(user=request.user).order_by('-updated_at')
    
    # Create a context with additional statistics
    stories_with_stats = []
    for story in stories:
        # Get current season
        current_season = story.seasons.filter(is_current=True).first()
        
        # Get basic stats
        total_seasons = story.seasons.count()
        
        # You could expand this to include more stats if desired
        stories_with_stats.append({
            'story': story,
            'current_season': current_season,
            'total_seasons': total_seasons,
            'club_logo': story.club.club_logo_small_url if story.club and hasattr(story.club, 'club_logo_small_url') else None
        })
    
    context = {
        'stories': stories_with_stats,
        'total_stories': len(stories_with_stats)
    }
    
    return render(request, 'storytracker/my_stories.html', context)

@login_required
def story_detail(request, slug):
    """
    Display story details including player statistics
    """
    story = get_object_or_404(Story, slug=slug)
    
    # Check if the user is authorized to view this story
    if story.user != request.user and not story.is_public:
        return HttpResponseForbidden("You don't have permission to view this story.")
    
    # Get the current season or the latest season if none is marked current
    current_season = story.get_current_season() or story.seasons.order_by('-season_number').first()
    
    # Get all player stats for the current season
    player_stats = PlayerStats.objects.filter(story=story, season=current_season) if current_season else []
    
    context = {
        'story': story,
        'current_season': current_season,
        'seasons': story.seasons.all(),
        'player_stats': player_stats,
    }
    
    return render(request, 'storytracker/story_detail.html', context)

@login_required
def add_player_stats(request, slug):
    """
    Add or update player statistics for a specific season
    """
    story = get_object_or_404(Story, slug=slug)
    
    # Check if the user is authorized to edit this story
    if story.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this story.")
    
    if request.method == "POST":
        season_id = request.POST.get('season_id')
        player_id = request.POST.get('player_id')
        
        try:
            season = Season.objects.get(id=season_id, story=story)
            player = Player.objects.get(id=player_id)
            
            # Get or create player stats
            stats, created = PlayerStats.objects.get_or_create(
                story=story,
                season=season,
                player=player,
                defaults={
                    'overall_rating': request.POST.get('overall_rating', 0),
                    'appearances': request.POST.get('appearances', 0),
                    'goals': request.POST.get('goals', 0),
                    'assists': request.POST.get('assists', 0),
                    'clean_sheets': request.POST.get('clean_sheets', 0),
                    'red_cards': request.POST.get('red_cards', 0),
                    'yellow_cards': request.POST.get('yellow_cards', 0),
                    'average_rating': request.POST.get('average_rating', 0.0),
                }
            )
            
            if not created:
                # Update existing stats
                stats.overall_rating = request.POST.get('overall_rating', stats.overall_rating)
                stats.appearances = request.POST.get('appearances', stats.appearances)
                stats.goals = request.POST.get('goals', stats.goals)
                stats.assists = request.POST.get('assists', stats.assists)
                stats.clean_sheets = request.POST.get('clean_sheets', stats.clean_sheets)
                stats.red_cards = request.POST.get('red_cards', stats.red_cards)
                stats.yellow_cards = request.POST.get('yellow_cards', stats.yellow_cards)
                stats.average_rating = request.POST.get('average_rating', stats.average_rating)
                stats.save()
            
            return JsonResponse({'success': True})
            
        except (Season.DoesNotExist, Player.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def api_club_players(request, club_id):
    """API endpoint to get players for a specific club"""
    club = get_object_or_404(Club, id=club_id)
    players = Player.objects.filter(club=club).order_by('-overall')
    
    player_data = [{
        'id': player.id,
        'name': player.name,
        'overall': player.overall,
        'positions': player.positions
    } for player in players]
    
    return JsonResponse({'players': player_data})

@login_required
def api_season_player_stats(request, season_id):
    """API endpoint to get player stats for a specific season"""
    season = get_object_or_404(Season, id=season_id)
    
    # Check if the user is authorized to view this data
    if season.story.user != request.user and not season.story.is_public:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    player_stats = PlayerStats.objects.filter(season=season)
    
    stats_data = [{
        'id': stat.id,
        'player_id': stat.player.id,
        'player_name': stat.player.name,
        'overall_rating': stat.overall_rating,
        'appearances': stat.appearances,
        'goals': stat.goals,
        'assists': stat.assists,
        'clean_sheets': stat.clean_sheets,
        'yellow_cards': stat.yellow_cards,
        'red_cards': stat.red_cards,
        'average_rating': float(stat.average_rating)
    } for stat in player_stats]
    
    return JsonResponse({'player_stats': stats_data})