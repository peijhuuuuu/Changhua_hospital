import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import requests
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle

# --- 1. 字體下載設定 ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/iansui/Iansui-Regular.ttf"
FONT_PATH = "Iansui-Regular.ttf"

def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            print("正在下載中文字體...")
            r = requests.get(FONT_URL, timeout=10)
            r.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
            print("字體下載完成。")
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
CSV_HOSPITAL_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/113hospital.csv"
CSV_BED_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua_bed.csv"

# --- 3. 資料載入與準備 ---
@solara.memoize
def load_and_prepare_data():
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return None, None 

    try:
        hospital_data_raw = pd.read_csv(CSV_HOSPITAL_URL, encoding="big5", header=None)
        hospital_data = hospital_data_raw[0].str.split(',', expand=True)
        hospital_data.columns = ['鄉鎮', '合計', '醫院數', '診所數']
        hospital_data = hospital_data[hospital_data['鄉鎮'] != '鄉鎮'] 
        hospital_data['合計'] = pd.to_numeric(hospital_data['合計'], errors='coerce')
        merged_hospital = townships_gdf.merge(hospital_data, left_on='townname', right_on='鄉鎮', how='inner')
        merged_hospital['coords'] = merged_hospital['geometry'].apply(lambda x: x.representative_point().coords[0])
    except:
        merged_hospital = None

    try:
        bed_data_raw = pd.read_csv(CSV_BED_URL, encoding="utf-8")
        bed_data = bed_data_raw.copy()
        bed_data['一般病床'] = pd.to_numeric(bed_data['一般病床'], errors='coerce').fillna(0)
        bed_data['特殊病床'] = pd.to_numeric(bed_data['特殊病床'], errors='coerce').fillna(0)
        merged_bed = townships_gdf.merge(bed_data, left_on='townname', right_on='地區', how='inner')
    except:
        merged_bed = None

    return merged_hospital, merged_bed

# --- 4. 繪圖函數  ---

def plot_hospital_resource(data):
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    data.plot(ax=ax, color="#ffafaf", edgecolor="#000000", linewidth=1)

    ax.scatter(
        [c[0] for c in data['coords']], 
        [c[1] for c in data['coords']], 
        s=data['合計'] * 20, # 調大圓點尺寸
        color='blue', 
        alpha=0.6, 
        edgecolor='white',
    )
    # 調大標題字體 (15 -> 22)
    plt.title('彰化縣各鄉鎮市醫療資源分布圖', fontsize=30, fontproperties=custom_font, pad=20)
    plt.axis('off') 
    return fig

def add_donut(ax, x, y, val1, val2, scale=1.5): # 調大圓環比例 (1.0 -> 1.5)
    total = val1 + val2
    if total <= 0: return
    
    base_size = 25 * scale # 調大基礎大小
    da = DrawingArea(base_size, base_size, 0, 0)
    center = base_size / 2
    radius = base_size / 2
    
    p1 = (val1 / total) * 360
    w1 = Wedge((center, center), radius, 0, p1, color='#a93226') 
    w2 = Wedge((center, center), radius, p1, 360, color='#f1c40f') 
    center_circle = Circle((center, center), radius * 0.4, color='white')
    
    da.add_artist(w1)
    da.add_artist(w2)
    da.add_artist(center_circle)
    
    ab = AnnotationBbox(da, (x, y), frameon=False, pad=0)
    ax.add_artist(ab)

def plot_bed_distribution(data):
    fig, ax = plt.subplots(figsize=(12, 12))
    data.plot(ax=ax, color="#9affa7", edgecolor="#000000", linewidth=0.5)

    for _, row in data.iterrows():
        centroid = row.geometry.centroid
        # 調用加大的圓環函數
        add_donut(ax, centroid.x, centroid.y, row['一般病床'], row['特殊病床'], scale=1.8)

    ax.set_axis_off()
    # 調大標題字體 (18 -> 26)
    plt.title("彰化縣各行政區病床分佈圖", fontsize=30, fontweight='bold', fontproperties=custom_font, pad=20)
    
    # 調大圖例文字 (12 -> 18)
    ax.text(0.05, 0.12, "■ 一般病床", color='#a93226', transform=ax.transAxes, fontsize=18, fontproperties=custom_font)
    ax.text(0.05, 0.08, "■ 特殊病床", color='#f1c40f', transform=ax.transAxes, fontsize=18, fontproperties=custom_font)
    
    plt.tight_layout()
    return fig

# --- 5. Solara 應用程式介面 ---

@solara.component
def Page():
    merged_hospital, merged_bed = load_and_prepare_data()

    if merged_hospital is None or merged_bed is None:
        solara.Warning("資料載入失敗...", dense=True)
        return

    fig_hospital = solara.use_memo(lambda: plot_hospital_resource(merged_hospital), [merged_hospital])
    fig_bed = solara.use_memo(lambda: plot_bed_distribution(merged_bed), [merged_bed])

    with solara.Column(style={"padding": "20px"}):
        solara.Markdown("# 🏥 彰化縣醫療資源分析儀表板")
        solara.Markdown("---")

        with solara.Columns(widths=[6, 6]):
            with solara.Card(elevation=2):
                solara.FigureMatplotlib(fig_hospital)
            
            with solara.Card(elevation=2):
                solara.FigureMatplotlib(fig_bed)

        solara.Markdown("---")
        solara.Text("資料來源：彰化縣政府開放資料集", style="font-size: 1.2rem;")
