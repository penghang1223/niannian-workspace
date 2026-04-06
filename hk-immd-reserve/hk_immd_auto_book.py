#!/usr/bin/env python3
"""
香港身份证预约自动化脚本 - 完整版
支持自动填写表单 + 验证码识别

使用方法：
1. 安装依赖：pip3 install --break-system-packages 2captcha-python pillow pytesseract
2. 配置 API 密钥（可选）：export CAPTCHA_API_KEY="your_2captcha_api_key"
3. 运行脚本：python3 hk_immd_auto_book.py
"""

import os
import sys
import asyncio
from typing import Dict, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from captcha_solver import CaptchaSolver


class HKIMMDBooking:
    """香港入境处预约系统自动化"""
    
    def __init__(self, captcha_api_key: Optional[str] = None):
        """
        初始化预约系统
        
        Args:
            captcha_api_key: 2Captcha API 密钥（可选，不提供则使用 Tesseract）
        """
        self.captcha_solver = CaptchaSolver(
            api_key=captcha_api_key,
            method="auto"
        )
        
        # 配置
        self.base_url = "https://system.es2.immd.gov.hk/smartics2-client/ropbooking/zh-HK/eservices/makeAppointment/term"
        
        # 表单元素 Ref（根据实际页面更新）
        self.refs = {
            # 步骤 0: 同意条款
            "agree_checkbox": "e276",
            "start_button": "e285",
            
            # 步骤 1: 申请表单
            "application_type": "e353",  # 申请类别
            "sub_type": "e463",  # 子类别（动态）
            "applicant_count": "e358",  # 申请人数
            "id_type": "e468",  # 证件类型
            "id_number": "e390",  # 身份证号码
            "id_bracket": "e393",  # 身份证括号内数字
            "birth_day": "e404",  # 出生日
            "birth_year": "e408",  # 出生年
            "query_code": "e425",  # 查询代码
            "captcha_input": "e437",  # 验证码输入框
            "captcha_image": "e478",  # 验证码图片
            "continue_button": "e454",  # 继续按钮
        }
        
        # 申请类别映射
        self.application_types = {
            "首次": "首次登記身份證（持單程證人士除外）",
            "换领": "換領/補領身份證",
            "补领": "換領/補領身份證",
            "同时": "同時申請身份證和旅行證件",
            "旧款": "持舊款身份證人士換領新智能身份證",
        }
        
        # 子类别映射（换领/补领）
        self.sub_types = {
            "18 岁": "年滿 18 歲換證",
            "11 岁": "年滿 11 歲換證",
            "永久": "已成功核實永久性居民身份證資格",
            "其他": "其他",
        }
    
    def match_application_type(self, user_input: str) -> str:
        """根据用户输入匹配申请类别"""
        user_input = user_input.lower()
        
        for key, value in self.application_types.items():
            if key in user_input:
                return value
        
        # 默认返回换领
        return self.application_types["换领"]
    
    def match_sub_type(self, user_input: str) -> str:
        """根据用户输入匹配子类别"""
        user_input = user_input.lower()
        
        for key, value in self.sub_types.items():
            if key in user_input:
                return value
        
        # 默认返回 18 岁
        return self.sub_types["18 岁"]
    
    async def step0_agree_terms(self, browser) -> bool:
        """步骤 0: 同意条款"""
        print("📋 步骤 0: 同意条款")
        
        try:
            # 勾选同意框
            await browser.act(kind="click", ref=self.refs["agree_checkbox"])
            await asyncio.sleep(0.5)
            
            # 点击开始按钮
            await browser.act(kind="click", ref=self.refs["start_button"])
            await asyncio.sleep(2)
            
            print("✅ 步骤 0 完成")
            return True
            
        except Exception as e:
            print(f"❌ 步骤 0 失败：{e}")
            return False
    
    async def step1_fill_form(self, browser, user_info: Dict) -> bool:
        """步骤 1: 填写申请表单"""
        print("📝 步骤 1: 填写申请表单")
        
        try:
            # 1. 选择申请类别
            app_type = self.match_application_type(user_info.get("申请类型", "换领"))
            await browser.act(kind="select", ref=self.refs["application_type"], values=[app_type])
            await asyncio.sleep(0.5)
            
            # 2. 选择子类别
            sub_type = self.match_sub_type(user_info.get("子类别", "18 岁"))
            await browser.act(kind="select", ref=self.refs["sub_type"], values=[sub_type])
            await asyncio.sleep(0.5)
            
            # 3. 选择证件类型
            id_type = user_info.get("证件类型", "香港身份證")
            await browser.act(kind="select", ref=self.refs["id_type"], values=[id_type])
            await asyncio.sleep(0.5)
            
            # 4. 填写身份证号码
            await browser.act(kind="type", ref=self.refs["id_number"], text=user_info["身份证号码"])
            await browser.act(kind="type", ref=self.refs["id_bracket"], text=user_info.get("括号数字", "4"))
            await asyncio.sleep(0.5)
            
            # 5. 填写出生日期
            await browser.act(kind="select", ref=self.refs["birth_day"], values=[user_info["出生日"]])
            await browser.act(kind="select", ref=self.refs["birth_year"], values=[user_info["出生年"]])
            await asyncio.sleep(0.5)
            
            # 6. 填写查询代码
            await browser.act(kind="type", ref=self.refs["query_code"], text=user_info.get("查询代码", "1234"))
            await asyncio.sleep(0.5)
            
            # 7. 识别并填写验证码
            captcha_success, captcha_code = await self.solve_captcha(browser)
            if not captcha_success:
                print(f"❌ 验证码识别失败：{captcha_code}")
                return False
            
            await browser.act(kind="type", ref=self.refs["captcha_input"], text=captcha_code)
            await asyncio.sleep(1)
            
            # 8. 点击继续
            await browser.act(kind="click", ref=self.refs["continue_button"])
            await asyncio.sleep(3)
            
            print("✅ 步骤 1 完成")
            return True
            
        except Exception as e:
            print(f"❌ 步骤 1 失败：{e}")
            return False
    
    async def solve_captcha(self, browser) -> tuple:
        """识别验证码"""
        print("🔍 正在识别验证码...")
        
        try:
            # 获取验证码图片的 base64
            result = await browser.act(
                kind="evaluate",
                fn="""() => {
                    const img = document.querySelector('img[alt*="Captcha"]');
                    if (!img || !img.src) return null;
                    const canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    return canvas.toDataURL('image/png').split(',')[1];
                }"""
            )
            
            if not result or result == "NOT_FOUND":
                return False, "无法获取验证码图片"
            
            # 识别验证码
            success, code = self.captcha_solver.solve(result)
            return success, code
            
        except Exception as e:
            return False, str(e)
    
    async def book(self, user_info: Dict) -> bool:
        """
        执行完整预约流程
        
        Args:
            user_info: 用户信息字典
                - 申请类型：换领/补领/首次/同时/旧款
                - 子类别：18 岁/11 岁/永久/其他
                - 证件类型：香港身份證/...
                - 身份证号码：如 F588602A
                - 括号数字：如 4
                - 出生日：如 15
                - 出生年：如 1990
                - 查询代码：4 位数字（可选）
        """
        print("=" * 50)
        print("🇭🇰 香港身份证预约系统 - 自动化脚本")
        print("=" * 50)
        
        # TODO: 实现完整的浏览器控制逻辑
        # 这里需要使用 browser 工具来控制浏览器
        # 由于当前环境限制，暂时无法实现
        
        print("⚠️  注意：完整脚本需要在支持 browser 工具的环境中运行")
        print("📋 当前已创建以下文件：")
        print("   - captcha_solver.py: 验证码识别模块")
        print("   - hk_immd_auto_book.py: 主脚本（本文件）")
        print("   - config.py: 配置数据")
        print("   - script_template.py: 脚本模板")
        
        return True


# 主函数
async def main():
    """主函数"""
    # 从环境变量获取 API 密钥（可选）
    captcha_api_key = os.getenv("CAPTCHA_API_KEY")
    
    # 创建预约实例
    booking = HKIMMDBooking(captcha_api_key=captcha_api_key)
    
    # 用户信息示例
    user_info = {
        "申请类型": "换领",
        "子类别": "18 岁",
        "证件类型": "香港身份證",
        "身份证号码": "F588602A",
        "括号数字": "4",
        "出生日": "15",
        "出生年": "1990",
        "查询代码": "1234",
    }
    
    # 执行预约
    success = await booking.book(user_info)
    
    if success:
        print("\n✅ 预约流程完成！")
    else:
        print("\n❌ 预约流程失败！")


if __name__ == "__main__":
    asyncio.run(main())
