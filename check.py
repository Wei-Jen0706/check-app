import os
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="檔案遺漏比對工具", layout="wide")
st.title("📁 檔案遺漏比對工具")

# 1. 上傳 Excel 清單
uploaded_excel = st.file_uploader("請上傳 Excel 比對清單 (.xlsx)", type=["xlsx"])

# 2. 選擇檔案來源模式
option = st.radio("請選擇實體檔案來源：", ["上傳 ZIP 壓縮檔 (包含所有待比對檔案)", "使用伺服器/本機資料夾"])

folder_files = set()

if option == "上傳 ZIP 壓縮檔 (包含所有待比對檔案)":
    uploaded_zip = st.file_uploader("請上傳壓縮檔 (.zip)", type=["zip"])
    if uploaded_zip:
        with zipfile.ZipFile(uploaded_zip, 'r') as z:
            for filename in z.namelist():
                # 排除資料夾路徑，僅保留檔名
                base_name = os.path.basename(filename)
                if base_name:
                    name_without_ext = os.path.splitext(base_name)[0].replace('-', '_').strip()
                    folder_files.add(name_without_ext)
        st.success(f"已讀取 ZIP 內 {len(folder_files)} 個獨立檔案編號")

else:
    target_dir = st.text_input("請輸入伺服器資料夾路徑：", value="./")
    if os.path.exists(target_dir):
        for f in os.listdir(target_dir):
            base_name = os.path.splitext(f)[0].replace('-', '_').strip()
            folder_files.add(base_name)
        st.info(f"資料夾內共有 {len(folder_files)} 個獨立檔案編號")
    else:
        st.error(f"找不到資料夾：{target_dir}")

# 3. 開始比對
if uploaded_excel and folder_files:
    if st.button("🚀 開始比對"):
        df = pd.read_excel(uploaded_excel)
        
        summary_data = []
        missing_details = {}

        for col in df.columns:
            year = str(col).replace('清單', '').strip()
            raw_items = df[col].dropna().astype(str).str.strip().tolist()
            unique_excel_items = sorted(list(set([x.replace('-', '_') for x in raw_items])))
            
            missing = [x for x in unique_excel_items if x not in folder_files]
            
            total_unique = len(unique_excel_items)
            missing_count = len(missing)
            found_count = total_unique - missing_count
            
            summary_data.append({
                '年份': year,
                '應有數量(不重複)': total_unique,
                '現有數量': found_count,
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

elif not uploaded_excel:
    st.info("👆 請先上傳 Excel 清單檔案開始比對。")
