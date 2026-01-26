import bcrypt
password = b"admin123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)
full_hash = hashed.decode('utf-8')
print("Full hash length:", len(full_hash))
print("Full hash:")
print(full_hash)
# Save to file
with open("admin_hash.txt", "w") as f:
    f.write(full_hash)
print("Saved to admin_hash.txt")
