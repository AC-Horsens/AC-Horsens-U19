import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from scipy.ndimage import gaussian_filter
import gspread
import plotly.graph_objs as go


st.set_page_config(layout="wide")

@st.cache_data()
def load_matchstats():
    #events = pd.read_csv(r'events.csv')
    df_matchstats = pd.read_csv(r'matchstats.csv')
    return df_matchstats

def load_events():
    events = pd.read_csv(r'events.csv')
    return events

def load_xg():
    df_xg = pd.read_csv(r'xg.csv')
    return df_xg

def load_xg_agg():
    df_xg_agg = pd.read_csv(r'xg_agg.csv')
    return df_xg_agg

def load_horsens_events():
    events = pd.read_csv(r'events.csv')
    events = events[events['label'].str.contains('Horsens')]
    return events

@st.cache_data()
def Process_data_spillere(events,df_xg,df_matchstats):
    xg = events[['player.name','label','shot.xg']]
    xg['shot.xg'] = xg['shot.xg'].astype(float)
    xg = xg.groupby(['player.name','label']).sum().reset_index()
    df_scouting = xg.merge(df_matchstats, on=['player.name', 'label'], how='inner')
    def calculate_score(df, column, score_column):
        df_unique = df.drop_duplicates(column).copy()
        df_unique.loc[:, score_column] = pd.qcut(df_unique[column], q=10, labels=False, duplicates='raise') + 1
        return df.merge(df_unique[[column, score_column]], on=column, how='left')
    
    minutter_kamp = 45
    minutter_total = 300
    
    df_matchstats = df_matchstats[['player.name','team.name','label','position_codes','total_minutesOnField','average_successfulPassesToFinalThird','percent_aerialDuelsWon','percent_newSuccessfulDribbles','average_throughPasses','percent_duelsWon','percent_successfulPassesToFinalThird','average_xgAssist','average_crosses','average_progressivePasses','average_progressiveRun','average_accelerations','average_passesToFinalThird','percent_successfulProgressivePasses','percent_successfulPasses','average_ballRecoveries','average_interceptions','average_defensiveDuels','average_successfulDefensiveAction','average_forwardPasses','average_successfulForwardPasses','average_touchInBox','average_xgShot','average_keyPasses','average_successfulAttackingActions','average_shotAssists']]
    df_scouting = df_xg.merge(df_matchstats,how='right')
    df_scouting['penAreaEntries_per90&crosses%shotassists'] = ((df_scouting['average_passesToFinalThird'].astype(float)+df_scouting['average_crosses'].astype(float) + df_scouting['average_xgAssist'].astype(float))/ df_scouting['total_minutesOnField'].astype(float)) * 90

    df_scouting.fillna(0, inplace=True)
    df_scouting = df_scouting.drop_duplicates(subset=['player.name', 'team.name', 'position_codes','label'])

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
        
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_duelsWon', 'percent_duelsWon score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_interceptions', 'average_interceptions score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_ballRecoveries', 'ballRecovery score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'percent_aerialDuelsWon', 'percent_aerialDuelsWon score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'average_progressivePasses', 'average_progressivePasses score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')

        df_balanced_central_defender['Defending'] = df_balanced_central_defender[['percent_duelsWon score','percent_aerialDuelsWon score', 'average_interceptions score', 'average_interceptions score', 'ballRecovery score']].mean(axis=1)
        df_balanced_central_defender['Possession value added'] = df_balanced_central_defender[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score']].mean(axis=1)
        df_balanced_central_defender['Passing'] = df_balanced_central_defender[['percent_successfulPasses score', 'percent_successfulPasses score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_balanced_central_defender['Total score'] = df_balanced_central_defender[['Defending','Possession value added','Passing']].mean(axis=1)

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

        df_backs['Defending'] = (df_backs['percent_duelsWon score'] + df_backs['percent_duelsWon score'] + df_backs['average_interceptions score'])/3
        df_backs['Passing'] = (df_backs['percent_successfulPassesToFinalThird score'] + df_backs['percent_successfulPassesToFinalThird score'] + df_backs['percent_successfulPasses score'] + df_backs['Possession value added score'])/4
        df_backs['Chance creation'] = (df_backs['Penalty area entries & crosses & shot assists score'] + df_backs['average_crosses_per90 score'] + df_backs['average_crosses_per90 score'] + df_backs['percent_successfulPassesToFinalThird score']+ df_backs['percent_successfulPassesToFinalThird score'] + df_backs['percent_successfulPassesToFinalThird score']+ df_backs['percent_successfulPassesToFinalThird score'] + df_backs['Possession value added score'] + df_backs['Possession value added score'])/9
        df_backs['Possession value added'] = df_backs[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score']].mean(axis=1)
        
        df_backs = calculate_score(df_backs, 'Defending', 'Defending_')
        df_backs = calculate_score(df_backs, 'Passing', 'Passing_')
        df_backs = calculate_score(df_backs, 'Chance creation','Chance_creation')
        df_backs = calculate_score(df_backs, 'Possession value added', 'Possession_value_added')
        
        df_backs['Total score'] = (df_backs['Defending_'] + df_backs['Defending_'] + df_backs['Defending_'] + df_backs['Defending_'] + df_backs['Passing_']+ df_backs['Passing_'] + df_backs['Chance_creation'] + df_backs['Chance_creation'] + df_backs['Chance_creation'] + df_backs['Possession_value_added'] + df_backs['Possession_value_added'] + df_backs['Possession_value_added'] + df_backs['Possession_value_added']) / 13
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

        df_sekser = calculate_score(df_sekser,'average_successfulAttackingActions', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'percent_duelsWon', 'percent_duelsWon score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPasses', 'percent_successfulPasses score')
        df_sekser = calculate_score(df_sekser, 'average_interceptions', 'average_interceptions score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulPassesToFinalThird', 'percent_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'average_ballRecoveries', 'ballRecovery score')
        df_sekser = calculate_score(df_sekser, 'average_successfulPassesToFinalThird', 'average_successfulPassesToFinalThird score')
        df_sekser = calculate_score(df_sekser, 'percent_successfulProgressivePasses', 'percent_successfulProgressivePasses score')

        
        df_sekser['Defending'] = df_sekser[['percent_duelsWon score','average_interceptions score','average_interceptions score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['percent_successfulPasses score','percent_successfulPasses score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['Possession value added score','Possession value added score','percent_successfulPassesToFinalThird score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser[['average_successfulPassesToFinalThird score','percent_successfulPassesToFinalThird score','percent_successfulProgressivePasses score','percent_successfulProgressivePasses score']].mean(axis=1)
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_','Passing_','Progressive_ball_movement','Possession_value_added']].mean(axis=1)
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
        df_10 = df_scouting[(df_scouting['position_codes'].str.contains('amf')) & (~df_scouting['position_codes'].str.contains('lamf|ramf'))]
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
        
        df_10['Total score'] = df_10[['Passing_','Chance_creation','Chance_creation','Chance_creation','Chance_creation','Goalscoring_','Goalscoring_','Goalscoring_','Possession_value','Possession_value','Possession_value']].mean(axis=1)
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

        
        df_striker['Total score'] = df_striker[['Linkup play','Chance creation','Goalscoring','Possession value']].mean(axis=1)
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
events = load_events()

position_dataframes = Process_data_spillere(events,df_xg,df_matchstats)
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
    df_passes = df[(df['pass.endLocation.x'].notna()) | (df['carry.endLocation.x'].notna())]
    df_duels = df[df['type.primary'] == 'duel']

    pitch = Pitch(pitch_type='wyscout', pitch_color='grass', line_color='white')
    fig, ax = pitch.draw()

    for index, row in df_passes.iterrows():
        # Start point
        start_x = row['location.x']
        start_y = row['location.y']

        # End point
        end_x = row['pass.endLocation.x'] if pd.notnull(row['pass.endLocation.x']) else row['carry.endLocation.x']
        end_y = row['pass.endLocation.y'] if pd.notnull(row['pass.endLocation.y']) else row['carry.endLocation.y']

        # Determine arrow color
        arrow_color = 'red' if not row['pass.accurate'] else '#0dff00'

        # Plot arrow
        ax.arrow(start_x, start_y, end_x - start_x, end_y - start_y, color=arrow_color,
                 length_includes_head=True, head_width=0.5, head_length=0.5)

    # Plot duels as yellow dots
    ax.scatter(df_duels['location.x'], df_duels['location.y'], color='yellow', zorder=3)

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

def player_data(events,df_matchstats,balanced_central_defender_df,fullbacks_df,number8_df,number6_df,number10_df,winger_df,classic_striker_df):
    horsens = events[events['team.name'].str.contains('Horsens')]
    horsens = horsens.sort_values(by='player.name')
    player_name = st.selectbox('Choose player', horsens['player.name'].unique())
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

    if 'pass.endLocation.x' in df.columns:
        Alle_off_aktioner = df[(df['pass.endLocation.x'] > 0) & (df['player.name'] == player_name)]
    else:
        st.error("'pass.endLocation.x' column does not exist in the DataFrame.")
    plot_arrows(Alle_off_aktioner)


def dashboard():
    st.title('U19 Dashboard')
    events = load_horsens_events()
    events['label'] = events['label'] + ' ' + events['date']
    events['date'] = pd.to_datetime(events['date'],utc=True)
    events = events.sort_values('date').reset_index(drop=True)
    matches = events['label'].unique()
    matches = matches[::-1]
    match_choice = st.multiselect('Choose a match', matches)

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
        st.write('All matches')
        st.dataframe(all_xg, hide_index=True)
        st.write('Chosen matches')
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
        
        sc = ax.scatter(df_xg_plot['location.x'], df_xg_plot['location.y'], s=df_xg_plot['shot.xg'] * 100, c='red', edgecolors='black', alpha=0.6)
        
        for i, row in df_xg_plot.iterrows():
            ax.text(row['location.x'], row['location.y'], f"{row['player.name']}\n{row['shot.xg']:.2f}", fontsize=6, ha='center', va='center')
        
        st.pyplot(fig)

    def pressing():
        st.write('To be added')
        
    def chance_creation():
        st.write('To be added')

    Data_types = {
        'xG': xg(),
        'Pressing': pressing(),
        'Chance Creation': chance_creation()
    }

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

Data_types = {
    'Dashboard': dashboard,
    'Wellness data': wellness,
    'Player data': player_data,
    'Training ratings': training_ratings
    }


st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
selected_data = st.sidebar.radio('Choose data type',list(Data_types.keys()))

st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
Data_types[selected_data]()
