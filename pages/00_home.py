import solara
# 使用 solara.Markdown 來渲染 Markdown 格式的文字。
# 這裡使用三引號 """ 來包含多行文字，保持格式清晰。
markdown_content = """
## 🏥 醫療服務利用與資源分配

世界衛生組織（World Health Organization, WHO）（2000）指出群體之間的**醫療服務利用的不平等是不公正且應該要避免的**。

醫療資源的合理分配是確保人們可以獲得**可及性和可負擔的醫療福祉**的重要關鍵。

---

*資料來源：World Health Organization (WHO), 2000*
"""

# 定義 Solara 應用程式的主頁面組件
@solara.component
def Page():
    # 使用 solara.Markdown 來顯示內容
    return solara.Markdown(markdown_content)

# 執行 Solara 應用程式 (這部分通常在 Jupyter/Colab 或獨立的 main 檔案中)
# 如果在 Jupyter/Colab 中，您只需定義 Page 組件，它就會自動渲染。
# 如果是獨立應用程式，您可以使用 `solara run your_file.py`