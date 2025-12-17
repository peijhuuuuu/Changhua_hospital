import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# -----------------------------------------------------------------
# 🎯 步驟 1: 檔案路徑定義 (使用您的 GitHub Raw URL)
# -----------------------------------------------------------------
csv_path = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/彰化縣現住人口之年齡結構.csv'
geojson_path = 'https://raw.githubusercontent.com/peijhuuuuu/Changhua_hospital/main/changhua.geojson' 
# -----------------------------------------------------------------

# 初始化變數，防止讀取失敗時後續 NameError
population_df = None
gdf_towns = None

# --- 2. 數據讀取與編碼處理 ---
try:
    # 嘗試 big5 編碼
    population_df = pd.read_csv(csv_path, encoding='big5')
    gdf_towns = gpd.read_file(geojson_path)
    print("✅ 檔案讀取成功！")
except UnicodeDecodeError:
    # 嘗試 cp950 編碼
    try:
        population_df = pd.read_csv(csv_path, encoding='cp950')
        gdf_towns = gpd.read_file(geojson_path)
        print("✅ 檔案讀取成功！(使用 cp950)")
    except Exception as e:
        print(f"❌ 檔案讀取失敗，請檢查編碼或 Raw URL：{e}")
        
except Exception as e:
    print(f"❌ 檔案讀取失敗：{e}")


# --- 3. 數據清理、計算與合併 ---
if population_df is not None and gdf_towns is not None:
    
    TOWN_COL_CSV = '區域別'
    TOWN_COL_GEO = 'townname'  # GeoJSON 中正確的鄉鎮欄位名

    age_cols = [col for col in population_df.columns if '(人數)' in col]
    elderly_cols = [col for col in age_cols if int(col.split('歲')[0]) >= 65]

    # 清除逗號並轉換為數值
    for col in age_cols:
        population_df[col] = (
            population_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
        )
        population_df[col] = pd.to_numeric(population_df[col], errors='coerce').fillna(0) 

    # 計算總人口和老年人口
    population_df['總人口數'] = population_df[age_cols].sum(axis=1)
    population_df['65歲以上總數'] = population_df[elderly_cols].sum(axis=1)

    # 按鄉鎮分組加總並計算占比
    population_summary = population_df.groupby(TOWN_COL_CSV).agg({
        '總人口數': 'sum',
        '65歲以上總數': 'sum'
    }).reset_index()

    population_summary['老年人口占比'] = (
        population_summary['65歲以上總數'] / population_summary['總人口數']
    ) * 100

    # 確保合併欄位名稱匹配
    population_summary = population_summary.rename(columns={TOWN_COL_CSV: TOWN_COL_GEO})


    # 數據合併
    gdf_merged = gdf_towns.merge(population_summary,
                                left_on=TOWN_COL_GEO, 
                                right_on=TOWN_COL_GEO, 
                                how='left')

    gdf_merged['老年人口占比'] = gdf_merged['老年人口占比'].fillna(0)
    print("✅ GeoDataFrame 合併完成。")

    
    # --- 4. 繪製純地理分佈圖 ---
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # 繪製面量圖 (關鍵設置：legend=False, ax.set_title(''), ax.set_axis_off())
    gdf_merged.plot(column='老年人口占比', 
                    ax=ax, 
                    cmap='Reds',           
                    legend=False,          # 移除圖例
                    scheme='Quantiles',    
                    k=5,                   
                    linewidth=0.8, 
                    edgecolor='0.8') 

    ax.set_title('', fontsize=1) # 移除標題
    ax.set_axis_off()          # 隱藏坐標軸

    plt.tight_layout(pad=0)
    plt.show()

    print("✅ 純地理分佈圖繪製完成 (無文字、無坐標軸、無圖例)。")
    
else:
    print("❌ 無法執行後續的數據計算與繪圖，請檢查檔案讀取是否成功。")