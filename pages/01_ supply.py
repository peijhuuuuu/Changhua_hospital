import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle

# 1. 讀取地圖 (底圖)
townships = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson' 

# 2. 讀取並拆分 CSV (處理欄位擠在一起的問題)
csv_path = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/113年彰化縣醫療院所數.csv"
data_raw = pd.read_csv(csv_path, encoding="big5", header=None)
data = data_raw[0].str.split(',', expand=True)
data.columns = ['鄉鎮', '合計', '醫院數', '診所數']

# 3. 資料型態轉換
data = data[data['鄉鎮'] != '鄉鎮'] # 剔除標題列
data['合計'] = pd.to_numeric(data['合計'], errors='coerce')

# 4. 【核心步驟】使用 Merge 進行資料合併
# how='inner' 會自動剔除掉 CSV 裡對不到地圖的雜質(如總計)，解決左下角雜點
merged = townships.merge(data, left_on='townname', right_on='鄉鎮', how='inner')

# 5. 計算合併後的中心座標
merged['coords'] = merged['geometry'].apply(lambda x: x.representative_point().coords[0])

# 6. 開始繪圖
fig, ax = plt.subplots(1, 1, figsize=(10, 12))

# 畫彰化縣底圖
merged.plot(ax=ax, color="#ffafaf", edgecolor="#000000", linewidth=1)

# 畫分級符號 (圓圈)
ax.scatter(
    [c[0] for c in merged['coords']], 
    [c[1] for c in merged['coords']], 
    s=merged['合計'] * 15,  # 15 是縮放倍率，可依喜好調整
    color='blue', 
    alpha=0.6, 
    edgecolor='white',
    label='醫院+診所數量'
)

# 6. 安裝字體
font_path = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/NotoSansCJKtc-Regular.otf"
fm.fontManager.addfont(font_path)
prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.sans-serif'] = [prop.get_name()]

# 7. 設定標題與字體
plt.title('彰化縣各鄉鎮市醫療資源分布圖', fontsize=15)
plt.axis('off') 

plt.show()

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle

# 1. 讀取與清理資料
# 讀取 CSV (假設第一列是標題，如果不是請調整 header)
bed_data = "https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/彰化縣病床數.csv"

# 2. 合併資料
merged = townships.merge(bed_data, left_on='townname', right_on='地區')

# 3. 繪圖
fig, ax = plt.subplots(figsize=(12, 12))

# 繪製行政區底圖 (顏色改為你指定的 #9affa7)
merged.plot(ax=ax, color="#9affa7", edgecolor="#000000", linewidth=0.5)

# 4. 定義繪製圓環圖的函數
def add_donut(ax, x, y, val1, val2, scale=1.0):
    total = val1 + val2
    if total <= 0: return
    
    # 根據病床總數動態調整圓環大小 (選用)
    base_size = 20 * scale
    da = DrawingArea(base_size, base_size, 0, 0)
    center = base_size / 2
    radius = base_size / 2
    
    # 計算比例
    p1 = (val1 / total) * 360
    
    # 繪製圓弧：一般病床 (深紅), 特殊病床 (黃)
    w1 = Wedge((center, center), radius, 0, p1, color='#a93226')
    w2 = Wedge((center, center), radius, p1, 360, color='#f1c40f')
    
    # 圓環中心孔洞 (白色)
    center_circle = Circle((center, center), radius * 0.4, color='white')
    
    da.add_artist(w1)
    da.add_artist(w2)
    da.add_artist(center_circle)
    
    # 放置於中心點
    ab = AnnotationBbox(da, (x, y), frameon=False, pad=0)
    ax.add_artist(ab)

# 5. 走訪合併後的 GeoDataFrame 繪製圖表
for _, row in merged.iterrows():
    # 自動獲取行政區的中心點座標
    centroid = row.geometry.centroid
    x, y = centroid.x, centroid.y
    
    # 傳入對應的欄位名稱
    add_donut(ax, x, y, row['一般病床'], row['特殊病床'])



# 7. 美化
ax.set_axis_off()
plt.title("彰化縣各行政區病床分佈圖", fontsize=18, fontweight='bold')

# 添加簡單圖例說明
plt.text(0.1, 0.1, "■ 一般病床", color='#a93226', transform=ax.transAxes, fontsize=12)
plt.text(0.1, 0.07, "■ 特殊病床", color='#f1c40f', transform=ax.transAxes, fontsize=12)

plt.tight_layout()
plt.show()