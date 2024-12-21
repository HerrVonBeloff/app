import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle


def get_current_temperature(city, api_key):
    global BASE_URL
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    response = requests.get(BASE_URL, params=params)
    return response.json()['main']['temp']


def is_current_temperature_anomaly(data, city, current_temp):
    current_month = datetime.now().month

    month_data = data[(data['city'] == city) & (data['timestamp'].dt.month == current_month)]

    if month_data.empty:
        print(f"No data for {city} and month {current_month}")
        return False
    
    mean_temp = month_data['temperature'].mean()
    std_temp = month_data['temperature'].std()

    is_anomaly = abs(current_temp-mean_temp) >= 2*std_temp

    return is_anomaly, mean_temp, std_temp

def default_analys(data):
    data['moving_avg'] = data.groupby('city')['temperature'].rolling(window=30).mean().reset_index(0, drop=True)
    data['moving_std'] = data.groupby('city')['temperature'].rolling(window=30).std().reset_index(0, drop=True)

    data['moving_avg'] = data['moving_avg'].fillna(method='bfill')
    data['moving_std'] = data['moving_std'].fillna(method='bfill')

    data['anomaly'] = (abs(data['temperature'] - data['moving_avg'])>=2*data['moving_std'])

    return data

def plot_horizontal_temperature_range(mean_temp, std_temp, current_temp):
    lower_bound = mean_temp - 2 * std_temp
    upper_bound = mean_temp + 2 * std_temp

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot([mean_temp, mean_temp], [-1, 1], color='green', alpha=0.5)
    ax.plot([lower_bound, lower_bound], [1, -1], color='green', alpha=0.5)
    ax.plot([upper_bound, upper_bound], [1, -1], color='green', alpha=0.5)

    ax.plot([current_temp, current_temp], [1.2, -1.2], color='red', alpha=0.6)
    ax.add_patch(Rectangle((lower_bound, -1), upper_bound-lower_bound, 2, color='green', alpha=0.2))

    ax.spines['bottom'].set_position(('data', 0))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)


    ax.set_ybound(-5, 5)
    ax.set_xbound(-40, 40)
    ax.set_yticks([]) 
    ax.text(mean_temp, -1.8, f"{mean_temp:.2f} °C", color='green', ha='center', va='bottom', fontsize=10)
    ax.text(lower_bound, -1.8, f"{lower_bound:.2f} °C", color='green', ha='center', va='bottom', fontsize=10)
    ax.text(upper_bound, -1.8, f"{upper_bound:.2f} °C", color='green', ha='center', va='bottom', fontsize=10)
    ax.text(current_temp, 1.5, f"{current_temp:.2f} °C", color='red', ha='center', va='bottom', fontsize=10)
    st.pyplot(fig)

def historical_plot(data):
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.scatter(data[(data['city']==city) & (data['anomaly']==True)]['timestamp'], 
                data[(data['city']==city) & (data['anomaly']==True)]['temperature'], 
                s=2, 
                alpha=0.5,
                color='r'
                )
    ax.scatter(data[(data['city']==city) & (data['anomaly']==False)]['timestamp'], 
                data[(data['city']==city) & (data['anomaly']==False)]['temperature'], 
                s=1, 
                alpha=0.5,
                color='green'
                )
    ax.plot(data[data['city']==city]['timestamp'], data[data['city']==city]['moving_avg'], color='darkgreen', alpha=0.7, linewidth=0.7)
    ax.fill_between(data[data['city']==city]['timestamp'], 
                    data[data['city']==city]['moving_avg']+2*data[data['city']==city]['moving_std'],
                    data[data['city']==city]['moving_avg']-2*data[data['city']==city]['moving_std'],
                    color='darkgreen',
                    alpha=0.1
                    )
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    st.pyplot(fig)
st.title("Temperature Anomaly Detection")


df = st.file_uploader("Загрузите CSV файл", type=["csv"])

if df is not None:
    df = pd.read_csv(df)
    st.write("Загруженный датасет:")
else:
    st.write("Файл не загружен. Используется дефолтный датасет.")
    df = pd.read_csv("temperature_data.csv")

df = pd.read_csv('temperature_data.csv')
df = default_analys(df)
df['timestamp'] = pd.to_datetime(df['timestamp'])

BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
api_key = st.text_input("Введите API Key:")
city = st.selectbox("Выберите город", df['city'].unique())

if st.button("Проверить температуру"):
    if not api_key:
        st.error("Введите API key.")
    else:
        current_temp = get_current_temperature(city, api_key)
        if current_temp is not None:
            is_anomaly, mean_temp, std_temp = is_current_temperature_anomaly(df, city, current_temp)

            st.write(f"Текущая температура {city}: {current_temp} °C")



            if mean_temp is not None:
                if is_anomaly:
                    st.error("Текущая температура аномальна")
                else:
                    st.success("Текущая температура в пределах нормы")
                st.write(f"Средняя температура в текущем месяце: {mean_temp:.2f} °C")
                st.write(f"Диапазон допустимых температур: ({mean_temp-2*std_temp:.2f} ;{mean_temp+2*std_temp:.2f}) °C")
                plot_horizontal_temperature_range(mean_temp, std_temp, current_temp)
                historical_plot(df)
                
            else:
                st.warning("Нет исторических данных для анализа")
        else:
            st.error("Что-то пошло не так")