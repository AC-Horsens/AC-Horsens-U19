import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from datetime import datetime
from datetime import date
from fileinput import filename

def load_data():
    df_xg = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/xg.csv')
    
    events = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/events.csv')
    
    df_possession_stats = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/terr_poss.csv')
    
    df_xg_agg = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/xg.csv')
    
    penalty_area_entry_counts = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/penalty_area_entry_counts.csv')
    
    df_matchstats = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/matchstats.csv')
    
    df_ppda = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/ppda.csv')
    
    df_groundduels = pd.read_csv('C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/groundduels_per_player.csv')
    
    return df_xg ,events, df_possession_stats,df_xg_agg, penalty_area_entry_counts, df_matchstats, df_ppda, df_groundduels

def create_stacked_bar_chart(win_prob, draw_prob, loss_prob, title, filename):
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Define the colors for each segment
    colors = ['green', 'yellow', 'red']
    segments = [win_prob, draw_prob, loss_prob]
    labels = ['Win', 'Draw', 'Loss']
    
    # Plot the stacked bar segments
    left = 0
    for seg, color, label in zip(segments, colors, labels):
        ax.barh(0, seg, left=left, color=color, height=0.5, label=label)
        left += seg
    
    # Add text annotations for each segment
    left = 0
    for seg, color, label in zip(segments, colors, labels):
        ax.text(left + seg / 2, 0, f"{label}: {seg:.2f}", ha='center', va='center', fontsize=10, color='black', fontweight='bold')
        left += seg
    
    # Formatting
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.axis('off')
    plt.title(label=title, fontsize=12, fontweight='bold', y=1.2, va='top', loc='left')
    plt.savefig(filename, bbox_inches='tight', dpi=500)  # Use high DPI for better quality
    plt.close()

def create_bar_chart(value, title, filename, max_value, thresholds, annotations):
    fig, ax = plt.subplots(figsize=(8, 2))
    
    if value < thresholds[0]:
        bar_color = 'red'
    elif value < thresholds[1]:
        bar_color = 'orange'
    elif value < thresholds[2]:
        bar_color = 'yellow'
    else:
        bar_color = 'green'
    
    # Plot the full bar background
    ax.barh(0, max_value, color='lightgrey', height=0.5)
    
    # Plot the value bar with the determined color
    ax.barh(0, value, color=bar_color, height=0.5)
    # Plot the thresholds with annotations
    for threshold, color, annotation in zip(thresholds, ['red', 'yellow', 'green'], annotations):
        ax.axvline(threshold, color=color, linestyle='--', linewidth=1.5)
        ax.text(threshold, 0.3, f"{threshold:.2f}", ha='center', va='center', fontsize=10, color=color)
        ax.text(threshold, -0.3, annotation, ha='center', va='center', fontsize=10, color=color)
    
    # Add the text for title and value
    ax.text(value, -0.0, f"{value:.2f}", ha='center', va='center', fontsize=12, fontweight='bold', color='black')
        
    # Formatting
    ax.set_xlim(0, max_value)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.axis('off')
    plt.title(label=title, fontsize=12, fontweight='bold',y=1.2,va='top', loc='left')   
    plt.savefig(filename, bbox_inches='tight', dpi=500)  # Use high DPI for better quality
    plt.close()

def generate_cumulative_chart(df_xg_agg, column, title, filename):
    df = df_xg_agg
    df['cumulative_shot_xg'] = df.groupby('team.name')['shot.xg'].cumsum()
    
    plt.figure(figsize=(12, 6))
    for team in df['team.name'].unique():
        team_data = df[df['team.name'] == team]
        plt.plot(team_data['minute'], team_data[column], label=team)
    
    plt.xlabel('Time (minutes)')
    plt.title(f'Cumulative {title}')
    plt.legend()
    plt.savefig(filename, bbox_inches='tight', dpi=500)
    plt.close()

def generate_possession_chart(df_possession_stats, label,filename):
    df_possession_stats['minute'] = pd.to_numeric(df_possession_stats['minute'], errors='coerce')
    df_grouped = df_possession_stats.groupby(['label', 'minute','territorial_possession']).size().reset_index(name='territorial_possession_team')
    df_grouped = df_grouped[df_grouped['minute'] < 100]
    df_total_possessions = df_possession_stats.groupby(['label', 'minute']).size().reset_index(name='total_possessions')
    df_total_possessions = df_total_possessions[df_total_possessions['minute'] < 100]
    df_grouped = df_grouped.merge(df_total_possessions, on=['label', 'minute'])
    df_grouped['percentage_possession'] = (df_grouped['territorial_possession_team'] / df_grouped['total_possessions']) * 100
    df_grouped['rolling_avg_territorial_possession_team'] = df_grouped.groupby(['label', 'territorial_possession'])['percentage_possession'].rolling(window=10, min_periods=1).mean().reset_index(level=[0,1], drop=True)
    label = df_grouped['label'].iloc[0]
    # Plot the rolling average of percentages
    plt.figure(figsize=(10, 6))
    for team in df_grouped['territorial_possession'].unique():
        team_data = df_grouped[(df_grouped['label'] == label) & (df_grouped['territorial_possession'] == team)]
        if not team_data.empty:
            plt.plot(team_data['minute'], team_data['rolling_avg_territorial_possession_team'], label=f'{team}')
    x_ticks = np.arange(0, df_grouped['minute'].max() + 1, 5)
    
    # Plot the rolling average for the middle possession
    plt.xlabel('Minute')
    plt.ylabel('Territorial Possession (%) (Rolling Average)')
    plt.title(f'Territorial Possession ({label})')
    plt.legend()
    plt.grid(True)
    plt.xticks()  # Rotate x-axis labels for better readability
    plt.savefig(filename, bbox_inches='tight', dpi=500)
    plt.close()

def calculate_territorial_possession(df_possession_stats):
    df_possession_summary = df_possession_stats.groupby(['label','territorial_possession']).size().reset_index(name='territorial_possession_team')
    df_total_possessions = df_possession_stats.groupby(['label']).size().reset_index(name='total_possessions')
    df_possession_summary = df_possession_summary.merge(df_total_possessions, on=['label'])
    df_possession_summary['percentage_possession'] = (df_possession_summary['territorial_possession_team'] / df_possession_summary['total_possessions']) * 100
    df_possession_summary = df_possession_summary.groupby(['label','territorial_possession']).mean().reset_index()
    df_possession_summary = df_possession_summary[['label', 'territorial_possession', 'percentage_possession']]
    return df_possession_summary

