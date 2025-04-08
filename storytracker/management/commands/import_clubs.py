from django.core.management.base import BaseCommand
import pandas as pd
from storytracker.models import Club, Competition
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Import clubs from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument('--create-competitions', action='store_true', help='Create competitions if they do not exist')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        create_competitions = kwargs.get('create_competitions', False)
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            clubs_created = 0
            clubs_skipped = 0
            competitions_created = 0
            
            # First, ensure all competitions exist
            if create_competitions:
                unique_leagues = df[['League ID', 'League', 'Country', 'League Rep']].drop_duplicates()
                for _, row in unique_leagues.iterrows():
                    try:
                        comp = Competition.objects.filter(name=row['League']).first()
                        if not comp:
                            comp = Competition(
                                name=row['League'],
                                country=row['Country'],
                                tier=row['League ID'],
                                league_rep=row['League Rep'],
                                competition_type='LEAGUE', # Default value
                                slug=slugify(row['League'])
                            )
                            comp.save()
                            competitions_created += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"Created competition: {comp.name}")
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error creating competition '{row['League']}': {str(e)}")
                        )
            
            # Then import clubs
            for _, row in df.iterrows():
                try:
                    # Try to get the competition for this club
                    try:
                        competition = Competition.objects.get(name=row['League'])
                    except Competition.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"Competition '{row['League']}' not found, skipping club '{row['Club']}'")
                        )
                        continue
                    
                    # Check if club already exists
                    if Club.objects.filter(name=row['Club']).exists():
                        self.stdout.write(
                            self.style.WARNING(f"Club '{row['Club']}' already exists, skipping")
                        )
                        clubs_skipped += 1
                        continue
                    
                    # Default values for required fields that might be null in CSV
                    scout_region = row['Scout Region'] if 'Scout Region' in row and not pd.isna(row['Scout Region']) else row['Country']
                    youth_region = row['Youth Scouting Region'] if 'Youth Scouting Region' in row and not pd.isna(row['Youth Scouting Region']) else row['Country']
                    
                    # Create new club with fields from the CSV
                    club = Club(
                        name=row['Club'],
                        league=competition,
                        country=row['Country'],
                        club_logo_small_url=row['Club Logo Small'],
                        club_logo_big_url=row['Club Logo Big'],
                        overall=row['Overall'],
                        att_rating=row['ATT'],
                        mid_rating=row['MID'],
                        def_rating=row['DEF'],
                        dom_prestige=row['Dom. Prestige'],
                        intl_prestige=row["Int'l Prestige"],
                        league_rep=row['League Rep'],
                        scout_region=scout_region,
                        youth_scouting_region=youth_region
                    )
                    
                    # Add international competition if available
                    if "Int'l Comp" in row and not pd.isna(row["Int'l Comp"]):
                        club.international_competition = row["Int'l Comp"]
                    
                    # Generate slug
                    club.slug = slugify(club.name)
                    
                    # Save the club
                    club.save()
                    clubs_created += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Imported club: {club.name} ({competition.name})")
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error importing club '{row['Club']}': {str(e)}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f"\nClubs import summary: {clubs_created} created, {clubs_skipped} skipped")
            )
            if create_competitions:
                self.stdout.write(
                    self.style.SUCCESS(f"Competitions created: {competitions_created}")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error reading CSV file: {str(e)}")
            )