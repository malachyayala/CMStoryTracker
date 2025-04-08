from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse


class Competition (models.Model):
    """
    Represents a football competition such as a league or cup tournament.

    Attributes:
        name (str): The name of the competition. This is a CharField with a
        maximum length of 100 characters, indexed for faster queries,
        and must be unique.
        slug (str): URL-friendly version of the competition name,
        automatically generated if not provided. This is a SlugField with a
        maximum length of 120 characters and must be unique.
        competition_type (str): The type of competition. Must be one of:
            - LEAGUE: Regular league competition
            - CUP: Knockout cup competition
            - INTERNATIONAL: International competition
        country (str): The country where the competition takes place. This is
        a CharField with a maximum length of 100 characters and is indexed
        for faster queries.
        logo_url (str): URL to the competition's logo image. This is a
        URLField that can be blank or null.
        league_rep (int): The reputation level of the league. This is an
        IntegerField with a minimum value of 0, validated using
        MinValueValidator.
        tier (int): The tier level of the competition within its country's
        football pyramid. This is an IntegerField with a minimum value of 1,
        validated using MinValueValidator.
        min_wage_budget (decimal): The minimum wage budget for clubs in this
        competition. This is a DecimalField with 10 digits, 2 decimal places,
        and a minimum value of 0.

    Methods:
        save(*args, **kwargs): Overridden to automatically generate slug if
        not provided.
        get_absolute_url(): Returns the URL for the competition's detail view.

    Meta:
        verbose_name (str): Human-readable singular name for the model.
        verbose_name_plural (str): Human-readable plural name for the model.
        indexes (list): Database indexes for optimizing queries on frequently
        accessed fields.
    """
    COMPETITION_TYPES = [
        ('LEAGUE', 'League'),
        ('CUP', 'Cup'),
        ('INTERNATIONAL', 'International'),
    ]

    name = models.CharField (max_length = 100, db_index = True, unique = True)
    slug = models.SlugField (max_length = 120, unique = True, blank = True)
    competition_type = models.CharField (
        max_length = 50,
        choices = COMPETITION_TYPES,
        default = 'LEAGUE',
        db_index = True  # Add index for faster filtering by type
    )
    country = models.CharField (max_length = 100, db_index = True)
    logo_url = models.URLField (null = True, blank = True)
    league_rep = models.IntegerField (
        validators = [MinValueValidator (0), MaxValueValidator (5)],
        # Add max value
        help_text = "League reputation from 0 to 5"
    )
    tier = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (5)],
        # Add max value
        help_text = "Competition tier from 1 (top) to 5"
    )
    min_wage_budget = models.DecimalField (
        max_digits = 10,
        decimal_places = 2,
        validators = [MinValueValidator (0)],
        help_text = "Minimum wage budget in euros"
    )

    class Meta:
        verbose_name = "Competition"
        verbose_name_plural = "Competitions"
        indexes = [
            models.Index (fields = ['name']),
            models.Index (fields = ['country']),
        ]
        constraints = [
            # Ensure tier 1 is unique per country for leagues
            models.UniqueConstraint (
                fields = ['country', 'tier'],
                condition = models.Q (competition_type = 'LEAGUE', tier = 1),
                name = 'unique_tier1_league_per_country'
            ),
        ]

    def __str__ (self):
        return self.name

    def save (self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify (self.name)
        super ().save (*args, **kwargs)

    def get_absolute_url (self):
        return reverse ("competition_detail", kwargs = {"slug": self.slug})

class Club (models.Model):
    """
    Represents a football club with detailed attributes and ratings.

    Attributes:
        league (Competition): The league in which the club competes.
        ForeignKey to Competition model
            with CASCADE delete behavior. When a competition is deleted,
            all associated clubs will
            also be deleted.
        name (str): The name of the club. CharField with max_length=255,
        indexed for faster queries.
            Must be unique within each country.
        club_logo_small_url (str): URL to the small version of the club's
        logo. URLField that can
            be blank or null.
        club_logo_big_url (str): URL to the big version of the club's logo.
        URLField that can be
            blank or null.
        overall (int): The overall rating of the club on a scale from 1 to
        99, validated using
            MinValueValidator and MaxValueValidator.
        att_rating (int): The attacking rating of the club on a scale from 1
        to 99, validated
            using MinValueValidator and MaxValueValidator.
        mid_rating (int): The midfield rating of the club on a scale from 1
        to 99, validated
            using MinValueValidator and MaxValueValidator.
        def_rating (int): The defensive rating of the club on a scale from 1
        to 99, validated
            using MinValueValidator and MaxValueValidator.
        country (str): The country where the club is based. CharField with
        max_length=100,
            indexed for faster queries.
        scout_region (str): The geographic region where the club can scout
        players. CharField
            with max_length=100.
        dom_prestige (int): The domestic prestige of the club on a scale from
        1 to 10,
            validated using MinValueValidator and MaxValueValidator.
        intl_prestige (int): The international prestige of the club on a
        scale from 1 to 10,
            validated using MinValueValidator and MaxValueValidator.
        league_rep (int): The league reputation of the club on a scale from 1
        to 10,
            validated using MinValueValidator and MaxValueValidator.
        youth_scouting_region (str): The geographic region where the club can
        scout youth
            players. CharField with max_length=100.

    Methods:
        __str__(): Returns the name of the club as its string representation.

    Meta:
        verbose_name (str): Human-readable singular name for the model.
        verbose_name_plural (str): Human-readable plural name for the model.
        indexes (list): Database indexes for optimizing queries on frequently
        accessed fields:
            - name: For searching clubs by name
            - country: For filtering clubs by country
            - overall: For sorting and filtering by rating
        constraints (list): Database constraints to ensure data integrity:
            - unique_club_name_per_country: Ensures club names are unique
            within each country
    """

    # Existing fields
    league = models.ForeignKey (Competition, on_delete = models.CASCADE)
    name = models.CharField (
        max_length = 255, db_index = True
        )  # Add index for faster queries
    club_logo_small_url = models.URLField (null = True, blank = True)
    club_logo_big_url = models.URLField (null = True, blank = True)
    overall = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)],
        help_text = "Club's overall rating from 1 to 99"
    )
    att_rating = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)],
        help_text = "Club's attack rating from 1 to 99"
    )
    mid_rating = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)],
        help_text = "Club's midfield rating from 1 to 99"
    )
    def_rating = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)],
        help_text = "Club's defense rating from 1 to 99"
    )
    country = models.CharField (
        max_length = 100, db_index = True
        )  # Add index for faster queries
    scout_region = models.CharField (max_length = 100)
    dom_prestige = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (10)],
        help_text = "Domestic prestige from 1 to 10"
    )
    intl_prestige = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (10)],
        help_text = "International prestige from 1 to 10"
    )
    league_rep = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (10)],
        help_text = "League reputation from 1 to 10"
    )
    youth_scouting_region = models.CharField (max_length = 100)

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubs"
        indexes = [
            models.Index (fields = ['name']),
            models.Index (fields = ['country']),
            models.Index (fields = ['overall']),
        ]
        constraints = [
            # Ensure unique club name per country
            models.UniqueConstraint (
                fields = ['name', 'country'],
                name = 'unique_club_name_per_country'
            )
        ]

    def __str__ (self):
        return self.name