def sliding_average_plot(df, window_size=3, filename=None):
    
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values(by='date')
    df_sorted = df_sorted.reset_index()
    #df_sorted['label'] = (df_sorted.index + 1).astype(str) + '. ' + df_sorted['label'].str[:-10]
    def shorten_labels(labels):
        return [label.split(',')[0] for label in labels]

    # Apply the shortening function to the 'label' column
    df_sorted['label'] = shorten_labels(df_sorted['label'])

    # Calculate the sliding average and cumulative average
    sliding_average = df_sorted['expected_points'].rolling(window=window_size).mean()
    cumulative_average = df_sorted['expected_points'].expanding().mean()

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 3))
    # Adjust the subplot to give more room for the x-axis labels
    fig.subplots_adjust(bottom=0.3)
    
    # Plot the sliding average line and cumulative average
    line1, = ax.plot(df_sorted['label'], sliding_average, color='blue', label='3-game rolling average')
    line2, = ax.plot(df_sorted['label'], cumulative_average, color='black', label='Cumulative Average')

    # Add horizontal lines and annotations
    line3 = ax.axhline(y=1.1, color='red', linestyle='--', label='Top 10')
    line4 = ax.axhline(y=1.5, color='yellow', linestyle='--', label='Top 6')
    line5 = ax.axhline(y=2.0, color='green', linestyle='--', label='Top 3')

    # Set y-axis limits
    ax.set_ylim(0, 3)

    # Add the first legend for sliding and cumulative averages
    legend1 = ax.legend(handles=[line1, line2], loc='upper left', bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=6)
    ax.add_artist(legend1)  # Add the first legend manually to the axes

    # Add the second legend for horizontal lines
    ax.legend(handles=[line3, line4, line5], loc='upper right', bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=6)

    # Set labels and title
    ax.set_ylabel('Expected Points',fontsize=6)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right', fontsize=6)

    # Show grid
    ax.grid(True)
    
    # Set the x-axis limits
    ax.set_xlim(df_sorted['label'].iloc[0], df_sorted['label'].iloc[-1])

    ax.axhspan(0, 1.1, color='red', alpha=0.6)  # Below relegation
    ax.axhspan(1.1, 1.5, color='orange', alpha=0.6)  # Between relegation and top 6
    ax.axhspan(1.5, 2.0, color='yellow', alpha=0.6)  # Between top 6 and promotion
    ax.axhspan(2.0, 3, color='green', alpha=0.6)  # Above promotion

    # Save the plot to a file if filename is provided
    if filename:
        plt.savefig(filename, format='png', dpi=500, bbox_inches='tight')
    else:
        plt.show()
        
def simulate_goals(values, num_simulations=100000):
    return np.random.binomial(1, values[:, np.newaxis], (len(values), num_simulations)).sum(axis=0)

def simulate_match(home_values, away_values, num_simulations=100000):
    home_goals_simulated = simulate_goals(home_values, num_simulations)
    away_goals_simulated = simulate_goals(away_values, num_simulations)
    
    home_wins = np.sum(home_goals_simulated > away_goals_simulated)
    draws = np.sum(home_goals_simulated == away_goals_simulated)
    away_wins = np.sum(home_goals_simulated < away_goals_simulated)
    
    home_points = (home_wins * 3 + draws) / num_simulations
    away_points = (away_wins * 3 + draws) / num_simulations
    
    home_win_prob = home_wins / num_simulations
    draw_prob = draws / num_simulations
    away_win_prob = away_wins / num_simulations
    
    return home_points, away_points, home_win_prob, draw_prob, away_win_prob

def calculate_expected_points(df, value_column):
    expected_points_list = []
    total_expected_points = {team: 0 for team in df['team.name'].unique()}
    
    matches = df.groupby('label')
    for label, match_df in matches:
        teams = match_df['team.name'].unique()
        if len(teams) == 2:
            home_team, away_team = teams
            home_values = match_df[match_df['team.name'] == home_team][value_column].values
            away_values = match_df[match_df['team.name'] == away_team][value_column].values
            
            home_points, away_points, home_win_prob, draw_prob, away_win_prob = simulate_match(home_values, away_values)
            match_date = match_df['date'].iloc[0]
            
            expected_points_list.append({
                'label': label,
                'date': match_date,
                'team.name': home_team,
                'expected_points': home_points, 
                'win_probability': home_win_prob, 
                'draw_probability': draw_prob, 
                'loss_probability': away_win_prob
            })
            expected_points_list.append({
                'label': label,
                'date': match_date,
                'team.name': away_team, 
                'expected_points': away_points, 
                'win_probability': away_win_prob, 
                'draw_probability': draw_prob, 
                'loss_probability': home_win_prob
            })
            
            total_expected_points[home_team] += home_points
            total_expected_points[away_team] += away_points
    
    expected_points_df = pd.DataFrame(expected_points_list)
    total_expected_points_df = pd.DataFrame(list(total_expected_points.items()), columns=['team.name', 'total_expected_points'])
    total_expected_points_df = total_expected_points_df.sort_values(by='total_expected_points', ascending=False)

    return expected_points_df, total_expected_points_df

def create_holdsummary(df_xg, df_matchstats,penalty_area_entry_counts,df_ppda):
    df_possession_summary = calculate_territorial_possession(df_possession_stats)
    df_possession_summary = df_possession_summary[['territorial_possession', 'label', 'percentage_possession']]
    df_possession_summary = df_possession_summary.rename(columns={'percentage_possession': 'terr_poss'})
    df_possession_summary = df_possession_summary.rename(columns={'territorial_possession': 'team.name'})
    df_xg_hold = df_xg.groupby(['team.name', 'label'])['shot.xg'].sum().reset_index()
    penalty_area_entry_counts = penalty_area_entry_counts.rename(columns={'count': 'penAreaEntries'})
    selected_columns = df_matchstats[['team.name', 'label', 'average_touchInBox']]
    touches_in_box = selected_columns.groupby(['team.name', 'label'])['average_touchInBox'].sum().reset_index()
    df_holdsummary = df_xg_hold.merge(df_possession_summary)
    df_holdsummary = df_holdsummary.merge(penalty_area_entry_counts)
    df_holdsummary = df_holdsummary.merge(touches_in_box)
    df_holdsummary = df_holdsummary.merge(df_ppda)
    df_holdsummary = df_holdsummary[['team.name', 'label', 'shot.xg','penAreaEntries','PPDA','terr_poss','average_touchInBox']]
    
    return df_holdsummary

