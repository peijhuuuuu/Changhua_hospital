import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle
import io # 用於處理字串讀取

# --- 資料來源 (修正 404/Private Repo 問題，直接從 Raw GitHub 連結讀取) ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_HOSPITAL_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/113hospital.csv"
CSV_BED_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua_bed.csv"

# --- 數據載入和處理 (使用 solara.memoize 避免重複載入) ---

@solara.memoize
def load_and_prepare_data():
    """載入所有資料並進行初步處理和合併，返回兩個 GeoDataFrame。"""
    
    # 1. 讀取 GeoJSON 地圖 (修正 townships 變數為 GeoDataFrame)
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        # 如果網路讀取失敗，使用一個空的 GeoDataFrame 避免程序崩潰
        townships_gdf = gpd.GeoDataFrame()
        return None, None 

    # --- 處理醫療資源數據 (圖表一所需) ---
    hospital_data_raw = pd.read_csv(CSV_HOSPITAL_URL, encoding="big5", header=None)
    
    # 讀取 CSV 時欄位擠在一起的處理
    # 假設 CSV 數據在第一列，需要拆分
    hospital_data = hospital_data_raw[0].str.split(',', expand=True)
    hospital_data.columns = ['鄉鎮', '合計', '醫院數', '診所數']
    
    # 資料清理與型態轉換
    hospital_data = hospital_data[hospital_data['鄉鎮'] != '鄉鎮'] # 剔除標題列
    hospital_data['合計'] = pd.to_numeric(hospital_data['合計'], errors='coerce')

    # 合併圖表一數據
    merged_hospital = townships_gdf.merge(hospital_data, left_on='townname', right_on='鄉鎮', how='inner')
    merged_hospital['coords'] = merged_hospital['geometry'].apply(lambda x: x.representative_point().coords[0])

    # --- 處理病床數據 (圖表二所需) ---
    bed_data_raw = pd.read_csv(CSV_BED_URL)
    
    # 將病床數欄位轉換為數字 (假設欄位名稱為 '一般病床', '特殊病床')
    # 這裡假設 bed_data_raw 已經是乾淨的 DataFrame 格式
    bed_data = bed_data_raw
    bed_data['一般病床'] = pd.to_numeric(bed_data['一般病床'], errors='coerce').fillna(0)
    bed_data['特殊病床'] = pd.to_numeric(bed_data['特殊病床'], errors='coerce').fillna(0)

    # 合併圖表二數據
    # 假設合併鍵是 'townname' 對 '地區'
    merged_bed = townships_gdf.merge(bed_data, left_on='townname', right_on='地區', how='inner')

    return merged_hospital, merged_bed

# --- 繪圖函數 ---

# 圖表一：醫療資源分布圖 (分級符號圖)
def plot_hospital_resource(merged_hospital):
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))

    # 畫彰化縣底圖
    merged_hospital.plot(ax=ax, color="#ffafaf", edgecolor="#000000", linewidth=1)

    # 畫分級符號 (圓圈)
    # 由於 '合計' 欄位已經是數字 (步驟 3)，這裡可以直接使用
    ax.scatter(
        [c[0] for c in merged_hospital['coords']], 
        [c[1] for c in merged_hospital['coords']], 
        s=merged_hospital['合計'] * 15, # 15 是縮放倍率
        color='blue', 
        alpha=0.6, 
        edgecolor='white',
        label='醫院+診所數量'
    )
    
    # 標籤每個行政區的名稱 (可選)
    # for x, y, label in zip([c[0] for c in merged_hospital['coords']], [c[1] for c in merged_hospital['coords']], merged_hospital['townname']):
    #     ax.text(x, y, label, fontsize=8, ha='center', va='center')


    plt.title('彰化縣各鄉鎮市醫療資源分布圖', fontsize=15)
    plt.axis('off') 
    return fig

# 圖表二：病床分佈圖 (圓環圖)
# 定義繪製圓環圖的函數 (與您原來的邏輯相同)
def add_donut(ax, x, y, val1, val2, scale=1.0):
    total = val1 + val2
    if total <= 0: return
    
    base_size = 20 * scale
    da = DrawingArea(base_size, base_size, 0, 0)
    center = base_size / 2
    radius = base_size / 2
    
    p1 = (val1 / total) * 360
    
    w1 = Wedge((center, center), radius, 0, p1, color='#a93226') # 一般病床 (深紅)
    w2 = Wedge((center, center), radius, p1, 360, color='#f1c40f') # 特殊病床 (黃)
    
    center_circle = Circle((center, center), radius * 0.4, color='white')
    
    da.add_artist(w1)
    da.add_artist(w2)
    da.add_artist(center_circle)
    
    ab = AnnotationBbox(da, (x, y), frameon=False, pad=0)
    ax.add_artist(ab)

def plot_bed_distribution(merged_bed):
    fig, ax = plt.subplots(figsize=(12, 12))

    # 繪製行政區底圖
    merged_bed.plot(ax=ax, color="#9affa7", edgecolor="#000000", linewidth=0.5)

    # 走訪合併後的 GeoDataFrame 繪製圖表
    for _, row in merged_bed.iterrows():
        centroid = row.geometry.centroid
        x, y = centroid.x, centroid.y
        
        # 傳入對應的欄位名稱
        add_donut(ax, x, y, row['一般病床'], row['特殊病床'])

    ax.set_axis_off()
    plt.title("彰化縣各行政區病床分佈圖", fontsize=18, fontweight='bold')

    # 添加簡單圖例說明
    plt.text(0.1, 0.1, "■ 一般病床", color='#a93226', transform=ax.transAxes, fontsize=12)
    plt.text(0.1, 0.07, "■ 特殊病床", color='#f1c40f', transform=ax.transAxes, fontsize=12)

    plt.tight_layout()
    return fig

# --- Solara 應用程式組件 ---

@solara.component
def Page():
    # 載入數據
    merged_hospital, merged_bed = load_and_prepare_data()

    if merged_hospital is None or merged_bed is None:
        solara.Warning("資料載入失敗，請檢查 URL 或網路連線。", dense=True)
        return

    with solara.Columns(widths=[6, 6]):
        
        # 顯示圖表一：將數據作為具名參數 'data' 傳遞
        with solara.Card(title="醫療資源分布 (醫院 + 診所數量)", elevation=2):
            solara.FigureMatplotlib(plot_hospital_resource, data=merged_hospital) 
        
        # 顯示圖表二：將數據作為具名參數 'data' 傳遞
        with solara.Card(title="病床分佈 (圓環圖)", elevation=2):
            solara.FigureMatplotlib(plot_bed_distribution, data=merged_bed)