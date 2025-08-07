import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import mplsoccer
from mplsoccer import Pitch
from scipy.ndimage import gaussian_filter
import gspread
import plotly.graph_objs as go
import numpy as np
import re

st.set_page_config(layout="wide")

@st.cache_data()
def load_matchstats():
    #events = pd.read_csv(r'events.csv')
    df_matchstats = pd.read_csv(r'U19 Ligaen_matchstats.csv')    
    return df_matchstats

@st.cache_data()
def load_events():
    events = pd.read_csv(r'U19 Ligaen_events.csv')
    return events

@st.cache_data()
def load_xg():
    df_xg = pd.read_csv(r'U19 Ligaen_xg.csv')    
    return df_xg

@st.cache_data()
def load_groundduels():
    df_xg = pd.read_csv(r'U19 Ligaen_groundduels.csv')    
    return df_xg

@st.cache_data()
def Process_data_spillere(events,df_xg,df_matchstats,groundduels):
    xg = events[['SHORTNAME','MATCHLABEL','SHOTXG']]
    xg['SHOTXG'] = xg['SHOTXG'].astype(float)
    xg = xg.groupby(['SHORTNAME','MATCHLABEL']).sum().reset_index()
    df_scouting = xg.merge(df_matchstats, on=['SHORTNAME', 'MATCHLABEL'], how='inner').reset_index()
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
    
    df_matchstats = df_matchstats[['SHORTNAME','TEAMNAME','MATCHLABEL','POSITION1CODE','MINUTESONFIELD','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE','FIELDAERIALDUELSWON_PERCENT','SUCCESSFULDRIBBLES_PERCENT','SUCCESSFULTHROUGHPASSES_AVERAGE','DUELSWON_PERCENT','SUCCESSFULPASSESTOFINALTHIRD_PERCENT','XGASSIST','SUCCESSFULCROSSES_AVERAGE','SUCCESSFULPROGRESSIVEPASSES_AVERAGE','PROGRESSIVERUN','ACCELERATIONS','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE','SUCCESSFULPROGRESSIVEPASSES_PERCENT','SUCCESSFULPASSES_PERCENT','BALLRECOVERIES','INTERCEPTIONS','DEFENSIVEDUELSWON_AVERAGE','SUCCESSFULDEFENSIVEACTION','SUCCESSFULFORWARDPASSES_AVERAGE','SUCCESSFULFORWARDPASSES_AVERAGE','TOUCHINBOX','XGSHOT','SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULATTACKINGACTIONS','SUCCESSFULSHOTASSISTS','BALLLOSSES']]
    df_scouting = df_xg.merge(df_matchstats,on=['SHORTNAME','TEAMNAME','MATCHLABEL'],how='right')
    df_scouting.fillna(0, inplace=True)
    st.write(df_scouting)
    df_scouting['penAreaEntries_per90&crosses%shotassists'] = ((df_scouting['SUCCESSFULPASSESTOFINALTHIRD_AVERAGE'].astype(float)+df_scouting['SUCCESSFULCROSSES_AVERAGE'].astype(float) + df_scouting['XGASSIST'].astype(float))/ df_scouting['MINUTESONFIELD'].astype(float)) * 90

    df_scouting = df_scouting.drop_duplicates(subset=['SHORTNAME', 'TEAMNAME', 'POSITION1CODE','MATCHLABEL'])

    def calculate_match_xg(df_scouting):
        # Calculate the total match_xg for each match_id
        df_scouting['match_xg'] = df_scouting.groupby('MATCHLABEL')['SHOTXG'].transform('sum')
        
        # Calculate the total team_xg for each team in each match
        df_scouting['team_xg'] = df_scouting.groupby(['TEAMNAME', 'MATCHLABEL'])['SHOTXG'].transform('sum')
        
        # Calculate opponents_xg as match_xg - team_xg
        df_scouting['opponents_xg'] = df_scouting['match_xg'] - df_scouting['team_xg']
        df_scouting['opponents_xg'] = pd.to_numeric(df_scouting['opponents_xg'], errors='coerce')
       
        return df_scouting

    df_scouting = calculate_match_xg(df_scouting)
    df_scouting.fillna(0, inplace=True)

    def ball_playing_central_defender():
        df_spillende_stopper = df_scouting[df_scouting['player_codes'].str.contains('cb')]
        df_spillende_stopper['MINUTESONFIELD'] = df_spillende_stopper['MINUTESONFIELD'].astype(int)
        df_spillende_stopper = df_spillende_stopper[df_spillende_stopper['MINUTESONFIELD'].astype(int) >= minutter_kamp]
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'BALLRECOVERIES', 'BALLRECOVERIES score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'SUCCESSFULATTACKINGACTIONS', 'SUCCESSFULATTACKINGACTIONS score')
        df_spillende_stopper = calculate_score(df_spillende_stopper, 'FIELDAERIALDUELSWON_PERCENT', 'FIELDAERIALDUELSWON_PERCENT score')

        df_spillende_stopper['Passing'] = df_spillende_stopper[['SUCCESSFULPASSES_PERCENT score', 'SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_spillende_stopper['Forward passing'] = df_spillende_stopper[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score']].mean(axis=1)
        df_spillende_stopper['Defending'] = df_spillende_stopper[['DUELSWON_PERCENT score', 'INTERCEPTIONS score', 'INTERCEPTIONS score', 'BALLRECOVERIES score']].mean(axis=1)
        df_spillende_stopper['Possession value added'] = df_spillende_stopper['SUCCESSFULATTACKINGACTIONS score']
        
        df_spillende_stopper['Total score'] = df_spillende_stopper[['Passing','Passing','Forward passing','Forward passing','Forward passing','Defending','Defending','Possession value added','Possession value added','Possession value added']].mean(axis=1)
        df_spillende_stopper = df_spillende_stopper[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Passing','Forward passing','Defending','Possession value added score','Total score']] 
        df_spillende_stoppertotal = df_spillende_stopper[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Passing','Forward passing','Defending','Possession value added score','Total score']]
        df_spillende_stoppertotal = df_spillende_stoppertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_spillende_stopper.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_spillende_stoppertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_spillende_stopper = df_spillende_stopper.sort_values('Total score',ascending = False)
        df_spillende_stoppertotal = df_spillende_stoppertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Passing','Forward passing','Defending','Possession value added score','Total score']]
        df_spillende_stoppertotal = df_spillende_stoppertotal[df_spillende_stoppertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_spillende_stoppertotal = df_spillende_stoppertotal.sort_values('Total score',ascending = False)
        return df_spillende_stopper
   
    def defending_central_defender():
        df_forsvarende_stopper = df_scouting[df_scouting['player_codes'].str.contains('cb')]
        df_forsvarende_stopper['MINUTESONFIELD'] = df_forsvarende_stopper['MINUTESONFIELD'].astype(int)
        df_forsvarende_stopper = df_forsvarende_stopper[df_forsvarende_stopper['MINUTESONFIELD'].astype(int) >= minutter_kamp]
        
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'BALLRECOVERIES', 'ballRecovery score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper,'FIELDAERIALDUELSWON_PERCENT', 'FIELDAERIALDUELSWON_PERCENT score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'SUCCESSFULATTACKINGACTIONS', 'SUCCESSFULATTACKINGACTIONS score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_forsvarende_stopper = calculate_score(df_forsvarende_stopper, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')


        df_forsvarende_stopper['Defending'] = df_forsvarende_stopper[['DUELSWON_PERCENT score','FIELDAERIALDUELSWON_PERCENT score', 'INTERCEPTIONS score', 'INTERCEPTIONS score', 'ballRecovery score']].mean(axis=1)
        df_forsvarende_stopper['Duels'] = df_forsvarende_stopper[['DUELSWON_PERCENT score','DUELSWON_PERCENT score','FIELDAERIALDUELSWON_PERCENT score']].mean(axis=1)
        df_forsvarende_stopper['Intercepting'] = df_forsvarende_stopper[['INTERCEPTIONS score','INTERCEPTIONS score','ballRecovery score']].mean(axis=1)
        df_forsvarende_stopper['Passing'] = df_forsvarende_stopper[['SUCCESSFULPASSES_PERCENT score', 'SUCCESSFULPASSES_PERCENT score','SUCCESSFULATTACKINGACTIONS score','SUCCESSFULATTACKINGACTIONS score']].mean(axis=1)
        df_forsvarende_stopper['Total score'] = df_forsvarende_stopper[['Defending','Defending','Defending','Defending','Duels','Duels','Duels','Intercepting','Intercepting','Intercepting','Passing','Passing']].mean(axis=1)

        df_forsvarende_stopper = df_forsvarende_stopper[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stopper[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_forsvarende_stopper.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_forsvarende_stoppertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_forsvarende_stopper = df_forsvarende_stopper.sort_values('Total score',ascending = False)
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending','Duels','Intercepting','Passing','Total score']]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal[df_forsvarende_stoppertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_forsvarende_stoppertotal = df_forsvarende_stoppertotal.sort_values('Total score',ascending = False)
        return df_forsvarende_stopper

    def balanced_central_defender():
        df_balanced_central_defender = df_scouting[df_scouting['POSITION1CODE'].str.contains('cb')]
        df_balanced_central_defender['MINUTESONFIELD'] = df_balanced_central_defender['MINUTESONFIELD'].astype(int)
        df_balanced_central_defender = df_balanced_central_defender[df_balanced_central_defender['MINUTESONFIELD'].astype(int) >= minutter_kamp]
        df_balanced_central_defender = calculate_opposite_score(df_balanced_central_defender,'opponents_xg', 'opponents xg score')
        
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'totalDuels', 'totalDuels score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'BALLRECOVERIES', 'ballRecovery score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'FIELDAERIALDUELSWON_PERCENT', 'FIELDAERIALDUELSWON_PERCENT score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender,'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'SUCCESSFULPROGRESSIVEPASSES_PERCENT', 'SUCCESSFULPROGRESSIVEPASSES_PERCENT score')
        df_balanced_central_defender = calculate_opposite_score(df_balanced_central_defender,'BALLLOSSES','BALLLOSSES score')

        df_balanced_central_defender['Defending'] = df_balanced_central_defender[['DUELSWON_PERCENT score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','stoppedProgressPercentage score','opponents xg score','opponents xg score','FIELDAERIALDUELSWON_PERCENT score', 'INTERCEPTIONS score', 'INTERCEPTIONS score', 'ballRecovery score']].mean(axis=1)
        df_balanced_central_defender['Possession value added'] = df_balanced_central_defender[['SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','BALLLOSSES score']].mean(axis=1)
        df_balanced_central_defender['Passing'] = df_balanced_central_defender[['SUCCESSFULPASSES_PERCENT score', 'SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score']].mean(axis=1)

        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'Defending', 'Defending_')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'Passing', 'Passing_')
        df_balanced_central_defender = calculate_score(df_balanced_central_defender, 'Possession value added', 'Possession_value_added')


        df_balanced_central_defender['Total score'] = df_balanced_central_defender[['Defending_','Defending_','Possession_value_added','Passing_']].mean(axis=1)

        df_balanced_central_defender = df_balanced_central_defender[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Possession_value_added','Passing_','Total score']]
        
        df_balanced_central_defendertotal = df_balanced_central_defender[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Possession_value_added','Passing_','Total score']]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_balanced_central_defender.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_balanced_central_defendertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_balanced_central_defender = df_balanced_central_defender.sort_values('Total score',ascending = False)
        df_balanced_central_defendertotal = df_balanced_central_defendertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Possession_value_added','Passing_','Total score']]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal[df_balanced_central_defendertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_balanced_central_defendertotal = df_balanced_central_defendertotal.sort_values('Total score',ascending = False)
        return df_balanced_central_defender

    
    def fullbacks():
        df_backs = df_scouting[(df_scouting['POSITION1CODE'].str.contains('rb') |df_scouting['POSITION1CODE'].str.contains('lb') |df_scouting['POSITION1CODE'].str.contains('lwb') |df_scouting['POSITION1CODE'].str.contains('rwb'))]        
        df_backs['MINUTESONFIELD'] = df_backs['MINUTESONFIELD'].astype(int)
        df_backs = df_backs[df_backs['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_backs = calculate_score(df_backs,'totalDuels', 'totalDuels score')
        df_backs = calculate_score(df_backs,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_backs = calculate_score(df_backs,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_backs = calculate_opposite_score(df_backs,'opponents_xg', 'opponents xg score')
        df_backs = calculate_score(df_backs,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_backs = calculate_score(df_backs, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_backs = calculate_score(df_backs, 'penAreaEntries_per90&crosses%shotassists', 'Penalty area entries & crosses & shot assists score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULSHOTASSISTS', 'SUCCESSFULSHOTASSISTS score')
        df_backs = calculate_score(df_backs, 'INTERCEPTIONS', 'interception_per90 score')
        df_backs = calculate_score(df_backs, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULCROSSES_AVERAGE', 'SUCCESSFULCROSSES_AVERAGE_per90 score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULPROGRESSIVEPASSES_PERCENT', 'SUCCESSFULPROGRESSIVEPASSES_PERCENT score')
        df_backs = calculate_score(df_backs, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_backs = calculate_opposite_score(df_backs,'BALLLOSSES','BALLLOSSES score')

        df_backs['Defending'] = df_backs[['DUELSWON_PERCENT score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','DUELSWON_PERCENT score','INTERCEPTIONS score','opponents xg score']].mean(axis=1)
        df_backs['Passing'] = df_backs[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSES_PERCENT score','Possession value added score','BALLLOSSES score']].mean(axis=1)
        df_backs['Chance creation'] = df_backs[['Penalty area entries & crosses & shot assists score','SUCCESSFULCROSSES_AVERAGE_per90 score','SUCCESSFULCROSSES_AVERAGE_per90 score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','Possession value added score','Possession value added score']].mean(axis=1)
        df_backs['Possession value added'] = df_backs[['SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','BALLLOSSES score']].mean(axis=1)
        
        df_backs = calculate_score(df_backs, 'Defending', 'Defending_')
        df_backs = calculate_score(df_backs, 'Passing', 'Passing_')
        df_backs = calculate_score(df_backs, 'Chance creation','Chance_creation')
        df_backs = calculate_score(df_backs, 'Possession value added', 'Possession_value_added')
        
        df_backs['Total score'] = df_backs[['Defending_','Defending_','Defending_','Defending_','Passing_','Passing_','Chance_creation','Chance_creation','Chance_creation','Possession_value_added','Possession_value_added','Possession_value_added']].mean(axis=1)
        df_backs = df_backs[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backs = df_backs.dropna()
        df_backstotal = df_backs[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backstotal = df_backstotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_backs.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_backstotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_backs = df_backs.sort_values('Total score',ascending = False)
        df_backstotal = df_backstotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Passing_','Chance_creation','Possession_value_added','Total score']]
        df_backstotal = df_backstotal[df_backstotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_backstotal = df_backstotal.sort_values('Total score',ascending = False)
        return df_backs
    
    def number6():
        df_sekser = df_scouting[(df_scouting['POSITION1CODE'].str.contains('dmf'))]
        df_sekser['MINUTESONFIELD'] = df_sekser['MINUTESONFIELD'].astype(int)
        df_sekser = df_sekser[df_sekser['MINUTESONFIELD'].astype(int) >= minutter_kamp]


        df_sekser = calculate_score(df_sekser,'totalDuels', 'totalDuels score')
        df_sekser = calculate_score(df_sekser,'stoppedProgressPercentage', 'stoppedProgressPercentage score')
        df_sekser = calculate_score(df_sekser,'recoveredPossessionPercentage', 'recoveredPossessionPercentage score')
        df_sekser = calculate_opposite_score(df_sekser,'opponents_xg', 'opponents xg score')
        df_sekser = calculate_score(df_sekser,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULFORWARDPASSES_AVERAGE', 'SUCCESSFULFORWARDPASSES_AVERAGE score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULFORWARDPASSES_AVERAGE', 'SUCCESSFULFORWARDPASSES_AVERAGE score')
        df_sekser = calculate_score(df_sekser, 'BALLRECOVERIES', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'BALLRECOVERIES', 'ballRecovery score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPROGRESSIVEPASSES_PERCENT', 'SUCCESSFULPROGRESSIVEPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_sekser = calculate_opposite_score(df_sekser,'BALLLOSSES','BALLLOSSES score')
        
        
        df_sekser['Defending'] = df_sekser[['DUELSWON_PERCENT score','opponents xg score','totalDuels score','stoppedProgressPercentage score','stoppedProgressPercentage score','recoveredPossessionPercentage score','INTERCEPTIONS score','INTERCEPTIONS score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSES_PERCENT score','BALLLOSSES score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','SUCCESSFULFORWARDPASSES_AVERAGE score','SUCCESSFULFORWARDPASSES_AVERAGE score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser[['BALLLOSSES score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score','SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score']].mean(axis=1)
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_', 'Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()
        df_seksertotal = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_sekser.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_seksertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_sekser = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser

    def number6_destroyer():
        df_sekser = df_scouting[(df_scouting['POSITION1CODE'].str.conitans('dmf'))]
        df_sekser['MINUTESONFIELD'] = df_sekser['MINUTESONFIELD'].astype(int)
        df_sekser = df_sekser[df_sekser['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_sekser = calculate_score(df_sekser,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_sekser = calculate_score(df_sekser, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_sekser = calculate_score(df_sekser, 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'BALLRECOVERIES', 'ballRecovery score')

        
        df_sekser['Defending'] = df_sekser[['DUELSWON_PERCENT score','INTERCEPTIONS score','INTERCEPTIONS score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['Possession value added score','Possession value added score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser['Possession value added score']
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_','Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()

        df_seksertotal = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_sekser.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_seksertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_sekser_destroyer = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser_destroyer
    
    def number6_double_6_forward():
        df_sekser = df_scouting[(df_scouting['POSITION1CODE'].str.conitans('dmf'))]
        df_sekser['MINUTESONFIELD'] = df_sekser['MINUTESONFIELD'].astype(int)
        df_sekser = df_sekser[df_sekser['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_sekser = calculate_score(df_sekser,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_sekser = calculate_score(df_sekser, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_sekser = calculate_score(df_sekser, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_sekser = calculate_score(df_sekser, 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_sekser = calculate_score(df_sekser, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_sekser = calculate_score(df_sekser, 'BALLRECOVERIES', 'ballRecovery score')

        
        df_sekser['Defending'] = df_sekser[['DUELSWON_PERCENT score','INTERCEPTIONS score','INTERCEPTIONS score','ballRecovery score']].mean(axis=1)
        df_sekser['Passing'] = df_sekser[['SUCCESSFULPASSES_PERCENT score','SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_sekser['Progressive ball movement'] = df_sekser[['Possession value added score','Possession value added score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score']].mean(axis=1)
        df_sekser['Possession value added'] = df_sekser['Possession value added score']
        
        df_sekser = calculate_score(df_sekser, 'Defending', 'Defending_')
        df_sekser = calculate_score(df_sekser, 'Passing', 'Passing_')
        df_sekser = calculate_score(df_sekser, 'Progressive ball movement','Progressive_ball_movement')
        df_sekser = calculate_score(df_sekser, 'Possession value added', 'Possession_value_added')
        
        df_sekser['Total score'] = df_sekser[['Defending_','Defending_','Passing_','Passing_','Progressive_ball_movement','Progressive_ball_movement','Possession_value_added','Possession_value_added']].mean(axis=1)
        df_sekser = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_sekser = df_sekser.dropna()
        df_seksertotal = df_sekser[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]

        df_seksertotal = df_seksertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_sekser.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_seksertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_sekser_double_6_forward = df_sekser.sort_values('Total score',ascending = False)
        df_seksertotal = df_seksertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Passing_','Progressive_ball_movement','Possession_value_added','Total score']]
        df_seksertotal= df_seksertotal[df_seksertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_seksertotal = df_seksertotal.sort_values('Total score',ascending = False)
        return df_sekser_double_6_forward
    
    def number8():
        df_otter = df_scouting[(df_scouting['POSITION1CODE'].str.contains('cmf'))]
        df_otter['MINUTESONFIELD'] = df_otter['MINUTESONFIELD'].astype(int)
        df_otter = df_otter[df_otter['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_otter = calculate_score(df_otter,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_otter = calculate_score(df_otter,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_otter = calculate_score(df_otter,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_otter = calculate_score(df_otter, 'DUELSWON_PERCENT', 'DUELSWON_PERCENT score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_otter = calculate_score(df_otter, 'INTERCEPTIONS', 'INTERCEPTIONS score')
        df_otter = calculate_score(df_otter, 'BALLRECOVERIES', 'possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_otter = calculate_score(df_otter, 'TOUCHINBOX','TOUCHINBOX score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_otter = calculate_score(df_otter, 'SUCCESSFULPROGRESSIVEPASSES_PERCENT', 'SUCCESSFULPROGRESSIVEPASSES_PERCENT score')


        df_otter['Defending'] = df_otter[['DUELSWON_PERCENT score','possWonDef3rd_possWonMid3rd_possWonAtt3rd_per90 score']].mean(axis=1)
        df_otter['Passing'] = df_otter[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_otter['Progressive ball movement'] = df_otter[['SUCCESSFULSHOTASSISTS score','SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','Possession value total score']].mean(axis=1)
        df_otter['Possession value'] = df_otter[['SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score','SUCCESSFULPROGRESSIVEPASSES_PERCENT score']].mean(axis=1)
        
        df_otter = calculate_score(df_otter, 'Defending', 'Defending_')
        df_otter = calculate_score(df_otter, 'Passing', 'Passing_')
        df_otter = calculate_score(df_otter, 'Progressive ball movement','Progressive_ball_movement')
        df_otter = calculate_score(df_otter, 'Possession value', 'Possession_value')
        
        df_otter['Total score'] = df_otter[['Defending_','Passing_','Passing_','Progressive_ball_movement','Progressive_ball_movement','Possession_value','Possession_value','Possession_value']].mean(axis=1)
        df_otter = df_otter[['SHORTNAME','TEAMNAME','POSITION1CODE','MATCHLABEL','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]
        df_otter = df_otter.dropna()

        df_ottertotal = df_otter[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]

        df_ottertotal = df_ottertotal.groupby(['SHORTNAME','TEAMNAME','POSITION1CODE']).mean().reset_index()
        minutter = df_otter.groupby(['SHORTNAME', 'TEAMNAME','POSITION1CODE'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_ottertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_otter = df_otter.sort_values('Total score',ascending = False)
        df_ottertotal = df_ottertotal[['SHORTNAME','TEAMNAME','POSITION1CODE','MINUTESONFIELD total','Defending_','Passing_','Progressive_ball_movement','Possession_value','Total score']]
        df_ottertotal= df_ottertotal[df_ottertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_ottertotal = df_ottertotal.sort_values('Total score',ascending = False)
        return df_otter
        
    def number10():
        df_10 = df_scouting[(df_scouting['POSITION1CODE'].str.contains('amf'))]
        df_10['MINUTESONFIELD'] = df_10['MINUTESONFIELD'].astype(int)
        df_10 = df_10[df_10['MINUTESONFIELD'].astype(int) >= minutter_kamp]
        
        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_10 = calculate_score(df_10, 'TOUCHINBOX','TOUCHINBOX score')
        df_10 = calculate_score(df_10, 'SUCCESSFULDRIBBLES_PERCENT','SUCCESSFULDRIBBLES_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULTHROUGHPASSES_AVERAGE','SUCCESSFULTHROUGHPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULKEYPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SHOTXG','SHOTXG score')


        df_10['Passing'] = df_10[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_10['Chance creation'] = df_10[['SUCCESSFULSHOTASSISTS score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','Possession value total score','Possession value score','SUCCESSFULPROGRESSIVEPASSES_AVERAGE score','SUCCESSFULDRIBBLES_PERCENT score','TOUCHINBOX score','SUCCESSFULTHROUGHPASSES_AVERAGE score','SUCCESSFULKEYPASSES_AVERAGE score']].mean(axis=1)
        df_10['Goalscoring'] = df_10[['TOUCHINBOX score','SHOTXG score','SHOTXG score','SHOTXG score']].mean(axis=1)
        df_10['Possession value'] = df_10[['Possession value total score','Possession value total score','Possession value added score','Possession value score','Possession value score','Possession value score']].mean(axis=1)
                
        df_10 = calculate_score(df_10, 'Passing', 'Passing_')
        df_10 = calculate_score(df_10, 'Chance creation','Chance_creation')
        df_10 = calculate_score(df_10, 'Goalscoring','Goalscoring_')        
        df_10 = calculate_score(df_10, 'Possession value', 'Possession_value')
        
        df_10['Total score'] = df_10[['Passing_','Chance_creation','Chance_creation','Chance_creation','Goalscoring_','Goalscoring_','Possession_value','Possession_value']].mean(axis=1)
        df_10 = df_10[['SHORTNAME','TEAMNAME','MATCHLABEL','MINUTESONFIELD','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10 = df_10.dropna()
        df_10total = df_10[['SHORTNAME','TEAMNAME','MINUTESONFIELD','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]

        df_10total = df_10total.groupby(['SHORTNAME','TEAMNAME']).mean().reset_index()
        minutter = df_10.groupby(['SHORTNAME', 'TEAMNAME'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_10total['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_10 = df_10.sort_values('Total score',ascending = False)
        df_10total = df_10total[['SHORTNAME','TEAMNAME','MINUTESONFIELD total','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10total= df_10total[df_10total['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_10total = df_10total.sort_values('Total score',ascending = False)
        return df_10
    
    def winger():
        df_10 = df_scouting[(df_scouting['POSITION1CODE'].str.contains('lw')) | (df_scouting['POSITION1CODE'].str.contains('rw'))| (df_scouting['POSITION1CODE'].str.contains('lamf'))| (df_scouting['POSITION1CODE'].str.contains('ramf'))] 
        df_10['MINUTESONFIELD'] = df_10['MINUTESONFIELD'].astype(int)
        df_10 = df_10[df_10['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_10 = calculate_score(df_10,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_10 = calculate_score(df_10,'PROGRESSIVERUN', 'progressiveRun score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_10 = calculate_score(df_10, 'TOUCHINBOX','TOUCHINBOX score')
        df_10 = calculate_score(df_10, 'SUCCESSFULDRIBBLES_PERCENT','SUCCESSFULDRIBBLES_PERCENT score')
        df_10 = calculate_score(df_10, 'SUCCESSFULTHROUGHPASSES_AVERAGE','SUCCESSFULTHROUGHPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULKEYPASSES_AVERAGE score')
        df_10 = calculate_score(df_10, 'SHOTXG','SHOTXG score')


        df_10['Passing'] = df_10[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score']].mean(axis=1)
        df_10['Chance creation'] = df_10[['progressiveRun score','SUCCESSFULSHOTASSISTS score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','Possession value total score','Possession value score','SUCCESSFULDRIBBLES_PERCENT score','SUCCESSFULDRIBBLES_PERCENT score','SUCCESSFULDRIBBLES_PERCENT score','TOUCHINBOX score','SUCCESSFULTHROUGHPASSES_AVERAGE score','SUCCESSFULKEYPASSES_AVERAGE score','SUCCESSFULKEYPASSES_AVERAGE score','SUCCESSFULKEYPASSES_AVERAGE score']].mean(axis=1)
        df_10['Goalscoring'] = df_10[['TOUCHINBOX','SHOTXG score','SHOTXG score','SHOTXG score']].mean(axis=1)
        df_10['Possession value'] = df_10[['Possession value total score','Possession value total score','Possession value added score','Possession value score','Possession value score','Possession value score']].mean(axis=1)
                
        df_10 = calculate_score(df_10, 'Passing', 'Passing_')
        df_10 = calculate_score(df_10, 'Chance creation','Chance_creation')
        df_10 = calculate_score(df_10, 'Goalscoring','Goalscoring_')        
        df_10 = calculate_score(df_10, 'Possession value', 'Possession_value')
        
        df_10['Total score'] = df_10[['Passing_','Chance_creation','Chance_creation','Chance_creation','Chance_creation','Goalscoring_','Goalscoring_','Goalscoring_','Goalscoring_','Possession_value','Possession_value','Possession_value','Possession_value']].mean(axis=1)
        df_10 = df_10[['SHORTNAME','TEAMNAME','MATCHLABEL','MINUTESONFIELD','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10 = df_10.dropna()
        df_10total = df_10[['SHORTNAME','TEAMNAME','MINUTESONFIELD','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]

        df_10total = df_10total.groupby(['SHORTNAME','TEAMNAME']).mean().reset_index()
        minutter = df_10.groupby(['SHORTNAME', 'TEAMNAME'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_10total['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_kant = df_10.sort_values('Total score',ascending = False)
        df_10total = df_10total[['SHORTNAME','TEAMNAME','MINUTESONFIELD total','Passing_','Chance_creation','Goalscoring_','Possession_value','Total score']]
        df_10total= df_10total[df_10total['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_10total = df_10total.sort_values('Total score',ascending = False)
        return df_kant
    
    def Classic_striker():
        df_striker = df_scouting[(df_scouting['POSITION1CODE'].str.contains('cf'))]
        df_striker['MINUTESONFIELD'] = df_striker['MINUTESONFIELD'].astype(int)
        df_striker = df_striker[df_striker['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_striker = calculate_score(df_striker, 'TOUCHINBOX','TOUCHINBOX score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULDRIBBLES_PERCENT','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULKEYPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SHOTXG','SHOTXG score')


        df_striker['Linkup_play'] = df_striker[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score','Possession value score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['TOUCHINBOX score','Possession value total score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['TOUCHINBOX','SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Chance creation','Goalscoring','Goalscoring','Possession value']].mean(axis=1)
        df_striker = df_striker[['SHORTNAME','TEAMNAME','MATCHLABEL','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()

        df_strikertotal = df_striker[['SHORTNAME','TEAMNAME','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['SHORTNAME','TEAMNAME']).mean().reset_index()
        minutter = df_striker.groupby(['SHORTNAME', 'TEAMNAME'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_strikertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_classic_striker = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['SHORTNAME','TEAMNAME','MINUTESONFIELD total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_strikertotal = df_strikertotal.sort_values('Total score',ascending = False)
        return df_classic_striker
    
    def Targetman():
        df_striker = df_scouting[(df_scouting['POSITION1CODE'] == 'Striker') & (df_scouting['POSITION1CODESide'].str.contains('Centre'))]
        df_striker['MINUTESONFIELD'] = df_striker['MINUTESONFIELD'].astype(int)
        df_striker = df_striker[df_striker['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_striker = calculate_score(df_striker, 'TOUCHINBOX','TOUCHINBOX score')
        df_striker = calculate_score(df_striker, 'percent_successfuldPassesToFinalThird','percent_successfuldPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'shotFastbreak_per90','shotFastbreak_per90 score')
        df_striker = calculate_score(df_striker, 'bigChanceCreated_per90','bigChanceCreated_per90 score')
        df_striker = calculate_score(df_striker, 'newSuccessfulDribbles','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'TOUCHINBOX','TOUCHINBOX score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULKEYPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SHOTXG','SHOTXG score')
        df_striker = calculate_score(df_striker, 'SHOTXG','SHOTXG score')
        df_striker = calculate_score(df_striker, 'aerialWon','aerialWon score')


        df_striker['Linkup_play'] = df_striker[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score','Possession value score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score','aerialWon score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['TOUCHINBOX score','Possession value total score','bigChanceCreated_per90 score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Linkup play','Linkup play','Chance creation','Goalscoring','Goalscoring','Possession value','Possession value']].mean(axis=1)
        df_striker = df_striker[['SHORTNAME','TEAMNAME','MATCHLABEL','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()
        df_strikertotal = df_striker[['SHORTNAME','TEAMNAME','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['SHORTNAME','TEAMNAME']).mean().reset_index()
        minutter = df_striker.groupby(['SHORTNAME', 'TEAMNAME'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_strikertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_targetman = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['SHORTNAME','TEAMNAME','MINUTESONFIELD total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
        df_strikertotal = df_strikertotal.sort_values('Total score',ascending = False)
        return df_targetman

    def Boxstriker():
        df_striker = df_scouting[(df_scouting['POSITION1CODE'] == 'Striker') & (df_scouting['POSITION1CODESide'].str.contains('Centre'))]
        df_striker['MINUTESONFIELD'] = df_striker['MINUTESONFIELD'].astype(int)
        df_striker = df_striker[df_striker['MINUTESONFIELD'].astype(int) >= minutter_kamp]

        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS','Possession value total score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value score')
        df_striker = calculate_score(df_striker,'SUCCESSFULATTACKINGACTIONS', 'Possession value added score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSES_PERCENT', 'SUCCESSFULPASSES_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE', 'SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT', 'SUCCESSFULPASSESTOFINALTHIRD_PERCENT score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE', 'SUCCESSFULPROGRESSIVEPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULSHOTASSISTS','SUCCESSFULSHOTASSISTS score')
        df_striker = calculate_score(df_striker, 'TOUCHINBOX','TOUCHINBOX score')
        df_striker = calculate_score(df_striker, 'percent_successfuldPassesToFinalThird','percent_successfuldPassesToFinalThird score')
        df_striker = calculate_score(df_striker, 'shotFastbreak_per90','shotFastbreak_per90 score')
        df_striker = calculate_score(df_striker, 'bigChanceCreated_per90','bigChanceCreated_per90 score')
        df_striker = calculate_score(df_striker, 'newSuccessfulDribbles','newSuccessfulDribbles score')
        df_striker = calculate_score(df_striker, 'TOUCHINBOX','TOUCHINBOX score')
        df_striker = calculate_score(df_striker, 'SUCCESSFULKEYPASSES_AVERAGE','SUCCESSFULKEYPASSES_AVERAGE score')
        df_striker = calculate_score(df_striker, 'SHOTXG','SHOTXG score')
        df_striker = calculate_score(df_striker, 'SHOTXG','SHOTXG score')


        df_striker['Linkup_play'] = df_striker[['SUCCESSFULPASSESTOFINALTHIRD_PERCENT score','SUCCESSFULPASSES_PERCENT score','Possession value score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score']].mean(axis=1)
        df_striker['Chance_creation'] = df_striker[['TOUCHINBOX score','Possession value total score','bigChanceCreated_per90 score','TOUCHINBOX score','SUCCESSFULPASSESTOFINALTHIRD_AVERAGE score']].mean(axis=1)
        df_striker['Goalscoring_'] = df_striker[['SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score','SHOTXG score']].mean(axis=1)
        df_striker['Possession_value'] = df_striker[['Possession value total score','Possession value score','Possession value score','Possession value score']].mean(axis=1)

        df_striker = calculate_score(df_striker, 'Linkup_play', 'Linkup play')
        df_striker = calculate_score(df_striker, 'Chance_creation','Chance creation')
        df_striker = calculate_score(df_striker, 'Goalscoring_','Goalscoring')        
        df_striker = calculate_score(df_striker, 'Possession_value', 'Possession value')

        
        df_striker['Total score'] = df_striker[['Linkup play','Chance creation','Goalscoring','Goalscoring','Goalscoring','Goalscoring','Possession value','Possession value','Possession value']].mean(axis=1)
        df_striker = df_striker[['SHORTNAME','TEAMNAME','MATCHLABEL','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_striker = df_striker.dropna()
        df_strikertotal = df_striker[['SHORTNAME','TEAMNAME','MINUTESONFIELD','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]

        df_strikertotal = df_strikertotal.groupby(['SHORTNAME','TEAMNAME']).mean().reset_index()
        minutter = df_striker.groupby(['SHORTNAME', 'TEAMNAME'])['MINUTESONFIELD'].sum().astype(float).reset_index()
        df_strikertotal['MINUTESONFIELD total'] = minutter['MINUTESONFIELD']
        df_boksstriker = df_striker.sort_values('Total score',ascending = False)
        df_strikertotal = df_strikertotal[['SHORTNAME','TEAMNAME','MINUTESONFIELD total','Linkup play','Chance creation','Goalscoring','Possession value','Total score']]
        df_strikertotal= df_strikertotal[df_strikertotal['MINUTESONFIELD total'].astype(int) >= minutter_total]
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

players = events['SHORTNAME'].unique()
teams = events['TEAMNAME'].unique()
def plot_heatmap_location(data, title):
    pitch = Pitch(pitch_type='wyscout', line_zorder=2, pitch_color='grass', line_color='white')
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(data['location.x'], data['location.y'], statistic='count', bins=(50, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot')
    st.write(title)  # Use st.title() instead of plt.title()
    st.pyplot(fig)

def plot_heatmap_end_location(data, title):
    pitch = Pitch(pitch_type='wyscout', line_zorder=2, pitch_color='grass', line_color='white')
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(data['pass.endLocation.x'], data['pass.endLocation.y'], statistic='count', bins=(50, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot')
    st.write(title)  # Use st.title() instead of plt.title()
    st.pyplot(fig)

def pass_accuracy(df, kampvalg):
    df = df[df['MATCHLABEL'].isin(kampvalg)]
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

    # Plot shots (dots with size proportional to SHOTXG)
    shots = df[df['SHOTXG'] > 0]
    pitch.scatter(shots['location.x'], shots['location.y'], s=shots['SHOTXG'] * 100, color='yellow', edgecolors='black', ax=ax, alpha=0.6)

    # Use Streamlit to display the plot
    st.pyplot(fig)
  
def dashboard():
    st.title('U19 Dashboard')
    dangerzone_entries['TEAMNAME'] = dangerzone_entries['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    events = load_events()
    events['MATCHLABEL'] = events['MATCHLABEL'] + ' ' + events['DATE']
    events['DATE'] = pd.to_DATEtime(events['DATE'],utc=True)
    events = events.sort_values('DATE').reset_index(drop=True)
    events = events[events['TEAMNAME'].str.contains('Horsens')]
    matches = events['MATCHLABEL'].unique()
    matches = matches[::-1]
    match_choice = st.multiselect('Choose a match', matches)
    df_xg = load_xg()
    df_xg['MATCHLABEL'] = df_xg['MATCHLABEL'] + ' ' + df_xg['DATE']
    df_xg = df_xg.drop(columns=['DATE'],errors = 'ignore')
    events['TEAMNAME'] = events['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    df_xg['TEAMNAME'] = df_xg['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')

    df_matchstats = load_matchstats()
    df_matchstats['MATCHLABEL'] = df_matchstats['MATCHLABEL'] + ' ' + df_matchstats['DATE']
    df_matchstats = df_matchstats.drop(columns=['DATE'],errors = 'ignore')

    df_xg = df_xg[df_xg['MATCHLABEL'].isin(match_choice)]
    df_possession_stats = df_possession_stats[df_possession_stats['MATCHLABEL'].isin(match_choice)]
    df_matchstats = df_matchstats[df_matchstats['MATCHLABEL'].isin(match_choice)]
    penareaentries = penareaentries[penareaentries['MATCHLABEL'].isin(match_choice)]
    dangerzone_entries = dangerzone_entries[dangerzone_entries['MATCHLABEL'].isin(match_choice)]
    df_matchstats = df_matchstats.drop_duplicates()
    df_matchstats['TEAMNAME'] = df_matchstats['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    df_passes = df_matchstats[['TEAMNAME','MATCHLABEL','SUCCESSFULFORWARDPASSES_AVERAGE','SUCCESSFULFORWARDPASSES_AVERAGE']]

    df_passes = df_passes.groupby(['TEAMNAME','MATCHLABEL']).sum().reset_index()

    df_xg_summary = df_xg.groupby(['TEAMNAME','MATCHLABEL'])['SHOTXG'].sum().reset_index()
    df_ppda = df_ppda[df_ppda['MATCHLABEL'].isin(match_choice)]
    df_ppda = df_ppda.groupby(['TEAMNAME','MATCHLABEL'])['PPDA'].sum().reset_index()
    df_ppda = df_ppda.drop(columns=['DATE'],errors = 'ignore')
    df_ppda['TEAMNAME'] = df_ppda['TEAMNAME'] = df_ppda['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    penareaentries = penareaentries.groupby(['TEAMNAME','MATCHLABEL']).sum().reset_index()
    penareaentries = penareaentries.rename(columns={'count':'penaltyAreaEntryCount'})
    penareaentries['TEAMNAME'] = penareaentries['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    penareaentries = penareaentries.drop(columns=['DATE'],errors = 'ignore')
    df_possession_stats = df_possession_stats.value_counts(['territorial_possession','MATCHLABEL']).reset_index()
    df_possession_stats_grouped = df_possession_stats.groupby('MATCHLABEL')['count'].sum().reset_index()
    df_possession_stats_grouped.columns = ['MATCHLABEL', 'total_possession']

    # Merge back with original dataframe to calculate percentage
    df_possession_stats = pd.merge(df_possession_stats, df_possession_stats_grouped, on='MATCHLABEL')

    # Calculate the possession percentage
    df_possession_stats['terr_poss %'] = (df_possession_stats['count'] / df_possession_stats['total_possession']) * 100

    # Drop unnecessary columns if needed
    df_possession_stats = df_possession_stats.drop(columns=['total_possession','count'])
    df_possession_stats = df_possession_stats[df_possession_stats['territorial_possession'] != 'Middle']
    df_possession_stats = df_possession_stats.rename(columns={'territorial_possession':'TEAMNAME'})
    df_possession_stats['TEAMNAME'] = df_possession_stats['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
    dangerzone_entries = dangerzone_entries.value_counts(['TEAMNAME','MATCHLABEL']).reset_index()
    dangerzone_entries = dangerzone_entries.rename(columns={'count':'dangerzoneEntryCount'})
    team_summary = df_xg_summary.merge(df_passes, on=['TEAMNAME','MATCHLABEL'])
    team_summary = team_summary.merge(penareaentries, on=['TEAMNAME','MATCHLABEL'])
    team_summary = team_summary.merge(dangerzone_entries, on=['TEAMNAME','MATCHLABEL'])
    team_summary = team_summary.merge(df_ppda, on=['TEAMNAME','MATCHLABEL'])
    team_summary = team_summary.merge(df_possession_stats, on=['TEAMNAME','MATCHLABEL'])
    team_summary = team_summary.drop(columns=['MATCHLABEL'])
    team_summary = team_summary.groupby('TEAMNAME').mean().reset_index()
    team_summary = team_summary.round(2)
    st.dataframe(team_summary.style.format(precision=2), use_container_width=True,hide_index=True)
    

    def xg():
        df_xg = load_xg()

        all_xg = df_xg.copy()
        df_xg1 = df_xg.copy()
        all_xg['MATCHLABEL'] = all_xg['MATCHLABEL'] + ' ' + all_xg['DATE']
        df_xg_agg['MATCHLABEL'] = df_xg_agg['MATCHLABEL'] + ' ' + df_xg_agg['DATE']

        all_xg['DATE'] = pd.to_DATEtime(all_xg['DATE'], utc=True)
        all_xg = all_xg.sort_values('DATE').reset_index(drop=True)
        all_xg['match_xg'] = all_xg.groupby('MATCHLABEL')['SHOTXG'].transform('sum')
        all_xg['team_xg'] = all_xg.groupby(['MATCHLABEL', 'TEAMNAME'])['SHOTXG'].transform('sum')
        all_xg['xg_diff'] = all_xg['team_xg'] - all_xg['match_xg'] + all_xg['team_xg']
        all_xg['xG rolling average'] = all_xg.groupby('TEAMNAME')['xg_diff'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        fig = go.Figure()
        
        for team in all_xg['TEAMNAME'].unique():
            team_data = all_xg[all_xg['TEAMNAME'] == team]
            line_size = 5 if team == 'Horsens U19' else 1  # Larger line for Horsens
            fig.add_trace(go.Scatter(
                x=team_data['DATE'], 
                y=team_data['xG rolling average'], 
                mode='lines',
                name=team,
                line=dict(width=line_size)
            ))
        
        fig.upDATE_layout(
            title='3-Game Rolling Average of xG Difference Over Time',
            xaxis_title='DATE',
            yaxis_title='3-Game Rolling Average xG Difference',
            template='plotly_white'
        )
        st.header('Whole season')
        
        st.plotly_chart(fig)

        all_xg = all_xg[['TEAMNAME','xg_diff']]
        all_xg = all_xg.drop_duplicates()
        all_xg = all_xg.groupby('TEAMNAME')['xg_diff'].sum().reset_index()
        all_xg = all_xg.sort_values('xg_diff', ascending=False)
        df_xg['MATCHLABEL'] = df_xg['MATCHLABEL'] + ' ' + df_xg['DATE']
        df_xg1['MATCHLABEL'] = df_xg1['MATCHLABEL'] + ' ' + df_xg1['DATE']

        df_xg = df_xg[df_xg['MATCHLABEL'].isin(match_choice)]
        df_xg1 = df_xg1[df_xg1['MATCHLABEL'].isin(match_choice)]

        df_xg['match_xg'] = df_xg.groupby('MATCHLABEL')['SHOTXG'].transform('sum')
        df_xg['team_xg'] = df_xg.groupby(['MATCHLABEL','TEAMNAME'])['SHOTXG'].transform('sum')
        df_xg['xg_diff'] = df_xg['team_xg'] - df_xg['match_xg'] + df_xg['team_xg']
        df_xg = df_xg[['TEAMNAME','xg_diff']]
        df_xg = df_xg.drop_duplicates()
        df_xg = df_xg[df_xg['TEAMNAME'].str.contains('Horsens')]
        df_xg = df_xg.groupby('TEAMNAME')['xg_diff'].sum().reset_index()
        st.dataframe(all_xg, hide_index=True)
        st.header('Chosen matches')
        st.dataframe(df_xg, hide_index=True)
        df_xg1['TEAMNAME'] = df_xg1['TEAMNAME'].apply(lambda x: x if x == 'Horsens U19' else 'Opponent')
        df_xg1 = df_xg1.sort_values(by=['TEAMNAME','minute'])

        df_xg1['cumulative_xG'] = df_xg1.groupby(['TEAMNAME'])['SHOTXG'].cumsum()
        fig = go.Figure()
        
        for team in df_xg1['TEAMNAME'].unique():
            team_data = df_xg1[df_xg1['TEAMNAME'] == team]
            fig.add_trace(go.Scatter(
                x=team_data['minute'], 
                y=team_data['cumulative_xG'], 
                mode='lines',
                name=team,
            ))
        
        fig.upDATE_layout(
            title='Average Cumulative xG Over Time',
            xaxis_title='Time (Minutes)',
            yaxis_title='Average Cumulative xG',
            template='plotly_white'
        )
        st.plotly_chart(fig)
        df_xg_agg = df_xg_agg[df_xg_agg['MATCHLABEL'].isin(match_choice)]    
        df_xg_plot = df_xg_agg[['SHORTNAME','TEAMNAME','location.x','location.y', 'SHOTXG']]
        df_xg_plot = df_xg_plot[df_xg_plot['TEAMNAME'] == 'Horsens U19']
        pitch = Pitch(pitch_type='wyscout',half=True,line_color='white', pitch_color='grass')
        fig, ax = pitch.draw(figsize=(10, 6))
        
        sc = ax.scatter(df_xg_plot['location.x'], df_xg_plot['location.y'], s=df_xg_plot['SHOTXG'] * 100, c='yellow', edgecolors='black', alpha=0.6)
        
        for i, row in df_xg_plot.iterrows():
            ax.text(row['location.x'], row['location.y'], f"{row['SHORTNAME']}\n{row['SHOTXG']:.2f}", fontsize=6, ha='center', va='center')
        
        st.pyplot(fig)
        df_xg_plot = df_xg_plot.groupby(['SHORTNAME'])['SHOTXG'].sum().reset_index()
        df_xg_plot = df_xg_plot.sort_values('SHOTXG', ascending=False)
        st.dataframe(df_xg_plot, hide_index=True)
        
    def offensive_transitions():
        st.header('Whole season')
        st.write('Transition xg')
        transitions = events[events['POSSESSIONTYPE'].str.contains('transition|counterattack', case=False, na=False)]
        transitions = transitions.sort_values('DATE', ascending=False)
        transitionxg_chosen = transitions[transitions['MATCHLABEL'].isin(match_choice)]
        transitionxg_chosen = transitionxg_chosen.groupby(['TEAMNAME','MATCHLABEL','DATE'])['SHOTXG'].sum().reset_index()
        transitionxg_chosen = transitionxg_chosen.sort_values('DATE', ascending=False)
        transitionxg_chosen = transitionxg_chosen[['TEAMNAME','MATCHLABEL','SHOTXG']]
        transitionxg = transitions.groupby(['TEAMNAME'])['SHOTXG'].sum().reset_index()
        transitionxg_diff = transitions.copy()
        transitionxg = transitionxg.sort_values('SHOTXG', ascending=False)
        transitionxg_diff['match_xg'] = transitionxg_diff.groupby('MATCHLABEL')['SHOTXG'].transform('sum')
        transitionxg_diff['team_xg'] = transitionxg_diff.groupby(['MATCHLABEL', 'TEAMNAME'])['SHOTXG'].transform('sum')
        transitionxg_diff['xg_diff'] = transitionxg_diff['team_xg'] - transitionxg_diff['match_xg'] + transitionxg_diff['team_xg']
        transitionxg_diff = transitionxg_diff[['TEAMNAME','MATCHLABEL','xg_diff']]
        transitionxg_diff_chosen = transitionxg_diff[transitionxg_diff['MATCHLABEL'].isin(match_choice)]
        transitionxg_diff_chosen = transitionxg_diff_chosen.drop_duplicates()
        transitionxg_diff = transitionxg_diff.drop_duplicates()
        transitionxg_diff = transitionxg_diff.groupby('TEAMNAME')['xg_diff'].sum().reset_index()
        transitionxg_diff = transitionxg_diff.sort_values('xg_diff', ascending=False)
        st.dataframe(transitionxg_diff,hide_index=True)
        st.dataframe(transitionxg,hide_index=True)
        st.header('Chosen matches')
        transitionxg_chosen = transitionxg_chosen[transitionxg_chosen['TEAMNAME'] == 'Horsens U19']
        transitionxg_chosen = transitionxg_chosen.sort_values('SHOTXG',ascending=False)
        transitionxg_diff_chosen = transitionxg_diff_chosen[transitionxg_diff_chosen['TEAMNAME'] == 'Horsens U19']
        transitionxg_diff_chosen = transitionxg_diff_chosen.sort_values('xg_diff',ascending=False)

        st.dataframe(transitionxg_chosen, hide_index=True)
        st.dataframe(transitionxg_diff_chosen, hide_index=True)
        
        st.write('Interceptions/recoveries that lead to a chance')
        chance_start = transitions[transitions['TEAMNAME'].str.contains('Horsens')]
        chance_start = chance_start[chance_start['MATCHLABEL'].isin(match_choice)]
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
            label = f"{row['SHORTNAME']}\n{row['possession.attack.xg']:.2f}"
            ax.annotate(label, (row['location.x'], row['location.y']),
                        fontsize=8, ha='center', va='bottom', color='black', weight='bold',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='black'))

        # Display the plot in Streamlit
        st.pyplot(fig)
        st.write('Player involvement')
        player_involvement = chance_start.groupby(['SHORTNAME'])['possession.attack.xg'].sum().reset_index()
        player_involvement = player_involvement.sort_values('possession.attack.xg', ascending=False)
        st.dataframe(player_involvement, hide_index=True)

    def chance_creation():
        st.header('Whole season')
        penalty_area_entries = events[
            (events['LOCATIONX'] > 84) &
            ((events['LOCATIONY'] < 81) & (events['LOCATIONY'] > 19))
        ]
        dangerzone_entries = events[
            (events['LOCATIONX'] > 88) &
            ((events['LOCATIONY'] < 63) & (events['LOCATIONY'] > 37))
        ]
        dangerzone_entries_per_team = dangerzone_entries.groupby(['TEAMNAME'])['dangerzone_entry'].sum().reset_index()
        dangerzone_entries_per_team = dangerzone_entries_per_team.sort_values('dangerzone_entry', ascending=False)
        penalty_area_entries_per_team = penalty_area_entries.groupby(['TEAMNAME'])['penalty_area_entry'].sum().reset_index()
        penalty_area_entries_per_team = penalty_area_entries_per_team.sort_values('penalty_area_entry', ascending=False)
        penalty_area_entries_per_team = penalty_area_entries_per_team.merge(dangerzone_entries_per_team,how='outer', on='TEAMNAME')
        penalty_area_entries_per_team = penalty_area_entries_per_team.fillna(0)
        st.dataframe(penalty_area_entries_per_team, hide_index=True)
        st.header('Chosen matches')
        st.write('Penalty area entries')
        penalty_area_entries_matches = penalty_area_entries[penalty_area_entries['MATCHLABEL'].isin(match_choice)]
        player_penalty_area_entries = penalty_area_entries_matches[penalty_area_entries_matches['TEAMNAME'] == 'Horsens U19']
        player_penalty_area_received = player_penalty_area_entries.groupby(['pass.recipient.name'])['penalty_area_entry'].sum().reset_index()
        player_penalty_area_entries = player_penalty_area_entries.groupby(['SHORTNAME'])['penalty_area_entry'].sum().reset_index()
        penalty_area_entries_location = penalty_area_entries_matches.copy()
        penalty_area_entries_matches['Whole match'] = penalty_area_entries_matches.groupby('MATCHLABEL')['penalty_area_entry'].transform('sum')
        penalty_area_entries_matches['Team'] = penalty_area_entries_matches.groupby(['MATCHLABEL', 'TEAMNAME'])['penalty_area_entry'].transform('sum')
        penalty_area_entries_matches['Paentries Diff'] = penalty_area_entries_matches['Team'] - penalty_area_entries_matches['Whole match'] + penalty_area_entries_matches['Team']
        penalty_area_entries_matches = penalty_area_entries_matches[['TEAMNAME','MATCHLABEL', 'Paentries Diff']]
        penalty_area_entries_matches = penalty_area_entries_matches[penalty_area_entries_matches['TEAMNAME'] == 'Horsens U19']
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
        player_penalty_area_received = player_penalty_area_received.rename(columns={'pass.recipient.name': 'SHORTNAME','penalty_area_entry': 'penalty_area_received'})
        player_penalty_area_entries['penalty_area_entry'] = pd.to_numeric(player_penalty_area_entries['penalty_area_entry'], errors='coerce').fillna(0)
        player_penalty_area_received['penalty_area_received'] = pd.to_numeric(player_penalty_area_received['penalty_area_received'], errors='coerce').fillna(0)
        player_penalty_area_entries = player_penalty_area_entries.merge(player_penalty_area_received, on='SHORTNAME', how='outer')
        player_penalty_area_entries = player_penalty_area_entries.fillna(0)
        player_penalty_area_entries['Total'] = player_penalty_area_entries['penalty_area_entry'] + player_penalty_area_entries['penalty_area_received']
        player_penalty_area_entries = player_penalty_area_entries.sort_values('Total', ascending=False)

        st.dataframe(player_penalty_area_entries,hide_index=True)
        # Display the plot in Streamlit
        
        st.write('Dangerzone entries')
        dangerzone_entries_matches = dangerzone_entries[dangerzone_entries['MATCHLABEL'].isin(match_choice)]
        player_dangerzone_entries = dangerzone_entries_matches[dangerzone_entries_matches['TEAMNAME'] == 'Horsens U19']
        player_dangerzone_received = player_dangerzone_entries.groupby(['pass.recipient.name'])['dangerzone_entry'].sum().reset_index()
        player_dangerzone_entries = player_dangerzone_entries.groupby(['SHORTNAME'])['dangerzone_entry'].sum().reset_index()

        dangerzone_entries_location = dangerzone_entries_matches.copy()
        dangerzone_entries_matches['Whole match'] = dangerzone_entries_matches.groupby('MATCHLABEL')['dangerzone_entry'].transform('sum')
        dangerzone_entries_matches['Team'] = dangerzone_entries_matches.groupby(['MATCHLABEL', 'TEAMNAME'])['dangerzone_entry'].transform('sum')
        dangerzone_entries_matches['Dzentries Diff'] = dangerzone_entries_matches['Team'] - dangerzone_entries_matches['Whole match'] + dangerzone_entries_matches['Team']
        dangerzone_entries_matches = dangerzone_entries_matches[['TEAMNAME','MATCHLABEL', 'Dzentries Diff']]
        dangerzone_entries_matches = dangerzone_entries_matches.groupby(['TEAMNAME','MATCHLABEL'])['Dzentries Diff'].sum().reset_index()
        dangerzone_entries_matches = dangerzone_entries_matches[dangerzone_entries_matches['TEAMNAME'] == 'Horsens U19']
        dangerzone_entries_matches = dangerzone_entries_matches.round(2)
        dangerzone_entries_matches = dangerzone_entries_matches.sort_values('Dzentries Diff', ascending=False)
        st.dataframe(dangerzone_entries_matches,hide_index=True)
        dangerzone_entries_location['endLocation.x'] = dangerzone_entries_location['pass.endLocation.x'].combine_first(dangerzone_entries_location['carry.endLocation.x'])
        dangerzone_entries_location['endLocation.y'] = dangerzone_entries_location['pass.endLocation.y'].combine_first(dangerzone_entries_location['carry.endLocation.y'])
        dangerzone_entries_location = dangerzone_entries_location[dangerzone_entries_location['TEAMNAME'] == 'Horsens U19']
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
        player_dangerzone_received = player_dangerzone_received.rename(columns={'pass.recipient.name': 'SHORTNAME','dangerzone_entry': 'dangerzone_received'})
        player_dangerzone_entries = player_dangerzone_entries.merge(player_dangerzone_received,how='outer')
        player_dangerzone_entries = player_dangerzone_entries.fillna(0)
        player_dangerzone_entries['Total'] = player_dangerzone_entries['dangerzone_entry'] + player_dangerzone_entries['dangerzone_received']
        player_dangerzone_entries = player_dangerzone_entries.sort_values('Total', ascending=False)
        st.dataframe(player_dangerzone_entries,hide_index=True)
    
        
    Data_types = {
        'xG': xg,
        'Offensive transitions': offensive_transitions,
        'Chance Creation': chance_creation,
    }

    for i in range(1, 4):
        if f'selected_data{i}' not in st.session_state:
            st.session_state[f'selected_data{i}'] = ''

    # Create three columns for select boxes
    col1, col2, col3 = st.columns(3)

    # Function to create selectbox and upDATE session state without rerunning entire page
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
    # Load and preprocess match statistics data
    df_matchstats = load_matchstats()

    # Combine 'MATCHLABEL' with 'DATE' and round 'PPDA' values
    df_matchstats['MATCHLABEL'] += ' ' + df_matchstats['DATE']

    # Standardize DATE format if necessary
    df_matchstats['DATE'] = df_matchstats['DATE'].str.replace(r'GMT\+(\d)$', r'GMT+0\1:00', regex=True)

    # Aggregate match statistics and merge with PPDA data
    df_matchstats = df_matchstats.groupby(['TEAMNAME', 'MATCHLABEL', 'DATE']).sum().reset_index()

    # Set 'MATCHLABEL' column to 1 for non-null values
    df_matchstats['MATCHLABEL'] = np.where(df_matchstats['MATCHLABEL'].notnull(), 1, df_matchstats['MATCHLABEL'])

    # Convert 'DATE' column to UTC, then make it timezone-naive
    df_matchstats['DATE'] = pd.to_DATEtime(df_matchstats['DATE'], errors='coerce', utc=True).dt.tz_convert(None)

    # Drop rows with NaT in 'DATE'
    df_matchstats = df_matchstats.dropna(subset=['DATE'])

    # Define DATE range for slider
    min_DATE = df_matchstats['DATE'].min()
    max_DATE = df_matchstats['DATE'].max()
    DATE_range = pd.DATE_range(start=min_DATE, end=max_DATE, freq='D')
    DATE_options = DATE_range.strftime('%Y-%m-%d').tolist()

    # Ensure min_DATE and max_DATE are included in DATE_options
    if min_DATE.strftime('%Y-%m-%d') not in DATE_options:
        DATE_options.insert(0, min_DATE.strftime('%Y-%m-%d'))
    if max_DATE.strftime('%Y-%m-%d') not in DATE_options:
        DATE_options.append(max_DATE.strftime('%Y-%m-%d'))

    # Default DATEs for slider
    default_start_DATE = min_DATE.strftime('%Y-%m-%d')
    default_end_DATE = max_DATE.strftime('%Y-%m-%d')

    # Set up select_slider for DATE range selection
    selected_start_DATE, selected_end_DATE = st.select_slider(
        'Choose DATEs',
        options=DATE_options,
        value=(default_start_DATE, default_end_DATE)
    )

    # Convert selected DATEs to DATEtime (naive) for filtering
    selected_start_DATE = pd.to_DATEtime(selected_start_DATE, format='%Y-%m-%d')
    selected_end_DATE = pd.to_DATEtime(selected_end_DATE, format='%Y-%m-%d')

    # Filter the dataframe based on the selected DATE range
    df_matchstats = df_matchstats[
        (df_matchstats['DATE'] >= selected_start_DATE) & (df_matchstats['DATE'] <= selected_end_DATE)
    ]

    # Drop unnecessary columns
    columns_to_drop = ['player.id', 'SHORTNAME', 'matchId', 'position_names', 'POSITION1CODE']
    df_matchstats = df_matchstats.drop(columns=[col for col in columns_to_drop if col in df_matchstats.columns])
    # Perform aggregation
    df_matchstats = df_matchstats.groupby(['TEAMNAME']).agg({
        'MATCHLABEL': 'sum',
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


    # Create "per match" columns by dividing by 'MATCHLABEL', excluding PPDA
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

    # Create "per match" columns by dividing by 'MATCHLABEL'
    for col in columns_to_per_match:
        if col in df_matchstats.columns:  # Check if the column exists
            df_matchstats[f'{col}_per_match'] = df_matchstats[col] / df_matchstats['MATCHLABEL']

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
    sorted_teams = df_matchstats['TEAMNAME'].sort_values().unique()
    df_matchstats_1 = df_matchstats.set_index('TEAMNAME')
    # Display the DataFrame
    st.dataframe(df_matchstats_1)

    # Sort teams alphabetically for the selectbox

    # Select team from dropdown
    selected_team = st.selectbox('Choose team', sorted_teams)

    # Filter DataFrame for selected team
    team_df = df_matchstats.loc[df_matchstats['TEAMNAME'] == selected_team]

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


Data_types = {
    'Dashboard': dashboard,
    'Opposition analysis': opposition_analysis,
    }

st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
selected_data = st.sidebar.radio('Choose data type',list(Data_types.keys()))

st.cache_data(experimental_allow_widgets=True)
st.cache_resource(experimental_allow_widgets=True)
Data_types[selected_data]()
