import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import mplsoccer
from mplsoccer import Pitch
from scipy.ndimage import gaussian_filter
import gspread
import plotly.graph_objs as go
from datetime import datetime
from dateutil import parser
import numpy as np

st.set_page_config(layout="wide")

@st.cache_data()
def load_matchstats():
    #events = pd.read_csv(r'events.csv')
    df_matchstats = pd.read_csv(r'matchstats.csv')    
    return df_matchstats

@st.cache_data()
def load_events():
    events = pd.read_csv(r'events.csv')
    return events

@st.cache_data()
def load_xg():
    df_xg = pd.read_csv(r'xg.csv')    
    return df_xg

@st.cache_data()
def load_xg_agg():
    df_xg_agg = pd.read_csv(r'xg_agg.csv')
    return df_xg_agg

@st.cache_data()
def load_horsens_events():
    events = pd.read_csv(r'events.csv')
    events = events[events['label'].str.contains('Horsens')]
    return events

@st.cache_data()
def load_transitions():
    transitions = pd.read_csv(r'transitions.csv')
    transitions['label'] = transitions['label'] + ' ' + transitions['date']
    return transitions

@st.cache_data()
def load_PPDA():
    df_ppda = pd.read_csv(r'PPDA.csv')
    df_ppda['label'] = df_ppda['label'] + ' ' + df_ppda['date']

    return df_ppda

@st.cache_data()
def load_penalty_area_entry_counts():
    penalty_area_entry_counts = pd.read_csv(r'penalty_area_entry_counts.csv')
    penalty_area_entry_counts['label'] = penalty_area_entry_counts['label'] + ' ' + penalty_area_entry_counts['date']
    return penalty_area_entry_counts

st.cache_data()
def load_dangerzone_entries():
    dangerzone_entries = pd.read_csv(r'dangerzone_entries.csv')
    dangerzone_entries['label'] = dangerzone_entries['label'] + ' ' + dangerzone_entries['date']
    return dangerzone_entries

@st.cache_data()
def load_penalty_area_entries():
    penalty_area_entries = pd.read_csv(r'penalty_area_entries.csv')
    penalty_area_entries['label'] = penalty_area_entries['label'] + ' ' + penalty_area_entries['date']

    return penalty_area_entries    

@st.cache_data()
def load_possession_stats():
    df_possession_stats = pd.read_csv(r'terr_poss.csv')
    df_possession_stats['label'] = df_possession_stats['label'] + ' ' + df_possession_stats['date']
    return df_possession_stats

@st.cache_data
def load_groundduels():
    groundduels = pd.read_csv(r'groundduels_per_player.csv')
    return groundduels

@st.cache_data()
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

df_matchstats = load_matchstats()
df_xg = load_xg()
df_xg_agg = load_xg_agg()
horsens_events = load_horsens_events()
penalty_area_entry_counts = load_penalty_area_entry_counts()
penalty_area_entries = load_penalty_area_entries()
events = load_events()
groundduels = load_groundduels()

position_dataframes = Process_data_spillere(events,df_xg,df_matchstats,groundduels)
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

