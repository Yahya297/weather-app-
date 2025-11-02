import requests
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from io import BytesIO

# =====================================================
# CONFIGURATION & CONSTANTS
# =====================================================
# ❗️ IMPORTANT: Replace this placeholder with your actual OpenWeather API key.
API_KEY = "c3566146eb2e82dc377c159fbdcd4b9f" 

# OpenWeather API Endpoints and Constants
API_URL_CURRENT = "http://api.openweathermap.org/data/2.5/weather"
API_URL_ONE_CALL = "https://api.openweathermap.org/data/3.0/onecall" # For 7-day forecast
ICON_URL_BASE = "http://openweathermap.org/img/wn/"

# =====================================================
# API CALL AND DATA PROCESSING FUNCTIONS
# =====================================================

def get_current_weather_and_coords(city_name):
    """
    Fetches current weather data for a city and extracts latitude/longitude 
    needed for the 7-day forecast.
    """
    url = f"{API_URL_CURRENT}?q={city_name}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('cod') == '404':
             return {"error": f"City '{city_name}' not found. Please enter a valid name."}
        
        # Extract Current Data
        current_temp_c = int(data['main']['temp'])
        description = data['weather'][0]['description'].capitalize()
        icon_code = data['weather'][0]['icon']
        
        # Extract Coordinates (key for the One Call API)
        lat = data['coord']['lat']
        lon = data['coord']['lon']

        return {
            "city": data['name'],
            "lat": lat,
            "lon": lon,
            "temp": current_temp_c,
            "humidity": data['main']['humidity'],
            "pressure": data['main']['pressure'],
            "description": description,
            "icon_code": icon_code,
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Network or API Key Error. Check your connection or API key: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_7_day_forecast(lat, lon):
    """
    Fetches the 7-day forecast using coordinates from the One Call API 3.0.
    """
    url = f"{API_URL_ONE_CALL}?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        forecast = []
        # 'daily' array contains 8 days, we use the next 7 (starting from index 1)
        for day in data['daily'][1:8]: 
            day_name = datetime.fromtimestamp(day['dt']).strftime('%a')
            
            day_temp = int(day['temp']['day'])
            max_temp = int(day['temp']['max'])
            min_temp = int(day['temp']['min'])

            forecast.append({
                "day": day_name,
                "temp": day_temp,
                "min_max": f"{min_temp}°C / {max_temp}°C",
                "description": day['weather'][0]['description'].capitalize(),
                "icon_code": day['weather'][0]['icon']
            })
        
        return forecast

    except Exception:
        return []

# =====================================================
# BONUS FEATURE LOGIC (ADVICE)
# =====================================================

def get_obo_jr_advice(description, temp):
    """Provides personalized packing advice for Obo Jr. based on weather and temperature."""
    desc = description.lower()
    
    if temp < 5:
        return "❄️ It's freezing! Obo Jr. needs heavy-duty thermal gear."
    elif 'rain' in desc or 'drizzle' in desc:
        return "☔ Remember to bring your umbrella and waterproof jacket!"
    elif 'snow' in desc or 'sleet' in desc:
        return "🧤 Prepare for snow! Hat, scarf, and warm gloves are essential."
    elif 'clear' in desc or 'sun' in desc and temp > 25:
        return "☀️ Perfect for travel! Light clothes, sunscreen, and shades."
    elif 'cloud' in desc or 'overcast' in desc:
        return "☁️ It's a bit cloudy. A light jacket is a good idea."
    else:
        return "🎒 The weather is mild. Happy travels, Obo Jr.!"

# =====================================================
# TKINTER GUI CLASS (STEPS 4 & 5)
# =====================================================

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Obo Jr.'s Weather Adventure App 🤖")
        self.geometry("700x650")
        self.configure(bg='#CCE5FF') # Light blue background
        
        self.current_weather_image = None
        self.forecast_images = []
        
        self.create_widgets()

    def create_widgets(self):
        # --- 1. City Input Frame ---
        input_frame = tk.Frame(self, bg='#CCE5FF', padx=10, pady=10)
        input_frame.pack(fill='x')

        tk.Label(input_frame, text="City Name:", bg='#CCE5FF', font=('Arial', 14, 'bold')).pack(side='left', padx=(0, 10))
        
        self.city_entry = tk.Entry(input_frame, font=('Arial', 14))
        self.city_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        search_btn = tk.Button(input_frame, text="Get Weather", command=self.fetch_all_weather, font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white', activebackground='#45A049')
        search_btn.pack(side='right', padx=5)

        # --- 2. Current Weather Display ---
        current_frame = tk.LabelFrame(self, text="🌞 Current Weather Report", bg='white', padx=10, pady=10, font=('Arial', 14, 'bold'))
        current_frame.pack(fill='x', padx=20, pady=10)
        
        self.current_image_label = tk.Label(current_frame, bg='white')
        self.current_image_label.grid(row=0, column=0, rowspan=3, padx=10, sticky='n')
        
        self.current_report_label = tk.Label(current_frame, text="Enter a city for Obo Jr.'s report!", justify=tk.LEFT, bg='white', font=('Arial', 12))
        self.current_report_label.grid(row=0, column=1, sticky='w', padx=10)
        
        self.advice_label = tk.Label(current_frame, text="🤖 Obo Jr.'s Advice will appear here.", justify=tk.LEFT, bg='white', fg='#FF5722', font=('Arial', 12, 'italic'))
        self.advice_label.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        current_frame.grid_columnconfigure(1, weight=1)

        # --- 3. 7-Day Forecast Frame ---
        self.forecast_frame = tk.LabelFrame(self, text="📅 7-Day Forecast (Next 7 Days)", bg='#F0F8FF', padx=10, pady=10, font=('Arial', 14, 'bold'))
        self.forecast_frame.pack(fill='both', expand=True, padx=20, pady=10)

    def load_image_from_url(self, url, size=(50, 50)):
        """Fetches and resizes an image from a URL for Tkinter."""
        try:
            image_data = requests.get(url, stream=True).content
            image = Image.open(BytesIO(image_data))
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    def fetch_all_weather(self):
        """Main handler to fetch and display both current weather and forecast."""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Error", "Please enter a valid city name.")
            return

        # 1. Get Current Weather and Coordinates
        current_data = get_current_weather_and_coords(city)

        if current_data['error']:
            messagebox.showerror("Weather Error", current_data['error'])
            self.current_report_label.config(text=f"Error: {current_data['error']}")
            self.advice_label.config(text="🤖 Obo Jr. can't find that city!")
            self.current_image_label.config(image='')
            self.clear_forecast_widgets()
            return
        
        # --- Update Current Report Section ---
        report_text = f"Location: {current_data['city']}\n"
        report_text += f"Temperature: {current_data['temp']}°C\n"
        report_text += f"Humidity: {current_data['humidity']}%\n"
        report_text += f"Pressure: {current_data['pressure']} hPa\n"
        report_text += f"Description: {current_data['description']}"
        
        self.current_report_label.config(text=report_text)
        
        # Add Advice
        advice = get_obo_jr_advice(current_data['description'], current_data['temp'])
        self.advice_label.config(text=advice, fg='#00008B')
        
        # Load and Display Current Weather Icon
        icon_url = f"{ICON_URL_BASE}{current_data['icon_code']}@2x.png"
        self.current_weather_image = self.load_image_from_url(icon_url, size=(100, 100))
        if self.current_weather_image:
             self.current_image_label.config(image=self.current_weather_image)
             self.current_image_label.image = self.current_weather_image

        # 2. Get 7-Day Forecast using the coordinates
        forecast_data = get_7_day_forecast(current_data['lat'], current_data['lon'])
        self.display_forecast(forecast_data)

    def clear_forecast_widgets(self):
        """Clears previous forecast data from the GUI."""
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()
        self.forecast_images = []
        
    def display_forecast(self, forecast_data):
        """Dynamically builds the 7-day forecast table."""
        self.clear_forecast_widgets()
        
        if not forecast_data:
            tk.Label(self.forecast_frame, text="Could not retrieve 7-Day Forecast.", bg='#F0F8FF').pack(pady=10)
            return

        # Create header row for the forecast table
        headers = ["Icon", "Day", "Temp", "Min/Max", "Description"]
        for col, text in enumerate(headers):
            tk.Label(self.forecast_frame, text=text, font=('Arial', 10, 'bold'), bg='#DDDDFF', relief='raised', width=12).grid(row=0, column=col, padx=1, pady=1, sticky='nsew')
            
        # Display each day's forecast
        for i, day_forecast in enumerate(forecast_data):
            row = i + 1

            # Load and Display Forecast Icon
            icon_url = f"{ICON_URL_BASE}{day_forecast['icon_code']}.png"
            img = self.load_image_from_url(icon_url, size=(40, 40))
            self.forecast_images.append(img)

            img_label = tk.Label(self.forecast_frame, image=img, bg='#F0F8FF')
            img_label.grid(row=row, column=0, padx=5, pady=2)
            
            # Data Labels
            data_labels = [
                day_forecast['day'], 
                f"{day_forecast['temp']}°C", 
                day_forecast['min_max'], 
                day_forecast['description']
            ]
            
            for col_idx, text in enumerate(data_labels):
                 tk.Label(self.forecast_frame, text=text, bg='#F0F8FF', font=('Arial', 10)).grid(row=row, column=col_idx + 1, padx=5, sticky='w')

        # Configure column weights to distribute space evenly
        for col in range(len(headers)):
            self.forecast_frame.grid_columnconfigure(col, weight=1)

# =====================================================
# DRIVER CODE
# =====================================================

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY":
        print("🛑 ERROR: Please replace 'YOUR_API_KEY' in the code with your actual OpenWeather API key.")
        messagebox.showerror("Setup Error", "Please update the API_KEY variable in the code with your key.")
    else:
        app = WeatherApp()
        app.mainloop()