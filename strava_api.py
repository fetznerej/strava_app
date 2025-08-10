# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import sys 
sys.path.append("/Users/emilyfetzner/Desktop/Desktop - Emily’s MacBook Air/run_app/strava_app") 


import pandas as pd
from extract_data.pull_activities import main
import numpy as np
import folium
import os
import webbrowser

all_activities = main()


# ----------------------------------------
# Convert to DF 
# ----------------------------------------

# Define column names
column_names = ['start_date_local', 'name', 'type', 'distance', 'average_heartrate', 'average_speed', 'elapsed_time', 'map.summary_polyline']

full_activity_df = pd.json_normalize(all_activities)


activity_df = full_activity_df[column_names]

    
# ----------------------------------------    
## Clean up
# ----------------------------------------

def meters_to_miles(distance_in_meters, conversion = 1609.34):
    # Conversion factor from meters to miles

    # Convert distance from meters to miles
    distance_in_miles = distance_in_meters / conversion
    
    return distance_in_miles


def ms_to_min_per_mile(speed_in_ms, conversion = 1609.34):
    # Conversion factor from meters per second to miles per hour

    distance_miles = speed_in_ms / conversion
    
    # Convert speed from mph to minutes per mile
    if distance_miles == 0:
        return float('inf')  # return infinity if speed is zero to avoid division by zero
    else:
        mile_per_min = distance_miles * 60
        return 1/mile_per_min
    
    
def time_elapsed(time):
    time_in_min = time/60
    time_in_hr = time_in_min / 60
    return time_in_hr



    
# Filter out running activities only
running_df = activity_df[activity_df["type"] == "Run"].drop_duplicates()

# Apply the conversion function to the 'distance' column
running_df['distance'] = running_df['distance'].apply(meters_to_miles)

# Apply the conversion function to the 'pace' column
running_df['pace'] = running_df['average_speed'].apply(ms_to_min_per_mile)


running_df['elapsed_time'] = running_df['elapsed_time'].apply(time_elapsed)

# mae sure data is in right format 

running_df['start_date_local'] = pd.to_datetime(running_df['start_date_local'])


def convert_pace(pace):
    try:
        if np.isinf(pace) or np.isnan(pace):
            return None
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/mile"
    except Exception as e:
        print(e)
        return None


def convert_elapsed_time(hours):
    try:
        if np.isinf(hours) or np.isnan(hours):
            return None
        total_seconds = int(hours * 3600)
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception as e:
        return None

# Applying the function to the pace column
running_df['formatted_pace'] = running_df['pace'].apply(convert_pace)


# Applying the function to the elapsed_time column
running_df['formatted_elapsed_time'] = running_df['elapsed_time'].apply(convert_elapsed_time)


from pypolyline.cutil import decode_polyline
import folium
import pandas as pd
import polyline  # Make sure the polyline library is installed

# Function to decode polyline safely
def decode_poly(polyline_str):
    try:
        if not polyline_str or pd.isna(polyline_str):
            return None  # Handle empty or NaN values
        # If the polyline is in bytes, decode it to a string
        if isinstance(polyline_str, bytes):
            polyline_str = polyline_str.decode('utf-8')  # Decode bytes to string
        return polyline.decode(polyline_str)  # Decode the polyline string
    except Exception as e:
        print(f"Error decoding polyline {polyline_str}: {e}")
        return None

# Ensure there are no NaN values in the column, replace with empty strings
running_df['map.summary_polyline'] = running_df['map.summary_polyline'].fillna('')

# Apply the decoding function to each polyline
running_df['decoded_map'] = running_df['map.summary_polyline'].apply(decode_poly)

    
## MAP

# Function to ensure the coordinates are in the correct format
def ensure_decoded(polyline):
    if isinstance(polyline, str):
        return decode_polyline(polyline, 5)
    return polyline

# no treadmill
outside_runs = running_df[~pd.isna(running_df['decoded_map'])]

# Create a map centered at the centroid of the first route with OpenStreetMap tiles
first_run = outside_runs.iloc[0, :]
decoded_map = ensure_decoded(first_run['decoded_map'])

