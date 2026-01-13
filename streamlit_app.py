import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import requests

st.title("🥤Customize Your Smoothie!🥤")
st.write("Choose fruits you want in your custom Smoothie.")

name_on_order = st.text_input("Name on smoothie:")
st.write("The name on your smoothie will be:", name_on_order)

@st.cache_resource
def create_session():
    return Session.builder.configs({
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "role": st.secrets["snowflake"]["role"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"],
    }).create()

session = create_session()

# Get both FRUIT_NAME for display and SEARCH_ON for API calls
my_dataframe = (
    session
    .table("smoothies.public.fruit_options")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
    .to_pandas()
)

# Create a dictionary mapping display names to search terms
fruit_mapping = dict(zip(my_dataframe["FRUIT_NAME"], my_dataframe["SEARCH_ON"]))

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    my_dataframe["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)
    for fruit_chosen in ingredients_list: 
        ingredients_string += fruit_chosen + ' '
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        # Use the SEARCH_ON value for API call instead of FRUIT_NAME
        search_term = fruit_mapping.get(fruit_chosen, fruit_chosen)
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_term)
        
        # Check if API call was successful
        if smoothiefroot_response.status_code == 200:
            st_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        else:
            st.error(f"Could not fetch nutrition data for {fruit_chosen} (API returned {smoothiefroot_response.status_code})")

    if st.button("Submit Order"):
        session.sql(
            """
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES (?, ?)
            """,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success(f"Your Smoothie, {name_on_order}, is ordered! ✅")
