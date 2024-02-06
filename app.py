from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from geopy.geocoders import Nominatim
import math
from urllib.request import urlopen
import re as r

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13he0c578dfde280ba245'


class WeatherForm(FlaskForm):
    city_name = StringField('City', validators=[DataRequired()])
    state_name = StringField('State', validators=[DataRequired()])
    country_name = StringField('Country', validators=[DataRequired()])
    submit = SubmitField('Find Weather')


def getIP():
    d = str(urlopen('http://checkip.dyndns.com/').read())
    return r.search(r'Address: (\d+\.\d+\.\d+\.\d+)', d).group(1)


def get_location(ip_address):
    url = f'http://ipinfo.io/{ip_address}/json'

    try:
        response = requests.get(url)
        data = response.json()
        city = data.get('city', '')
        region = data.get('region', '')
        country = data.get('country', '')
        return city, region, country
    except Exception as e:
        return None, None, None


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = WeatherForm()

    # Fetch user's location based on IP
    user_ip_address = getIP()
    city, state, country = get_location(user_ip_address)

    # Print location for debugging
    print("User Location:", city, state, country)

    # Fetch current weather for the user's location
    current_weather = get_default_weather(city, state, country)
    
    # Print current_weather for debugging
    print("Current Weather:", current_weather)

    if form.validate_on_submit():
        # If the form is submitted, fetch weather data for the specified location
        city, state, country = form.city_name.data, form.state_name.data, form.country_name.data
        return weather_finder(city, state, country)

    return render_template('home.html', form=form, current_weather=current_weather)


from geopy.exc import GeocoderTimedOut

def finding_coordinates(city, state, country):
    location_finder = f'{city}, {state}, {country}'
    geolocator = Nominatim(user_agent="weather_app")

    try:
        location = geolocator.geocode(location_finder, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None


def weather_finder(city, state, country):
    api_key = '12f1f965e3ae56e0fee7b8c8d9c0cc1d'
    latitude, longitude = finding_coordinates(city, state, country)

    if latitude is None or longitude is None:
        return render_template('error.html', error='Location not found')

    url = f'http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == '404':
        return render_template('error.html', error='City not found')

    # Convert temperature from Kelvin to Celsius and Fahrenheit
    temperature_kelvin = data['main']['temp']
    temperature_celsius = temperature_kelvin - 273.15
    temperature_fahrenheit = (temperature_kelvin - 273.15) * 9/5 + 32

    weather_info = {
        'city': data['name'],
        'temperature_celsius': math.floor(temperature_celsius),
        'description': data['weather'][0]['description'],
    }

    return render_template('weather.html', weather=weather_info)


def get_default_weather(city, state, country):
    api_key = '12f1f965e3ae56e0fee7b8c8d9c0cc1d'
    latitude, longitude = finding_coordinates(city, state, country)

    if latitude is None or longitude is None:
        return None

    url = f'http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == '404':
        return None

    # Convert temperature from Kelvin to Celsius and Fahrenheit
    temperature_kelvin = data['main']['temp']
    temperature_celsius = temperature_kelvin - 273.15
    temperature_fahrenheit = (temperature_kelvin - 273.15) * 9/5 + 32

    default_weather = {
        'city': data['name'],
        'state': state,
        'country': country,
        'temperature_celsius': math.ceil(temperature_celsius),
        'description': data['weather'][0]['description'],
    }

    return default_weather


if __name__ == '__main__':
    app.run(debug=True)
