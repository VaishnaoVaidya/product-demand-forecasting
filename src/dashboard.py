import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from flask import Flask
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt

def create_dash_app(server: Flask):
    # Load dataset
    df = pd.read_csv(r"C:\Users\vaish\Project phase I\Supermart Grocery Sales - Retail Analytics Dataset.csv")

    # Clean column names
    df.columns = df.columns.str.strip()

    # Group sales by city
    city_sales_distribution = df.groupby("City")["Sales"].sum().reset_index()


    # Check if 'Order Date' column exists
    if "Order Date" not in df.columns:
        raise KeyError("The dataset does not contain an 'Order Date' column. Check column names: " + str(df.columns))

    df["Order Date"] = pd.to_datetime(df["Order Date"], format="mixed", dayfirst=False, errors="coerce")

    # Aggregate sales data
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order ID"].nunique()  # Unique number of orders
    aov = total_sales / total_orders  # Calculate Average Order Value (AOV)

    # Group by Order Date for sales trend
    daily_sales = df.groupby("Order Date")["Sales"].sum().reset_index()

    # Group by Category for sales distribution
    category_sales = df.groupby("Category")["Sales"].sum().reset_index()

    # Group by Customer Name for customer distribution
    customer_distribution = df.groupby("Customer Name")["Sales"].sum().reset_index()

    # Region-wise sales data
    regions = ["Central", "East", "South", "West"]
    sales_data = np.array([  # Sample data
        [109543.91, 128017.14, 126587.35, 111517.05, 131699.53, 109261.91, 140179.95],  # Central
        [153741.06, 144498.17, 164465.08, 154932.01, 141292.78, 155569.22, 159847.26],  # East
        [89102.07,  84058.78,  93728.18,  94823.55,  92961.26,  73909.18,  94979.87],   # South
        [176134.02, 169031.67, 182576.61, 167890.03, 164446.81, 158753.70, 173171.77]   # West
    ])
    total_sales_per_region = sales_data.sum(axis=1)

    # Sales Forecasting using Exponential Smoothing (Holt-Winters)
    df.set_index('Order Date', inplace=True)
    df_monthly_sales = df.resample('M').sum()

    # Apply Exponential Smoothing Model (Holt-Winters) for forecasting
    model = ExponentialSmoothing(df_monthly_sales['Sales'], trend='add', seasonal='add', seasonal_periods=12)
    model_fit = model.fit()

    # Forecast sales for the next 3 months (2025)
    forecast = model_fit.forecast(steps=3)

    # Create forecast dates (for 2025)
    forecast_dates = pd.date_range(df_monthly_sales.index[-1] + pd.Timedelta(days=1), periods=3, freq='M')
    forecast_df = pd.DataFrame({'Forecasted Sales': forecast}, index=forecast_dates)

    # Create Dash app
    dash_app = dash.Dash(
        __name__,
        server=server,  # Pass the Flask server to the Dash app
        routes_pathname_prefix="/dashboard/",
        external_stylesheets=['/static/css/styles.css']  # Link to external CSS
    )

    dash_app.layout = html.Div(className="container", children=[ 
        html.H1("Product Demand Forecast Dashboard", className="header"),

        # KPI display section
        html.Div([  
            html.Div([
                html.H3("Total Sales"),
                html.P(f"Rs{total_sales:,.2f}")
            ], className="kpi-box"),

            html.Div([
                html.H3("Total Profit"),
                html.P(f"Rs{total_profit:,.2f}")
            ], className="kpi-box"),

            html.Div([
                html.H3("Average Order Value (AOV)"),
                html.P(f"Rs{aov:,.2f}")
            ], className="kpi-box"),
        ], className="kpi-row"),

        # First row with 2 charts (Category-wise sales and Customer distribution)
        html.Div([ 
            html.Div([  # Category-wise sales bar chart
                html.H3("Category-wise Sales Distribution", className="chart-title"), 
                dcc.Graph(
                    id="category-sales",
                    figure={
                        "data": [
                            go.Bar(
                                x=category_sales["Category"],
                                y=category_sales["Sales"],
                                name="Sales by Category"
                            )
                        ],
                        "layout": go.Layout(title="", xaxis_title="Category", yaxis_title="Sales")
                    }
                )
            ], className="chart-box"),


             # Third row with Region-wise Sales Pie Chart
        html.Div([ 
                html.H3("Total Sales Distribution by Region", className="chart-title"),
                dcc.Graph(
                    id="region-sales-pie",
                    figure={
                        "data": [
                            go.Pie(
                                labels=regions,
                                values=total_sales_per_region,
                                name="Region Sales",
                                marker=dict(colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"])
                            )
                        ],
                        "layout": go.Layout(title="")
                    }
                )
            ], className="chart-box"),
        ], className="chart-row"),

        # Second row with Sales Trend chart
        html.Div([ 
            html.Div([  # Sales trend line chart
                dcc.Graph(
                    id="sales-trend",
                    figure={
                        "data": [
                            go.Scatter(
                                x=daily_sales["Order Date"],
                                y=daily_sales["Sales"],
                                mode="lines+markers",
                                name="Sales"
                            )
                        ],
                        "layout": go.Layout(title="Daily Sales Trend", xaxis_title="Order Date", yaxis_title="Sales")
                    }
                )
            ], className="chart-box-next"),
        ], className="chart-row"),

       

        # Fourth row for Forecasted Sales (Next 3 months)
        html.Div([ 
            html.Div([ 
                html.H3("Sales Forecast for the Next 3 Months", className="chart-title"),
                dcc.Graph(
                    id="forecasted-sales",
                    figure={
                        "data": [
                            go.Scatter(
                                x=df_monthly_sales.index,
                                y=df_monthly_sales['Sales'],
                                mode="lines+markers",
                                name="Historical Sales"
                            ),
                            go.Scatter(
                                x=forecast_df.index,
                                y=forecast_df['Forecasted Sales'],
                                mode="lines+markers",
                                name="Forecasted Sales",
                                line=dict(dash='dash')
                            )
                        ],
                        "layout": go.Layout(title="Sales Forecast for the Next 3 Months", xaxis_title="Date", yaxis_title="Sales")
                    }
                )
            ], className="chart-box"),

        # Fifth row for 2025 Predicted Sales (First 3 Months)
        html.Div([
                html.H3("Predicted Sales for the First 3 Months of 2025", className="chart-title"),
                dcc.Graph(
                    id="sales-forecast-2025",
                    figure={
                        "data": [
                            go.Scatter(
                                x=forecast_df.index,
                                y=forecast_df['Forecasted Sales'],
                                mode="lines+markers",
                                name="2025 Predicted Sales",
                                line=dict(color='rgb(255, 99, 71)', dash='dot')
                            )
                        ],
                        "layout": go.Layout(title="Predicted Sales for 2025 (First 3 Months)", xaxis_title="Date", yaxis_title="Sales")
                    }
                )
            ], className="chart-box"),
        ], className="chart-row"),

         html.Div([
        html.H3("Sales Distribution by City", className="chart-title"),
        dcc.Graph(
            figure={
                "data": [
                    go.Pie(
                        labels=city_sales_distribution["City"],
                        values=city_sales_distribution["Sales"],
                        name="City Sales",
                        hole=0.3  # Donut chart style
                    )
                ],
                "layout": go.Layout(title="Sales by City")
            }
        )
    ], className="chart-box")
        
    ])

    return dash_app
