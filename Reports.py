import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from datetime import datetime
from datetime import date
from fileinput import filename

def load_data():
    df_xg = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/xg.csv')
    
    df_possession_stats = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/terr_poss.csv')
    
    df_xg_agg = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/xg.csv')
    
    penalty_area_entry_counts = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/penalty_area_entry_counts.csv')
    
    df_matchstats = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/matchstats.csv')
    
    df_ppda = pd.read_csv('C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-U19/ppda.csv')
    
    return df_xg, df_possession_stats,df_xg_agg, penalty_area_entry_counts, df_matchstats, df_ppda
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
    df_possession_stats['minute_interval'] = ((df_possession_stats['minute'] // 5) * 5).astype(str).str.zfill(2) + '-' + (((df_possession_stats['minute'] // 5) * 5) + 5).astype(str).str.zfill(2)
    df_grouped = df_possession_stats.groupby(['team.name', 'label', 'minute_interval', 'territorial_possession']).size().reset_index(name='count')
    df_total_possessions = df_grouped.groupby(['team.name', 'label', 'minute_interval'])['count'].sum().reset_index()
    df_total_possessions = df_total_possessions.rename(columns={'count': 'total_possessions'})
    df_grouped = df_grouped.merge(df_total_possessions, on=['team.name', 'label', 'minute_interval'])
    df_grouped['percentage_possession'] = (df_grouped['count'] / df_grouped['total_possessions']) * 100
    minute_intervals_order = [f'{i}-{i+5}' for i in range(0, 90, 5)]
    df_grouped['minute_interval'] = pd.Categorical(df_grouped['minute_interval'], categories=minute_intervals_order, ordered=True)
    df_grouped['minute_interval'] = df_grouped['minute_interval'].astype(str)
    df_grouped = df_grouped.groupby(['team.name', 'label', 'minute_interval'])['percentage_possession'].mean().reset_index()
    df_grouped['rolling_avg_percentage'] = df_grouped['percentage_possession'].rolling(window=10, min_periods=1).mean().reset_index(level=[0, 0], drop=True)

    df_grouped = df_grouped.dropna(subset=['minute_interval'])
    df_grouped['minute_interval'] = df_grouped['minute_interval'].astype(str)
    df_grouped = df_grouped.sort_values(by='minute_interval')

    # Plot the rolling average of percentages
    plt.figure(figsize=(10, 6))
    for team in df_grouped['team.name'].unique():
        team_data = df_grouped[(df_grouped['label'] == label) & (df_grouped['team.name'] == team)]
        if not team_data.empty:
            plt.plot(team_data['minute_interval'], team_data['rolling_avg_percentage'], label=f'{team}')
        
    # Plot the rolling average for the middle possession
    plt.xlabel('Minute Interval')
    plt.ylabel('Territorial Possession (%) (Rolling Average)')
    plt.title(f'Rolling Average of Territorial Possession Percentage for Every 5 Minutes ({label})')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.savefig(filename, bbox_inches='tight', dpi=500)
    plt.close()

def calculate_territorial_possession(df_possession_stats):
    df_grouped = df_possession_stats.groupby(['team.name', 'label', 'territorial_possession']).size().reset_index(name='count')
    df_total_possessions = df_grouped.groupby(['label'])['count'].sum().reset_index()
    df_total_possessions = df_total_possessions.rename(columns={'count': 'total_possessions'})
    df_total_possessions = df_grouped.merge(df_total_possessions)
    df_total_possessions['percentage_possession'] = (df_total_possessions['count'] / df_total_possessions['total_possessions']) * 100
    df_total_possessions = df_total_possessions.groupby(['team.name','label'])['percentage_possession'].mean().reset_index()
    df_total_possessions = df_total_possessions[['team.name','label','percentage_possession']]
    return df_total_possessions

def sliding_average_plot(df, window_size=3, filename=None):
    # Sort the DataFrame by 'date'
    df_sorted = df.sort_values(by='date')
    df_sorted = df_sorted.reset_index()
    #df_sorted['label'] = (df_sorted.index + 1).astype(str) + '. ' + df_sorted['label'].str[:-10]

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
    line3 = ax.axhline(y=1, color='red', linestyle='--', label='Relegation')
    line4 = ax.axhline(y=1.3, color='yellow', linestyle='--', label='Top 6')
    line5 = ax.axhline(y=1.8, color='green', linestyle='--', label='Promotion')

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

    ax.axhspan(0, 1, color='red', alpha=0.6)  # Below relegation
    ax.axhspan(1, 1.3, color='orange', alpha=0.6)  # Between relegation and top 6
    ax.axhspan(1.3, 1.8, color='yellow', alpha=0.6)  # Between top 6 and promotion
    ax.axhspan(1.8, 3, color='green', alpha=0.6)  # Above promotion

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
            
            expected_points_list.append({
                'label': label,
                'team.name': home_team, 
                'expected_points': home_points, 
                'win_probability': home_win_prob, 
                'draw_probability': draw_prob, 
                'loss_probability': away_win_prob
            })
            expected_points_list.append({
                'label': label,
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

def create_holdsummary(df_xg,penalty_area_entry_counts,df_ppda):
    df_total_possessions = calculate_territorial_possession(df_possession_stats)
    df_total_possessions = df_total_possessions[['team.name', 'label', 'percentage_possession']]
    df_total_possessions = df_total_possessions.rename(columns={'percentage_possession': 'terr_poss'})
    df_xg_hold = df_xg.groupby(['team.name', 'label'])['shot.xg'].sum().reset_index()
    penalty_area_entry_counts = penalty_area_entry_counts.rename(columns={'count': 'penAreaEntries'})
    df_holdsummary = df_xg_hold.merge(df_total_possessions)
    df_holdsummary = df_holdsummary.merge(penalty_area_entry_counts)
    df_holdsummary = df_holdsummary.merge(df_ppda)
    df_holdsummary = df_holdsummary[['team.name', 'label', 'shot.xg','penAreaEntries','PPDA','terr_poss']]
    
    return df_holdsummary

def process_data():
    expected_points_xg, total_expected_points_xg = calculate_expected_points(df_xg, 'shot.xg')
    df_holdsummary = create_holdsummary(df_xg, penalty_area_entry_counts, df_ppda)
    # Calculate expected points based on xA
    merged_df = expected_points_xg.merge(df_holdsummary,on=['label', 'team.name'],how='outer')
    label_counts_per_team = merged_df.groupby('team.name')['label'].count().reset_index()
    horsens_df = merged_df[merged_df['team.name'].str.contains('Horsens')]

    total_expected_points_combined = total_expected_points_xg
    total_expected_points_combined = label_counts_per_team.merge(total_expected_points_combined)
    total_expected_points_combined ['Expected points per game'] = total_expected_points_combined['total_expected_points'] / total_expected_points_combined['label']
    total_expected_points_combined = total_expected_points_combined.rename(columns={'label': 'matches'})
    return total_expected_points_combined, merged_df,horsens_df
df_xg, df_possession_stats,df_xg_agg, penalty_area_entry_counts, df_matchstats, df_ppda = load_data()

df_total_possessions = calculate_territorial_possession(df_possession_stats)
print(df_total_possessions)

total_expected_points_combined, merged_df,horsens_df = process_data()
print(merged_df)
def create_pdf_game_report(game_data, df_xg_agg, merged_df, df_possession_stats):
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
    create_bar_chart(expected_points, 'Expected Points', 'bar_combined.png', 3.0, [1.0, 1.3, 1.8], ['Relegation','Top 6', 'Promotion'])
    create_stacked_bar_chart(win_prob, draw_prob, loss_prob, 'Win/Draw/Loss Probabilities', 'bar_combined_win_prob.png')
    
    # Add bar charts to PDF side by side
    pdf.image('bar_combined.png', x=10, y=25, w=90, h=30)
    pdf.image('bar_combined_win_prob.png', x=110, y=25, w=90, h=30)

    pdf.set_xy(5, 60)
    game_xg_agg = df_xg_agg[df_xg_agg['label'] == label]
    df_possession_stats = df_possession_stats[df_possession_stats['label'] == label]

    generate_cumulative_chart(game_xg_agg, 'cumulative_shot_xg', 'shot.xg', 'cumulative_xg.png')
    generate_possession_chart(df_possession_stats, label, 'cumulative_possession.png')

    pdf.image('cumulative_xg.png', x=5, y=55, w=66, h=60)
    pdf.image('cumulative_possession.png', x=139, y=55, w=66, h=60)
    # Add a summary table

    pdf.set_xy(5, 115)
    pdf.set_font_size(6)
    pdf.cell(20, 5, 'Summary', 0, 1, 'C')
    pdf.set_font("Arial", size=6)
    pdf.cell(20, 5, 'Team', 1)
    pdf.cell(20, 5, 'xG', 1)
    pdf.cell(30, 5, 'Territorial possession', 1)
    pdf.cell(25, 5, 'Penalty area entries', 1)
    pdf.cell(20, 5, 'PPDA', 1)

    pdf.ln()

    game_merged_df = merged_df[merged_df['label'] == label]
    for index, row in game_merged_df.iterrows():
        pdf.cell(20, 5, row['team.name'], 1)
        pdf.cell(20, 5, f"{row['shot.xg']:.2f}", 1)
        pdf.cell(30, 5, f"{row['terr_poss']:.2f}", 1)
        pdf.cell(25, 5, f"{row['penAreaEntries']:.0f}", 1)
        pdf.cell(20, 5, f"{row['PPDA']:.2f}", 1)

        pdf.ln()
    pdf.output(f"Match reports/Match_Report_{label}.pdf")
    print(f'{label} report created')

for index, row in horsens_df.iterrows():
    create_pdf_game_report(row, df_xg_agg, merged_df, df_possession_stats)

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
    pdf.image("total_expected_points_table.png", x=5, y=71, w=200)
    
    y_position = 120  # Initial y position after the table image
    pdf.set_xy(5, y_position)
    

    pdf.output(f"Progress reports/Progress_report_{today}.pdf")
    print(f'{today} progress report created')


create_pdf_progress_report(horsens_df,total_expected_points_combined)


folder_path = 'C:/Users/SéamusPeareBartholdy/Documents/GitHub/AC-Horsens-First-Team/'

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
