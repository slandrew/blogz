from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
#A way to determine time an date - useful
from datetime import datetime
#Googled a way to be able to order by DESC
from sqlalchemy import desc

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:MyNewPass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
#This is used for sessions. Imported for the next assignment
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted = db.Column(db.Integer)

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        #checks to see if there is a time - may be redundant but I copied this from material
        if self.pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.owner = owner
        self.deleted = False

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25))
    password = db.Column(db.String(25))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

#Function to determine if user is logged on
def logged_in():
    if 'username' in session:
        return True
    else: return False

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blogs', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
    

@app.route('/blog', methods=['POST', 'GET'])
def blogs():

    blog_header = 'The Experience and Friends'
    if 'username' in session:
        logged_in_user = User.query.filter_by(username=session['username']).first()
    else:
        logged_in_user = ''
    #If Posted as new post
    if request.method == 'POST':
        #Collect form data, save to variables No commit yet to avoid erroneous database entries
        blog_title = request.form['title']
        blog_body = request.form['body']
        blog_owner = User.query.filter_by(username=session['username']).first()
        new_blog = Blog(blog_title, blog_body, blog_owner)
        #Validation and Error
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = 'Please include a title for your blog.'
        if not blog_body:
            body_error = 'Please enter a body for your blog.'
        #Pass Validation
        if not title_error and not body_error:
            #Add and commit to database
            db.session.add(new_blog)
            db.session.commit()
            #Find generated primary key and redirect to page displaying only one blog
            blog_id = str(new_blog.id)
            blogs = Blog.query.filter_by(deleted = False).all()
            return redirect('/blog?id='+blog_id)
        #Fail Validation - Return Error, saving title and post
        else:
            return render_template('newpost.html', title='New Post', blog_title=blog_title, blog_body=blog_body, title_error=title_error, body_error=body_error, logged_in=logged_in(), blog_header=blog_header)
    #Handles get requests from either a redirect from a new post or first time on site and renders accordingly
    else:
        blog_id = request.args.get('id')
        user_id = request.args.get('userId')
        #If no id parameter - shows all blogs
        if not blog_id and not user_id:
            blogs = Blog.query.order_by(desc(Blog.pub_date)).filter_by(deleted = False).all()
            display_title = 'Blogs'
        #With an id parameter shows only posts with that id
        elif blog_id:
            blogs = Blog.query.filter_by(id=blog_id, deleted = False).all()
            blog = Blog.query.filter_by(id=blog_id, deleted = False).first()
            #TODO make title appear as title of blog id
            display_title = blog.title
        else:
            #is there a better way to pull data using a foreign key?
            owner = User.query.filter_by(id=user_id, deleted = False).first()
            owner_id = owner.id
            blogs = Blog.query.filter_by(owner_id=owner_id, deleted = False).order_by(desc(Blog.pub_date)).all()
            display_title = owner.username
            blog_header = owner.username + """'s Wall"""
        return render_template('blog.html', title=display_title, blogs=blogs, logged_in=logged_in(), blog_header=blog_header, logged_in_user=logged_in_user)

#A very simple template to make a new post
@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    return render_template('newpost.html', title='New Post', logged_in=logged_in())

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()

        #Validation 
        valid = True

        if not username:
            valid = False
            flash('Please enter a username.', 'error')
        elif len(username) < 3 or len(username) > 25:
            valid = False
            flash('Please enter a valid username between 3 and 25 characters.', 'error')

        if not password:
            valid = False
            flash('Please enter a password.', 'error')
        elif len(password) < 3 or len(password) > 25:
            valid = False
            flash('Please enter a valid password between 3 and 25 characters.', 'error')

        if password != verify:
            valid = False
            flash('Password mismatch.', 'error')
        

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user and valid == True:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            flash('Account created!')
            return redirect('/newpost')
        elif existing_user:
            flash('Duplicate User', 'error')
    return render_template('signup.html', logged_in=logged_in())

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
        elif user and user.password != password:
            flash('User password incorrect.', 'error')
        elif not user:
            flash('User does not exist.', 'error')
    return render_template('login.html', logged_in=logged_in())

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, logged_in=logged_in())

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/delete-post', methods=['POST'])
def delete_post():
    blog_id = int(request.form['blog-id'])
    blog = Blog.query.get(blog_id)
    blog.deleted = True
    db.session.add(blog)
    db.session.commit()

    return redirect('/blog')


if __name__ == '__main__':
    app.run()