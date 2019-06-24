import hashlib


def ceil(a, b):
    if a % b == 0:
        return a // b
    else:
        return a // b + 1


def content_operation(source):
    source = source.replace('\\', '\\\\')
    source = source.replace('\'', '\\\'')
    source = source.replace('\"', '\\\"')
    return source


def password_encrypt(password, salt='segmentation_fault'):
    hash_class = hashlib.sha256()
    password += salt
    hash_class.update(password.encode())
    return hash_class.hexdigest()