#!/usr/bin/env python3
"""
香港身份证预约自动化脚本
记录所有步骤和元素选择器，用于后续自动化

当前进度：步骤 1/5 - 填写申请表单
"""

# ==================== 步骤记录 ====================

"""
步骤 0: 同意条款页面
URL: https://system.es2.immd.gov.hk/smartics2-client/ropbooking/zh-HK/eservices/makeAppointment/term
元素:
  - 同意复选框：ref=e276
  - 开始按钮：ref=e285
操作:
  1. click("e276")  # 勾选同意
  2. click("e285")  # 点击开始
"""

"""
步骤 1: 填写申请表单 (当前步骤)
URL: https://system.es2.immd.gov.hk/smartics2-client/ropbooking/zh-HK/eservices/makeAppointment/step1
元素:
  - 申请类别：ref=e353
  - 申请人数：ref=e358
  - 证件类型：ref=e385
  - 身份证号码：ref=e390
  - 身份证括号数字：ref=e393
  - 出生日：ref=e404
  - 出生年：ref=e408
  - 查询代码：ref=e425
  - 验证码：ref=e437
  - 验证码图片：ref=e443
  - 继续按钮：ref=e454
操作:
  1. select("e353", "換領/補領身份證")
  2. select("e385", "香港身份證")
  3. type("e390", "A1234567")
  4. type("e393", "4")
  5. select("e404", "15")
  6. select("e408", "1990")
  7. type("e425", "1234")
  8. type("e437", "验证码")  # 需要 OCR 识别
  9. click("e454")  # 继续
"""

"""
步骤 2: 选择办理地点 (待探索)
预期元素:
  - 办事处选择下拉框
  - 继续按钮
"""

"""
步骤 3: 选择预约时间 (待探索)
预期元素:
  - 日期选择
  - 时间段选择
  - 继续按钮
"""

"""
步骤 4: 确认 (待探索)
预期元素:
  - 信息确认
  - 确认按钮
"""

"""
步骤 5: 预约详情 (待探索)
预期元素:
  - 预约编号显示
  - 打印/保存按钮
"""

# ==================== 完整脚本模板 ====================

def book_appointment(user_info: dict):
    """
    完整预约流程
    
    user_info: {
        "name": "張三",
        "id_number": "A1234567",
        "id_bracket": "4",
        "birth_day": "15",
        "birth_year": "1990",
        "application_type": "換領/補領身份證",
        "id_type": "香港身份證",
        "query_code": "1234",
        "office": "灣仔",
    }
    """
    
    # 步骤 0: 同意条款
    browser.click("e276")  # 同意复选框
    browser.click("e285")  # 开始按钮
    wait(2)  # 等待页面加载
    
    # 步骤 1: 填写申请表单
    browser.select("e353", user_info["application_type"])  # 申请类别
    browser.select("e385", user_info["id_type"])  # 证件类型
    browser.type("e390", user_info["id_number"])  # 身份证号码
    browser.type("e393", user_info["id_bracket"])  # 括号内数字
    browser.select("e404", user_info["birth_day"])  # 出生日
    browser.select("e408", user_info["birth_year"])  # 出生年
    browser.type("e425", user_info["query_code"])  # 查询代码
    
    # 验证码识别（需要实现）
    captcha = recognize_captcha()
    browser.type("e437", captcha)
    
    browser.click("e454")  # 继续按钮
    wait(2)
    
    # 步骤 2: 选择办事处（待实现）
    # 步骤 3: 选择时间（待实现）
    # 步骤 4: 确认（待实现）
    # 步骤 5: 完成（待实现）
    
    return True

def recognize_captcha():
    """
    验证码识别函数
    
    可选方案:
    1. 使用 Tesseract OCR 本地识别
    2. 调用 2Captcha API
    3. 手动输入（测试用）
    """
    # TODO: 实现验证码识别
    return "ABCD"  # 占位符

# ==================== 下一步 ====================
"""
1. 继续探索步骤 2-5 的页面结构
2. 实现验证码识别功能
3. 测试完整流程
4. 添加错误处理和重试机制
"""
