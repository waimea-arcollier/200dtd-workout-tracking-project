#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html
from datetime import date, timedelta

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.dates   import init_datetime, utc_datetime_str, utc_date_str, utc_time_str
from urllib.parse        import urlparse, parse_qs


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def show_all_workouts():
    with connect_db() as client:
        today_str = date.today().strftime("%Y-%m-%d")

        # Get all the things from the DB
        sql = """
            SELECT 
                id, 
                name, 
                reps_target,   
                (SELECT COUNT(*) FROM sessions WHERE workout_id = workouts.id AND date = ?) AS done,
                (SELECT COUNT(*) FROM sessions WHERE date = ?) AS total_completed
            FROM workouts
             
            ORDER BY name ASC
        
        """
        params = [today_str, today_str]
        result = client.execute(sql, params)
        workouts = result.rows
        day_of_week = date.today().isoweekday()
        today_date = date.today().strftime("%d-%m")

        # And show them on the page
        return render_template("pages/home.jinja", workouts=workouts, day_of_week=day_of_week, today_date=today_date)


#-----------------------------------------------------------
# New workout form
#-----------------------------------------------------------
@app.get("/new/")
def show_all_things():
    with connect_db() as client:
        # Get data from the DB
        sql = "SELECT id, name FROM workouts "
        params = []
        result = client.execute(sql, params)
        workouts = result.rows
        today_date = date.today().strftime("%d-%m")

        # And show them on the page
        return render_template("pages/new.jinja", workouts=workouts, today_date=today_date)


@app.post("/workout/<int:id>")
def record_workout_session(id):
    with connect_db() as client:
        # Read the reps from the workout table
        sql = "SELECT reps_target FROM workouts WHERE id=?"
        params = [id]
        result = client.execute(sql, params)
        reps = result.rows[0][0]
        date_str = date.today().strftime("%Y-%m-%d")

        # Do an insert into the session table with the id and reps
        sql = "INSERT INTO sessions (workout_id, reps, date) VALUES (?, ?, ?)"
        params = [id, reps, date_str]
        client.execute(sql, params)   
        
        return redirect("/")
   


#-----------------------------------------------------------
# Individual Workout
#-----------------------------------------------------------
@app.get("/workout/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the workout details from the DB
        sql = "SELECT id, name, video_id, reps_target, notes FROM workouts WHERE id=?"
        params = [id]
        result = client.execute(sql, params)
        
        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            workout = result.rows[0]

            today_str = date.today().strftime("%Y-%m-%d")
            today_date = date.today().strftime("%d-%m")
            four_weeks_ago = date.today() - timedelta(days=(-7*4))  # Four weeks ago
            past_str = four_weeks_ago.strftime("%Y-%m-%d")
            
            # Get the workout details from the DB
            sql = "SELECT date, reps FROM sessions WHERE workout_id=? ORDER BY date DESC"
            params = [id]
            result = client.execute(sql, params)
            sessions = result.rows

            return render_template("pages/workout.jinja", workout=workout, sessions=sessions, today_date=today_date)

        else:
            # No, so show error
            return not_found_error()
        
#-----------------------------------------------------------
# Edit workout info
#-----------------------------------------------------------
@app.get("/edit/<int:id>")
def edit_info(id):
    with connect_db() as client:
        # Get the workout details from the DB
        sql = "SELECT id, name, video_id, reps_target, notes FROM workouts WHERE id=?"
        params = [id]
        result = client.execute(sql, params)


        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            workout = result.rows[0]
            today_date = date.today().strftime("%d-%m")
            return render_template("pages/edit.jinja", workout=workout, today_date=today_date)

        else:
            # No, so show error
            return not_found_error()

#-----------------------------------------------------------
# Route for adding a workout, using data posted from a form
#-----------------------------------------------------------
@app.post("/add")
def add_a_workout():
    # Get the data from the form
    name  = request.form.get("name")
    yt_vid_link = request.form.get("video_link")
    reps_target  = request.form.get("reps_target")
    notes  = request.form.get("notes")

    # Get the YT video ID from the URL
    parsed_url = urlparse(yt_vid_link)
    query_string = parsed_url.query
    query_parameters = parse_qs(query_string)

    if 'v' in query_parameters:
        yt_vid_id = query_parameters["v"][0]
    else:
        yt_vid_id = None
    
    #sanitise
    name = html.escape(name)
    notes = html.escape(notes) if notes else None

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO workouts (name, video_id, reps_target, notes) VALUES (?, ?, ?, ?)"
        params = [name, yt_vid_id, reps_target, notes]
        client.execute(sql, params)
        
        # Go back to the home page
        return redirect("/")

#-----------------------------------------------------------
# Route for editing a workout, using data posted from a form
#-----------------------------------------------------------
@app.post("/edit/<int:id>")
def edit_info_post(id):
    # Get the data from the form
    yt_vid_link = request.form.get("video_link")
    reps_target  = request.form.get("reps_target")
    notes  = request.form.get("notes")

    # Gte the YT video ID from the URL
    parsed_url = urlparse(yt_vid_link)
    query_string = parsed_url.query
    query_parameters = parse_qs(query_string)

    if 'v' in query_parameters:
        yt_vid_id = query_parameters["v"][0]
    else:
        yt_vid_id = None
        

    # Sanitize the other text inputs
    notes = html.escape(notes) if notes else None

    with connect_db() as client:
        # Add the thing to the DB
        sql ="""UPDATE workouts 
                SET video_id = ?, reps_target = ?, notes = ?
                WHERE id = ?
             """
        params = [yt_vid_id, reps_target, notes, id]
        client.execute(sql, params)
        

        # Go back to the home page
        return redirect(f"/workout/{id}")

#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_workout(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM workouts WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        return redirect("/")


