import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
from flask import Flask
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Flask app to manage routes
server = Flask(__name__)

def create_dash_app(server):
    # Load the dataset
    df = pd.read_csv(r"C:\Users\vaish\Project phase I\Supermart Grocery Sales - Retail Analytics Dataset.csv")

    # Convert 'Order Date' to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')

    # Aggregate sales over time
    sales_over_time = df.groupby('Order Date')['Sales'].sum().reset_index()

    # Aggregate sales by sub-category
    sales_by_subcategory = df.groupby('Sub Category')['Sales'].sum().reset_index()

    # Aggregate sales by discount
    sales_by_discount = df.groupby('Discount')['Sales'].sum().reset_index()

    # Aggregate sales by city
    sales_by_city = df.groupby('City')['Sales'].sum().reset_index()

    # Initialize the Dash app
    app = dash.Dash(__name__, server=server, url_base_pathname='/geo_forecast/')  # '/' path for general dashboard

    # Demand Forecast: Using Holt-Winters Exponential Smoothing
    model = ExponentialSmoothing(sales_over_time['Sales'], trend='add', seasonal='add', seasonal_periods=12)
    forecast = model.fit().forecast(12)
    forecast_dates = pd.date_range(start=sales_over_time['Order Date'].max(), periods=13, freq='M')[1:]

    # Regional Sales Map (using Plotly Express)
    regional_sales_map = px.choropleth(df, locations="Region", color="Sales", hover_name="Region", color_continuous_scale="Viridis")

    # Define the layout for sales dashboard
    app.layout = html.Div([
        html.H1("Supermart Sales Dashboard", style={'textAlign': 'center'}),

        # Sales Over Time
        dcc.Graph(
            id='sales-over-time',
            figure={
                'data': [go.Scatter(x=sales_over_time['Order Date'], y=sales_over_time['Sales'], mode='lines')],
                'layout': go.Layout(title='Sales Over Time')
            }
        ),

        # Sales by Sub-Category
        dcc.Graph(
            id='sales-by-subcategory',
            figure={
                'data': [go.Bar(x=sales_by_subcategory['Sub Category'], y=sales_by_subcategory['Sales'])],
                'layout': go.Layout(title='Sales by Sub-Category')
            }
        ),

        # Sales by Discount
        dcc.Graph(
            id='sales-by-discount',
            figure={
                'data': [go.Scatter(x=sales_by_discount['Discount'], y=sales_by_discount['Sales'], mode='lines')],
                'layout': go.Layout(title='Sales by Discount')
            }
        ),

        # Demand Forecast
        dcc.Graph(
            id='demand-forecast',
            figure={
                'data': [
                    go.Scatter(x=sales_over_time['Order Date'], y=sales_over_time['Sales'], mode='lines', name='Historical Sales'),
                    go.Scatter(x=forecast_dates, y=forecast, mode='lines', name='Forecast')
                ],
                'layout': go.Layout(title='Sales Demand Forecast')
            }
        ),

        # Regional Sales Map
        dcc.Graph(
            id='regional-sales-map',
            figure=regional_sales_map
        ),

        # City Performance (Bar chart comparing cities)
        dcc.Graph(
            id='city-performance',
            figure={
                'data': [go.Bar(x=sales_by_city['City'], y=sales_by_city['Sales'])],
                'layout': go.Layout(title='City Performance')
            }
        ),

        # Inventory Recommendations (based on sales forecast)
       # Inventory Recommendations (based on sales forecast)
        html.Div([
            html.H3("Inventory Recommendations"),
            html.P("Based on the forecasted sales, we recommend the following inventory levels for the next 3 months:"),
            html.Ul([
                html.Li(f"Product {i+1}: {round(forecast.iloc[i]*1.1)} units (10% buffer)") for i in range(len(forecast))
            ])
        ]),


        # What-If Scenarios (Different discount strategies)
        html.Div([
            html.H3("What-If Scenarios"),
            html.P("Simulating sales with different discount rates:"),
            html.Div([
                dcc.Slider(
                    id='discount-slider',
                    min=0,
                    max=50,
                    step=5,
                    value=10,
                    marks={i: f"{i}%" for i in range(0, 51, 5)},
                ),
                html.Div(id='discount-output')
            ])
        ])
    ])

    return app