players = events['player.name'].unique()
teams = events['team.name'].unique()
def plot_heatmap_location(data, title):
    pitch = Pitch(pitch_type='wyscout', line_zorder=2, pitch_color='grass', line_color='white')
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(data['location.x'], data['location.y'], statistic='count', bins=(50, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='black')
    st.write(title)  # Use st.title() instead of plt.title()
    st.pyplot(fig)

def plot_heatmap_end_location(data, title):
    pitch = Pitch(pitch_type='wyscout', line_zorder=2, pitch_color='grass', line_color='white')
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(data['pass.endLocation.x'], data['pass.endLocation.y'], statistic='count', bins=(50, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='black')
    st.write(title)  # Use st.title() instead of plt.title()
    st.pyplot(fig)

def pass_accuracy(df, kampvalg):
    df = df[df['label'].isin(kampvalg)]
    df_passes = df[df['type.primary'] == 'pass']
    df_accurate = df_passes[df_passes['pass.accurate'] == True]
    if len(df_passes) == 0:
        df_accurate_percent = 0
    else:
        df_accurate_percent = len(df_accurate) / len(df_passes)*100
    df_accurate_percent = round(df_accurate_percent, 2)
    df_pass_accuracy = pd.DataFrame({'Pass Accuracy': [df_accurate_percent]})
    return df_pass_accuracy

def plot_arrows(df):

    pitch = Pitch(pitch_type='wyscout', pitch_color='grass', line_color='white')
    fig, ax = pitch.draw()

    # Plot passes with color based on accuracy
    passes = df[df['pass.endLocation.x'] > 0]
    for _, row in passes.iterrows():
        # Determine arrow color based on pass accuracy
        pass_color ='#90EE90' if row.get('pass.accurate', False) else 'red'
        pitch.arrows(row['location.x'], row['location.y'], row['pass.endLocation.x'], row['pass.endLocation.y'],
                     color=pass_color, ax=ax, width=2, headwidth=3, headlength=3)

    # Plot carries (yellow arrows)
    carries = df[df['carry.endLocation.x'] > 0]
    for _, row in carries.iterrows():
        pitch.arrows(row['location.x'], row['location.y'], row['carry.endLocation.x'], row['carry.endLocation.y'],
                     color='yellow', ax=ax, width=2, headwidth=3, headlength=3)

    # Plot shots (dots with size proportional to shot.xg)
    shots = df[df['shot.xg'] > 0]
    pitch.scatter(shots['location.x'], shots['location.y'], s=shots['shot.xg'] * 100, color='yellow', edgecolors='black', ax=ax, alpha=0.6)

    # Use Streamlit to display the plot
    st.pyplot(fig)
    
def training_ratings():
    gc = gspread.service_account('wellness-1123-178fea106d0a.json')
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1fG0BYf_BbbDIgELdkSGTgjzdT_7pnKDfocUW7TR510I/edit?resourcekey=&gid=201497853#gid=201497853')
    ws = sh.worksheet('Formularsvar 1')
    df = pd.DataFrame(ws.get_all_records())
    df['Tidsstempel'] = pd.to_datetime(df['Tidsstempel'],dayfirst=True, format='%d/%m/%Y %H.%M.%S')

    # Create a new column 'date' with the format 'dd/mm/yyyy'
    df['date'] = df['Tidsstempel'].dt.strftime('%d/%m/%Y')
    # Melt the DataFrame to long format
    df_melted = df.melt(id_vars=['Coach name', 'date','Tidsstempel'], 
                        var_name='Player', 
                        value_name='Rating')

    # Remove 'Rating [' and ']' from Player names
    df_melted['Player'] = df_melted['Player'].str.replace('Rating \[|\]', '', regex=True)
    df_melted['date'] = pd.to_datetime(df_melted['date'], format='%d/%m/%Y')

    # Streamlit app
    st.title("Player Ratings")

    # Main layout filters
    selected_coaches = st.multiselect('Select Coaches', df['Coach name'].unique(), df['Coach name'].unique())
    if st.button('Select All Players'):
        selected_players = df_melted['Player'].unique().tolist()
    elif st.button('Deselect All Players'):
        selected_players = []
    else:
        selected_players = st.multiselect('Select Players', sorted(df_melted['Player'].unique()))
    min_date = pd.to_datetime(df_melted['date'], format='%d/%m/%Y').min().date()
    max_date = pd.to_datetime(df_melted['date'], format='%d/%m/%Y').max().date()
    start_date, end_date = st.date_input('Select Date Range', [min_date, max_date], min_value=min_date, max_value=max_date)

    # Filter DataFrame based on the selected filters
    filtered_df = df_melted[
        (df_melted['Coach name'].isin(selected_coaches)) &
        (df_melted['Player'].isin(selected_players)) &
        (pd.to_datetime(df_melted['date'], format='%d/%m/%Y').dt.date >= start_date) &
        (pd.to_datetime(df_melted['date'], format='%d/%m/%Y').dt.date <= end_date)
    ]
        
    # Drop rows where Rating is NaN
    filtered_df = filtered_df[['date','Player', 'Rating','Coach name']]
    # Ensure 'Rating' column is numeric
    filtered_df = filtered_df[['date','Player', 'Rating']]
    filtered_df.replace('', pd.NA, inplace=True)

    # Filter out rows where the 'rating' column has NaN values
    filtered_df = filtered_df.dropna(subset=['Rating'])

    # Calculate the average ratings, ignoring None values
    average_ratings = filtered_df.groupby(['Player', 'date'])['Rating'].mean().reset_index()
    average_of_period = average_ratings.groupby('Player')['Rating'].mean().reset_index()
    average_of_period['Rating'] = average_of_period['Rating'].astype(float)
    average_of_period['Rating'] = average_of_period['Rating'].round(2)

    average_of_period = average_of_period.sort_values('Rating', ascending=False)
    st.dataframe(average_of_period,hide_index=True)
    fig = go.Figure()

    for player in average_ratings['Player'].unique():
        player_data = average_ratings[average_ratings['Player'] == player]
        fig.add_trace(go.Scatter(
            x=player_data['date'],
            y=player_data['Rating'],
            mode='lines+markers',
            name=player
        ))

    fig.update_layout(
        title='Player Ratings Over Time',
        xaxis_title='Date',
        yaxis_title='Rating',
        yaxis=dict(range=[1, 10]),  # Set y-axis range from 1 to 10        
        width=800,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def wellness():
    try:
        gc = gspread.service_account('wellness-1123-178fea106d0a.json')
        sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/170aa3MNioMs4fxYtCgaS_x73yG6d8Lxb9QOEejilu1w/edit?gid=1576347711#gid=1576347711')
        ws = sh.worksheet('Formularsvar 1')
        df = pd.DataFrame(ws.get_all_records())
        df['Tidsstempel'] = pd.to_datetime(df['Tidsstempel'], dayfirst=True, format='%d/%m/%Y %H.%M.%S')

        df['date'] = df['Tidsstempel'].dt.strftime('%d/%m/%Y')
        number_of_dates = len(df['date'].unique())
        number_of_replies_per_player = df['Player Name'].value_counts()
        
        st.write('Number of replies that should be made:', number_of_dates)
        st.write('Number of replies per player:', number_of_replies_per_player/2)
        col1,col2 = st.columns(2)
        with col1:
            players = st.multiselect('Choose player', sorted(df['Player Name'].unique()))
        
        with col2:
            activity = st.selectbox('Choose activity', df['Questionnaire'].unique())

        df = df[df['Player Name'].isin(players)]
        df = df[df['Questionnaire'] == activity]

        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
        min_date = df['Tidsstempel'].min().to_pydatetime()
        max_date = df['Tidsstempel'].max().to_pydatetime()
        start_date, end_date = st.slider(
            'Select date range',
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="DD/MM/YYYY"
        )

        df = df[(df['Tidsstempel'] >= start_date) & (df['Tidsstempel'] <= end_date)]

        df['date'] = df['date'].dt.strftime('%d/%m/%Y')

        if activity == 'Before activity':
            df = df[['date', 'Player Name', 'Rate your freshness (1 is the best, 7 is the worst)', 'Rate how you feel mentally (1 is the best, 7 is the worst)', 'Have you eaten enough yesterday? (1 is the best, 7 is the worst)', 'Have you eaten enough before the activity? (1 is the best, 7 is the worst)', 'Rate your sleep quality (1 is the best, 7 is the worst)', 'How many hours did you sleep last night?']]
        if activity == 'After activity':
            df = df[['date', 'Player Name', 'Activity length in minutes (only write a number)', 'How hard was the training/match (10 is hardest) ', 'How exausted are you?  (1 is the best, 7 is the worst)', 'Rate your muscle soreness  (1 is the best, 7 is the worst)', 'How do you feel mentally?  (1 is the best, 7 is the worst)', 'I felt suitably challenged during training/match  (1 is the best, 7 is the worst)', 'My sense of time disappeared during training/match   (1 is the best, 7 is the worst)', 'I experienced that thoughts and actions were directed towards training  (1 is the best, 7 is the worst)']]
        
        st.dataframe(df, hide_index=True)
    except KeyError:
        st.write('Choose one or more players')

def player_data():
    events = load_events()
    df_matchstats = load_matchstats()
    balanced_central_defender_df = position_dataframes['Central defender']
    fullbacks_df = position_dataframes['Fullbacks']
    number6_df = position_dataframes['Number 6']
    number8_df = position_dataframes['Number 8']
    number10_df = position_dataframes['Number 10']
    winger_df = position_dataframes['Winger']
    classic_striker_df = position_dataframes['Classic striker']

    col1, col2 = st.columns(2)

    with col1:
        # Filter out non-string values, drop NaN, ensure uniqueness, and sort alphabetically
        team_name = st.selectbox('Choose team', sorted(set([name for name in events['team.name'].dropna() if isinstance(name, str)])))

    events = events[events['team.name'] == team_name]
    with col2:
        # Filter out non-string values, drop NaN, ensure uniqueness, and sort alphabetically
        player_name = st.selectbox('Choose player', sorted(set([name for name in events['player.name'].dropna() if isinstance(name, str)])))

    st.title(f'{player_name} dashboard')    
    df = events[(events['player.name'] == player_name)|(events['pass.recipient.name'] == player_name)]
    df = df[~df['type.primary'].isin(['corner', 'free_kick', 'throw_in'])]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date',ascending=False)
    kampe = df['label'].unique()
    kampvalg = st.multiselect('Choose matches', kampe, kampe[0:3])
    df = df[df['label'].isin(kampvalg)]
    df_matchstats_player = df_matchstats[(df_matchstats['player.name'] == player_name) & (df_matchstats['label'].isin(kampvalg))]
    df_matchstats_player['date'] = pd.to_datetime(df_matchstats_player['date'])
    df_matchstats_player = df_matchstats_player.sort_values(by='date')
    balanced_central_defender_df = balanced_central_defender_df[(balanced_central_defender_df['label'].isin(kampvalg)) & (balanced_central_defender_df['player.name'] == player_name)]
    fullbacks_df = fullbacks_df[(fullbacks_df['label'].isin(kampvalg)) & (fullbacks_df['player.name'] == player_name)]
    number6_df = number6_df[(number6_df['label'].isin(kampvalg)) & (number6_df['player.name'] == player_name)]
    number8_df = number8_df[(number8_df['label'].isin(kampvalg)) & (number8_df['player.name'] == player_name)]
    number10_df = number10_df[(number10_df['label'].isin(kampvalg)) & (number10_df['player.name'] == player_name)]
    winger_df = winger_df[(winger_df['label'].isin(kampvalg)) & (winger_df['player.name'] == player_name)]
    classic_striker_df = classic_striker_df[(classic_striker_df['label'].isin(kampvalg)) & (classic_striker_df['player.name'] == player_name)]
    balanced_central_defender_df = balanced_central_defender_df.drop(columns=['player.name', 'team.name', 'position_codes'],errors = 'ignore')
    fullbacks_df = fullbacks_df.drop(columns=['player.name', 'team.name', 'position_codes'],errors = 'ignore')
    number6_df = number6_df.drop(columns=['player.name','team.name','position_codes'],errors = 'ignore')
    number8_df = number8_df.drop(columns=['player.name','team.name','position_codes'],errors = 'ignore')
    number10_df = number10_df.drop(columns=['player.name', 'team.name', 'position_codes'],errors = 'ignore')
    winger_df = winger_df.drop(columns=['player.name', 'team.name', 'position_codes'],errors = 'ignore')
    classic_striker_df = classic_striker_df.drop(columns=['player.name', 'team.name', 'position_codes'],errors = 'ignore')
        
    if not balanced_central_defender_df.empty:
        st.write('As central defender')
        st.dataframe(balanced_central_defender_df, hide_index=True)

    if not fullbacks_df.empty:
        st.write('As fullback')
        st.dataframe(fullbacks_df, hide_index=True)

    if not number6_df.empty:
        st.write('As number 6')
        st.dataframe(number6_df, hide_index=True)

    if not number8_df.empty:
        st.write('As number 8')
        st.dataframe(number8_df, hide_index=True)

    if not number10_df.empty:
        st.write('As number 10')
        st.dataframe(number10_df, hide_index=True)

    if not winger_df.empty:
        st.write('As winger')
        st.dataframe(winger_df, hide_index=True)

    if not classic_striker_df.empty:
        st.write('As classic striker')
        st.dataframe(classic_striker_df, hide_index=True)


    Bolde_modtaget = df[df['pass.recipient.name'] == player_name]
    Bolde_modtaget_til = Bolde_modtaget[['pass.endLocation.x','pass.endLocation.y']]

    Pasninger_spillet = df[(df['type.primary'] == 'pass') & (df['pass.accurate'] == True)]
    Pasninger_spillet_til = Pasninger_spillet[['pass.endLocation.x','pass.endLocation.y']]

    Defensive_aktioner = df[(df['type.primary'] == 'interception') | (df['type.primary'] == 'duel') | (df['type.primary'] == 'clearance') | (df['type.primary'] == 'infraction')]
    Defensive_aktioner = Defensive_aktioner[['location.x','location.y']]
    
    
    col1,col2,col3 = st.columns(3)

    with col1:
        plot_heatmap_location(Defensive_aktioner, f'Defensive actions taken by {player_name}')

    with col2:
        plot_heatmap_end_location(Bolde_modtaget_til, f'Passes recieved {player_name}')
                
    with col3:
        plot_heatmap_end_location(Pasninger_spillet_til, f'Passes {player_name}')
    df = df[df['player.name'] == player_name]
    plot_arrows(df)

def dashboard():
    st.title('U19 Dashboard')
    xg = load_xg_agg()
    df_ppda = load_PPDA()
    penareaentries = load_penalty_area_entry_counts()
    df_possession_stats = load_possession_stats()
    dangerzone_entries = load_dangerzone_entries()
    dangerzone_entries['team.name'] = dangerzone_entries['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    events = load_horsens_events()
    events['label'] = events['label'] + ' ' + events['date']
    events['date'] = pd.to_datetime(events['date'],utc=True)
    events = events.sort_values('date').reset_index(drop=True)
    events = events[events['team.name'].str.contains('Horsens')]
    matches = events['label'].unique()
    matches = matches[::-1]
    match_choice = st.multiselect('Choose a match', matches)
    df_xg = load_xg()
    df_xg['label'] = df_xg['label'] + ' ' + df_xg['date']
    df_xg = df_xg.drop(columns=['date'],errors = 'ignore')
    events['team.name'] = events['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    df_xg['team.name'] = df_xg['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')

    df_matchstats = load_matchstats()
    df_matchstats['label'] = df_matchstats['label'] + ' ' + df_matchstats['date']
    df_matchstats = df_matchstats.drop(columns=['date'],errors = 'ignore')

    df_xg = df_xg[df_xg['label'].isin(match_choice)]
    df_possession_stats = df_possession_stats[df_possession_stats['label'].isin(match_choice)]
    df_matchstats = df_matchstats[df_matchstats['label'].isin(match_choice)]
    penareaentries = penareaentries[penareaentries['label'].isin(match_choice)]
    dangerzone_entries = dangerzone_entries[dangerzone_entries['label'].isin(match_choice)]
    df_matchstats = df_matchstats.drop_duplicates()
    df_matchstats['team.name'] = df_matchstats['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    df_passes = df_matchstats[['team.name','label','average_forwardPasses','average_successfulForwardPasses']]

    df_passes = df_passes.groupby(['team.name','label']).sum().reset_index()

    df_xg_summary = df_xg.groupby(['team.name','label'])['shot.xg'].sum().reset_index()
    df_ppda = df_ppda[df_ppda['label'].isin(match_choice)]
    df_ppda = df_ppda.groupby(['team.name','label'])['PPDA'].sum().reset_index()
    df_ppda = df_ppda.drop(columns=['date'],errors = 'ignore')
    df_ppda['team.name'] = df_ppda['team.name'] = df_ppda['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    penareaentries = penareaentries.groupby(['team.name','label']).sum().reset_index()
    penareaentries = penareaentries.rename(columns={'count':'penaltyAreaEntryCount'})
    penareaentries['team.name'] = penareaentries['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    penareaentries = penareaentries.drop(columns=['date'],errors = 'ignore')
    df_possession_stats = df_possession_stats.value_counts(['territorial_possession','label']).reset_index()
    df_possession_stats_grouped = df_possession_stats.groupby('label')['count'].sum().reset_index()
    df_possession_stats_grouped.columns = ['label', 'total_possession']

    # Merge back with original dataframe to calculate percentage
    df_possession_stats = pd.merge(df_possession_stats, df_possession_stats_grouped, on='label')

    # Calculate the possession percentage
    df_possession_stats['terr_poss %'] = (df_possession_stats['count'] / df_possession_stats['total_possession']) * 100

    # Drop unnecessary columns if needed
    df_possession_stats = df_possession_stats.drop(columns=['total_possession','count'])
    df_possession_stats = df_possession_stats[df_possession_stats['territorial_possession'] != 'Middle']
    df_possession_stats = df_possession_stats.rename(columns={'territorial_possession':'team.name'})
    df_possession_stats['team.name'] = df_possession_stats['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    dangerzone_entries = dangerzone_entries.value_counts(['team.name','label']).reset_index()
    dangerzone_entries = dangerzone_entries.rename(columns={'count':'dangerzoneEntryCount'})
    team_summary = df_xg_summary.merge(df_passes, on=['team.name','label'])
    team_summary = team_summary.merge(penareaentries, on=['team.name','label'])
    team_summary = team_summary.merge(dangerzone_entries, on=['team.name','label'])
    team_summary = team_summary.merge(df_ppda, on=['team.name','label'])
    team_summary = team_summary.merge(df_possession_stats, on=['team.name','label'])
    team_summary = team_summary.drop(columns=['label'])
    team_summary = team_summary.groupby('team.name').mean().reset_index()
    team_summary = team_summary.round(2)
    st.dataframe(team_summary.style.format(precision=2), use_container_width=True,hide_index=True)
    

    def xg():
        df_xg = load_xg()
        df_xg_agg = load_xg_agg()

        all_xg = df_xg.copy()
        df_xg1 = df_xg.copy()
        all_xg['label'] = all_xg['label'] + ' ' + all_xg['date']
        df_xg_agg['label'] = df_xg_agg['label'] + ' ' + df_xg_agg['date']

        all_xg['date'] = pd.to_datetime(all_xg['date'], utc=True)
        all_xg = all_xg.sort_values('date').reset_index(drop=True)
        all_xg['match_xg'] = all_xg.groupby('label')['shot.xg'].transform('sum')
        all_xg['team_xg'] = all_xg.groupby(['label', 'team.name'])['shot.xg'].transform('sum')
        all_xg['xg_diff'] = all_xg['team_xg'] - all_xg['match_xg'] + all_xg['team_xg']
        all_xg['xG rolling average'] = all_xg.groupby('team.name')['xg_diff'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        fig = go.Figure()
        
        for team in all_xg['team.name'].unique():
            team_data = all_xg[all_xg['team.name'] == team]
            line_size = 5 if team == 'Horsens U19' else 1  # Larger line for Horsens
            fig.add_trace(go.Scatter(
                x=team_data['date'], 
                y=team_data['xG rolling average'], 
                mode='lines',
                name=team,
                line=dict(width=line_size)
            ))
        
        fig.update_layout(
            title='3-Game Rolling Average of xG Difference Over Time',
            xaxis_title='Date',
            yaxis_title='3-Game Rolling Average xG Difference',
            template='plotly_white'
        )
        st.header('Whole season')
        
        st.plotly_chart(fig)

        all_xg = all_xg[['team.name','xg_diff']]
        all_xg = all_xg.drop_duplicates()
        all_xg = all_xg.groupby('team.name')['xg_diff'].sum().reset_index()
        all_xg = all_xg.sort_values('xg_diff', ascending=False)
        df_xg['label'] = df_xg['label'] + ' ' + df_xg['date']
        df_xg1['label'] = df_xg1['label'] + ' ' + df_xg1['date']

        df_xg = df_xg[df_xg['label'].isin(match_choice)]
        df_xg1 = df_xg1[df_xg1['label'].isin(match_choice)]

        df_xg['match_xg'] = df_xg.groupby('label')['shot.xg'].transform('sum')
        df_xg['team_xg'] = df_xg.groupby(['label','team.name'])['shot.xg'].transform('sum')
        df_xg['xg_diff'] = df_xg['team_xg'] - df_xg['match_xg'] + df_xg['team_xg']
        df_xg = df_xg[['team.name','xg_diff']]
        df_xg = df_xg.drop_duplicates()
        df_xg = df_xg[df_xg['team.name'].str.contains('Horsens')]
        df_xg = df_xg.groupby('team.name')['xg_diff'].sum().reset_index()
        st.dataframe(all_xg, hide_index=True)
        st.header('Chosen matches')
        st.dataframe(df_xg, hide_index=True)
        df_xg1['team.name'] = df_xg1['team.name'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
        df_xg1 = df_xg1.sort_values(by=['team.name','minute'])

        df_xg1['cumulative_xG'] = df_xg1.groupby(['team.name'])['shot.xg'].cumsum()
        fig = go.Figure()
        
        for team in df_xg1['team.name'].unique():
            team_data = df_xg1[df_xg1['team.name'] == team]
            fig.add_trace(go.Scatter(
                x=team_data['minute'], 
                y=team_data['cumulative_xG'], 
                mode='lines',
                name=team,
            ))
        
        fig.update_layout(
            title='Average Cumulative xG Over Time',
            xaxis_title='Time (Minutes)',
            yaxis_title='Average Cumulative xG',
            template='plotly_white'
        )
        st.plotly_chart(fig)
        df_xg_agg = df_xg_agg[df_xg_agg['label'].isin(match_choice)]    
        df_xg_plot = df_xg_agg[['player.name','team.name','location.x','location.y', 'shot.xg']]
        df_xg_plot = df_xg_plot[df_xg_plot['team.name'] == 'Horsens U19']
        pitch = Pitch(pitch_type='wyscout',half=True,line_color='white', pitch_color='grass')
        fig, ax = pitch.draw(figsize=(10, 6))
        
        sc = ax.scatter(df_xg_plot['location.x'], df_xg_plot['location.y'], s=df_xg_plot['shot.xg'] * 100, c='yellow', edgecolors='black', alpha=0.6)
        
        for i, row in df_xg_plot.iterrows():
            ax.text(row['location.x'], row['location.y'], f"{row['player.name']}\n{row['shot.xg']:.2f}", fontsize=6, ha='center', va='center')
        
        st.pyplot(fig)
        df_xg_plot = df_xg_plot.groupby(['player.name'])['shot.xg'].sum().reset_index()
        df_xg_plot = df_xg_plot.sort_values('shot.xg', ascending=False)
        st.dataframe(df_xg_plot, hide_index=True)
        
    def offensive_transitions():
        st.header('Whole season')
        st.write('Transition xg')
        transitions = load_transitions()
        low_transitions = transitions[transitions['location.x'] < 33]
        mid_transitions = transitions[
            (transitions['location.x'] >= 33) & 
            (transitions['location.x'] < 66) & 
            (transitions['possession.eventsNumber'] < 12)
        ]       
        high_transitions = transitions[(transitions['location.x'] >= 66) & (transitions['possession.eventsNumber'] < 8)]
        transitions = pd.concat([low_transitions, mid_transitions, high_transitions])
        transitions = transitions.sort_values('date', ascending=False)
        transitionxg_chosen = transitions[transitions['label'].isin(match_choice)]
        transitionxg_chosen = transitionxg_chosen.groupby(['team.name','label','date'])['shot.xg'].sum().reset_index()
        transitionxg_chosen = transitionxg_chosen.sort_values('date', ascending=False)
        transitionxg_chosen = transitionxg_chosen[['team.name','label','shot.xg']]
        transitionxg = transitions.groupby(['team.name'])['shot.xg'].sum().reset_index()
        transitionxg_diff = transitions.copy()
        transitionxg = transitionxg.sort_values('shot.xg', ascending=False)
        transitionxg_diff['match_xg'] = transitionxg_diff.groupby('label')['shot.xg'].transform('sum')
        transitionxg_diff['team_xg'] = transitionxg_diff.groupby(['label', 'team.name'])['shot.xg'].transform('sum')
        transitionxg_diff['xg_diff'] = transitionxg_diff['team_xg'] - transitionxg_diff['match_xg'] + transitionxg_diff['team_xg']
        transitionxg_diff = transitionxg_diff[['team.name','label','xg_diff']]
        transitionxg_diff_chosen = transitionxg_diff[transitionxg_diff['label'].isin(match_choice)]
        transitionxg_diff_chosen = transitionxg_diff_chosen.drop_duplicates()
        transitionxg_diff = transitionxg_diff.drop_duplicates()
        transitionxg_diff = transitionxg_diff.groupby('team.name')['xg_diff'].sum().reset_index()
        transitionxg_diff = transitionxg_diff.sort_values('xg_diff', ascending=False)
        st.dataframe(transitionxg_diff,hide_index=True)
        st.dataframe(transitionxg,hide_index=True)
        st.header('Chosen matches')
        transitionxg_chosen = transitionxg_chosen[transitionxg_chosen['team.name'] == 'Horsens U19']
        transitionxg_chosen = transitionxg_chosen.sort_values('shot.xg',ascending=False)
        transitionxg_diff_chosen = transitionxg_diff_chosen[transitionxg_diff_chosen['team.name'] == 'Horsens U19']
        transitionxg_diff_chosen = transitionxg_diff_chosen.sort_values('xg_diff',ascending=False)

        st.dataframe(transitionxg_chosen, hide_index=True)
        st.dataframe(transitionxg_diff_chosen, hide_index=True)
        
        st.write('Interceptions/recoveries that lead to a chance')
        chance_start = transitions[transitions['team.name'].str.contains('Horsens')]
        chance_start = chance_start[chance_start['label'].isin(match_choice)]
        chance_start = chance_start[chance_start['possession.attack.xg'] > 0.1]
        chance_start_plot = chance_start[chance_start['possession.eventIndex'] == 0]
        pitch = mplsoccer.Pitch(pitch_type='wyscout', line_zorder=2,pitch_color='grass')
        fig, ax = pitch.draw(figsize=(10, 7))

        # Plot the data
        sc = ax.scatter(
            chance_start_plot['location.x'],
            chance_start_plot['location.y'],
            s=chance_start_plot['possession.attack.xg'] * 1000,  # Scale dot size
            c='yellow',
            edgecolors='black',
            linewidth=1.5,
            alpha=0.7
        )
        for i, row in chance_start_plot.iterrows():
            label = f"{row['player.name']}\n{row['possession.attack.xg']:.2f}"
            ax.annotate(label, (row['location.x'], row['location.y']),
                        fontsize=8, ha='center', va='bottom', color='black', weight='bold',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='black'))

        # Display the plot in Streamlit
        st.pyplot(fig)
        st.write('Player involvement')
        player_involvement = chance_start.groupby(['player.name'])['possession.attack.xg'].sum().reset_index()
        player_involvement = player_involvement.sort_values('possession.attack.xg', ascending=False)
        st.dataframe(player_involvement, hide_index=True)

    def chance_creation():
        st.header('Whole season')
        penalty_area_entries = load_penalty_area_entries()
        dangerzone_entries = load_dangerzone_entries()
        dangerzone_entries_per_team = dangerzone_entries.groupby(['team.name'])['dangerzone_entry'].sum().reset_index()
        dangerzone_entries_per_team = dangerzone_entries_per_team.sort_values('dangerzone_entry', ascending=False)
        penalty_area_entries_per_team = penalty_area_entries.groupby(['team.name'])['penalty_area_entry'].sum().reset_index()
        penalty_area_entries_per_team = penalty_area_entries_per_team.sort_values('penalty_area_entry', ascending=False)
        penalty_area_entries_per_team = penalty_area_entries_per_team.merge(dangerzone_entries_per_team,how='outer', on='team.name')
        penalty_area_entries_per_team = penalty_area_entries_per_team.fillna(0)
        st.dataframe(penalty_area_entries_per_team, hide_index=True)
        st.header('Chosen matches')
        st.write('Penalty area entries')
        penalty_area_entries_matches = penalty_area_entries[penalty_area_entries['label'].isin(match_choice)]
        player_penalty_area_entries = penalty_area_entries_matches[penalty_area_entries_matches['team.name'] == 'Horsens U19']
        player_penalty_area_received = player_penalty_area_entries.groupby(['pass.recipient.name'])['penalty_area_entry'].sum().reset_index()
        player_penalty_area_entries = player_penalty_area_entries.groupby(['player.name'])['penalty_area_entry'].sum().reset_index()
        penalty_area_entries_location = penalty_area_entries_matches.copy()
        penalty_area_entries_matches['Whole match'] = penalty_area_entries_matches.groupby('label')['penalty_area_entry'].transform('sum')
        penalty_area_entries_matches['Team'] = penalty_area_entries_matches.groupby(['label', 'team.name'])['penalty_area_entry'].transform('sum')
        penalty_area_entries_matches['Paentries Diff'] = penalty_area_entries_matches['Team'] - penalty_area_entries_matches['Whole match'] + penalty_area_entries_matches['Team']
        penalty_area_entries_matches = penalty_area_entries_matches[['team.name','label', 'Paentries Diff']]
        penalty_area_entries_matches = penalty_area_entries_matches[penalty_area_entries_matches['team.name'] == 'Horsens U19']
        penalty_area_entries_matches = penalty_area_entries_matches.round(2)
        penalty_area_entries_matches = penalty_area_entries_matches.sort_values('Paentries Diff', ascending=False)
        penalty_area_entries_matches = penalty_area_entries_matches.drop_duplicates(keep='first')
        st.dataframe(penalty_area_entries_matches,hide_index=True)
        penalty_area_entries_location['endLocation.x'] = penalty_area_entries_location['pass.endLocation.x'].combine_first(penalty_area_entries_location['carry.endLocation.x'])
        penalty_area_entries_location['endLocation.y'] = penalty_area_entries_location['pass.endLocation.y'].combine_first(penalty_area_entries_location['carry.endLocation.y'])
        option2 = st.selectbox(
            'Select the position',
            ('Start', 'End'),key='1'
        )

        # Initialize the pitch
        pitch = Pitch(pitch_type='wyscout',line_zorder=2, pitch_color='grass', line_color='white')
        fig, ax = pitch.draw()

        # Extract coordinates based on user selection
        if option2 == 'Start':
            x_coords = penalty_area_entries_location['location.x']
            y_coords = penalty_area_entries_location['location.y']
        elif option2 == 'End':
            x_coords = penalty_area_entries_location['endLocation.x']
            y_coords = penalty_area_entries_location['endLocation.y']

        # Plot the heatmap
        fig.set_facecolor('#22312b')
        bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(50, 50))  # Adjust bins as needed
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
        pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b')

        # Display the plot in Streamlit
        st.pyplot(fig)
        player_penalty_area_received = player_penalty_area_received.rename(columns={'pass.recipient.name': 'player.name','penalty_area_entry': 'penalty_area_received'})
        player_penalty_area_entries['penalty_area_entry'] = pd.to_numeric(player_penalty_area_entries['penalty_area_entry'], errors='coerce').fillna(0)
        player_penalty_area_received['penalty_area_received'] = pd.to_numeric(player_penalty_area_received['penalty_area_received'], errors='coerce').fillna(0)
        player_penalty_area_entries = player_penalty_area_entries.merge(player_penalty_area_received, on='player.name', how='outer')
        player_penalty_area_entries = player_penalty_area_entries.fillna(0)
        player_penalty_area_entries['Total'] = player_penalty_area_entries['penalty_area_entry'] + player_penalty_area_entries['penalty_area_received']
        player_penalty_area_entries = player_penalty_area_entries.sort_values('Total', ascending=False)

        st.dataframe(player_penalty_area_entries,hide_index=True)
        # Display the plot in Streamlit
        
        st.write('Dangerzone entries')
        dangerzone_entries_matches = dangerzone_entries[dangerzone_entries['label'].isin(match_choice)]
        player_dangerzone_entries = dangerzone_entries_matches[dangerzone_entries_matches['team.name'] == 'Horsens U19']
        player_dangerzone_received = player_dangerzone_entries.groupby(['pass.recipient.name'])['dangerzone_entry'].sum().reset_index()
        player_dangerzone_entries = player_dangerzone_entries.groupby(['player.name'])['dangerzone_entry'].sum().reset_index()

        dangerzone_entries_location = dangerzone_entries_matches.copy()
        dangerzone_entries_matches['Whole match'] = dangerzone_entries_matches.groupby('label')['dangerzone_entry'].transform('sum')
        dangerzone_entries_matches['Team'] = dangerzone_entries_matches.groupby(['label', 'team.name'])['dangerzone_entry'].transform('sum')
        dangerzone_entries_matches['Dzentries Diff'] = dangerzone_entries_matches['Team'] - dangerzone_entries_matches['Whole match'] + dangerzone_entries_matches['Team']
        dangerzone_entries_matches = dangerzone_entries_matches[['team.name','label', 'Dzentries Diff']]
        dangerzone_entries_matches = dangerzone_entries_matches.groupby(['team.name','label'])['Dzentries Diff'].sum().reset_index()
        dangerzone_entries_matches = dangerzone_entries_matches[dangerzone_entries_matches['team.name'] == 'Horsens U19']
        dangerzone_entries_matches = dangerzone_entries_matches.round(2)
        dangerzone_entries_matches = dangerzone_entries_matches.sort_values('Dzentries Diff', ascending=False)
        st.dataframe(dangerzone_entries_matches,hide_index=True)
        dangerzone_entries_location['endLocation.x'] = dangerzone_entries_location['pass.endLocation.x'].combine_first(dangerzone_entries_location['carry.endLocation.x'])
        dangerzone_entries_location['endLocation.y'] = dangerzone_entries_location['pass.endLocation.y'].combine_first(dangerzone_entries_location['carry.endLocation.y'])
        dangerzone_entries_location = dangerzone_entries_location[dangerzone_entries_location['team.name'] == 'Horsens U19']
        option3 = st.selectbox(
            'Select the position',
            ('Start', 'End'),key='2'
        )

        # Initialize the pitch
        pitch = Pitch(pitch_type='wyscout',line_zorder=2, pitch_color='grass', line_color='white')
        fig, ax = pitch.draw()

        # Extract coordinates based on user selection
        if option3 == 'Start':
            x_coords = dangerzone_entries_location['location.x']
            y_coords = dangerzone_entries_location['location.y']
        elif option3 == 'End':
            x_coords = dangerzone_entries_location['endLocation.x']
            y_coords = dangerzone_entries_location['endLocation.y']

        # Plot the heatmap
        fig.set_facecolor('#22312b')
        bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(50, 50))  # Adjust bins as needed
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
        pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b')

        # Display the plot in Streamlit
        st.pyplot(fig)
        player_dangerzone_received = player_dangerzone_received.rename(columns={'pass.recipient.name': 'player.name','dangerzone_entry': 'dangerzone_received'})
        player_dangerzone_entries = player_dangerzone_entries.merge(player_dangerzone_received,how='outer')
        player_dangerzone_entries = player_dangerzone_entries.fillna(0)
        player_dangerzone_entries['Total'] = player_dangerzone_entries['dangerzone_entry'] + player_dangerzone_entries['dangerzone_received']
        player_dangerzone_entries = player_dangerzone_entries.sort_values('Total', ascending=False)
        st.dataframe(player_dangerzone_entries,hide_index=True)
    
    def pressing():
        st.header('Whole season')
        ppda = load_PPDA()
        ppda['date'] = pd.to_datetime(ppda['date'], utc=True)
        ppda = ppda.sort_values('date').reset_index(drop=True)
        ppda['ppda rolling average'] = ppda.groupby('team.name')['PPDA'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        fig = go.Figure()
        
        for team in ppda['team.name'].unique():
            team_data = ppda[ppda['team.name'] == team]
            line_size = 5 if team == 'Horsens U19' else 1  # Larger line for Horsens
            fig.add_trace(go.Scatter(
                x=team_data['date'], 
                y=team_data['PPDA'], 
                mode='lines',
                name=team,
                line=dict(width=line_size)
            ))
        
        fig.update_layout(
            title='3-Game Rolling Average of ppda Over Time',
            xaxis_title='Date',
            yaxis_title='3-Game Rolling Average ppda',
            template='plotly_white'
        )
        
        st.plotly_chart(fig)

        ppda_sæson = ppda[['team.name', 'PPDA']].groupby(['team.name'])['PPDA'].mean().reset_index()
        ppda_sæson = ppda_sæson.sort_values('PPDA',ascending=True)
        st.dataframe(ppda_sæson, hide_index=True)
        ppda_horsens = ppda_sæson[ppda_sæson['team.name'] == 'Horsens U19']
        ppda_sæson_gennemsnit = ppda_horsens['PPDA'].values[0]  # Extracting the value
        st.header('Chosen matches')
        ppda_kampe = ppda[ppda['label'].isin(match_choice)]
        ppda_kampe = ppda_kampe[['team.name','label','PPDA']]
        ppda_kampe = ppda_kampe[ppda_kampe['team.name'] == 'Horsens U19']
        ppda_kampe = ppda_kampe.sort_values('PPDA', ascending=True)
        def format_label(label):
    # Split the label into parts and add a line break after the match result
            parts = label.split(',')
            if len(parts) >= 3:
                return f"{parts[0]}, {parts[1]}<br>{parts[2]}"
            return label

# Apply the label formatting
        ppda_kampe['formatted_label'] = ppda_kampe['label'].apply(format_label)

        st.dataframe(ppda_kampe[['label','PPDA']], hide_index=True)
        fig = go.Figure()

        # Add bars for the PPDA of chosen matches
        fig.add_trace(go.Bar(
            x=ppda_kampe['formatted_label'],
            y=ppda_kampe['PPDA'],
            name='PPDA per Match',
            marker_color='blue'
        ))

        # Add a horizontal line for the season average PPDA
        fig.add_trace(go.Scatter(
            x=ppda_kampe['formatted_label'],
            y=[ppda_sæson_gennemsnit] * len(ppda_kampe['label']),
            mode='lines',
            name=f'Season Avg: {ppda_sæson_gennemsnit:.2f}',
            line=dict(color='red', dash='dash')
        ))

        # Update layout for better readability
        fig.update_layout(
            title='PPDA for Chosen Matches (Horsens U19)',
            yaxis_title='PPDA',
            xaxis_tickangle=90,  # Angle x-axis labels for better readability
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            height=500
        )

        # Display the plot in Streamlit
        st.plotly_chart(fig)

        
    Data_types = {
        'xG': xg,
        'Offensive transitions': offensive_transitions,
        'Chance Creation': chance_creation,
        'Pressing': pressing
    }

    for i in range(1, 4):
        if f'selected_data{i}' not in st.session_state:
            st.session_state[f'selected_data{i}'] = ''

    # Create three columns for select boxes
    col1, col2, col3 = st.columns(3)

    # Function to create selectbox and update session state without rerunning entire page
    def create_selectbox(column, key):
        with column:
            selected_data = st.selectbox(f'Choose data type {key[-1]}', [''] + list(Data_types.keys()), key=key)
            if selected_data and selected_data != st.session_state[key]:
                st.session_state[key] = selected_data
                st.experimental_rerun()

    # Create select boxes for each column
    create_selectbox(col1, 'selected_data1')
    create_selectbox(col2, 'selected_data2')
    create_selectbox(col3, 'selected_data3')

    # Display the current selection results in columns
    with col1:
        if st.session_state['selected_data1']:
            Data_types[st.session_state['selected_data1']]()

    with col2:
        if st.session_state['selected_data2']:
            Data_types[st.session_state['selected_data2']]()

    with col3:
        if st.session_state['selected_data3']:
            Data_types[st.session_state['selected_data3']]()

def opposition_analysis():
    # Display the full dataframe
    df_matchstats = load_matchstats()
    df_matchstats['label'] = df_matchstats['label'] + ' ' + df_matchstats['date']
    df_PPDA = load_PPDA()
    df_PPDA['PPDA'] = df_PPDA['PPDA'].round(2)
    # Correct the date format in 'date' column if necessary
    df_matchstats['date'] = df_matchstats['date'].str.replace(r'GMT\+(\d)$', r'GMT+0\1:00')
    df_PPDA['date'] = df_PPDA['date'].str.replace(r'GMT\+(\d)$', r'GMT+0\1:00')
    df_matchstats = df_matchstats.groupby(['team.name','label', 'date']).sum().reset_index()
    df_matchstats = df_matchstats.merge(df_PPDA, on=['team.name','label','date'], how='left')

    df_matchstats['label'] = np.where(df_matchstats['label'].notnull(), 1, df_matchstats['label'])

    # Convert the 'date' column to datetime objects with mixed format handling
    df_matchstats['date'] = pd.to_datetime(df_matchstats['date'], format='mixed', errors='coerce')

    # Ensure all datetime objects are timezone-naive (remove timezones)
    df_matchstats['date'] = df_matchstats['date'].dt.tz_convert(None)
    df_matchstats = df_matchstats.dropna(subset=['date'])
    # Drop rows where date parsing failed (NaT)
    df_matchstats['date'] = df_matchstats['date'].astype(str)
    df_matchstats['date'] = df_matchstats['date'].str.slice(0, -9)
    df_matchstats['date'] = pd.to_datetime(df_matchstats['date'], format='%Y-%m-%d')
    date_format = '%Y-%m-%d'
    df_matchstats['date'] = pd.to_datetime(df_matchstats['date'], format=date_format)
    min_date = df_matchstats['date'].min()
    max_date = df_matchstats['date'].max()

    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    date_options = date_range.strftime(date_format)  # Convert dates to the specified format

    default_end_date = date_options[-1]

    default_end_date_dt = pd.to_datetime(default_end_date, format=date_format)
    default_start_date_dt = default_end_date_dt - pd.Timedelta(days=2)  # Subtract 14 days
    default_start_date = default_start_date_dt.strftime(date_format)  # Convert to string

    # Set the default start and end date values for the select_slider
    selected_start_date, selected_end_date = st.select_slider(
        'Choose dates',
        options=date_options,
        value=(min_date.strftime(date_format), max_date.strftime(date_format))
    )
    
    selected_start_date = pd.to_datetime(selected_start_date, format=date_format)
    selected_end_date = pd.to_datetime(selected_end_date, format=date_format)
    df_matchstats = df_matchstats[
        (df_matchstats['date'] >= selected_start_date) & (df_matchstats['date'] <= selected_end_date)
    ]    
    df_matchstats = df_matchstats.drop(columns=['date','player.id','player.name','matchId','position_names','position_codes'])
    # Perform aggregation
    df_matchstats = df_matchstats.groupby(['team.name']).agg({
        'label': 'sum',
        'total_duels': 'sum',
        'total_duelsWon': 'sum',
        'total_defensiveDuels': 'sum',
        'total_defensiveDuelsWon': 'sum',
        'total_aerialDuelsWon': 'sum',
        'total_passes': 'sum',
        'total_smartPasses': 'sum',
        'total_successfulSmartPasses': 'sum',
        'total_passesToFinalThird': 'sum',
        'total_successfulPassesToFinalThird': 'sum',
        'total_crosses': 'sum',
        'total_successfulCrosses': 'sum',
        'total_forwardPasses': 'sum',
        'total_successfulForwardPasses': 'sum',
        'total_longPasses': 'sum',
        'total_recoveries': 'sum',
        'total_opponentHalfRecoveries': 'sum',
        'total_losses': 'sum',
        'total_ownHalfLosses': 'sum',
        'total_touchInBox': 'sum',
        'total_progressivePasses': 'sum',
        'total_counterpressingRecoveries': 'sum',
        'PPDA': 'mean'  # Keep PPDA as mean for the team
    }).reset_index()


    # Create "per match" columns by dividing by 'label', excluding PPDA
    columns_to_per_match = [
        'total_duels', 'total_duelsWon', 'total_defensiveDuels',
        'total_defensiveDuelsWon', 'total_aerialDuelsWon', 'total_passes',
        'total_smartPasses', 'total_successfulSmartPasses', 'total_passesToFinalThird',
        'total_successfulPassesToFinalThird', 'total_crosses', 'total_successfulCrosses',
        'total_forwardPasses', 'total_successfulForwardPasses', 'total_longPasses',
        'total_recoveries', 'total_opponentHalfRecoveries', 'total_losses',
        'total_ownHalfLosses', 'total_touchInBox', 'total_progressivePasses',
        'total_counterpressingRecoveries'
    ]

    # Create "per match" columns by dividing by 'label'
    for col in columns_to_per_match:
        if col in df_matchstats.columns:  # Check if the column exists
            df_matchstats[f'{col}_per_match'] = df_matchstats[col] / df_matchstats['label']

    # Calculate additional metrics
    df_matchstats['forward pass share'] = df_matchstats['total_forwardPasses_per_match'] / df_matchstats['total_passes_per_match']
    df_matchstats['long pass share'] = df_matchstats['total_longPasses_per_match'] / df_matchstats['total_passes_per_match']
    df_matchstats['pass per loss'] = df_matchstats['total_passes_per_match'] / df_matchstats['total_losses_per_match']
    df_matchstats['Own half losses %'] = df_matchstats['total_ownHalfLosses'] / df_matchstats['total_losses']
    df_matchstats['Opponent half recoveries %'] = df_matchstats['total_opponentHalfRecoveries'] / df_matchstats['total_recoveries']

    # Now attempt to rank the specified columns
    metrics_to_rank = [
        'PPDA', 'forward pass share', 'long pass share', 'pass per loss', 
        'Own half losses %', 'Opponent half recoveries %'
    ] + [f'{col}_per_match' for col in columns_to_per_match]  # Add per-match metrics


    # Rank the specified metrics
    for col in metrics_to_rank:
        if col in df_matchstats.columns:
            if col == 'PPDA':
                df_matchstats[f'{col}_rank'] = df_matchstats[col].rank(ascending=True, method='min')
            else:
                df_matchstats[f'{col}_rank'] = df_matchstats[col].rank(ascending=False, method='min')
        else:
            st.warning(f"Column '{col}' not found for ranking.")

    # Remove 'total_' prefix and '_per_match' suffix from column names
    sorted_teams = df_matchstats['team.name'].sort_values().unique()
    df_matchstats_1 = df_matchstats.set_index('team.name')
    # Display the DataFrame
    st.dataframe(df_matchstats_1)

    # Sort teams alphabetically for the selectbox

    # Select team from dropdown
    selected_team = st.selectbox('Choose team', sorted_teams)

    # Filter DataFrame for selected team
    team_df = df_matchstats.loc[df_matchstats['team.name'] == selected_team]

    # Target ranks to filter
    target_ranks = [1, 2, 3, 4, 10, 11, 12, 13, 14]

    # Filter the selected team's ranks and values
    filtered_data_df = pd.DataFrame()
    for col in team_df.columns:
        if col.endswith('_rank'):
            # Original column name without '_rank'
            original_col = col.replace('_rank', '')

            # Filter based on target ranks
            team_ranks = team_df[col].values
            if any(rank in target_ranks for rank in team_ranks):
                # If any rank is in the target ranks, add it to the filtered data
                filtered_data_df[f'{original_col}_rank'] = team_df[col]
                filtered_data_df[f'{original_col}_value'] = team_df[original_col]

    # Display the filtered data in two columns
    col1, col2 = st.columns([1, 2])
    with col1:
        # Transpose the DataFrame for better display
        filtered_data_df = filtered_data_df.T
        st.dataframe(filtered_data_df)
    
def keeper_ratings():
    gc = gspread.service_account('wellness-1123-178fea106d0a.json')
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1e5kAIxFAMmTSuamV1E_ymgzva0rLA6Q4oM21VRU6FwI/edit?resourcekey=&gid=1263806243#gid=1263806243')
    ws = sh.worksheet('Formularsvar 1')
    df = pd.DataFrame(ws.get_all_records())
    df['Tidsstempel'] = pd.to_datetime(df['Tidsstempel'],dayfirst=True, format='%d/%m/%Y %H.%M.%S')

    # Create a new column 'date' with the format 'dd/mm/yyyy'
    df['date'] = df['Tidsstempel'].dt.strftime('%d/%m/%Y')
    # Melt the DataFrame to long format
    df_melted = df.melt(id_vars=['Coach name', 'date','Tidsstempel'], 
                        var_name='Player', 
                        value_name='Rating')

    # Remove 'Rating [' and ']' from Player names
    df_melted['Player'] = df_melted['Player'].str.replace('Rating \[|\]', '', regex=True)
    df_melted['date'] = pd.to_datetime(df_melted['date'], format='%d/%m/%Y')

    # Streamlit app
    st.title("Player Ratings")

    # Main layout filters
    selected_coaches = st.multiselect('Select Coaches', df['Coach name'].unique(), df['Coach name'].unique())
    if st.button('Select All Players'):
        selected_players = df_melted['Player'].unique().tolist()
    elif st.button('Deselect All Players'):
        selected_players = []
    else:
        selected_players = st.multiselect('Select Players', sorted(df_melted['Player'].unique()))
    min_date = pd.to_datetime(df_melted['date'], format='%d/%m/%Y').min().date()
    max_date = pd.to_datetime(df_melted['date'], format='%d/%m/%Y').max().date()
    start_date, end_date = st.date_input('Select Date Range', [min_date, max_date], min_value=min_date, max_value=max_date)

    # Filter DataFrame based on the selected filters
    filtered_df = df_melted[
        (df_melted['Coach name'].isin(selected_coaches)) &
        (df_melted['Player'].isin(selected_players)) &
        (pd.to_datetime(df_melted['date'], format='%d/%m/%Y').dt.date >= start_date) &
        (pd.to_datetime(df_melted['date'], format='%d/%m/%Y').dt.date <= end_date)
    ]
        
    # Drop rows where Rating is NaN
    filtered_df = filtered_df[['date','Player', 'Rating','Coach name']]
    # Ensure 'Rating' column is numeric
    filtered_df = filtered_df[['date','Player', 'Rating']]
    filtered_df.replace('', pd.NA, inplace=True)

    # Filter out rows where the 'rating' column has NaN values
    filtered_df = filtered_df.dropna(subset=['Rating'])

    # Calculate the average ratings, ignoring None values
    average_ratings = filtered_df.groupby(['Player', 'date'])['Rating'].mean().reset_index()
    average_of_period = average_ratings.groupby('Player')['Rating'].mean().reset_index()
    average_of_period['Rating'] = average_of_period['Rating'].astype(float)
    average_of_period['Rating'] = average_of_period['Rating'].round(2)

    average_of_period = average_of_period.sort_values('Rating', ascending=False)
    st.dataframe(average_of_period,hide_index=True)
    fig = go.Figure()

    for player in average_ratings['Player'].unique():
        player_data = average_ratings[average_ratings['Player'] == player]
        fig.add_trace(go.Scatter(
            x=player_data['date'],
            y=player_data['Rating'],
            mode='lines+markers',
            name=player
        ))

    fig.update_layout(
        title='Player Ratings Over Time',
        xaxis_title='Date',
        yaxis_title='Rating',
        yaxis=dict(range=[1, 10]),  # Set y-axis range from 1 to 10        
        width=800,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def sportspsykologiske_målinger():
    # Password input
    password = st.text_input("Input password", type="password")

    # Check if the password is correct
    if password == "ACHORSENSU19":
        # Initialize Google Sheets connection
        gc = gspread.service_account(r'wellness-1123-178fea106d0a.json')

        # Function to open a Google Sheet and return it as a DataFrame
        def get_sheet_as_dataframe(sheet_url, worksheet_name, num_columns=None):
            sh = gc.open_by_url(sheet_url)
            ws = sh.worksheet(worksheet_name)
            data = ws.get_all_values()
            
            # Convert the sheet data to a DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Optionally limit the number of columns
            if num_columns:
                df = df.iloc[:, :num_columns]
            
            return df

        # Function to process the DataFrame: convert 'Tidsstempel' to datetime, extract the month, and rename columns
        def process_dataframe(dataframe, suffix):
            # Convert 'Tidsstempel' to datetime format
            dataframe['Tidsstempel'] = pd.to_datetime(dataframe['Tidsstempel'], format='%d/%m/%Y %H.%M.%S', errors='coerce')
            
            # Remove rows with invalid or missing 'Tidsstempel'
            dataframe.dropna(subset=['Tidsstempel'], inplace=True)
            
            # Extract the month
            dataframe['Month'] = dataframe['Tidsstempel'].dt.month
            
            # Drop the 'Tidsstempel' column
            dataframe.drop(columns=['Tidsstempel'], inplace=True)
            
            # Rename other columns to avoid conflicts (except 'Your Name' and 'Month')
            dataframe = dataframe.rename(columns={col: f"{col}_{suffix}" for col in dataframe.columns if col not in ['Your Name', 'Month']})
            
            return dataframe

        # Load the sheets into DataFrames
        df = get_sheet_as_dataframe('https://docs.google.com/spreadsheets/d/1h4WAhpuT6uQ_jp6bfMUUgMrhGtXnbqaaz1p6yUZCPbM/edit?resourcekey=&gid=1240737519#gid=1240737519', 'Formularsvar 1')
        df1 = get_sheet_as_dataframe('https://docs.google.com/spreadsheets/d/1zXEFfrD_meajd32Hy_TT0-yT5v9vi5WdQHYI51yfZH4/edit?resourcekey=&gid=198410459#gid=198410459', 'Formularsvar 1')
        df2 = get_sheet_as_dataframe('https://docs.google.com/spreadsheets/d/1GGtgwYYoLWQ1yS9tyM2-2MVvrQNgMpVECRjA3-H2O8A/edit?resourcekey=&gid=698467196#gid=698467196', 'Formularsvar 1')
        df3 = get_sheet_as_dataframe('https://docs.google.com/spreadsheets/d/1Z_MANeXqcyMrhnoqbk_9bHy1Ic3-VGlnRT0vcn6Bb5k/edit?resourcekey=&gid=1340211860#gid=1340211860', 'Formularsvar 1')

        # Process each DataFrame to extract 'Month' and rename columns
        df = process_dataframe(df, 'CD_RISC')
        df1 = process_dataframe(df1, 'PNSS-S')
        df2 = process_dataframe(df2, 'TMID')
        df3 = process_dataframe(df3, 'PSS')

        # Merge all the DataFrames on 'Your Name' and 'Month'
        merged_df = df.merge(df1, on=['Your Name', 'Month'], how='outer') \
                    .merge(df2, on=['Your Name', 'Month'], how='outer') \
                    .merge(df3, on=['Your Name', 'Month'], how='outer')

        # Group by 'Your Name' and 'Month' and get the first non-null value
        merged_df = merged_df.groupby(['Your Name', 'Month'], as_index=False).first()

        # Extract only the first character for all columns except 'Your Name' and 'Month'
        columns_to_modify = merged_df.columns.difference(['Your Name', 'Month'])
        merged_df[columns_to_modify] = merged_df[columns_to_modify].applymap(lambda x: x[0] if pd.notnull(x) else x)

        # Remove rows where 'Your Name' is empty
        merged_df = merged_df[merged_df['Your Name'] != ""]

        # Calculate the overall averages for all players (unfiltered)
        categories = {
            'CD_RISC': [col for col in merged_df.columns if 'CD_RISC' in col],
            'PNSS-S': [col for col in merged_df.columns if 'PNSS-S' in col],
            'TMID': [col for col in merged_df.columns if 'TMID' in col],
            'PSS': [col for col in merged_df.columns if 'PSS' in col]
        }

        # Calculate averages for each category for ALL players
        for category, columns in categories.items():
            merged_df[f'{category}_Average'] = merged_df[columns].apply(pd.to_numeric, errors='coerce').mean(axis=1)

        # Streamlit interaction for player selection
        players = merged_df['Your Name'].unique()

        # Create side-by-side selectboxes
        col1, col2 = st.columns(2)

        with col1:
            chosen_players = st.selectbox('Choose player(s)', players)

        with col2:
            # Selectbox for category selection
            selected_category = st.selectbox('Select a category', ['CD_RISC', 'PNSS-S', 'TMID', 'PSS'])

        # Filter data based on selected players
        if chosen_players:
            filtered_df = merged_df[merged_df['Your Name']==chosen_players]
            
            # Show scatterplots for each column in the selected category
            for col in categories[selected_category]:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
                valid_data = filtered_df[['Month', col]].dropna()
                
                if not valid_data.empty:
                    plt.figure(figsize=(8, 6))
                    plt.scatter(valid_data['Month'], valid_data[col], label=col)
                    plt.xlim(0, 12)  # Set x-axis from 0 to 12 (months)
                    plt.ylim(1, 7)   # Set y-axis from 1 to 7 (responses)
                    plt.title(f'Scatterplot of {col}')
                    plt.xlabel('Month')
                    plt.ylabel(col)
                    plt.legend()
                    st.pyplot(plt)

            # Combined scatterplot of averages for each category
            plt.figure(figsize=(8, 6))
            
            # Plot averages for each category for the chosen players
            for category in categories.keys():
                valid_category_avg = filtered_df[['Month', f'{category}_Average']].dropna()
                if not valid_category_avg.empty:
                    plt.scatter(valid_category_avg['Month'], valid_category_avg[f'{category}_Average'], label=f'{category} Average')
            
            # Plot formatting
            plt.xlim(0, 12)  # Set x-axis from 0 to 12 (months)
            plt.ylim(1, 7)   # Set y-axis from 1 to 7 (responses)
            plt.title('Scatterplot of Category Averages (Chosen Players)')
            plt.xlabel('Month')
            plt.ylabel('Average Score')
            plt.legend()
            st.pyplot(plt)

        # Scatterplot for the overall average of all players (not filtered by selected players)
        plt.figure(figsize=(8, 6))

        for category in categories.keys():
            # Group by month to get the average for each month across all players
            overall_category_avg = merged_df.groupby('Month')[f'{category}_Average'].mean().reset_index()
            
            if not overall_category_avg.empty:
                plt.scatter(overall_category_avg['Month'], overall_category_avg[f'{category}_Average'], label=f'Overall {category} Average')

        # Plot formatting for overall averages
        plt.xlim(0, 12)  # Set x-axis from 0 to 12 (months)
        plt.ylim(1, 7)   # Set y-axis from 1 to 7 (responses)
        plt.title('Overall Averages for All Players (By Category)')
        plt.xlabel('Month')
        plt.ylabel('Average Score Across All Players')
        plt.legend()
        st.pyplot(plt)

    else:
        st.error("Wrong password. Please try again.")
    
Data_types = {
    'Dashboard': dashboard,
    'Opposition analysis': opposition_analysis,
    'Wellness data': wellness,
    'Player data': player_data,
    'Training ratings': training_ratings,
    'Keeper ratings': keeper_ratings,
    'Sports Psychological measures': sportspsykologiske_målinger
    }


st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
selected_data = st.sidebar.radio('Choose data type',list(Data_types.keys()))

st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
Data_types[selected_data]()
