# 公司编码规范

> **版本**: 1.0  
> **作者**: 年年 🎀  
> **创建时间**: 2026-04-05  
> **适用 Agent**: 玄机（开发工程师）/霓裳（前端开发）  
> **触发条件**: 自动触发（检测到代码文件）/手动触发（@code-style）

---

## 🎯 适用范围

本规范适用于 OpenClaw 项目的所有代码，包括：
- Python 后端代码
- JavaScript/TypeScript 前端代码
- Shell 脚本

---

## 📝 Python 编码规范

### 命名规范

#### 类命名
```python
# ✅ 正确：大驼峰命名（PascalCase）
class UserService:
    pass

class OrderController:
    pass

# ❌ 错误：小写/下划线命名
class user_service:
    pass

class order_controller:
    pass
```

#### 函数/方法命名
```python
# ✅ 正确：小写 + 下划线（snake_case）
def get_user_by_id(user_id):
    pass

def create_order(order_data):
    pass

# ❌ 错误：大驼峰/纯小写
def GetUserById(user_id):
    pass

def get(user_id):  # 太简短，无意义
    pass
```

#### 变量命名
```python
# ✅ 正确：描述性命名
user_name = "张三"
order_list = []
total_count = 0

# ❌ 错误：无意义/太简短
name = "张三"  # 什么 name？
list = []  # 什么的 list？
count = 0  # 什么的 count？

# ❌ 错误：使用内置关键字
list = []  # list 是内置类型
str = "hello"  # str 是内置类型
```

#### 常量命名
```python
# ✅ 正确：全大写 + 下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"

# ❌ 错误：小写
max_retry_count = 3  # 常量应该大写
```

### 代码格式

#### 缩进
```python
# ✅ 正确：4 个空格
def hello():
    print("Hello")  # 4 个空格缩进

# ❌ 错误：Tab/2 个空格
def hello():
	print("Hello")  # Tab
```

#### 行宽
```python
# ✅ 正确：最大 120 字符
long_variable_name = some_function(arg1, arg2, arg3, arg4, arg5)

# 超长换行（在运算符前）
result = (some_long_variable_name + another_long_variable_name
          + yet_another_long_variable_name)

# ❌ 错误：超过 120 字符
very_very_very_very_very_very_very_very_very_very_very_very_very_long_line = True  # 太长了
```

#### 空行
```python
# ✅ 正确：
# - 类成员间空 1 行
# - 方法间空 1 行
# - 逻辑块间空 1 行
class UserService:
    def __init__(self):
        self.users = []
    
    def get_user(self, user_id):
        # 逻辑块间空 1 行
        if not user_id:
            return None
        
        for user in self.users:
            if user.id == user_id:
                return user
        
        return None
    
    def create_user(self, name):
        pass

# ❌ 错误：没有空行/太多空行
class UserService:
    def __init__(self):
        self.users = []
    def get_user(self, user_id):  # 方法间没有空行
        pass


    def create_user(self, name):  # 太多空行
        pass
```

### 注释规范

#### 类注释
```python
# ✅ 正确：Docstring 格式
class UserService:
    """
    用户服务类
    
    负责用户相关的业务逻辑，包括：
    1. 用户注册/登录
    2. 用户信息管理
    3. 用户权限控制
    
    Attributes:
        users (list): 用户列表
        db (Database): 数据库连接
    
    Example:
        >>> service = UserService()
        >>> user = service.get_user(1)
    """
    pass
```

#### 函数注释
```python
# ✅ 正确：完整的 Docstring
def get_user_by_id(user_id: int) -> User:
    """
    根据 ID 获取用户
    
    Args:
        user_id (int): 用户 ID，不能为空
    
    Returns:
        User: 用户对象，如果不存在返回 None
    
    Raises:
        ValueError: 当 user_id 为空时抛出
    
    Example:
        >>> user = get_user_by_id(1)
        >>> print(user.name)
    """
    if not user_id:
        raise ValueError("user_id 不能为空")
    
    # ... 实现
```

#### 行内注释
```python
# ✅ 正确：解释为什么（不是解释是什么）
if retry_count > MAX_RETRY_COUNT:
    # 超过最大重试次数，停止重试
    raise RetryExceededException()

# 好的注释
total = sum(prices)  # 计算总价，用于后续折扣计算

# ❌ 错误：解释是什么（代码已经很清楚）
i += 1  # i 加 1
return result  # 返回结果
```

### 最佳实践

#### 异常处理
```python
# ✅ 正确：捕获具体异常
try:
    user = User.objects.get(id=user_id)
except User.DoesNotExist:
    logger.warning(f"用户不存在：{user_id}")
    return None
except DatabaseError as e:
    logger.error(f"数据库错误：{e}")
    raise

# ❌ 错误：捕获所有异常
try:
    user = User.objects.get(id=user_id)
except Exception:  # 太宽泛
    pass  # 吞异常
```

