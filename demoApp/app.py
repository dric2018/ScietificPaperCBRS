import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import io


from utils import get_recommendation_list, get_personalized_recommendations

pd.options.plotting.backend = "plotly"

from annotated_text import annotated_text

@st.cache(allow_output_mutation=True)
def load_data():
    # articles
    ARTICLES_URL = "https://drive.google.com/file/d/17pI0-_Zkmh68FrSvvc0dasznEbIj8YKu/view?usp=sharing"
    ARTICLES_FILE_ID=ARTICLES_URL.split('/')[-2]
    ARTICLES_DWN_LINK='https://drive.google.com/uc?id=' + ARTICLES_FILE_ID
    articles = pd.read_csv(ARTICLES_DWN_LINK)

    # similarity matrix
    SIMILARITY_MATRIX_URL = "https://drive.google.com/file/d/1rv9wri2O517dJ-H3zofI1_mabPZjMs4w/view?usp=sharing"
    SIMILARITY_MATRIX_FILE_ID=SIMILARITY_MATRIX_URL.split('/')[-2]
    SIMILARITY_MATRIX_DWN_LINK='https://drive.google.com/uc?id=' + SIMILARITY_MATRIX_FILE_ID    
    sim_matrix = np.load(SIMILARITY_MATRIX_DWN_LINK)
    
    # indices
    INDICES_URL = "https://drive.google.com/file/d/1hgbwX3BBZ9BNhKe_IaHhDqb91uOSvGlh/view?usp=sharing"
    INDICES_FILE_ID=INDICES_URL.split('/')[-2]
    INDICES_DWN_LINK='https://drive.google.com/uc?id=' + INDICES_FILE_ID
    indices = pd.read_csv(INDICES_DWN_LINK, header=None, index_col=0)


    # interactions
    INTERACTIONS_URL = "https://drive.google.com/file/d/1KpKWLM8S5lqPBaGpIg8LPMHVIo4wX4-r/view?usp=sharing"
    INTERACTIONS_FILE_ID=INTERACTIONS_URL.split('/')[-2]
    INTERACTIONS_DWN_LINK='https://drive.google.com/uc?id=' + INTERACTIONS_FILE_ID
    interactions = pd.read_csv(INTERACTIONS_DWN_LINK)


    return articles, sim_matrix, indices, interactions

