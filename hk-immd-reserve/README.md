# 香港入境事务处身份证预约工具

> 自动化预约香港身份证办理服务

## 📋 功能特点

- ✅ 自动填写预约信息
- ✅ 自动选择办事处/日期/时间
- ✅ 支持多人并发预约
- ✅ 自动截图保存确认页面
- ✅ 支持指定日期/时间或选最早

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd /Users/narain/.openclaw/workspace/hk-immd-reserve

# 安装 browser-use（已安装可跳过）
pip3 install --break-system-packages browser-use
```

### 2. 编辑预约信息

**单人版** - 编辑 `hk_immd_reserve.py`：

```python
# 修改这部分
result = await book_hk_immd_appointment(
    name="張三",  # 繁体中文姓名
    id_number="A1234567",  # 身份证号
    phone="91234567",  # 电话
    email="test@example.com",  # 电邮
    office="灣仔",  # 办事处
    date=None,  # 指定日期或 None
    time=None,  # 指定时间或 None
    headed=True,  # 是否显示浏览器
)
```

**多人版** - 编辑 `hk_immd_multi.py`：

```python
# 修改 APPLICANTS 列表
APPLICANTS = [
    {
        "name": "張三",
        "id": "A1234567",
        "phone": "91234567",
        "email": "zhang@example.com",
        "office": "灣仔"
    },
    # ... 添加更多人
]
```

### 3. 运行脚本

**单人版**：

```bash
python3 hk_immd_reserve.py
```

**多人版**：

```bash
python3 hk_immd_multi.py
```

## 📁 输出文件

- `appointment_姓名.png` - 预约确认截图
- 终端输出预约编号

## 🎯 办事处列表

- 灣仔
- 觀塘
- 長沙灣
- 荃灣
- 沙田
- 大埔
- 屯門
- 元朗

## ⚙️ 高级选项

### 使用已有 Chrome Profile

编辑脚本，在 Agent 初始化前添加：

```python
import os
os.environ['BROWSER_USE_PROFILE'] = 'Default'
```

### 后台运行（不显示浏览器）

```python
headed=False  # 修改此参数
```

### 指定日期和时间

```python
date="2026-04-15"  # 格式：YYYY-MM-DD
time="10:00"       # 格式：HH:MM
```

## ⚠️ 注意事项

1. **繁体中文** - 姓名必须用繁体中文
2. **身份证号** - 格式：字母 +7 位数字（如 A1234567）
3. **电话** - 8 位数字（如 91234567）
4. **并发限制** - 建议最多 5 个同时，避免被封锁
5. **验证码** - 如遇验证码，可能需要手动处理

## 🔧 故障排查

### 问题 1：browser-use 未找到

```bash
# 检查安装
which browser-use

# 重新安装
pip3 install --break-system-packages browser-use
```

### 问题 2：Chrome 未找到

```bash
# 检查 Chrome 位置
ls -la /Applications/ | grep -i chrome

# 确保 Chrome 已安装
```

### 问题 3：预约失败

- 检查网络连接
- 确认信息格式正确
- 查看终端错误信息
- 尝试手动访问网站确认是否正常

## 📞 官方信息

- **网站**：https://www.immd.gov.hk
- **电话预约**：2598 0888
- **预约期**：96 个工作天

## ⚖️ 法律声明

本工具仅供学习研究使用。使用本工具预约时，请确保：

1. 提供的信息真实准确
2. 遵守香港入境事务处规定
3. 不用于商业牟利
4. 不影响系统正常运行

---

**版本**: 1.0  
**更新时间**: 2026-04-06
