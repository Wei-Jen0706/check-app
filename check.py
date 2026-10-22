import os
import re
import io
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance
import pytesseract  # 補上必要的套件匯入

st.set_page_config(page_title="檔案遺漏比對與匯出工具", layout="wide")
st.title("🖼️ 檔案遺漏比對與下載工具")

st.markdown("""
本工具支援：
1. 上傳 **Excel 比對清單** (例如 `清單2.xlsx`)。
2. 上傳 **檔案列表截圖/圖片** (可多選 `.png`, `.jpg`, `.jpeg`)。
3. 自動進行**圖像對比強化與 2 倍放大**，提升文字辨識精準度並提供 **Excel 報告下載**。
""")

uploaded_excel = st.file_uploader("1️⃣ 請上傳 Excel 比對清單 (.xlsx)", type=["xlsx"])
uploaded_images = st.file_uploader("2️⃣ 請上傳包含檔案列表的圖片 (可多選)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_excel and uploaded_images:
    if st.button("🚀 開始辨識圖片並比對遺漏檔案"):
        with st.spinner("正在優化圖片對比並進行文字辨識，請稍候..."):
            extracted_filenames = set()
            
            for img_file in uploaded_images:
                try:
                    image = Image.open(img_file)
                    
                    # 1. 轉灰階
                    gray_img = image.convert('L')
                    
                    # 2. 提高對比度 (1.8 倍)
                    enhancer = ImageEnhance.Contrast(gray_img)
                    contrast_img = enhancer.enhance(1.8)
                    
                    # 3. 圖片放大 2 倍 (幫助小字體辨識)
                    new_size = (contrast_img.width * 2, contrast_img.height * 2)
                    resized_img = contrast_img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # 4. OCR 辨識
                    text = pytesseract.image_to_string(resized_img, config='--psm 6')
                    
                    matches = re.findall(r'\b\d{4}[_-]\d{4}(?:_[A-Za-z]+)?\b', text)
                    for m in matches:
                        extracted_filenames.add(m.replace('-', '_').strip())
                except Exception as e:
                    st.error(f"辨識圖片 {img_file.name} 時發生錯誤: {e}")

        st.success(f"已從上傳圖片中成功辨識出 {len(extracted_filenames)} 個不重複檔案編號！")

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

        # 1. 顯示統計總覽
        st.subheader("📊 比對統計總覽")
        st.dataframe(summary_df, use_container_width=True)
        st.warning(f"⚠️ 總計遺漏數量：{summary_df['遺漏數量'].sum()} 個檔案")

        # 2. 建立匯出 Excel 活頁簿
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='統計總覽', index=False)
            
            max_len = max([len(m) for m in missing_details.values()]) if missing_details else 0
            excel_style_dict = {}
            for year, m_list in missing_details.items():
                excel_style_dict[f"{year}遺漏清單"] = m_list + [None] * (max_len - len(m_list))
            
            missing_df = pd.DataFrame(excel_style_dict)
            missing_df.to_excel(writer, sheet_name='遺漏明細', index=False)

        output.seek(0)

        # 3. 提供下載按鈕
        st.subheader("📥 匯出結果報告")
        st.download_button(
            label="📥 下載遺漏檔案清單 (.xlsx)",
            data=output,
            file_name="遺漏檔案比對報告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 4. 網頁預覽
        st.subheader("📋 各年份遺漏明細（網頁預覽）")
        for year, missing_list in missing_details.items():
            with st.expander(f"📅 {year} 年（共遺漏 {len(missing_list)} 個）"):
                if missing_list:
                    st.write(", ".join(missing_list))
                else:
                    st.success("無遺漏檔案")

elif not uploaded_excel:
    st.info("👆 請先上傳 Excel 比對清單。")
elif not uploaded_images:
    st.info("👆 請上傳包含檔案列表的圖片。")
