import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder

def create_dash_app(server: Flask):
    # Load & preprocess data
    df = pd.read_csv(r"C:\Users\vaish\Project phase I\Supermart Grocery Sales - Retail Analytics Dataset.csv")
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Order Date'])

    # KPIs
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    avg_discount = df['Discount'].mean()

    # Holt‑Winters Forecast
    df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    monthly_sales = df.groupby('YearMonth')['Sales'].sum().reset_index()
    monthly_sales['YearMonth_dt'] = pd.to_datetime(monthly_sales['YearMonth'])
    monthly_sales.sort_values('YearMonth_dt', inplace=True)
    hw_model = ExponentialSmoothing(monthly_sales['Sales'], seasonal='add', seasonal_periods=12, initialization_method="estimated")
    hw_fit = hw_model.fit()
    hw_forecast = hw_fit.forecast(3)
    hw_df = pd.DataFrame({
        'Month': pd.date_range(monthly_sales['YearMonth_dt'].iloc[-1] + pd.DateOffset(months=1), periods=3, freq='ME'),
        'Forecasted Sales': hw_forecast
    })

    # Regional / Category / Sub‑category Sales
    regional_sales = df.groupby('Region')['Sales'].sum().reset_index()
    category_sales = df.groupby('Category')['Sales'].sum().reset_index()
    subcat_sales = df.groupby(['Category','Sub Category'])['Sales'].sum().reset_index()

    # XGBoost product‑level forecast prep
    df_fc = df.copy()
    df_fc['YearMonth'] = df_fc['Order Date'].dt.to_period('M').astype(str)
    grp = df_fc.groupby(['Category','Sub Category','YearMonth'])['Sales'].sum().reset_index()
    grp['YearMonth_dt'] = pd.to_datetime(grp['YearMonth'])
    grp['Month_Ordinal'] = grp['YearMonth_dt'].map(lambda x: x.toordinal())

    le_cat = LabelEncoder().fit(grp['Category'])
    le_sub = LabelEncoder().fit(grp['Sub Category'])
    grp['Category_enc'] = le_cat.transform(grp['Category'])
    grp['Sub_enc']      = le_sub.transform(grp['Sub Category'])

    X = grp[['Category_enc','Sub_enc','Month_Ordinal']]
    y = grp['Sales']
    xgb = XGBRegressor(n_estimators=100).fit(X,y)

    last = grp['YearMonth_dt'].max()
    future_months = [last + pd.DateOffset(months=i) for i in range(1,4)]
    rows=[]
    for c in grp['Category'].unique():
        for s in grp[grp['Category']==c]['Sub Category'].unique():
            for m in future_months:
                rows.append({
                    'Category':c,'Sub Category':s,
                    'Category_enc':le_cat.transform([c])[0],
                    'Sub_enc':le_sub.transform([s])[0],
                    'Month_Ordinal':m.toordinal(),
                    'YearMonth_dt':m
                })
    future_df = pd.DataFrame(rows)
    future_df['Predicted_Sales'] = xgb.predict(future_df[['Category_enc','Sub_enc','Month_Ordinal']])

    # Build Dash
    app = dash.Dash(__name__, server=server, url_base_pathname='/category/')

    app.layout = html.Div([
        html.H1("Category-Wise Sales Dashboard", style={'textAlign':'center'}),

        # KPIs
       html.Div([
    html.Div([
        html.H4("Total Sales", style={
            "fontSize": "1rem",
            "color": "#343a40",
            "fontWeight": "500",
            "marginBottom": "8px"
        }),
        html.P(f"₹{total_sales:,.0f}", style={
            "fontSize": "1.5rem",
            "color": "#007bff",
            "fontWeight": "600",
            "margin": "0"
        })
    ], style={
        "background": "#ffffff",
        "borderRadius": "6px",
        "padding": "16px",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        "textAlign": "center",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease"
    }),

    html.Div([
        html.H4("Total Profit", style={
            "fontSize": "1rem",
            "color": "#343a40",
            "fontWeight": "500",
            "marginBottom": "8px"
        }),
        html.P(f"₹{total_profit:,.0f}", style={
            "fontSize": "1.5rem",
            "color": "#007bff",
            "fontWeight": "600",
            "margin": "0"
        })
    ], style={
        "background": "#ffffff",
        "borderRadius": "6px",
        "padding": "16px",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        "textAlign": "center",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease"
    }),

    html.Div([
        html.H4("Avg Discount", style={
            "fontSize": "1rem",
            "color": "#343a40",
            "fontWeight": "500",
            "marginBottom": "8px"
        }),
        html.P(f"{avg_discount:.2%}", style={
            "fontSize": "1.5rem",
            "color": "#007bff",
            "fontWeight": "600",
            "margin": "0"
        })
    ], style={
        "background": "#ffffff",
        "borderRadius": "6px",
        "padding": "16px",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        "textAlign": "center",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease"
    })
], style={
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
    "gap": "16px",
    "marginBottom": "32px"
})
,

        # Regional & Category charts
        html.Div([
            dcc.Graph(figure=px.pie(category_sales, names='Category', values='Sales', title="Category Sales")),
            dcc.Graph(figure=px.sunburst(subcat_sales, path=['Category','Sub Category'], values='Sales', title="Category > Sub-Category")),

        ], style={'display':'flex'}),

        # Sub‑category sunburst

        # Holt‑Winters forecast
        dcc.Graph(figure=px.line(hw_df, x='Month', y='Forecasted Sales', markers=True, title="HW Forecast Next 3 Months")),

        # Product‑level forecast
        html.Div([
            html.Label("Select Category:"),
            dcc.Dropdown(id='cat-dd', options=[{'label':c,'value':c} for c in grp['Category'].unique()]),
            html.Label("Select Sub-Category:"),
            dcc.Dropdown(id='sub-dd', disabled=True),
            dcc.Graph(id='xgb-graph'),
            html.Div(id='notify', style={'fontWeight':'bold','marginTop':'10px'})
        ], style={'border':'1px solid #ccc','padding':'10px','marginTop':'20px'})
    ])

    # enable & populate sub‑dropdown
    @app.callback(
        [Output('sub-dd','options'), Output('sub-dd','disabled')],
        Input('cat-dd','value')
    )
    def set_sub_options(cat):
        if not cat:
            return [], True
        subs = grp[grp['Category']==cat]['Sub Category'].unique()
        return ([{'label':s,'value':s} for s in subs], False)

    # update XGB graph & notification
    @app.callback(
        Output('xgb-graph','figure'),
        Output('notify','children'),
        Input('cat-dd','value'),
        Input('sub-dd','value')
    )
    def update_xgb(cat, sub):
        if not cat or not sub:
            return {}, ""
        d = future_df[(future_df['Category']==cat)&(future_df['Sub Category']==sub)]
        fig = go.Figure(go.Bar(x=d['YearMonth_dt'], y=d['Predicted_Sales']))
        fig.update_layout(title=f"Predicted Sales for {cat} > {sub}", xaxis_title="Month", yaxis_title="₹ Sales")
        units = int(d['Predicted_Sales'].sum()/100)  # assume ₹100 per unit
        msg = f"Stock at least {units} units of {sub} for next 3 months."
        return fig, msg

    return app

# run on Flask
if __name__=='__main__':
    server = Flask(__name__)
    dash_app = create_dash_app(server)
    server.run(debug=True)
