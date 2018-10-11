import os
import numpy as np
import pandas as pd
from IPython.display import display, HTML

import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
%matplotlib inline

DATA_DIR = os.getcwd() + '/data/test_files/'
users_sessions = os.listdir(DATA_DIR)
all_sessions = {i: os.listdir(DATA_DIR + i) for i in users_sessions}
print('Number of Users: %s' % len(all_sessions.keys()))
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
display(data[:50])

# search pattern
# separation of mouse position values with active clicks
press = data[['state']].values == 'Pressed'
press = data[press]
XY = press[['x', 'y']]

# the formation of a dictionary of unique provisions
XY_dict = [i[0] + ';' + i[1] for i in XY.values]
print('Total number of positions, ', len(XY_dict)) 
print('Number of unique positions, ', len(set(XY_dict)))

XY_set = pd.DataFrame(XY_dict, columns=['xy'])
XY_count = XY_set.xy.value_counts()
means = XY_count.mean()
XY_count = XY_count[XY_count > 2]
len(XY_count)
XY_count_dict = {x: y for x, y in zip(list(XY_count.index), list(XY_count.values))}
x = [int(i.split(';')[0]) for i in XY_count_dict.keys()]
y = [int(i.split(';')[1]) for i in XY_count_dict.keys()]

plt.scatter(x, y, s=10)
plt.xlabel("screen coordinate x")
plt.ylabel("screen coordinate y")
plt.legend()
plt.savefig('pattern_1.png')
plt.show()
plt.close()

# K-means clustering
from sklearn.cluster import KMeans

X = np.hstack((np.array(x).reshape(len(x), 1), np.array(y).reshape(len(y), 1)))
# methods of K-means
kmeans = KMeans(n_clusters=11)
#Training models
kmeans.fit(X)
# labeling
y_kmeans = kmeans.predict(X)
plt.scatter(X[:, 0], X[:, 1], c=y_kmeans, s=50, cmap='viridis')
centers = kmeans.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1], c='black', s=200, alpha=0.5)
plt.xlabel("Screen Orientation x")
plt.ylabel("Screen Orientation y")
plt.legend()
plt.savefig('pattern_2.png')
plt.show()

y_kmeans_all = kmeans.predict(XY.values)
markers = pd.DataFrame(y_kmeans_all, columns=['label'])
m = markers.label.value_counts()
plt.hist(markers.label.values)
plt.xlabel("found clusters")
plt.ylabel("clicks")
plt.legend()
plt.savefig('interactive.png')
plt.show()
