
# kaggle.com/orgesleka/imdbmovies

import pandas as pd
import math
df = pd.read_csv('datasets/imdb.csv', usecols=[
    "imdbRating",
    "ratingCount",
    "duration",
    "year",
    "nrOfWins",
    "nrOfNominations",
    "nrOfPhotos",
    "nrOfNewsArticles",
    "nrOfUserReviews",
    "nrOfGenre",
    "Action",
    "Adult",
    "Adventure",
    "Animation",
    "Biography",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "FilmNoir",
    "GameShow",
    "History",
    "Horror",
    "Music",
    "Musical",
    "Mystery",
    "News",
    "RealityTV",
    "Romance",
    "SciFi",
    "Short",
    "Sport",
    "TalkShow",
    "Thriller",
    "War",
    "Western",
])

data = []
for i in range(df.shape[0]):
    obj = df.iloc[i, :]
    tmp = []
    for v in obj.values:
        n = 0
        if isinstance(v, str) and v.isdigit():
            n = float(v)
        tmp.append(n)
    data.append(tmp)

print(df.shape)
print(data)
print(len(data))

