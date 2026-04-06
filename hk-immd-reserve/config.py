#!/usr/bin/env python3
"""
香港身份证预约系统 - 配置数据
记录所有申请类别和选项，用于自动匹配用户需求
"""

# 申请类别
APPLICATION_TYPES = {
    "首次登記": "首次登記身份證（持單程證人士除外）",
    "換領": "換領/補領身份證",
    "補領": "換領/補領身份證",
    "同時申請": "同時申請身份證和旅行證件",
    "舊款換新": "持舊款身份證人士換領新智能身份證",
}

# 子类别（根据申请类别动态显示）
SUB_TYPES = {
    "換領/補領身份證": {
        "18 歲": "年滿 18 歲換證",
        "11 歲": "年滿 11 歲換證",
        "永久": "已成功核實永久性居民身份證資格",
        "其他": "其他",
    },
    "首次登記身份證（持單程證人士除外）": {
        # 待探索
    },
    "同時申請身份證和旅行證件": {
        # 待探索
    },
    "持舊款身份證人士換領新智能身份證": {
        # 待探索
    },
}

# 证件类型
ID_TYPES = {
    "身份證": "香港身份證",
    "出生證": "香港出生證明書",
    "回港證": "香港回港證",
    "簽證身份書": "香港簽證身份書",
    "其他": "其他旅行證件",
}

# 申请人数
APPLICANT_COUNTS = ["1", "2", "3", "4"]

# 日期选项（日）
DAYS = [f"{i:02d}" for i in range(1, 32)]

# 年份选项（1900-2026）
YEARS = [str(y) for y in range(2026, 1899, -1)]

# 办事处列表
OFFICES = {
    "灣仔": "灣仔",
    "觀塘": "觀塘",
    "長沙灣": "長沙灣",
    "荃灣": "荃灣",
    "沙田": "沙田",
    "大埔": "大埔",
    "屯門": "屯門",
    "元朗": "元朗",
}

# 验证码元素 ID（动态变化，需要运行时获取）
CAPTCHA_INPUT_REF = "e437"  # 验证码输入框
CAPTCHA_IMAGE_REF = "e443"  # 验证码图片
CONTINUE_BUTTON_REF = "e454"  # 继续按钮

# 表单元素 Ref 映射（步骤 1/5）
STEP1_REFS = {
    "application_type": "e353",  # 申请类别下拉框
    "sub_type": "e463",  # 子类别下拉框（根据申请类别动态显示）
    "applicant_count": "e358",  # 申请人数下拉框
    "id_type": "e468",  # 证件类型下拉框
    "id_number": "e390",  # 身份证号码输入框
    "id_bracket": "e393",  # 身份证括号内数字
    "birth_day": "e404",  # 出生日
    "birth_year": "e408",  # 出生年
    "query_code": "e425",  # 查询代码（4 位数字）
    "captcha": "e437",  # 验证码输入
    "continue_btn": "e454",  # 继续按钮
}

# 用户需求匹配规则
def match_application_type(user_need: str) -> str:
    """根据用户需求匹配申请类别"""
    user_need = user_need.lower()
    
    if "首次" in user_need or "第一次" in user_need:
        return APPLICATION_TYPES["首次登記"]
    elif "換領" in user_need or "换领" in user_need or "到期" in user_need:
        return APPLICATION_TYPES["換領"]
    elif "補領" in user_need or "补领" in user_need or "丢失" in user_need or "遺失" in user_need:
        return APPLICATION_TYPES["補領"]
    elif "同時" in user_need or "一起" in user_need or "both" in user_need:
        return APPLICATION_TYPES["同時申請"]
    elif "舊款" in user_need or "旧款" in user_need or "smart" in user_need.lower():
        return APPLICATION_TYPES["舊款換新"]
    else:
        # 默认返回换领
        return APPLICATION_TYPES["換領"]

def match_id_type(user_need: str) -> str:
    """根据用户需求匹配证件类型"""
    if "出生證" in user_need or "出生" in user_need:
        return ID_TYPES["出生證"]
    elif "回港證" in user_need or "回港" in user_need:
        return ID_TYPES["回港證"]
    elif "簽證" in user_need or "身份書" in user_need:
        return ID_TYPES["簽證身份書"]
    else:
        return ID_TYPES["身份證"]

# 示例使用
if __name__ == "__main__":
    # 测试匹配
    print("申请类别匹配测试:")
    test_cases = [
        "我要换领身份证",
        "第一次申请身份证",
        "身份证丢了要补领",
        "同时申请身份证和护照",
        "旧款身份证换新款",
    ]
    
    for case in test_cases:
        result = match_application_type(case)
        print(f"  {case} → {result}")
    
    print("\n所有配置数据已定义，可在脚本中导入使用")