#### 资源管理
```python
# ✅ 正确：使用上下文管理器
with open('file.txt', 'r') as f:
    content = f.read()

with database.connection() as conn:
    conn.execute(query)

# ❌ 错误：忘记关闭资源
f = open('file.txt', 'r')
content = f.read()
# 忘记 f.close()
```

#### 类型提示
```python
# ✅ 正确：使用类型提示
from typing import List, Dict, Optional

def get_users(user_ids: List[int]) -> List[User]:
    pass

def get_user(user_id: int) -> Optional[User]:
    pass

def get_user_data() -> Dict[str, any]:
    pass

# ❌ 错误：没有类型提示
def get_users(user_ids):  # 什么类型？
    pass
```

---

## 📝 JavaScript/TypeScript 编码规范

### 命名规范

#### 类/组件命名
```typescript
// ✅ 正确：大驼峰命名（PascalCase）
class UserService {
}

const UserProfile: React.FC = () => {
}

// ❌ 错误：小写
class userService {
}
```

#### 函数/变量命名
```typescript
// ✅ 正确：小驼峰命名（camelCase）
function getUserById(userId: number) {
}

const userName = "张三";
const orderList: Order[] = [];

// ❌ 错误：大驼峰/下划线
function GetUserById(userId: number) {
}

const user_name = "张三";  // Python 风格
```

#### 常量命名
```typescript
// ✅ 正确：全大写 + 下划线
const MAX_RETRY_COUNT = 3;
const API_VERSION = "v1";

// ❌ 错误：小写
const max_retry_count = 3;  // 常量应该大写
```

### 代码格式

#### 缩进
```typescript
// ✅ 正确：2 个空格
function hello() {
  console.log("Hello");  // 2 个空格
}

// ❌ 错误：4 个空格/Tab
function hello() {
    console.log("Hello");  // 4 个空格（JS 社区习惯 2 个）
}
```

#### 分号
```typescript
// ✅ 正确：统一使用分号
const name = "张三";
function hello() {
  console.log("Hello");
}

// 或者统一不使用分号（项目统一即可）
const name = "张三"
function hello() {
  console.log("Hello")
}
```

### TypeScript 类型规范

#### 接口定义
```typescript
// ✅ 正确：清晰的接口定义
interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

// ❌ 错误：any 类型
interface User {
  id: any;  // 应该用 number
  name: any;  // 应该用 string
}
```

#### 泛型使用
```typescript
// ✅ 正确：使用泛型
function getData<T>(url: string): Promise<T> {
}

// ❌ 错误：使用 any
function getData(url: string): Promise<any> {
}
```

---

## 📝 Shell 脚本规范

### 脚本头
```bash
#!/bin/bash
#
# 脚本名称：deploy.sh
# 描述：部署脚本
# 作者：年年
# 创建时间：2026-04-05
# 用法：./deploy.sh [environment]
#
```

### 变量命名
```bash
# ✅ 正确：大写常量，小写变量
readonly MAX_RETRY=3
deploy_env="production"

# ❌ 错误：混用
max_retry=3  # 常量应该大写
DEPLOY_ENV="production"  # 变量应该小写
```

### 错误处理
```bash
# ✅ 正确：检查返回值
set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错
set -o pipefail  # 管道中任何命令失败都算失败

# 检查命令执行结果
if ! command -v git &> /dev/null; then
    echo "错误：git 未安装"
    exit 1
fi

# ❌ 错误：不检查返回值
some_command  # 失败了也不知道
another_command
```

---

## 🎯 代码审查检查清单

### 命名检查
- [ ] 类名使用大驼峰
- [ ] 函数/变量使用小驼峰/蛇形
- [ ] 常量使用全大写
- [ ] 命名描述性，不简短

### 格式检查
- [ ] 缩进一致（Python 4 空格，JS 2 空格）
- [ ] 行宽不超过 120 字符
- [ ] 适当的空行分隔

### 注释检查
- [ ] 类/函数有 Docstring
- [ ] 行内注释解释为什么（不是是什么）
- [ ] 注释与代码同步更新

### 最佳实践
- [ ] 异常处理合理
- [ ] 资源及时关闭
- [ ] 使用类型提示（Python）/类型定义（TS）
- [ ] 无魔法数字

---

## 📚 参考资源

- [Python PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)

---

**🎀 创建者**: 年年  
**📅 创建时间**: 2026-04-05  
**📁 存放位置**: 🎀 年年 - 大总管 目录 → Skills  
**🔄 版本**: v1.0