"""
邮箱服务类
处理邮箱相关的业务逻辑：注册、验证码发送、邮箱绑定等
"""

import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
from typing import Optional

from app.config import settings
from app.constant import SMSSendBiz
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.services.cache.sys import VerifyCodeCache


class EmailService:
    """邮箱服务类"""

    def __init__(self):
        # 邮箱服务配置（需要在配置文件中添加相应配置）
        self.smtp_server = settings.EMAIL_SMTP_SERVER
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.sender_email = settings.EMAIL_SENDER
        self.sender_password = settings.EMAIL_PASSWORD

    def generate_verify_code(self, length: int = 6) -> str:
        """
        生成验证码

        :param length: 验证码长度，默认6位
        :return: 验证码字符串
        """
        return "".join([str(secrets.randbelow(10)) for _ in range(length)])

    async def send_verify_code(self, email: str, biz: SMSSendBiz) -> str:
        """
        发送验证码到指定邮箱

        :param email: 接收邮箱
        :param biz: 业务场景（注册、登录、重置密码等）
        :return: 验证码
        """
        # 生成验证码
        code = self.generate_verify_code()

        # 缓存验证码（5分钟过期）
        await VerifyCodeCache(biz, email).add(code, expire=300)

        # 发送邮件
        try:
            await self._send_email(
                to_email=email,
                subject=self._get_email_subject(biz),
                body=self._get_email_body(code, biz),
            )
        except Exception:
            raise AuthException(code=AppCode.EMAIL_SEND_FAILED, errmsg="邮件发送失败")

        return code

    async def verify_code(self, email: str, code: str, biz: SMSSendBiz) -> bool:
        """
        验证邮箱验证码

        :param email: 邮箱
        :param code: 验证码
        :param biz: 业务场景
        :return: 验证是否成功
        """
        try:
            await VerifyCodeCache(biz, email).validate(code)
            return True
        except Exception:
            raise AuthException(code=AppCode.VERIFY_CODE_ERROR, errmsg="验证码错误或已过期")

    async def _send_email(self, to_email: str, subject: str, body: str):
        """
        实际发送邮件的方法

        :param to_email: 收件人邮箱
        :param subject: 邮件主题
        :param body: 邮件内容
        """
        # 如果没有配置邮件服务，则跳过实际发送（开发环境）
        if not self.sender_email or not self.sender_password:
            print(f"[DEV MODE] 邮件验证码发送到 {to_email}: {body}")
            return

        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to_email

        # 添加邮件正文
        html_content = f"""
        <html>
            <body>
                <div style="padding: 20px; font-family: Arial, sans-serif;">
                    <h2 style="color: #333;">验证码</h2>
                    <p style="font-size: 16px; color: #666;">
                        您的验证码是：
                    </p>
                    <div style="font-size: 32px; font-weight: bold; color: #007bff; padding: 20px; background-color: #f8f9fa; border-radius: 5px; display: inline-block;">
                        {body}
                    </div>
                    <p style="font-size: 14px; color: #999; margin-top: 20px;">
                        验证码有效期为5分钟，请勿泄露给他人。
                    </p>
                </div>
            </body>
        </html>
        """

        part = MIMEText(html_content, "html")
        message.attach(part)

        # 发送邮件
        try:
            # 或使用smtplib.SMTP方式
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
                server.quit()
        except Exception as e:
            print(f"邮件发送失败: {str(e)}")
            raise

    def _get_email_subject(self, biz: SMSSendBiz) -> str:
        """
        根据业务场景获取邮件主题

        :param biz: 业务场景
        :return: 邮件主题
        """
        subject_mapping = {
            SMSSendBiz.SIGN: "注册验证码",
            SMSSendBiz.LOGIN: "登录验证码",
            SMSSendBiz.SET_PWD: "重置密码验证码",
            SMSSendBiz.BIND_PHONE: "绑定手机号验证码",
            SMSSendBiz.REVOKE: "账号注销验证码",
        }
        return subject_mapping.get(biz, "验证码")

    def _get_email_body(self, code: str, biz: SMSSendBiz) -> str:
        """
        获取邮件正文（验证码）

        :param code: 验证码
        :param biz: 业务场景
        :return: 邮件正文
        """
        return code


# 创建全局实例
email_service = EmailService()
