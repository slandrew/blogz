from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:MyNewPass@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))

    def __init__(self, title, body):
        self.title = title
        self.body = body

@app.route('/blog', methods=['POST', 'GET'])
def blogs():

    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        new_blog = Blog(blog_title, blog_body)
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = 'Please include a title for your blog.'
        if not blog_body:
            body_error = 'Please enter a body for your blog.'

        if not title_error and not body_error:
            db.session.add(new_blog)
            db.session.commit()
            blogs = Blog.query.all()
            return render_template('blog.html', title='Blogs', blogs=blogs)
        else:
            return render_template('newpost.html', title='New Post', blog_title=blog_title, blog_body=blog_body, title_error=title_error, body_error=body_error)
    else:
        blogs = Blog.query.all()
        return render_template('blog.html', title='Blogs', blogs=blogs)

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    return render_template('newpost.html', title='New Post')

if __name__ == '__main__':
    app.run()