if decoded_map is not None:
    # Calculate the centroid of the first run
    latitudes = [coord[0] for coord in decoded_map]
    longitudes = [coord[1] for coord in decoded_map]
    centroid = [np.mean(latitudes), np.mean(longitudes)]

    # Initialize the map with the centroid
    all_routes_map = folium.Map(location=centroid, zoom_start=13, tiles='OpenStreetMap')

    # Iterate through each route in the filtered DataFrame (outside_runs)
    for index, row in outside_runs.iterrows():
        decoded_map = ensure_decoded(row['decoded_map'])
        if decoded_map is not None:
            # Add the route to the map
            folium.PolyLine(decoded_map, color="blue", weight=2.5, opacity=.45).add_to(all_routes_map)

    # Save the map to the user's home directory
    map_file = os.path.join(os.path.expanduser("~"), "all_routes_map.html")
    all_routes_map.save(map_file)

    # Print the path to the map file
    print(f"Map saved as {map_file}")

    # Open the HTML file in the default web browser
    webbrowser.open(map_file)



from folium.plugins import HeatMap

# Function to ensure the coordinates are in the correct format
def ensure_decoded(polyline):
    if isinstance(polyline, str):
        return decode_polyline(polyline, 5)
    return polyline

# Collect all coordinates for the heat map
all_coords = []

# Iterate through each route in the DataFrame
for index, row in running_df.iterrows():
    decoded_map = ensure_decoded(row['decoded_map'])
    if decoded_map is not None:
        # Reverse coordinates: (latitude, longitude) -> (longitude, latitude)
        decoded_map_corrected = [(coord[1], coord[0]) for coord in decoded_map]
        all_coords.extend(decoded_map_corrected)

if all_coords:
    # Calculate the centroid for initializing the map
    latitudes = [coord[0] for coord in all_coords]
    longitudes = [coord[1] for coord in all_coords]
    centroid = [np.mean(latitudes), np.mean(longitudes)]

    # Create a map centered at the calculated centroid with OpenStreetMap tiles
    heat_map = folium.Map(location=centroid, zoom_start=13, tiles='OpenStreetMap')

    # Add the heat map
    HeatMap(all_coords, radius=8, blur=6).add_to(heat_map)

    # Save the map to an HTML file
    map_file = "heat_map.html"
    heat_map.save(map_file)

    # Print the path to the map file
    print(f"Map saved as {os.path.abspath(map_file)}")

    # Open the HTML file in the default web browser
    import webbrowser
    webbrowser.open(os.path.abspath(map_file))
else:
    print("No valid routes found")
