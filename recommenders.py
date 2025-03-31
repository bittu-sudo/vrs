import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Reader, Dataset, SVD

# class hybridRecommender:
#     def __init__(self) -> None:
#         pass

#     def load_dataset(self):
#         self.df = pd.read_csv('./movies_metadata.csv', low_memory=False)

#     def calculate_cosine_sim(self):
#         self.tfidf = TfidfVectorizer(stop_words='english')

#         self.df['overview'] = self.df['overview'].fillna('')

#         self.tfidf_matrix = self.tfidf.fit_transform(self.df['overview'])

#         self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)



#     def content_based_recommender(self, title, cosine_sim = None):

#         if cosine_sim == None:

#             cosine_sim = self.cosine_sim

#         indices = pd.Series(self.df.index, index=self.df['title'])

#         indices = indices[~indices.index.duplicated(keep='last')]

#         movie_index = indices[title]

#         similarity_scores = pd.self.df(cosine_sim[movie_index], columns=["score"])

#         movie_indices = similarity_scores.sort_values("score", ascending=False)[1:11].index

#         return self.df['title'].iloc[movie_indices]

    

#     def recommend(self):

#         recommendations = np.empty(self.df.shape[0]*11, dtype = np.object).reshape(self.df.shape[0], 11)

#         j = 0

#         for i in self.df['title']:

#             recommendations[j][0] = i

#             recommendations[j][1:] = self.content_based_recommender(i).to_numpy()

#             j = j + 1

#         return recommendations

    

class tfidRecommender:   #we use this recommender 

    def __init__(self) -> None:          #initialize the recommender

        pass



    def load_dataset(self):              #load the data set into self class df data member is a data frame

        self.df = pd.read_csv('./movies_metadata.csv', low_memory=False)

        

    def calculate_cosine_sim(self):            #calculate the cosine similarity between the movies depending on overview of two movies

        self.tfidf = TfidfVectorizer(stop_words='english')

        print("Checkpoint 1: TfidVecorizer completion")

        self.df['overview'] = self.df['overview'].fillna('')

        self.tfidf_matrix = self.tfidf.fit_transform(self.df['overview'])

        print("Checkpoint 2: Fitting and Transform completion")

        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

        print("Checkpoint 3: Similarity completion")

        print(self.cosine_sim)



    def content_based_recommender(self, title, cosine_sim = None):   #

        if cosine_sim == None:

            cosine_sim = self.cosine_sim

        similarity_scores = pd.DataFrame(cosine_sim[self.df[self.df['title'] == title].iloc[0, 0]], columns=["score"])

        movie_indices = similarity_scores.sort_values("score", ascending=False)[1:11].index

        return self.df['title'].iloc[movie_indices]

    

    def recommend(self):

        recommendations = np.zeros(self.df.shape[0]*11, dtype = object).reshape(self.df.shape[0], 11)

        j = 0

        for i in self.df['title']:

            # print(j)

            recommendations[j][0] = i

            recommendations[j][1:] = (self.content_based_recommender(i)).to_numpy()

            j = j + 1

        return recommendations



if __name__ == '__main__':

    print("This is a Recommender model")



    model_rec = tfidRecommender() 



    def train_model(model_name):

        model_name.load_dataset()

        model_name.calculate_cosine_sim()

        return model_name.recommend()

    

    model_v1 = train_model(model_rec)

    mod={}

    for i in model_v1:

        mod[i[0].lower()]=i[1:].tolist()



    import pickle

    with open("rec_model", "wb") as file:

        pickle.dump(mod, file)

    del model_rec

    del model_v1