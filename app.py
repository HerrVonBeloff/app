import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import plotly.graph_objects as go

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

    # Создание графика
    fig = go.Figure()

    # Добавление горизонтальной линии для средней температуры
    fig.add_trace(go.Scatter(
        x=[mean_temp, mean_temp],
        y=[-1, 1],
        mode='lines',
        line=dict(color='green', width=2, dash='solid'),
        name='Средняя температура'
    ))

    # Добавление горизонтальных линий для нижней и верхней границ
    fig.add_trace(go.Scatter(
        x=[lower_bound, lower_bound],
        y=[-1, 1],
        mode='lines',
        line=dict(color='green', width=2, dash='dash'),
        name='Нижняя граница'
    ))
    fig.add_trace(go.Scatter(
        x=[upper_bound, upper_bound],
        y=[-1, 1],
        mode='lines',
        line=dict(color='green', width=2, dash='dash'),
        name='Верхняя граница'
    ))

    # Добавление вертикальной линии для текущей температуры
    fig.add_trace(go.Scatter(
        x=[current_temp, current_temp],
        y=[-1.2, 1.2],
        mode='lines',
        line=dict(color='red', width=2, dash='solid'),
        name='Текущая температура'
    ))

    # Добавление закрашенной области между границами
    fig.add_trace(go.Scatter(
        x=[lower_bound, upper_bound, upper_bound, lower_bound],
        y=[-1, -1, 1, 1],
        fill='toself',
        fillcolor='rgba(0, 255, 0, 0.2)',
        line=dict(color='rgba(0, 0, 0, 0)'),
        name='Диапазон температур'
    ))

    # Настройка осей и стилей
    fig.update_layout(
        xaxis=dict(range=[-40, 40], title="Температура (°C)"),
        yaxis=dict(range=[-5, 5], showticklabels=False),
        showlegend=True,
        title="Диапазон температур",
        template="plotly_white"
    )

    # Добавление текста
    fig.add_annotation(
        x=mean_temp, y=-1.8,
        text=f"{mean_temp:.2f} °C",
        showarrow=False,
        font=dict(color='green', size=10)
    )
    fig.add_annotation(
        x=lower_bound, y=-1.8,
        text=f"{lower_bound:.2f} °C",
        showarrow=False,
        font=dict(color='green', size=10)
    )
    fig.add_annotation(
        x=upper_bound, y=-1.8,
        text=f"{upper_bound:.2f} °C",
        showarrow=False,
        font=dict(color='green', size=10)
    )
    fig.add_annotation(
        x=current_temp, y=1.5,
        text=f"{current_temp:.2f} °C",
        showarrow=False,
        font=dict(color='red', size=10)
    )

    # Вывод графика в Streamlit
    st.plotly_chart(fig)

def historical_plot(data, city):
    # Фильтрация данных по городу
    city_data = data[data['city'] == city]

    # Создание графика
    fig = go.Figure()

    # Добавление точек для аномальных и нормальных температур
    fig.add_trace(go.Scatter(
        x=city_data[city_data['anomaly']]['timestamp'],
        y=city_data[city_data['anomaly']]['temperature'],
        mode='markers',
        marker=dict(color='red', size=4, opacity=0.5),
        name='Аномальная температура'
    ))
    fig.add_trace(go.Scatter(
        x=city_data[~city_data['anomaly']]['timestamp'],
        y=city_data[~city_data['anomaly']]['temperature'],
        mode='markers',
        marker=dict(color='green', size=2, opacity=0.5),
        name='Нормальная температура'
    ))

    # Добавление линии скользящего среднего
    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=city_data['moving_avg'],
        mode='lines',
        line=dict(color='darkgreen', width=1),
        name='Скользящее среднее'
    ))

    # Добавление закрашенной области для диапазона
    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=city_data['moving_avg'] + 2 * city_data['moving_std'],
        mode='lines',
        line=dict(color='rgba(0, 100, 0, 0.1)'),
        fill=None,
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=city_data['moving_avg'] - 2 * city_data['moving_std'],
        mode='lines',
        line=dict(color='rgba(0, 100, 0, 0.1)'),
        fill='tonexty',
        fillcolor='rgba(0, 100, 0, 0.1)',
        showlegend=False
    ))

    # Настройка осей и стилей
    fig.update_layout(
        xaxis=dict(title="Время"),
        yaxis=dict(title="Температура (°C)"),
        showlegend=True,
        title=f"Исторические данные для города {city}",
        template="plotly_white"
    )

    # Вывод графика в Streamlit
    st.plotly_chart(fig)
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
                historical_plot(df, city)
                
            else:
                st.warning("Нет исторических данных для анализа")
        else:
            st.error("Что-то пошло не так")