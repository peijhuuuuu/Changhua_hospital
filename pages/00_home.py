import solara

# 1. 定義 Markdown 內容 (已修正：加上結尾的三引號)
markdown_content = """
## 🏥 醫療服務利用與資源分配
世界衛生組織（World Health Organization, WHO）（2000）指出群體之間的**醫療服務利用的不平等是不公正且應該要避免的**。
醫療資源的合理分配是確保人們可以獲得**可及性和可負擔的醫療福祉**的重要關鍵。
"""

# 2. 定義頁面組件
@solara.component
def Page():
    # 建立一個反應式變數來儲存目前選中的圖層名稱
    selected_layout = solara.use_reactive("Layout 1: 基礎緩衝區")

    # 使用 Column 讓內容垂直排列
    with solara.Column(style={"padding": "20px", "max-width": "1000px", "margin": "0 auto"}):
        
        # 顯示原本的文字內容
        solara.Markdown(markdown_content)

        solara.Markdown("---")
        solara.Markdown("*資料來源：World Health Organization (WHO), 2000 & GIS Analysis Database*")

# 渲染頁面 (Solara 會自動尋找名為 Page 的組件)
