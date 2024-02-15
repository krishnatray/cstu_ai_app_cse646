# app.py
# CSTU Chat GPT App
# Sushil Sharma
#
import streamlit as st
import pandas as pd
import random
import time

from openai import OpenAI 
import textwrap3 as textwrap
import dotenv
from dotenv import load_dotenv
import os
from pinecone import Pinecone
import os
import csv
from fpdf import FPDF
import pandas as pd
import base64

# For sending email
import json
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

st.title("Welcome to StudentGPT 💬")
#st.sidebar.image("robo.gif")


#dotenv_path = '.env'  # Specify the path to the .env file
env = load_dotenv() # Copy .env file to the same directory before running

if env: 
    # st.error("Enviroment file error. Please check .env file in your directory.")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OpenAI.api_key = OPENAI_API_KEY
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
else:
    OPENAI_API_KEY = st.sidebar.text_input("Enter OpenAI key", type="password")
    OpenAI.api_key = OPENAI_API_KEY
    try:
        # OPENAI_API_KEY = st.secrets.OPENAI_API_KEY
        PINECONE_API_KEY = st.secrets.PINECONE_API_KEY
        SENDGRID_API_KEY = st.secrets.SENDGRID_API_KEY
    except Exception as e:
        st.error("Enviroment file error!")
        st.error(e)


embed_model = "text-embedding-3-small"
index_name = 'myindex'

pc = Pinecone(
    api_key=os.environ.get("PINECONE_API_KEY"),
    environment="asia-southeast1-gcp-free" 
)

index = pc.Index(index_name) # connect to pinecone index

client = OpenAI()

if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []    

# Initialize chat history
delimiter = ""
if "prompt_history" not in st.session_state: # Initialize the chat history with the system message if it doesn't exist
        st.session_state.prompt_history = [
            {'role': 'system', 'content': f"""\
You are a chat agent providing concise answers to questions about California Science and Technology University (CSTU) based on contents provided at system role.\
At begining, welcome users to CSTU. If users require information related to CSTU out of provided context, ask them to check the website www.cstu.edu.\
If users ask for course registration, ask for user's name. Then provide them a list of available courses for registration.\
If they select courses, you summarize them and check if they wish to enroll in any additional course or confirm with selected courses.\        
If it's all, ask for their email address. If they provide email address, complete the registration.\
If user ask to reconfirm or see the course registration record(s), ask for user's email address. If they provide email address, call function 
        get_registration with email address and display the results.
If user ask to enquire or see his her course grades, ask for user's email address. If they provide email address, call function 
        get_grades with email address and display the results.
If user ask to download his/her transcript, ask for user's email address. If they provide email address, call function 
        download_transcript with email address and display the results.

                                      """} ]



def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


# During the coversation, refer to chat history and the information delimited by {delimiter}.
def chat_complete_messages(messages, temperature=0):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
        functions = [
         {
            "name": "registration",
            "description": "complete the registration",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_name": {"type":"string","description":"The name of the user",},
                    "student_email": {"type": "string", "description": "The email of user",},
                    "courses":{"type":"string", "description":"The courses the user want to register",},
                    "body": {"type": "string", "description": "Confirmation content of CSTU about courses registered by user",},
                },
                "required": ["student_name", "student_email", "courses","body"],
            }
         },
        {
            "name": "get_registration",
            "description": "To reconfirm registration, get the student's registration details",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_email": {"type": "string", "description": "The email of the student user",}
                },
                "required": ["student_email"],
            }
         },
        {
            "name": "get_grades",
            "description": "To get the student's grades",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_email": {"type": "string", "description": "The email of the student user",}
                },
                "required": ["student_email"],
            }
         },

        {
            "name": "download_transcript",
            "description": "To download the transcript",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_email": {"type": "string", "description": "The email of the student user",}
                },
                "required": ["student_email"],
            }
         },


        ],
       function_call="auto",
    )
    return (response.choices[0].message.content, response.choices[0].message.tool_calls)


def limit_line_width(text, max_line_width):
    """ Function to limit the line width of the text """
    if text is None: return ""
    lines = textwrap.wrap(text, width=max_line_width)
    return "\n".join(lines)

def get_registration(student_email):
    try:
        df = pd.read_csv("registration_records.csv")
        result = df[df["EMAIL ADDRESS"] == student_email].to_dict()
        del df
    except Exception as e:
        result = f"Registration records not found for {student_email}!"

    return result

def get_grades(student_email):
    try:
        df = pd.read_csv("grades.csv")
        result = df[df["student_email"] == student_email].to_dict()
        if result:
            st.snow()
        del df
    except Exception as e:
        result = f"Grades records not found for {student_email}"

    return result

def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

