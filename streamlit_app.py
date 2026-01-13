import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import requests

st.title("🥤Customize Your Smoothie!🥤")
st.write("Choose fruits you want in your custom Smoothie.")

name_on_order = st.text_input("Name on smoothie:")

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

# Convert to pandas
pd_df = my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list)
    
    for fruit_chosen in ingredients_list: 
        # Get the search term for API call
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        st.subheader(f'{fruit_chosen} Nutrition Information')
        
        # Make API call with correct search term
        api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Display nutrition info in a nice format
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Carbs", f"{data.get('nutrition', {}).get('carbs', 'N/A')}g")
            with col2:
                st.metric("Fat", f"{data.get('nutrition', {}).get('fat', 'N/A')}g")
            with col3:
                st.metric("Protein", f"{data.get('nutrition', {}).get('protein', 'N/A')}g")
            with col4:
                if 'sugar' in data.get('nutrition', {}):
                    st.metric("Sugar", f"{data['nutrition']['sugar']}g")
                else:
                    st.metric("Sugar", "N/A")
            
            # Show additional info
            st.write(f"**Family:** {data.get('family', 'N/A')}")
            st.write(f"**Genus:** {data.get('genus', 'N/A')}")
            st.write(f"**Order:** {data.get('order', 'N/A')}")
            
        else:
            st.error(f"Could not fetch nutrition data for {fruit_chosen}")
            st.write(f"API tried: {search_on}")
            st.write(f"Status code: {response.status_code}")

    if st.button("Submit Order"):
        session.sql(
            """
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES (?, ?)
            """,
            params=[ingredients_string, name_on_order]
        ).collect()
        st.success(f"Your Smoothie, {name_on_order}, is ordered! ✅")
