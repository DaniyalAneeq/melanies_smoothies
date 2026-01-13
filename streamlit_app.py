import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import requests
import pandas as pd

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
            
            # Create nutrition dataframe
            nutrition_data = data.get('nutrition', {})
            
            if nutrition_data:
                # Create a proper nutrition dataframe
                nutrition_df = pd.DataFrame({
                    'Nutrient': ['Carbs', 'Fat', 'Protein', 'Sugar'],
                    'Amount (g)': [
                        nutrition_data.get('carbs', 'N/A'),
                        nutrition_data.get('fat', 'N/A'),
                        nutrition_data.get('protein', 'N/A'),
                        nutrition_data.get('sugar', 'N/A')
                    ]
                })
                
                # Format the Amount column - remove 'g' if it's already a number
                def format_amount(x):
                    if isinstance(x, (int, float)):
                        return f"{x}g"
                    return str(x)
                
                nutrition_df['Amount (g)'] = nutrition_df['Amount (g)'].apply(format_amount)
                
                # Display the dataframe
                st.dataframe(nutrition_df, use_container_width=True, hide_index=True)
            else:
                st.write("No nutrition data available for this fruit.")
                
                # Create empty nutrition dataframe
                nutrition_df = pd.DataFrame({
                    'Nutrient': ['Carbs', 'Fat', 'Protein', 'Sugar'],
                    'Amount (g)': ['N/A', 'N/A', 'N/A', 'N/A']
                })
                st.dataframe(nutrition_df, use_container_width=True, hide_index=True)
            
            # Create info dataframe
            info_data = {
                'Category': ['Family', 'Genus', 'Order'],
                'Value': [
                    data.get('family', 'N/A'),
                    data.get('genus', 'N/A'),
                    data.get('order', 'N/A')
                ]
            }
            info_df = pd.DataFrame(info_data)
            st.dataframe(info_df, use_container_width=True, hide_index=True)
            
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
