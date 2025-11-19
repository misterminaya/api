import pymysql
import hashlib
import random
import string
from peewee import *
from datetime import datetime, timedelta

pymysql.install_as_MySQLdb()

database = MySQLDatabase(
    'peliculas',
    user='root',
    password='secret',
    host='mysql',
    port=3306
)

class BaseModel(Model):
    class Meta:
        database = database

class User(BaseModel):
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100, unique=True)
    password = CharField(max_length=50)
    is_verified = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)

    def __str__(self):
        return self.username

    class Meta:
        table_name = 'users'

    @classmethod
    def authenticate(cls, username: str, password: str):
        hashed_password = cls.create_password(password)
        try:
            user = cls.get(cls.username == username, cls.password == hashed_password)
            return user
        except cls.DoesNotExist:
            return None


    @classmethod
    def create_password(self, password: str):
        h = hashlib.md5()

        h.update(password.encode('utf-8'))
        return h.hexdigest()


class OTPCode(BaseModel):
    user = ForeignKeyField(User, backref='otp_codes', on_delete='CASCADE')
    code = CharField(max_length=6)
    expires_at = DateTimeField()
    is_used = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'otp_codes'

    @classmethod
    def generate_code(cls):
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create_otp(cls, user):
        """Create a new OTP for a user with 10 minutes expiry"""
        # Invalidate previous unused OTPs for this user
        cls.update(is_used=True).where(
            (cls.user == user) & (cls.is_used == False)
        ).execute()

        code = cls.generate_code()
        expires_at = datetime.now() + timedelta(minutes=10)

        return cls.create(
            user=user,
            code=code,
            expires_at=expires_at
        )

    @classmethod
    def verify_otp(cls, user, code):
        """Verify OTP code for a user"""
        try:
            otp = cls.get(
                (cls.user == user) &
                (cls.code == code) &
                (cls.is_used == False) &
                (cls.expires_at > datetime.now())
            )
            otp.is_used = True
            otp.save()
            return True
        except cls.DoesNotExist:
            return False

class Movie(BaseModel): 
    title = CharField(max_length=50)
    created_at = DateTimeField(default=datetime.now)

    def __str__(self):
        return self.title

    class Meta:
        table_name = 'movies'

class UserReview(BaseModel):  
    user = ForeignKeyField(User, backref='reviews')
    movie = ForeignKeyField(Movie, backref='reviews')
    reviews = TextField()
    score = IntegerField()
    created_at = DateTimeField(default=datetime.now)

    def __str__(self):
        return f'{self.user.username}-{self.movie.title}'

    class Meta:
        table_name = 'user_reviews'
