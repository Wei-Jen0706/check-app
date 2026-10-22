import os
import re
import pandas as pd
import streamlit as st
from PIL import Image

# 嘗試載入 OCR 套件 (easyocr 或 pytesseract)
try:
    import easyocr
    import numpy as np
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

st.set_page_config(page_title="圖片檔名遺漏比對工具", layout="wide")
st.title("🖼️ 圖片檔名遺漏比對工具")

st.markdown("""
這個工具可以幫助您：
1. 上傳 **Excel 清單** (如 `清單2.xlsx`)。
2. 上傳包含檔案清單的 **截圖 / 圖片** (例如 `.png`, `.jpg`)。
3. 自動辨識圖片中的檔名（格式如 `2020_2547` 或 `2014-1103`），並與 Excel 比對遺漏檔案。
""")

# 1. 上傳 Excel 清單
uploaded_excel = st.file_uploader("1️⃣ 請上傳 Excel 比對清單 (.xlsx)", type=["xlsx"])

# 2. 上傳圖片檔
uploaded_images = st.file_uploader("2️⃣ 請上傳包含檔案列表的圖片 (可多選)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_excel and uploaded_images:
    if st.button("🚀 開始辨識圖片並比對遺漏檔案"):
        with st.spinner("正在辨識圖片中的文字與檔名，請稍候..."):
            extracted_filenames = set()
            
            # 使用 EasyOCR 解析圖片
            if HAS_EASYOCR:
                reader = easyocr.Reader(['en'], gpu=False)
                for img_file in uploaded_images:
                    image = Image.open(img_file)
                    img_np = np.array(image)
                    results = reader.readtext(img_np, detail=0)
                    
                    # 用正則表達式找出 YYYY_XXXX 或 YYYY-XXXX 格式的編號
                    for text in results:
                        matches = re.findall(r'\b\d{4}[_-]\d{4}(?:_[A-Za-z]+)?\b', text)
                        for m in matches:
                            extracted_filenames.add(m.replace('-', '_').strip())
            else:
                st.error("系統未安裝 EasyOCR 套件，請在 requirements.txt 中新增 `easyocr` 與 `opencv-python-headless`！")
                st.stop()

        st.success(f"從上傳的 {len(uploaded_images)} 張圖片中，成功辨識出 {len(extracted_filenames)} 個不重複檔案編號！")

        # 3. 比對 Excel
        df = pd.read_excel(uploaded_excel)
        summary_data = []
        missing_details = {}

        for col in df.columns:
            year = str(col).replace('清單', '').strip()
            raw_items = df[col].dropna().astype(str).str.strip().tolist()
            unique_excel_items = sorted(list(set([x.replace('-', '_') for x in raw_items])))
            
            # 找出遺漏項目
            missing = [x for x in unique_excel_items if x not in extracted_filenames]
            
            total_unique = len(unique_excel_items)
            missing_count = len(missing)
            found_count = total_unique - missing_count
            
            summary_data.append({
                '年份': year,
                '應有數量(不重複)': total_unique,
                '辨識到的數量': found_count,
                '遺漏數量': missing_count
            })
            missing_details[year] = missing

        summary_df = pd.DataFrame(summary_data)

        # 4. 顯示統計總覽
        st.subheader("📊 比對統計總覽")
        st.dataframe(summary_df, use_container_width=True)
        st.warning(f"⚠️ 總計遺漏數量：{summary_df['遺漏數量'].sum()} 個檔案")

        # 5. 顯示遺漏明細
        st.subheader("📋 各年份遺漏明細")
        for year, missing_list in missing_details.items():
            with st.expander(f"📅 {year} 年（共遺漏 {len(missing_list)} 個）"):
                if missing_list:
                    st.write(", ".join(missing_list))
                else:
                    st.success("無遺漏檔案")

elif not uploaded_excel:
    st.info("👆 請先上傳 Excel 清單檔案。")
elif not uploaded_images:
    st.info("👆 請上傳包含檔案列表的圖片。")
