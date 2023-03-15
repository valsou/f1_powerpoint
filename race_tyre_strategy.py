import fastf1 as ff1
from fastf1 import plotting
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

# Enable FastF1 cache
ff1.Cache.enable_cache('cache')

YEAR = 2022
GRAND_PRIX = 'Jeddah'
SESSION = 'R'

compound_colors = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFF200',
    'HARD': '#EBEBEB',
    'INTERMEDIATE': '#39B54A',
    'WET': '#00AEEF',
}

# Load the session data
race = ff1.get_session(YEAR, GRAND_PRIX, SESSION)
race.load()

laps = race.laps

# Lap by lap with a set of Track Status
# (LapNumber, {TrackStatus, ...})
all_laps = []
race_total_laps = 0

for name, group in laps[['Driver', 'LapNumber', 'TrackStatus']].groupby('LapNumber'):
    race_total_laps = name
    all_track_status = set()
    for _, lap in group.iterrows():
        for dig in lap['TrackStatus']:
            all_track_status.add(int(dig))

    all_laps.append((name, all_track_status))

# [(LapBegin, LapEnd, Status), ...]
laps_interrupted = []
tmp_lap_begin = 0
tmp_status = ''
interruption_detected = False

for lap in all_laps:
    # Safety Car
    if 4 in lap[1]:
        if interruption_detected == False:
            tmp_lap_begin = lap[0]
            tmp_status = 'SC'
            interruption_detected = True
    # Virtual Safety Car
    elif 6 in lap[1]:
        if interruption_detected == False:
            tmp_lap_begin = lap[0]
            tmp_status = 'VSC'
            interruption_detected = True
    elif interruption_detected == True:
        laps_interrupted.append((tmp_lap_begin, lap[0], tmp_status))
                                
        # Reset values
        tmp_lap_begin = 0
        tmp_status = ''
        interruption_detected = False

# Driver Stints
driver_stints = laps[['Driver', 'Stint', 'Compound', 'LapNumber', 'FreshTyre']].groupby(
    ['Driver', 'Stint', 'Compound', 'FreshTyre']
).count().reset_index()
driver_stints = driver_stints.rename(columns={'LapNumber': 'StintLength'})
driver_stints = driver_stints.sort_values(by=['Stint'])

stints = [stint['Stint'] for _, stint in driver_stints.iterrows()]
results = [driver for driver in race.results['Abbreviation']]    

data = []

# Stint compound stacked by driver
for driver in race.results['Abbreviation']:
    stints = driver_stints.loc[driver_stints['Driver'] == driver]

    for _, stint in stints.iterrows():
        pattern = '' if stint['FreshTyre'] else '.'
        data.append(go.Bar(
            x=[stint['StintLength']],
            y=[driver],
            marker_line=dict(width=1, color='black'),
            marker=dict(color=compound_colors[stint['Compound']]),
            text=stint['Compound'][0],
            orientation='h',
            marker_pattern_shape=pattern,
            marker_pattern_fgcolor='black',
            marker_pattern_size=5
        ))

layout = dict(title_text=f'{GRAND_PRIX} {YEAR} - Race Tyre Strategy',
              title_x=0.5,
              barmode='stack',
              yaxis={'title': 'Drivers'},
              xaxis={'title': 'Lap', 'dtick': '1'},
              showlegend=False
)

fig = go.Figure(data=data, layout=layout)

# Track Interruptions like Safety Car & Virtual Safety Car
for interruption in laps_interrupted:
    fig.add_shape(
        type='rect',
        x0=interruption[0],
        y0=-1,
        x1=interruption[1],
        y1=len(race.results['Abbreviation'])-1,
        fillcolor='yellow',
        line_width=0,
        opacity=0.3
    )

    fig.add_annotation(
        x=interruption[0],
        y=len(race.results['Abbreviation'])-1,
        showarrow=True,
        text=interruption[2]
    )

fig.show()