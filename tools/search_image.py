from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_google_api():
    """
    Thiết lập Google Custom Search API từ biến môi trường
    
    Returns:
        tuple: (service, custom_search_engine_id)
            - service: Đối tượng service của Google API
            - custom_search_engine_id: ID của Custom Search Engine
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    custom_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not custom_search_engine_id:
        raise ValueError("GOOGLE_API_KEY và GOOGLE_SEARCH_ENGINE_ID phải được cấu hình trong file .env")
        
    service = build("customsearch", "v1", developerKey=api_key)
    return service, custom_search_engine_id

def search_images(service, cx, keyword, num_images=5):
    """
    Tìm kiếm hình ảnh cho một từ khóa sử dụng Google Custom Search API
    
    Args:
        service: Đối tượng service của Google API
        cx (str): ID của Custom Search Engine
        keyword (str): Từ khóa cần tìm kiếm
        num_images (int): Số lượng hình ảnh cần tìm, mặc định là 5
    
    Returns:
        list: Danh sách các URL hình ảnh tìm được
    """
    try:
        result = service.cse().list(
            q=keyword,
            cx=cx,
            searchType='image',
            num=num_images
        ).execute()
        
        # Chỉ trả về list các URL hình ảnh
        return [item.get('link') for item in result.get('items', [])]
    except Exception as e:
        print(f"Lỗi khi tìm kiếm '{keyword}': {str(e)}")
        return []

def get_images_for_word(word, num_images=5):
    """
    Lấy danh sách URL hình ảnh cho một từ
    
    Args:
        word (str): Từ cần tìm hình ảnh
        num_images (int): Số lượng hình ảnh cần tìm, mặc định là 5
    
    Returns:
        list: Danh sách các URL hình ảnh
    """
    try:
        service, cx = setup_google_api()
        return search_images(service, cx, word, num_images)
    except Exception as e:
        print(f"Lỗi khi xử lý từ '{word}': {str(e)}")
        return []

if __name__ == "__main__":
    # Test với một từ
    word = "見ます"
    image_urls = get_images_for_word(word)
    print(f"Các URL hình ảnh cho từ '{word}':")
    for url in image_urls:
      print(url)