from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import requests

# Key for swell forecast API
key_API ="8e6bc43c-e89b-11ed-92e6-0242ac130002-8e6bc4a0-e89b-11ed-92e6-0242ac130002"

# Initialize the app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///surfboards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
Bootstrap(app)

# Create dictionaries for each city
sydney_coordinates = {
    'lat': -33.8688,
    'long': 151.209900
}

perth_coordinates = {
    'lat': -31.9514,
    'long': 115.8617
}

melbourne_coordinates = {
    'lat': -37.8136,
    'long': 144.9631
}

# Define the model
class Surfboard(db.Model):
    __tablename__ = 'surfboards'
    
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    skill_level = db.Column(db.String(50), nullable=False)
    tail_shape = db.Column(db.String(50), nullable=False)

    SKILL_LEVELS = {
        'beginner': 0.70,
        'progressive': 0.55,
        'advanced': 0.4,
    }

    TAIL_SHAPES_INFO = {
        'squash': 'Squash tail: Great for all-around performance.',
        'round': 'Round tail: Offers smooth turns and better control.',
        'pin': 'Pin tail: Ideal for big waves, provides excellent hold.',
        'swallow': 'Swallow tail: Enhances maneuverability in small waves.'
    }
    
    
    @classmethod
    def calculate_volume(cls, weight, skill_level):
        # Get skill factor based on selected skill level
        skill_factor = cls.SKILL_LEVELS.get(skill_level, 1.0)

        # Calculate volume based on weight and skill level
        volume = weight * skill_factor

        return volume
    
    # Function to calculate suitable board lengths for user based on their ability and weight
    def calc_length(x, y):
        if x == 'beginner' or x == 'progressive':
            if y <= 55:
                length = "5'8 - 6'2"
                return length
            elif y >= 55 or y <= 72:
                length = "5'10 - 6'4"
                return length
            elif y >= 72 or y <= 82:
                length = "6'0 - 6'8"
                return length
            elif y >= 82:
                length = "6'4 - 6'10"
                return length
        elif x == 'advanced':
            if y <= 55:
                length = "5'4 - 6'0"
                return length
            elif y >= 55 or y <= 72:
                length = "5'6 - 6'2"
                return length
            elif y >= 72 or y <= 82:
                length = "5'8 - 6'4"
                return length
            elif y >= 82:
                length = "5'10 - 6'6"
                return length   
    
    def surfboard_shape_rec(x):
        if x <= 0.5:
            board_shape = "Fish/Groveler/Longboard"
        elif 0.6 <= x <= 1.0:
            board_shape = "Fish/Shortboard"
        elif 1.1 <= x <= 1.5:
            board_shape = "Shortboard"
        elif 1.6 <= x <= 2.0:
            board_shape = "Shortboard/Performance Shortboard"
        elif 2.1 <= x <= 2.5:
            board_shape = "Performance Shortboard/Step Up"
        elif 2.6 <= x <= 3.5:
            board_shape = "Step Up"
        elif x >= 3.6:
            board_shape = "Gun/Tow - Goodluck :0"
        else:
            board_shape = 'Invalid parameters'
        return board_shape
        
    def get_city(x):
        if x == 'Sydney':
            location = sydney_coordinates
        elif x == 'Melbourne':
            location = melbourne_coordinates
        elif x == 'Perth':
            location = perth_coordinates
        else:
            location = "Invalid Location"
        return location

    
    
    def swell(x ,key):
        import arrow
        import requests
        
        lat = x['lat']
        lng = x['long']

        # Get first hour of today
        start = arrow.now().floor('day')

        # Get last hour of today
        end = arrow.now().ceil('day')

        response = requests.get(
        'https://api.stormglass.io/v2/weather/point',
        params={
            'lat': lat,
            'lng': lng,
            'params': ','.join(['waveHeight', 'waterTemperature']),
            'start': start.to('UTC').timestamp(),  # Convert to UTC timestamp
            'end': end.to('UTC').timestamp()  # Convert to UTC timestamp
        },
        headers={
            'Authorization': key
        }
        )
        
        json_data= response.json()
        
        # Get the first entry in the dictionary
        first_entry = json_data['hours'][0]
        
        # Extract the waveHeight
        height_swell = first_entry['waveHeight']['sg']
        
        return height_swell


# Define the form
class SurfboardForm(FlaskForm):
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    skill_level = SelectField('Skill Level', choices=[
        ('beginner', 'Beginner'),
        ('progressive', 'Progressive'),
        ('advanced', 'Advanced'),
    ], validators=[DataRequired()])
    tail_shape = SelectField('Tail Shape', choices=[
        ('squash', 'Squash Tail'),
        ('round', 'Round Tail'),
        ('pin', 'Pin Tail'),
        ('swallow', 'Swallow Tail'),
    ], validators=[DataRequired()])
    city = SelectField('Location:', choices=[
        ('Sydney'),
        ('Melbourne'), 
        ('Perth')
    ])


def get_weather_data(city):
    api_key = 'f3337f70ad27b09a847fe7856d3ceaaf'
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    response = requests.get(base_url, params=params)
    print(response.url)  # Print the URL for debugging
    print(response.json())  # Print the JSON response for debugging
    return response.json()


# Define the route
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SurfboardForm()
    error = None
    if form.validate_on_submit():
        weight = form.weight.data
        skill_level = form.skill_level.data
        tail_shape = form.tail_shape.data
        city_ = form.city.data
        city = request.form.get('city')
        original_volume = Surfboard.calculate_volume(weight, skill_level)
        volume_lower = original_volume - 2
        volume_upper = original_volume + 8
        length = Surfboard.calc_length(skill_level, weight) 
        tail_info = Surfboard.TAIL_SHAPES_INFO.get(tail_shape, 'Unknown tail shape')
        board_rec = Surfboard.surfboard_shape_rec(Surfboard.swell(Surfboard.get_city(city_), key_API))
        
        if city:
            weather_data = get_weather_data(city)
            if weather_data.get('cod') != 200:  # Check if the response contains an error code
                error = weather_data.get('message', 'Error fetching weather data')
            else:
                weather = weather_data

        return render_template('result.html', volume_lower=volume_lower, volume_upper=volume_upper, length=length, tail_info=tail_info, board_rec=board_rec, error=error)
    return render_template('calculate.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)