import csv
import utils
import m_action

def get_user_name_from_file_name(file_path):
    path = file_path[::-1]  
    pos = path.find('/')  
    rest = path[pos + 1::]  
    pos = rest.find('/')  
    user = rest[:pos]  
    user = user[::-1] 
    user = user[4:] 
    return user

def get_session_from_file_name(file_path):
    path = file_path[::-1]  
    pos = path.find('/')  
    session = path[:pos]
    session = session[::-1]  
    length = len('session_')
    return session[length:]

def get_mouse_action_type(mouse_events):
    # mouse move
    if mouse_events[-1][3] == 'Move':
        return utils.MOUSE_MOVE

    # mouse click
    if mouse_events[-1][3] == 'Released' and mouse_events[-2][3] == 'Pressed' \
            and (len(mouse_events) == 2 or mouse_events[-3][3] == 'Move'):
        return utils.POINT_CLICK

    # drag and drop
    if mouse_events[-1][3] == 'Released':
        index = len(mouse_events) - 2
        number_of_drag = 1
        while mouse_events[index][3] == 'Drag':
            index -= 1
            number_of_drag += 1
        if mouse_events[index][3] == 'Pressed':
            prev_x = mouse_events[index][4]
            prev_y = mouse_events[index][5]
            travelled_distance_x = 0
            travelled_distance_y = 0
            for i in range(index + 1, len(mouse_events) - 2):
                travelled_distance_x += abs(int(prev_x) - int(mouse_events[i][4]))
                travelled_distance_y += abs(int(prev_y) - int(mouse_events[i][5]))
                prev_x = mouse_events[i][4]
                prev_y = mouse_events[i][5]
            if travelled_distance_x < 3 and travelled_distance_y < 3:
                if number_of_drag > utils.LONG_CLICK_LIMIT:
                    return utils.LONG_CLICK
                else:
                    return utils.POINT_CLICK
            else:
                return utils.DRAG_AND_DROP

def is_long_event(mouse_events):
    number_of_moves = 0
    for i in range(0, len(mouse_events)):
        if mouse_events[i][3] == 'Move':
            number_of_moves += 1
    if number_of_moves <= utils.EVENT_LIMIT:
        return False
    return True


def is_long_drag_and_drop(mouse_events):
    number_of_drags = 0
    for i in range(0, len(mouse_events)):
        if mouse_events[i][3] == 'Drag':
            number_of_drags += 1
    if number_of_drags <= utils.EVENT_LIMIT:
        return False
    return True


