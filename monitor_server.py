# !/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from cgi import parse_header, parse_qs
from multiprocessing import Queue
from urllib.parse import urlparse, parse_qs
import http.client
from collections import defaultdict
import json
import os
import monitor
from time import strftime, localtime
import psutil

def tail(f, lines=1, _buffer=4098):
    """Tail a file and get n lines from the end
    taken from: http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
    """
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]


def send_header(BaseHTTPRequestHandler, format='HTML'):
    if format.upper() == 'HTML':
        BaseHTTPRequestHandler.send_response(200)
        BaseHTTPRequestHandler.send_header('Access-Control-Allow-Origin', '*')
        BaseHTTPRequestHandler.send_header('Content-type:', 'text/html')
        BaseHTTPRequestHandler.end_headers()
        BaseHTTPRequestHandler.wfile.write(bytes('\n', 'utf-8'))
        BaseHTTPRequestHandler.wfile.write(bytes('<html>\n', 'utf-8'))
    elif format.upper() == 'JSON':
        BaseHTTPRequestHandler.send_response(200)
        BaseHTTPRequestHandler.send_header('Access-Control-Allow-Origin', '*')
        BaseHTTPRequestHandler.send_header('Content-type:', 'application/json')
        BaseHTTPRequestHandler.end_headers()


def get_cpu_cores(url, port=8003, default=-1):
    # prevent dead lock by requesting own URL
    if myownsocket == url:
        return int(psutil.cpu_count())

    try:
        conn = http.client.HTTPConnection(url, port)
        conn.request('GET', '/cpuInfo')
        conn.timeout = 1
        r1 = conn.getresponse()
    except:
        return default
    if r1.status == 200:
        data1 = str(r1.read())
        if data1.find('{') < data1.find('}'):
            data1 = data1[data1.find('{'):data1.find('}') + 1]
            return json.loads(data1).get('CPU Cores')
    return default


class MyRequestHandler(BaseHTTPRequestHandler):
    def parameters_cpu_temperature(self, parameters):
        if 'interval' in parameters.keys():
            interval = int(parameters['interval'])
        else:
            interval = 1
        if 'start' in parameters.keys():
            start = parameters['start']
        else:
            start = -1
        if 'end' in parameters.keys():
            end = parameters['end']
        else:
            end = -1
        if 'last' in parameters.keys():
            last = int(parameters['last'])
        else:
            last = 300

    def do_GET(self):
        # checks if the server is alive
        if self.path == '/test':
            send_header(self)
            self.wfile.write(bytes('passed<br>', 'utf-8'))
            self.wfile.write(bytes('server is responding', 'utf-8'))
        # returns the running processes

        elif self.path == '/cpu_temperature':
            send_header(self, format='JSON')
            parsed = urlparse(self.path)
            parameters = parse_qs(parsed.query)
            last = 300
            interval = 1
            with open('cpu_temperature.log', 'r') as f:
                lines = tail(f, lines=last * interval)

            timestamps = list()
            values = defaultdict(list)
            # reads and stores the values
            for i in range(0, len(lines), interval):
                cells = lines[i].split('\t')
                timestamps.append(cells[0])
                cores = cells[1].split(';')
                for i, value in enumerate(cores):
                    values[i].append(float(value))
            # creates the dictionary to pass it as a JSON
            averages = list()
            data = list()
            #for i in range(len(cores)):
            min_values = list()
            max_values = list()
            avg_values = list()
            for i in range(len(timestamps)):
                min_values.append(min([values[value][i] for value in values]))
                max_values.append(max([values[value][i] for value in values]))
                avg_values.append(float(sum([values[value][i] for value in values])) / len(values))
            averages.append({'x': timestamps, 'y': min_values, 'line': {'width': 0}, 'marker': {'color': '"444"'}, 'mode': '"lines"', 'name': '"Lower Bound"', 'type': '"scatter"'})
            averages.append({'x': timestamps, 'y': avg_values, 'fill': 'tonexty', 'fillcolor': '"rgba(68, 68, 68, 0.3)"', 'line': {'color': "rgb(31, 119, 180)"}, 'mode': '"lines"', 'name': '"Average"', 'type': '"scatter"'})
            averages.append({'x': timestamps, 'y': max_values, 'fill': 'tonexty', 'fillcolor': '"rgba(68, 68, 68, 0.3)"', 'line': {'width': 0}, 'marker': {'color': '"444"'}, 'mode': '"lines"', 'name': '"Upper Bound"', 'type': '"scatter"'})
            for i, value in enumerate(values):
                data.append({'x': timestamps, 'y': values[i]})
            self.wfile.write(bytes(json.dumps({'data': data, 'averages': averages}), 'utf-8'))
        elif self.path == '/current_cpu_temperature':
            send_header(self, format='JSON')
            sensor = monitor.sensors()
            temperatures = sensor.get_core_temperatures()
            timestamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
            data = list()
            for temperature in temperatures:
                data.append({'x': timestamp, 'y': temperature})
            self.wfile.write(bytes(json.dumps({'data': data, 'averages': {}}), 'utf-8'))
        elif self.path == '/cpu_usage':
            send_header(self, format='JSON')
            psutil.cpu_percent(interval=0.0, percpu=True)
            usage = psutil.cpu_percent(interval=0.01, percpu=True)
            data = list()
            time_stamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
            # merge threads to cores if needed
            if psutil.cpu_count(logical=True) != psutil.cpu_count(logical=False):
                threads = int(psutil.cpu_count(logical=True) / psutil.cpu_count(logical=False))
                merged_data = list()
                for i in range(0, psutil.cpu_count(), threads):
                    for t in range(threads):
                        avg = usage[i + t]
                    merged_data.append(float(avg) / float(t))
                usage = merged_data

            for u in usage:
                data.append({'x': time_stamp, 'y': u})
            average = float(sum([u for u in usage])) / len(usage)
            self.wfile.write(bytes(json.dumps({'data': data, 'average': average}), 'utf-8'))
        elif self.path == '/disk_usage':
            send_header(self, format='JSON')
            devices = dict()
            disks = psutil.disk_partitions(all=False)
            for disk in disks:
                try:
                    devices[disk.device] = [psutil.disk_usage(disk.mountpoint).total,
                                            psutil.disk_usage(disk.mountpoint).free]
                except:
                    pass
            self.wfile.write(bytes(json.dumps(devices), 'utf-8'))


        else:
            send_header(self)
            self.wfile.write(bytes(str(self.client_address), 'utf-8'))
            self.wfile.write(bytes("<br>", 'utf-8'))
            self.wfile.write(bytes(self.path, 'utf-8'))
            print(self.path)


if __name__ == '__main__':
    # start server
    server = HTTPServer(('', 8004), MyRequestHandler)
    server.serve_forever()


