# Import libraries
import os
import numpy as np
import pandas as pd
from IPython.display import display, HTML
import matplotlib.pyplot as plt
%matplotlib inline
import math

from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import MinMaxScaler

# Formation of data matrices from local files with user sessions
# Dataset is used from the repository https://github.com/balabit/Mouse-Dynamics-Challenge
DATA_DIR = os.getcwd() + '/data/test_files/'
users_sessions = os.listdir(DATA_DIR)
all_sessions = {i: os.listdir(DATA_DIR + i) for i in users_sessions}
print('Number of users: %s' % len(all_sessions.keys()))
print('Total number of sessions: %s' % sum([len(v) for v in all_sessions.values()]))

# Creation of a matrix of data from all sessions of one user
def get_user_sessions(num_user):
    session = list(all_sessions.keys())[num_user]
    user_files = [DATA_DIR + session + '/' + i for i in all_sessions[session]]
    return user_files


def file_to_list(file):
    with open(file) as f:
        lt = f.readlines()
    return lt

def make_user_dataset(user_files):
    dataset = []
    columns = False
    for i in user_files:
        dataset += file_to_list(i)[1:]
        if not columns:
            columns = [i.replace(' ', '_').replace('\n', '').split(',')
                       for i in file_to_list(i)[0:1]][0]
    dataset = [i.replace('\n', '').split(',') for i in dataset]
    data = pd.DataFrame(dataset, columns=columns)
    return data

num_user = 0 # first user in the list
data = make_user_dataset(get_user_sessions(num_user))
print('Sliced raw data table')
display(data[:30])

# Data preprocessing
# obtain one-hot matrix from categorical data
cols_to_retain = ['button', 'state']
pr_data = data[cols_to_retain].to_dict(orient='records_timestamp')
vec = DictVectorizer(sparse=False, dtype=float)
one_hot_data = vec.fit_transform(pr_data)

# scalarization of numerical data
cols_to_scal = ['client_timestamp', 'x', 'y']
scaler = MinMaxScaler(feature_range=(0, 1), copy=False)
data_scal = scaler.fit_transform(data[cols_to_scal])

category = vec.get_feature_names()
print('List of main categories\n')
print(category)
print('Categories after conversion\n')
print(one_hot_data[:5])

# formation of the processed matrix
pr_data = np.hstack((data_scal, one_hot_data)).astype(float)
print("Converted data table")
print(pr_data[:12])
# Hyperparameter tuning
STEP = 50
SPL = 0.7

# Vectorization
def vectorizeXY(data, seq):
    X = np.zeros((data.shape[0], seq, data.shape[1]))
    Y = np.zeros((data.shape[0], data.shape[1]))
    for i in range(len(data) - seq - 1):
        X[i] = data[i:i + seq]
        Y[i] = data[i + seq + 1]
    return X, Y

def split_data(X, Y, spl):
    trainX = X[:int(len(X)*spl)]
    trainY = Y[:int(len(X)*spl)]
    testX = X[int(len(X)*spl):]
    testY = Y[int(len(X)*spl):]
    return trainX, testX, trainY, testY
    
# values of displacements, normalize
dataXY = data[['x', 'y']].values.astype('float')/1024
X, Y = vectorizeXY(dataXY, STEP)
trainX, testX, trainY, testY = split_data(X, Y, SPL)
print(trainX.shape, testX.shape, trainY.shape, testY.shape)

# LSTM Model
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Activation
from keras.callbacks import ModelCheckpoint
from keras.utils.vis_utils import plot_model as plot

model = Sequential()
model.add(LSTM(64, return_sequences=False, input_shape=(trainX.shape[1],
                                                        trainX.shape[2])))
model.add(Dense(trainY.shape[1], activation='relu'))
model.compile(loss='mse', optimizer='adam', metrics=["mean_squared_error"])
model.summary()
history = model.fit(trainX, trainY, batch_size=6000,
                    epochs=20, verbose=2,
                    validation_data=(testX, testY), shuffle=False)

try:
    plot(model, to_file = 'lstm_ub.png', show_layer_names=True)
except ImportError:
    print('It seems like the dependencies for drawing the model (pydot, graphviz) are not installed') 
    
# evaluation of model efficiency
score, _ = model.evaluate(testX, testY, batch_size=6000)
rmse = math.sqrt(score)
print("\nMSE: {:.3f}, RMSE: {:.3f}".format(score, rmse))

# Visualization of the results
plt.style.use('seaborn-whitegrid')

predict = model.predict(testX, batch_size=6000, verbose=2)
a = predict[:200, (0)]
b = testY[:200, (0)]
c = predict[:200, (1)]
d = testY[:200, (1)]
# visualization of predicted data to validation ratio
plt.plot(a, label='predicted value')
plt.plot(b, label='validation (real) value')
plt.xlabel("X movement")
plt.ylabel("pixels")
plt.legend()
plt.savefig('x_predict.png')
plt.show()

plt.plot(c, label='predicted value')
plt.plot(d, label='validation (real) value')
plt.xlabel("Y-Movements")
plt.ylabel("pixels")
plt.legend()
plt.savefig('y_predict.png')
plt.show()

plt.scatter(a, c, s=10)
plt.scatter(b, d, s=10)
plt.xlabel("screen coordinates by X")
plt.ylabel("screen coordinates by Y")
plt.legend()
plt.savefig('prediction.png')
plt.show()
