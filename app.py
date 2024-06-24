import dash
from dash import dash_table, html, dcc, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc

# Leer el archivo de Excel
df = pd.read_excel('full_piv.xlsx')

# Renombramos la columna "DB" a "CLIENTE"
df.rename(columns={'DB': 'CLIENTE'}, inplace=True)

# Obtener los valores únicos de la columna 'CLIENTE' para el filtro
unique_db = df['CLIENTE'].unique()
columns = df.columns

# Filtrar las columnas numéricas
#numeric_columns = df.select_dtypes(include=['number']).columns
# filtrar solo la columna "CANTIDAD"
numeric_columns = ['CANTIDAD']

# Inicializar la aplicación Dash con Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Definir el layout de la aplicación
app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("COOP", className="display-4", style={'textAlign': 'center', 'color': '#000', 'marginBottom': '30px'}),
                        html.Hr(),
                        dbc.Nav(
                            [
                                # dbc.NavLink("Home", href="#", active="exact"),
                                # dbc.NavLink("Analytics", href="#", active="exact"),
                                # dbc.NavLink("Reports", href="#", active="exact"),
                            ],
                            vertical=True,
                            pills=True,
                        ),
                    ],
                    width=2,
                    style={'backgroundColor': '#f8f9fa', 'height': '100vh', 'padding': '20px'}
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            dbc.Col(
                                dcc.Dropdown(
                                    id='db-filter',
                                    options=[{'label': db, 'value': db} for db in unique_db],
                                    placeholder='Select a CLIENTE',
                                    multi=True,
                                    style={'marginBottom': '20px', 'fontSize': '14px'}
                                ),
                                width=12
                            )
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='groupby-columns',
                                        options=[{'label': col, 'value': col} for col in columns],
                                        placeholder='Select columns to group by',
                                        multi=True,
                                        style={'marginBottom': '20px', 'fontSize': '14px'}
                                    ),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='numeric-columns',
                                        options=[{'label': col, 'value': col} for col in numeric_columns],
                                        placeholder='Select numeric columns for metrics',
                                        multi=True,
                                        style={'marginBottom': '20px', 'fontSize': '14px'}
                                    ),
                                    width=6
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Button('Generate Grouped Table', id='groupby-button', color='dark', className='mr-2', style={'fontSize': '14px'}), width="auto"),
                                dbc.Col(dbc.Button('Reset', id='reset-button', color='secondary', style={'fontSize': '14px'}), width="auto")
                            ],
                            className="mb-4"
                        ),
                        dbc.Row(
                            [
                                dbc.Col(html.Div(id='db-months', style={'fontSize': '14px'}), width=6),
                                dbc.Col(html.Div(id='brand-db', style={'fontSize': '14px'}), width=6)
                            ],
                            className="mb-4 justify-content-center"
                        ),
                        dbc.Row(
                            dbc.Col(
                                dash_table.DataTable(
                                    id='table',
                                    columns=[{"name": i, "id": i} for i in df.columns],
                                    data=df.to_dict('records'),
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                                    page_size=20,
                                    style_header={
                                        'backgroundColor': 'black',
                                        'color': 'white',
                                        'fontSize': '12px'
                                    },
                                    style_data={
                                        'backgroundColor': 'white',
                                        'color': 'black',
                                        'fontSize': '12px'
                                    }
                                ),
                                width=12
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    dbc.Button("Download CSV", id="btn-download-csv", color='dark', className='mt-4', style={'fontSize': '14px'}),
                                    dcc.Download(id="download-csv")
                                ],
                                width=12,
                                className="text-center"
                            )
                        )
                    ],
                    width=10,
                    style={'padding': '20px'}
                )
            ]
        )
    ]
)

