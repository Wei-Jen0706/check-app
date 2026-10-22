import os
import re
import io
import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PDF 檔名管理與自動化比對工具箱", layout="wide")
st.title("🛠️ PDF 檔名管理與自動化比對工具箱")

# 使用 Streamlit 分頁 (Tabs) 整合兩個工具
tab1, tab2 = st.tabs(["✂️ 功能一：PDF 檔名裁切重命名", "📊 功能二：檔案掃描與雙 Excel 遺漏比對"])

# ==========================================
# Tab 1: PDF 檔名裁切重命名工具 (原 remane.py)
# ==========================================
with tab1:
    st.header("✂️ PDF 檔名裁切工具 (保留 1234_5678 格式)")
    st.markdown("自動識別檔名開頭的 **4 位數字_4 位數字**，並將後面的多餘文字與數字刪除（例如：`2020_2547_年報.pdf` ➔ `2020_2547.pdf`）。")

    folder_path = st.text_input("請輸入資料夾完整路徑：", placeholder=r"C:\Users\User\Desktop\PDF_AI_Tool", key="rename_path")

    if folder_path and os.path.exists(folder_path):
        all_files = os.listdir(folder_path)
        pdf_files = [f for f in all_files if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(folder_path, f))]
        
        if not pdf_files:
            st.warning("⚠️ 該資料夾內沒有找到任何 .pdf 檔案。")
        else:
            st.success(f"📂 成功讀取到 {len(pdf_files)} 個 PDF 檔案。")
            
            rename_map = {}
            pattern = re.compile(r"^(\d{4}_\d{4})")

            for filename in pdf_files:
                name, ext = os.path.splitext(filename)
                match = pattern.match(name)
                
                if match:
                    new_filename = match.group(1) + ext
                    rename_map[filename] = new_filename
                else:
                    rename_map[filename] = filename

            st.subheader("👁️ 改名預覽")
            df_preview = pd.DataFrame([
                {
                    "原始檔名": old_f, 
                    "修改後檔名": new_f, 
                    "狀態": "✨ 將進行修改" if old_f != new_f else "⚠️ 未匹配格式（不變）"
                }
                for old_f, new_f in rename_map.items()
            ])
            
            st.dataframe(df_preview, use_container_width=True)

            changable_count = sum(1 for k, v in rename_map.items() if k != v)

            if changable_count > 0:
                if st.button(f"🚀 確定執行批次改名 ({changable_count} 個檔案)", type="primary", key="btn_rename"):
                    success_count = 0
                    error_count = 0
                    
                    for old_f, new_f in rename_map.items():
                        if old_f == new_f:
                            continue
                        
                        old_path = os.path.join(folder_path, old_f)
                        new_path = os.path.join(folder_path, new_f)
                        
                        try:
                            os.rename(old_path, new_path)
                            success_count += 1
                        except Exception as e:
                            st.error(f"修改 {old_f} 失敗: {e}")
                            error_count += 1
                    
                    if success_count > 0:
                        st.balloons()
                        st.success(f"🎉 成功修改 {success_count} 個檔案名稱！")
                        st.rerun()
            else:
                st.info("沒有需要修改的檔案名稱。")

    elif folder_path:
        st.error("❌ 找不到該資料夾路徑，請確認路徑輸入正確。")


