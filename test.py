import base64
import json
import os
import zlib

from app.utils.crypto import RsaCrypto, AesCbcCrypto


def test_rsa():
    pwd = "yuqiuwen666"
    cpt = RsaCrypto()

    private_key = "MIIEpAIBAAKCAQEAznGH42G8TnZ3nUJbAP6zvn1hyPo3BYkruG6vc8QgYj6iquBLzTUvu5lHkKmgQaYJRDnm6Z8iy1wPy67IzwwuLLfexPgTjtU6YFgQS29GJSPIFbkmTV4Yb7gcc7vUteWk1Mx2KWMOvB6btK30iAmNMKcTYiLvaetWrKhe7/EXvXGDzcvikNL6lcUuuOKMQ2jSK0Vva3Lwzk9zhVpu1AyOa05FhSpBTIufS0J21nr1w8dwiS0wvkCNyeWwjv6oVYPkL3PGHszhUvWOHEfrwSowxNEbOj5TfnKDhsh3peLELq1CI7nXAw0drTFC/Yv1piWp9nbHumHSGx+7O/ShJVjlpQIDAQABAoIBAAbHGdxgdty5dowFQ+blGmkw/DKG6sdjiN5t5rjkWLyw/sAPArBgaNy0zoPCSDVvjtwuyQvuFKfcaNU1KZ2bKSAS3i+MT39/66anGzlGyy361Pk1m3I+9a8jlcnWFFrvmx20kZ8iX1vUMAARg22qhFPOzidSvZZ/So+NUQJU882mdBsLO3k9EhCkgBL7D+sIdklXPJ0ocluDzYge4Kqp6UDNlIWjn9KDvn4mEtIXZSOuYBs8ysfHFTvP4r7jD85xb5GWRFzQSjlicZN+1IMqUm5wnZRN6KFxu2t7ZwUsyxfDpwcGj1gfS6jpAUK51mQdTG5KZ/Xvny6klLGNxSS9toECgYEA7qIl999yUGEreBUCuVgu4xnF+aHKvU5+ii2ikaQ90nl9G4euy3KMmk765ahwPxGEjH7xCPpnnPvf1d3Ct/JcJHr2C+tmaSCCJkZUwLVEYBsGdfb5Llk5NApJ54qyzGLrI5J8R4CGSO7/SAc0ES1DDs5cZnjrbSiO5Kc+9pO7xkECgYEA3XerXLqk6gMj1KIxQGBmluLQG5AzNYj1Vsc/Bhfzl++/CmI5EyIxAbfBwOedXJPpUzH+lxQUt7lzaPEL9YLm/SwCB4KsTA+HDOAKTNQZbpFpjniKQQm2revp6mKLvsoqVe5J3WktEgbNwRpDZa4y+rqCSVnrePJsiyqRXN2kLmUCgYEAlZo172W4BshENi4F3Sh5jIpV4SAbN/8DuaDOcDvlPhRH6IBxhr4zg3HMPToR1Jgo3uOePKCvYG1PcIZsUmGwfnZP1j0noPRuY4xoCcAaM539uOqyYOoywHtKxcvgN94zx8NIApOCnCqpBADwFWyow5l/uAZKoc5xdsua337Sk4ECgYEAu5AuQUqRgN9H6T20GKGMQR22wqFNvXlQzz3P0olWdMdHNLQbQmkiuCG4pneCfnWGlj8xLyKCqVcWtznutu82UhSDY3j4EzLTXcQg9RBsuYfNrivIa2yemo3Cfg8X622sjTpStIHu+eVpPLHRgrwV0ONElHrjQnuOEg7rLYtJEUECgYBcqn2PTU0XlqdcnAoWHmRTpzDG1sBoPJsH2UpJpFJoejM9igkQlOQsKIfGRKvMBtNmTs3fw2b2jeAc828snHZwi3HMjq0C1zGyCpVFWiDcUg0bS4ryFiVithFcrWty+gCX5JRnhUSWAOsjs1YvDIcOG9K1il7r/4gZDD2Eu4D6eQ=="
    public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAznGH42G8TnZ3nUJbAP6zvn1hyPo3BYkruG6vc8QgYj6iquBLzTUvu5lHkKmgQaYJRDnm6Z8iy1wPy67IzwwuLLfexPgTjtU6YFgQS29GJSPIFbkmTV4Yb7gcc7vUteWk1Mx2KWMOvB6btK30iAmNMKcTYiLvaetWrKhe7/EXvXGDzcvikNL6lcUuuOKMQ2jSK0Vva3Lwzk9zhVpu1AyOa05FhSpBTIufS0J21nr1w8dwiS0wvkCNyeWwjv6oVYPkL3PGHszhUvWOHEfrwSowxNEbOj5TfnKDhsh3peLELq1CI7nXAw0drTFC/Yv1piWp9nbHumHSGx+7O/ShJVjlpQIDAQAB"
    # private_key, public_key = cpt.gen_key()
    cpt.init_key(private_key=private_key, public_key=public_key)

    print("公钥：", public_key)
    print("私钥：", private_key)
    encrypted_pwd = cpt.encrypt(pwd, as_str=True)
    print("加密后密码：", encrypted_pwd)

    decrypted_pwd = cpt.decrypt(encrypted_pwd, as_str=True)
    print("解密后密码：", decrypted_pwd)


def test_aes(plain_text):
    data = [
        {
            "id": "01J67SSGMHXBC8G0SWKGDW44S4",
            "match_id": 3485614,
            "comp_id": 1366,
            "comp_name": "国际赛",
            "status": -1,
            "status_time": None,
            "home_id": 881,
            "away_id": 876,
            "round": "八月",
            "home_team": {
                "id": 881,
                "logo": "http://img.zgzcw.com/zgzcw/matchCenter/team/images/165018997867.png",
                "name": "约旦",
                "corners": None,
                "red_cards": None,
                "half_score": 0,
                "final_score": 0,
                "yellow_cards": None,
            },
            "away_team": {
                "id": 876,
                "logo": "http://img.zgzcw.com/zgzcw/matchCenter/team/images/165018947457.png",
                "name": "朝鲜",
                "corners": None,
                "red_cards": None,
                "half_score": 0,
                "final_score": 0,
                "yellow_cards": None,
            },
            "match_time": "2024-08-28 00:00:00",
            "version": "0.0.1",
            "bp_cnt": 0,
            "is_hit": False,
            "is_jc": False,
            "is_bd": False,
        }
    ]

    plain_text = json.dumps(data)
    plain_text = zlib.compress(plain_text.encode("utf-8"))

    key = base64.b64encode(os.urandom(32)).decode("utf-8")  # 256位密钥
    iv = base64.b64encode(os.urandom(16)).decode("utf-8")  # 初始化向量
    print("key:", key)
    print("iv:", iv)

    crypto = AesCbcCrypto(key, iv)
    cipher_text = crypto.encrypt(plain_text)
    print("Cipher Text:", cipher_text)
    print(len(cipher_text))

    decrypted_text = crypto.decrypt(cipher_text, decompress=True)
    print("Decrypted Text:", decrypted_text)


print(test_rsa())
