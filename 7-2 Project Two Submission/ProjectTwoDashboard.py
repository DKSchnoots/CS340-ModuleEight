#!/usr/bin/env python
# coding: utf-8

# In[3]:


# Setup the Jupyter version of Dash
from jupyter_dash import JupyterDash

# Configure the necessary Python module imports for dashboard components
import dash
import dash_leaflet as dl
#import dash_table as dt
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import base64
import plotly.express as px
from animal_shelter_crud1 import AnimalShelter

# Data Manipulation / Model
username = "aacuser"
password = "SNHU1234"
shelter = AnimalShelter(username, password)
df = pd.DataFrame.from_records(shelter.read({}))
df.drop(columns=['_id'], inplace=True)

# Dashboard Layout / View
app = JupyterDash(__name__)

# FIX ME: Add in Grazioso Salvare’s logo
image_filename = 'Grazioso Salvare Logo.png'  # Company image
encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode('utf-8')

app.layout = html.Div([
    html.Center(html.Img(src='data:image/png;base64,{}'.format(encoded_image))),
    html.Center(html.B(html.H1('Jamie Javis = CS-340 Dashboard'))),
    html.Center(html.P('Select up to five from the table for the map')),
    html.Div([
        dcc.RadioItems(
            id='filter-type',
            options=[
                {'label': 'Water Rescue', 'value': 'WR'},
                {'label': 'Mountain/Wilderness Rescue', 'value': 'MWR'},
                {'label': 'Disaster Rescue/Individual Tracking', 'value': 'DRIT'},
                {'label': 'Reset - returns unfiltered state', 'value': 'RESET'}
            ],
            value='RESET',
            labelStyle={'display': 'inline-block'}
        )
    ]),
    dash_table.DataTable(
        id='datatable-id',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns
        ],
        data=df.to_dict('records'),
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable=False,
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=10,
    ),
    html.Div(className='row', style={'display': 'flex'}, children=[
        html.Div(id='graph-id', className='col s12 m6'),
        html.Div(id='map-id', className='col s12 m6')
    ])
])

# Interaction Between Components / Controller
@app.callback([Output('datatable-id', 'data'),
               Output('datatable-id', 'columns')],
              [Input('filter-type', 'value')])
def update_dashboard(filter_type):
    if filter_type == 'WR':
        # Complex queries for water rescue
        df = pd.DataFrame(list(shelter.read({'$and': [{'sex_upon_outcome': 'Intact Female'},
                                                      {'$or': [
                                                          {'breed': 'Labrador Retriever Mix'},
                                                          {'breed': 'Chesa Bay Retr Mix'},
                                                          {'breed': 'Newfoundland Mix'},
                                                          {'breed': 'Newfoundland/Labrador Retriever'},
                                                          {'breed': 'Newfoundland/Australian Cattle Dog'},
                                                          {'breed': 'Newfoundland/Great Pyrenees'}]},
                                                      {'$and': [{'age_upon_outcome_in_weeks': {'$gte': 26}},
                                                                {'age_upon_outcome_in_weeks': {'$lte': 156}}]}]})))
    elif filter_type == 'MWR':
        # Complex queries for mountain/wilderness rescue
        df = pd.DataFrame(list(shelter.read({'$and': [{'sex_upon_outcome': 'Intact Male'},
                                                      {'$or': [
                                                          {'breed': 'German Shepherd'},
                                                          {'breed': 'Alaskan Malamute'},
                                                          {'breed': 'Old English Sheepdog'},
                                                          {'breed': 'Rottweiler'},
                                                          {'breed': 'Siberian Husky'}]},
                                                      {'$and': [{'age_upon_outcome_in_weeks': {'$gte': 26}},
                                                                {'age_upon_outcome_in_weeks': {'$lte': 156}}]}]})))
    elif filter_type == 'DRIT':
        # Complex queries for disaster rescue/individual tracking
        df = pd.DataFrame(list(shelter.read({'$and': [{'sex_upon_outcome': 'Intact Male'},
                                                      {'$or': [
                                                          {'breed': 'Doberman Pinscher'},
                                                          {'breed': 'German Shepherd'},
                                                          {'breed': 'Golden Retriever'},
                                                          {'breed': 'Bloodhound'},
                                                          {'breed': 'Rottweiler'}]},
                                                      {'$and': [{'age_upon_outcome_in_weeks': {'$gte': 20}},
                                                                {'age_upon_outcome_in_weeks': {'$lte': 300}}]}]})))
    elif filter_type == 'RESET':
        df = pd.DataFrame.from_records(shelter.read({}))

    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
    data = df.to_dict('records')

    return data, columns

@app.callback(
    Output('datatable-id', 'style_data_conditional'),
    [Input('datatable-id', 'selected_columns')]
)
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]

@app.callback(
    Output('graph-id', "children"),
    [Input('datatable-id', "derived_viewport_data")])
def update_graphs(viewData):
    dff = pd.DataFrame.from_dict(viewData)
    names = dff['breed'].value_counts().keys().tolist()
    values = dff['breed'].value_counts().tolist()
    return [
        dcc.Graph(
            figure=px.pie(
                data_frame=dff,
                values=values,
                names=names,
                color_discrete_sequence=px.colors.sequential.RdBu,
                width=800,
                height=500
            )
        )
    ]

@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "derived_viewport_data"),
     Input('datatable-id', 'selected_rows'),
     Input('datatable-id', 'selected_columns')])
def update_map(viewData, selected_rows, selected_columns):
    dff = pd.DataFrame.from_dict(viewData)
    if selected_rows == []:
        selected_rows = [0]

    markers = [
        dl.Marker(
            position=[row['location_lat'], row['location_long']],
            children=[
                dl.Tooltip(row['animal_name']),
                dl.Popup([
                    html.H4("Animal Name"),
                    html.P(row['animal_name']),
                    html.H4("Sex"),
                    html.P(row['sex']),
                    html.H4("Breed"),
                    html.P(row['breed']),
                    html.H4("Age"),
                    html.P(row['age'])
                ])
            ]
        ) for index, row in dff.iloc[selected_rows].iterrows()
    ]

    return [
        dl.Map(style={'width': '1000px', 'height': '500px'}, center=[30.75, -97.48], zoom=10, children=[
            dl.TileLayer(id="base-layer-id"),
            *markers
        ])
    ]

app.run_server(mode="inline")

# Instantiate the AnimalShelter object
if __name__ == "__main__":
    animal_shelter = AnimalShelter()

    # Example usage
    example = {"animal_type": "Dog", "name": "Lucky"}
    create_result = animal_shelter.create(example)
    print(create_result)  # Should print True or False

    cursor = animal_shelter.read({"animal_type": "Dog"})
    for doc in cursor:
        print(doc)

    update_result = animal_shelter.update({"animal_type": "Dog"}, {"name": "Linda"})
    print(update_result)  # Should print the number of modified documents

    delete_result = animal_shelter.delete({"animal_type": "Dog"})
    print(delete_result)  # Should print the number of deleted documents


# In[ ]:





# In[ ]:




