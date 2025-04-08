import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from storytracker.models import Player, Club

class Command(BaseCommand):
    help = 'Import players from FC25Players.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        import_source = "FC25_CSV_IMPORT"
        success_count = 0
        error_count = 0
        
        with open(csv_file_path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Get or create the club
                    club_name = row['Club']
                    try:
                        club = Club.objects.get(name=club_name)
                    except Club.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Club '{club_name}' does not exist. Skipping player {row['Authentic Player Name Search']}"))
                        error_count += 1
                        continue
                    
                    # Process positions
                    positions = []
                    if row['Primary'] and row['Primary'] != '':
                        positions.append(row['Primary'])
                    if row['Secondary'] and row['Secondary'] != '':
                        positions.append(row['Secondary'])
                    if row['Tertiary'] and row['Tertiary'] != '':
                        positions.append(row['Tertiary'])
                    
                    # Parse birth date
                    try:
                        birth_date = datetime.strptime(row['Birth Date'], '%m/%d/%y').date()
                    except ValueError:
                        try:
                            # Try alternate format
                            birth_date = datetime.strptime(row['Birth Date'], '%m/%d/%Y').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f"Invalid birth date format for {row['Authentic Player Name Search']}: {row['Birth Date']}"))
                            error_count += 1
                            continue
                    
                    # Calculate birth year
                    birth_year = birth_date.year
                    
                    # For contract dates, use approximate values (1 year contracts)
                    contract_start = datetime.now().date()
                    contract_end = contract_start + timedelta(days=365)
                    
                    # Process wages - ensure they're positive or set to default
                    try:
                        wage_eur = float(row['Wage EUR'])
                        wage_eur = abs(wage_eur) if wage_eur != 0 else 100
                    except (ValueError, TypeError):
                        wage_eur = 100
                        
                    try:
                        wage_usd = float(row['Wage USD'])
                        wage_usd = abs(wage_usd) if wage_usd != 0 else 100
                    except (ValueError, TypeError):
                        wage_usd = 100
                        
                    try:
                        wage_gbp = float(row['Wage GBP'])
                        wage_gbp = abs(wage_gbp) if wage_gbp != 0 else 100
                    except (ValueError, TypeError):
                        wage_gbp = 100
                    
                    # Create or update the player
                    player, created = Player.objects.update_or_create(
                        player_id=int(row['Player ID']),
                        defaults={
                            'name': row['Authentic Player Name Search'],
                            'slug': slugify(f"{row['Authentic Player Name Search']}-{row['Player ID']}"),
                            'positions': positions,
                            'nationality': row['Nationality'],
                            'birth_date': birth_date,
                            'birth_year': birth_year,
                            'age': int(row['Age']),
                            'face_pic_url': row['Face Pic'],
                            'club': club,
                            'wage_eur': wage_eur,
                            'wage_usd': wage_usd,
                            'wage_gbp': wage_gbp,
                            'contract_start': contract_start,
                            'contract_end': contract_end,
                            'contract_loan': False,
                            'overall': int(row['Overall']),
                            # Setting potential equal to overall as default
                            'potential': int(row['Overall']),
                            'import_source': import_source
                        }
                    )
                    
                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f"{action} player: {player.name} ({player.player_id})"))
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing player {row.get('Authentic Player Name Search', 'Unknown')}: {e}")
                    )
                    error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Successfully imported {success_count} players. Errors: {error_count}"
            )
        )