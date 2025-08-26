#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


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
        # Get all the things from the DB
        sql = """
            SELECT 
                workouts.id, 
                workouts.name, 
                workouts.reps_target,
                sessions.date
                
            FROM workouts 
            LEFT JOIN sessions ON sessions.workout_id = workouts.id
            
            WHERE sessions.date NOT current_date
            
            ORDER BY name ASC
        
        """
        params = []
        result = client.execute(sql, params)
        workouts = result.rows

        # And show them on the page
        return render_template("pages/home.jinja", workouts=workouts)


#-----------------------------------------------------------
# About page route
#-----------------------------------------------------------
@app.get("/history/")
def about():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name FROM workouts "
        params = []
        result = client.execute(sql, params)
        workouts = result.rows

        # And show them on the page
        return render_template("pages/history.jinja", workouts=workouts)


#-----------------------------------------------------------
# New workout form
#-----------------------------------------------------------
@app.get("/new/")
def show_all_things():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name FROM workouts "
        params = []
        result = client.execute(sql, params)
        workouts = result.rows

        # And show them on the page
        return render_template("pages/new.jinja", workouts=workouts)


#-----------------------------------------------------------
# Individual Workout
#-----------------------------------------------------------
@app.get("/thing/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = "SELECT id, name, video_link, reps_target, notes FROM workouts WHERE id=?"
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            workout = result.rows[0]
            return render_template("pages/workout.jinja", workout=workout)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
#-----------------------------------------------------------
@app.post("/add")
def add_a_thing():
    # Get the data from the form
    name  = request.form.get("name")
    instruction_video = request.form.get("instruction_video")
    reps_target  = request.form.get("reps_target")
    notes  = request.form.get("notes")

    # Sanitize the text inputs
    name = html.escape(name)
    notes = html.escape(notes)

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO workouts (name, video_link, reps_target, notes) VALUES (?, ?, ?, ?)"
        params = [name, instruction_video, reps_target, notes]
        client.execute(sql, params)

        # Go back to the home page
        return redirect("/")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_a_thing(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM things WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")


