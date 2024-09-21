# SQL Query Generator & Executor with OpenAI and LangGraph

This Streamlit application uses OpenAI API, Langchain and LangGraph to automatically generate and execute SQL queries based on natural language inputs. 
Users can upload a SQLite database, ask questions in plain English, and the app will generate the corresponding SQL query and fetch results from the database.

## Features
- OpenAI-powered natural language to SQL conversion
- SQLite database upload and integration
- Interactive querying interface
- Automatic query generation and execution

## Requirements
Before running the application, make sure you have the following installed:

Python 3.9+
streamlit
langchain>=0.2
openai

Install the required packages using:
```
pip install requirements.txt
```

## How to Use
 Clone the repository:


```
git clone https://github.com/your-repo/sql-query-openai-langgraph.git
cd sql-query-openai-langgraph
```

Run the Streamlit application:
```
streamlit run streamlit_app.py
```

## Steps in the application:

- **Page 1**: API Key Input
    - Enter your OpenAI API key for authentication.
- **Page 2**: Upload Database
    - Upload your SQLite database (.db file).
- **Page 3**: Ask Questions
    - Type a natural language question, and the app will generate and execute the corresponding SQL query.

This README includes all the necessary instructions for running and using the app. Raise an issue if you face any!