'''
import osmnx as ox
import geopandas as gpd
from shapely.geometry import LineString
import os

# Set cache directory for osmnx
cache_dir = os.path.expanduser('~/.osmnx_cache')
os.makedirs(cache_dir, exist_ok=True)
ox.settings.cache_folder = cache_dir
ox.settings.use_cache = True

# Function to ensure the coordinates are in the correct format
def ensure_decoded(polyline):
    if isinstance(polyline, str):
        return decode_polyline(polyline, 5)
    return polyline

# Collect all coordinates and create LineString for each route
all_routes = []

for index, row in running_df.iterrows():
    decoded_map = ensure_decoded(row['decoded_map'])
    if decoded_map is not None:
        # Reverse coordinates: (latitude, longitude) -> (longitude, latitude)
        decoded_map_corrected = [(coord[1], coord[0]) for coord in decoded_map]
        if len(decoded_map_corrected) > 1:  # Ensure there are at least two points
            try:
                route_line = LineString(decoded_map_corrected)
                all_routes.append(route_line)
            except Exception as e:
                print(f"Error creating LineString for row {index}: {e}")

# Create a GeoDataFrame for the running routes
gdf_routes = gpd.GeoDataFrame(geometry=all_routes, crs="EPSG:4326")

# Ensure all geometries are valid
gdf_routes = gdf_routes[gdf_routes.is_valid]

# Debugging: Print coordinate values to identify anomalies
print("Coordinate values (first 5 routes):")
for geom in gdf_routes.geometry.head():
    print(geom)

# Check if there are valid routes
if gdf_routes.empty:
    print("No valid routes found.")
else:
    # Filter out any geometries with invalid bounds
    gdf_routes = gdf_routes[gdf_routes.bounds.apply(lambda x: not (x.minx < -180 or x.maxx > 180 or x.miny < -90 or x.maxy > 90), axis=1)]

    # Check if there are valid routes after filtering
    if gdf_routes.empty:
        print("No valid routes found after filtering.")
    else:
        # Get the road network for Washington DC
        G = ox.graph_from_place('Washington, D.C., USA', network_type='all')
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Reproject the road network and routes to the same CRS (Web Mercator for area calculation)
        gdf_routes = gdf_routes.to_crs(epsg=3857)
        edges = edges.to_crs(epsg=3857)

        # Debugging: Print route geometries after transformation
        print("Route geometries (EPSG:3857):", gdf_routes)
        
        # Debugging: Print CRS and bounds to verify
        print("Routes CRS:", gdf_routes.crs)
        print("Edges CRS:", edges.crs)
        print("Routes bounds:", gdf_routes.total_bounds)
        print("Edges bounds:", edges.total_bounds)

        # Spatial join to find intersecting roads
        intersecting_roads = gpd.sjoin(edges, gdf_routes, how="inner", predicate='intersects')

        # Debugging: Print intersecting roads
        print("Intersecting roads:", intersecting_roads)

        # Calculate the total length of roads in Washington DC
        total_road_length = edges['geometry'].length.sum()

        # Calculate the total length of intersected roads
        intersected_road_length = intersecting_roads['geometry'].length.sum()

        # Calculate the percentage of roads covered
        percentage_covered = (intersected_road_length / total_road_length) * 100

        print(f"Percentage of roads covered by running: {percentage_covered:.2f}%")




def get_week_starting_date(date):
    return date - pd.DateOffset(days=date.dayofweek)





# Create a new column 'Week Starting' with the week starting date for each row
#running_df['Week Starting'] = running_df['start_date_local'].apply(get_week_starting_date)

running_df['Week Starting'] = running_df['start_date_local'].apply(get_week_starting_date).dt.date

running_df['Week Starting'] = pd.to_datetime(running_df['Week Starting'])




def determine_run_length(distance, long=11, short=3):
    if distance >= long:
        return "Long Run"
    elif distance <= short:
        return "Short Run"
    else:
        return "Standard Run"

running_df['Run_length'] = running_df['distance'].apply(determine_run_length)

# Group DataFrame by week and count runs
weekly_runs = running_df.groupby(['Week Starting', "Run_length"]).agg({'name': 'count', 'distance': 'sum'}).reset_index()




# Vizz


from bokeh.plotting import figure, show
from bokeh.io import output_file


# Create scatter plot
scatter_plot = figure(title='Scatter Plot', x_axis_label='Pace', y_axis_label='Distance')
scatter_plot.circle('pace', 'distance', source=running_df)

# Show the plot
show(scatter_plot)

# Specify the output file (optional)
output_file("scatter_plot.html")

show(scatter_plot)

import plotly.express as px

# Example plot with Plotly Express
fig = px.scatter(running_df, x='pace', y='distance')
#fig.show()
fig.write_html("dashboard.html")




# Create a list of years from the 'Week Starting' column
years = pd.to_datetime(weekly_runs['Week Starting']).dt.year.unique().tolist()

# Define a color palette
color_palette = {'Long Run': 'lightsteelblue', 'Short Run': 'cadetblue', 'Standard Run': 'steelblue'}

# Create Plotly bar chart with custom colors
fig = px.bar(weekly_runs, x="Week Starting", y="distance", text_auto='.2s', color="Run_length", 
             color_discrete_map=color_palette, title="Weekly Run Breakdown")


# Add range slider
fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)

fig.update_layout({
'plot_bgcolor': 'rgba(0, 0, 0, 0)',
'paper_bgcolor': 'rgba(0, 0, 0, 0)',
},
    legend_title_text ="Test")

fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)



# Write the interactive HTML file
fig.write_html("dashboard2.html" , auto_open=True)



# DB connect
import psycopg2
from sqlalchemy import create_engine


# PostgreSQL connection parameters
db_config = {
    'user': 'postgres',
    'password': 'jarvo3000',
    'host': 'localhost',  # or your host
    'port': '5432',       # default PostgreSQL port
    'database': 'running_ejf'
}

conn = psycopg2.connect(**db_config)


# Create engine for SQLAlchemy
engine = create_engine(f'postgresql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}')

# running table
table_name = 'running_data'
running_df.to_sql(table_name, engine, if_exists='replace', index=False)


# weekly summary table
table_name = 'weekly_summary'
weekly_stats.to_sql(table_name, engine, if_exists='replace', index=False)

# Close the connection
conn.close()