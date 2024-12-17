from cryptography.fernet import Fernet

# 生成合法密鑰
key = Fernet.generate_key()
print(f"你的密鑰是：{key.decode()}")

# 將生成的密鑰複製到程式碼中
