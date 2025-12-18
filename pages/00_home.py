import solara

# 1. 定義 Markdown 內容
markdown_content = """
## 🏥 醫療服務利用與資源分配

世界衛生組織（World Health Organization, WHO）（2000）指出群體之間的**醫療服務利用的不平等是不公正且應該要避免的**。

醫療資源的合理分配是確保人們可以獲得**可及性和可負擔的醫療福祉**的重要關鍵。

---

### 🗺️ 彰化醫院緩衝區分析 (GIS Analysis)
請透過下方選單切換不同的分析圖層：
"""

# 2. 定義圖片路徑（使用你提到的 Hugging Face Raw URL）
BASE_URL = "https://huggingface.co/peijhuuuuu/Changhua_hospital/resolve/main"
image_options = {
    "Layout 1: 基礎緩衝區": f"{BASE_URL}/Layout1.jpg",
    "Layout 1+2: 服務範圍重疊": f"{BASE_URL}/Layout1+2.jpg",
    "Layout 1+2+3: 完整資源分布": f"{BASE_URL}/Layout1+2+3.jpg"
}

@solara.component
def Page():
    # 建立一個反應式變數來儲存目前選中的圖層名稱
    selected_layout = solara.use_reactive("Layout 1: 基礎緩衝區")

    # 使用 Column 讓內容垂直排列
    with solara.Column(style={"padding": "20px", "max-width": "1000px", "margin": "0 auto"}):
        
        # 顯示原本的文字內容
        solara.Markdown(markdown_content)

        # 圖片選擇區域
        with solara.Card():
            # 下拉式選單
            solara.Select(
                label="選擇分析圖層", 
                value=selected_layout, 
                values=list(image_options.keys())
            )
            
            # 顯示圖片
            # 這裡會根據 selected_layout 的值從字典中取得對應的 URL
            solara.Image(image_options[selected_layout.value], width="100%")
            
            solara.Caption(f"當前檢視：{selected_layout.value}")

        # 頁腳註釋
        solara.Divider()
        solara.Markdown("*資料來源：World Health Organization (WHO), 2000 & GIS Analysis Database*")

# 渲染頁面
Page()