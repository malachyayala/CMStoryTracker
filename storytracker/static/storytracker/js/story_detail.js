$(document).ready(function() {
    // Setup CSRF token for all AJAX requests
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
    let newStatId = -1;
    let newTransferId = -1;
    let clubPlayers = []; // Store club players for autocomplete
    let selectedPlayerId = null; // Track the currently selected player

    // Load players for the current club
    loadClubPlayers();
    
    // Handle season filter change
    $('#seasonFilter').change(function() {
        const seasonId = $(this).val();
        loadSeasonData(seasonId);
    });
    
    // Show quick add row
    $('#add-player-stats-btn').on('click', function() {
        $('#emptyStateRow').hide(); // Hide empty state if present
        $('#quickAddRow').show(); // Show the quick add row
        $('#playerSearch').focus(); // Focus on the player search
        
        // Reset the quick add form
        resetQuickAddForm();
    });
    
    // Handle player search input
    $('#playerSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        const resultsContainer = $('#playerSearchResults');
        resultsContainer.empty();
        
        if (searchTerm.length < 2) {
            resultsContainer.removeClass('show');
            return;
        }
        
        // Filter players by search term
        const filteredPlayers = clubPlayers.filter(player => 
            player.name.toLowerCase().includes(searchTerm)
        );
        
        // Show results
        if (filteredPlayers.length > 0) {
            filteredPlayers.forEach(player => {
                resultsContainer.append(
                    `<div class="player-search-item" data-player-id="${player.id}" data-player-overall="${player.overall}">
                        ${player.name} (${player.overall})
                    </div>`
                );
            });
            resultsContainer.addClass('show');
        } else {
            resultsContainer.removeClass('show');
        }
    });
    
    // Handle player selection from search results
    $(document).on('click', '.player-search-item', function() {
        const playerId = $(this).data('player-id');
        const playerName = $(this).text().trim();
        const playerOverall = $(this).data('player-overall');
        
        // Set selected player
        selectedPlayerId = playerId;
        $('#playerSearch').val(playerName);
        $('#quickAddOverall').val(playerOverall);
        
        // Hide results
        $('#playerSearchResults').removeClass('show');
        
        // Focus on the next field
        $('#quickAddApps').focus();
    });
    
    // Close search results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.player-search-container').length) {
            $('#playerSearchResults').removeClass('show');
        }
    });
    
    // Save player stats
    $('#savePlayerBtn, #saveAndAddBtn').on('click', function() {
        const isSaveAndAdd = $(this).attr('id') === 'saveAndAddBtn';
        
        // Validate input
        if (!validateQuickAddForm()) {
            return;
        }
        
        // Get form data
        const formData = {
            player_id: selectedPlayerId,
            season_id: $('#seasonFilter').val(),
            overall_rating: $('#quickAddOverall').val() || 70,
            appearances: $('#quickAddApps').val() || 0,
            goals: $('#quickAddGoals').val() || 0,
            assists: $('#quickAddAssists').val() || 0,
            clean_sheets: $('#quickAddCleanSheets').val() || 0,
            yellow_cards: $('#quickAddYellowCards').val() || 0,
            red_cards: $('#quickAddRedCards').val() || 0,
            average_rating: $('#quickAddAvgRating').val() || 0
        };
        
        // Disable buttons during save
        const buttons = $('#savePlayerBtn, #saveAndAddBtn, #cancelAddBtn');
        buttons.prop('disabled', true);
        
        $.ajax({
            url: ADD_PLAYER_STATS_URL,  // Use the JS variable
            type: "POST",
            data: formData,
            success: function(response) {
                if (response.success) {
                    // Flash effect for success
                    $('#quickAddRow').addClass('flash');
                    setTimeout(() => {
                        $('#quickAddRow').removeClass('flash');
                    }, 500);
                    
                    // Refresh the player stats table
                    loadSeasonData($('#seasonFilter').val());
                    
                    // Show success message
                    showAlert('Player statistics saved successfully!', 'success');
                    
                    // Remove any empty state row
                    $('#emptyStateRow').remove();
                    
                    // Create a consistent row structure matching your template
                    const newRow = `
                        <tr data-stat-id="${response.stat_id}" data-season="${formData.season_id}">
                            <td contenteditable="true" data-field="player" data-stat-id="${response.stat_id}" class="text-left">${response.player_name}</td>
                            <td contenteditable="true" data-field="overall_rating" data-stat-id="${response.stat_id}" class="text-center">${formData.overall_rating}</td>
                            <td contenteditable="true" data-field="appearances" data-stat-id="${response.stat_id}" class="text-center">${formData.appearances}</td>
                            <td contenteditable="true" data-field="goals" data-stat-id="${response.stat_id}" class="text-center">${formData.goals}</td>
                            <td contenteditable="true" data-field="assists" data-stat-id="${response.stat_id}" class="text-center">${formData.assists}</td>
                            <td contenteditable="true" data-field="clean_sheets" data-stat-id="${response.stat_id}" class="text-center">${formData.clean_sheets}</td>
                            <td contenteditable="true" data-field="yellow_cards" data-stat-id="${response.stat_id}" class="text-center">${formData.yellow_cards}</td>
                            <td contenteditable="true" data-field="red_cards" data-stat-id="${response.stat_id}" class="text-center">${formData.red_cards}</td>
                            <td contenteditable="true" data-field="average_rating" data-stat-id="${response.stat_id}" class="text-center">${formData.average_rating}</td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-danger delete-player-btn" data-stat-id="${response.stat_id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                    
                    // Either append the row or add before quick add row depending on your design
                    if ($('#quickAddRow').is(':visible')) {
                        $(newRow).insertBefore('#quickAddRow');
                    } else {
                        $('#playerStatsTable').append(newRow);
                    }
                    
                    // If this is just save (not save & add), hide the quick add row
                    if (!isSaveAndAdd) {
                        $('#quickAddRow').hide();
                    } else {
                        // Reset the form for adding another
                        resetQuickAddForm();
                        $('#playerSearch').focus();
                    }
                    
                    // Show success message
                    showAlert('Player statistics added successfully!', 'success');
                }
            },
            error: function(xhr) {
                showAlert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Failed to save player statistics'), 'danger');
            },
            complete: function() {
                // Re-enable buttons
                buttons.prop('disabled', false);
            }
        });
    });
    
    // Cancel adding player
    $('#cancelAddBtn').on('click', function() {
        $('#quickAddRow').hide();
        resetQuickAddForm();
        
        // Show empty state if no players
        if ($('#playerStatsTable tr:not(#quickAddRow)').length === 0 || 
            $('#playerStatsTable tr:not(#quickAddRow)').length === 1 && $('#emptyStateRow').length) {
            $('#emptyStateRow').show();
        }
    });
    
    // Delete player stats button
    $(document).on('click', '.delete-player-btn', function() {
        const statId = $(this).data('stat-id');
        const row = $(this).closest('tr');
        const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
        
        if (confirm('Are you sure you want to delete this player\'s statistics?')) {
            $.ajax({
                url: DELETE_PLAYER_STAT_URL,  // Use the JS variable
                type: "POST",
                data: JSON.stringify({
                    stat_id: statId
                }),
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                success: function(response) {
                    if (response.success) {
                        // Remove the row with animation
                        row.fadeOut(300, function() {
                            $(this).remove();
                            
                            // Show empty state if no players left
                            if ($('#playerStatsTable tr:not(#quickAddRow)').length === 0) {
                                $('#playerStatsTable').append(`
                                    <tr id="emptyStateRow">
                                        <td colspan="10" class="text-center">
                                            <div class="empty-state">
                                                <i class="fas fa-user-slash"></i>
                                                <p>No player statistics available for this season.</p>
                                            </div>
                                        </td>
                                    </tr>
                                `);
                            }
                        });
                        
                        showAlert('Player statistics deleted successfully!', 'success');
                    } else {
                        showAlert('Error: ' + (response.error || 'Failed to delete player statistics'), 'danger');
                    }
                },
                error: function() {
                    showAlert('Error deleting player statistics. Please try again.', 'danger');
                }
            });
        }
    });

    // Add Season button handler
    $('#addSeasonBtn').on('click', function() {
        const button = this;
        
        // Prevent duplicate submissions
        if (button.disabled) return;
        button.disabled = true;
        
        // Get the current seasons
        const seasonSelect = document.getElementById('seasonFilter');
        const seasons = Array.from(seasonSelect.options).map(opt => opt.text);
        const lastSeason = seasons[seasons.length - 1];
        
        // Parse the season name to generate the next one
        // This assumes seasons are in format "YY/YY" like "24/25"
        const [start, end] = lastSeason.split('/');
        const newStart = parseInt(start) + 1;
        const newEnd = parseInt(end) + 1;
        const newSeasonName = `${newStart}/${newEnd}`;
        
        $.ajax({
            url: ADD_SEASON_URL,  // Use the JS variable
            type: "POST",
            data: JSON.stringify({
                story_slug: STORY_SLUG,  // Use the JS variable
                season_name: newSeasonName,
                season_number: seasons.length + 1
            }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Add new season to dropdown
                    const option = document.createElement('option');
                    option.value = response.season_id;
                    option.text = newSeasonName;
                    seasonSelect.appendChild(option);
                    
                    // Select the new season
                    seasonSelect.value = response.season_id;
                    
                    // Load the new season's data
                    loadSeasonData(response.season_id);
                    
                    showAlert('New season added successfully!', 'success');
                } else {
                    showAlert(response.error || 'Unknown error occurred', 'danger');
                }
            },
            error: function(xhr) {
                showAlert('Error adding season. Please try again.', 'danger');
                console.error("Failed to add season:", xhr.responseText);
            },
            complete: function() {
                button.disabled = false;
            }
        });
    });

    // Function to load season data (stats, awards, transfers)
    function loadSeasonData(seasonId) {
        // Update all section headers with the season name
        $.ajax({
            url: `/api/seasons/${seasonId}/`,
            type: "GET",
            success: function(response) {
                if (response.success) {
                    $('.season-name').text(response.season.name);
                }
            }
        });
        
        // Load player stats
        loadPlayerStats(seasonId);
        
        // Hide quick add row when changing seasons
        $('#quickAddRow').hide();
        resetQuickAddForm();
    }
    
    // Function to load club players
    function loadClubPlayers() {
        $.ajax({
            url: `/api/clubs/${CLUB_ID}/players/`,  // Use the JS variable
            type: "GET",
            success: function(response) {
                clubPlayers = response.players;
            },
            error: function() {
                console.error("Failed to load players");
                showAlert('Failed to load club players. Please refresh the page.', 'danger');
            }
        });
    }
    
    // Function to load player stats for a specific season
    function loadPlayerStats(seasonId) {
        $.ajax({
            url: `/api/seasons/${seasonId}/player-stats/`,
            type: "GET",
            success: function(response) {
                const tableBody = $('#playerStatsTable');
                const quickAddRow = $('#quickAddRow').detach();
                tableBody.empty().append(quickAddRow);
                
                if (response.player_stats.length === 0) {
                    tableBody.append(`
                        <tr id="emptyStateRow">
                            <td colspan="10" class="text-center">
                                <div class="empty-state">
                                    <i class="fas fa-user-slash"></i>
                                    <p>No player statistics available for this season.</p>
                                </div>
                            </td>
                        </tr>
                    `);
                    return;
                }
                
                response.player_stats.forEach(function(stat) {
                    tableBody.append(`
                        <tr data-stat-id="${stat.id}" data-season="${seasonId}">
                            <td contenteditable="true" data-field="player" data-stat-id="${stat.id}" class="text-left">${stat.player_name}</td>
                            <td contenteditable="true" data-field="overall_rating" data-stat-id="${stat.id}" class="text-center">${stat.overall_rating}</td>
                            <td contenteditable="true" data-field="appearances" data-stat-id="${stat.id}" class="text-center">${stat.appearances}</td>
                            <td contenteditable="true" data-field="goals" data-stat-id="${stat.id}" class="text-center">${stat.goals}</td>
                            <td contenteditable="true" data-field="assists" data-stat-id="${stat.id}" class="text-center">${stat.assists}</td>
                            <td contenteditable="true" data-field="clean_sheets" data-stat-id="${stat.id}" class="text-center">${stat.clean_sheets}</td>
                            <td contenteditable="true" data-field="yellow_cards" data-stat-id="${stat.id}" class="text-center">${stat.yellow_cards}</td>
                            <td contenteditable="true" data-field="red_cards" data-stat-id="${stat.id}" class="text-center">${stat.red_cards}</td>
                            <td contenteditable="true" data-field="average_rating" data-stat-id="${stat.id}" class="text-center">${stat.average_rating}</td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-danger delete-player-btn" data-stat-id="${stat.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `);
                });
                
                setupContentEditableHandlers();
            },
            error: function() {
                console.error("Failed to load player stats");
                showAlert('Failed to load player statistics. Please refresh the page.', 'danger');
            }
        });
    }
    
    // Function to reset the quick add form
    function resetQuickAddForm() {
        $('#playerSearch').val('');
        $('#quickAddOverall').val('');
        $('#quickAddApps').val('');
        $('#quickAddGoals').val('');
        $('#quickAddAssists').val('');
        $('#quickAddCleanSheets').val('');
        $('#quickAddYellowCards').val('');
        $('#quickAddRedCards').val('');
        $('#quickAddAvgRating').val('');
        selectedPlayerId = null;
    }
    
    // Function to validate the quick add form
    function validateQuickAddForm() {
        // Check if a player is selected
        if (!selectedPlayerId) {
            showAlert('Please select a player from the dropdown.', 'danger');
            $('#playerSearch').focus();
            return false;
        }
        
        // Check if overall rating is valid
        const overall = $('#quickAddOverall').val();
        if (overall && (overall < 1 || overall > 99)) {
            showAlert('Overall rating must be between 1 and 99.', 'danger');
            $('#quickAddOverall').focus();
            return false;
        }
        
        // Check if average rating is valid
        const avgRating = $('#quickAddAvgRating').val();
        if (avgRating && (avgRating < 0 || avgRating > 10)) {
            showAlert('Average rating must be between 0 and 10.', 'danger');
            $('#quickAddAvgRating').focus();
            return false;
        }
        
        return true;
    }
    
    // Set up contenteditable handlers for player stats
    function setupContentEditableHandlers() {
        // Store original values when focusing
        $(document).off('focus', '[contenteditable="true"]').on('focus', '[contenteditable="true"]', function() {
            $(this).data('original-value', $(this).text().trim());
        });
        
        // Save on Enter key
        $(document).off('keydown', '[contenteditable="true"]').on('keydown', '[contenteditable="true"]', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                
                const statId = $(this).data('stat-id');
                const fieldName = $(this).data('field');
                const value = $(this).text().trim();
                
                // Save the field value
                savePlayerStatField(statId, fieldName, value, $(this));
                
                // Move focus to next cell if available
                const allCells = $('[contenteditable="true"]');
                const currentIndex = allCells.index(this);
                if (currentIndex < allCells.length - 1) {
                    allCells.eq(currentIndex + 1).focus();
                }
            }
        });
        
        // Save on blur (focus out) if value changed
        $(document).off('blur', '[contenteditable="true"]').on('blur', '[contenteditable="true"]', function() {
            const originalValue = $(this).data('original-value');
            const currentValue = $(this).text().trim();
            
            if (originalValue !== currentValue) {
                const statId = $(this).data('stat-id');
                const fieldName = $(this).data('field');
                
                savePlayerStatField(statId, fieldName, currentValue, $(this));
            }
        });
    }
    
    // Function to save a player stat field
    function savePlayerStatField(statId, fieldName, value, element) {
        // Visual feedback - saving
        element.css('background-color', '#f0f8ff');
        
        $.ajax({
            url: "/api/player-stats/update/",
            type: "POST",
            data: JSON.stringify({
                stat_id: statId,
                field: fieldName,
                value: value
            }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Success feedback
                    element.css('background-color', '#e6ffe6');
                    setTimeout(() => {
                        element.css('background-color', '');
                    }, 500);
                } else {
                    // Error feedback
                    element.css('background-color', '#ffe6e6');
                    showAlert('Error saving: ' + (response.error || 'Unknown error'), 'danger');
                    setTimeout(() => {
                        element.css('background-color', '');
                    }, 500);
                }
            },
            error: function() {
                // Error feedback
                element.css('background-color', '#ffe6e6');
                showAlert('Error saving change. Please try again.', 'danger');
                setTimeout(() => {
                    element.css('background-color', '');
                }, 500);
            }
        });
    }
    
    // Function to show alerts
    function showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        `;
        
        // Remove any existing alerts
        $('.alert').alert('close');
        
        // Add new alert
        $('body').append(alertHtml);
        
        // Auto dismiss after 3 seconds
        setTimeout(function() {
            $('.alert').alert('close');
        }, 3000);
    }

    // Initialize Bootstrap collapse for all cards
    $('.collapse').collapse({
        toggle: false
    });

    // Handle card header clicks
    $('.card-header').on('click', function(e) {
        e.preventDefault();
        const target = $(this).data('target');
        const icon = $(this).find('.collapse-icon');
        
        $(target).collapse('toggle');
        
        // Toggle the collapsed class and rotate icon
        $(this).toggleClass('collapsed');
        if ($(this).hasClass('collapsed')) {
            icon.css('transform', 'rotate(180deg)');
        } else {
            icon.css('transform', 'rotate(0deg)');
        }
    });

    // Initialize the page
    loadSeasonData($('#seasonFilter').val());
});