class IndividualAward (models.Model):
    """
    Represents an individual award.

    Attributes:
        name (str): The name of the award. This is a CharField with a maximum
        length of 100 characters.
    """
    name = models.CharField (max_length = 100)  # e.g. "Ballon d'Or"

    def __str__ (self):
        return self.name

class Player (models.Model):
    """
    Represents a football player with detailed personal, professional,
    and performance attributes.

    Attributes:
        Basic Information:
            player_id (int): Unique identifier for the player. IntegerField
            with unique=True.
            name (str): Player's full name. CharField(100) with db_index for
            faster queries.
            slug (str): URL-friendly version of name. SlugField(150),
            auto-generated, unique.
            positions (list): Array of up to 3 positions from
            POSITION_CHOICES. ArrayField with CharField(3).
            nationality (str): Player's country of origin. CharField(100).
            
        Personal Details:
            birth_date (date): Player's date of birth. DateField.
            birth_year (int): Year of birth, derived from birth_date.
            IntegerField, can be null.
            age (int): Current age, consider using current_age property
            instead. IntegerField.
            face_pic_url (str): URL to player's profile image. URLField,
            can be null.

        Club Information:
            club (Club): Current club. ForeignKey to Club with CASCADE delete.
            contract_start (date): Start date of current contract. DateField.
            contract_end (date): End date of current contract. DateField.
            contract_loan (bool): Indicates if player is on loan.
            BooleanField, default False.

        Financial Details:
            wage_eur (decimal): Wage in Euros. DecimalField(10,2).
            wage_usd (decimal): Wage in US Dollars. DecimalField(10,2).
            wage_gbp (decimal): Wage in British Pounds. DecimalField(10,2).

        Ratings:
            overall (int): Current ability rating (1-99). IntegerField with
            validators.
            potential (int): Maximum potential ability rating (1-99).
            IntegerField with validators.

        Import Data:
            last_import_date (datetime): Last data update timestamp.
            DateTimeField(auto_now=True).
            import_source (str): Data source identifier. CharField(100),
            can be null.

    Methods:
        save(*args, **kwargs): Overrides default save to:
            - Auto-generate slug if not provided
            - Calculate birth_year from birth_date
        current_age(): Property that calculates current age from birth_date.
        __str__(): Returns formatted string with name, overall rating, and club.

    Meta:
        verbose_name (str): "Player"
        verbose_name_plural (str): "Players"
        ordering (list): ['-overall', 'name']
        indexes (list): Optimized queries for:
            - name and overall
            - club and positions
        constraints (list):
            - potential_gte_overall: Ensures potential ≥ overall
            - contract_end_after_start: Validates contract dates
            - birth_year_matches_date: Ensures birth_year matches birth_date
            - positive_wages: Ensures all wage fields > 0
            - unique_player_club_registration: Prevents duplicate registrations
    """
    # Primary identifiers
    player_id = models.IntegerField (
        unique = True
        )  # Keep this if it matches your CSV column

    # Basic info
    name = models.CharField (max_length = 100, db_index = True)
    slug = models.SlugField (
        max_length = 150, unique = True, blank = True
        )  # URL-friendly name

    # Position fields with choices for better validation
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('CB', 'Center Back'),
        ('LB', 'Left Back'),
        ('RB', 'Right Back'),
        ('CDM', 'Defensive Midfielder'),
        ('CM', 'Central Midfielder'),
        ('CAM', 'Attacking Midfielder'),
        ('LM', 'Left Midfielder'),
        ('RM', 'Right Midfielder'),
        ('LW', 'Left Winger'),
        ('RW', 'Right Winger'),
        ('ST', 'Striker'),
        ('CF', 'Center Forward'),
    ]

    positions = ArrayField (
        models.CharField (
            max_length = 3,
            # Change to match the max length of position codes (e.g., "CAM")
            choices = POSITION_CHOICES
        ),
        size = 3,  # Limits to 3 positions per player
        blank = True,
        null = True
    )

    # Personal details
    nationality = models.CharField (max_length = 100)
    birth_date = models.DateField ()
    birth_year = models.IntegerField (
        null = True, blank = True
        )  # Derived field, can be calculated from birth_date
    age = models.IntegerField ()  # Consider making this a property method
    # instead of a field
    face_pic_url = models.URLField (null = True, blank = True)

    # Club information
    club = models.ForeignKey (
        Club, on_delete = models.CASCADE, db_index = True
        )  # Changed to ForeignKey

    # Contract details
    wage_eur = models.DecimalField (max_digits = 10, decimal_places = 2)
    wage_usd = models.DecimalField (max_digits = 10, decimal_places = 2)
    wage_gbp = models.DecimalField (max_digits = 10, decimal_places = 2)
    contract_start = models.DateField ()
    contract_end = models.DateField ()
    contract_loan = models.BooleanField (default = False)

    # Skills and ratings
    overall = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)]
    )
    potential = models.IntegerField (
        validators = [MinValueValidator (1), MaxValueValidator (99)]
    )

    # Import tracking
    last_import_date = models.DateTimeField (auto_now = True)
    import_source = models.CharField (
        max_length = 100, blank = True, null = True
        )  # e.g., "FIFA23_CSV_IMPORT"

    # Meta configuration
    class Meta:
        verbose_name = "Player"
        verbose_name_plural = "Players"
        ordering = ['-overall', 'name']
        indexes = [
            models.Index (fields = ['name', 'overall']),
            models.Index (fields = ['club', 'positions']),
        ]
        constraints = [
            # Ensure potential is greater than or equal to overall
            models.CheckConstraint (
                check = models.Q (potential__gte = models.F ('overall')),
                name = 'potential_gte_overall'
            ),
            # Ensure contract_end is after contract_start
            models.CheckConstraint (
                check = models.Q (
                    contract_end__gt = models.F ('contract_start')
                    ),
                name = 'contract_end_after_start'
            ),
            # Ensure wages are positive
            models.CheckConstraint (
                check = models.Q (wage_eur__gt = 0) & models.Q (
                    wage_usd__gt = 0
                    ) & models.Q (wage_gbp__gt = 0),
                name = 'positive_wages'
            ),
            # Prevent duplicate player registrations at the same club
            models.UniqueConstraint (
                fields = ['player_id', 'club'],
                name = 'unique_player_club_registration'
            )
        ]

    def __str__ (self):
        return f"{self.name} ({self.overall}) - {self.club}"

    def save (self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify (f"{self.name}-{self.player_id}")

        # Calculate birth_year from birth_date if not provided
        if not self.birth_year and self.birth_date:
            self.birth_year = self.birth_date.year

        super ().save (*args, **kwargs)

    @property
    def current_age (self):
        """Calculate current age instead of using static field"""
        from datetime import date
        today = date.today ()
        return today.year - self.birth_date.year - (
                (today.month, today.day) < (
        self.birth_date.month, self.birth_date.day)
        )

class Story (models.Model):
    """
    Represents a user's career mode story with enhanced tracking and
    customization options.

    Attributes:
        Basic Information:
            user (User): Story creator (ForeignKey to User)
            club (Club): Starting club (ForeignKey to Club)
            name (str): Story title/name
            slug (str): URL-friendly version of name
            status (str): Current story status (active/completed/abandoned)
            
        Game Settings:
            formation (str): Starting formation
            difficulty (str): Game difficulty level
            currency (str): Preferred currency for financial tracking
            
        Story Elements:
            challenge (str): Main challenge/objective
            background (str): Story background/context
                        
        Metadata:
            created_at (datetime): Creation timestamp
            updated_at (datetime): Last update timestamp
            is_public (bool): Story visibility setting
            view_count (int): Number of story views
            
    Methods:
        save(): Handles slug generation and timestamps
        get_absolute_url(): Returns story detail URL
        get_current_season(): Returns active season
        get_statistics(): Returns story statistics
    """

    # Status choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]

    # Difficulty choices
    DIFFICULTY_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('AMATEUR', 'Amateur'),
        ('SEMI-PRO', 'Semi-Pro'),
        ('PROFESSIONAL', 'Professional'),
        ('WORLD CLASS', 'World Class'),
        ('LEGENDARY', 'Legendary'),
        ('ULTIMATE', 'Ultimate'),
    ]

    # Currency choices
    CURRENCY_CHOICES = [
        ('EUR', '€ (Euro)'),
        ('GBP', '£ (British Pound)'),
        ('USD', '$ (US Dollar)'),
    ]

    # Basic Information
    user = models.ForeignKey (
        User,
        on_delete = models.CASCADE,
        related_name = 'stories'
    )
    club = models.ForeignKey (
        Club,
        on_delete = models.CASCADE,
        related_name = 'stories'
    )
    name = models.CharField (
        max_length = 200,
        help_text = "Give your story a memorable title"
    )
    slug = models.SlugField (
        max_length = 250,
        unique = True,
        blank = True
    )
    status = models.CharField (
        max_length = 20,
        choices = STATUS_CHOICES,
        default = 'ACTIVE'
    )

    # Game Settings
    formation = models.CharField (
        max_length = 10,
        help_text = "Starting formation (e.g., 4-4-2)"
    )
    difficulty = models.CharField (
        max_length = 20,
        choices = DIFFICULTY_CHOICES,
        default = 'PROFESSIONAL'
    )
    currency = models.CharField (
        max_length = 3,
        choices = CURRENCY_CHOICES,
        default = 'EUR'
    )

    # Story Elements
    challenge = models.TextField (
        help_text = "Describe your career mode challenge"
    )
    background = models.TextField (
        help_text = "Provide background context for your story",
        blank = True
    )

    # Metadata
    created_at = models.DateTimeField (auto_now_add = True)
    updated_at = models.DateTimeField (auto_now = True)
    is_public = models.BooleanField (
        default = True,
        help_text = "Make story visible to other users"
    )
    view_count = models.PositiveIntegerField (default = 0)

    class Meta:
        verbose_name = "Story"
        verbose_name_plural = "Stories"
        ordering = ['-created_at']
        indexes = [
            models.Index (fields = ['user', 'created_at']),
            models.Index (fields = ['status', 'is_public']),
        ]

    def __str__ (self):
        return f"{self.name} - {self.user.username}"

    def save (self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify (f"{self.name}-{self.user.username}")
        super ().save (*args, **kwargs)

    def get_absolute_url (self):
        return reverse ('story_detail', kwargs = {'slug': self.slug})

    def get_current_season (self):
        """Returns the current active season for this story"""
        return self.seasons.filter (is_current = True).first ()

    def get_statistics (self):
        """
        Returns dictionary with story statistics:
        - Total seasons
        - Trophies won
        - Top scorers
        - etc.
        """
        return {
            'total_seasons': self.seasons.count (),
            'trophies': self.competition_winners.count (),
            'transfers': self.transfers.count (),
            'current_season': self.get_current_season (),
        }

class Season (models.Model):
    """
    Represents a football season within a career mode story.

    Attributes:
        story (Story): The parent story to which this season belongs.
        name (str): Season identifier (e.g., "2024-2025").
        season_number (int): Sequential number of this season within the story.
        is_current (bool): Indicates if this is the currently active season.
        
        # Financial attributes
        transfer_budget (decimal): Available transfer budget for this season.
        wage_budget (decimal): Available wage budget for this season.
        
        # Team status
        league_position (int): Final or current league position.
        
        # Metadata
        created_at (datetime): When this record was created.
        updated_at (datetime): When this record was last updated.
        notes (text): Any additional notes about the season.

    Methods:
        get_statistics(): Returns aggregated season statistics.
        get_formations(): Returns frequently used formations.
        get_top_players(): Returns top performing players.
    """
    story = models.ForeignKey (
        Story, on_delete = models.CASCADE, related_name = 'seasons'
        )
    name = models.CharField (max_length = 10)  # e.g. "2024-2025"
    season_number = models.PositiveIntegerField (
        help_text = "Sequential number of this season in the story (1, 2, 3, "
                    "etc.)"
    )
    is_current = models.BooleanField (default = False)

    # Financial tracking
    transfer_budget = models.DecimalField (
        max_digits = 12,
        decimal_places = 2,
        null = True,
        blank = True,
        help_text = "Available transfer budget at start of season"
    )
    wage_budget = models.DecimalField (
        max_digits = 12,
        decimal_places = 2,
        null = True,
        blank = True,
        help_text = "Available wage budget at start of season"
    )

    # Team status
    league_position = models.PositiveIntegerField (
        null = True,
        blank = True,
        help_text = "Final or current league position"
    )

    # Metadata
    created_at = models.DateTimeField (auto_now_add = True)
    updated_at = models.DateTimeField (auto_now = True)
    notes = models.TextField (blank = True)

    class Meta:
        unique_together = [
            ['story', 'name'],
            ['story', 'season_number']
        ]
        ordering = ['season_number', 'name']
        indexes = [
            models.Index (fields = ['story', 'is_current']),
        ]

    def __str__ (self):
        return f"{self.story.club.name} - {self.name}"

    def get_statistics (self):
        """Returns aggregated season statistics"""
        pass
        # return {
        #     'matches_played': self.matches.count(),
        #     'wins': self.matches.filter(result='WIN').count(),
        #     'draws': self.matches.filter(result='DRAW').count(),
        #     'losses': self.matches.filter(result='LOSS').count(),
        #     'goals_for': sum(m.goals_for for m in self.matches.all()),
        #     'goals_against': sum(m.goals_against for m in self.matches.all()),
        #     'top_scorer': self.player_stats.order_by('-goals').first(),
        #     'top_assister': self.player_stats.order_by('-assists').first(),
        #     'trophies': self.competition_winners.count(),
        # }

    def get_formations (self):
        """Returns the most used formations during this season"""
        # Implementation would depend on having formation tracking
        pass

    def get_top_players (self, limit = 5):
        """Returns the top performing players by average rating"""
        return self.player_stats.order_by ('-average_rating')[:limit]

class Transfer (models.Model):
    """
    Represents a player transfer between clubs.

    Attributes:
        season (Season): The season during which the transfer occurred. This
        is a ForeignKey to the Season model with CASCADE delete and a
        related_name of 'transfers'.
        story (Story): The story to which the transfer belongs. This is a
        ForeignKey to the Story model with CASCADE delete and a related_name
        of 'seasons'.
        player (Player): The player being transferred. This is a ForeignKey
        to the Player model with CASCADE delete.
        from_club (Club): The club from which the player is being
        transferred. This is a ForeignKey to the Club model with CASCADE
        delete and a related_name of 'transfers_out'.
        to_club (Club): The club to which the player is being transferred.
        This is a ForeignKey to the Club model with CASCADE delete and a
        related_name of 'transfers_in'.
        fee (decimal): The transfer fee. This is a DecimalField with a
        maximum of 12 digits and 2 decimal places.
        fee_currency (str): The currency of the transfer fee. This is a
        CharField with a maximum length of 3 characters and a default value
        of 'EUR'.
        transfer_date (date): The date of the transfer. This is a DateField.
    
    Meta:
        unique_together (tuple): Ensures that the combination of season,
        player, from_club, and to_club is unique.
    """
    season = models.ForeignKey (
        Season, on_delete = models.CASCADE, related_name = 'transfers'
        )
    story = models.ForeignKey (
        Story, on_delete = models.CASCADE, related_name = 'transfers'
        )
    player = models.ForeignKey (Player, on_delete = models.CASCADE)
    from_club = models.ForeignKey (
        Club, on_delete = models.CASCADE, related_name = 'transfers_out'
        )
    to_club = models.ForeignKey (
        Club, on_delete = models.CASCADE, related_name = 'transfers_in'
        )
    fee = models.DecimalField (max_digits = 12, decimal_places = 2)
    fee_currency = models.CharField (max_length = 3, default = 'EUR')
    transfer_date = models.DateField ()

    class Meta:
        unique_together = ('season', 'player', 'from_club', 'to_club')

class PlayerStats (models.Model):
    """
    Represents the statistics of a player for a specific season.

    Attributes:
        story (Story): The story to which these statistics belong. ForeignKey
        to the Story model with CASCADE delete behavior.
        season (Season): The season during which these statistics were
        recorded. ForeignKey to the Season model with CASCADE delete behavior.
        player (Player): The player to whom these statistics belong.
        ForeignKey to the Player model with CASCADE delete behavior.
        overall_rating (int): The player's overall rating for this season.
        IntegerField with a default value of 0, validated to be between 0 and
        99.
        appearances (int): The total number of appearances made by the player
        across all competitions. IntegerField with a default value of 0,
        validated to be non-negative.
        goals (int): The total number of goals scored by the player.
        IntegerField with a default value of 0, validated to be non-negative,
        and indexed for sorting.
        assists (int): The total number of assists made by the player.
        IntegerField with a default value of 0, validated to be non-negative.
        clean_sheets (int): The total number of clean sheets kept by the
        player (mainly for goalkeepers). IntegerField with a default value of
        0, validated to be non-negative.
        red_cards (int): The number of red cards received by the player.
        IntegerField with a default value of 0, validated to be non-negative.
        yellow_cards (int): The number of yellow cards received by the
        player. IntegerField with a default value of 0, validated to be
        non-negative.
        average_rating (decimal): The player's average match rating out of
        10. DecimalField with a maximum of 4 digits and 2 decimal places,
        default value of 0.00, validated to be between 0 and 10, and indexed
        for sorting.

    Methods:
        aggregate_competition_stats(): Aggregates and returns the player's
        statistics from all competitions in the season.
        goals_per_game(): Calculates and returns the player's goals per game
        ratio.
        assists_per_game(): Calculates and returns the player's assists per
        game ratio.
        update_from_competitions(): Updates the player's aggregate statistics
        from competition statistics.

    Meta:
        unique_together (tuple): Ensures that the combination of season and
        player is unique.
        indexes (list): Database indexes for optimizing queries on frequently
        accessed fields.
    """
    story = models.ForeignKey (
        Story, on_delete = models.CASCADE, related_name = 'player_stats'
        )
    season = models.ForeignKey (
        Season, on_delete = models.CASCADE, related_name = 'player_stats'
        )
    player = models.ForeignKey (Player, on_delete = models.CASCADE)
    overall_rating = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0), MaxValueValidator (99)],
        help_text = "Player's overall rating for this season"
    )
    appearances = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Total number of appearances across all competitions"
    )
    goals = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        db_index = True,  # Add index for sorting
        help_text = "Total number of goals scored"
    )
    assists = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Total number of assists"
    )
    clean_sheets = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Total number of clean sheets (mainly for goalkeepers)"
    )
    red_cards = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Number of red cards received"
    )
    yellow_cards = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Number of yellow cards received"
    )
    average_rating = models.DecimalField (
        max_digits = 4,
        decimal_places = 2,
        default = 0.00,
        validators = [MinValueValidator (0), MaxValueValidator (10)],
        db_index = True,  # Add index for sorting
        help_text = "Average match rating out of 10"
    )

    class Meta:
        unique_together = ['season', 'player']
        indexes = [
            models.Index (fields = ['-goals']),
            models.Index (fields = ['-average_rating']),
            models.Index (fields = ['-assists']),
        ]

    def aggregate_competition_stats (self):
        """Aggregate stats from CompetitionPlayerStats"""
        competition_stats = self.competition_player_stats.all ()
        total_appearances = sum (stat.appearances for stat in competition_stats)
        total_goals = sum (stat.goals for stat in competition_stats)
        total_assists = sum (stat.assists for stat in competition_stats)
        total_clean_sheets = sum (
            stat.clean_sheets for stat in competition_stats
            )
        total_red_cards = sum (stat.red_cards for stat in competition_stats)
        total_yellow_cards = sum (
            stat.yellow_cards for stat in competition_stats
            )
        average_rating = sum (
            stat.average_rating for stat in competition_stats
            ) / len (
            competition_stats
        ) if competition_stats else 0

        return {
            'total_appearances': total_appearances,
            'total_goals': total_goals,
            'total_assists': total_assists,
            'total_clean_sheets': total_clean_sheets,
            'total_red_cards': total_red_cards,
            'total_yellow_cards': total_yellow_cards,
            'average_rating': average_rating,
        }

    @property
    def goals_per_game (self):
        """Calculate goals per game ratio"""
        return round (
            self.goals / self.appearances, 2
            ) if self.appearances > 0 else 0

    @property
    def assists_per_game (self):
        """Calculate assists per game ratio"""
        return round (
            self.assists / self.appearances, 2
            ) if self.appearances > 0 else 0

    def update_from_competitions (self):
        """Update aggregate stats from competition stats"""
        stats = self.aggregate_competition_stats ()
        for key, value in stats.items ():
            if hasattr (self, key):
                setattr (self, key, value)
        self.save ()

