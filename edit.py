import pickle
# changed the movie names which are used as keys to lowercase in the recommendation model
# to avoid case sensitivity issues when loading the model
with open('rec_model', 'rb') as file:
    recommendations = pickle.load(file)

changed = {}

for i in recommendations:
    changed[i.lower()] = recommendations[i]

with open('rec_model', 'wb') as file:
    pickle.dump(changed, file)