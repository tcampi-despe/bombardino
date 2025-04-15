## Funciones para leer la base GPT
import os
import pandas as pd
import json
import re
from openai import OpenAI
import openai
from dotenv import load_dotenv
import os
from prompts import system_read_db
from tools import describe_tools
import pandas as pd
load_dotenv()

api_key = os.getenv('OpenAI_GPT')
client = OpenAI(api_key=api_key)

def read_columns(df):
    """
    Reads the columns of the DataFrame and returns a list of column names.
    """
    return ', '.join(df.columns.tolist())

def read_column_values(df, column):
    """
    Reads the values of a specific column in the DataFrame and returns them as a list.
    If the column appears to be an ID column or has more than 20 unique values, it limits the output to a sample of unique values.
    """
    unique_values = df[column].unique().tolist()
    if len(unique_values) > 20:
        # Limit the output to the first 20 unique values
        return '\n'.join(map(str, unique_values[:20])) + ('\n...' if len(unique_values) > 20 else '')
    return '\n'.join(map(str, unique_values))

def ask_info(question):
    return input(f"{question}")


def check_nulls(df):
    return df.isnull().sum()/len(df)*100

def drop_nulls(df, column):
    df.dropna(subset=[column], inplace=True)
    return 'Nulls from column {} have been dropped'.format(column)

def fill_nulls(df, column, value):
    df[column].fillna(value, inplace=True)
    return 'Nulls from column {} have been filled with {}'.format(column, value)

def retrieve_dataframe(df, petition):
    """Describes the dataframe based on user's intent for clustering."""
    messages = [
        {"role": "system", "content": system_read_db},
        {"role": "user", "content": petition}
    ]
    return describe_dataframe(df, messages, describe_tools)

def describe_dataframe(df, messages, tools):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=messages,
            max_tokens=5000,
            tools=tools,
            tool_choice='auto',
            temperature=0
        )
        if response.choices[0].message.content == None:
            if len(response.choices[0].message.tool_calls)>0:
                tool_name = response.choices[0].message.tool_calls[0].function.name
                print("Tool Calling: ", tool_name)
                if tool_name == "read_columns":
                    columns = read_columns(df)
                    print(columns)
                    messages.append({"role": "assistant", "content": None, "function_call": {"name": tool_name, "arguments": response.choices[0].message.tool_calls[0].function.arguments}})
                    messages.append({"role": "function", "name": tool_name, "content": columns})
                    return describe_dataframe(df, messages, tools)
                elif tool_name == "read_column_values":
                    column = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["column"]
                    values = read_column_values(df,column)
                    print("Reading column: ", column)
                    messages.append({"role": "assistant", "content": None, "function_call": {"name": tool_name, "arguments": response.choices[0].message.tool_calls[0].function.arguments}})
                    messages.append({"role": "function", "name": tool_name, "content": values})
                    return describe_dataframe(df, messages, tools)
                elif tool_name == "ask_info":
                    question = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["question"]
                    answer = ask_info(question)
                    messages.append({"role": "assistant", "content": None, "function_call": {"name": tool_name, "arguments": response.choices[0].message.tool_calls[0].function.arguments}})
                    messages.append({"role": "function", "name": tool_name, "content": answer})
                    return describe_dataframe(df, messages, tools)
        else:
            return response.choices[0].message.content
        
    except openai.BadRequestError as e:
        
        print(e.message)
        #print(response.messages[3].content[0])
        return {"data":"Error"}
         

def prompt_beautifier(df, messages, tools):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=messages,
            max_tokens=5000,
            tools=tools,
            tool_choice='auto',
            response_format= {"type": "json_object"},
            temperature=0
        )
        if response.choices[0].message.content == None:
            if len(response.choices[0].message.tool_calls)>0:
                tool_name = response.choices[0].message.tool_calls[0].function.name
                print("Tool Calling: ", tool_name)
                petition = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["petition"]
                schema = retrieve_dataframe(df, petition)
                print(schema)
                messages.append({"role": "assistant", "content": None, "function_call": {"name": tool_name, "arguments": response.choices[0].message.tool_calls[0].function.arguments}})
                messages.append({"role": "function", "name": tool_name, "content": schema})
                return describe_dataframe(df, messages, tools)
        else:
            return response.choices[0].message.content
        
    except openai.BadRequestError as e:
        
        print(e.message)
        #print(response.messages[3].content[0])
        return {"data":"Error"}