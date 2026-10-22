import os
import re
import pandas as pd
import streamlit as st
from PIL import Image
import pytesseract

st.set_page_config(page_title="圖片檔名遺漏比對工具", layout="wide")
st.title("🖼️ 圖片檔名遺漏比對工具")

uploaded_excel = st.file_uploader("1️⃣ 請上傳 Excel 比對清單 (.xlsx)", type=["xlsx"])
uploaded_images = st.file_uploader("2️⃣ 請上傳包含檔案列表的圖片 (可多選)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_excel and uploaded_images:
    if st.button("🚀 開始辨識圖片並比對遺漏檔案"):
        with st.spinner("正在辨識圖片中的文字與檔名..."):
            extracted_filenames = set()
            
            for img_file in uploaded_images:
                image = Image.open(img_file)
                # 使用 pytesseract 進行光學辨識
                text = pytesseract.image_to_string(image)
                
                # 正則表達式抓取 YYYY_XXXX 或 YYYY-XXXX 編號
                matches = re.findall(r'\b\d{4}[_-]\d{4}(?:_[A-Za-z]+)?\b', text)
                for m in matches:
                    extracted_filenames.add(m.replace('-', '_').strip())

        st.success(f"從上傳圖片中，成功辨識出 {len(extracted_filenames)} 個不重複檔案編號！")

        df = pd.read_excel(uploaded_excel)
        summary_data = []
        missing_details = {}

        for col in df.columns:
            year = str(col).replace('清單', '').strip()
            raw_items = df[col].dropna().astype(str).str.strip().tolist()
            unique_excel_items = sorted(list(set([x.replace('-', '_') for x in raw_items])))
            
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

        st.subheader("📊 比對統計總覽")
        st.dataframe(summary_df, use_container_width=True)
        st.warning(f"⚠️ 總計遺漏數量：{summary_df['遺漏數量'].sum()} 個檔案")

        st.subheader("📋 各年份遺漏明細")
        for year, missing_list in missing_details.items():
            with st.expander(f"📅 {year} 年（共遺漏 {len(missing_list)} 個）"):
                if missing_list:
                    st.write(", ".join(missing_list))
                else:
                    st.success("無遺漏檔案")