def show_data_exploration(articles, interactions):

    st.markdown("### Data exploration")

    shape = articles.shape
    st.write("Preview of the dataset")
    st.write(f"Number of articles: {shape[0]}\n")
    st.write(f"Number of attributes: {shape[1]}\n")

    attr_options = st.multiselect(
        label='Select columns to view',
        options=articles.columns.to_list(),
        default = ["title", "category_name", "group_name", "categories"]
    )
    df = articles[attr_options]

    st.dataframe(df)

    count = articles.categories.value_counts()

    ## plotting
    k = 20

    fig = articles.categories.value_counts()[:k].sort_values().plot(kind = 'barh')
    fig.layout.bargap = 0
    fig.update_layout(
        title=f"Number of articles per category (Top {k})"
    )
    st.plotly_chart(fig)
    
    counts = articles.group_name.value_counts()


    fig = px.pie(
        counts, 
        values=counts.values, 
        names=counts.index, 
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    fig.update_layout(
        title="Paper distibution per group"
    )
    
    st.plotly_chart(fig)
    interactions_count = interactions.eventType.value_counts()

    fig = px.pie(
        interactions, 
        interactions_count.index,
        interactions_count.values, 
        title='Distribution of Interaction Type',
        color_discrete_sequence=px.colors.sequential.RdBu

    )
    
    st.plotly_chart(fig)



def main(articles, sim_matrix, indices, interactions, personalized):
    ### Main 

    st.markdown(
        """ ### CBRS for scientific articles
        """
    )
    search = st.text_input(label='What are you looking for?', value="Quantum computing")
    get_sim_btn = st.button("Get similar articles")
    if ((search or get_sim_btn) and search !="" or personalized):

        query_title, user_id = get_recommendations(
            search_key=search, 
            interactions=interactions, 
            personalized=personalized,
            articles=articles, 
            sim_matrix=sim_matrix, 
            indices=indices
        )

        if query_title is not None:
            st.sidebar.markdown("## [Persoalized recommendation]")
            # st.sidebar.markdown("### Results for search key: "+ "`" +query_title+"`")
        else:
            st.sidebar.markdown("## [Non-Persoalized recommendation]")
            st.sidebar.markdown("### Results for search key: "+ "`" +search+"`")

    elif (search or get_sim_btn) and search == "":
        st.warning("Empty search...please try again")


def get_recommendations(
    search_key:str, 
    interactions:pd.DataFrame, 
    articles, 
    indices, 
    sim_matrix, 
    personalized:bool=False
    ):

    query_title, u_id = None, None

    if personalized:
        random_id = interactions.personId.sample(n=1).values[0]
        recommendations, query_title, u_id = get_personalized_recommendations(
            user_id=random_id, 
            articles=articles, 
            interactions = interactions, 
            eventType="LIKE",
            similarity_matrix=sim_matrix,
            indices=indices
        )
        st.sidebar.markdown("### User ID :")
        st.sidebar.write(str(u_id))

        st.sidebar.markdown("### Query title:")
        st.sidebar.write(query_title)
    else:
        
        recommendations = get_recommendation_list(
            similarity_matrix=sim_matrix, 
            indices=indices, 
            title_or_keyword=search_key, 
            df=articles
        )

    # st.write(recommendations.shape)
    # with st.container():
        # container = st.expander(label="x", expanded=True)
        

    titles = recommendations.title.values.tolist()
    # st.write(titles)
    # [
    #     "This is some annotated text for those of you who like this sort of thing.", 
    #     "Title 2: Attention is all you need"
    # ]
    
    abstracts = recommendations.abstract.values.tolist()
    
    # [
    #     """
    #     is slechts een proeftekst uit het drukkerij- en zetterijwezen. 
    #     Lorem Ipsum is de standaard proeftekst in deze bedrijfstak sinds de 16e eeuw, 
    #     toen een onbekende drukker een zethaak met letters nam en ze door elkaar husselde 
    #     om een font-catalogus te maken. Het heeft niet alleen vijf eeuwen overleefd maar is ook, 
    #     vrijwel onveranderd, overgenomen in elektronische letterzetting. 
    #     Het is in de jaren '60 populair geworden met de introductie van Letraset vellen 
    #     met Lorem Ipsum passages en meer recentelijk door desktop publishing software 
    #     zoals Aldus PageMaker die versies van Lorem Ipsum bevatten.
    # """,
    # """
    #     There are many variations of passages of Lorem Ipsum available, but the majority have suffered 
    #     alteration in some form, by injected humour, or randomised words which don't look even slightly 
    #         believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't
    #     anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet 
    #     tend to repeat predefined chunks as necessary, making this the first true generator on the Internet. 
    #     It uses a dictionary of over 200 Latin words, combined with a handful of model sentence structures, 
    #     to generate Lorem Ipsum which looks reasonable. The generated Lorem Ipsum is therefore always free 
    #     from repetition, injected humour, or non-characteristic words etc.
    # """
    # ]
    all_tags = recommendations.categories.values.tolist()
    all_tags = [tags.split(",") for tags in all_tags]
    
    # [
    #     ['cs.AI', 'cs.CL', 'stat.GEO', 'het-ph'],
    #     ['cs.CL', 'math.GN']
    # ]

    all_links = ["#" for _ in range(recommendations.shape[0])]

    all_authors = recommendations.authors.values.tolist()

    # all_authors = [
    #     ["Bengio", "Lecun"],
    #     ["Bhiksha", "Busogi"]
    # ]

    scores = recommendations.score.values.tolist()

    for idx, (t, a, tags, link, authors, score) in enumerate(zip(titles, abstracts, all_tags, all_links, all_authors, scores)):
        container = st.expander(label="", expanded=True)
        with container:
            cols = st.columns([4, 1])

            cols[0].subheader(t)
            cols[0].write(a)
            cols[0].markdown(f"`{authors}`")
            # with cols[0]:
            #     for auth in authors:
            #         annotated_text(('', auth))

            with cols[1]:
                for tag in tags:
                    annotated_text(('', tag))
                
                st.markdown("### Action")
                view_btn = st.button("View 👀", key=f'13k0_{idx}')
                like_btn = st.button("Like 👍", key=f'13kk_{idx}')
                bookmark_btn = st.button("Bookmark ⬇️", key=f'13k_{idx}')
                comment = st.text_input("Leave a comment 📝",  key=f'2k_{idx}')


                st.info(f"{100*score:.3f}% Match")


    return query_title, u_id
              


        



if __name__ =="__main__":

    st.set_page_config(
        page_title="Scientific paper Recommender System",
        page_icon=":book",
    )
    articles, sim_matrix, indices, interactions = load_data()

    st.title(" 04-800 Introduction to Recommender Systems (RS)")

    ### Side bar
    options = [
        "Content based without user preferences",
        "Explore dataset"

    ]
    selected_page = st.sidebar.radio("Options", options)

    personalized = st.sidebar.checkbox(label="Personalized")

    if selected_page == "Explore dataset":
        show_data_exploration(articles, interactions)
    else:
        main(articles, sim_matrix, indices, interactions, personalized)
    st.sidebar.image("cmu_africa.jpg", use_column_width=True)
    st.sidebar.markdown("By Cedric Manouan @CMU-Africa, Fall 202")
