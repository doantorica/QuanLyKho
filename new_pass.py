import bcrypt

# Tạo mật khẩu mới
new_password = "doantorica".encode('utf-8')
hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())
hashed_str = hashed.decode('utf-8')  # Chuyển bytes sang chuỗi base64

print(f"Mật khẩu hash mới: {hashed_str}")