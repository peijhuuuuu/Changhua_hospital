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
    """Loads population data using a more robust request method."""
    try:
        # 1. Load GeoJSON
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        
        # 2. Fetch CSV using requests (more reliable than pandas directly)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(CSV_POPULATION_URL, headers=headers)
        
        if response.status_code == 404:
            print("DEBUG: GitHub returned 404. Check if repo is PUBLIC.")
            return "404_ERROR"
        
        # Convert response content to a pandas DataFrame
        # Trying UTF-8, falling back to CP950
        try:
            csv_data = response.content.decode('utf-8')
        except UnicodeDecodeError:
            csv_data = response.content.decode('cp950')
            
        population_df = pd.read_csv(io.StringIO(csv_data))
        
    except Exception as e:
        print(f"DEBUG: Critical Error: {e}")
        return None

    # --- Data Processing (Same as before) ---
    age_cols = [col for col in population_df.columns if '歲' in col]
    elderly_cols = []
    for col in age_cols:
        try:
            age_num = int(''.join(filter(str.isdigit, col.split('-')[0])))
            if age_num >= 65:
                elderly_cols.append(col)
        except:
            continue

    if not age_cols: return None

    population_df['總人口數'] = population_df[age_cols].sum(axis=1)
    population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)
    population_df['老年人口占比'] = (population_df['65歲以上總數'] / population_df['總人口數']) * 100
    
    townships_gdf['townname'] = townships_gdf['townname'].str.strip()
    population_df['地區'] = population_df['地區'].str.strip()
    
    return townships_gdf.merge(population_df, left_on='townname', right_on='地區', how='inner')

def plot_elderly_ratio(data):
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

    # Specific error handling for the 404 issue
    if gdf_merged == "404_ERROR":
        solara.Error("⚠️ 伺服器回傳 404：找不到檔案", dense=True)
        with solara.Card("解決步驟"):
            solara.Markdown(f"""
            1. **檢查隱私設定**：請確認 GitHub 儲存庫 `Changhua_hospital` 是 **Public (公開)**。如果是 Private，程式碼無法讀取。
            2. **確認檔案名稱**：請確認 GitHub 上的檔名完全是 `age_population.csv` (大小寫需一致)。
            """)
        return

    if gdf_merged is None or (isinstance(gdf_merged, pd.DataFrame) and gdf_merged.empty):
        solara.Error("資料讀取失敗或合併後無資料。", dense=True)
        return

    with solara.Card(title="老年人口占比 (醫療需求分佈)", elevation=2):
        fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
        solara.FigureMatplotlib(fig)