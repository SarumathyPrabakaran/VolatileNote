from flask import Flask,render_template,request,flash, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string
from boto3 import resource
import uuid
import config
import os



app = Flask(__name__)
SECRET_KEY = "hello"
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///privnote.sqlite3'


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.environ.get("REGION_NAME")

resource = resource(
    'dynamodb',
    aws_access_key_id     = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name           = REGION_NAME
)



table = resource.Table('Notes')


def put_an_item(code, message):
    response = table.put_item(Item={
        'code' : code,
        'message' : message
    })

    return response

def read_from_db(code):
        
        response = table.get_item(
        Key = {
            'code' : code
        },
        AttributesToGet = [
           'message' 
        ]                      
    )
        return response


def delete_from_db(code):
        response = table.delete_item(
        Key = {
            'code': code
        }
    )

        return response


db=SQLAlchemy(app)


def get_num():

    characters = list(string.digits)
    code = ''.join(random.choice(characters) for i in range(6))
    return code
    
class privnote(db.Model):
    _id = db.Column("id",db.Integer, primary_key=True)
    num = db.Column("num",db.String(10), nullable=False)
    message = db.Column(db.String(1200), nullable=False)

    def __init__(self,num,message):
        self.message = message
        self.num = num

@app.route('/')
def home():
    return render_template("home.html")



@app.route("/createnote", methods=['GET','POST'])
def create_note():
    print("hello")
    mess = ''
    if request.method == 'POST':
        print("enters")
        mess = request.form['text_message']
        n = get_num()
        note = privnote(n,mess)

        unique_id = str(uuid.uuid4())
        print(put_an_item(unique_id, mess))


        db.session.add(note)
        db.session.commit()

        id1 = privnote.query.filter_by(message=mess).first().num
        
        flash(f'{unique_id}    {id1}')
        print(unique_id)

    return render_template("index.html")




# with unique code.
@app.route('/get_note',methods=["POST",'GET'])
def get_note():
    if request.method=="POST":
        code = request.form.get("code")
        print(code)
        data = privnote.query.filter_by(num=code).first()
        data_dynamo = read_from_db(code)
        if data_dynamo:
            print(data_dynamo["Item"])
            
            return render_template('get.html',data = data_dynamo["Item"]["message"])
        else:
            print("NOthing")
    return render_template('get.html')




#unique URL
@app.route("/view/<n>")
def view(n):
    try:
        found_mess = privnote.query.filter_by(num=n).first()
        print("hurrah")
        todel = privnote.query.filter_by(num=n).first()
        db.session.delete(todel)
        db.session.commit()
        return render_template("view.html",values = found_mess)
    except:
        return 'The note might have destroyed.'


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)