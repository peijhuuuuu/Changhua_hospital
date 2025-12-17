import solara
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.offsetbox import DrawingArea, AnnotationBbox
from matplotlib.patches import Wedge, Circle

# 1. 讀取地圖 (底圖)
townships = gpd.read_file(r"C:\Users\user\Downloads\changhua.geojson")

# 2. 讀取並拆分 CSV (處理欄位擠在一起的問題)
csv_path = r"C:\Users\user\Downloads\113年彰化縣醫療院所數.csv"
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

# 7. 設定標題與字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.title('彰化縣各鄉鎮市醫療資源分布圖', fontsize=15)
plt.axis('off') 

plt.show()