def download_transcript(student_email):
    try:
        df = pd.read_csv("grades.csv")
        title = "California Science and Technology University http://www.cstu.edu"
        heading = "Fake Transcript generated by CSTU Chat GPT "
        text_top = """ 
            
                
                
        """
        txt_mid = df[df['student_email']==student_email].to_string()

        txt_footer="""


                Signed by
                CSTUGPT Bot :)
            """
        text = text_top + txt_mid + txt_footer
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 15)
        pdf.cell(w=210, h=9, txt=title, border=0, ln=1, align='C', fill=0)
        pdf.set_font('Times', 'B', 15)
        pdf.cell(w=0, h=6, txt=heading, border=0, ln=1, align='C', fill=0)
        pdf.set_font('Times', 'B', 15)
        pdf.cell(w=0, h=6, txt="_"*60, border=0, ln=1, align='C', fill=0)
        pdf.set_font('Times', '', 12)
        pdf.multi_cell(w=0, h=5, txt=text)
        
        
        # response.headers['Content-Type'] = 'application/pdf'
        output_file = pdf.output(dest="S").encode("latin-1")
        html = create_download_link(output_file, "transcript")
        st.markdown(html, unsafe_allow_html=True)
        result = "Success!"
        del df
    except Exception as e:
        result = e

    return result

# Define a function sending confirmation email for registration
def registration(student_name,student_email,courses,body):
    try:
        csv_file = "registration_records.csv"
        #print(student_email,body,name, courses)
        data = [time.strftime("%Y-%m-%d %H:%M:%S"), student_name, student_email, courses]
        if not os.path.exists(csv_file):
            with open(csv_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["REGISTRATION TIME","STUDENT NAME", "EMAIL ADDRESS", "COURSE NAME"])
        with open(csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(data)
        message = Mail(
            from_email='cstu02@gmail.com',
            to_emails=student_email,
            subject='Course registration confirmation from CSTU',
            html_content=body)
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        #print(response.status_code)
        #print(response.body)
        #print(response.headers)
    except Exception as e:
            print(e.message)
            st.info("A registration confirmation message has been sent to your email.")

# Display chat messages from history on app rerun
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# Accept user input
if user_input := st.chat_input("Welcome to CSTU StudentChatGPT! 🤖"):
    if OPENAI_API_KEY:
        # res = client.embeddings.create(
        #     input=[user_input],
        #     model=embed_model
        #     )
        
        res = get_embedding("".join([user_input]))

        kb_res = index.query(vector = res, top_k=1, include_metadata=True, namespace='cstu')

        #If the include_metadata parameter is set to True, the query method will only return the id, score, and metadata for each document. The vector for each document will not be returned
        metadata_text_list = [x['metadata']['text'] for x in kb_res['matches']]
        limit = 3600  #set the limit of knowledge base words
        kb_content = " "
        count = 0
        proceed = True
        while proceed and count < len(metadata_text_list):  # append until hitting limit
            if len(kb_content) + len(metadata_text_list[count]) >= limit:
                proceed = False
            else:
                    kb_content += metadata_text_list[count]
            count += 1
        knowledge_message = {"role": "system", "content": f"""
                            {delimiter}{kb_content}{delimiter}
                            """}
    
        # Add user message to chat history
        user_message = {"role": "user", "content": user_input}
        st.session_state.chat_history.append(user_message)
        
        # Add knowledge base and user message to promt history      
        st.session_state.prompt_history.append(knowledge_message)        
        st.session_state.prompt_history.append(user_message)

        # Get the model response
        response, tool_calls = chat_complete_messages(st.session_state.prompt_history, temperature=0)
        #response = chat_complete_messages(C, temperature=0)
        # Limit the line width to, for example, 60 characters
        max_line_width = 60
        #x = response
        # st.write(response)
        # st.write(type(response))
        if tool_calls: # e.g. Sending email
            
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            # st.write(function_name)
            # print("function_name: ",function_name)
            
            # function_to_call = available_functions[function_name]
            # print("function_to_call: ", function_to_call)

            function_args = json.loads(tool_call.function.arguments)
            if function_name == 'registration':
                registration(function_args.get("student_name"), function_args.get("student_email"), function_args.get("courses"), function_args.get("body"))
                formatted_text = "Thank you for providing your email address. A confirmation message for your registration has been sent to your email. Please check it and let me known if there is any further requirement."
                #st.info("The following message has been sent to "+function_args.get("student_email")+":\n"+function_args.get("body"))
            elif function_name == 'get_registration':
                # print(function_args.get("student_email"))
                result = get_registration(function_args.get("student_email")) 
                formatted_text = f"{result}"
            elif function_name == 'get_grades':
                result = get_grades(function_args.get("student_email")) 
                formatted_text = f"{result}"
            elif function_name == 'download_transcript':
                result = download_transcript(function_args.get("student_email")) 
                formatted_text = f"{result}"
            else:
                print("function_name: ",function_name)
                
        
        else:
            # formatted_text = limit_line_width(response["content"], max_line_width)
            # print(response)
            formatted_text = response

        ai_message = {"role": "assistant", "content": formatted_text}
        st.session_state.chat_history.append(ai_message)
        st.session_state.prompt_history.append(ai_message)

        # Display message in chat message container
        with st.chat_message("user"):
            st.write(user_message['content'])
        with st.chat_message("assistant"):
            try:
                st.write(pd.DataFrame(result))
            except Exception as e: 
                st.write(ai_message['content'])

    else:
        st.write("!!! Error: You need to enter OPENAI_API_KEY!")
    
