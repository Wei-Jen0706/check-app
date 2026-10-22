import cv2
import numpy as np

# 在迴圈讀取圖片時進行強化處理
for img_file in uploaded_images:
    try:
        image = Image.open(img_file)
        
        # 1. 轉成 OpenCV 格式
        img_np = np.array(image)
        
        # 2. 轉灰階與提高對比度
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        # 放大圖片 2 倍以利小字辨識
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 3. 執行 OCR
        text = pytesseract.image_to_string(resized, config='--psm 6')
        
        matches = re.findall(r'\b\d{4}[_-]\d{4}(?:_[A-Za-z]+)?\b', text)
        for m in matches:
            extracted_filenames.add(m.replace('-', '_').strip())
            
    except Exception as e:
        st.error(f"辨識圖片 {img_file.name} 時發生錯誤: {e}")
