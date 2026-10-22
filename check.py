import os
import pandas as pd

def check_missing_files(excel_path, target_dir):
    """
    比對 Excel 清單與資料夾中的實體檔案，列出各年份遺漏的檔案。
    
    :param excel_path: Excel 清單檔案路徑 (例如 '清單2.xlsx')
    :param target_dir: 存放待比對檔案的資料夾路徑
    """
    if not os.path.exists(excel_path):
        print(f"錯誤：找不到 Excel 檔案 {excel_path}")
        return
        
    if not os.path.exists(target_dir):
        print(f"錯誤：找不到資料夾 {target_dir}")
        return

    # 1. 取得資料夾中所有檔案的主檔名（自動去除副檔名並統一連字號符號）
    folder_files = set()
    for f in os.listdir(target_dir):
        base_name = os.path.splitext(f)[0].replace('-', '_').strip()
        folder_files.add(base_name)

    print(f"資料夾中共有 {len(folder_files)} 個獨立檔案編號。\n")

    # 2. 讀取 Excel 清單
    df = pd.read_excel(excel_path)
    
    summary_data = []
    missing_details = {}

    # 3. 逐欄（各年份）比對
    for col in df.columns:
        year = col.replace('清單', '').strip()
        raw_items = df[col].dropna().astype(str).str.strip().tolist()
        
        # 取得不重複的 Excel 清單編號
        unique_excel_items = sorted(list(set([x.replace('-', '_') for x in raw_items])))
        
        # 找出不在資料夾中的檔案
        missing = [x for x in unique_excel_items if x not in folder_files]
        
        total_unique = len(unique_excel_items)
        found_count = total_unique - len(missing)
        missing_count = len(missing)
        
        summary_data.append({
            '年份': year,
            '應有數量(不重複)': total_unique,
            '現有數量': found_count,
            '遺漏數量': missing_count
        })
        
        missing_details[year] = missing

    # 4. 輸出統計結果
    summary_df = pd.DataFrame(summary_data)
    print("=== 比對統計總覽 ===")
    print(summary_df.to_string(index=False))
    print(f"\n總計遺漏數量：{summary_df['遺漏數量'].sum()} 個檔案\n")

    # 5. 輸出各年份遺漏明細
    print("=== 各年份遺漏檔案明細 ===")
    for year, missing_list in missing_details.items():
        print(f"\n📅 {year} 年（共遺漏 {len(missing_list)} 個）：")
        if missing_list:
            print(", ".join(missing_list))
        else:
            print("無遺漏檔案")

if __name__ == "__main__":
    # 請修改為您的 Excel 檔案路徑與存放 PDF / 檔案的實體資料夾路徑
    EXCEL_FILE = "清單2.xlsx"
    TARGET_FOLDER = "./my_files"  # 資料夾路徑
    
    check_missing_files(EXCEL_FILE, TARGET_FOLDER)