def determine_actions(file_path, data_writer):
    with open(file_path, 'r') as csv_file:
        data_reader = csv.reader(csv_file, delimiter=',')
        next(data_reader) 

        user_name = get_user_name_from_file_name(file_path)
        session = get_session_from_file_name(file_path)
        previous_row = next(data_reader)
        mouse_events = [previous_row]

        data = {
            'user_name': user_name,
            'session': session,
            'index_event': 2,
            'index_action': 1,
            'mouse_events': mouse_events,
            'from': 2,
            'to': 2,
            'previous_row': previous_row,
            'row': previous_row,
            'data_writer': data_writer
        }
        attributes = {
            'ds_x': 0,
            'ds_y': 0,
            'd': 0,
            'ds': 0,
            'dt': 0,
            'vx': 0,
            'vy': 0,
            'v': 0,
            'min_vx': 0,
            'max_vx': 0,
            'mean_vx': 0,
            'std_vx': 0,
            'min_vy': 0,
            'max_vy': 0,
            'mean_vy': 0,
            'std_vy': 0,
            'min_v': 0,
            'max_v': 0,
            'mean_v': 0,
            'std_v': 0,
            'min_a': 0,
            'max_a': 0,
            'mean_a': 0,
            'std_a': 0,
            'min_jerk': 0,
            'max_jerk': 0,
            'mean_jerk': 0,
            'std_jerk': 0,
            'min_angle': 0,
            'max_angle': 0,
            'mean_angle': 0,
            'std_angle': 0,
            'sum_of_angles': 0,
            'min_ang_vel': 0,
            'max_ang_vel': 0,
            'mean_ang_vel': 0,
            'std_ang_vel': 0,
            'min_curv': 0,
            'max_curv': 0,
            'mean_curv': 0,
            'std_curv': 0,
            'min_d_curv': 0,
            'max_d_curv': 0,
            'mean_d_curv': 0,
            'std_d_curv': 0,
            'number_of_events': 0,
            'straightness': 0,
            'critical_points': 0,
            'number_of_pauses': 0,
            'paused_time': 0,
            'paused_time_ratio': 0,
            'time_to_click': 0,
            'direction': 0,
            'length_of_line': 0,
            'largest_deviation': 0,
            'is_legal': 0
        }

        for row in data_reader:  # reading starts at row 3.
            data['row'] = row
            data['mouse_events'].append(data['row'])
            data['index_event'] += 1

            if data['row'][3] == 'Move':
                if data['previous_row'][3] == 'Released' \
                        or data['previous_row'][3] == 'Down' \
                        or data['previous_row'][3] == 'Up':

                    if len(data['mouse_events']) > utils.EVENT_LIMIT:
                        data['mouse_action'] = get_mouse_action_type(data['mouse_events'][:-1])

                        if data['mouse_action'] == utils.DRAG_AND_DROP:
                            handle_drag_and_drop(data, attributes)

                        else:
                            record_mouse_action(data, -1, attributes)
                    initialize_variables(data)

                else:
                    # Bad mouse event pattern
                    if data['previous_row'][3] != 'Move' \
                            and data['previous_row'][3] != 'Released' \
                            and data['previous_row'][3] != 'Down' \
                            and data['previous_row'][3] != 'Up':
                        initialize_variables(data)

            else:
                # Check pause between mouse events, if it splits a complete mouse action
                if (data['row'][3] == 'Down' and data['previous_row'][3] != 'Down'
                    or data['row'][3] == 'Up' and data['previous_row'][3] != 'Up') \
                        or (float(data['row'][1]) - float(data['previous_row'][1]) > utils.TIME_LIMIT
                            and (data['previous_row'][3] == 'Released'
                                 or data['previous_row'][3] == 'Down'
                                 or data['previous_row'][3] == 'Up'
                                 or data['previous_row'][3] == 'Move')):
                    data['mouse_action'] = get_mouse_action_type(data['mouse_events'][:-1])
                    record_mouse_action(data, -1, attributes)
                    initialize_variables(data)

            data['previous_row'] = data['row']

        data['mouse_action'] = get_mouse_action_type(data['mouse_events'])
        record_mouse_action(data, 0, attributes)
        return


def initialize_variables(data):
    data['from'] = data['index_event']
    data['mouse_events'] = [data['row']]


def split_drag_and_drop(mouse_events):
    number_of_mouse_moves = 0
    index = 0
    while mouse_events[index][3] != 'Drag':
        number_of_mouse_moves += 1
        index += 1
    return number_of_mouse_moves


def handle_drag_and_drop(data, attributes):
    split = split_drag_and_drop(data['mouse_events'][:-1]) - 1
    if split != 0:
        data['to'] = data['from'] + split - 1
        mouse_events = data['mouse_events'][0:split]
        filtered_mouse_events = filter_bad_records(mouse_events)
        if is_long_event(filtered_mouse_events):
            data['mouse_action'] = get_mouse_action_type(filtered_mouse_events)
            determine_attributes(filtered_mouse_events, attributes, data['session'])
            if attributes['ds'] == 0:
                return
            make_new_record(data, attributes)
            data['index_action'] += 1

    data['from'] = data['to'] + 1
    data['to'] = data['index_event'] - 1
    mouse_events = data['mouse_events'][split:]
    filtered_mouse_events = filter_bad_records(mouse_events)
    if is_long_drag_and_drop(filtered_mouse_events):
        determine_attributes(filtered_mouse_events, attributes, data['session'])
        if attributes['ds'] == 0:
            return
        data['mouse_action'] = utils.DRAG_AND_DROP
        make_new_record(data, attributes)

        data['index_action'] += 1


