import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
import dash_bootstrap_components as dbc



def create_dash_app(server: Flask):

    # Sample DataFrame (replace this with your full Supermart dataset)
    df = pd.read_csv(r"C:\Users\vaish\Project phase I\Supermart Grocery Sales - Retail Analytics Dataset.csv")
    # Fix datetime parsing
    df["Order Date"] = pd.to_datetime(df["Order Date"], infer_datetime_format=True, errors="coerce")
    df = df.dropna(subset=["Order Date"])
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.month
    df["Weekday"] = df["Order Date"].dt.day_name()

        
    # Sample accuracy data
    accuracy_percent_data = pd.DataFrame({
        'Model': ['SARIMA', 'LSTM', 'XGBoost'],
        'MAPE (%)': [18.45, 15.84, 13.23]  # Replace with real values
    })

    # Create bar chart using Plotly Express
    fig = px.bar(
        accuracy_percent_data,
        x='Model',
        y='MAPE (%)',
        title='Sales Prediction Accuracy Comparison (Lower MAPE% Indicates Better Accuracy)',
        color='Model',
        color_discrete_sequence=px.colors.sequential.Blues,
        text='MAPE (%)'
    )

    fig.update_layout(
        yaxis_title='Mean Absolute Percentage Error (MAPE%)',
        xaxis_title='Model',
        title_font_size=16,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        margin=dict(t=50, b=20),
        height=400
    )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_yaxes(range=[0, max(accuracy_percent_data['MAPE (%)']) + 5], showgrid=True, gridwidth=1, gridcolor='LightGray')

    metrics = ['MAE', 'RMSE', 'MAPE', 'R2 Score', 'Accuracy']
    values = [85, 90, 88, 92, 95]  # hypothetical success rates or percentages

    # Create bar chart using Plotly Graph Objects
    bar_chart = go.Figure(
        data=[
            go.Bar(
                x=metrics,
                y=values,
                text=[f'{v}%' for v in values],
                textposition='outside',
                marker=dict(color='mediumseagreen', line=dict(color='black', width=1))
            )
        ]
    )

    # Customize the layout
    bar_chart.update_layout(
        title=dict(
            text='Performance Metrics of Product Demand Forecast Model',
            x=0.5,
            font=dict(size=20, family='Arial', color='black')
        ),
        xaxis_title='Evaluation Metrics',
        yaxis_title='Success Rate (%)',
        yaxis=dict(range=[80, 100], gridcolor='lightgray', tickmode='linear', dtick=2),
        plot_bgcolor='white',
        bargap=0.4
    )


    # Initialize Dash app with Bootstrap
    app = dash.Dash(__name__, server=server, url_base_pathname='/sales/')  # '/' path for general dashboard

    # -------------------- Layout --------------------
    app.layout = dbc.Container([
    html.H2("📊 Supermart Grocery Sales Dashboard", className="my-4 text-center fw-bold"),

    # Filter Row
    dbc.Row([
        dbc.Col([
            html.Label("Category", className="fw-bold"),
            dcc.Dropdown(
                id="category-filter",
                options=[{"label": c, "value": c} for c in sorted(df["Category"].unique())],
                placeholder="Select Category"
            )
        ], md=2),
        dbc.Col([
            html.Label("City", className="fw-bold"),
            dcc.Dropdown(
                id="city-filter",
                options=[{"label": c, "value": c} for c in sorted(df["City"].unique())],
                placeholder="Select City"
            )
        ], md=2),
        dbc.Col([
            html.Label("Year", className="fw-bold"),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": y, "value": y} for y in sorted(df["Year"].unique())],
                placeholder="Select Year"
            )
        ], md=2),
        dbc.Col([
            html.Label("Month", className="fw-bold"),
            dcc.Dropdown(
                id="month-filter",
                options=[{"label": pd.to_datetime(str(m), format="%m").strftime("%B"), "value": m} for m in sorted(df["Month"].unique())],
                placeholder="Select Month"
            )
        ], md=2),
        dbc.Col([
            html.Label("Discount Range", className="fw-bold"),
            dcc.RangeSlider(
                id="discount-filter",
                min=0, max=1, step=0.05,
                value=[0, 1],
                marks={round(i * 0.1, 1): f"{int(i*10)}%" for i in range(11)}
            )
        ], md=4),
    ], className="mb-4"),

    html.Hr(),

    # Dynamic Graph Output (Filtered Visuals)
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading",
                children=[html.Div(id="filtered-content")],
                type="circle"
            )
        ])
    ]),

    html.Hr(),

    # Static Accuracy Chart
   # Inside your layout, just before or alongside the accuracy chart:

