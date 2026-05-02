from flask import Flask, render_template, request, redirect, url_for
from run_pipeline import run_pipeline
from analysis import recommend_tee, yardage_chart, give_motivation
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

# create a Flask object called app
app = Flask(__name__)


# define a route to the home page
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/results", methods=["POST"])
def results():
    course_name = request.form.get("Course Name")

    country = request.form.get("Country")

    state = request.form.get("State")


    # Gathers and writes the golf course data to 3 CSV's
    result = run_pipeline(course_name=course_name, country=country, state=state)
    if result['status'] == 'no-results':
        return render_template("home.html", error="No courses found. Try a different search.")


    course_dir = result['course_dir']

    full_path = f'{course_dir}/tee_box_holes.csv'

    try:
        tee_box_df = pd.read_csv(full_path)
    except FileNotFoundError:
        return render_template("home.html", error="😕 Course data unavailable. Please try a different search.")
    
    tees_sorted = tee_box_df.groupby("Tee Box Name").first().sort_values(by='Tee Slope Rating', ascending=False)
    default_tee = tees_sorted.index[0]
    chart = yardage_chart(full_path, default_tee)
    chart_filename = os.path.basename(chart)

    return render_template("results.html", chart=chart_filename, course_name=course_name, course_dir=course_dir)


@app.route("/tee_rec_result", methods=["POST"])
def tee_rec_result():
    print(request.form.get("course_dir"))
    try:
        handicap = int(request.form.get("Handicap"))
    except ValueError:
        return render_template("home.html", error="😊 Please enter a valid number for your handicap!")
    
    course_dir = request.form.get("course_dir")
    
    full_path = f"{course_dir}/tee_box_holes.csv"
    tee_box_df = pd.read_csv(full_path)
    
    tee_rec = recommend_tee(handicap=handicap, tee_box_df=tee_box_df)
    motivational_msg = give_motivation(handicap=handicap)
    
    return render_template("tee_rec_result.html", tee=tee_rec, handicap=handicap, motivational_msg=motivational_msg)

if __name__ == "__main__":
    app.run(debug=True)