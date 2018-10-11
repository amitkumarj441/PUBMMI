import csv
import numpy
import math
import utils

data = {
    'x': [],
    'y': [],
    'dt': [],
    'ds_x': [],
    'ds_y': [],
    'ds': [],
    'v_x': [],
    'v_y': [],
    'v': [],
    'a_x': [],
    'a_y': [],
    'a': [],
    'angles': [],
    'curvatures': [],
    'change_of_curvatures': []
}


def distance(mouse_events):
    data['ds_x'] = []
    data['ds_y'] = []
    data['ds'] = []
    data['x'] = [(int(mouse_events[0][4]))]
    data['y'] = [(int(mouse_events[0][5]))]
    for i in range(1, len(mouse_events)):
        x1 = int(mouse_events[i-1][4])
        x2 = int(mouse_events[i][4])
        y1 = int(mouse_events[i-1][5])
        y2 = int(mouse_events[i][5])
        data['x'].append(int(mouse_events[i][4]))
        data['y'].append(int(mouse_events[i][5]))
        data['ds_x'].append((x2 - x1))
        data['ds_y'].append((y2 - y1))
        data['ds'].append(distance_between(x1, y1, x2, y2))
    return data['ds_x'], data['ds_y'], data['ds']


def time(mouse_events):
    data['dt'] = []
    for i in range(1, len(mouse_events)):
        data['dt'].append(float(mouse_events[i][1]) - float(mouse_events[i - 1][1]))
    return data['dt']

def angles():  
    data['angles'] = []
    for i in range(0, len(data['ds'])):
        data['angles'].append(math.atan2(data['ds_y'][i], data['ds_x'][i]))
    return data['angles']


def curvature():
    data['curvatures'] = []
    for i in range(1, len(data['angles'])):
        if data['ds'][i] != 0:
            d_angle = data['angles'][i] - data['angles'][i-1]
            data['curvatures'].append(d_angle / data['ds'][i])
    return data['curvatures']


def change_of_curvature():
    data['change_of_curvatures'] = []
    for i in range(1, len(data['curvatures'])):
        if data['ds'][i+1] != 0:
            c = data['curvatures'][i] - data['curvatures'][i-1]
            data['change_of_curvatures'].append(c / data['ds'][i+1])
    return data['change_of_curvatures']


def number_of_events(mouse_events):
    return len(mouse_events)

def straightness():
    x1 = int(data['x'][0])
    y1 = int(data['y'][0])
    x2 = int(data['x'][-1])
    y2 = int(data['y'][-1])
    line = distance_between(x1, y1, x2, y2)
    s = summarize(data['ds'])
    if s == 0:
        return 0
    return line / s


def angle_between_three_point(x1, y1, x2, y2, x3, y3):
    a = numpy.array([x1, y1])
    b = numpy.array([x2, y2])
    c = numpy.array([x3, y3])

    d1 = a - b  # [x1-x2, y1-y2]
    d2 = c - b  # [x3-x2, y3-y2]

    norm_d1 = numpy.linalg.norm(d1)  # |d1| = sqrt((x1-x2)^2 + (y1-y2)^2)
    norm_d2 = numpy.linalg.norm(d2)  # |d2| = sqrt((x3-x2)^2 + (y3-y2)^2)
    d1_d2 = numpy.dot(d1, d2)  # d1*d2 = (x1-x2)*(x3-x2) + (y1-y2)*(y3-y2)

    if norm_d1 * norm_d2 != 0.0:
        cosine_angle = d1_d2 / (norm_d1 * norm_d2)  # cos(a) = d1*d2 / |d1|*|d2|
        if cosine_angle > 1.0:
            cosine_angle = 1.0
        if cosine_angle < -1.0:
            cosine_angle = -1.0
        a = numpy.arccos(cosine_angle)  # a = arccos(cos(a))

        return math.degrees(a)
    return 361


def pauses():
    number_of_pauses = 0
    paused_time = 0
    for i in range(0, len(data['dt'])):
        if data['dt'][i] < utils.TIME_PAUSE_LIMIT:
            number_of_pauses += 1
            paused_time += data['dt'][i]
    paused_time_ratio = paused_time / summarize(data['dt'])
    return number_of_pauses, paused_time, paused_time_ratio


def time_to_click(index):
    if index == -1:
        return 0
    else:
        return data['dt'][index]


def direction_of():
    """ Determines the directions of a mouse action. """

    x1 = data['x'][0]
    y1 = data['y'][0]
    x2 = data['x'][-1]
    y2 = data['y'][-1]

    angle_radian = math.atan2(y2-y1, x2-x1)
    angle = math.degrees(angle_radian)
    if angle < 0:
        angle_radian += 2*math.pi
        angle = math.degrees(angle_radian)

    if 22.5 <= angle < 67.5:
        return 1
    if 67.5 <= angle < 112.5:
        return 2
    if 112.5 <= angle < 157.5:
        return 3
    if 157.5 <= angle < 202.5:
        return 4
    if 202.5 <= angle < 247.5:
        return 5
    if 247.5 <= angle < 292.5:
        return 6
    if 292.5 <= angle < 337.5:
        return 7
    return 8


def length_of_line():
    x1 = data['x'][0]
    y1 = data['y'][0]
    x2 = data['x'][-1]
    y2 = data['y'][-1]

    return distance_between(x1, y1, x2, y2)

def distance_between_point_and_line(x1, y1):
    p1 = numpy.array([data['x'][0], data['y'][0]])
    p2 = numpy.array([data['x'][-1], data['y'][-1]])
    p3 = numpy.array([x1, y1])
    if numpy.linalg.norm(p2 - p1) != 0:
        d = numpy.linalg.norm(numpy.cross(p2 - p1, p1 - p3)) / numpy.linalg.norm(p2 - p1)
        return d
    return 0


def is_legal(session):
    s = 'session_' + session
    with open(settings.IS_VALID, 'r') as csv_file:
        data_reader = csv.reader(csv_file, delimiter=',')
        for row in data_reader:
            if row[0] == s:
                return row[1]
    return -1


def minimum(array):
    return min(array)

def maximum(array):
    return max(array)

def mean(array):
    return numpy.mean(array)

def standard_deviation(array):
    return numpy.std(array)

def distance_between(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def summarize(array):
    return sum(array)
