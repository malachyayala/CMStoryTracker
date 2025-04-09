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
def delete_player_stat(request):
    """Delete player statistics"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stat_id = data.get('stat_id')
            
            # Get the stat object
            stat = get_object_or_404(PlayerStats, id=stat_id)
            
            # Check permission
            if stat.story.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Delete the stat
            stat.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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

@login_required
def add_season(request):
    """Create a new season for a story"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            story_slug = data.get('story_slug')
            season_name = data.get('season_name')
            season_number = data.get('season_number')
            
            # Get the story
            story = get_object_or_404(Story, slug=story_slug, user=request.user)
            
            # Check if season with this name already exists
            if Season.objects.filter(story=story, name=season_name).exists():
                return JsonResponse({'error': 'Season with this name already exists'}, status=400)
            
            # Set all seasons to not current
            story.seasons.update(is_current=False)
            
            # Create new season
            new_season = Season.objects.create(
                story=story,
                name=season_name,
                season_number=season_number,
                is_current=True
            )
            
            return JsonResponse({
                'success': True,
                'season_id': new_season.id,
                'season_name': new_season.name
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def update_player_stat(request):
    """Update a single field of player statistics"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stat_id = data.get('stat_id')
            field_name = data.get('field')
            value = data.get('value')
            
            # Get the stat object
            stat = get_object_or_404(PlayerStats, id=stat_id)
            
            # Check permission
            if stat.story.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Update the specified field
            if hasattr(stat, field_name):
                setattr(stat, field_name, value)
                stat.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def update_season_awards(request, slug):
    """Update season awards information"""
    if request.method == 'POST':
        story = get_object_or_404(Story, slug=slug)
        
        # Check permission
        if story.user != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        season_id = request.POST.get('season_id')
        season = get_object_or_404(Season, id=season_id, story=story)
        
        # Here you would update various competition winners
        # This depends on your exact model structure
        # Example:
        la_liga = request.POST.get('la_liga_winner')
        if la_liga:
            club = Club.objects.filter(name=la_liga).first()
            if club:
                CompetitionWinner.objects.update_or_create(
                    story=story,
                    season=season,
                    competition__name='La Liga',
                    defaults={'winner': club}
                )
        
        # Do the same for other leagues and awards...
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def add_transfer(request):
    """Add a new transfer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            season_id = data.get('season_id')
            player_name = data.get('player_name')
            fee = data.get('fee')
            direction = data.get('direction')
            
            # Get the season
            season = get_object_or_404(Season, id=season_id)
            story = season.story
            
            # Check permission
            if story.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Find or create player
            player, created = Player.objects.get_or_create(
                name=player_name,
                defaults={'club': story.club}
            )
            
            # Create transfer record
            if direction == 'in':
                club_name = data.get('from_club', 'Unknown Club')
                from_club, created = Club.objects.get_or_create(name=club_name)
                
                transfer = Transfer.objects.create(
                    season=season,
                    story=story,
                    player=player,
                    from_club=from_club,
                    to_club=story.club,
                    fee=fee,
                    transfer_date=timezone.now().date()
                )
            else:
                club_name = data.get('to_club', 'Unknown Club')
                to_club, created = Club.objects.get_or_create(name=club_name)
                
                transfer = Transfer.objects.create(
                    season=season,
                    story=story,
                    player=player,
                    from_club=story.club,
                    to_club=to_club,
                    fee=fee,
                    transfer_date=timezone.now().date()
                )
            
            return JsonResponse({
                'success': True,
                'transfer_id': transfer.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def delete_transfer(request):
    """Delete a transfer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transfer_id = data.get('transfer_id')
            
            # Get the transfer
            transfer = get_object_or_404(Transfer, id=transfer_id)
            
            # Check permission
            if transfer.story.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Delete the transfer
            transfer.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_season_data(request, season_id):
    """Get basic season information"""
    season = get_object_or_404(Season, id=season_id)
    
    # Check permission
    if season.story.user != request.user and not season.story.is_public:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    return JsonResponse({
        'success': True,
        'season': {
            'id': season.id,
            'name': season.name,
            'number': season.season_number,
            'is_current': season.is_current
        }
    })

@login_required
def get_season_awards(request, season_id):
    """Get awards data for a season"""
    season = get_object_or_404(Season, id=season_id)
    story = season.story
    
    # Check permission
    if story.user != request.user and not story.is_public:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Get competition winners
    competition_winners = CompetitionWinner.objects.filter(season=season)
    
    # Transform to expected format
    awards = {
        'la_liga_winner': '',
        'serie_a_winner': '',
        'bundesliga_winner': '',
        'ligue_1_winner': '',
        'premier_league_winner': '',
        'champions_league_winner': '',
        'europa_league_winner': '',
        'conference_league_winner': '',
        'super_cup_winner': '',
        'balon_dor_winner': '',
        'golden_boy_winner': ''
    }
    
    # Populate with actual data
    for winner in competition_winners:
        comp_name = winner.competition.name.lower().replace(' ', '_')
        awards[f'{comp_name}_winner'] = winner.winner.name
    
    # Get individual awards
    award_winners = AwardWinner.objects.filter(season=season)
    for award in award_winners:
        award_name = award.award.name.lower().replace(' ', '_').replace("'", '')
        awards[f'{award_name}_winner'] = award.player.name
    
    return JsonResponse({
        'success': True,
        'awards': awards
    })

@login_required
def get_season_transfers(request, season_id):
    """Get transfers for a season"""
    season = get_object_or_404(Season, id=season_id)
    story = season.story
    
    # Check permission
    if story.user != request.user and not story.is_public:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Get transfers
    transfers_in = Transfer.objects.filter(season=season, to_club=story.club)
    transfers_out = Transfer.objects.filter(season=season, from_club=story.club)
    
    # Format transfers
    transfers_in_data = [{
        'id': t.id,
        'player_name': t.player.name,
        'from_club': t.from_club.name,
        'fee': t.fee,
        'date': t.transfer_date.strftime('%Y-%m-%d')
    } for t in transfers_in]
    
    transfers_out_data = [{
        'id': t.id,
        'player_name': t.player.name,
        'to_club': t.to_club.name,
        'fee': t.fee,
        'date': t.transfer_date.strftime('%Y-%m-%d')
    } for t in transfers_out]
    
    return JsonResponse({
        'success': True,
        'transfers_in': transfers_in_data,
        'transfers_out': transfers_out_data
    })