# ==========================================
# Tab 2: 檔案掃描與雙 Excel 遺漏比對 (原 check_2.py)
# ==========================================
with tab2:
    st.header("📊 本機檔案掃描登記 ➔ 雙 Excel 遺漏交叉比對系統")
    st.markdown("""
    本功能提供一站式自動化比對流程：
    1. **輸入資料夾路徑**：自動掃描並清理本機/伺服器檔案名稱（去除副檔名與規格化編號）。
    2. **上傳主應有清單**：上傳包含應有檔案編號的 Excel（如 `清單2.xlsx`）。
    3. **一鍵產出雙報告**：同時下載「實體檔案登記表」與「遺漏比對報告」。
    """)

    st.subheader("1️⃣ 輸入本機 / 伺服器資料夾路徑")
    raw_paths_input = st.text_area(
        "請貼上資料夾路徑（例如: C:\\PDF_Folder 或 /path/to/folder），多筆請分行貼上：",
        height=100,
        placeholder="C:\\PDF_Folder\nC:\\Users\\User\\Documents\\2024_PDFs",
        key="check_paths"
    )

    st.subheader("2️⃣ 上傳【主清單 / 應有清單】(.xlsx)")
    uploaded_master = st.file_uploader("請上傳包含各年份/類別應有檔案編號的 Excel", type=["xlsx"], key="master_check")

    if raw_paths_input.strip() and uploaded_master:
        if st.button("🚀 開始掃描登記並比對遺漏檔案", type="primary", key="btn_check"):
            with st.spinner("正在掃描本機檔案並進行交叉比對..."):
                lines = [line.strip().strip('"').strip("'") for line in raw_paths_input.splitlines() if line.strip()]
                file_paths = []

                for path in lines:
                    if os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for f in files:
                                file_paths.append(os.path.join(root, f))
                    elif os.path.isfile(path):
                        file_paths.append(path)

                if not file_paths:
                    st.error("❌ 未在指定路徑中找到任何有效的檔案，請檢查輸入的路徑是否正確！")
                else:
                    records = []
                    actual_filenames = set()

                    for p in file_paths:
                        try:
                            full_name = os.path.basename(p)
                            size_bytes = os.path.getsize(p)
                            name_without_ext, ext = os.path.splitext(full_name)
                            ext = ext.lstrip(".").lower()

                            if size_bytes < 1024:
                                size_fmt = f"{size_bytes} B"
                            elif size_bytes < 1024 * 1024:
                                size_fmt = f"{size_bytes / 1024:.2f} KB"
                            else:
                                size_fmt = f"{size_bytes / (1024 * 1024):.2f} MB"

                            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(p))
                            time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

                            norm_item = name_without_ext.replace('-', '_').strip()
                            if norm_item:
                                actual_filenames.add(norm_item)

                            records.append({
                                "檔案名稱 (不含副檔名)": name_without_ext,
                                "標準化編號": norm_item,
                                "副檔名": ext,
                                "大小 (Bytes)": size_bytes,
                                "格式化大小": size_fmt,
                                "登記時間": time_str
                            })
                        except Exception as e:
                            pass

                    df_registered = pd.DataFrame(records)

                    df_master = pd.read_excel(uploaded_master)
                    summary_data = []
                    missing_details = {}

                    for col in df_master.columns:
                        year = str(col).replace('清單', '').strip()
                        raw_items = df_master[col].dropna().astype(str).str.strip().tolist()
                        unique_master_items = sorted(list(set([x.replace('-', '_') for x in raw_items])))
                        
                        missing = [x for x in unique_master_items if x not in actual_filenames]
                        
                        total_unique = len(unique_master_items)
                        missing_count = len(missing)
                        found_count = total_unique - missing_count
                        
                        summary_data.append({
                            '年份/類別': year,
                            '應有數量(不重複)': total_unique,
                            '現有數量': found_count,
                            '遺漏數量': missing_count
                        })
                        missing_details[year] = missing

                    summary_df = pd.DataFrame(summary_data)

                    st.success(f"✅ 成功掃描本機 {len(records)} 個檔案，並完成主清單交叉比對！")

                    st.divider()
                    st.subheader("📊 1. 檔案遺漏比對總覽")
                    st.dataframe(summary_df, use_container_width=True)
                    st.warning(f"⚠️ 總計遺漏數量：{summary_df['遺漏數量'].sum()} 個檔案")

                    col_dl1, col_dl2 = st.columns(2)

                    reg_output = io.BytesIO()
                    with pd.ExcelWriter(reg_output, engine='openpyxl') as writer:
                        df_registered.to_excel(writer, sheet_name="檔案登記清單", index=False)
                    reg_output.seek(0)

                    with col_dl1:
                        st.download_button(
                            label="📥 下載本機實體檔案登記表 (.xlsx)",
                            data=reg_output,
                            file_name="本機實體檔案登記清單.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_reg"
                        )

                    report_output = io.BytesIO()
                    with pd.ExcelWriter(report_output, engine='openpyxl') as writer:
                        summary_df.to_excel(writer, sheet_name='統計總覽', index=False)
                        max_len = max([len(m) for m in missing_details.values()]) if missing_details else 0
                        excel_style_dict = {}
                        for year, m_list in missing_details.items():
                            excel_style_dict[f"{year}遺漏清單"] = m_list + [None] * (max_len - len(m_list))
                        missing_df = pd.DataFrame(excel_style_dict)
                        missing_df.to_excel(writer, sheet_name='遺漏明細', index=False)
                    report_output.seek(0)

                    with col_dl2:
                        st.download_button(
                            label="📥 下載遺漏比對報告 (.xlsx)",
                            data=report_output,
                            file_name="檔案遺漏比對報告.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_report"
                        )

                    st.subheader("📋 各年份/類別遺漏明細預覽")
                    for year, missing_list in missing_details.items():
                        with st.expander(f"📅 {year}（共遺漏 {len(missing_list)} 個）"):
                            if missing_list:
                                st.write(", ".join(missing_list))
                            else:
                                st.success("無遺漏檔案")

    elif not raw_paths_input.strip():
        st.info("👆 請輸入要掃描的本機或伺服器資料夾路徑。")
    elif not uploaded_master:
        st.info("👆 請上傳【主清單 / 應有清單】(.xlsx)。")