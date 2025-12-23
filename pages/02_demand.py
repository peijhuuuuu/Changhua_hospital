import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import io
import os

# --- 1. 字體下載與設定 ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/iansui/Iansui-Regular.ttf"
FONT_PATH = "Iansui-Regular.ttf"

def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, timeout=10)
            r.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"字體下載失敗: {e}")

download_font()

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    custom_font_name = fm.FontProperties(fname=FONT_PATH).get_name()
    plt.rcParams['font.sans-serif'] = [custom_font_name]
    plt.rcParams['axes.unicode_minus'] = False 
    custom_font = fm.FontProperties(fname=FONT_PATH)
else:
    custom_font = None

# --- 2. 資料來源 ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_POPULATION_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/age_population.csv" 

# --- 3. 資料載入與準備 ---
@solara.memoize
def load_and_prepare_demand_data():
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
        response = requests.get(CSV_POPULATION_URL)
        if response.status_code != 200:
            return None
        try:
            decoded_csv = response.content.decode('big5')
        except:
            decoded_csv = response.content.decode('utf-8', errors='ignore')
            
        df = pd.read_csv(io.StringIO(decoded_csv))
        age_cols = [col for col in df.columns if '(人數)' in col]
        
        for col in age_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '', regex=False).str.strip(), 
                errors='coerce'
            ).fillna(0)

        population_summary = df.groupby('區域別')[age_cols].sum().reset_index()
        elderly_cols = [col for col in age_cols if int(col.split('歲')[0]) >= 65]
        population_summary['總人口數'] = population_summary[age_cols].sum(axis=1).astype(int)
        population_summary['65歲以上總數'] = population_summary[elderly_cols].sum(axis=1).astype(int)
        population_summary['老年人口占比'] = (
            population_summary['65歲以上總數'] / population_summary['總人口數']
        ).fillna(0) * 100
        
        townships_gdf['townname'] = townships_gdf['townname'].str.strip()
        population_summary['區域別'] = population_summary['區域別'].str.strip()
        
        return townships_gdf.merge(population_summary, left_on='townname', right_on='區域別', how='inner')
    except Exception as e:
        print(f"解析失敗: {e}")
        return None

# --- 4. 繪圖函數 (字體已調大) ---
def plot_elderly_ratio(data):
    # 增加畫布高度以適應大標題
    fig, ax = plt.subplots(1, 1, figsize=(10, 11))
    
    # 繪製地圖
    data.plot(
        column='老年人口占比',
        ax=ax,
        legend=True,
        cmap='Reds',
        scheme='Quantiles', 
        k=5,
        edgecolor='0.8',
        linewidth=0.8,
        # 調大圖例標題與數值字體大小
        legend_kwds={
            'loc': 'lower right', 
            'title': "占比 (%)",
            'fmt': "{:.1f}",
        }
    )
    
    # 1. 調大標題 (16 -> 24)
    ax.set_title("彰化縣各鄉鎮老年人口占比圖", fontsize=24, fontproperties=custom_font, pad=20)
    
    # 2. 調大圖例內部的文字與標題
    legend = ax.get_legend()
    if legend:
        plt.setp(legend.get_texts(), fontsize=14, fontproperties=custom_font) # 圖例級別文字
        legend.get_title().set_fontsize(16) # 圖例標題 "占比 (%)"
        legend.get_title().set_fontproperties(custom_font)

    ax.set_axis_off()
    return fig

# --- 5. Solara 元件 ---
@solara.component
def Page():
    gdf_merged = load_and_prepare_demand_data()

    if gdf_merged is None or gdf_merged.empty:
        solara.Error("資料載入失敗，請確認資料源或檔案格式。", dense=True)
        return

    with solara.Column(style={"padding": "20px", "max-width": "1000px", "margin": "0 auto"}):
        
        solara.Markdown("# 彰化縣老年人口占比圖", style={"text-align": "center", "color": "#2c3e50"})
        
        solara.Markdown("""
        ### 醫療需求背景說明
        因高齡人口的健康水準下滑，通常需要更多的醫療照護和長期護理。
        > **圖表判讀指南：**
        > 顏色越深表示該行政區的**老年人口占比越高**。
        """, style={"font-size": "1.1rem", "line-height": "1.6", "background-color": "#f8f9fa", "padding": "15px", "border-radius": "8px"})

        # 地圖顯示區塊
        with solara.Card(elevation=4):
            fig = solara.use_memo(lambda: plot_elderly_ratio(gdf_merged), [gdf_merged])
            solara.FigureMatplotlib(fig)
            
        with solara.Details("查看各鄉鎮詳細數據表"):
            table_df = gdf_merged[['townname', '總人口數', '65歲以上總數', '老年人口占比']].copy()
            table_df.columns = ['鄉鎮名稱', '總人口數', '65歲以上人口', '老年人口占比(%)']
            table_df = table_df.drop_duplicates(subset=['鄉鎮名稱'])
            table_df = table_df.sort_values('老年人口占比(%)', ascending=False).reset_index(drop=True)
            table_df.index = table_df.index + 1
            table_df['老年人口占比(%)'] = table_df['老年人口占比(%)'].round(2)
            
            solara.Markdown("### 📊 彰化縣各行政區高齡化排名")
            solara.DataFrame(table_df.reset_index())
