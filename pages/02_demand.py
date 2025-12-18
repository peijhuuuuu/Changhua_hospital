import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# --- 1. 資料路徑 (對應 Colab 的 URL 版本) ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

@solara.memoize
def load_and_prepare_demand_data():
    """同步 Colab 邏輯：清理資料、處理數字逗號、男女加總、計算占比。"""
    try:
        # 讀取地圖
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        
        # 讀取 CSV (處理編碼)
        response = requests.get(CSV_POPULATION_URL)
        if response.status_code != 200:
            return None
        try:
            # 優先嘗試 Big5 (Colab 使用的編碼)
            decoded_csv = response.content.decode('big5')
        except:
            # 如果失敗則嘗試 UTF-8
            decoded_csv = response.content.decode('utf-8', errors='ignore')
            
        df = pd.read_csv(io.StringIO(decoded_csv))
        
        # --- [Colab 同步邏輯]：定義欄位 ---
        TOWN_COL_CSV = '區域別'
        TOWN_COL_GEO = 'townname' # 對應地圖檔的欄位名稱
        
        # 定義所有年齡層欄位
        age_cols = [col for col in df.columns if '(人數)' in col]
        
        # --- [Colab 同步邏輯]：清除逗號並轉數值 ---
        for col in age_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '', regex=False).str.strip(), 
                errors='coerce'
            ).fillna(0)

        # --- [Colab 同步邏輯]：按「區域別」分組加總 (合併男、女資料) ---
        # 這一步最關鍵，確保每個鄉鎮只有一列總計資料
        population_summary = df.groupby(TOWN_COL_CSV)[age_cols].sum().reset_index()

        # --- [Colab 同步邏輯]：篩選 65 歲以上欄位 ---
        elderly_cols = [col for col in age_cols if int(col.split('歲')[0]) >= 65]

        # --- [Colab 同步邏輯]：計算總人口與占比 ---
        population_summary['總人口數'] = population_summary[age_cols].sum(axis=1)
        population_summary['65歲以上總數'] = population_summary[elderly_cols].sum(axis=1)
        
        # 計算最終占比 (%)
        population_summary['老年人口占比'] = (
            population_summary['65歲以上總數'] / population_summary['總人口數']
        ) * 100
        
        # --- [Colab 同步邏輯]：數據合併 (Merge) ---
        # 統一將 CSV 的「區域別」更名為與地圖一致的「townname」
        population_summary = population_summary.rename(columns={TOWN_COL_CSV: TOWN_COL_GEO})
        
        # 清除名稱空白，確保合併成功
        townships_gdf[TOWN_COL_GEO] = townships_gdf[TOWN_COL_GEO].str.strip()
        population_summary[TOWN_COL_GEO] = population_summary[TOWN_COL_GEO].str.strip()
        
        # 執行合併
        gdf_merged = townships_gdf.merge(population_summary, on=TOWN_COL_GEO, how='inner')
        
        return gdf_merged

    except Exception as e:
        print(f"解析失敗: {e}")
        return None

def plot_elderly_ratio(data):
    """繪製面量圖 (同步 Colab 的 Reds 漸層與分級邏輯)"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # 同步 Colab 參數：scheme='Quantiles', k=5, cmap='Reds'
    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds',
        scheme='Quantiles', # 分五級
        k=5,
        edgecolor='0.8',
        linewidth=0.8,
        legend_kwds={'loc': 'lower right', 'title': "需求熱區 (占比 %)"}
    )

    plt.title('彰化縣老年人口占比分佈圖', fontsize=16, fontweight='bold')
    plt.axis('off')
    return fig

@solara.component
def Page():
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Error("資料讀取或合併失敗，請確認 CSV 是否包含『區域別』及『(人數)』欄位。", dense=True)
        return

    with solara.Card(title="彰化縣人口需求熱區 (同步 Colab 邏輯)", elevation=4):
        with solara.Column():
            fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
            solara.FigureMatplotlib(fig)
            
            with solara.Details("查看詳細人口統計表"):
                # 顯示表格方便檢查數據是否正確
                solara.DataFrame(gdf_merged[['townname', '總人口數', '65歲以上總數', '老年人口占比']].sort_values('老年人口占比', ascending=False))