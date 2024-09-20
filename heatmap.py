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

events = pd.read_csv(r'C:\Users\SéamusPeareBartholdy\Documents\GitHub\AC-Horsens-U19\events.csv')
loss = events[events['type.secondary'].str.contains('loss')]
#loss = loss[loss['label'].str.contains('Nordsjælland U19 - Horsens U19')]
loss = loss[loss['team.name'].str.contains('Brøndby')]
loss = loss[['player.name','location.x','location.y','pass.endLocation.x','pass.endLocation.y','carry.endLocation.x','carry.endLocation.y']]
print(loss)
pitch = Pitch(pitch_type='wyscout',line_zorder=2, pitch_color='grass', line_color='white')
fig, ax = pitch.draw()

x_coords = np.where(loss['pass.endLocation.x'] > 0, loss['pass.endLocation.x'], 
            np.where(loss['carry.endLocation.x'] > 0, loss['carry.endLocation.x'], loss['location.x']))

y_coords = np.where(loss['pass.endLocation.x'] > 0, loss['pass.endLocation.y'], 
            np.where(loss['carry.endLocation.x'] > 0, loss['carry.endLocation.y'], loss['location.y']))

# Plot the heatmap
fig.set_facecolor('#22312b')
bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(50, 25))  # Adjust bins as needed
bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot')

# Display the plot in Streamlit
st.pyplot(fig)

groundduels = pd.read_csv(r'C:\Users\SéamusPeareBartholdy\Documents\GitHub\AC-Horsens-U19\groundduels.csv')
groundduels = groundduels[groundduels['team.name'].str.contains('Horsens')]
groundduels = groundduels[groundduels['label'].str.contains('Nordsjælland U19 - Horsens U19')]
pitch = Pitch(pitch_type='wyscout', line_zorder=2, pitch_color='grass', line_color='white')
fig, ax = pitch.draw()

# Extract coordinates
x_coords = groundduels['location.x']
y_coords = groundduels['location.y']

# Scatter plot with color based on 'groundDuel.stoppedProgress'
colors = groundduels['groundDuel.stoppedProgress'].apply(lambda x: 'green' if x else 'red')
sc = ax.scatter(x_coords, y_coords, c=colors, s=100, edgecolors='black', linewidth=0.5, zorder=3)
st.pyplot(fig)
