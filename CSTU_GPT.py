#
# app.py
# Author : Sushil K Sharma
#

import streamlit as st

st.set_page_config(
    page_title="CSTU GPT",
    page_icon="💬",
)

st.title("Welcome to CSTU GPT 💬")

st.sidebar.success("Select a site above.")

credits_text = """
## CSE 646, Spring 2024 - AI/GenAI Application

- Project: CSTUGPT [Github](https://github.com/krishnatray/cstu_ai_app_cse646.git)

---------------------
## Project Team:
- Sushil K Sharma [Linkedin](https://linkedin.com/in/krishnatray)
---------------------
## Professor:
#### Laiq Ahmad (laiqahmad@gmail.com)

California Science and Technology University
https://www.cstu.edu/
              
"""
st.markdown(credits_text) 