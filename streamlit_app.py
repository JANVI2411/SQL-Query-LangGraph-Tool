import streamlit as st
import openai
import sqlite3
import os

cwd = os.path.dirname(os.path.abspath(__file__))

if 'page' not in st.session_state:
    st.session_state.page = 1  # Start at page 1
# State management across pages
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False

if 'db_file_uploaded' not in st.session_state:
    st.session_state.db_file_uploaded = False

def validate_openai_key(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        try:
            client.models.list()
        except openai.AuthenticationError:
            return False
        os.environ['OPENAI_API_KEY'] = api_key
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def get_openai_response(api_key, user_input):
    try: 
        os.environ['OPENAI_API_KEY'] = api_key
        from scripts.sql_rag_langgraph import app

        messages = app.invoke(
            {"messages": [("user", user_input)]}
        )
        json_str = messages["messages"][-1].tool_calls[0]["args"]["final_answer"]
        return json_str
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Streamlit multi-page flow
def main():
    st.title("SQL Query App")
    
    # Navigation buttons
    page_options = ["1. API Key Input", "2. Upload Database", "3. Ask Question"]
    page_selection = st.sidebar.radio("Go to", page_options)

    if page_selection == "1. API Key Input":
        st.session_state.page = 1
    elif page_selection == "2. Upload Database":
        st.session_state.page = 2
    elif page_selection == "3. Ask Question":
        st.session_state.page = 3

    # Page 1: API Key Input
    if st.session_state.page == 1:
        st.header("Step 1: Enter OpenAI API Key")
        api_key = st.text_input("Enter your OpenAI API key:", type="password")
        if st.button("Validate API Key"):
            if validate_openai_key(api_key):
                st.success("API key is valid!")
                st.session_state.api_key = api_key
                st.session_state.api_key_valid = True
            else:
                st.error("Invalid API key. Please try again.")

    # Page 2: Database File Upload
    if st.session_state.page == 2 and st.session_state.api_key_valid:
        st.header("Step 2: Upload SQLite Database File")
        uploaded_file = st.file_uploader("Choose a SQLite database file", type=["db"])
        
        if uploaded_file is not None:
            with open(f"/tmp/temp_{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            db_file_name = f"/tmp/temp_{uploaded_file.name}"
            try:
                conn = sqlite3.connect(db_file_name)
                st.session_state.db_conn = conn
                st.success(f"Database file '{uploaded_file.name}' uploaded successfully!")
                st.session_state.db_file_uploaded = True
                
                from scripts.sql_rag_langgraph import update_db
                db_file_path = os.path.join(cwd,db_file_name)
                st.session_state.db_file_path = db_file_path
                update_db(db_file_path)
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Page 3: Ask Questions
    if st.session_state.page == 3 and st.session_state.api_key_valid and st.session_state.db_file_uploaded:
        st.header("Step 3: Ask a Question")
        user_query = st.text_input("Enter your question:")
        
        if st.button("Generate SQL and Get Answer"):
            if user_query:
                # Generate SQL query using OpenAI
                # Execute the SQL query against the uploaded database
                result = get_openai_response(st.session_state.api_key, user_query)
                
                if result:
                    st.write("Query Results:")
                    st.write(result)
            else:
                st.error("Please enter a query.")

if __name__ == "__main__":
    main()

# import streamlit as st
# import openai
# import os 
# # Function to validate OpenAI API key by sending a simple test query
# def validate_openai_key(api_key):
#     try:
#         # Set the OpenAI API key
#         client = openai.OpenAI(api_key=api_key)
#         try:
#             client.models.list()
#         except openai.AuthenticationError:
#             return False
#         os.environ['OPENAI_API_KEY'] = api_key
#         return True
#     except Exception as e:
#         st.error(f"Error: {e}")
#         return False

# # Function to generate a response from OpenAI model based on user input
# def get_openai_response(api_key, user_input):
#     try: 
#         os.environ['OPENAI_API_KEY'] = api_key
#         from scripts.sql_rag_langgraph import app

#         messages = app.invoke(
#             {"messages": [("user", user_input)]}
#         )
#         json_str = messages["messages"][-1].tool_calls[0]["args"]["final_answer"]
#         return json_str
#     except Exception as e:
#         st.error(f"Error: {e}")
#         return None

# # Streamlit App
# def main():
#     st.title("OpenAI Query App")

#     # Step 1: Request OpenAI API Key from the user
#     api_key = st.text_input("Enter your OpenAI API key:", type="password")
    
#     # Validate API Key Button
#     if st.button("Validate API Key"):
#         if validate_openai_key(api_key):
#             st.success("API key is valid. You can now ask your query!")
#             st.session_state.api_key_valid = True
#         else:
#             st.error("Invalid API key. Please try again.")

#     # Proceed only if the API key is valid
#     if "api_key_valid" in st.session_state and st.session_state.api_key_valid:
#         # Step 2: Ask for user input (natural language query)
#         user_input = st.text_input("Enter your query:")
        
#         # Submit query button
#         if st.button("Submit Query"):
#             if user_input:
#                 # Step 3: Get response from OpenAI and display
#                 with st.spinner("Fetching response..."):
#                     response = get_openai_response(api_key, user_input)
#                     if response:
#                         st.write("### Response:")
#                         st.write(response)
#             else:
#                 st.error("Please enter a query to submit.")

# # Run the Streamlit app
# if __name__ == "__main__":
#     main()
