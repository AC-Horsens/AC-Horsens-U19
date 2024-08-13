from azure.storage.fileshare import ShareServiceClient
import json
import pandas as pd
from pandas import json_normalize


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
events = events[['id','player.name', 'player.id', 'team.name', 'matchId','pass.recipient.name','pass.accurate','label','date','minute','second','groundDuel','aerialDuel','infraction','carry','type.primary','type.secondary','location.x','location.y','pass.endLocation.x','pass.endLocation.y','carry.endLocation.x','carry.endLocation.y','shot.xg','possession.types','possession.eventsNumber','possession.eventIndex','possession.startLocation.x','possession.startLocation.y','possession.endLocation.x','possession.endLocation.y','possession.team.name','possession.attack.xg']]
transitions = events[events['possession.eventsNumber']<=15]
exclude_types = ['throw_in', 'set_piece_attack', 'free_kick', 'corner']

def convert_to_list(value):
    if isinstance(value, str):
        return ast.literal_eval(value)
    return value

transitions['possession.types'] = transitions['possession.types'].apply(convert_to_list)

def exclude_possession_types(possession_types):
    return any(ex_type in possession_types for ex_type in exclude_types)

transitions = transitions[~transitions['possession.types'].apply(exclude_possession_types)]
transitions.to_csv('transitions.csv', index=False)

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
matchstats.rename(columns={'playerId': 'player.id'}, inplace=True)
name_and_id = events[['player.name','player.id','team.name','date','matchId','label']]
name_and_id = name_and_id.drop_duplicates()
matchstats = matchstats.merge(name_and_id)
data = matchstats['positions']
df1 = pd.DataFrame(data)
def extract_positions(data):
    positions_list = ast.literal_eval(data) # Konverterer strengen til en liste af ordbøger
    names = [pos['position']['name'] for pos in positions_list]
    codes = [pos['position']['code'] for pos in positions_list]
    return pd.Series({'position_names': names, 'position_codes': codes})

df1[['position_names', 'position_codes']] = df1['positions'].apply(extract_positions)

matchstats = pd.merge(matchstats,df1,left_index=True, right_index=True)
matchstats = matchstats[['player.id','player.name','team.name','matchId','label','date','position_names','position_codes','average','percent','total']]
matchstats['percent'] = matchstats['percent'].apply(lambda x: ast.literal_eval(x))

new_df = pd.DataFrame(matchstats['percent'].to_list(), index=matchstats.index).add_prefix('percent_')

matchstats = pd.concat([matchstats, new_df], axis=1)
matchstats = matchstats.drop('percent', axis=1)

matchstats['total'] = matchstats['total'].apply(lambda x: ast.literal_eval(x))

new_df = pd.DataFrame(matchstats['total'].to_list(), index=matchstats.index).add_prefix('total_')

matchstats = pd.concat([matchstats, new_df], axis=1)

matchstats = matchstats.drop('total', axis=1)

matchstats['average'] = matchstats['average'].apply(lambda x: ast.literal_eval(x))
new_df = pd.DataFrame(matchstats['average'].to_list(), index=matchstats.index).add_prefix('average_')
matchstats = pd.concat([matchstats, new_df], axis=1)
matchstats = matchstats.drop('average', axis=1)
matchstats['position_codes'] = matchstats['position_codes'].astype(str)
matchstats = matchstats[['player.id','player.name','team.name','label','date','position_codes','total_minutesOnField','average_successfulPassesToFinalThird','percent_aerialDuelsWon','percent_newSuccessfulDribbles','average_throughPasses','percent_duelsWon','percent_successfulPassesToFinalThird','average_xgAssist','average_crosses','average_progressivePasses','average_progressiveRun','average_accelerations','average_passesToFinalThird','percent_successfulProgressivePasses','percent_successfulPasses','average_ballRecoveries','average_interceptions','average_defensiveDuels','average_successfulDefensiveAction','average_forwardPasses','average_successfulForwardPasses','average_touchInBox','average_xgShot','average_keyPasses','average_successfulAttackingActions','average_shotAssists']]
matchstats.to_csv('matchstats.csv',index=False)

xg = events[events['shot.xg'] > 0]
xg = xg[['player.name','team.name','label','date','location.x','location.y','minute','shot.xg']]
xg.to_csv('xg.csv',index=False)

xg_agg = xg[xg['label'].str.contains('Horsens')]
xg_agg.to_csv('xg_agg.csv', index=False)

terr_poss = events[['team.name', 'minute', 'label','date', 'location.x', 'location.y']]

