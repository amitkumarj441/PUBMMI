# Referenced from https://github.com/subho406/Mouse-Dynamics-Analysis/blob/master/notebook/Feature%20Analysis%20and%20Visualization.ipynb

import pandas as pd
import numpy as np
import os 
import glob
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
%matplotlib inline

dataset = '/home/ith/Practice/predict-users-behavior/mouse_dataset/training_files/'
user_names=glob.glob(os.path.join(dataset,'*'))
files_dict={}
for u in user_names:
    files_dict[os.path.basename(u)]=glob.glob(os.path.join(u,'*'))
    
len(files_dict)
final_df=pd.DataFrame()
for u in user_names:
    files=files_dict[os.path.basename(u)]
    for f in files:
        csv=pd.read_csv(f)
        csv['user']=os.path.basename(u)
        csv['session']=os.path.basename(f)
        final_df=pd.concat([final_df,csv],ignore_index=True)
        
features=[]
user_names=pd.Series.unique(final_df['user'])
for u in user_names:
    feature=[]
    df=final_df[final_df['user']==u]
    feature.append(df['x'].mean())
    feature.append(df['y'].mean())
    feature.append(df['x'].std())
    feature.append(df['y'].std())
    features.append(feature)
features=np.stack(features)

for f in features:
    print(len(f))
    
scaler=StandardScaler()
features=scaler.fit_transform(features)
pca=PCA(n_components=2)
two_d=pca.fit_transform(features)
fig, ax = plt.subplots()

fig.set_size_inches(18.5, 10.5)
ax.scatter(two_d[:,0],two_d[:,1])
fig.savefig('scatuser.png')
for i, txt in enumerate(user_names):
    ax.annotate(txt, (two_d[i,0],two_d[i,1]))
    
# Clustering - Elbow method
k_val=range(1,10)
cluster_vals=range(1,11)
distortions=[]
for c in cluster_vals:
    kmeans=KMeans(n_clusters=c)
    cluster_index=kmeans.fit_predict(features)
    distortions.append(sum(np.min(cdist(features, kmeans.cluster_centers_, 'euclidean'), axis=1))/features.shape[0])
    
plt.xticks(cluster_vals)
plt.plot(cluster_vals,distortions,'bx-')
plt.xlabel('k')
plt.ylabel('Distortion')
plt.legend()
plt.savefig('elbow.png')
plt.show()

# Elbow at K=3
kmeans=KMeans(n_clusters=3)
cluster_index=kmeans.fit_predict(features)
fig, ax = plt.subplots()

fig.set_size_inches(18.5, 10.5)
ax.scatter(two_d[:,0],two_d[:,1],c=cluster_index,marker='o',s=200)
ax.set_title("Plot  showing individual users as a 2D scatter")
for i, txt in enumerate(user_names):
    ax.annotate(txt, (two_d[i,0],two_d[i,1]))
