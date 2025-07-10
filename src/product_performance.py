import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import dash_bootstrap_components as dbc

# Sample DataFrame for illustration (replace with actual data)
df = pd.read_csv('sales_data.csv')

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout for Product Profitability, Inventory Turnover, Product Affinity, and Discount Effectiveness
app.layout = html.Div([
    # Product Profitability (Scatter Plot)
    dcc.Graph(
        id='product-profitability',
        figure={
            'data': [go.Scatter(x=df['sales'], y=df['profit'], mode='markers')],
            'layout': go.Layout(title='Product Profitability')
        }
    ),

    # Inventory Turnover (Bar Chart)
    dcc.Graph(
        id='inventory-turnover',
        figure={
            'data': [go.Bar(x=df['product'], y=df['inventory_turnover'])],
            'layout': go.Layout(title='Inventory Turnover')
        }
    ),

    # Product Affinity (Bubble Chart)
    dcc.Graph(
        id='product-affinity',
        figure={
            'data': [go.Scatter(x=df['product_1'], y=df['product_2'], mode='markers', marker=dict(size=20))],
            'layout': go.Layout(title='Product Affinity')
        }
    ),

    # Discount Effectiveness (Line Chart)
    dcc.Graph(
        id='discount-effectiveness',
        figure={
            'data': [go.Scatter(x=df['discount'], y=df['sales'], mode='lines')],
            'layout': go.Layout(title='Discount Effectiveness')
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
