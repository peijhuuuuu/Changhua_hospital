import solara

# 1. 定義 Markdown 內容
markdown_content = """
## 🏥 醫療服務利用與資源分配

世界衛生組織（World Health Organization, WHO）（2000）指出群體之間的**醫療服務利用的不平等是不公正且應該要避免的**。

醫療資源的合理分配是確保人們可以獲得**可及性和可負擔的醫療福祉**的重要關鍵。

---

        # 頁腳註釋
        solara.Divider()
        solara.Markdown("*資料來源：World Health Organization (WHO), 2000 & GIS Analysis Database*")

# 渲染頁面
Page()
