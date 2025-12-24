# 邮箱注册功能使用说明

## 概述

本项目已新增邮箱注册功能，用户可以使用邮箱进行注册。邮箱注册功能通过独立的 `EmailService` 类实现，负责验证码发送、验证等邮箱相关操作。

## 功能特性

1. **邮箱注册** - 用户使用邮箱 + 密码 + 验证码完成注册
2. **验证码发送** - 向指定邮箱发送6位数字验证码
3. **验证码验证** - 验证码有效期5分钟，存储在 Redis 中
4. **邮箱唯一性检查** - 确保同一邮箱只能注册一次

## 新增文件

- `app/services/email.py` - 邮箱服务类，处理邮箱相关业务逻辑
- `alembic/versions/add_email_unique_constraint.py` - 数据库迁移文件，添加 email 唯一约束

## 修改文件

1. **app/schemas/user.py**
   - 新增 `EmailSignSchema` - 邮箱注册的请求模型
   - 新增 `SendEmailCodeSchema` - 发送邮箱验证码的请求模型

2. **app/services/auth.py**
   - 新增 `sign_email()` 方法 - 处理邮箱注册逻辑

3. **app/services/user.py**
   - 新增 `create_by_email()` 方法 - 通过邮箱创建用户
   - 更新 `check_user_exist()` 方法，支持通过 email 查询

4. **app/models/user.py**
   - email 字段添加 unique=True 约束

5. **app/routers/v1/auth.py**
   - 新增 `POST /v1/auth/signup/email` 接口 - 邮箱注册
   - 新增 `POST /v1/auth/email/send_code` 接口 - 发送邮箱验证码

6. **app/config/__init__.py**
   - 添加邮件服务配置项（EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD）
   - 将新接口添加到白名单

## API 接口说明

### 1. 发送邮箱验证码

**接口**: `POST /v1/auth/email/send_code`

**请求参数**:
```json
{
  "email": "user@example.com",
  "biz": "sign"  // 业务场景：sign-注册, login-登录, set_pwd-重置密码
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "验证码已发送，请查收邮件",
  "data": null
}
```

### 2. 邮箱注册

**接口**: `POST /v1/auth/signup/email`

**请求参数**:
```json
{
  "email": "user@example.com",
  "pwd": "加密后的密码",  // 前端使用 RSA 加密
  "code": "123456"  // 6位数字验证码
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "注册成功",
  "data": null
}
```

## 环境配置

在 `.env` 文件中添加以下邮件服务配置（如果需要实际发送邮件）：

```bash
# 邮件服务配置
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# 注意：
# 1. Gmail 需要使用应用专用密码，而不是账户密码
# 2. 其他邮箱服务商请参考其 SMTP 配置
```

如果不配置邮件服务，系统将工作在开发模式，验证码会打印在控制台中，不会实际发送邮件。

## 数据库迁移

运行以下命令应用数据库迁移，为 email 字段添加唯一约束：

```bash
# 方式1：使用项目提供的脚本
bash scripts/db-migrate.sh

# 方式2：直接使用 alembic
alembic upgrade head
```

## 使用示例

### Python 客户端示例

```python
import requests
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# 1. 获取公钥
response = requests.get("http://localhost:8000/v1/secret/rsa_public_key")
public_key_str = response.json()["data"]["public_key"]

# 2. 加密密码
from cryptography.hazmat.backends import default_backend
public_key = serialization.load_pem_public_key(
    public_key_str.encode(), 
    backend=default_backend()
)
password = "MyPassword123"
encrypted = public_key.encrypt(
    password.encode(),
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
encrypted_pwd = base64.b64encode(encrypted).decode()

# 3. 发送验证码
response = requests.post(
    "http://localhost:8000/v1/auth/email/send_code",
    json={
        "email": "user@example.com",
        "biz": "sign"
    }
)
print(response.json())

# 4. 注册
code = input("请输入收到的验证码: ")
response = requests.post(
    "http://localhost:8000/v1/auth/signup/email",
    json={
        "email": "user@example.com",
        "pwd": encrypted_pwd,
        "code": code
    }
)
print(response.json())
```

### JavaScript/前端示例

```javascript
// 1. 发送验证码
async function sendEmailCode(email) {
  const response = await fetch('/v1/auth/email/send_code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      biz: 'sign'
    })
  });
  return await response.json();
}

// 2. 邮箱注册
async function signupByEmail(email, encryptedPassword, code) {
  const response = await fetch('/v1/auth/signup/email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      pwd: encryptedPassword,  // 需要先用 RSA 公钥加密
      code: code
    })
  });
  return await response.json();
}

// 使用示例
await sendEmailCode('user@example.com');
// 用户输入验证码后...
const result = await signupByEmail('user@example.com', encryptedPwd, '123456');
```

## 错误码说明

- `code=0` - 操作成功
- `code=ACCOUNT_EXIST` - 邮箱已被使用
- `code=CODE_ERROR` - 验证码错误或已过期
- `code=SERVER_ERROR` - 服务器错误（如邮件发送失败）

## 注意事项

1. **密码加密**: 前端需要使用 RSA 公钥加密密码后再传输
2. **验证码有效期**: 验证码5分钟后过期
3. **邮箱格式**: 邮箱会自动转为小写存储
4. **开发模式**: 如果没有配置邮件服务，验证码会打印在控制台
5. **唯一性**: 同一邮箱只能注册一次

## EmailService 类说明

`EmailService` 是专门处理邮箱相关业务的服务类，主要方法：

- `generate_verify_code(length=6)` - 生成随机验证码
- `send_verify_code(email, biz)` - 发送验证码到指定邮箱
- `verify_code(email, code, biz)` - 验证邮箱验证码
- `_send_email(to_email, subject, body)` - 实际发送邮件的底层方法

该类独立封装，便于后续扩展其他邮箱相关功能（如邮箱绑定、邮箱找回密码等）。

## 测试建议

### 单元测试
建议在 `app/tests/` 目录下添加邮箱功能的测试用例：

```python
# app/tests/api_v1/test_email_signup.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_send_email_code(client: AsyncClient):
    response = await client.post(
        "/v1/auth/email/send_code",
        json={"email": "test@example.com", "biz": "sign"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

@pytest.mark.asyncio
async def test_signup_by_email(client: AsyncClient):
    # 实现邮箱注册测试
    pass
```

## 未来扩展

可以基于 `EmailService` 类扩展以下功能：

1. 邮箱登录
2. 邮箱找回密码
3. 邮箱绑定/解绑
4. 邮箱验证（验证邮箱所有权）
5. 邮件通知功能

