import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Reader, Dataset, SVD

class tfidRecommender:
    def __init__(self) -> None:
        pass
        
    def load_dataset(self):
        self.df = pd.read_csv('./movies_metadata.csv', low_memory=False)
        
    def calculate_cosine_sim(self):
        self.tfidf = TfidfVectorizer(stop_words='english')
        print("Checkpoint 1: TfidVecorizer completion")
        self.df['overview'] = self.df['overview'].fillna('')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['overview'])
        print("Checkpoint 2: Fitting and Transform completion")
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        print("Checkpoint 3: Similarity completion")
        print(self.cosine_sim)
        
    def content_based_recommender(self, title, cosine_sim = None):
        if cosine_sim is None:
            cosine_sim = self.cosine_sim
            
        # Create an index mapping for movie titles
        indices = pd.Series(self.df.index, index=self.df['title'])
        # Handle duplicate titles by keeping the last occurrence
        indices = indices[~indices.index.duplicated(keep='last')]
        
        # Check if the title exists in our dataset
        if title not in indices:
            # Return empty series if title not found
            return pd.Series([], dtype='object')
            
        # Get the index of the movie
        idx = indices[title]
        
        # Get similarity scores for the movie
        similarity_scores = pd.DataFrame(cosine_sim[idx], columns=["score"])
        
        # Get indices of top 10 similar movies (excluding itself)
        movie_indices = similarity_scores.sort_values("score", ascending=False)[1:11].index
        
        return self.df['title'].iloc[movie_indices]
        
    def recommend(self):
        recommendations = np.zeros(self.df.shape[0]*11, dtype=object).reshape(self.df.shape[0], 11)
        j = 0
        
        # Get unique titles to avoid duplicates
        unique_titles = self.df['title'].unique()
        
        for i in unique_titles:
            try:
                recs = self.content_based_recommender(i)
                if not recs.empty:
                    recommendations[j][0] = i
                    recommendations[j][1:] = recs.to_numpy()
                    j += 1
            except Exception as e:
                print(f"Error processing title '{i}': {e}")
                # Continue with next title
                continue
                
        # Trim the array to only include populated rows
        recommendations = recommendations[:j]
        return recommendations

if __name__ == '__main__':
    print("This is a Recommender model")
    model_rec = tfidRecommender()
    
    def train_model(model_name):
        model_name.load_dataset()
        model_name.calculate_cosine_sim()
        return model_name.recommend()
    
    model_v1 = train_model(model_rec)
    
    mod = {}
    for i in model_v1:
        mod[i[0].lower()] = i[1:].tolist()
    
    import pickle
    with open("rec_model", "wb") as file:
        pickle.dump(mod, file)
    
    del model_rec
    del model_v1