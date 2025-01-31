import bcrypt

import os,pickle

def dump_bcrypt_salt(PATH_BCRYPT_SALT):
    salt = bcrypt.gensalt()
    with open(PATH_BCRYPT_SALT,'wb') as f:
        pickle.dump(salt,f)

def load_bcrypt_salt(PATH_BCRYPT_SALT)->bytes:
    with open(PATH_BCRYPT_SALT,'rb') as f:
        salt = pickle.load(f)
    return salt


class Encrypter:
    def __init__(self):
        self.salt = None  #not initialize

    def init_encrypter(self, PATH_BCRYPT_SALT):
        if not os.path.exists(PATH_BCRYPT_SALT):
            dump_bcrypt_salt(PATH_BCRYPT_SALT)
        self.salt = load_bcrypt_salt(PATH_BCRYPT_SALT)

    def encrypt(self, password:str)->str:
        password_bytes = password.encode('utf-8')
        return bcrypt.hashpw(password_bytes, self.salt).decode('utf-8')



    