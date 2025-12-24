import base64
import os
import traceback
import zlib
from typing import Union, Literal

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes, padding as Padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.exception import DecryptedError


class RsaCrypto:
    def __init__(self):
        self.__private_key = None
        self.__public_key = None

    def init_key(self, *, private_key: str, public_key: str = None):
        self.__private_key = self.load_private_key(private_key)
        self.__public_key = None if not public_key else self.load_public_key(public_key)

        return self

    @classmethod
    def gen_key(cls, as_str=True, **kwargs):
        key = rsa.generate_private_key(
            public_exponent=kwargs.get("public_exponent", 65537),
            key_size=kwargs.get("key_size", 2048),
            backend=default_backend(),
        )
        if as_str:
            return cls.dump_private_key(key, as_str=True), cls.dump_public_key(
                key.public_key(), as_str=True
            )
        return key, key.public_key()

    @classmethod
    def dump_public_key(cls, key, as_str=False, remove_flag=True, **kwargs):
        pem = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if as_str:
            if remove_flag:
                return "".join(pem.decode("utf-8").splitlines()[1:-1])
            return pem.decode("utf-8")
        return pem

    @classmethod
    def dump_private_key(cls, key, as_str=False, remove_flag=True, **kwargs):
        data = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        if as_str:
            if remove_flag:
                return "".join(data.decode("utf-8").splitlines()[1:-1])
            return data.decode("utf-8")
        return data

    @classmethod
    def load_public_key(cls, key: str, append_flag=True):
        if append_flag:
            key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"
        return serialization.load_pem_public_key(key.encode(), backend=default_backend())

    @classmethod
    def load_private_key(cls, key: str, append_flag=True):
        if append_flag:
            key = f"-----BEGIN RSA PRIVATE KEY-----\n{key}\n-----END RSA PRIVATE KEY-----"
        return serialization.load_pem_private_key(
            key.encode(), password=None, backend=default_backend()
        )

    def encrypt(self, data: str, as_str=False, padding_mode: Literal["PKCS", "OAEP"] = "OAEP"):
        if padding_mode == "PKCS":
            _padding = padding.PKCS1v15()
        else:
            _padding = padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            )

        text = self.__public_key.encrypt(data.encode(), _padding)
        if as_str:
            return base64.b64encode(text).decode("utf-8")
        return text

    def decrypt(
        self,
        data: Union[bytes, str],
        as_str=False,
        raise_err=True,
        padding_mode: Literal["PKCS", "OAEP"] = "OAEP",
    ):
        if padding_mode == "PKCS":
            _padding = padding.PKCS1v15()
        else:
            _padding = padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            )
        try:
            if not isinstance(data, bytes):
                data = base64.b64decode(data)
            ret = self.__private_key.decrypt(data, _padding)
            if as_str:
                return ret.decode("utf-8")
            return ret
        except Exception:
            if raise_err:
                traceback.print_exc()
                raise DecryptedError("rsa decrypted failed")
            pass


class AesCbcCrypto:
    # 生成密钥

    def __init__(self, key: str, iv: str):
        self.key = base64.b64decode(key)
        self.iv = base64.b64decode(iv)

    @classmethod
    def gen_key(cls, as_str=True):
        # 256位密钥, 初始化向量
        key, iv = os.urandom(32), os.urandom(16)
        if as_str:
            return base64.b64encode(key).decode("utf-8"), base64.b64encode(iv).decode("utf-8")
        return key, iv

    def encrypt(self, plain_text: Union[bytes, str]):
        # 创建 AES 加密器
        if not isinstance(plain_text, bytes):
            plain_text = plain_text.encode("utf-8")
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # 填充文本以满足块大小要求
        pads = Padding.PKCS7(algorithms.AES.block_size).padder()
        padded_plaintext = pads.update(plain_text) + pads.finalize()

        # 加密
        cipher_text = encryptor.update(padded_plaintext) + encryptor.finalize()

        return base64.b64encode(cipher_text).decode("utf-8")

    def decrypt(self, cipher_text: str, decompress=False):
        # 创建 AES 解密器
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # 解密
        padded_plain_text = decryptor.update(base64.b64decode(cipher_text)) + decryptor.finalize()

        # 去掉填充
        unpadder = Padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_plain_text) + unpadder.finalize()
        if decompress:
            plaintext = zlib.decompress(plaintext)
        return plaintext.decode("utf-8")


class AesGcmCrypto:
    def __init__(self, key: bytes | None = None):
        """
        :param key: 主密钥（32字节），为None时自动生成
        """
        self.key = key or AESGCM.generate_key(128)

    def encrypt(self, data: str, associated_data: str | None = None) -> str:
        """
        加密数据
        :param data: 待加密的数据
        :param associated_data: 关联数据（用于认证但不加密）
        :return: base64编码的加密字符串
        """
        if associated_data is not None:
            associated_data = associated_data.encode()

        nonce = os.urandom(12)
        aes = AESGCM(self.key)

        ciphertext = aes.encrypt(nonce=nonce, data=data.encode(), associated_data=associated_data)
        # 组合为：nonce(12) + ciphertext
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted: str, associated_data: str | None = None) -> str:
        """
        解密数据
        :raises ValueError: 当解密失败时抛出
        """
        if associated_data is not None:
            associated_data = associated_data.encode()

        data = base64.urlsafe_b64decode(encrypted.encode())
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce=nonce, data=ciphertext, associated_data=associated_data)
        return plaintext.decode()

    @staticmethod
    def generate_pepper() -> str:
        """生成客户端pepper（增强密钥安全性）"""
        return base64.urlsafe_b64encode(os.urandom(8)).decode()