def filter_bad_records(mouse_events):
    filtered_mouse_events = []
    previous_row = mouse_events[0]
    for i in range(1, len(mouse_events)):
        row = mouse_events[i]
        if (float(previous_row[1]) == float(row[1])
            and previous_row[3] == row[3]) \
                or (int(previous_row[4]) >= utils.X_LIMIT
                    or int(previous_row[5]) >= utils.Y_LIMIT):
            previous_row = row
            continue
        filtered_mouse_events.append(previous_row)
        previous_row = row
    filtered_mouse_events.append(previous_row)
    return filtered_mouse_events


def get_first_press(mouse_events):
    index = 0
    while index < len(mouse_events) and mouse_events[index][3] != 'Pressed':
        index += 1
    if index >= len(mouse_events) - 1:
        return -1
    return index


def determine_attributes(filtered_mouse_events, attributes, session):
    attributes['ds_x'], attributes['ds_y'], attributes['d'] = m_action.distance(filtered_mouse_events)
    attributes['dt'] = m_action.summarize(m_action.time(filtered_mouse_events))
    attributes['ds'] = m_action.summarize(attributes['d'])

    angle = m_action.angles()
    attributes['min_angle'] = m_action.minimum(angle)
    attributes['max_angle'] = m_action.maximum(angle)
    attributes['mean_angle'] = m_action.mean(angle)
    attributes['std_angle'] = m_action.standard_deviation(angle)
    attributes['sum_of_angles'] = m_action.sum_of_angles()

    curvature = m_action.curvature()
    attributes['min_curv'] = m_action.minimum(curvature)
    attributes['max_curv'] = m_action.maximum(curvature)
    attributes['mean_curv'] = m_action.mean(curvature)
    attributes['std_curv'] = m_action.standard_deviation(curvature)

    d_curvature = m_action.change_of_curvature()
    attributes['min_d_curv'] = m_action.minimum(d_curvature)
    attributes['max_d_curv'] = m_action.maximum(d_curvature)
    attributes['mean_d_curv'] = m_action.mean(d_curvature)
    attributes['std_d_curv'] = m_action.standard_deviation(d_curvature)

    attributes['number_of_events'] = m_action.number_of_events(filtered_mouse_events)
    attributes['straightness'] = m_action.straightness()
    attributes['critical_points'] = m_action.number_of_critical_points()
    attributes['number_of_pauses'], attributes['paused_time'], attributes['paused_time_ratio'] = \
        m_action.pauses()

    index = get_first_press(filtered_mouse_events)
    attributes['time_to_click'] = m_action.time_to_click(index)
    attributes['direction'] = m_action.direction_of()
    attributes['length_of_line'] = m_action.length_of_line()
    attributes['largest_deviation'] = m_action.largest_deviation()
    attributes['is_legal'] = m_action.is_legal(session)


def make_new_record(data, attributes):
    data['data_writer'].writerow(
        [data['user_name'], data['session'], data['index_action'], data['mouse_action'], data['from'], data['to'],
         attributes['ds'], attributes['dt'],
         attributes['min_angle'], attributes['max_angle'], attributes['mean_angle'], attributes['std_angle'],
         attributes['sum_of_angles'],
         attributes['min_ang_vel'], attributes['max_ang_vel'], attributes['mean_ang_vel'], attributes['std_ang_vel'],
         attributes['min_curv'], attributes['max_curv'], attributes['mean_curv'], attributes['std_curv'],
         attributes['min_d_curv'], attributes['max_d_curv'], attributes['mean_d_curv'], attributes['std_d_curv'],
         attributes['number_of_events'], attributes['straightness'], attributes['critical_points'],
         attributes['number_of_pauses'], attributes['paused_time'], attributes['paused_time_ratio'],
         attributes['time_to_click'],
         attributes['direction'], attributes['length_of_line'], attributes['largest_deviation'],
         attributes['is_legal']])
