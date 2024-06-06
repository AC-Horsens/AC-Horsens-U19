from azure.storage.fileshare import ShareServiceClient
import json
import pandas as pd
from pandas import json_normalize
import numpy as np

connection_string = 'SharedAccessSignature=sv=2020-08-04&ss=f&srt=sco&sp=rl&se=2025-01-11T22:47:25Z&st=2022-01-11T14:47:25Z&spr=https&sig=CXdXPlHz%2FhW0IRugFTfCrB7osNQVZJ%2BHjNR1EM2s6RU%3D;FileEndpoint=https://divforeningendataout1.file.core.windows.net/;'
share_name = 'divisionsforeningen-outgoingdata'
dir_path = 'KampData/Sæson 23-24/U19 Ligaen/'

service_client = ShareServiceClient.from_connection_string(connection_string)
share_client = service_client.get_share_client(share_name)
directory_client = share_client.get_directory_client(dir_path)

json_files = []

def find_json_files(directory_client):
    for item in directory_client.list_directories_and_files():
        if item.is_directory:
            sub_directory_client = directory_client.get_subdirectory_client(item.name)
            find_json_files(sub_directory_client)
        elif item.name.endswith('.json') and 'MatchEvents' in item.name:
            json_files.append(json.loads(directory_client.get_file_client(item.name).download_file().readall().decode()))

find_json_files(directory_client)

events_list = []

for item in json_files:
    events_list.extend(item['events'])

df = pd.json_normalize(events_list)

json_files = []

def find_json_files(directory_client):
    for item in directory_client.list_directories_and_files():
        if item.is_directory:
            sub_directory_client = directory_client.get_subdirectory_client(item.name)
            find_json_files(sub_directory_client)
        elif item.name.endswith('.json') and 'MatchDetail' in item.name:
            json_files.append(json.loads(directory_client.get_file_client(item.name).download_file().readall().decode()))
            
find_json_files(directory_client)
kampdetaljer = json_normalize(json_files)
kampdetaljer = kampdetaljer[['wyId','label','date']]
kampdetaljer = kampdetaljer.rename(columns={'wyId':'matchId'})
events = kampdetaljer.merge(df)
events = events[['id','matchId','player.name','player.id','date','team.name','type.primary','type.secondary','pass.accurate','pass.endLocation.x','pass.endLocation.y','carry.endLocation.x','carry.endLocation.y','minute','label','location.x','location.y','shot.xg']]
events.to_csv('events.csv',index=False)

connection_string = 'SharedAccessSignature=sv=2020-08-04&ss=f&srt=sco&sp=rl&se=2025-01-11T22:47:25Z&st=2022-01-11T14:47:25Z&spr=https&sig=CXdXPlHz%2FhW0IRugFTfCrB7osNQVZJ%2BHjNR1EM2s6RU%3D;FileEndpoint=https://divforeningendataout1.file.core.windows.net/;'
share_name = 'divisionsforeningen-outgoingdata'
dir_path = 'KampData/Sæson 23-24/U19 Ligaen/'


service_client = ShareServiceClient.from_connection_string(connection_string)
share_client = service_client.get_share_client(share_name)
directory_client = share_client.get_directory_client(dir_path)

json_files = []

def find_json_files(directory_client):
    for item in directory_client.list_directories_and_files():
        if item.is_directory:
            if 'AC Horsens' in item.name:
                # Recursively search for JSON files in the subdirectory if it contains 'AC Horsens' in its name
                sub_directory_client = directory_client.get_subdirectory_client(item.name)
                find_json_files(sub_directory_client)
            else:
                # Otherwise, continue searching in the current directory
                find_json_files(directory_client.get_subdirectory_client(item.name))
        elif item.name.endswith('.json') and 'MatchAdvancePlayerStats' in item.name:
            # If the item is a JSON file with 'MatchEvents' in the name, download it and append its data to the list
            json_files.append(json.loads(directory_client.get_file_client(item.name).download_file().readall().decode()))

find_json_files(directory_client)

# Create an empty list to store the events data
players_list = []
# Iterate over each item in the json_files list and append its 'events' data to the events_list
for item in json_files:
    players_list.extend(item['players'])


# Convert the events_list to a DataFrame
matchstats = pd.DataFrame(players_list)
matchstats.to_csv('matchstats.csv',index=False)

import pandas as pd
import ast

matchstats = pd.read_csv(r'C:\Users\SéamusPeareBartholdy\Documents\GitHub\AC-Horsens-U19\matchstats.csv')
events = pd.read_csv(r'C:\Users\SéamusPeareBartholdy\Documents\GitHub\AC-Horsens-U19\events.csv')
name_and_id = events[['player.name','player.id','team.name','matchId','label']]
name_and_id.rename(columns={'player.id':'playerId'})
name_and_id = name_and_id.drop_duplicates()
matchstats = name_and_id.merge(matchstats)
# Extract positions from the 'positions' column
def extract_positions(positions_str):
    positions_list = ast.literal_eval(positions_str)
    names = [pos['position']['name'] for pos in positions_list]
    codes = [pos['position']['code'] for pos in positions_list]
    return pd.Series({'position_names': names, 'position_codes': codes})

# Apply the extract_positions function to the 'positions' column
matchstats[['position_names', 'position_codes']] = matchstats['positions'].apply(extract_positions)

# Drop unnecessary columns and merge the extracted positions
matchstats = matchstats[['player.name', 'team.name', 'matchId', 'label', 'position_names', 'position_codes', 'average', 'percent', 'total']]

# Convert 'percent', 'total', and 'average' columns to appropriate data types
matchstats['percent'] = matchstats['percent'].apply(ast.literal_eval)
matchstats['total'] = matchstats['total'].apply(ast.literal_eval)
matchstats['average'] = matchstats['average'].apply(ast.literal_eval)