dbc.Row([
    dbc.Col([
        html.Div([
            html.H5("Model Accuracy (MAPE %)", className="fw-bold mb-3"),
            html.Ul([
                html.Li("📉 SARIMA  : 18.45%", style={"fontSize": "18px"}),
                html.Li("📊 XGBoost : 13.23%", style={"fontSize": "18px"}),
                html.Li("🔁 LSTM    : 15.84%", style={"fontSize": "18px"}),
            ], style={"listStyleType": "none", "paddingLeft": 0}),
        ], className="p-3 border rounded bg-light")
    ], md=6),

    dbc.Col([
        html.Label("Model Accuracy Comparison Chart", className="fw-bold"),
        dcc.Graph(figure=fig, id="accuracy-chart")
    ], md=6),

    dbc.Row([
        dbc.Col(html.H2("Product Demand Forecast Model Performance", className="text-center mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=bar_chart), width=12)
    ])

])

], fluid=True)



    # -------------------- Callback --------------------
    @app.callback(
        Output("filtered-content", "children"),
        Input("category-filter", "value"),
        Input("city-filter", "value"),
        Input("year-filter", "value"),
        Input("month-filter", "value"),
        Input("discount-filter", "value"),
    )
    def update_dashboard(category, city, year, month, discount_range):
        # Filtering logic
        filtered_df = df.copy()
        if category:
            filtered_df = filtered_df[filtered_df["Category"] == category]
        if city:
            filtered_df = filtered_df[filtered_df["City"] == city]
        if year:
            filtered_df = filtered_df[filtered_df["Year"] == year]
        if month:
            filtered_df = filtered_df[filtered_df["Month"] == month]
        if discount_range:
            filtered_df = filtered_df[
                (filtered_df["Discount"] >= discount_range[0]) &
                (filtered_df["Discount"] <= discount_range[1])
            ]

        # ---- Visualization 1: Sales by Sub-Category (Bar Chart) ----
        sub_sales = filtered_df.groupby("Sub Category")["Sales"].sum().sort_values().reset_index()
        fig_sub = px.bar(sub_sales, x="Sales", y="Sub Category", orientation="h",
                        color="Sales", title="Sales by Sub-Category",
                        color_continuous_scale="Tealgrn")

        # ---- Visualization 2: Discount vs Profit (Scatter) ----
        fig_scatter = px.scatter(filtered_df, x="Discount", y="Profit",
                                size="Sales", color="Category",
                                title="Discount Impact on Profit",
                                hover_data=["City", "Sub Category"])

        # ---- Visualization 3: Sales Heatmap (Weekday vs Month) ----
        heatmap_data = filtered_df.groupby(["Weekday", "Month"])["Sales"].sum().unstack(fill_value=0)
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[pd.to_datetime(str(m), format="%m").strftime("%b") for m in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale="YlGnBu"
        ))
        fig_heatmap.update_layout(title="Sales Heatmap: Weekday vs Month", xaxis_title="Month", yaxis_title="Weekday")

        # ---- Return Updated Charts ----
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_sub), md=4),
            dbc.Col(dcc.Graph(figure=fig_scatter), md=4),
            dbc.Col(dcc.Graph(figure=fig_heatmap), md=4),
        ], className="g-4")

