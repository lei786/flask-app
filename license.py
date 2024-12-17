from cryptography.fernet import Fernet

# 將這裡的密鑰替換為上一步生成的密鑰
SECRET_KEY = b'crpVRIStUGJ2B2AtARXqNyIV7RQ-pZsu_wDhlIsz5IA='
fernet = Fernet(SECRET_KEY)

# 設定授權到期日
expiration_date = "2024-12-31"  # 格式：年-月-日
encrypted_data = fernet.encrypt(expiration_date.encode())

# 寫入 license.key
with open("license.key", "wb") as f:
    f.write(encrypted_data)

print("license.key 文件生成成功！")
