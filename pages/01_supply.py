import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle

# --- Data Sources ---
TOWNSHIPS_URL = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson'
CSV_HOSPITAL_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/113hospital.csv"
CSV_BED_URL = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua_bed.csv"

# --- Data Loading and Preparation ---

@solara.memoize
def load_and_prepare_data():
    """Loads all data and performs initial processing."""
    try:
        townships_gdf = gpd.read_file(TOWNSHIPS_URL)
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return None, None 

    # --- Hospital Resource Data ---
    # Note: Use 'cp950' for many Taiwan government CSVs if 'big5' or 'utf-8' fails
    hospital_data_raw = pd.read_csv(CSV_HOSPITAL_URL, encoding="big5", header=None)
    hospital_data = hospital_data_raw[0].str.split(',', expand=True)
    hospital_data.columns = ['鄉鎮', '合計', '醫院數', '診所數']
    hospital_data = hospital_data[hospital_data['鄉鎮'] != '鄉鎮'] 
    hospital_data['合計'] = pd.to_numeric(hospital_data['合計'], errors='coerce')

    merged_hospital = townships_gdf.merge(hospital_data, left_on='townname', right_on='鄉鎮', how='inner')
    merged_hospital['coords'] = merged_hospital['geometry'].apply(lambda x: x.representative_point().coords[0])

    # --- Bed Data ---
    bed_data_raw = pd.read_csv(CSV_BED_URL, encoding="utf-8")
    bed_data = bed_data_raw.copy()
    bed_data['一般病床'] = pd.to_numeric(bed_data['一般病床'], errors='coerce').fillna(0)
    bed_data['特殊病床'] = pd.to_numeric(bed_data['特殊病床'], errors='coerce').fillna(0)

    merged_bed = townships_gdf.merge(bed_data, left_on='townname', right_on='地區', how='inner')

    return merged_hospital, merged_bed

# --- Plotting Functions ---

def plot_hospital_resource(data):
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    data.plot(ax=ax, color="#ffafaf", edgecolor="#000000", linewidth=1)

    ax.scatter(
        [c[0] for c in data['coords']], 
        [c[1] for c in data['coords']], 
        s=data['合計'] * 15, 
        color='blue', 
        alpha=0.6, 
        edgecolor='white',
        label='醫院+診所數量'
    )
    plt.title('彰化縣各鄉鎮市醫療資源分布圖', fontsize=15)
    plt.axis('off') 
    return fig

def add_donut(ax, x, y, val1, val2, scale=1.0):
    total = val1 + val2
    if total <= 0: return
    
    base_size = 20 * scale
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
        add_donut(ax, centroid.x, centroid.y, row['一般病床'], row['特殊病床'])

    ax.set_axis_off()
    plt.title("彰化縣各行政區病床分佈圖", fontsize=18, fontweight='bold')
    plt.text(0.1, 0.1, "■ 一般病床", color='#a93226', transform=ax.transAxes, fontsize=12)
    plt.text(0.1, 0.07, "■ 特殊病床", color='#f1c40f', transform=ax.transAxes, fontsize=12)
    plt.tight_layout()
    return fig

# --- Solara Application Component ---

@solara.component
def Page():
    # 1. Load Data
    merged_hospital, merged_bed = load_and_prepare_data()

    if merged_hospital is None or merged_bed is None:
        solara.Warning("資料載入失敗，請檢查資料來源與網路連線。", dense=True)
        return

    # 2. Use Memo to create the Figure objects (prevents redundant plotting)
    fig_hospital = solara.use_memo(lambda: plot_hospital_resource(merged_hospital), [merged_hospital])
    fig_bed = solara.use_memo(lambda: plot_bed_distribution(merged_bed), [merged_bed])

    # 3. Render the UI
    with solara.Columns(widths=[6, 6]):
        with solara.Card(title="醫療資源分布 (醫院 + 診所數量)", elevation=2):
            solara.FigureMatplotlib(fig_hospital)
        
        with solara.Card(title="病床分佈 (圓環圖)", elevation=2):
            solara.FigureMatplotlib(fig_bed)

# To run: solara run your_filename.py