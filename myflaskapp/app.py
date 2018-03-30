from flask import Flask,render_template, request, flash, redirect, url_for, session, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='user123'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'
# init MYSQL
mysql=MySQL(app)



@app.route('/')
def index():
     return render_template('home.html')

@app.route('/about')
def about():
     return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    data=cur.fetchone()
    print "title is "+data['Title']
    articles= cur.fetchall()

    if result>0:
        return render_template('articles.html',articles=articles)
    else:
        msg = 'No Article found '
        return render_template('articles.html',message=msg)
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    data=cur.fetchone()
    print "title is "+data['Title']
    articles= cur.fetchall()

    if result>0:
        return render_template('articles.html',articles=articles)
    else:
        msg = 'No Article found '
        return render_template('articles.html',message=msg)
    cur.close()

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
#--issue one dame space in front of Post
    if request.method =='POST' and form.validate():

        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        #Create cursor
        cur=mysql.connection.cursor()
        print (''+name+email+username+password)
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        print (''+name+email+username+password)
        #commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close
        flash('You are now registerd and logind','success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    print "runing Login"
    if request.method=='POST':
        username= request.form['username']
        password_candicate=request.form['password']

        print 'password to verify is '+password_candicate
        cur=mysql.connection.cursor()
        # Get user by Username
        result=cur.execute("SELECT * FROM users WHERE username=%s",[username])
        print str(result)+'some result '
        if result >0:
            data=cur.fetchone()
            print "data is "+data['username']
            password=data['password']
            print "password is "+data['password']
            #login suceess
            if sha256_crypt.verify(password_candicate,password):
                app.logger.info('Password Matched')
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                print 'wrong password'
                error='wrong password'
                return render_template('login.html',error=error)
        else:
            print (" password wrong ")
            error='wrong password'
            app.logger.info('No USER')
            return render_template('login.html',error=error)
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
            if 'logged_in' in session:
                return f(*args,**kwargs)
            else:
                flash('Please login ')
                return redirect(url_for('login'))
    return wrap
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():

    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    data=cur.fetchone()
    print "title is "+data['Title']
    articles= cur.fetchall()

    if result>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg = 'No Article found '
        return render_template('dashboard.html',message=msg)
    cur.close()

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('body', [validators.Length(min=6)])

@app.route('/addarticle',methods=['GET','POST'])
@is_logged_in
def addArticle():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body= form.body.data
        cur =mysql.connection.cursor()
        cur.execute("INSERT INTO articles (title,body ,author) VALUES (%s,%s,%s)",(title,body,session['username']))
        mysql.connection.commit()
        cur.close()
        flash ('Article Created ','success')
        return redirect(url_for('dashboard'))
    return render_template('addarticle.html',form=form)

@app.route('/deletearticle/<string:id>',methods=['POST'])
@is_logged_in
def deletearticle(id):
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM articles where id=%s",[id])
    mysql.connection.commit()
    cur.close()
    flash('Article deleted ')
    return redirect(url_for('dashboard'))


if __name__=='__main__':
        app.secret_key='secret111'
        app.run(debug=True)
