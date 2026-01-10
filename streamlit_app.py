import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

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

my_dataframe = (
    session
    .table("smoothies.public.fruit_options")
    .select(col("FRUIT_NAME"))
    .to_pandas()
)

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    my_dataframe["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)

    if st.button("Submit Order"):
        session.sql("""
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES (%s, %s)
        """, params=[ingredients_string, name_on_order]).collect()

        st.success(f"Your Smoothie, {name_on_order}, is ordered! ✅")
