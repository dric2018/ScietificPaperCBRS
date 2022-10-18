import pandas as pd
import spacy
from spacy import displacy
nlp = spacy.load('en_core_web_sm')
from spacy.lang.en.stop_words import STOP_WORDS
import en_core_web_sm
import string

def get_category_name(df=pd.DataFrame, category_id:list="cs.AI"):
    names = []

    for cat_id in category_id:
        names.append(df[df["category_id"] == cat_id].category_name.values.tolist())
        if len(names) == 1:
            try:
                return names[0][0]
            except IndexError:
                return names[0]
        else:
            return ",".join(names)

def get_group_name(df=pd.DataFrame, category_id:list=["cs.AI"]):

    names = []
    for cat_id in category_id:
        names.append(df[df["category_id"] == cat_id].group_name.values.tolist())
        if len(names) == 1:
            try:
                return names[0][0]
            except IndexError:
                return names[0]
        else:
            return ",".join(names)

def get_category_description(df=pd.DataFrame, category_id:list=["cs.AI"]):
    descriptions = []
    for cat_id in category_id:
        descriptions.append(df[df["category_id"] == cat_id].category_description.values.tolist())
        if len(descriptions) == 1:
            try:
                return descriptions[0][0]
            except IndexError:
                return descriptions[0]
        else:
            return ",".join(descriptions)
        
### Recommendation utils
def get_paper_by_keywords(keywords:str, articles):
    kw_doc = nlp(keywords)
    words = " ".join([word.text.lower() for word in kw_doc if word.text not in list(STOP_WORDS)])

    matches = []

    for t_idx in range(articles.shape[0]):
        kw_list = words.strip().split()
        for k in kw_list:
            if k in articles.title[t_idx].lower().split():
                matches.append(articles.title[t_idx])

    return matches

        
def get_paper_by_title(title:list, indices:pd.DataFrame):
    title = [t.lower() for t in title]
    result = []
    for t in title:
        try:
            result.append(indices.loc[t][0])
        except: 
            result.append(indices.loc[t][1])
    
    return result


def get_recommendation_list(similarity_matrix, indices, title_or_keyword:str, df:pd.DataFrame, k:int=10):
    i = -1
    title = title_or_keyword
    exact_match = False
    try:
        # search using title
        i = get_paper_by_title(title=[title], indices=indices)[0]
        exact_match = True

    except:
        title = get_paper_by_keywords(keywords=title_or_keyword, articles=df)
        if title == []:
            title="random"
            t = indices.sample(n=1).index[0]
            i  = get_paper_by_title(title=[t], indices=indices)[0]
            exact_match = True
        else:
            i = get_paper_by_title(title=title, indices=indices)[0]
        
    print(title, i, exact_match)
        

    scores = enumerate(similarity_matrix[i])
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    if exact_match:
        scores = scores[1:k]
    else:
        scores = scores[:k]

    
    similar_papers_indices = [sim[0] for sim in scores]
    
    
    return df.iloc[similar_papers_indices]

def get_article_title_by_id(article_id:str, articles:pd.DataFrame):
    return articles[articles["id"]==article_id].title.values[0]

def get_personalized_recommendations(user_id:int, interactions_df:pd.DataFrame, articles:pd.DataFrame, eventType:str="LIKE"):
    
    event_map = {
        "VIEW": 4,
        "LIKE": 3,
        "BOOKMARK": 0,
        "FOLLOW": 2,
        "COMMENT CREATED": 1,
    }
    
    event_id = event_map[eventType]
    # get user interactions
    user_interactions = interactions[(interactions["personId"] == user_id) & (interactions["eventType"]==event_id)]
    if user_interactions.shape[0] == 0:
        # look for viewed articles 
        user_interactions = interactions[(interactions["personId"] == user_id) & (interactions["eventType"]==4)]

    # pick a random article from those articles the current user have liked
    a_id = user_interactions.contentId.sample(n=1).values[0]
    # get artilcle title by id
    a_t = get_article_title_by_id(article_id=a_id, articles=articles)
        
    return get_recommendation_list(title_or_keyword=a_t), a_t
    