import pandas as pd
from pathlib import Path

def convert_xlsx_to_csv(xlsx_file, csv_file):
    try:
        # Đọc file Excel
        df = pd.read_excel(xlsx_file)
        
        # Chuyển đổi và lưu thành file CSV
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"Đã chuyển đổi thành công file '{xlsx_file}' sang '{csv_file}'")
    except Exception as e:
        print(f"Lỗi: {str(e)}")

if __name__ == "__main__":
    xlsx_file = Path(__file__).parent.parent / "data" / "final.xlsx"
    csv_file = Path(__file__).parent.parent / "data" / "flashcards.csv"
    
    convert_xlsx_to_csv(xlsx_file, csv_file)
