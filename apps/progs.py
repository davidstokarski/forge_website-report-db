from datetime import datetime
from werkzeug.utils import secure_filename
import os

# FOR TESTING .csv PURPOSES
import pandas as pd
from folium import plugins
import folium

def allowed_file(filename,ALLOWED_FILES):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_FILES

def process_csv(file_loc):
    csv_name=file_loc
    SSB_incident_locations = pd.read_csv(csv_name)

    #creating an initial base layer
    map = folium.Map(location=[SSB_incident_locations.Latitude.mean()-20, SSB_incident_locations.Longitude.mean()], zoom_start=3, control_scale=True)
    map

    #defining locations
    location = [SSB_incident_locations["Latitude"], SSB_incident_locations["Longitude"]]
    popups=SSB_incident_locations['Title']

    marker_cluster = plugins.MarkerCluster().add_to(map)
    count = 0
    for i in location[0]:
        folium.Marker([location[0][count], location[1][count]], popup=popups[count]).add_to(marker_cluster)
        count += 1
    map

    #option to save map as an html page
    map.save(os.path.join('apps/templates/temp','ClusterMapTestSSB.html'))
    return map

def process_csvOLD(file,filename):
    new_file=file
    filename=secure_filename(new_file.filename)
    new_filename = f'{filename.split(".")[0]}_{str(datetime.now())}.csv'
    save_location=os.path.join('website','output',new_filename)
    new_file.save(save_location)
    return save_location