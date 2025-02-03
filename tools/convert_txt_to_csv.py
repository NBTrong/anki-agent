import csv
from pathlib import Path

def convert_txt_to_csv(input_file, output_file):
    # Đọc file txt và chuyển thành csv
    with open(input_file, 'r', encoding='utf-8') as txt_file:
        # Đọc tất cả các dòng từ file txt
        lines = txt_file.readlines()
        
        # Mở file csv để ghi
        with open(output_file, 'w', encoding='utf-8', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            
            # Viết header cho file CSV
            headers = ['Kanji', 'Meaning']
            csv_writer.writerow(headers)
            
            # Xử lý từng dòng
            for line in lines:
                # Bỏ qua dòng trống
                if not line.strip():
                    continue
                    
                # Tách các trường dữ liệu bằng tab
                fields = line.strip().split('\t')
                
                # Lọc bỏ các phần tử rỗng
                fields = [field for field in fields if field]
                
                if len(fields) >= 2:
                    kanji = fields[0]
                    meaning = fields[1].strip('"""')  # Loại bỏ dấu ngoặc kép
                    
                    # Ghi dòng vào file CSV
                    csv_writer.writerow([kanji, meaning])

if __name__ == "__main__":
    input_file = Path(__file__).parent.parent / "data" / "goi_n3.txt"
    output_file = Path(__file__).parent.parent / "data" / "goi_n3.csv"  # Tên file output mong muốn
    convert_txt_to_csv(input_file, output_file)
