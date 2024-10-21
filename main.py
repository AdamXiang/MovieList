from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
# initialize the app with the extension
db.init_app(app)

# CREATE MODEL
class Movie(db.Model):
    __tablename__ = 'Movies'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


# DEFINE THE EDIT FROM
class RateMovieForm(FlaskForm):
    rating = StringField(u'Your Rating Out of 10 e.g. 7.5')
    review = StringField(u'Your Review')
    submit = SubmitField(u'Done')

class AddMovieForm(FlaskForm):
    title = StringField(u'Movie Title', validators=[DataRequired()])
    submit = SubmitField(u'Add Movie')


# HOME PAGE
@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()

    # all() effectively converts scalars to python list
    movies_info = movies.all()

    init_ranking = 1
    for movie in movies_info:
        movie.ranking = init_ranking
        init_ranking += 1
    
    db.session.commit()

    return render_template("index.html", movies=movies_info)

# EDIT PAGE
@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()

        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

# DELETE MOVIE
@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for('home'))

# ADD MOVIE
@app.route('/add', methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    
    if form.validate_on_submit(): 
        title = form.title.data
        url = f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=true&language=en-US&page=1"

        headers = {
            "accept": "application/json",
            "Authorization": Your API KEY
        }

        response = requests.get(url, headers=headers)
        data = response.json()["results"]

        return render_template('select.html', options=data)

    return render_template('add.html', form=form)

# New Find Movie
@app.route('/find')
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}?language=en-US"

        headers = {
            "accept": "application/json",
            "Authorization": Your API KEY
        }

        response = requests.get(movie_api_url, headers=headers)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
            rating=0.0,
            ranking=1
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
