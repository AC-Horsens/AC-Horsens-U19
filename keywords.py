import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
st.set_page_config(layout='wide')

# Load data
possession_events = pd.read_csv(r'events.csv')

# Extract unique match labels for selection
matches = possession_events['label'].unique()
matches = [match for match in matches if 'Horsens' in match]
match = st.selectbox('Select match', matches)
possession_events = possession_events[possession_events['label'] == match]
# Filter for expected goals events
expected_goals = possession_events[possession_events['shot.xg'].astype(float) > 0]
# Late crosses definition
late_crosses = possession_events[
    (possession_events['type.primary'] == 'pass') &
    (possession_events['location.x'].astype(float) >= 90) &
    (possession_events['shot.xg'].isna()) &  # Exclude shots
    ((possession_events['location.y'].astype(float) <= 19) |  # Starts on left side of box
     (possession_events['location.y'].astype(float) >= 81)) &  # Or right side of box
    (possession_events['pass.endLocation.x'].astype(float) >= 84) &  # Ends close to the goal
    (possession_events['pass.endLocation.y'].astype(float) <= 63) &  # In the defined target area
    (possession_events['pass.endLocation.y'].astype(float) >= 37)
]

# Define penalty area entries (any end in or start in the box)
penalty_area_entries = possession_events[
    (possession_events['shot.xg'].isna()) &  # Exclude shots
    (
        ((possession_events['pass.endLocation.x'].astype(float) >= 84) &
         (possession_events['pass.endLocation.y'].astype(float) >= 19) &
         (possession_events['pass.endLocation.y'].astype(float) <= 81)) |  # Ends in the box
         
        ((possession_events['carry.endLocation.x'].astype(float) >= 84) &
         (possession_events['carry.endLocation.y'].astype(float) >= 19) &
         (possession_events['carry.endLocation.y'].astype(float) <= 81)) |  # Carry ends in the box
        
        ((possession_events['location.x'].astype(float) >= 84) &
         (possession_events['location.y'].astype(float) >= 19) &
         (possession_events['location.y'].astype(float) <= 81))  # Starts in the box
    )
]
# High xG events weight calculation
expected_goals['event_weight'] = expected_goals['shot.xg'].apply(lambda d: 2 if d >= 0.1 else 0)

# Assign weights to other events
late_crosses['event_weight'] = 1
penalty_area_entries['event_weight'] = 1

# Combine all offensive intense events
offensive_intense_events = pd.concat([late_crosses, penalty_area_entries, expected_goals])
# Filter for Horsens team and calculate counts for players with weights > 0
names = offensive_intense_events[offensive_intense_events['team.name'] == 'Horsens U19']
names = names[names['event_weight'] > 0]
names = names.value_counts('player.name')

# Display the result
st.dataframe(names)

# Filter passes in the opponent's half (type.primary == 1 and x > 50)
passes_opponent_half = possession_events[
    (possession_events['location.x'].astype(float) >= 50) & 
    (possession_events['type.primary'] == 'pass' )
]

# Group offensive intense events by minute and calculate the weighted count
offensive_intense_actions_per_min = offensive_intense_events.groupby(['team.name','minute'])['event_weight'].sum().reset_index().rename(columns={'event_weight': 'offensive_intense_actions'})
# Group passes in the opponent's half by minute
passes_opponent_half_per_min = passes_opponent_half.groupby(['team.name','minute'])['id'].count().reset_index().rename(columns={'id': 'passes_in_opponent_half'})

# Merge to calculate offensive intensity (offensive intense actions / passes in opponent's half)
offensive_intensity = pd.merge(offensive_intense_actions_per_min, passes_opponent_half_per_min, on=['team.name','minute'], how='outer').fillna(0)

# Calculate offensive intensity, replacing any inf values with 0 for safe division
offensive_intensity['offensive_intensity'] = (
    offensive_intensity['offensive_intense_actions'] / offensive_intensity['passes_in_opponent_half']
).replace([np.inf, -np.inf], 0).fillna(0)  # Replace infinities and NaNs with 0

# Ensure offensive intensity is in float type
offensive_intensity['offensive_intensity'] = offensive_intensity['offensive_intensity'].astype(float)
offensive_intensity = offensive_intensity.sort_values(['team.name','minute'])