def Process_data_spillere(events,df_xg,df_matchstats,groundduels):
    xg = events[['player.name','label','shot.xg']]
    xg['shot.xg'] = xg['shot.xg'].astype(float)
    xg = xg.groupby(['player.name','label']).sum().reset_index()
    df_scouting = xg.merge(df_matchstats, on=['player.name', 'label'], how='inner')
    def calculate_score(df, column, score_column):
        df_unique = df.drop_duplicates(column).copy()
        df_unique.loc[:, score_column] = pd.qcut(df_unique[column], q=10, labels=False, duplicates='raise') + 1
        return df.merge(df_unique[[column, score_column]], on=column, how='left')
    
    def calculate_opposite_score(df, column, score_column):
        df_unique = df.drop_duplicates(column).copy()
        df_unique.loc[:, score_column] = pd.qcut(-df_unique[column], q=10, labels=False, duplicates='raise') + 1
        return df.merge(df_unique[[column, score_column]], on=column, how='left')
    minutter_kamp = 45
    minutter_total = 160
    
    df_matchstats = df_matchstats[['player.name','team.name','label','position_codes','total_minutesOnField','average_successfulPassesToFinalThird','percent_aerialDuelsWon','percent_newSuccessfulDribbles','average_throughPasses','percent_duelsWon','percent_successfulPassesToFinalThird','average_xgAssist','average_crosses','average_progressivePasses','average_progressiveRun','average_accelerations','average_passesToFinalThird','percent_successfulProgressivePasses','percent_successfulPasses','average_ballRecoveries','average_interceptions','average_defensiveDuels','average_successfulDefensiveAction','average_forwardPasses','average_successfulForwardPasses','average_touchInBox','average_xgShot','average_keyPasses','average_successfulAttackingActions','average_shotAssists','average_losses']]
    df_scouting = df_xg.merge(df_matchstats,how='right')
    df_scouting = groundduels.merge(df_scouting,on=['player.name','team.name', 'label'],how='right')
    df_scouting['penAreaEntries_per90&crosses%shotassists'] = ((df_scouting['average_passesToFinalThird'].astype(float)+df_scouting['average_crosses'].astype(float) + df_scouting['average_xgAssist'].astype(float))/ df_scouting['total_minutesOnField'].astype(float)) * 90

    df_scouting.fillna(0, inplace=True)
    df_scouting = df_scouting.drop_duplicates(subset=['player.name', 'team.name', 'position_codes','label'])

    def calculate_match_xg(df_scouting):
        # Calculate the total match_xg for each match_id
        df_scouting['match_xg'] = df_scouting.groupby('label')['shot.xg'].transform('sum')
        
        # Calculate the total team_xg for each team in each match
        df_scouting['team_xg'] = df_scouting.groupby(['team.name', 'label'])['shot.xg'].transform('sum')
        
        # Calculate opponents_xg as match_xg - team_xg
        df_scouting['opponents_xg'] = df_scouting['match_xg'] - df_scouting['team_xg']
        df_scouting['opponents_xg'] = pd.to_numeric(df_scouting['opponents_xg'], errors='coerce')
       
        return df_scouting

    df_scouting = calculate_match_xg(df_scouting)
    df_scouting.fillna(0, inplace=True)

    def ball_playing_central_defender():
        df_spillende_stopper = df_scouting[df_scouting['player_codes'].str.contains('cb')]
        df_spillende_stopper['total_minutesOnField'] = df_spillende_stopper['total_minutesOnField'].astype(int)
        df_spillende_stopper = df_spillende_stopper[df_spillende_stopper['total_minutesOnField'].astype(int) >= minutter_kamp]
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'percent_duelsWon', 'percent_duelsWon score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'average_interceptions', 'average_interceptions score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'average_ballRecoveries', 'average_ballRecoveries score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'average_successfulAttackingActions', 'average_successfulAttackingActions score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'percent_aerialDuelsWon', 'percent_aerialDuelsWon score')

        df_spillende_stopper['Passing'] = df_spillende_stopper[['percent_successfulPasses score', 'percent_successfulPasses score']].mean(axis=1)
        df_spillende_stopper['Forward passing'] = df_spillende_stopper[['percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_spillende_stopper['Defending'] = df_spillende_stopper[['percent_duelsWon score', 'average_interceptions score', 'average_interceptions score', 'average_ballRecoveries score']].mean(axis=1)
        df_spillende_stopper['Possession value added'] = df_spillende_stopper['average_successfulAttackingActions score']
        
        df_spillende_stopper['Total score'] = df_spillende_stopper[['Passing','Passing','Forward passing','Forward passing','Forward passing','Defending','Defending','Possession value added','Possession value added','Possession value added']].mean(axis=1)
        df_spillende_stopper = df_spillende_stopper[['player.name','team.name','position_codes','label','total_minutesOnField','Passing','Forward passing','Defending','Possession value added score','Total score']] 
        df_spillende_stoppertotal = df_spillende_stopper[['player.name','team.name','position_codes','total_minutesOnField','Passing','Forward passing','Defending','Possession value added score','Total score']]
        df_spillende_stoppertotal = df_spillende_stoppertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_spillende_stopper.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_spillende_stoppertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_spillende_stopper = df_spillende_stopper.sort_values('Total score',ascending = False)
        df_spillende_stoppertotal = df_spillende_stoppertotal[['player.name','team.name','position_codes','total_minutesOnField total','Passing','Forward passing','Defending','Possession value added score','Total score']]
        df_spillende_stoppertotal = df_spillende_stoppertotal[df_spillende_stoppertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_spillende_stoppertotal = df_spillende_stoppertotal.sort_values('Total score',ascending = False)
        return df_spillende_stopper
  
  
    def defending_central_defender():
        df_forsvarende_stopper = df_scouting[df_scouting['player_codes'].str.contains('cb')]
        df_forsvarende_stopper['total_minutesOnField'] = df_forsvarende_stopper['total_minutesOnField'].astype(int)
        df_forsvarende_stopper = df_forsvarende_stopper[df_forsvarende_stopper['total_minutesOnField'].astype(int) >= minutter_kamp]
        
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'percent_duelsWon', 'percent_duelsWon score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'average_interceptions', 'average_interceptions score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'average_ballRecoveries', 'ballRecovery score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper,'percent_aerialDuelsWon', 'percent_aerialDuelsWon score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'average_successfulAttackingActions', 'average_successfulAttackingActions score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'percent_successfulPasses', 'percent_successfulPasses score')


        df_forsvarende_stopper['Defending'] = df_forsvarende_stopper[['percent_duelsWon score','percent_aerialDuelsWon score', 'average_interceptions score', 'average_interceptions score', 'ballRecovery score']].mean(axis=1)
        df_forsvarende_stopper['Duels'] = df_forsvarende_stopper[['percent_duelsWon score','percent_duelsWon score','percent_aerialDuelsWon score']].mean(axis=1)
        df_forsvarende_stopper['Intercepting'] = df_forsvarende_stopper[['average_interceptions score','average_interceptions score','ballRecovery score']].mean(axis=1)
        df_forsvarende_stopper['Passing'] = df_forsvarende_stopper[['percent_successfulPasses score', 'percent_successfulPasses score','average_successfulAttackingActions score','average_successfulAttackingActions score']].mean(axis=1)
        df_forsvarende_stopper['Total score'] = df_forsvarende_stopper[['Defending','Defending','Defending','Defending','Duels','Duels','Duels','Intercepting','Intercepting','Intercepting','Passing','Passing']].mean(axis=1)

        df_forsvarende_stopper = df_forsvarende_stopper[['player.name','team.name','position_codes','label','total_minutesOnField','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stopper[['player.name','team.name','position_codes','total_minutesOnField','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_forsvarende_stopper.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_forsvarende_stoppertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_forsvarende_stopper = df_forsvarende_stopper.sort_values('Total score',ascending = False)
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal[df_forsvarende_stoppertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal.sort_values('Total score',ascending = False)
        return df_forsvarende_stopper

    def balanced_central_defender():
        df_balanced_central_defender = df_scouting[df_scouting['position_codes'].str.contains('cb')]
        df_balanced_central_defender['total_minutesOnField'] = df_balanced_central_defender['total_minutesOnField'].astype(int)
        df_balanced_central_defender = df_balanced_central_defender[df_balanced_central_defender['total_minutesOnField'].astype(int) >= minutter_kamp]
        df_balanced_central_defender = calculate_opposite_score(df_balanced_central_defender,'opponents_xg', 'opponents xg score')
        
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'totalDuels', 'totalDuels score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_duelsWon', 'percent_duelsWon score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_interceptions', 'average_interceptions score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_ballRecoveries', 'ballRecovery score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'percent_aerialDuelsWon', 'percent_aerialDuelsWon score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_progressivePasses', 'average_progressivePasses score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')
        df_balanced_central_defender = calculate_opposite_score(df_balanced_central_defender,'average_losses','average_losses score')

        df_balanced_central_defender['Defending'] = df_balanced_central_defender[['percent_duelsWon score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','stoppedProgressPercentage score','opponents xg score','opponents xg score','percent_aerialDuelsWon score', 'average_interceptions score', 'average_interceptions score', 'ballRecovery score']].mean(axis=1)
        df_balanced_central_defender['Possession value added'] = df_balanced_central_defender[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score','average_progressivePasses score','average_losses score']].mean(axis=1)
        df_balanced_central_defender['Passing'] = df_balanced_central_defender[['percent_successfulPasses score', 'percent_successfulPasses score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_balanced_central_defender['Total score'] = df_balanced_central_defender[['Defending','Defending','Possession value added','Passing']].mean(axis=1)

        df_balanced_central_defender = df_balanced_central_defender[['player.name','team.name','position_codes','label','total_minutesOnField','Defending','Possession value added','Passing','Total score']]
        
        df_balanced_central_defendertotal = df_balanced_central_defender[['player.name','team.name','position_codes','total_minutesOnField','Defending','Possession value added','Passing','Total score']]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_balanced_central_defender.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_balanced_central_defendertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_balanced_central_defender = df_balanced_central_defender.sort_values('Total score',ascending = False)
        df_balanced_central_defendertotal = df_balanced_central_defendertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending','Possession value added','Passing','Total score']]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal[df_balanced_central_defendertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal.sort_values('Total score',ascending = False)
        return df_balanced_central_defender
    
    def fullbacks():
        df_backs = df_scouting[(df_scouting['position_codes'].str.contains('rb') |df_scouting['position_codes'].str.contains('lb') |df_scouting['position_codes'].str.contains('lwb') |df_scouting['position_codes'].str.contains('rwb'))]        
        df_backs['total_minutesOnField'] = df_backs['total_minutesOnField'].astype(int)
        df_backs = df_backs[df_backs['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_backs = calculate_score(df_backs,'totalDuels', 'totalDuels score')
        df_backs = calculate_score(df_backs,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_backs = calculate_score(df_backs,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_backs = calculate_opposite_score(df_backs,'opponents_xg', 'opponents xg score')
        df_backs = calculate_score(df_backs,'average_successfulAttackingActions', 'Possession value added score')
        df_backs = calculate_score(df_backs, 'percent_duelsWon', 'percent_duelsWon score')
        df_backs = calculate_score(df_backs, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_backs = calculate_score(df_backs, 'penAreaEntries_per90&crosses%shotassists', 'Penalty area entries & crosses & shot assists score')
        df_backs = calculate_score(df_backs, 'average_shotAssists', 'average_shotAssists score')
        df_backs = calculate_score(df_backs, 'average_interceptions', 'interception_per90 score')
        df_backs = calculate_score(df_backs, 'average_interceptions', 'average_interceptions score')
        df_backs = calculate_score(df_backs, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_backs = calculate_score(df_backs, 'average_crosses', 'average_crosses_per90 score')
        df_backs = calculate_score(df_backs, 'average_progressivePasses', 'average_progressivePasses score')
        df_backs = calculate_score(df_backs, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')
        df_backs = calculate_score(df_backs, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_backs = calculate_opposite_score(df_backs,'average_losses','average_losses score')

        df_backs['Defending'] = df_backs[['percent_duelsWon score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','percent_duelsWon score','average_interceptions score','opponents xg score']].mean(axis=1)
        df_backs['Passing'] = df_backs[['percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulPasses score','percent_successfulPasses score','Possession value added score','average_losses score']].mean(axis=1)
        df_backs['Chance creation'] = df_backs[['Penalty area entries & crosses & shot assists score','average_crosses_per90 score','average_crosses_per90 score','percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','Possession value added score','Possession value added score']].mean(axis=1)
        df_backs['Possession value added'] = df_backs[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score','average_losses score']].mean(axis=1)
        
        df_backs = calculate_score(df_backs, 'Defending', 'Defending_')
        df_backs = calculate_score(df_backs, 'Passing', 'Passing_')
        df_backs = calculate_score(df_backs, 'Chance creation','Chance_creation')
        df_backs = calculate_score(df_backs, 'Possession value added', 'Possession_value_added')
        
        df_backs['Total score'] = df_backs[['Defending_','Defending_','Defending_','Defending_','Passing_','Passing_','Chance_creation','Chance_creation','Chance_creation','Possession_value_added','Possession_value_added','Possession_value_added']].mean(axis=1)
        df_backs = df_backs[['player.name','team.name','position_codes','label','total_minutesOnField','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backs = df_backs.dropna()
        df_backstotal = df_backs[['player.name','team.name','position_codes','total_minutesOnField','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backstotal = df_backstotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_backs.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_backstotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_backs = df_backs.sort_values('Total score',ascending = False)
        df_backstotal = df_backstotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backstotal = df_backstotal[df_backstotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_backstotal = df_backstotal.sort_values('Total score',ascending = False)
        return df_backs
    
    def number6():
        df_sekser = df_scouting[(df_scouting['position_codes'].str.contains('dmf'))]
        df_sekser['total_minutesOnField'] = df_sekser['total_minutesOnField'].astype(int)
        df_sekser = df_sekser[df_sekser['total_minutesOnField'].astype(int) >= minutter_kamp]


        df_sekser = calculate_score(df_sekser,'totalDuels', 'totalDuels score')
        df_sekser = calculate_score(df_sekser,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_sekser = calculate_score(df_sekser,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_sekser = calculate_opposite_score(df_sekser,'opponents_xg', 'opponents xg score')
        df_sekser = calculate_score(df_sekser,'average_successfulAttackingActions', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'percent_duelsWon', 'percent_duelsWon score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'average_interceptions', 'average_interceptions score')
        df_sekser = calculate_score(df_sekser, 'average_forwardPasses', 'average_forwardPasses score')
        df_sekser = calculate_score(df_sekser, 'average_successfulForwardPasses', 'average_successfulForwardPasses score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'ballRecovery score')
        df_sekser = calculate_score(df_sekser, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')
        df_sekser = calculate_score(df_sekser, 'average_progressivePasses', 'average_progressivePasses score')
        df_sekser = calculate_opposite_score(df_sekser,'average_losses','average_losses score')
        
        
        df_sekser['Defending'] = df_sekser[['percent_duelsWon score','opponents xg score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','average_interceptions score','average_interceptions score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['percent_successfulPasses score','percent_successfulPasses score','percent_successfulPasses score','average_losses score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['average_progressivePasses score','average_forwardPasses score','average_successfulForwardPasses score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser[['average_losses score','average_successfulPassesToFinalThird score','average_progressivePasses score','average_progressivePasses score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score']].mean(axis=1)
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_', 'Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['player.name','team.name','position_codes','label','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()
        df_seksertotal = df_sekser[['player.name','team.name','position_codes','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_sekser.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_seksertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_sekser = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser

    def number6_destroyer():
        df_sekser = df_scouting[(df_scouting['position_codes'].str.conitans('dmf'))]
        df_sekser['total_minutesOnField'] = df_sekser['total_minutesOnField'].astype(int)
        df_sekser = df_sekser[df_sekser['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_sekser = calculate_score(df_sekser,'average_successfulAttackingActions', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'percent_duelsWon', 'percent_duelsWon score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_interceptions', 'average_interceptions score')
        df_sekser = calculate_score(df_sekser, 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'ballRecovery score')

        
        df_sekser['Defending'] = df_sekser[['percent_duelsWon score','average_interceptions score','average_interceptions score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['percent_successfulPasses score','percent_successfulPasses score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['Possession value added score','Possession value added score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser['Possession value added score']
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_','Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['player.name','team.name','position_codes','label','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()

        df_seksertotal = df_sekser[['player.name','team.name','position_codes','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_sekser.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_seksertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_sekser_destroyer = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser_destroyer
    
    def number6_double_6_forward():
        df_sekser = df_scouting[(df_scouting['position_codes'].str.conitans('dmf'))]
        df_sekser['total_minutesOnField'] = df_sekser['total_minutesOnField'].astype(int)
        df_sekser = df_sekser[df_sekser['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_sekser = calculate_score(df_sekser,'average_successfulAttackingActions', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'percent_duelsWon', 'percent_duelsWon score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_interceptions', 'average_interceptions score')
        df_sekser = calculate_score(df_sekser, 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'ballRecovery score')

        
        df_sekser['Defending'] = df_sekser[['percent_duelsWon score','average_interceptions score','average_interceptions score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['percent_successfulPasses score','percent_successfulPasses score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['Possession value added score','Possession value added score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser['Possession value added score']
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Progressive_ball_movement','Possession_value_added','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['player.name','team.name','position_codes','label','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()
        df_seksertotal = df_sekser[['player.name','team.name','position_codes','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_sekser.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_seksertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_sekser_double_6_forward = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser_double_6_forward
    
    def number8():
        df_otter = df_scouting[(df_scouting['position_codes'].str.contains('cmf'))]
        df_otter['total_minutesOnField'] = df_otter['total_minutesOnField'].astype(int)
        df_otter = df_otter[df_otter['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_otter = calculate_score(df_otter,'average_successfulAttackingActions','Possession value total score')
        df_otter = calculate_score(df_otter,'average_successfulAttackingActions', 'Possession value score')
        df_otter = calculate_score(df_otter,'average_successfulAttackingActions', 'Possession value added score')
        df_otter = calculate_score(df_otter, 'percent_duelsWon', 'percent_duelsWon score')
        df_otter = calculate_score(df_otter, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_otter = calculate_score(df_otter, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_otter = calculate_score(df_otter, 'average_interceptions', 'average_interceptions score')
        df_otter = calculate_score(df_otter, 'average_ballRecoveries', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_otter = calculate_score(df_otter, 'average_passesToFinalThird', 'average_passesToFinalThird score')
        df_otter = calculate_score(df_otter, 'average_shotAssists','average_shotAssists score')
        df_otter = calculate_score(df_otter, 'average_touchInBox','average_touchInBox score')
        df_otter = calculate_score(df_otter, 'average_progressivePasses', 'average_progressivePasses score')
        df_otter = calculate_score(df_otter, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_otter = calculate_score(df_otter, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')


        df_otter['Defending'] = df_otter[['percent_duelsWon score','possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score']].mean(axis=1)
        df_otter['Passing'] = df_otter[['percent_successfulPassesToFinalThird score','percent_successfulPasses score']].mean(axis=1)
        df_otter['Progressive ball movement'] = df_otter[['average_shotAssists score','average_progressivePasses score','average_touchInBox score','percent_successfulPassesToFinalThird score','Possession value total score']].mean(axis=1)
        df_otter['Possession value'] = df_otter[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score']].mean(axis=1)
        
        df_otter = calculate_score(df_otter, 'Defending', 'Defending_')
        df_otter = calculate_score(df_otter, 'Passing', 'Passing_')
        df_otter = calculate_score(df_otter, 'Progressive ball movement','Progressive_ball_movement')
        df_otter = calculate_score(df_otter, 'Possession value', 'Possession_value')
        
        df_otter['Total score'] = df_otter[['Defending_','Passing_','Passing_','Progressive_ball_movement','Progressive_ball_movement','Possession_value','Possession_value','Possession_value']].mean(axis=1)
        df_otter = df_otter[['player.name','team.name','position_codes','label','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]
        df_otter = df_otter.dropna()

        df_ottertotal = df_otter[['player.name','team.name','position_codes','total_minutesOnField','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]

        df_ottertotal = df_ottertotal.groupby(['player.name','team.name','position_codes']).mean().reset_index()
        minutter = df_otter.groupby(['player.name', 'team.name','position_codes'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_ottertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_otter = df_otter.sort_values('Total score',ascending = False)
        df_ottertotal = df_ottertotal[['player.name','team.name','position_codes','total_minutesOnField total','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]
        df_ottertotal= df_ottertotal[df_ottertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_ottertotal = df_ottertotal.sort_values('Total score',ascending = False)
        return df_otter
        
    def number10():
        df_10 = df_scouting[(df_scouting['position_codes'].str.contains('amf'))]
        df_10['total_minutesOnField'] = df_10['total_minutesOnField'].astype(int)
        df_10 = df_10[df_10['total_minutesOnField'].astype(int) >= minutter_kamp]
        
        df_10 = calculate_score(df_10,'average_successfulAttackingActions','Possession value total score')
        df_10 = calculate_score(df_10,'average_successfulAttackingActions', 'Possession value score')
        df_10 = calculate_score(df_10,'average_successfulAttackingActions', 'Possession value added score')
        df_10 = calculate_score(df_10, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_10 = calculate_score(df_10, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_10 = calculate_score(df_10, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_10 = calculate_score(df_10, 'average_progressivePasses', 'average_progressivePasses score')
        df_10 = calculate_score(df_10, 'average_shotAssists','average_shotAssists score')
        df_10 = calculate_score(df_10, 'average_touchInBox','average_touchInBox score')
        df_10 = calculate_score(df_10, 'percent_newSuccessfulDribbles','percent_newSuccessfulDribbles score')
        df_10 = calculate_score(df_10, 'average_throughPasses','average_throughPasses score')
        df_10 = calculate_score(df_10, 'average_keyPasses','average_keyPasses score')
        df_10 = calculate_score(df_10, 'shot.xg','shot.xg score')


        df_10['Passing'] = df_10[['percent_successfulPassesToFinalThird score','percent_successfulPasses score']].mean(axis=1)
        df_10['Chance creation'] = df_10[['average_shotAssists score','average_touchInBox score','percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','Possession value total score','Possession value score','average_progressivePasses score','percent_newSuccessfulDribbles score','average_touchInBox score','average_throughPasses score','average_keyPasses score']].mean(axis=1)
        df_10['Goalscoring'] = df_10[['average_touchInBox score','shot.xg score','shot.xg score','shot.xg score']].mean(axis=1)
        df_10['Possession value'] = df_10[['Possession value total score','Possession value total score','Possession value added score','Possession value score','Possession value score','Possession value score']].mean(axis=1)
                
        df_10 = calculate_score(df_10, 'Passing', 'Passing_')
        df_10 = calculate_score(df_10, 'Chance creation','Chance_creation')
        df_10 = calculate_score(df_10, 'Goalscoring','Goalscoring_')        
        df_10 = calculate_score(df_10, 'Possession value', 'Possession_value')
        
        df_10['Total score'] = df_10[['Passing_','Chance_creation','Chance_creation','Chance_creation','Goalscoring_','Goalscoring_','Possession_value','Possession_value']].mean(axis=1)
        df_10 = df_10[['player.name','team.name','label','total_minutesOnField','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10 = df_10.dropna()
        df_10total = df_10[['player.name','team.name','total_minutesOnField','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]

        df_10total = df_10total.groupby(['player.name','team.name']).mean().reset_index()
        minutter = df_10.groupby(['player.name', 'team.name'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_10total['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_10 = df_10.sort_values('Total score',ascending = False)
        df_10total = df_10total[['player.name','team.name','total_minutesOnField total','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10total= df_10total[df_10total['total_minutesOnField total'].astype(int) >= minutter_total]
        df_10total = df_10total.sort_values('Total score',ascending = False)
        return df_10
    
    def winger():
        df_10 = df_scouting[(df_scouting['position_codes'].str.contains('lw')) | (df_scouting['position_codes'].str.contains('rw'))| (df_scouting['position_codes'].str.contains('lamf'))| (df_scouting['position_codes'].str.contains('ramf'))] 
        df_10['total_minutesOnField'] = df_10['total_minutesOnField'].astype(int)
        df_10 = df_10[df_10['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_10 = calculate_score(df_10,'average_successfulAttackingActions','Possession value total score')
        df_10 = calculate_score(df_10,'average_successfulAttackingActions', 'Possession value score')
        df_10 = calculate_score(df_10,'average_successfulAttackingActions', 'Possession value added score')
        df_10 = calculate_score(df_10,'average_progressiveRun', 'progressiveRun score')
        df_10 = calculate_score(df_10, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_10 = calculate_score(df_10, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_10 = calculate_score(df_10, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_10 = calculate_score(df_10, 'average_progressivePasses', 'average_progressivePasses score')
        df_10 = calculate_score(df_10, 'average_shotAssists','average_shotAssists score')
        df_10 = calculate_score(df_10, 'average_touchInBox','average_touchInBox score')
        df_10 = calculate_score(df_10, 'percent_newSuccessfulDribbles','percent_newSuccessfulDribbles score')
        df_10 = calculate_score(df_10, 'average_throughPasses','average_throughPasses score')
        df_10 = calculate_score(df_10, 'average_keyPasses','average_keyPasses score')
        df_10 = calculate_score(df_10, 'shot.xg','shot.xg score')


        df_10['Passing'] = df_10[['percent_successfulPassesToFinalThird score','percent_successfulPasses score']].mean(axis=1)
        df_10['Chance creation'] = df_10[['progressiveRun score','average_shotAssists score','average_touchInBox score','percent_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','Possession value total score','Possession value score','percent_newSuccessfulDribbles score','percent_newSuccessfulDribbles score','percent_newSuccessfulDribbles score','average_touchInBox score','average_throughPasses score','average_keyPasses score','average_keyPasses score','average_keyPasses score']].mean(axis=1)
        df_10['Goalscoring'] = df_10[['average_touchInBox','shot.xg score','shot.xg score','shot.xg score']].mean(axis=1)
        df_10['Possession value'] = df_10[['Possession value total score','Possession value total score','Possession value added score','Possession value score','Possession value score','Possession value score']].mean(axis=1)
                
        df_10 = calculate_score(df_10, 'Passing', 'Passing_')
        df_10 = calculate_score(df_10, 'Chance creation','Chance_creation')
        df_10 = calculate_score(df_10, 'Goalscoring','Goalscoring_')        
        df_10 = calculate_score(df_10, 'Possession value', 'Possession_value')
        
        df_10['Total score'] = df_10[['Passing_','Chance_creation','Chance_creation','Chance_creation','Chance_creation','Goalscoring_','Goalscoring_','Goalscoring_','Goalscoring_','Possession_value','Possession_value','Possession_value','Possession_value']].mean(axis=1)
        df_10 = df_10[['player.name','team.name','label','total_minutesOnField','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10 = df_10.dropna()
        df_10total = df_10[['player.name','team.name','total_minutesOnField','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]

        df_10total = df_10total.groupby(['player.name','team.name']).mean().reset_index()
        minutter = df_10.groupby(['player.name', 'team.name'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_10total['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_kant = df_10.sort_values('Total score',ascending = False)
        df_10total = df_10total[['player.name','team.name','total_minutesOnField total','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10total= df_10total[df_10total['total_minutesOnField total'].astype(int) >= minutter_total]
        df_10total = df_10total.sort_values('Total score',ascending = False)
        return df_kant
    
    def Classic_striker():
        df_striker = df_scouting[(df_scouting['position_codes'].str.contains('cf'))]
        df_striker['total_minutesOnField'] = df_striker['total_minutesOnField'].astype(int)
        df_striker = df_striker[df_striker['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'average_successfulAttackingActions','Possession value total score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_striker = calculate_score(df_striker, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'average_progressivePasses', 'average_progressivePasses score')
        df_striker = calculate_score(df_striker, 'average_shotAssists','average_shotAssists score')
        df_striker = calculate_score(df_striker, 'average_touchInBox','average_touchInBox score')
        df_striker = calculate_score(df_striker, 'percent_newSuccessfulDribbles','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'average_keyPasses','average_keyPasses score')
        df_striker = calculate_score(df_striker, 'shot.xg','shot.xg score')


        df_striker['Linkup_play'] = df_striker[['percent_successfulPassesToFinalThird score','percent_successfulPasses score','Possession value score','average_touchInBox score','average_successfulPassesToFinalThird score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['average_touchInBox score','Possession value total score','average_touchInBox score','average_successfulPassesToFinalThird score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['average_touchInBox','shot.xg score','shot.xg score','shot.xg score','shot.xg score','shot.xg score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Chance creation','Goalscoring','Goalscoring','Possession value']].mean(axis=1)
        df_striker = df_striker[['player.name','team.name','label','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()

        df_strikertotal = df_striker[['player.name','team.name','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['player.name','team.name']).mean().reset_index()
        minutter = df_striker.groupby(['player.name', 'team.name'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_strikertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_classic_striker = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['player.name','team.name','total_minutesOnField total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_strikertotal = df_strikertotal.sort_values('Total score',ascending = False)
        return df_classic_striker
    
    def Targetman():
        df_striker = df_scouting[(df_scouting['position_codes'] == 'Striker') & (df_scouting['position_codesSide'].str.contains('Centre'))]
        df_striker['total_minutesOnField'] = df_striker['total_minutesOnField'].astype(int)
        df_striker = df_striker[df_striker['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'average_successfulAttackingActions','Possession value total score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_striker = calculate_score(df_striker, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'average_progressivePasses', 'average_progressivePasses score')
        df_striker = calculate_score(df_striker, 'average_shotAssists','average_shotAssists score')
        df_striker = calculate_score(df_striker, 'average_touchInBox','average_touchInBox score')
        df_striker = calculate_score(df_striker, 'percent_successfuldPassesToFinalThird','percent_successfuldPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'shotFastbreak_per90','shotFastbreak_per90 score')
        df_striker = calculate_score(df_striker, 'bigChanceCreated_per90','bigChanceCreated_per90 score')
        df_striker = calculate_score(df_striker, 'newSuccessfulDribbles','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'average_touchInBox','average_touchInBox score')
        df_striker = calculate_score(df_striker, 'average_keyPasses','average_keyPasses score')
        df_striker = calculate_score(df_striker, 'shot.xg','shot.xg score')
        df_striker = calculate_score(df_striker, 'shot.xg','shot.xg score')
        df_striker = calculate_score(df_striker, 'aerialWon','aerialWon score')


        df_striker['Linkup_play'] = df_striker[['percent_successfulPassesToFinalThird score','percent_successfulPasses score','Possession value score','average_touchInBox score','average_successfulPassesToFinalThird score','aerialWon score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['average_touchInBox score','Possession value total score','bigChanceCreated_per90 score','average_touchInBox score','average_successfulPassesToFinalThird score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['shot.xg score','shot.xg score','shot.xg score','shot.xg score','shot.xg score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Linkup play','Linkup play','Chance creation','Goalscoring','Goalscoring','Possession value','Possession value']].mean(axis=1)
        df_striker = df_striker[['player.name','team.name','label','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()
        df_strikertotal = df_striker[['player.name','team.name','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['player.name','team.name']).mean().reset_index()
        minutter = df_striker.groupby(['player.name', 'team.name'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_strikertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_targetman = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['player.name','team.name','total_minutesOnField total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_strikertotal = df_strikertotal.sort_values('Total score',ascending = False)
        return df_targetman

    def Boxstriker():
        df_striker = df_scouting[(df_scouting['position_codes'] == 'Striker') & (df_scouting['position_codesSide'].str.contains('Centre'))]
        df_striker['total_minutesOnField'] = df_striker['total_minutesOnField'].astype(int)
        df_striker = df_striker[df_striker['total_minutesOnField'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'average_successfulAttackingActions','Possession value total score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value score')
        df_striker = calculate_score(df_striker,'average_successfulAttackingActions', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_striker = calculate_score(df_striker, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'average_progressivePasses', 'average_progressivePasses score')
        df_striker = calculate_score(df_striker, 'average_shotAssists','average_shotAssists score')
        df_striker = calculate_score(df_striker, 'average_touchInBox','average_touchInBox score')
        df_striker = calculate_score(df_striker, 'percent_successfuldPassesToFinalThird','percent_successfuldPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'shotFastbreak_per90','shotFastbreak_per90 score')
        df_striker = calculate_score(df_striker, 'bigChanceCreated_per90','bigChanceCreated_per90 score')
        df_striker = calculate_score(df_striker, 'newSuccessfulDribbles','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'average_touchInBox','average_touchInBox score')
        df_striker = calculate_score(df_striker, 'average_keyPasses','average_keyPasses score')
        df_striker = calculate_score(df_striker, 'shot.xg','shot.xg score')
        df_striker = calculate_score(df_striker, 'shot.xg','shot.xg score')


        df_striker['Linkup_play'] = df_striker[['percent_successfulPassesToFinalThird score','percent_successfulPasses score','Possession value score','average_touchInBox score','average_successfulPassesToFinalThird score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['average_touchInBox score','Possession value total score','bigChanceCreated_per90 score','average_touchInBox score','average_successfulPassesToFinalThird score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['shot.xg score','shot.xg score','shot.xg score','shot.xg score','shot.xg score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Chance creation','Goalscoring','Goalscoring','Goalscoring','Goalscoring','Possession value','Possession value','Possession value']].mean(axis=1)
        df_striker = df_striker[['player.name','team.name','label','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()
        df_strikertotal = df_striker[['player.name','team.name','total_minutesOnField','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['player.name','team.name']).mean().reset_index()
        minutter = df_striker.groupby(['player.name', 'team.name'])['total_minutesOnField'].sum().astype(float).reset_index()
        df_strikertotal['total_minutesOnField total'] = minutter['total_minutesOnField']
        df_boksstriker = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['player.name','team.name','total_minutesOnField total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['total_minutesOnField total'].astype(int) >= minutter_total]
        df_strikertotal = df_strikertotal.sort_values('Total score',ascending = False)
        return df_boksstriker
    return {
        'Central defender': balanced_central_defender(),
        'Fullbacks': fullbacks(),
        'Number 6' : number6(),
        'Number 8': number8(),
        'Number 10': number10(),
        'Winger': winger(),
        'Classic striker': Classic_striker(),
    }

df_xg ,events, df_possession_stats,df_xg_agg, penalty_area_entry_counts, df_matchstats, df_ppda, df_groundduels = load_data()
position_dataframes = Process_data_spillere(events,df_xg,df_matchstats,df_groundduels)

#defending_central_defender_df = position_dataframes['defending_central_defender']
#ball_playing_central_defender_df = position_dataframes['ball_playing_central_defender']
balanced_central_defender_df = position_dataframes['Central defender']
fullbacks_df = position_dataframes['Fullbacks']
number6_df = position_dataframes['Number 6']
#number6_double_6_forward_df = position_dataframes['number6_double_6_forward']
#number6_destroyer_df = position_dataframes['Number 6 (destroyer)']
number8_df = position_dataframes['Number 8']
number10_df = position_dataframes['Number 10']
winger_df = position_dataframes['Winger']
classic_striker_df = position_dataframes['Classic striker']
#targetman_df = position_dataframes['Targetman']
#box_striker_df = position_dataframes['Boxstriker']

def process_data():
    expected_points_xg, total_expected_points_xg = calculate_expected_points(df_xg, 'shot.xg')
    df_holdsummary = create_holdsummary(df_xg,df_matchstats, penalty_area_entry_counts, df_ppda)
    # Calculate expected points based on xA
    merged_df = expected_points_xg.merge(df_holdsummary,on=['label', 'team.name'],how='outer')
    label_counts_per_team = merged_df.groupby('team.name')['label'].count().reset_index()
    horsens_df = merged_df[merged_df['team.name'].str.contains('Horsens')]

    total_expected_points_combined = total_expected_points_xg
    total_expected_points_combined = label_counts_per_team.merge(total_expected_points_combined)
    total_expected_points_combined ['Expected points per game'] = total_expected_points_combined['total_expected_points'] / total_expected_points_combined['label']
    total_expected_points_combined = total_expected_points_combined.rename(columns={'label': 'matches'})
    return total_expected_points_combined, merged_df,horsens_df
df_total_possessions= calculate_territorial_possession(df_possession_stats)
total_expected_points_combined, merged_df,horsens_df = process_data()
def create_pdf_game_report(game_data, df_xg_agg, merged_df, df_possession_stats, position_dataframes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    label = game_data['label']
    expected_points = game_data['expected_points']
    win_prob = game_data['win_probability']
    draw_prob = game_data['draw_probability']
    loss_prob = game_data['loss_probability']
    
    # Add the team logo
    pdf.image(r'C:\Users\SéamusPeareBartholdy\Documents\GitHub\AC-Horsens-U19\Logo.png', x=165, y=5, w=15, h=15)
    pdf.set_xy(10, 10)
    pdf.cell(140, 5, txt=f"Match Report: {label}", ln=True, align='L')
    
    pdf.ln(4)
    
    # Create bar charts for expected points and probabilities
    create_bar_chart(expected_points, 'Expected Points', 'bar_combined.png', 3.0, [1.1, 1.5, 2], ['Top 10','Top 6', 'Top 3'])
    create_stacked_bar_chart(win_prob, draw_prob, loss_prob, 'Win/Draw/Loss Probabilities', 'bar_combined_win_prob.png')
    
    # Add bar charts to PDF side by side
    pdf.image('bar_combined.png', x=10, y=25, w=90, h=30)
    pdf.image('bar_combined_win_prob.png', x=110, y=25, w=90, h=30)

    pdf.set_xy(5, 60)
    game_xg_agg = df_xg_agg[df_xg_agg['label'] == label]
    game_xg_agg = game_xg_agg.sort_values(by=['team.name','minute'])
    df_possession_stats = df_possession_stats[df_possession_stats['label'] == label]
    df_possession_stats = df_possession_stats.sort_values(by=['team.name','minute'])

    generate_cumulative_chart(game_xg_agg, 'cumulative_shot_xg', 'shot.xg', 'cumulative_xg.png')
    generate_possession_chart(df_possession_stats, label, 'cumulative_possession.png')

    pdf.image('cumulative_xg.png', x=5, y=55, w=66, h=60)
    pdf.image('cumulative_possession.png', x=73, y=55, w=130, h=60)
    # Add a summary table

    pdf.set_xy(5, 115)
    pdf.set_font_size(6)
    pdf.cell(20, 5, 'Summary', 0, 1, 'C')
    pdf.set_font("Arial", size=6)
    pdf.cell(20, 5, 'Team', 1)
    pdf.cell(20, 5, 'xG', 1)
    pdf.cell(30, 5, 'Territorial possession', 1)
    pdf.cell(25, 5, 'Penalty area entries', 1)
    pdf.cell(25, 5, 'Touches in box', 1)
    pdf.cell(20, 5, 'PPDA', 1)

    pdf.ln()

    game_merged_df = merged_df[merged_df['label'] == label]
    for index, row in game_merged_df.iterrows():
        pdf.cell(20, 5, row['team.name'], 1)
        pdf.cell(20, 5, f"{row['shot.xg']:.2f}", 1)
        pdf.cell(30, 5, f"{row['terr_poss']:.2f}", 1)
        pdf.cell(25, 5, f"{row['penAreaEntries']:.0f}", 1)
        pdf.cell(25, 5, f"{row['average_touchInBox']:.0f}", 1)
        pdf.cell(20, 5, f"{row['PPDA']:.2f}", 1)
        
        pdf.ln()
           
    for position, df in position_dataframes.items():
        filtered_df = df[(df['team.name'].str.contains('Horsens')) & (df['label'] == label)]
        if 'position_codes' in filtered_df.columns:
            filtered_df = filtered_df.drop(columns=['label', 'team.name', 'position_codes'])
        else:
            filtered_df = filtered_df.drop(columns=['label', 'team.name'])
        filtered_df = filtered_df.round(2)
        filtered_df['Total score'] = filtered_df['Total score'].astype(float)
        pdf.set_font("Arial", size=6)
        pdf.cell(190, 4, txt=f"Position Report: {position}", ln=True, align='C')
        pdf.ln(-1)
        # Add table headers
        pdf.set_font("Arial", size=6)
        headers = filtered_df.columns
        col_width = 30  # Fixed width for all columns except the last one
        last_col_width = 15  # Width for the last column

        for header in headers[:-1]:
            pdf.cell(col_width, 4, txt=header, border=1)
        pdf.cell(last_col_width, 4, txt=headers[-1], border=1)
        pdf.ln(4)

        # Add table content
        for index, row in filtered_df.iterrows():
            total_score = row['Total score']
            if total_score <= 4:
                fill_color = (255, 0, 0)  # Red
            elif 4 < total_score <= 6:
                fill_color = (255, 255, 0)  # Yellow
            else:
                fill_color = (0, 255, 0)  # Green

            pdf.set_fill_color(*fill_color)

            # Add all cells for the row
            for value in row.values[:-1]:
                pdf.cell(col_width, 4, txt=str(value), border=1, fill=True)
            pdf.cell(last_col_width, 4,txt=str(row.values[-1]), border=1, fill=True)
            pdf.ln(4)       

        pdf.ln()
    pdf.output(f"Match reports/Match_Report_{label}.pdf")
    print(f'{label} report created')

for index, row in horsens_df.iterrows():
    create_pdf_game_report(row, df_xg_agg, merged_df, df_possession_stats,position_dataframes)

def create_pdf_progress_report(horsens_df, total_expected_points_combined):
    today = date.today()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Add the team logo
    pdf.image('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-First-Team/Logo.png', x=165, y=5, w=10, h=10)
    pdf.set_xy(5, 5)
    pdf.cell(140, 5, txt=f"Progress report: {today}", ln=True, align='L')

    # Save the sliding average plot as an image
    plt.figure(figsize=(12, 3))
    sliding_average_plot(horsens_df, window_size=3, filename='sliding_average_plot.png')
    plt.close()
    pdf.image("sliding_average_plot.png", x=5, y=15, w=200)

    # Generate the DataFrame summary table for total expected points
    total_expected_points_combined = total_expected_points_combined.round(2)
    total_expected_points_combined = total_expected_points_combined.sort_values(by='Expected points per game', ascending=False)
    plt.figure(figsize=(12, 0.01), dpi=500)
    plt.axis('off')
    plt.rc('font', size=6)  # Set font size
    plt.table(cellText=total_expected_points_combined.values, colLabels=total_expected_points_combined.columns,colLoc='left', cellLoc='left', loc='center')
    plt.savefig("total_expected_points_table.png", format="png", bbox_inches='tight')
    plt.close()
    pdf.image("total_expected_points_table.png", x=5, y=75, w=200)
    
    y_position = 140  # Initial y position after the table image
    pdf.set_xy(5, y_position)
    
    for position, df in position_dataframes.items():
        filtered_df = df[(df['team.name'].str.contains('Horsens'))]

        numeric_columns = filtered_df.select_dtypes(include='number').columns.tolist()
        numeric_columns.remove('total_minutesOnField')
        
        # Sum minsPlayed and mean for the rest of the numeric columns
        aggregation_dict = {col: 'mean' for col in numeric_columns}
        aggregation_dict['total_minutesOnField'] = 'sum'
        
        filtered_df = filtered_df.groupby('player.name').agg(aggregation_dict).reset_index()
        filtered_df = filtered_df[filtered_df['total_minutesOnField'] > 160]
        filtered_df = filtered_df.round(2)
        filtered_df['Total score'] = filtered_df['Total score'].astype(float)        
        reordered_columns = ['player.name', 'total_minutesOnField'] + numeric_columns
        filtered_df = filtered_df[reordered_columns]
        filtered_df = filtered_df.sort_values('Total score',ascending=False)
        pdf.set_font("Arial", size=6)
        pdf.cell(190, 4, txt=f"Position Report: {position}", ln=True, align='C')
        pdf.ln(0)

        # Add table headers
        pdf.set_font("Arial", size=6)
        headers = filtered_df.columns
        col_width = 30  # Fixed width for all columns except the last one
        last_col_width = 15  # Width for the last column

        for header in headers[:-1]:
            pdf.cell(col_width, 4, txt=header, border=1)
        pdf.cell(last_col_width, 4, txt=headers[-1], border=1)
        pdf.ln(4)

        # Add table content
        for index, row in filtered_df.iterrows():
            total_score = row['Total score']
            if total_score <= 4:
                fill_color = (255, 0, 0)  # Red
            elif 4 < total_score <= 6:
                fill_color = (255, 255, 0)  # Yellow
            else:
                fill_color = (0, 255, 0)  # Green

            pdf.set_fill_color(*fill_color)

            # Add all cells for the row
            for value in row.values[:-1]:
                pdf.cell(col_width, 4, txt=str(value), border=1, fill=True)
            pdf.cell(last_col_width, 4,txt=str(row.values[-1]), border=1, fill=True)
            pdf.ln(4)  # Move to next line for the next player's row

        pdf.ln(0)  # Add some space between position reports
    pdf.output(f"Progress reports/Progress_report_{today}.pdf")
    print(f'{today} progress report created')


create_pdf_progress_report(horsens_df,total_expected_points_combined)


folder_path = 'C:/Users/Seamus-admin/Documents/GitHub/AC-Horsens-U19/'

# List all files in the folder
files = os.listdir(folder_path)

# Iterate over each file
for file in files:
    # Check if the file is a PNG file and not 'logo.png'
    if file.endswith(".png") and file != "Logo.png":
        # Construct the full path to the file
        file_path = os.path.join(folder_path, file)
        # Remove the file
        os.remove(file_path)
        print(f"Deleted: {file_path}")
