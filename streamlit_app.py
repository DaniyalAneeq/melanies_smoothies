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
)

# Convert to pandas once
pd_df = my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    # Build ingredients string properly
    ingredients_string = " ".join(ingredients_list)
    
    for fruit_chosen in ingredients_list: 
        # Find the search term for this fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        st.write(f'The search value for {fruit_chosen} is {search_on}.')
        st.subheader(f'{fruit_chosen} Nutrition Information')
        
        # Make API call with the SEARCH_ON value
        smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        # Check if API call was successful before displaying
        if smoothiefroot_response.status_code == 200:
            st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        else:
            st.error(f"Could not fetch nutrition data for {fruit_chosen}")

    if st.button("Submit Order"):
        session.sql(
            """
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES (?, ?)
            """,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success(f"Your Smoothie, {name_on_order}, is ordered! ✅")