class CompetitionPlayerStats (models.Model):
    """
    Represents the statistics of a player for a specific competition.

    Attributes:
        story (Story): The story to which these statistics belong. ForeignKey
        to the Story model with CASCADE delete behavior.
        season (Season): The season during which these statistics were
        recorded. ForeignKey to the Season model with CASCADE delete behavior.
        competition (Competition): The competition in which these statistics
        were recorded. ForeignKey to the Competition model with CASCADE
        delete behavior.
        player (Player): The player to whom these statistics belong.
        ForeignKey to the Player model with CASCADE delete behavior.
        overall_rating (int): The player's overall rating in this
        competition. IntegerField with a default value of 0, validated to be
        between 0 and 99.
        appearances (int): The total number of appearances made by the player
        in this competition. IntegerField with a default value of 0,
        validated to be non-negative.
        goals (int): The total number of goals scored by the player in this
        competition. IntegerField with a default value of 0, validated to be
        non-negative, and indexed for sorting.
        assists (int): The total number of assists made by the player in this
        competition. IntegerField with a default value of 0, validated to be
        non-negative.
        clean_sheets (int): The total number of clean sheets kept by the
        player in this competition (mainly for goalkeepers). IntegerField
        with a default value of 0, validated to be non-negative.
        red_cards (int): The number of red cards received by the player in
        this competition. IntegerField with a default value of 0, validated
        to be non-negative.
        yellow_cards (int): The number of yellow cards received by the player
        in this competition. IntegerField with a default value of 0,
        validated to be non-negative.
        average_rating (decimal): The player's average match rating out of 10
        in this competition. DecimalField with a maximum of 4 digits and 2
        decimal places, default value of 0.00, validated to be between 0 and
        10, and indexed for sorting.

    Methods:
        goals_per_game(): Calculates and returns the player's goals per game
        ratio for this competition.

    Meta:
        unique_together (tuple): Ensures that the combination of season,
        competition, and player is unique.
        indexes (list): Database indexes for optimizing queries on frequently
        accessed fields.
    """
    story = models.ForeignKey (
        Story, on_delete = models.CASCADE,
        related_name = 'competition_player_stats'
        )
    season = models.ForeignKey (
        Season, on_delete = models.CASCADE,
        related_name = 'competition_player_stats'
        )
    competition = models.ForeignKey (
        Competition,
        on_delete = models.CASCADE,
        related_name = 'player_stats'  # Add related_name
    )
    player = models.ForeignKey (
        Player,
        on_delete = models.CASCADE,
        related_name = 'competition_stats'  # Add related_name
    )
    overall_rating = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0), MaxValueValidator (99)],
        help_text = "Player's overall rating in this competition"
    )
    appearances = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Number of appearances in this competition"
    )
    goals = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        db_index = True,
        help_text = "Goals scored in this competition"
    )
    assists = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Assists made in this competition"
    )
    clean_sheets = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Clean sheets in this competition"
    )
    red_cards = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Red cards in this competition"
    )
    yellow_cards = models.IntegerField (
        default = 0,
        validators = [MinValueValidator (0)],
        help_text = "Yellow cards in this competition"
    )
    average_rating = models.DecimalField (
        max_digits = 4,
        decimal_places = 2,
        default = 0.00,
        validators = [MinValueValidator (0), MaxValueValidator (10)],
        db_index = True,
        help_text = "Average match rating in this competition"
    )

    class Meta:
        unique_together = ['season', 'competition', 'player']
        indexes = [
            models.Index (fields = ['competition', '-goals']),
            models.Index (fields = ['competition', '-average_rating']),
            models.Index (fields = ['competition', '-assists']),
        ]

    @property
    def goals_per_game (self):
        """Calculate goals per game ratio for this competition"""
        return round (
            self.goals / self.appearances, 2
            ) if self.appearances > 0 else 0

