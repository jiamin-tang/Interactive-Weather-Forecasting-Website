import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
import dash_table
import pandas as pd

from data_acquire import load_forecast_data
from database import fetch_forecast_data_as_df

# Definitions of constants. This projects uses extra CSS stylesheet at `./assets/style.css`
COLORS = ['rgb(67,67,67)', 'rgb(115,115,115)', 'rgb(49,130,189)', 'rgb(189,189,189)']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/style.css']

# Define the dash app first
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define component functions
def page_header():
    """
    Returns the page header as a dash `html.Div`
    """
    return html.Div(id='header', children=[
        html.Div([html.H3('Weather Exploration with Air Quality')],
                 className="ten columns"),

        html.A([html.Img(id='logo', src=app.get_asset_url('github.png'),
                         style={'height': '35px', 'paddingTop': '7%'}),
                html.Span('Shake Shake', style={'fontSize': '2rem', 'height': '35px', 'bottom': 0,
                                                'paddingLeft': '4px', 'color': '#a3a7b0',
                                                'textDecoration': 'none'})],
               className="two columns row",
               href='https://github.com/yiweisang97/data1050-final-project-shake-shake/'),
        
        html.Div(children=[dcc.Markdown('''
        Developed by 
        Yiwei Sang, 
        Jiamin Tang, 
        Qinyun Wu, 
        Zeyan Du
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row"),

        html.Div(children=[dcc.Markdown('''
        [About Page](https://docs.google.com/document/d/1k4v4rgel3_xJdulQ0ch_x7ybQcCo2DULQ81QOnYUShU/edit), 
        [Additional Details](https://docs.google.com/document/d/18XoGPsdgbGC5XbXeA5Yrj0VoRzE6wc47bA8wkq61qhU/edit?usp=sharing)
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")
    ], className="row")


def description():
    """
    Returns overall project description in markdown
    """
    return html.Div(children=[dcc.Markdown('''
        # Weather Forecast
        Weather impacts every facet of our daily life and is the most influential external factor
        in the economy. Weather strategies involved in industries such as agriculture, retail, 
        transportation, manufacturing, energy and utilities to anticipate and plan have boosted
        in recent years. They contribute a lot to optimizing operations, reducing cost and excavating
        new opportunities.

        Accurate weather forecast helps ensure that we are prepared for the upcoming affairs. In this
        case, our tool offers queries about cities in the United States. We provide both forecast in
        next 24 hours and in the following 10 days to help you make better decisions.
        
        ### Data Source
        In this case, we stay ahead of weather conditions through API from [World Weather Online]
        (https://www.worldweatheronline.com/developer/api/docs/local-city-town-weather-api.aspx).
        Weather data is gathered from 1st July, 2008 to present time and keeps updating.
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def display_date(date_time):
    dict_weekday = {0:'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}
    return '{}, {}'.format(date_time.strftime(format='%Y-%m-%d'), dict_weekday[date_time.weekday()])

#df_table = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv') #Change city when available
def weather_table():
    df_static_daily_forecast = fetch_forecast_data_as_df()[0]
    df_static_daily_forecast['datetime'] = df_static_daily_forecast['datetime'].apply(display_date)
    return html.Div(children=[
        dcc.Markdown('''New York Weather Forecast''', className='row',style={'paddingLeft': '50%'}),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_static_daily_forecast.columns],
            data=df_static_daily_forecast.to_dict('records'),
            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
            style_cell={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white',
            },
        )
    ],style={'marginTop': '2rem', 'width': '500px', 'marginLeft': '200px', 'display': 'inline-block'})


def hourly_static_stacked_trend_graph(stack=False):
    """
    Returns scatter line plot of related weather features.
    If `stack` is `True`, the 4 features are stacked together.
    """
    df_static_hourly_forecast = fetch_forecast_data_as_df()[1]
    if df_static_hourly_forecast is None:
        return go.Figure()
    sources = ['tempC', 'tempF', 'precipMM', 'uvIndex']
    x = df_static_hourly_forecast['datetime']
    fig = go.Figure()
    for i, s in enumerate(sources):
        fig.add_trace(go.Scatter(x=x, y=df_static_hourly_forecast[s], mode='lines', name=s,
                                 line={'width': 2, 'color': COLORS[i]}))
    title = '24-Hour New York Weather Forecast'
    fig.update_layout(template='plotly_dark',
                      title=title,
                      plot_bgcolor='#23272c',
                      paper_bgcolor='#23272c',
                      yaxis_title='',
                      xaxis_title='Date')
    return fig


cols = ['datetime', 'sunrise', 'sunset', 'moonrise', 'moonset', 'moon_phase',
                            'moon_illumination', 'tempC', 'tempF', 'sunHour', 'uvIndex']
empty_data = {col:['']*7 for col in cols}
df_interactive_daily_forecast = pd.DataFrame(data=empty_data)
def weather_table_interactive():
    return html.Div(children=[
        dcc.Markdown('''Weather Forecast of Selected City''', className='row',style={'paddingLeft': '30%'}),
        dash_table.DataTable(
            id='table_interactive',
            columns=[{"name": i, "id": i} for i in df_interactive_daily_forecast.columns],
            data=df_interactive_daily_forecast.to_dict('records'),
            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
            style_cell={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white',
            },
        )
    ],style={'marginTop': '2rem', 'width': '800px', 'marginLeft': '200px', 'display': 'inline-block'})


df = pd.read_csv('uscities.csv')
all_state_name = sorted(df['state_name'].unique())
all_options = {state:[city for city in df[df['state_name'] == state]['city']] for state in all_state_name}
def select_city():
    """Select the state and city the user wants to enquire"""
    return html.Div(children=[
        html.Div(children=[
        html.Div(children=[
        dcc.Markdown('''Select a state'''),
        dcc.Dropdown(
            id='states-dropdown',
            options=[{'label': k, 'value': k} for k in all_options.keys()],
            value='',
            multi=False,
            style={'height': '30px', 'width': '300px'}
        )], style={'width': '300px', 'marginLeft': '90px', 'display': 'inline-block'}),

        html.Div(children=[
        dcc.Markdown('''Select a city'''),
        dcc.Dropdown(
            id='cities-dropdown',
            style={'height': '30px', 'width': '300px'}
        )], style={'width': '300px', 'align': 'right', 'marginLeft': '400px', 'display': 'inline-block'})
        ])])


def enhance_des():
    """
    Returns enhancement description in markdown
    """
    return html.Div(children=[dcc.Markdown('''
        # Explorations
        Except for weather-related business, weather also has something to do with weather itself. We
        look into air quality, more specifically, PM2.5, which is the air index that people care about
        the most nowadays. We aim to explore if the weather features including different measurements
        of temperature, sunhours and uvindex are strongly associated with air quality.
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def process_datetime(date_time):
    return date_time.strftime(format='%Y-%m-%d')

df_air = pd.read_csv('air_quality.csv')
df_air.columns = ['datetime', 'Year', 'Concentration', 'UNITS','SITE_LATITUDE', 'SITE_LONGITUDE']
df_air['datetime'] = pd.to_datetime(df_air['datetime'], format='%m/%d/%Y')
df_air['datetime'].apply(process_datetime).unique()

df_daily = pd.read_csv('daily_data.csv')
df_daily['datetime'] = pd.to_datetime(df_daily['datetime'], format='%Y/%m/%d')
df_daily['datetime'].apply(process_datetime)
dfm = df_air.merge(df_daily,how='inner',on='datetime')

def enhancement():
    return html.Div([
        html.Div([

            html.Div([
                dcc.Markdown('''Select a weather feature.'''),
                dcc.Dropdown(
                    id='xaxis-column',
                    options=[{'label': i, 'value': i} for i in ['maxtempC', 'maxtempF', 'mintempC',
                                                                'mintempF', 'avgtempC', 'avgtempF',
                                                                'totalSnow_cm', 'sunHour','uvIndex']],
                    value=''
                ),
            ],
            style={'paddingLeft': '5%','width': '48%', 'display': 'inline-block'}),
        ]),

        dcc.Graph(id='indicator-graphic',style={'marginTop': '2rem','height': '400px','paddingLeft': '5%','width': '90%'}),

        dcc.Slider(
            id='year--slider',
            min=dfm['Year'].min(),
            max=dfm['Year'].max(),
            value=dfm['Year'].max(),
            marks={str(year): str(year) for year in dfm['Year'].unique()},
            step=None
        )
    ])


def architecture_summary():
    """
    Returns the text and image of architecture summary of the project.
    """
    return html.Div(children=[
        dcc.Markdown('''
            # Project Architecture
            This project uses MongoDB as the database. All data acquired are stored in raw form to the
            database (with de-duplication). An abstract layer is built in `database.py` so all queries
            can be done via function call. For a more complicated app, the layer will also be
            responsible for schema consistency. A `plot.ly` & `dash` app is serving this web page
            through. Actions on responsive components on the page is redirected to `app.py` which will
            then update certain components on the page.  
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),

        html.Div(children=[
            html.Img(src="https://docs.google.com/drawings/d/e/2PACX-1vQNerIIsLZU2zMdRhIl3ZZkDMIt7jhE_fjZ6ZxhnJ9bKe1emPcjI92lT5L7aZRYVhJgPZ7EURN0AqRh/pub?w=670&amp;h=457",
                     className='row'),
        ], className='row', style={'textAlign': 'center'}),

        dcc.Markdown('''
        
        ''')
    ], className='row')


# Sequentially add page components to the app's layout
def dynamic_layout():
    return html.Div([
        page_header(),
        html.Hr(),
        description(),
        weather_table(),
        dcc.Graph(id='stacked-trend-graph', figure=hourly_static_stacked_trend_graph(True)),
        select_city(),
        weather_table_interactive(),
        enhance_des(),
        enhancement(),
        # dcc.Graph(id='trend-graph', figure=static_stacked_trend_graph(stack=False)),
        #dcc.Graph(id='stacked-trend-graph', figure=daily_static_stacked_trend_graph(stack=True)),
        #what_if_description(),
        #what_if_tool(),
        architecture_summary(),
    ], className='row', id='content')


# set layout to a function which updates upon reloading
app.layout = dynamic_layout

@app.callback(
    dash.dependencies.Output('cities-dropdown', 'options'),
    [dash.dependencies.Input('states-dropdown', 'value')])
def set_cities_options(selected_state):
    return [{'label': i, 'value': i} for i in all_options[selected_state]]

@app.callback(
    dash.dependencies.Output('cities-dropdown', 'value'),
    [dash.dependencies.Input('cities-dropdown', 'options')])
def set_cities_value(available_options):
    return available_options[0]['value']

@app.callback(
    dash.dependencies.Output('table_interactive', 'data'),
    [dash.dependencies.Input('cities-dropdown', "value")])
def update_table(city):
    df_interactive_daily_forecast, df_interactive_hourly_forecast = load_forecast_data(city)
    df_interactive_daily_forecast['datetime'] = df_interactive_daily_forecast['datetime'].apply(display_date)
    return df_interactive_daily_forecast.to_dict('records')

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('year--slider', 'value')])
def update_graph(xaxis_column_name, year_value):
    dff = dfm[dfm['Year'] == year_value]

    return {
        'data': [dict(
            x=dff[xaxis_column_name],
            y=dff['Concentration'],
            text=dff['datetime'],
            mode='markers',
            marker={
                'size': 10,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            }
        )],
        'layout': dict(
            xaxis={
                'title': xaxis_column_name,
            },
            yaxis={
                'title': 'PM2.5 Concentration',
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=False, port=1050, host='0.0.0.0')