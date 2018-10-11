import os
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelBinarizer
from sklearn.utils import shuffle

# mouse actions
MOUSE_MOVE = 1
POINT_CLICK = 2
DRAG_AND_DROP = 3

# preprocessing
X_LIMIT = 1920
Y_LIMIT = 1080
EVENT_LIMIT = 5
TIME_LIMIT = 10
CRITICAL_POINT = 0.0005  # change of curvature
ANGLE_LIMIT = 20.0
TIME_PAUSE_LIMIT = 0.1

# plot
MOUSE_MOVE_COLOR = 'green'
POINT_CLICK_COLOR = 'blue'
DRAG_AND_DROP_COLOR = 'orange'

def timestamp_to_dts(timestamps):
    """ Converts a list of timestamps to time-deltas """
    orig = timestamps[0]
    timestamps = [i-orig for i in timestamps]
    timestamps[1:] = [timestamps[idx+1] - timestamps[idx] for idx, i in enumerate(timestamps[1:])]
    return timestamps

def fix_data(df):
    """convert timestamps to time-deltas or removing some nasty outliers """
    df['record timestamp'] = timestamps_to_dts(df['record timestamp'])
    df['client timestamp'] = timestamps_to_dts(df['client timestamp'])
    df = df.rename(columns = 
               {'client timestamp': 'client_dt', 'record timestamp' : 'record_dt'})
    df = df[df.client_dt < df.client_dt.quantile(.95)]
    df = df[df.record_dt < df.record_dt.quantile(.95)]
    df = df[df.x < 5000]
    return df

def load_mouse_dynamics_dataset():
    """
    training, validation, and testing
    """
    
    training_sessions = [] 
    validation_sessions = [] 
    testing_sessions = [] 
    
    dataset_path = '/home/ith/Practice/predict-users-behavior/mouse_dataset/'
    training_files_path = os.path.join(dataset_path, 'training_files')
    testing_files_path = os.path.join(dataset_path, 'test_files')
 
    # Load public labels, these are for the testing set, the labels only indicate if the user input
    labels_path = os.path.join(dataset_path, 'public_labels.csv')
    labels = pd.read_csv(labels_path)
    session_to_label = {labels['filename'][idx]: labels['is_illegal'][idx] for idx in range(len(labels))}
    
    user_names = os.listdir(training_files_path)
    
    # Load training and testing data for each user
    for user_name in user_names:
        
        user_id = user_name[4:]
        
        # Load training sessions
        user_training_path = os.path.join(training_files_path, user_name)
        training_session_names = os.listdir(user_training_path)
        
        for session_name in training_session_names:
            
            session_id = session_name[8:]
            df_session = pd.read_csv(os.path.join(user_training_path, session_name))
            
            # Fix some errors and issues in the data
            df_session = fix_data(df_session)
                
            training_sessions.append({ 
                'user_id': int(user_id), 
                'session_id' : int(session_id), 
                'data': df_session
            })
        
        # Load testing sessions
        user_testing_path = os.path.join(testing_files_path, user_name)
        testing_session_names = os.listdir(user_testing_path)
        
        for session_name in testing_session_names:
            
            session_id = session_name[8:]
            df_session = pd.read_csv(os.path.join(user_testing_path, session_name))
            df_session = fix_data(df_session)
            
            try:
                is_illegal = session_to_label[session_name]
                
                # We don't want illegal sessions for now
                if not is_illegal:
                    validation_sessions.append({
                        # assign special user_id of 0 to illegal users 
                        'user_id': int(user_id) if is_illegal == 0 else 0, 
                        'session_id' : int(session_id), 
                        'data': df_session
                    })
            except KeyError:   
   
                testing_sessions.append({
                    # assign special user_id = -1 to unlabeled sessions
                    'user_id': -1, 
                    'session_id' : int(session_id), 
                    'data': df_session
                })
                
    return training_sessions, validation_sessions, testing_sessions

def print_stats(sessions, name):
    """
    Prints info about either training validation or testing sessions
    """
    average_size = np.average([len(i['data']) for i in sessions])
    print('[*] Loaded {} {} sessions with an average of {:.2f} data points'.format(
        len(sessions), name, average_size))
    user_ids = [i['user_id'] for i in sessions]
    print('{} sessions per user: {}'.format(name, dict(Counter(user_ids))))

def sessions_to_dataframe(sessions):
    df = pd.DataFrame()
    for session in sessions:
        df_sess = pd.DataFrame(session['data'])
        
        df_sess['user_id'] = session['user_id']
        df = df.append(df_sess)
        
    return df
        
def preprocess_data(df):
    """ 
    Preprocess a dataframe:
    - Normalizes the numerical variables
    - One hot encodes the categorical variables
    - Drops unused features
    """

    # Give 0 mean and unit variance to data
    standard_scaler = StandardScaler()
    df[['client_dt', 'x', 'y']] = standard_scaler.fit_transform(df[['client_dt', 'x', 'y']])
    
    # One-hot encode categorical variables
    df = pd.concat([df, pd.get_dummies(df['state'])], axis=1);
    df = pd.concat([df, pd.get_dummies(df['button'])], axis=1);
    
    # Drop unused columns
    df = df.drop(['record_dt', 'button', 'state'], axis = 1)
    
    return df

def data_to_machine_learning_examples(df, seq_size):
    """
    Division of the data into training examples, also
    makes a one hot encoding of the labels
    """

    x = None
    y = None
    
    binarizer = LabelBinarizer()
    binarizer.fit(df['user_id'])
    classes_ = binarizer.classes_

    local_users = [20, 7, 9]
    remote_users = [16, 35, 21, 23, 12, 15, 29]
    
    for class_ in classes_:
        
        one_class_data = df[df.user_id == class_]
        one_class_data = one_class_data.drop(['user_id'], axis = 1)

        np_data = one_class_data.values
        num_examples = np_data.shape[0] // seq_size
        np_data = np_data[:num_examples * seq_size] 
        np_data = np.array(np.vsplit(np_data, num_examples))
        
        if x is None :
            x = np_data
        else:
            x = np.concatenate([x, np_data])

        labels = np.full(np_data.shape[0], class_, dtype=np.int32)
        
        if y is None:
            y = labels
        else:
            y = np.concatenate([y, labels])
    
    # One hot encoding of labels
    encoder = OneHotEncoder(sparse=False)
    encoder.fit(y.reshape(-1, 1))
    y = encoder.transform(y.reshape(-1, 1))
    
    # randomize example order
    x, y = shuffle(x, y, random_state = 0)
    
    return x, y
