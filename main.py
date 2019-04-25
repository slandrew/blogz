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
#This is used for sessions. Still not ENTIRELY sure how this is sues, but it has to do with encryption
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted = db.Column(db.Integer)
    replies = db.relationship('Reply', backref='original_post')

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
    replies = db.relationship('Reply', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password
#I wanted to inherit from the Blog class but couldnt quite figure it out TODO: refactor with inheritence
class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted = db.Column(db.Integer)
    original_post_id = db.Column(db.Integer, db.ForeignKey('blog.id'))

    def __init__(self, title, body, owner, original_post_id):
        self.title = title
        self.body = body
        #checks to see if there is a time - may be redundant but I copied this from material
        if self.pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.owner = owner
        self.deleted = False
        self.original_post_id = original_post_id

#Function to determine if user is logged on
def logged_in():
    if 'username' in session:
        return True
    else: return False

#function to return logged in user class
def logged_in_user():
    if 'username' in session:
        logged_in_user = User.query.filter_by(username=session['username']).first()
    else:
        logged_in_user = ''
    return logged_in_user

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blogs', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
    

@app.route('/blog', methods=['POST', 'GET'])
def blogs():

    blog_header = 'The Experience and Friends'
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
            return render_template('newpost.html', title='New Post', blog_title=blog_title, blog_body=blog_body, title_error=title_error, body_error=body_error, logged_in=logged_in(), blog_header=blog_header, logged_in_user=logged_in_user())
    #Handles get requests from either a redirect from a new post or first time on site and renders accordingly
    else:
        blog_id = request.args.get('id')
        user_id = request.args.get('userId')
        #If no id parameter - shows all blogs
        if not blog_id and not user_id:
            blogs = Blog.query.order_by(desc(Blog.pub_date)).filter_by(deleted = False).all()
            display_title = 'Blogs'
            replies = Reply.query.order_by(desc(Reply.pub_date)).filter_by(deleted = False).all()
        #With an id parameter shows only posts with that id
        elif blog_id:
            blogs = Blog.query.filter_by(id=blog_id, deleted = False).all()
            blog = Blog.query.filter_by(id=blog_id, deleted = False).first()
            replies = Reply.query.filter_by(original_post_id=blog_id).all()
            #TODO make title appear as title of blog id
            if not blog:
                flash('Sorry, no blog matches that id!', 'error')
                return redirect('/blog')
            display_title = blog.title
        else:
            #is there a better way to pull data using a foreign key?
            owner = User.query.filter_by(id=user_id).first()
            if not owner:
                flash('Sorry, no user matches that id!', 'error')
                return redirect('/blog')
            owner_id = owner.id
            blogs = Blog.query.filter_by(owner_id=owner_id, deleted = False).order_by(desc(Blog.pub_date)).all()
            display_title = owner.username
            replies = Reply.query.filter_by(original_post_id=blog_id).all()
            blog_header = owner.username + """'s Wall"""
        return render_template('blog.html', title=display_title, blogs=blogs, replies=replies, logged_in=logged_in(), blog_header=blog_header, logged_in_user=logged_in_user())

#A very simple template to make a new post
@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    return render_template('newpost.html', title='New Post', logged_in=logged_in(), logged_in_user=logged_in_user())

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
            flash('Account created!', 'success')
            return redirect('/')
        elif existing_user:
            flash('Duplicate User', 'error')
    return render_template('signup.html', logged_in=logged_in(), logged_in_user=logged_in_user())

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in", 'success')
            return redirect('/newpost')
        elif user and user.password != password:
            flash('User password incorrect.', 'error')
        elif not user:
            flash('User does not exist.', 'error')
    return render_template('login.html', logged_in=logged_in(), logged_in_user=logged_in_user())

#index displays list of all users with links
@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, logged_in=logged_in(), logged_in_user=logged_in_user())

@app.route('/logout')
def logout():
    del session['username']
    flash('Successfully logged out', 'success')
    return redirect('/blog')

#delete post if user is original poster
@app.route('/delete-post', methods=['POST'])
def delete_post():
    blog_id = int(request.form['blog-id'])
    blog = Blog.query.get(blog_id)
    blog.deleted = True
    db.session.add(blog)
    db.session.commit()

    return redirect('/blog')

#handles GET requests to render teplate and POSTS to add reply to DB
@app.route('/reply', methods=['POST', 'GET'])
def reply():
    if request.method == 'GET':
        original_post_id = request.args.get('blogId')
        blog = Blog.query.filter_by(id=original_post_id, deleted = False).first()
        return render_template('/reply.html', blog=blog, logged_in=logged_in(), logged_in_user=logged_in_user())
    else:
        reply_title = request.form['title']
        reply_body = request.form['body']
        reply_owner = User.query.filter_by(username=session['username']).first()
        original_post = int(request.form['original-post-id'])
        new_reply = Reply(reply_title, reply_body, reply_owner, original_post)
        #Validation and Error
        title_error = ''
        body_error = ''

        if not reply_title:
            title_error = 'Please include a title for your blog.'
        if not reply_body:
            body_error = 'Please enter a body for your blog.'
        #Pass Validation
        if not title_error and not body_error:
            #Add and commit to database
            db.session.add(new_reply)
            db.session.commit()
            #Find generated primary key and redirect to page displaying only one blog
            blogs = Blog.query.filter_by(deleted = False).all()
            return redirect('/blog?id=' + str(original_post))
        else:
            return render_template('reply.html', title='Reply', reply_body=reply_body, title_error=title_error, body_error=body_error, logged_in=logged_in(), logged_in_user=logged_in_user())


if __name__ == '__main__':
    app.run()