def determine_defending_team(row, team_1, team_2):
    if row['location.x'] <= 33.33:
        return row['team.name']
    elif row['location.x'] <= 66.67:
        return 'Middle'
    else:
        if row['team.name'] == team_1:
            return team_2
        else:
            return team_1

def apply_for_each_label(group):
    team_names = group['team.name'].unique()
    if len(team_names) != 2:
        raise ValueError(f"Unexpected number of teams in group: {team_names}")
    team_1, team_2 = team_names[0], team_names[1]
    group['territorial_possession'] = group.apply(determine_defending_team, axis=1, team_1=team_1, team_2=team_2)
    return group

terr_poss = terr_poss.groupby('label').apply(apply_for_each_label).reset_index(drop=True)
terr_poss = terr_poss.to_csv('terr_poss.csv', index=False)

df_ppda = events[['type.primary','type.secondary','team.name','location.x','label','date','id']]
df_ppdabeyond40 = df_ppda[df_ppda['location.x'] > 40]
df_ppdabeyond40_passes = df_ppdabeyond40[df_ppdabeyond40['type.primary'] == 'pass']
df_ppdabeyond40_passestotal = df_ppdabeyond40_passes.groupby(['label','date'])['id'].count().reset_index()
df_ppdabeyond40_passestotal = df_ppdabeyond40_passestotal.rename(columns={'id': 'passes in game'})
df_ppdabeyond40_passesteam = df_ppdabeyond40_passes.groupby(['label','date','team.name'])['id'].count().reset_index()
df_ppdabeyond40_passesteam = df_ppdabeyond40_passesteam.rename(columns={'id': 'passes'})

df_ppdabeyond40_defactions = df_ppdabeyond40[(df_ppdabeyond40['type.primary'].isin(['interception', 'infraction', 'clearance']))]
df_ppdabeyond40_defactionstotal = df_ppdabeyond40_defactions.groupby(['label','date'])['id'].count().reset_index()
df_ppdabeyond40_defactionstotal = df_ppdabeyond40_defactionstotal.rename(columns={'id': 'defactions in game'})
df_ppdabeyond40_defactionsteam = df_ppdabeyond40_defactions.groupby(['label', 'team.name','date'])['id'].count().reset_index()
df_ppdabeyond40_defactionsteam = df_ppdabeyond40_defactionsteam.rename(columns={'id': 'defensive actions'})
df_ppdabeyond40_total = df_ppdabeyond40_defactionstotal.merge(df_ppdabeyond40_passestotal)
df_ppdabeyond40 = df_ppdabeyond40_defactionsteam.merge(df_ppdabeyond40_total)
df_ppdabeyond40 = df_ppdabeyond40.merge(df_ppdabeyond40_passesteam)
df_ppdabeyond40['opponents passes'] = df_ppdabeyond40['passes in game'] - df_ppdabeyond40['passes']
df_ppdabeyond40['PPDA'] = df_ppdabeyond40['opponents passes'] / df_ppdabeyond40['defensive actions']
df_ppda = df_ppdabeyond40[['label', 'team.name','date', 'PPDA']]
df_ppda.to_csv('PPDA.csv', index=False)

penalty_area_entry_condition = (
    (
        (events['pass.endLocation.x'] > 83) & 
        (events['pass.endLocation.y'].between(19, 81)) & 
        (events['pass.accurate'] == True) &
        (
            (events['location.x'] <= 83) | 
            (events['location.y'] < 19) | 
            (events['location.y'] > 81)
        )
    ) |
    (
        (events['carry.endLocation.x'] > 83) &
        (events['carry.endLocation.y'].between(19, 81)) &
        (
            (events['location.x'] <= 83) | 
            (events['location.y'] < 19) | 
            (events['location.y'] > 81)
        )
    )
)
events['penalty_area_entry'] = penalty_area_entry_condition

penalty_area_entries = events[['team.name', 'label','date','location.x', 'location.y','pass.endLocation.x', 'pass.endLocation.y', 'carry.endLocation.x', 'carry.endLocation.y', 'penalty_area_entry']]
penalty_area_entries = penalty_area_entries[penalty_area_entries['penalty_area_entry'] == True]
penalty_area_entries.to_csv('penalty_area_entries.csv', index=False)
penalty_area_entry_counts = penalty_area_entries.groupby(['label','date', 'team.name'])['penalty_area_entry'].sum()

penalty_area_entry_counts = penalty_area_entry_counts.reset_index()

penalty_area_entry_counts = penalty_area_entry_counts.rename(columns={'penalty_area_entry': 'count'})
penalty_area_entry_counts.to_csv('penalty_area_entry_counts.csv', index=False)