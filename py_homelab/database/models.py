from .main import db
from flask_bcrypt import generate_password_hash, check_password_hash
from throw_out_py import Map


class User(db.Document):
    id = db.ObjectIdField().gen()
    email = db.StringField(required=True)
    password = db.StringField(required=True, min_length=6)
    role = db.IntField(required=True)

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


roles = Map({"member": 1, "admin": 999})
