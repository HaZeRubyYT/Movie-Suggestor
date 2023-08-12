from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, validators
from collections import Counter
import requests
import json


SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
IMAGE_URL = "https://image.tmdb.org/t/p/original"
DETAILS_URL = "https://api.themoviedb.org/3/movie/"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
GENRES_LIST_URL = "https://api.themoviedb.org/3/genre/movie/list"
HEADERS = {
    "accept": "application/json",
    "Authorization": (
        "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZGZlMTJlZ"
        "GVlM2M1NzBkZGFmMjMxZGU1M2Y1YWYwZiIsInN1YiI6IjY0YzhiM2JkODlmNzQ5MDE"
        "yNmFjYjhiYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.tE_DtSd"
        "ASn2zwIP-H7PBh1c3GDRBvKaDpGJ9xqD3h_I"
    ),
}

# Initialization and Configuration
db = SQLAlchemy()
app = Flask(__name__)

show = False

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SECRET_KEY"] = "fduifnnfernfn324324dss"


# WTForm
class MovieForm(FlaskForm):
    title = StringField(
        validators=[validators.DataRequired()],
    )


# Database Model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, nullable=False, unique=True)
    title = db.Column(db.String, nullable=False)
    poster = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String, nullable=False)
    show = db.Column(db.Boolean, nullable=False)


db.init_app(app)
with app.app_context():
    db.create_all()


# Website Routes
@app.route("/", methods=["POST", "GET"])
def home():
    form = MovieForm()
    movie_data = Movie.query.all()

    # Fav Movies Section
    if request.args.get("id"):
        id = request.args.get("id")

        # To check if movies do not repeat
        if not Movie.query.filter(Movie.film_id == id).first():
            details = requests.get(
                url=f"{DETAILS_URL}/{id}", headers=HEADERS
            ).json()
            movie = Movie(
                film_id=id,
                title=details["title"],
                poster=IMAGE_URL + details["poster_path"],
                year=details["release_date"][0:4],
                # Converting list into json string
                genre=json.dumps(
                    [json.dumps(i["id"]) for i in details["genres"]]
                ),
                show=True,
            )
            db.session.add(movie)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template(
        "index.html",
        form=form,
        movie_data=movie_data,
        show=False,
        ex_movie=Movie.query.first(),
        movie_count=len(movie_data),
    )


@app.route("/searching", methods=["POST", "GET"])
def search():
    form = MovieForm()
    if form.validate_on_submit():
        result_json = requests.get(
            url=SEARCH_URL,
            headers=HEADERS,
            params={
                "query": form.title.data,
                "include_adult": "false",
            },
        ).json()["results"]

        return render_template(
            "results.html",
            json=result_json,
            image_url=IMAGE_URL,
            form=form,
        )
    return redirect(url_for("home"))


@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/suggestions")
def suggest():
    all_movies = Movie.query.all()
    final_genre_list = []
    for movie in all_movies:
        genre_id_list = json.loads(movie.genre)
        for genre_id in genre_id_list:
            final_genre_list.append(int(genre_id))
    all_genre = requests.get(url=GENRES_LIST_URL, headers=HEADERS).json()[
        "genres"
    ]
    collection = Counter(final_genre_list)
    top3_id = collection.most_common(3)
    top3_name = []
    for id in top3_id:
        for genre in all_genre:
            if id[0] == genre["id"]:
                top3_name.append(genre["name"])
    first_genre = requests.get(
        url=DISCOVER_URL,
        headers=HEADERS,
        params={
            "include_adult": "false",
            "include_video": "false",
            "language": "en-US",
            "sort_by": "vote_count.desc",
            "with_genres": top3_id[0][0],
            "with_original_language": "en",
        },
    ).json()["results"]
    second_genre = requests.get(
        url=DISCOVER_URL,
        headers=HEADERS,
        params={
            "include_adult": "false",
            "include_video": "false",
            "language": "en-US",
            "sort_by": "vote_count.desc",
            "with_genres": top3_id[1][0],
            "with_original_language": "en",
        },
    ).json()["results"]
    third_genre = requests.get(
        url=DISCOVER_URL,
        headers=HEADERS,
        params={
            "include_adult": "false",
            "include_video": "false",
            "language": "en-US",
            "sort_by": "vote_count.desc",
            "with_genres": top3_id[2][0],
            "with_original_language": "en",
        },
    ).json()["results"]
    # print(top3_id[0][0], first_genre)
    # print(top3_id[1][0], first_genre)
    # print(top3_id[2][0], first_genre)
    print(all_movies)
    return render_template(
        "suggestions.html",
        first=first_genre,
        second=second_genre,
        third=third_genre,
        names=top3_name,
        all_movies=all_movies,
        image_url=IMAGE_URL,
    )


if __name__ == "__main__":
    app.run(debug=True)
