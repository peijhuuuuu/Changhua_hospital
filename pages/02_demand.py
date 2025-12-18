import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# --- 1. 資料來源 ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

@solara.memoize
def load_and_prepare_demand_data():
    """載入資料、清理、加總男女人口並與地圖合併。"""
    try:
        # 讀取地圖
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        
        # 讀取 CSV
        response = requests.get(CSV_POPULATION_URL)
        if response.status_code != 200:
            return None
        try:
            decoded_csv = response.content.decode('big5')
        except:
            decoded_csv = response.content.decode('utf-8', errors='ignore')
            
        df = pd.read_csv(io.StringIO(decoded_csv))
        
        # --- 數據清理 ---
        age_cols = [col for col in df.columns if '(人數)' in col]
        
        for col in age_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '', regex=False).str.strip(), 
                errors='coerce'
            ).fillna(0)

        # 核心修正：先將男女數據按「區域別」完全加總
        # 確保每個鄉鎮在此步驟後只剩下一筆資料
        population_summary = df.groupby('區域別')[age_cols].sum().reset_index()

        # 篩選 65 歲以上欄位
        elderly_cols = [col for col in age_cols if int(col.split('歲')[0]) >= 65]

        # 計算總數與占比
        population_summary['總人口數'] = population_summary[age_cols].sum(axis=1).astype(int)
        population_summary['65歲以上總數'] = population_summary[elderly_cols].sum(axis=1).astype(int)
        population_summary['老年人口占比'] = (
            population_summary['65歲以上總數'] / population_summary['總人口數']
        ).fillna(0) * 100
        
        # --- 合併地圖 ---
        townships_gdf['townname'] = townships_gdf['townname'].str.strip()
        population_summary['區域別'] = population_summary['區域別'].str.strip()
        
        # 使用 inner join 確保只顯示有對應到的行政區
        gdf_merged = townships_gdf.merge(
            population_summary, 
            left_on='townname', 
            right_on='區域別', 
            how='inner'
        )
        
        return gdf_merged
    except Exception as e:
        print(f"解析失敗: {e}")
        return None

def plot_elderly_ratio(data):
    """繪製地圖"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds',
        scheme='Quantiles', 
        k=5,
        edgecolor='0.8',
        linewidth=0.8,
        legend_kwds={'loc': 'lower right', 'title': "占比 (%)"}
    )
    ax.set_axis_off()
    return fig

@solara.component
def Page():
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Error("資料載入失敗，請確認資料源或檔案格式。", dense=True)
        return

    with solara.Column(style={"padding": "20px", "max-width": "1000px", "margin": "0 auto"}):
        
        # 標題與說明文字
        solara.Markdown("# 彰化縣老年人口占比圖", style={"text-align": "center", "color": "#2c3e50"})
        
        solara.Markdown("""
        ### 醫療需求背景說明
        因高齡人口的健康水準下滑，通常需要更多的醫療照護和長期護理，**醫療需求相對於青壯年以及幼年高**。
        因此可由各行政區老年人口之比例大略推估該地區對醫療資源需求度的高低。
        
        > **圖表判讀指南：**
        > 顏色越深表示該行政區的**老年人口占比越高**，也就是說該行政區需要較多針對高齡人口的醫療資源。
        """, style={"font-size": "1.1rem", "line-height": "1.6", "background-color": "#f8f9fa", "padding": "15px", "border-radius": "8px"})

        # 地圖區塊
        with solara.Card(elevation=4):
            fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
            solara.FigureMatplotlib(fig)
            
        # --- 數據表修正區塊：確保各鄉鎮唯一化與排名 ---
        with solara.Details("查看各鄉鎮詳細數據表"):
            # 1. 取出並備份資料
            table_df = gdf_merged[['townname', '總人口數', '65歲以上總數', '老年人口占比']].copy()
            
            # 2. 重新命名
            table_df.columns = ['鄉鎮名稱', '總人口數', '65歲以上人口', '老年人口占比(%)']
            
            # 3. 關鍵修正：確保鄉鎮名稱唯一（防止 Merge 產生的重複）
            table_df = table_df.drop_duplicates(subset=['鄉鎮名稱'])
            
            # 4. 進行排序並產生名次
            table_df = table_df.sort_values('老年人口占比(%)', ascending=False).reset_index(drop=True)
            table_df.index = table_df.index + 1 # 名次從 1 開始
            table_df.index.name = '排名'
            
            # 5. 格式化數值
            table_df['老年人口占比(%)'] = table_df['老年人口占比(%)'].round(2)
            
            solara.Markdown("### 📊 彰化縣各行政區高齡化排名")
            solara.Markdown("*(數據已按老年人口占比由高至低排序，名次 1 代表高齡化最嚴重之區域)*")
            
            # 將索引（排名）重設為欄位以便在表格顯示
            solara.DataFrame(table_df.reset_index())