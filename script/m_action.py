import csv
import matplotlib.pyplot as plt
import utils
import preprocess_sessions


def plot(data, title):
    """one mouse action"""
    if len(data) == 0:
        return
    axes = plt.gca()
    axes.set_xlim(0, utils.X_LIMIT)
    axes.set_ylim(0, utils.Y_LIMIT)
    x0 = int(data[0][0])
    y0 = int(data[0][1])
    green = True
    blue = True
    orange = True
    yellow = True
    black = True
    purple = True
    red = True
    brown = True
    for i in range(1, len(data)):
        row = data[i]
        print(i)
        if row[2] == utils.MOUSE_MOVE:
            color = utils.MOUSE_MOVE_COLOR
        elif row[2] == utils.POINT_CLICK:
            color = utils.POINT_CLICK_COLOR
        elif row[2] == utils.DRAG_AND_DROP:
            color = utils.DRAG_AND_DROP_COLOR
        xt = int(row[0])
        yt = int(row[1])
        x = [x0, xt]
        y = [y0, yt]
        if color == 'green' and green:
            plt.plot(x, y, color=color, marker='.', linewidth=1, label='mouse move')
            green = False
        elif color == 'blue' and blue:
            plt.plot(x, y, color=color, marker='.', linewidth=1, label='point click')
            blue = False
        elif color == 'orange' and orange:
            plt.plot(x, y, color=color, marker='.', linewidth=1, label='drag and drop')
            orange = False
        else:
            plt.plot(x, y, color=color, marker='.', linewidth=1)
        x0, y0 = xt, yt
    plt.suptitle(title)
    plt.legend(loc='upper right')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()
    return

def handle_drag_and_drop(data):
    split = preprocess_sessions.split_drag_and_drop(data['mouse_events'][:-1]) - 1
    if split != 0:
        data['to'] = data['from'] + split - 1
        mouse_events = data['mouse_events'][0:split]
        filtered_mouse_events = preprocess_sessions.filter_bad_records(mouse_events)
        if preprocess_sessions.is_long_event(filtered_mouse_events):
            data['mouse_action'] = preprocess_sessions.get_mouse_action_type(filtered_mouse_events)
            data['index_action'] += 1

    data['from'] = data['to'] + 1
    data['to'] = data['index_event'] - 1
    mouse_events = data['mouse_events'][split:]
    filtered_mouse_events = preprocess_sessions.filter_bad_records(mouse_events)
    if preprocess_sessions.is_long_drag_and_drop(filtered_mouse_events):
        data['mouse_action'] = utils.DRAG_AND_DROP

        data['index_action'] += 1


def determine_actions():
    with open(utils.PATH, 'r') as csv_file:
        data_reader = csv.reader(csv_file, delimiter=',')
        next(data_reader)  
        user_name = preprocess_sessions.get_user_name_from_file_name(utils.PATH)
        session = preprocess_sessions.get_session_from_file_name(utils.PATH)
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
        }

        data_plot = []
        data_plot.append([previous_row[4], previous_row[5], 0])

        for row in data_reader:  # reading starts at row 3.
            data_plot.append([row[4], row[5], 0])
            data['row'] = row
            data['mouse_events'].append(data['row'])
            data['index_event'] += 1

            # Check where should split raw data into mouse actions
            if data['row'][3] == 'Move':
                if data['previous_row'][3] == 'Released' \
                        or data['previous_row'][3] == 'Down' \
                        or data['previous_row'][3] == 'Up':

                    if len(data['mouse_events']) > utils.EVENT_LIMIT:
                        data['mouse_action'] = preprocess_sessions.get_mouse_action_type(data['mouse_events'][:-1])
                        data_plot[-1][2] = data['mouse_action']

                        if data['mouse_action'] == utils.DRAG_AND_DROP:
                            handle_drag_and_drop(data)
                            data_plot[-1][2] = data['mouse_action']

                            preprocess_sessions.initialize_variables(data)

                else:
                    # Bad mouse event pattern
                    if data['previous_row'][3] != 'Move' \
                            and data['previous_row'][3] != 'Released' \
                            and data['previous_row'][3] != 'Down' \
                            and data['previous_row'][3] != 'Up':
                        preprocess_sessions.initialize_variables(data)

            else:
                # scroll action
                # Check pause between mouse events, if it splits a complete mouse action
                if (data['row'][3] == 'Down' and data['previous_row'][3] != 'Down'
                    or data['row'][3] == 'Up' and data['previous_row'][3] != 'Up') \
                        or (float(data['row'][1]) - float(data['previous_row'][1]) > utils.TIME_LIMIT
                            and (data['previous_row'][3] == 'Released'
                                 or data['previous_row'][3] == 'Down'
                                 or data['previous_row'][3] == 'Up'
                                 or data['previous_row'][3] == 'Move')):
                    data['mouse_action'] = preprocess_sessions.get_mouse_action_type(data['mouse_events'][:-1])
                    data_plot[-1][2] = data['mouse_action']
                    preprocess_sessions.initialize_variables(data)

            data['previous_row'] = data['row']

        data['mouse_action'] = preprocess_sessions.get_mouse_action_type(data['mouse_events'])
        data_plot[-1][2] = data['mouse_action']
        return data_plot, session, user_name


def fill_in_gaps(data_plot):
    for i in reversed(data_plot):
        if i[2] != 0:
            mouse_type = i[2]
        i[2] = mouse_type
    return data_plot


if __name__ == '__main__':
    data_plot, session, user_name = determine_actions()
    data = fill_in_gaps(data_plot)
    title = 'user' + user_name + '_session_' + session
    plot(data, title)