# Calculate rolling average (10-minute rolling window)
offensive_intensity['offensive_intensity_15_min_avg'] = offensive_intensity['offensive_intensity'].rolling(window=15, min_periods=1).mean()

# Display the final result

# Plot the rolling average of offensive intensity per team

fig = go.Figure()

# Plot for each team (assuming 'team.name' is available in possession_events)
for team in possession_events['team.name'].unique():
    team_data = offensive_intensity[offensive_intensity['team.name'] == team]
    color = 'yellow' if team == 'Horsens U19' else 'red'  # Set to yellow for Horsens

    fig.add_trace(go.Scatter(
        x=team_data['minute'],
        y=team_data['offensive_intensity_15_min_avg'],
        mode='lines',
        name=f'{team} (15-min avg)',
        line=dict(color=color)  # Set line color based on team
    ))

# Set layout for the plot
fig.update_layout(
    title='Offensive Intensity (15-Minute Rolling Average) Per Minute in the Match',
    xaxis_title='Minute',
    yaxis_title='Offensive Intensity (15-min avg)',
    legend_title='Teams',
    template='plotly_white',
    yaxis=dict(range=[0, 1.5])  # Set y-axis range from 0 to 1
)

# Display the plot in Streamlit
st.plotly_chart(fig)


defensive_actions = possession_events[possession_events['type.primary'].isin(['interception', 'infraction', 'clearance'])]
names = defensive_actions[defensive_actions['team.name'] == 'Horsens U19']
names = names.value_counts('player.name')
st.dataframe(names)
teams = possession_events['team.name'].unique()
home_team_id = teams[0]
away_team_id = teams[1]   
def calculate_opponents_passes_and_defensive_actions(df, home_team_id, away_team_id):
    # Create 10-minute intervals
    df['time_interval'] = pd.cut(df['minute'], bins=range(0, df['minute'].max() + 5, 5), right=False, labels=range(0, df['minute'].max(), 5))

    # Filter events beyond the 40-yard line
    df = df[df['location.x'].astype(float) > 40]

    # Separate passes and defensive actions by each team, now with time_interval column included
    passes_by_home_team = df[(df['team.name'] == home_team_id) & (df['type.primary'] == 'pass')]
    passes_by_away_team = df[(df['team.name'] == away_team_id) & (df['type.primary'] == 'pass')]
    
    defensive_actions_by_home_team = df[
        (df['team.name'] == home_team_id) &
        (
            df['type.primary'].isin(['interception', 'infraction', 'clearance']) |
            df['type.secondary'].str.contains('defensive_duel', na=False)  # Check for 'defensive_duel' in 'type.secondary'
        )
    ]    
    defensive_actions_by_away_team = df[
        (df['team.name'] == away_team_id) &
        (
            df['type.primary'].isin(['interception', 'infraction', 'clearance']) |
            df['type.secondary'].str.contains('defensive_duel', na=False)  # Check for 'defensive_duel' in 'type.secondary'
        )
    ]    
    # Group by 10-minute intervals for passes and defensive actions
    opponent_passes_for_home_team = passes_by_away_team.groupby('time_interval')['id'].count().reset_index().rename(columns={'id': 'opponent_passes'})
    opponent_passes_for_away_team = passes_by_home_team.groupby('time_interval')['id'].count().reset_index().rename(columns={'id': 'opponent_passes'})

    defensive_actions_for_home_team = defensive_actions_by_home_team.groupby('time_interval')['id'].count().reset_index().rename(columns={'id': 'defensive_actions'})
    defensive_actions_for_away_team = defensive_actions_by_away_team.groupby('time_interval')['id'].count().reset_index().rename(columns={'id': 'defensive_actions'})

    # Merge opponent passes and defensive actions by interval
    ppda_home_team = pd.merge(opponent_passes_for_home_team, defensive_actions_for_home_team, on='time_interval', how='outer')
    ppda_away_team = pd.merge(opponent_passes_for_away_team, defensive_actions_for_away_team, on='time_interval', how='outer')

    # Calculate PPDA for each 10-minute interval
    ppda_home_team['PPDA'] = ppda_home_team['opponent_passes'] / ppda_home_team['defensive_actions']
    ppda_away_team['PPDA'] = ppda_away_team['opponent_passes'] / ppda_away_team['defensive_actions']

    # Add team names
    ppda_home_team['team.name'] = home_team_id
    ppda_away_team['team.name'] = away_team_id

    # Concatenate both teams' PPDA data
    ppda_df = pd.concat([ppda_home_team, ppda_away_team])

    return ppda_df
