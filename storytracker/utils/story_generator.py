import os
import random
from openai import OpenAI
from django.conf import settings
from storytracker.models import Club, Competition  # Import the Club and Competition models

def get_random_item(file_path):
    with open(file_path, 'r') as f:
        return random.choice(f.readlines()).strip()

def get_random_club_from_db():
    """Get a random club from the database"""
    count = Club.objects.count()
    if count == 0:
        return "No clubs in database"
    
    random_index = random.randint(0, count - 1)
    return Club.objects.all()[random_index]

def generate_club_history_prompt(randomClub: str) -> str:
    return f"""
    Provide the following information about {randomClub} in immersive and historically detailed HTML format. 
    Ensure it reads like a historian’s analysis and reflects the deep-rooted culture of the club. 
    Use evocative language and concrete examples rather than generalizations.

    <h4>Club Backstory:</h4>
    <p> Write a rich historical backstory of {randomClub}, covering its founding, struggles, golden eras, and cultural impact. 
    Include details about its two fiercest rivals, explaining how these rivalries originated and evolved over time—highlighting key matches, controversial moments, ideological divides, and legendary clashes. 
    Mention the club’s fan culture, stadium atmosphere, and how the team is perceived domestically and internationally. 
    Ensure this section is no longer than 10 sentences. </p>

    <h4>League History:</h4>
    <p> Provide an authoritative historical overview of the league {randomClub} competes in. 
    Detail its formation, major reforms, and most successful clubs (focusing on the four most dominant teams). 
    Discuss the five fiercest rivalries, explaining their origins—whether based on geography, class divides, historical matches, or political tensions. 
    Ensure the paragraph is at least 6 sentences long and written in an engaging, historian-like tone. </p>

    <h4>Club Philosophy:</h4>
    <p> Explain {randomClub}’s tactical identity and transfer policy in an engaging and detailed manner. 
    Cover their playing style (e.g., possession-based, counter-attacking, pressing), their approach to player recruitment (big spending vs. academy reliance), and how their philosophy has evolved under different managers. 
    Mention the club’s youth development strategy, scouting networks, and managerial legacy. 
    Ensure this is a structured, 7-sentence response. </p>

    <h4>Club Influence and Achievements:</h4>
    <p> Analyze {randomClub}’s historical significance and competitive achievements. 
    Detail their most successful league season, their greatest international triumphs, and how they compare to domestic and continental rivals. 
    Mention club legends, current star players, and their role in shaping the modern game. Discuss their fanbase, media presence, and lasting legacy within football culture. 
    Ensure this reads like a historian’s perspective, rather than a generic summary. </p> 
    """

def generate_club_background(club):
    client = OpenAI(base_url="http://192.168.0.107:1234/v1", api_key="lm-studio")
    
    response = client.chat.completions.create(
        model='your-model',
        messages=[{"role": "user", "content": generate_club_history_prompt(club)}],
        stream=False
    )
    final = response.choices[0].message.content
    
    # Remove any prefixes before the first <h4> tag
    if '<h4>' in final:
        final = final[final.find('<h4>'):]
    
    # Clean up any other potential markers
    noThinkResponse = final.split('</think>')[-1].strip()
    noHTMLResponse = noThinkResponse.split('```html')[-1].strip()
    cleanResponse = noHTMLResponse.split('```')[0].strip()
    
    return cleanResponse

def generate_all():
    data_dir = os.path.join(settings.BASE_DIR, 'storytracker/data')
    
    # Get a random club from the database
    club_obj = get_random_club_from_db()
    club_name = club_obj.name if isinstance(club_obj, Club) else club_obj
    
    return {
        'club': club_name,
        'club_id': getattr(club_obj, 'id', None),  # Store club ID for later reference
        'formation': get_random_item(os.path.join(data_dir, 'fifaFormations.txt')),
        'challenge': get_random_item(os.path.join(data_dir, 'fifaChallenges.txt')),
        'background': generate_club_background(club_name)
    }