import pyttsx3

# Khởi tạo engine
engine = pyttsx3.init()

# Lấy danh sách tất cả các giọng nói
voices = engine.getProperty('voices')

# # In ra thông tin của từng giọng nói
# for idx, voice in enumerate(voices):
#     print(f"Voice #{idx}")
#     print(f" - ID: {voice.id}")
#     print(f" - Name: {voice.name}")
#     print(f" - Languages: {voice.languages}")
#     print(f" - Gender: {voice.gender}")
#     print("------------------------")

# Nếu muốn thử một giọng nói cụ thể
# Thay đổi voice_index tương ứng với giọng tiếng Nhật bạn tìm được
voice_index = 26  # Thay đổi số này
engine.setProperty('voice', voices[voice_index].id)
engine.say("探します、捜します")
engine.runAndWait()