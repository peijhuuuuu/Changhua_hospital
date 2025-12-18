import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 資料來源 (假設與 supply.py 使用相同的 GeoJSON) ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 
# 假設這是您的 CSV 人口資料 URL

# --- 數據載入和處理 ---

@solara.memoize
def load_and_prepare_demand_data():
    """載入人口資料並計算老年人口佔比。"""
    
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
    except Exception:
        return None

    # 讀取人口資料 (假設編碼和格式正確)
    population_df = pd.read_csv(CSV_POPULATION_URL, encoding="utf-8") 
    
    # 假設欄位名稱和資料清理邏輯如下：
    
    # 選擇所有年齡欄位 (您需要根據您的 CSV 實際欄位名稱調整)
    age_cols = [col for col in population_df.columns if '歲' in col]
    
    # 選擇 65 歲以上欄位 (您需要根據您的 CSV 實際欄位名稱調整)
    elderly_cols = [col for col in age_cols if int(col.split('-')[0].replace('歲', '')) >= 65]

    # 計算總人口數和老年人口數 (優化：使用 copy() 消除 PerformanceWarning)
    population_df['總人口數'] = population_df[age_cols].sum(axis=1)
    population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)
    
    # 消除碎片化警告
    population_df = population_df.copy()

    # 計算老年人口占比
    population_df['老年人口占比'] = (population_df['65歲以上總數'] / population_df['總人口數']) * 100
    
    # 假設合併鍵是 'townname' 對 '鄉鎮' 或 '地區'
    gdf_merged = townships_gdf.merge(population_df, left_on='townname', right_on='地區', how='inner') 
    
    return gdf_merged

# --- 繪圖函數 ---

def plot_elderly_ratio(data):
    """繪製老年人口占比圖 (需要 mapclassify)"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds', # 使用紅色系漸層
        scheme='quantiles', # 這裡需要 mapclassify
        figsize=(10, 10),
        edgecolor='black',
        linewidth=0.5
    )

    plt.title('彰化縣老年人口占比分布圖 (醫療需求指標)', fontsize=15)
    plt.axis('off')
    return fig

# --- Solara 應用程式組件 ---

@solara.component
def Page():
    # 載入數據
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Warning("需求端資料載入失敗，請檢查 URL 或 GeoJSON。", dense=True)
        return

    with solara.Card(title="老年人口占比 (醫療需求分佈)", elevation=2):
        # 修正為 solara.FigureMatplotlib，並使用具名參數 data=
        solara.FigureMatplotlib(plot_elderly_ratio, data=gdf_merged)