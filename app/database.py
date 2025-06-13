import pymysql
import hashlib
from peewee import *
from datetime import datetime

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
    password = CharField(max_length=50)
    created_at = DateTimeField(default=datetime.now)

    def __str__(self):
        return self.username

    class Meta:
        table_name = 'users'

    @classmethod
    def create_password(self, password: str):
        h = hashlib.md5()
        
        h.update(password.encode('utf-8'))
        return h.hexdigest()

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