# Expand the 'percent', 'total', and 'average' columns into separate columns
matchstats = pd.concat([
    matchstats,
    pd.DataFrame(matchstats['percent'].to_list(), index=matchstats.index).add_prefix('percent_'),
    pd.DataFrame(matchstats['total'].to_list(), index=matchstats.index).add_prefix('total_'),
    pd.DataFrame(matchstats['average'].to_list(), index=matchstats.index).add_prefix('average_')
], axis=1)

# Drop the original 'percent', 'total', and 'average' columns
matchstats = matchstats.drop(['percent', 'total', 'average'], axis=1)
empty_lists_mask = (matchstats['position_names'].apply(len) == 0) & (matchstats['position_codes'].apply(len) == 0)
matchstats = matchstats[~empty_lists_mask]
matchstats = matchstats[['player.name','team.name','position_codes','total_minutesOnField','percent_duelsWon','percent_successfulPassesToFinalThird','average_xgAssist','average_crosses','average_passesToFinalThird','percent_successfulProgressivePasses','percent_successfulPasses','average_ballRecoveries','average_interceptions','average_defensiveDuels','average_successfulDefensiveAction','average_forwardPasses','average_successfulForwardPasses','average_touchInBox','average_xgShot','average_keyPasses','average_successfulAttackingActions','average_shotAssists']]
matchstats.to_csv('matchstats.csv',index=False)

xg = events[events['shot.xg'] > 0]
xg = xg[['team.name','label','minute','shot.xg']]
xg.to_csv('xg.csv',index=False)

xg_agg = xg[xg['label'].str.contains('Horsens')]
xg_agg.to_csv('xg_agg.csv', index=False)

terr_poss = events[['team.name','minute','label','location.x','location.y']]
team_names = terr_poss['team.name'].unique()
team_1 = team_names[0]
team_2 = team_names[1]
def determine_defending_team(row):
    if row['location.x'] <= 33.33:
        return row['team.name']
    elif row['location.x'] <= 66.67:
        return 'Middle'
    else:
        # Assume the other team is defending the final third
        if row['team.name'] == team_1:
            return team_2
        else:
            return team_1

# Apply the function to create the 'defending_team' column
terr_poss['territorial_possession'] = terr_poss.apply(determine_defending_team, axis=1)
terr_poss.to_csv('terr_poss.csv', index=False)

df_ppda = events[['type.primary','type.secondary','team.name','location.x','label','id']]
df_ppdabeyond40 = df_ppda[df_ppda['location.x'] > 40]
df_ppdabeyond40_passes = df_ppdabeyond40[df_ppdabeyond40['type.primary'] == 'pass']
df_ppdabeyond40_passestotal = df_ppdabeyond40_passes.groupby('label')['id'].count().reset_index()
df_ppdabeyond40_passestotal = df_ppdabeyond40_passestotal.rename(columns={'id': 'passes in game'})
df_ppdabeyond40_passesteam = df_ppdabeyond40_passes.groupby(['label','team.name'])['id'].count().reset_index()
df_ppdabeyond40_passesteam = df_ppdabeyond40_passesteam.rename(columns={'id': 'passes'})

df_ppdabeyond40_defactions = df_ppdabeyond40[(df_ppdabeyond40['type.primary'].isin(['interception', 'infraction', 'clearance']))]
df_ppdabeyond40_defactionstotal = df_ppdabeyond40_defactions.groupby('label')['id'].count().reset_index()
df_ppdabeyond40_defactionstotal = df_ppdabeyond40_defactionstotal.rename(columns={'id': 'defactions in game'})
df_ppdabeyond40_defactionsteam = df_ppdabeyond40_defactions.groupby(['label', 'team.name'])['id'].count().reset_index()
df_ppdabeyond40_defactionsteam = df_ppdabeyond40_defactionsteam.rename(columns={'id': 'defensive actions'})
df_ppdabeyond40_total = df_ppdabeyond40_defactionstotal.merge(df_ppdabeyond40_passestotal)
df_ppdabeyond40 = df_ppdabeyond40_defactionsteam.merge(df_ppdabeyond40_total)
df_ppdabeyond40 = df_ppdabeyond40.merge(df_ppdabeyond40_passesteam)
df_ppdabeyond40['opponents passes'] = df_ppdabeyond40['passes in game'] - df_ppdabeyond40['passes']
df_ppdabeyond40['PPDA'] = df_ppdabeyond40['opponents passes'] / df_ppdabeyond40['defensive actions']
df_ppda = df_ppdabeyond40[['label', 'team.name', 'PPDA']]
df_ppda.to_csv('PPDA.csv')

penalty_area_entry_condition = (
    ((events['pass.endLocation.x'] > 83) & 
     (events['pass.endLocation.y'].between(19, 81))) |
    ((events['carry.endLocation.x'] > 83) &
     (events['carry.endLocation.y'].between(19, 81)))
)

# Assign the boolean mask to a new column 'penalty_area_entry'
events['penalty_area_entry'] = penalty_area_entry_condition

# Create a new DataFrame with selected columns
penalty_area_entries = events[['team.name', 'label', 'penalty_area_entry']]

penalty_area_entry_counts = penalty_area_entries.groupby(['label', 'team.name'])['penalty_area_entry'].sum()

# Reset the index to convert the result into a DataFrame
penalty_area_entry_counts = penalty_area_entry_counts.reset_index()

# Rename the column to 'count' for clarity
penalty_area_entry_counts = penalty_area_entry_counts.rename(columns={'penalty_area_entry': 'count'})
penalty_area_entry_counts.to_csv('penalty_area_entry_counts.csv')