import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Data Sources ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
# Updated URL provided by the user
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

# --- Data Loading and Preparation ---

@solara.memoize
def load_and_prepare_demand_data():
    """Loads population data and calculates elderly percentage."""
    
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        # Note: If utf-8 fails, try encoding="cp950"
        population_df = pd.read_csv(CSV_POPULATION_URL, encoding="utf-8") 
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

    # 1. Identify age columns (e.g., '0-4歲', '65-69歲')
    age_cols = [col for col in population_df.columns if '歲' in col]
    
    # 2. Identify elderly columns (65+) using a robust numeric check
    elderly_cols = []
    for col in age_cols:
        try:
            # Extract numbers from the start of the column name
            age_num = int(''.join(filter(str.isdigit, col.split('-')[0])))
            if age_num >= 65:
                elderly_cols.append(col)
        except ValueError:
            continue

    # 3. Calculate Totals
    population_df['總人口數'] = population_df[age_cols].sum(axis=1)
    population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)
    
    # Avoid fragmentation warning
    population_df = population_df.copy()

    # 4. Calculate Ratio
    population_df['老年人口占比'] = (population_df['65歲以上總數'] / population_df['總人口數']) * 100
    
    # 5. Merge (Ensuring keys are clean of extra spaces)
    townships_gdf['townname'] = townships_gdf['townname'].str.strip()
    population_df['地區'] = population_df['地區'].str.strip()
    
    gdf_merged = townships_gdf.merge(population_df, left_on='townname', right_on='地區', how='inner') 
    
    return gdf_merged

# --- Plotting Functions ---

def plot_elderly_ratio(data):
    """Generates the choropleth map figure."""
    # Ensure mapclassify is installed: pip install mapclassify
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds',
        scheme='quantiles', 
        edgecolor='black',
        linewidth=0.5,
        legend_kwds={'loc': 'lower right', 'title': "占比 (%)"}
    )

    plt.title('彰化縣老年人口占比分布圖 (醫療需求指標)', fontsize=15, fontweight='bold')
    plt.axis('off')
    return fig

# --- Solara Application Component ---

@solara.component
def Page():
    # Load and process data
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Error("資料載入失敗！請確認 URL 是否正確或檔案編碼是否為 UTF-8。", dense=True)
        return

    with solara.Card(title="老年人口占比 (醫療需求分佈)", elevation=2):
        # FIX: Call the plotting function inside use_memo to get the 'fig' object
        fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
        
        # Display the figure object
        solara.FigureMatplotlib(fig)

# To run: solara run your_script_name.py