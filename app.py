import solara

# 1. 建立一個「響應式」變數 (元件的私有記憶)
count = solara.reactive(0)

# 2. 定義一個 Solara 元件 (用 @ 裝飾)
@solara.component
def Page():
    solara.Title("我的 Solara App")
    solara.Markdown(f"## 按鈕被點擊了 {count.value} 次！")

    def increment():
        count.value += 1 # 改變狀態值

    # 3. 建立一個按鈕，綁定 on_click 事件
    solara.Button("點我！", on_click=increment)