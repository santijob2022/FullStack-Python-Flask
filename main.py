from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,  FloatField
from wtforms.validators import DataRequired, Length
import requests
from dotenv import load_dotenv
import os

load_dotenv()

####################### API FUNCTIONS #######################
def api_movies(title):
    API_KEY=os.environ['API_MOVIES']
    
    endpoint = 'https://api.themoviedb.org/3/search/movie'    
    params = {
        'api_key':f'{API_KEY}',
        'language':'en-US',
        'query':f'{title}',
        'page':'1',
        'include_adult':'false',
    }    
    res = requests.get(url=endpoint,params=params,timeout=(20, 59))
    search = res.json()
    return search

def movie_details(movie_id):
    API_KEY=os.environ['API_MOVIES']    
    endpoint = f'https://api.themoviedb.org/3/movie/{movie_id}'    
    params = {
        'api_key':f'{API_KEY}',
        'language':'en-US',
    }        
    res = requests.get(url=endpoint,params=params,timeout=(20, 59))
    search = res.json()
    return search

    
####################### FLASK #######################
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['flask_secret_key']
Bootstrap(app)

############## This is an example of how to add a custom validator ##############
# def is_float(form, field):
#     try:
#         float(field.data)
#     except ValueError:
#         raise validators.ValidationError('Not a float')

# class MyForm(Form):
#     my_field = FloatField('My Field', validators=[is_float])

class MovieEditForm(FlaskForm):    
    rating = FloatField('Your rating out of 10 e.g.',
                        validators=[DataRequired()])
    review =StringField('Your review', validators=[DataRequired(),Length(max=400)])    
    submit = SubmitField(label='Done')

class MovieAddForm(FlaskForm):
    title =StringField('Movie Title', validators=[DataRequired(),Length(max=400)])    
    submit = SubmitField(label='Add Movie')

####################### DATABASE #######################
app.config['SQLALCHEMY_DATABASE_URI'] = \
os.environ['db_name']
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))#unique=True
    year = db.Column(db.Integer)
    description = db.Column(db.String(400))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer) #unique=True
    review = db.Column(db.String(400))
    img_url = db.Column(db.String)

    def __repr__(self):
        return '<Author: %r>' % self.author\
        + '\n<Title: %r>' % self.title
with app.app_context():
    db.create_all()

############################ Routes ############################

@app.route('/',methods=["GET","POST"])
def home():    
    #sqlalchemy.orm.query.Query.order_by(*criterion)
    #all_Movies = db.session.query(Movie).order_by(Movie.id).all()
    all_Movies = db.session.query(Movie).order_by(Movie.ranking.desc()).all() 
    #all_Movies = db.session.query(Movie).order_by(Movie.rating.desc(), Movie.title.asc())       

    if request.args.get('movie_id'):        
        # movie = db.session.query(Movie).get(request.args.get('movie_id'))          
        filter_Movies = db.session.query(Movie).order_by(Movie.rating.desc(), Movie.title.asc())
#filter_Movies = db.session.query(Movie).order_by(Movie.rating.desc())
        for i,movie in enumerate(filter_Movies):   
            if i<10:        
                movie.ranking = i+1
                db.session.commit()
            else:                
                db.session.delete(movie)
                db.session.commit()  
        return redirect(url_for("home"))

    return render_template("index.html", all_Movies=all_Movies)

@app.route('/add',methods=["GET","POST"])
def add():
    form = MovieAddForm()
    if form.validate_on_submit():
        search = api_movies(form.title.data)
        return render_template("select.html",search=search)
    return render_template("add.html",form=form)

@app.route('/details')
def details():
    movie_id = request.args.get('id')
    details = movie_details(movie_id)
    img_url = 'https://image.tmdb.org/t/p/w500'
    if details['poster_path']:
        img_url = img_url + details['poster_path']
    new_movie = Movie(title=details['title'],
                      year=details['release_date'],
                      description=details['overview'],
                      img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit',movie_id=new_movie.id))

@app.route('/edit/<movie_id>',methods =["GET","POST"])
def edit(movie_id):
    form = MovieEditForm()
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating=form.rating.data        
        movie.review=form.review.data        
        db.session.commit()
        return redirect(url_for('home',movie_id=movie_id))  
            
    return render_template("edit.html", movie=movie,form=form)    

######### This shows how to pass the parameters without #########
######### including it on the URL #########
@app.route('/delete')
def delete():    
    movie_id = request.args.get('id')    
    movie_delete = Movie.query.get(movie_id)    
    db.session.delete(movie_delete)
    db.session.commit()    
    return redirect(url_for('home',movie_id=movie_id))

if __name__ == '__main__':
    app.run(debug=True)
