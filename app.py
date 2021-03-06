import pandas as pd
from sqlalchemy import create_engine

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from utils import *
# from math import floor, ceil


app = Flask(__name__)
bootstrap = Bootstrap(app)

if __name__ == '__main__':
    app.run(debug=True)


def connection():
    username = 'postgres'
    pwd = 'Polki123'
    host = '192.168.0.179'
    db = 'postgres'

    engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(username, pwd, host, db))
    return engine


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/aquarium', methods=['POST', 'GET'])
def aquarium():
    if request.method == 'POST':
        aquarium_post(request.query_string.decode())
    elif request.methos == 'GET':
        aquarium_get()

    return ('', 204)


def aquarium_post(stream):
    # Parse post data
    print(stream)
    sensors_values = [x.split(',') for x in stream.split(';')]  # split data into sensors
    conn = connection()

    # prepare query string
    query = "insert into public.readings (id_sensor, value, timestamp) values "
    _query = "({_id_sensor}, {_value}, '{_timestamp}')"
    values = []

    for sensor_data in sensors_values:
        # get entry data
        _id_sensor = sensor_data[0]
        _value = sensor_data[1]
        _timestamp = sensor_data[2]

        # add new entry into the list
        values.append(_query.format(_id_sensor=_id_sensor, 
                                    _value=_value, 
                                    _timestamp=_timestamp))     

    query += ','.join(values) + ';'  # prepare query string
    conn.execute(query)  # insert data into db

    return


def aquarium_get():
    raise NotImplementedError


@app.route('/')
@app.route('/scheduler')
def scheduler():
    conn = connection()
    df = pd.read_sql("select id, day, hour, amount, active from aquarium.water_change", index_col='id', con=conn)
    # df['active'] = df['active'].astype(int)

    # df = pd.read_csv('scheduler.csv', sep=';', index_col='id')
    df.sort_index(inplace=True)

    rows = df.to_dict(orient='row')

    df_light_program = pd.read_sql("select id, name, timestamp_from, timestamp_to from aquarium.lightning", con=conn)
    # df_light_program = pd.read_csv('light.csv', sep=';', index_col='id')
    light_programs = df_light_program.to_dict(orient='row')
    
    return render_template('scheduler.html',
                           rows=rows,
                           programs=light_programs)


@app.route('/')
@app.route('/stats')
def stats():
    # conn = connection('aquarium_arduino', 'test')
    # df = pd.read_sql("select * from v_readings where id_sensor=1 order by 1, 2, 3, 4", conn)

    df = pd.read_csv(r'data.csv', sep=';')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values(by='timestamp', inplace=True)
 
    # get available sensors
    sensors = df[['id_sensor', 'sensor_name']].\
        drop_duplicates().to_dict(orient='records')

    groups = df.groupby(by='id_sensor')[['value', 'timestamp']]  # group sensor data
    sensors_data = {}  # containter for chart data

    # loop throught sensors
    for key, group in groups:
        labels = group['timestamp'].tolist()
        values = group['value'].apply(lambda x: round(x, 2)).tolist()  
        sensors_data[key] = {'labels': labels, 'values': values}

    labels = df['timestamp']
    values = df['value'].apply(lambda x: round(x, 2))

    return render_template('stats.html', 
                           values=values,
                           labels=labels,
                           sensors=sensors,
                           sensors_data=sensors_data)
