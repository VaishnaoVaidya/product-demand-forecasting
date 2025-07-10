import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import dash_bootstrap_components as dbc

def create_dash_app(server):

    # Load the dataset
    df = pd.read_csv(r"C:\Users\vaish\Project phase I\Supermart Grocery Sales - Retail Analytics Dataset.csv")

    # Display column names to verify
    print(df.columns)

    # Replace '-' with '/' in 'Order Date' and convert to datetime
    df['Order Date'] = df['Order Date'].str.replace('-', '/')
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%Y')

    # Calculate Recency: Days since the last purchase for each customer
    df['recency'] = (df['Order Date'].max() - df['Order Date']).dt.days

    # Calculate Frequency: Number of purchases per customer
    df['frequency'] = df.groupby('Customer Name')['Order ID'].transform('count')

    # Calculate Monetary: Total spending per customer
    df['total_spent'] = df.groupby('Customer Name')['Sales'].transform('sum')

    # Calculate Customer Lifetime Value (CLV) for illustration
    df['clv'] = df['total_spent'] * df['frequency']  # Simple CLV calculation

    # Calculate Repeat Purchase Frequency
    df['repeat_purchase_frequency'] = df.groupby('Customer Name')['Order ID'].transform('count')

    # Create monetary bins (5 edges, resulting in 5 labels)
    monetary_bins = [0, 50, 100, 200, 500, float('inf')]  # Example bin edges
    df['monetary_segment'] = pd.cut(df['total_spent'], bins=monetary_bins, labels=['Very Low Spender', 'Low Spender', 'Medium Spender', 'High Spender', 'Very High Spender'])

    # Create the Dash app
    app = dash.Dash(__name__, server=server, url_base_pathname='/customer/')  # Mount Dash at /customer/

    # Layout for RFM Analysis, Top Customers, CLV, and Repeat Purchase Patterns
    app.layout = html.Div([
        # RFM Analysis (Recency, Frequency)
        dcc.Graph(
            id='rfm-analysis',
            figure={
                'data': [go.Scatter(x=df['recency'], y=df['frequency'], mode='markers')],
                'layout': go.Layout(title='Recency Frequency Monetary Analysis Analysis')
            }
        ),

        # Top Customers (Table)
        html.Div([
            dbc.Table.from_dataframe(
                df[['Customer Name', 'total_spent']].drop_duplicates().nlargest(10, 'total_spent'),
                striped=True,
                bordered=True,
                hover=True
            )
        ]),

        # Customer Lifetime Value (CLV)
        dcc.Graph(
            id='clv',
            figure={
                'data': [go.Scatter(x=df['Customer Name'], y=df['clv'], mode='lines')],
                'layout': go.Layout(title='Customer Lifetime Value (CLV)')
            }
        ),

        # Repeat Purchase Patterns (Bar Chart)
        dcc.Graph(
            id='repeat-purchase',
            figure={
                'data': [go.Bar(x=df['Customer Name'], y=df['repeat_purchase_frequency'])],
                'layout': go.Layout(title='Repeat Purchase Patterns')
            }
        )
    ])

    return app
