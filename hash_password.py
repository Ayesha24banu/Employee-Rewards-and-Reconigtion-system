from hashlib import sha256

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def check_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