class CompetitionWinner (models.Model):
    """
    Represents the winner of a competition for a specific season.

    Attributes:
        story (Story): The story to which the competition winner belongs.
        ForeignKey to the Story model with CASCADE delete behavior.
        season (Season): The season during which the competition was held.
        ForeignKey to the Season model with CASCADE delete behavior.
        competition (Competition): The competition that was won. ForeignKey
        to the Competition model with CASCADE delete behavior.
        winner (Club): The club that won the competition. ForeignKey to the
        Club model with CASCADE delete behavior.

    Meta:
        unique_together (tuple): Ensures that the combination of season and
        competition is unique.
    """
    story = models.ForeignKey (
        Story, on_delete = models.CASCADE, related_name = 'competition_winners'
        )
    season = models.ForeignKey (
        Season, on_delete = models.CASCADE, related_name = 'competition_winners'
        )
    competition = models.ForeignKey (Competition, on_delete = models.CASCADE)
    winner = models.ForeignKey (Club, on_delete = models.CASCADE)

    class Meta:
        unique_together = ['season', 'competition']

    def __str__ (self):
        return (f"{self.competition.name} - {self.season.name} Winner: "
                f"{self.winner.name}")

class AwardWinner (models.Model):
    """
    Represents the winner of an individual award for a specific season.

    Attributes:
        story (Story): The story to which the award winner belongs. This is a
        ForeignKey to the Story model with CASCADE delete and a related_name
        of 'seasons'.
        season (Season): The season during which the award was given. This is
        a ForeignKey to the Season model with CASCADE delete and a
        related_name of 'award_winners'.
        award (IndividualAward): The award that was won. This is a ForeignKey
        to the IndividualAward model with CASCADE delete.
        player (Player): The player who won the award. This is a ForeignKey
        to the Player model with CASCADE delete.
    
    Meta:
        unique_together (tuple): Ensures that the combination of season and
        award is unique.
    """
    story = models.ForeignKey(
        Story, on_delete=models.CASCADE, related_name='award_winners'
    )
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name='award_winners'
    )
    award = models.ForeignKey(IndividualAward, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'award'],
                name='unique_season_award'
            )
        ]
