import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# --- Data Sources ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

@solara.memoize
def load_and_prepare_demand_data():
    """Loads population data and ensures all age columns are numeric."""
    try:
        # 1. Load GeoJSON
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        
        # 2. Fetch CSV (using requests for better stability)
        response = requests.get(CSV_POPULATION_URL)
        if response.status_code != 200:
            return None
            
        try:
            decoded_csv = response.content.decode('utf-8')
        except UnicodeDecodeError:
            decoded_csv = response.content.decode('cp950')
            
        population_df = pd.read_csv(io.StringIO(decoded_csv))
        
        # 3. Clean and Convert age columns to numeric
        age_cols = [col for col in population_df.columns if '歲' in col]
        
        for col in age_cols:
            # Remove commas (if any) and convert to numeric. 
            # errors='coerce' turns non-numeric entries into NaN, then we fill with 0.
            population_df[col] = pd.to_numeric(
                population_df[col].astype(str).str.replace(',', ''), 
                errors='coerce'
            ).fillna(0)

        # 4. Identify elderly columns (65+)
        elderly_cols = []
        for col in age_cols:
            try:
                age_num = int(''.join(filter(str.isdigit, col.split('-')[0])))
                if age_num >= 65:
                    elderly_cols.append(col)
            except:
                continue

        # 5. Calculations (Now it won't crash!)
        population_df['總人口數'] = population_df[age_cols].sum(axis=1)
        population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)
        
        # Avoid fragmentation
        population_df = population_df.copy()
        
        # Calculate Percentage (Handle 0 population case)
        population_df['老年人口占比'] = (population_df['65歲以上總數'] / population_df['總人口數']).fillna(0) * 100
        
        # 6. Merge
        townships_gdf['townname'] = townships_gdf['townname'].str.strip()
        population_df['地區'] = population_df['地區'].str.strip()
        
        return townships_gdf.merge(population_df, left_on='townname', right_on='地區', how='inner')

    except Exception as e:
        print(f"DEBUG Error: {e}")
        return None

def plot_elderly_ratio(data):
    # Ensure mapclassify is installed for 'quantiles'
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
    plt.title('彰化縣老年人口占比分布圖', fontsize=15, fontweight='bold')
    plt.axis('off')
    return fig

@solara.component
def Page():
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or (isinstance(gdf_merged, pd.DataFrame) and gdf_merged.empty):
        solara.Error("資料載入或解析失敗。請確認 CSV 格式正確且欄位名稱包含 '地區' 與 '歲'。", dense=True)
        return

    with solara.Card(title="老年人口占比 (醫療需求分佈)", elevation=2):
        # Generate the figure object using use_memo
        fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
        solara.FigureMatplotlib(fig)