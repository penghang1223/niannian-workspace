# 香港身份证预约自动化系统

> 自动填写表单 + 验证码识别

## 📦 已创建文件

| 文件 | 说明 | 大小 |
|------|------|------|
| `config.py` | 配置数据（申请类别/子类别/表单元素映射） | 3KB |
| `captcha_solver.py` | 验证码识别模块（2Captcha + Tesseract） | 5KB |
| `hk_immd_auto_book.py` | 主脚本（完整自动化流程） | 8KB |
| `script_template.py` | 脚本模板（步骤记录） | 3KB |
| `README.md` | 本文档 | - |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/narain/.openclaw/workspace/hk-immd-reserve

# 安装验证码识别库
pip3 install --break-system-packages 2captcha-python pillow pytesseract

# 确保 Tesseract OCR 已安装（macOS）
brew install tesseract
```

### 2. 配置 API 密钥（可选）

**方式 1: 使用 2Captcha API（推荐，识别率 95%+）**

```bash
# 注册 2Captcha: https://2captcha.com/
# 获取 API 密钥后设置环境变量
export CAPTCHA_API_KEY="your_2captcha_api_key"
```

**方式 2: 使用 Tesseract OCR（本地免费，识别率 60-80%）**

```bash
# 无需 API 密钥，直接使用
# 识别率取决于验证码图片质量
```

### 3. 运行脚本

```bash
# 编辑用户信息
nano hk_immd_auto_book.py

# 修改 user_info 字典
user_info = {
    "申请类型": "换领",  # 换领/补领/首次/同时/旧款
    "子类别": "18 岁",   # 18 岁/11 岁/永久/其他
    "证件类型": "香港身份證",
    "身份证号码": "F588602A",
    "括号数字": "4",
    "出生日": "15",
    "出生年": "1990",
    "查询代码": "1234",  # 自选 4 位数字
}

# 运行脚本
python3 hk_immd_auto_book.py
```

## 🔧 验证码识别模块

### 支持的方法

| 方法 | 识别率 | 速度 | 成本 | 推荐度 |
|------|--------|------|------|--------|
| **2Captcha API** | 95%+ | 10-30 秒 | $0.5-3/1000 次 | ⭐⭐⭐⭐⭐ |
| **Tesseract OCR** | 60-80% | <1 秒 | 免费 | ⭐⭐⭐ |

### 使用示例

```python
from captcha_solver import CaptchaSolver

# 方式 1: 自动选择（优先 2Captcha）
solver = CaptchaSolver(api_key="YOUR_API_KEY", method="auto")

# 方式 2: 强制使用 Tesseract
solver = CaptchaSolver(method="tesseract")

# 识别验证码
image_base64 = "..."  # 验证码图片的 base64
success, code = solver.solve(image_base64)

if success:
    print(f"验证码：{code}")
else:
    print(f"识别失败：{code}")
```

## 📋 申请类别说明

### 主类别（5 种）

| 关键词 | 对应选项 |
|--------|----------|
| 首次/第一次 | 首次登記身份證（持單程證人士除外） |
| 换领/到期 | 換領/補領身份證 |
| 补领/丢失 | 換領/補領身份證 |
| 同时/一起 | 同時申請身份證和旅行證件 |
| 旧款/智能 | 持舊款身份證人士換領新智能身份證 |

### 子类别（换领/补领）

| 关键词 | 对应选项 |
|--------|----------|
| 18 岁/成年 | 年滿 18 歲換證 |
| 11 岁/儿童 | 年滿 11 歲換證 |
| 永久 | 已成功核實永久性居民身份證資格 |
| 其他 | 其他 |

## 🎯 完整流程

```
步骤 0: 同意条款
  ↓
步骤 1: 填写申请表单（5 个下拉框 + 4 个输入框 + 验证码）
  ↓
步骤 2: 选择办理地点（待实现）
  ↓
步骤 3: 选择预约时间（待实现）
  ↓
步骤 4: 确认信息（待实现）
  ↓
步骤 5: 预约完成（待实现）
```

## ⚠️ 注意事项

1. **验证码识别**
   - 政府网站验证码通常有干扰线
   - 推荐使用 2Captcha API（人工识别）
   - Tesseract 对复杂验证码识别率较低

2. **反爬措施**
   - 不要频繁请求（建议间隔 2-5 秒）
   - 使用真实 User-Agent
   - 考虑使用代理 IP

3. **法律风险**
   - 仅供学习研究使用
   - 不要用于商业牟利
   - 遵守香港入境事务处规定

## 🔑 获取 2Captcha API 密钥

1. 访问 https://2captcha.com/
2. 注册账号
3. 充值（最低$5）
4. 在 API 页面获取密钥
5. 设置环境变量：`export CAPTCHA_API_KEY="xxx"`

## 📞 官方信息

- **网站**: https://www.immd.gov.hk
- **预约网址**: https://system.es2.immd.gov.hk/smartics2-client/ropbooking/
- **电话预约**: 2598 0888
- **预约期**: 96 个工作天

## 📝 更新日志

- **2026-04-06**: 初始版本
  - ✅ 验证码识别模块（2Captcha + Tesseract）
  - ✅ 配置数据（申请类别/子类别/表单元素）
  - ✅ 主脚本框架
  - ⏳ 步骤 2-5 待实现

---

**版本**: v0.1  
**创建时间**: 2026-04-06  
**状态**: 开发中