home_team_name = teams[0]
away_team_name = teams[1]  
# Example usage
ppda_df = calculate_opponents_passes_and_defensive_actions(possession_events, home_team_name, away_team_name)

# Example usage
ppda_df['PPDA'] = pd.to_numeric(ppda_df['PPDA'], errors='coerce')
ppda_df['PPDA_15_min_avg'] = ppda_df.groupby('team.name')['PPDA'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

# Create a plotly figure for visualization
fig = go.Figure()

# Plot the PPDA rolling average for each team
for team in ppda_df['team.name'].unique():
    team_data = ppda_df[ppda_df['team.name'] == team]
    color = 'yellow' if team == 'Horsens U19' else 'red'  # Set to yellow for Horsens

    # Add line for each team with 10-minute rolling average
    fig.add_trace(go.Scatter(
        x=team_data['time_interval'],
        y=team_data['PPDA_15_min_avg'],
        mode='lines',
        name=f'{team} (15-min avg)',
        line=dict(color=color)  # Set line color based on team
    ))

# Set title and axis labels for the plot
fig.update_layout(
    title='Defensive intensity (15-Minute Rolling Average) Per Minute in the Match',
    xaxis_title='Minute',
    yaxis_title='PPDA (15-min avg)',
    legend_title='Teams',
    template='plotly_white',
    yaxis=dict(range=[20, 0], autorange=False)  # Set y-axis from 0 to 10 and reverse it
)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig)

def calculate_passes_per_minute(df, home_team_id, away_team_id):
    # Filter passes (type.primary == 1)
    passes_by_home_team = df[(df['team.name'] == home_team_id) & (df['type.primary'] == 'pass') & (df['pass.accurate'] == True)]
    passes_by_away_team = df[(df['team.name'] == away_team_id) & (df['type.primary'] == 'pass') & (df['pass.accurate'] == True)]
    
    # Count passes per minute for home team
    passes_home_team = passes_by_home_team.groupby('minute')['id'].count().reset_index().rename(columns={'id': 'passes'})
    passes_home_team['team.name'] = home_team_id
    
    # Count passes per minute for away team
    passes_away_team = passes_by_away_team.groupby('minute')['id'].count().reset_index().rename(columns={'id': 'passes'})
    passes_away_team['team.name'] = away_team_id
    
    # Combine the passes data for both teams
    passes_df = pd.concat([passes_home_team, passes_away_team])

    return passes_df

# Example usage
passes_df = calculate_passes_per_minute(possession_events, home_team_name, away_team_name)

# Convert to numeric in case of issues with non-numeric data
passes_df['passes'] = pd.to_numeric(passes_df['passes'], errors='coerce')

# Calculate a 10-minute rolling average of passes for smoother trends
passes_df['passes_15_min_avg'] = passes_df.groupby('team.name')['passes'].transform(lambda x: x.rolling(window=10, min_periods=1).mean())

# Create a plotly figure for visualization
fig = go.Figure()

# Plot the passes rolling average for each team
for team in passes_df['team.name'].unique():
    team_data = passes_df[passes_df['team.name'] == team]
    color = 'yellow' if team == 'Horsens U19' else 'red'  # Set to yellow for Horsens

    # Add line for each team with 10-minute rolling average
    fig.add_trace(go.Scatter(
        x=team_data['minute'],
        y=team_data['passes_15_min_avg'],
        mode='lines',
        name=f'{team} (15-min avg)',
        line=dict(color=color)  # Set line color based on team

    ))

# Set title and axis labels for the plot
fig.update_layout(
    title='Control (15-Minute Rolling Average) Per Minute in the Match',
    xaxis_title='Minute',
    yaxis_title='Passes (15-min avg)',
    legend_title='Teams',
    template='plotly_white',
    yaxis=dict(range=[0, 10])  # Set y-axis range from 0 to 10

)


with col2:
    st.plotly_chart(fig)
