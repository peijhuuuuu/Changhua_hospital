import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# --- 資料來源 ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

@solara.memoize
def load_and_prepare_demand_data():
    """載入人口資料並處理欄位名稱與資料類型。"""
    try:
        # 1. 讀取地圖
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        
        # 2. 抓取 CSV (使用 requests 確保穩定性)
        response = requests.get(CSV_POPULATION_URL)
        if response.status_code != 200:
            return None
            
        try:
            decoded_csv = response.content.decode('utf-8')
        except UnicodeDecodeError:
            decoded_csv = response.content.decode('cp950')
            
        df = pd.read_csv(io.StringIO(decoded_csv))
        
        # 3. 處理數值轉換 (將包含 '歲' 的欄位轉為數字，並移除可能存在的逗號)
        age_cols = [col for col in df.columns if '歲' in col]
        for col in age_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', ''), 
                errors='coerce'
            ).fillna(0)

        # 4. 資料加總 (將同一個區域的「男」、「女」人口合併計算)
        # 使用您的 CSV 實際欄位名稱 '區域別'
        population_df = df.groupby('區域別')[age_cols].sum().reset_index()

        # 5. 定義 65 歲以上欄位 (從欄位名稱如 '65-69歲' 中提取數字判定)
        elderly_cols = []
        for col in age_cols:
            try:
                # 提取第一個出現的數字
                age_val = int(''.join(filter(str.isdigit, col.split('歲')[0])))
                if age_val >= 65:
                    elderly_cols.append(col)
            except:
                continue

        # 6. 計算各項指標
        population_df['總人口數'] = population_df[age_cols].sum(axis=1)
        population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)
        # 避免除以 0 的錯誤
        population_df['老年人口占比'] = (population_df['65歲以上總數'] / population_df['總人口數']).fillna(0) * 100
        
        # 7. 合併地圖與資料
        townships_gdf['townname'] = townships_gdf['townname'].str.strip()
        population_df['區域別'] = population_df['區域別'].str.strip()
        
        # 內對接：地圖的 'townname' 對應 CSV 的 '區域別'
        gdf_merged = townships_gdf.merge(population_df, left_on='townname', right_on='區域別', how='inner')
        
        return gdf_merged

    except Exception as e:
        print(f"解析失敗: {e}")
        return None

def plot_elderly_ratio(data):
    """繪製地圖函數"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    
    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds',
        scheme='quantiles', # 需安裝 mapclassify
        edgecolor='black',
        linewidth=0.5,
        legend_kwds={'loc': 'lower right', 'title': "老年人口比例 (%)"}
    )

    plt.title('彰化縣各鄉鎮老年人口佔比分布圖', fontsize=16, fontweight='bold')
    plt.axis('off')
    return fig

@solara.component
def Page():
    # 載入與處理數據
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Error("資料載入或合併失敗！請檢查 CSV 內容與欄位名稱。", dense=True)
        return

    with solara.Card(title="彰化縣人口需求分析", elevation=4):
        with solara.Column():
            solara.Markdown("此地圖顯示彰化縣各行政區之 65 歲以上人口占比。")
            
            # 使用 solara.use_memo 產生圖表物件
            fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
            solara.FigureMatplotlib(fig)
            
            # 修正：將 solara.Expansion 改為 solara.Details
            with solara.Details("查看各鄉鎮詳細數據清單"):
                # 顯示排行前幾名的鄉鎮數據
                display_df = gdf_merged[['區域別', '總人口數', '65歲以上總數', '老年人口占比']].sort_values('老年人口占比', ascending=False)
                solara.DataFrame(display_df)

# 執行指令: solara run 檔名.py