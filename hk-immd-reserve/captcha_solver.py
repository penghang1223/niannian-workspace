#!/usr/bin/env python3
"""
香港身份证预约系统 - 验证码识别模块
支持多种识别方式：
1. 2Captcha API（推荐，识别率高）
2. Tesseract OCR（本地，免费但识别率较低）
"""

import base64
import time
from typing import Optional, Tuple

# 方式 1: 2Captcha API（推荐）
try:
    from twocaptcha import TwoCaptcha
    HAS_2CAPTCHA = True
except ImportError:
    HAS_2CAPTCHA = False

# 方式 2: Tesseract OCR（本地）
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class CaptchaSolver:
    """验证码识别器"""
    
    def __init__(self, api_key: Optional[str] = None, method: str = "auto"):
        """
        初始化验证码识别器
        
        Args:
            api_key: 2Captcha API 密钥（可选）
            method: 识别方法 - "2captcha", "tesseract", "auto"
        """
        self.api_key = api_key
        self.method = method
        
        # 自动选择最佳方法
        if method == "auto":
            if HAS_2CAPTCHA and api_key:
                self.method = "2captcha"
            elif HAS_TESSERACT:
                self.method = "tesseract"
            else:
                raise RuntimeError("没有可用的验证码识别方法")
        
        print(f"✅ 验证码识别器已初始化，使用方法：{self.method}")
    
    def solve_2captcha(self, image_base64: str, timeout: int = 60) -> Tuple[bool, str]:
        """
        使用 2Captcha API 识别验证码
        
        Args:
            image_base64: 验证码图片的 base64 数据
            timeout: 超时时间（秒）
        
        Returns:
            (success, result): 成功标志和识别结果
        """
        if not HAS_2CAPTCHA:
            return False, "2Captcha 库未安装"
        
        if not self.api_key:
            return False, "缺少 2Captcha API 密钥"
        
        try:
            # 初始化求解器
            solver = TwoCaptcha(self.api_key)
            
            # 发送验证码图片
            result = solver.normal(body=image_base64)
            
            # 等待识别结果
            code = result['code']
            
            if code and len(code) >= 4:
                return True, code[:4].upper()
            else:
                return False, f"识别结果无效：{code}"
                
        except Exception as e:
            return False, f"2Captcha 错误：{str(e)}"
    
    def solve_tesseract(self, image_base64: str) -> Tuple[bool, str]:
        """
        使用 Tesseract OCR 识别验证码
        
        Args:
            image_base64: 验证码图片的 base64 数据
        
        Returns:
            (success, result): 成功标志和识别结果
        """
        if not HAS_TESSERACT:
            return False, "Tesseract 库未安装"
        
        try:
            # 解码 base64 图片
            img_data = base64.b64decode(image_base64)
            
            # 使用内存中的图片（不需要保存文件）
            from io import BytesIO
            img = Image.open(BytesIO(img_data))
            
            # 图像预处理（提高识别率）
            img = img.convert('L')  # 转灰度
            img = img.point(lambda x: 0 if x < 128 else 255)  # 二值化
            
            # OCR 识别
            config = '--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(img, config=config)
            
            # 清理结果
            code = ''.join(c for c in text if c.isalnum()).upper()[:4]
            
            if len(code) >= 3:
                return True, code
            else:
                return False, f"识别结果太短：{code}"
                
        except Exception as e:
            return False, f"Tesseract 错误：{str(e)}"
    
    def solve(self, image_base64: str) -> Tuple[bool, str]:
        """
        自动选择方法识别验证码
        
        Args:
            image_base64: 验证码图片的 base64 数据（不包含 data:image/png;base64, 前缀）
        
        Returns:
            (success, result): 成功标志和识别结果
        """
        print(f"🔍 开始识别验证码，方法：{self.method}")
        
        if self.method == "2captcha":
            success, result = self.solve_2captcha(image_base64)
        elif self.method == "tesseract":
            success, result = self.solve_tesseract(image_base64)
        else:
            return False, f"未知的识别方法：{self.method}"
        
        if success:
            print(f"✅ 验证码识别成功：{result}")
        else:
            print(f"❌ 验证码识别失败：{result}")
        
        return success, result


# 使用示例
if __name__ == "__main__":
    # 示例 1: 使用 2Captcha（需要 API 密钥）
    # solver = CaptchaSolver(api_key="YOUR_2CAPTCHA_API_KEY", method="2captcha")
    
    # 示例 2: 使用 Tesseract（本地识别）
    solver = CaptchaSolver(method="tesseract")
    
    # 示例验证码图片（需要替换为实际的 base64 数据）
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    success, code = solver.solve(test_image)
    print(f"识别结果：{code}")
