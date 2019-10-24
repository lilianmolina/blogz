from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:020993@localhost:8889/blogz'

app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
#adding a session feature to the site
app.secret_key = "543fja14nb"

#create blog class
class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(360)) #title of the blog post
    post = db.Column(db.Text) #body of the blog post uses text instead of string to ensure 
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, post, owner):
        self.title = title
        self.post = post
        self.owner = owner

#create User Class
class User(db.Model):

#create data fields that should go into table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

#adjust request to run first, to see if user is logged in
@app.before_request
def require_login():
    #allowed routes are the function name, not the directory
    allowed_routes = ['index', 'show_blog', 'login_user', 'add_user', 'static']
    #if user is not logged in, must redirect to login page
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
        

@app.route('/')
def index():
    all_users = User.query.distinct()
    return render_template('index.html', list_all_users = all_users)


#view once in blog posts
@app.route('/blog')
def show_blog():
    post_id = request.args.get('id')
    single_user_id = request.args.get('owner_id')
    if (post_id):
        each_post = Blog.query.get(post_id)
        return render_template('each_post.html', each_post=each_post)
    else:
        if (single_user_id):
            each_user_blog_posts = Blog.query.filter_by(owner_id=single_user_id)
            return render_template('singleUser.html', posts=each_user_blog_posts)
        else:
            # queries database for all existing blog entries
            # post_id = request.args.get('id')
            all_blog_posts = Blog.query.all()
            # first of the pair matches to {{}} in for loop in the .html template, second of the pair matches to variable declared above
            return render_template('blog.html', posts=all_blog_posts)


# VALIDATION FOR EMPTY FORM
def empty_val(x):
    if x:
        return True
    else:
        return False

# THIS HANDLES THE REDIRECT (SUCCESS) AND ERROR MESSAGES (FAILURE)

@app.route('/newblogpost', methods=['POST', 'GET'])
def add_entry():

    if request.method == 'POST':

        # assigning variable to blog title from entry form
        post_title = request.form['blog_title']
        # assigning variable to blog post from entry form
        post_entry = request.form['blog_post']
        # assigning owner variable to blog post from user signup
        owner = User.query.filter_by(username=session['username']).first()
        # creating a new blog post variable from title and entry
        post_new = Blog(post_title, post_entry, owner)

        # if the title and post entry are not empty, the object will be added
        if empty_val(post_title) and empty_val(post_entry):
            # adding the new post (this matches variable created above) as object 
            db.session.add(post_new)
            # commits new objects to the database
            db.session.commit()
            post_link = "/blog?id=" + str(post_new.id)
            return redirect(post_link)
        else:
            if not empty_val(post_title) and not empty_val(post_entry):
                flash('Where is your post? Please enter a title and blog entry', 'error')
                return render_template('newblogpost.html', post_title=post_title, post_entry=post_entry)
            elif not empty_val(post_title):
                flash('Remember to create a title. Please enter one.', 'error')
                return render_template('newblogpost.html', post_entry=post_entry)
            elif not empty_val(post_entry):
                flash('Remember to write your entry', 'error')
                return render_template('newblogpost.html', post_title=post_title)

    # DISPLAYS NEW BLOG ENTRY FORM
    else:
        return render_template('newblogpost.html')


@app.route('/signup', methods=['POST', 'GET'])
def add_user():

    if request.method == 'POST':

        # - - - - - VARIABLES FOR DATA FROM SIGNUP FORM
        # assigning variable to username from signup form
        user_name = request.form['username']
        # assigning variable to user password from signup form
        user_password = request.form['password']
        # assigning variable to user password from signup form
        user_password_validate = request.form['password_validate']


        # - - - - - USER SIGNUP VALIDATION

        # if the username or password is blank, flash error
        if not empty_val(user_name) or not empty_val(user_password) or not empty_val(user_password_validate):
            flash('All fields are required to be filled in', 'error')
            return render_template('signup.html')

        # if the password is blank, flash error
        if user_password != user_password_validate:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        if len(user_password) < 3 and len(user_name) < 3:
            flash('Username and password must be at least three characters', 'error')
            return render_template('signup.html')

        if len(user_password) < 3:
            flash('Password must be at least three characters', 'error')
            return render_template('signup.html')

        if len(user_name) < 3:
            flash('Username must be at least three characters', 'error')
            return render_template('signup.html')

        
        # - - - - - ADD NEW USER

        # queries db to see if there is an existing user with name username
        # username is coming from class, user_name from variable above
        # TODO - clean up this naming
        existing_user = User.query.filter_by(username=user_name).first()
        # if there are no existing users with same username, creates new user
        if not existing_user: 
            # creating a new user
            user_new = User(user_name, user_password) 
            # adds new user
            db.session.add(user_new)
            # commits new objects to the database
            db.session.commit()
            # adds username to this session so they will stay logged in
            session['username'] = user_name
            flash('New bloggerin the house!', 'success')
            return redirect('/newblogpost')
        else:
            flash('Error, this username already exists', 'error')
            return render_template('signup.html')

    # DISPLAYS NEW BLOG ENTRY FORM
    else:
        return render_template('signup.html')


@app.route('/login', methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        # creates variables for information being passed in login form
        username = request.form['username']
        password = request.form['password']

        # - - - - - LOGIN VALIDATIONS

        if not username and not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        if not username:
            flash('Username is required', 'error')
            return render_template('login.html')
        if not password:
            flash('Password is required', 'error')
            return render_template('login.html')
        
        # query matches username to existing username in the db
        # this will net the first result, there should only be one result bc field is unique
        # if there are no users with the same username, the result with be none
        user = User.query.filter_by(username=username).first()

        # - - - - - LOGIN VALIDATIONS

        # check name, error if incorrect
        if not user:
            flash('Username/Password is incorrect', 'error')
            return render_template('login.html')
        # check password, error if incorrect
        if user.password != password:
            flash('Username/Password is incorrect', 'error')
            return render_template('login.html')

        # - - - - - LOGIN IN USER

        # "if user" checks to see if user exists
        # "if user.password == password" checks to see if the pw provided matches pw in db
        if user and user.password == password:
            # saves username to session
            session['username'] = username
            return redirect('newblogpost')

    return render_template('login.html')
        
@app.route('/logout')
def logout():
    del session['username']
    flash('You have successfully logged out', 'success')
    return redirect('/blog')


if __name__ == '__main__':
    app.run()