# Callback para actualizar la tabla y los meses únicos según el filtro seleccionado
@app.callback(
    [Output('table', 'data'),
     Output('table', 'columns'),
     Output('db-months', 'children'),
     Output('brand-db', 'children'),
     Output('db-filter', 'value'),
     Output('groupby-columns', 'value'),
     Output('numeric-columns', 'value')],
    [Input('db-filter', 'value'),
     Input('groupby-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('groupby-columns', 'value'),
     State('numeric-columns', 'value')]
)
def update_table(selected_db, groupby_clicks, reset_clicks, groupby_columns, numeric_columns):
    ctx = dash.callback_context

    # Resetear todos los valores cuando se haga clic en el botón de reset
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'reset-button.n_clicks':
        filtered_df = df
        months = df.groupby('CLIENTE')['mes'].unique().reset_index()
        brands = df.groupby('MARCA')['CLIENTE'].unique().reset_index()
        months_table = create_months_table(months)
        brands_table = create_brands_table(brands, [])
        return filtered_df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], months_table, brands_table, [], [], []

    # Si no se hace clic en reset, seguir con el flujo normal
    if selected_db is None or len(selected_db) == 0:
        filtered_df = df
        months = df.groupby('CLIENTE')['mes'].unique().reset_index()
        brands = df.groupby('MARCA')['CLIENTE'].unique().reset_index()
    else:
        filtered_df = df[df['CLIENTE'].isin(selected_db)]
        months = filtered_df.groupby('CLIENTE')['mes'].unique().reset_index()
        brands = df.groupby('MARCA')['CLIENTE'].unique().reset_index()  # Mantener todas las marcas

    if groupby_columns and numeric_columns and groupby_clicks:
        if groupby_columns and numeric_columns:
            filtered_df = filtered_df.groupby(groupby_columns)[numeric_columns].sum().reset_index()

    columns = [{"name": i, "id": i} for i in filtered_df.columns]

    # Crear la lista de meses únicos
    months_table = create_months_table(months)
    brands_table = create_brands_table(brands, selected_db)

    return filtered_df.to_dict('records'), columns, months_table, brands_table, selected_db, groupby_columns, numeric_columns

def create_months_table(months):
    month_cols = list(range(1, 13))
    table_data = []

    for _, row in months.iterrows():
        db = row['CLIENTE']
        present_months = row['mes']
        row_data = {'CLIENTE': db}
        for month in month_cols:
            #row_data[month] = '✓' if month in present_months else ''
            # en vez de palomita sera la suma de la "CANTIDAD"
            row_data[month] = df[(df['CLIENTE'] == db) & (df['mes'] == month)]['CANTIDAD'].sum() if month in present_months else ''
        table_data.append(row_data)

    months_table = dash_table.DataTable(
        columns=[{'name': 'CLIENTE', 'id': 'CLIENTE'}] + [{'name': str(month), 'id': str(month)} for month in month_cols],
        data=table_data,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'fontSize': '12px'}
    )
    return months_table

def create_brands_table(brands, selected_db):
    db_cols = df['CLIENTE'].unique() if selected_db is None or len(selected_db) == 0 else selected_db
    table_data = []

    for _, row in brands.iterrows():
        marca = row['MARCA']
        present_dbs = row['CLIENTE']
        row_data = {'MARCA': marca}
        for db in db_cols:
            #row_data[db] = '✓' if db in present_dbs else ''
            # en vez de palomita sera la suma de la "CANTIDAD"
            row_data[db] = df[(df['MARCA'] == marca) & (df['CLIENTE'] == db)]['CANTIDAD'].sum() if db in present_dbs else ''
        table_data.append(row_data)

    brands_table = dash_table.DataTable(
        columns=[{'name': 'MARCA', 'id': 'MARCA'}] + [{'name': str(db), 'id': str(db)} for db in db_cols],
        data=table_data,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'fontSize': '12px'}
    )
    return brands_table

# Callback para descargar el archivo CSV
@app.callback(
    Output("download-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    State('table', 'data')
)
def download_csv(n_clicks, table_data):
    if n_clicks is None:
        return dash.no_update

    filtered_df = pd.DataFrame(table_data)

    return dcc.send_data_frame(filtered_df.to_csv, "filtered_data.csv", index=False)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)