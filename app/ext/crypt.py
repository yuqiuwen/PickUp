import os

from app.utils.crypto import RsaCrypto


pwd_crypto = RsaCrypto()


def init_key():
    pwd_crypto.init_key(private_key=os.getenv("PWD_PRIVATE_KEY"))
