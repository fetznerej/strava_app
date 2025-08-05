#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:50:32 2024

@author: emilyfetzner
"""







from pypolyline.cutil import decode_polyline
import folium
    
def decode_poly(polyline):
    try:
        if not polyline or pd.isna(polyline):
            return None  # Handle empty or NaN values
        return decode_polyline(polyline, 5)
    except Exception as e:
        print(f"Error decoding polyline {polyline}: {e}")
        return None

# Ensure there are no NaN values in the column
running_df['map.summary_polyline'] = running_df['map.summary_polyline'].fillna('')

running_df['decoded_map'] = running_df['map.summary_polyline'].apply(decode_poly)

running_df['map.summary_polyline'] = running_df['map.summary_polyline'].astype(bytes)





# Function to ensure the coordinates are in the correct format
def ensure_decoded(polyline):
    if isinstance(polyline, str):
        return decode_polyline(polyline, 5)
    return polyline



# Create a map centered at the centroid of the first route with OpenStreetMap tiles
first_ride = running_df.iloc[0, :]
decoded_map = ensure_decoded(first_ride['decoded_map'])

# Reverse the coordinates: (latitude, longitude) -> (longitude, latitude)
decoded_map_corrected = [(coord[1], coord[0]) for coord in decoded_map]


if decoded_map is not None:

    latitudes = [coord[0] for coord in decoded_map_corrected]
    longitudes = [coord[1] for coord in decoded_map_corrected]
    centroid = [np.mean(latitudes), np.mean(longitudes)]

    # Initialize the map
    all_routes_map = folium.Map(location=centroid, zoom_start=13, tiles='OpenStreetMap')

    # Iterate through each route in the DataFrame
    for index, row in running_df.iterrows():
        decoded_map = ensure_decoded(row['decoded_map'])
        if decoded_map is not None:
            # Reverse coordinates: (latitude, longitude) -> (longitude, latitude)
            decoded_map_corrected = [(coord[1], coord[0]) for coord in decoded_map]

            # Add the ride route to the map
            folium.PolyLine(decoded_map_corrected, color="blue", weight=2.5, opacity=.25).add_to(all_routes_map)

    # Save the map to an HTML file
    map_file = "all_routes_map.html"
    all_routes_map.save(map_file)

    # Print the path to the map file
    print(f"Map saved as {os.path.abspath(map_file)}")

    # Open the HTML file in the default web browser
    import webbrowser
    webbrowser.open(os.path.abspath(map_file))
else:
    print("First route is not in the expected format")