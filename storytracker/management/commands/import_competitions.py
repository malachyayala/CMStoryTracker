from django.core.management.base import BaseCommand
import pandas as pd
from storytracker.models import Competition
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Import competitions from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        try:
            # Read CSV file with proper column names
            df = pd.read_csv(csv_file)
            
            competitions_created = 0
            
            for _, row in df.iterrows():
                try:
                    # Handle empty wage budgets
                    min_wage = pd.to_numeric(row['Minimum Wage Budgets'], errors='coerce')
                    min_wage = 0 if pd.isna(min_wage) else min_wage

                    competition = Competition(
                        name=row['League'],
                        competition_type=row['competition_type'].upper(),
                        country=row['Country'],
                        logo_url=row['Image Link'],
                        league_rep=row['League Rep'],
                        tier=row['Tier'],
                        min_wage_budget=min_wage
                    )
                    
                    # Generate slug
                    competition.slug = slugify(competition.name)
                    
                    # Save the competition
                    competition.save()
                    competitions_created += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Imported: {competition.name} ({competition.country})')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing competition {row["League"]}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully imported {competitions_created} competitions')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {str(e)}')
            )