import os
import json
import pandas as pd
import tiktoken
import openai
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Custom module imports
from utils import *
from prompts import *
from tools import *

# Load environment variables
load_dotenv()
api_key = os.getenv('OpenAI_GPT')
client = OpenAI(api_key=api_key)


def chunk_list(data, chunk_size):
    """Splits a list into smaller chunks."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

# Load dataset
df = pd.read_csv(f'{input("Enter the path to the CSV file: ")}')

# Prepare prompt for clustering
messages = [
    {"role": "system", "content": system_prompt_beautifier},
    {"role": "user", "content": "Quiero crear clusters a partir un dataframe sobre interacciones de los clientes de despegar.com"}
]
new_prompt = prompt_beautifier(df, messages, retrieve_dataframe)
prompt_data = json.loads(new_prompt)
columns_list = prompt_data['unstructured_columns']

df_processed = df.copy()

# Process each unstructured column
for col in columns_list:
    column_name = col['column_name']
    description = col['description']
    
    print('Starting with column:', column_name)
    print('Description:', description)

    def process_row(i):
        data = df_processed[column_name][i]
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sumup_system.format(column_name=column_name, description=description)},
                    {"role": "user", "content": sumup_user.format(data=data)}
                ],
                temperature=0,
                max_tokens=400,
                seed=50
            )
            return i, response.choices[0].message.content
        except openai.BadRequestError as e:
            print(f"Error in row {i}: {e}")
            return i, "Error"

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_row, i): i for i in range(len(df_processed))}
        for future in tqdm(as_completed(futures), total=len(futures)):
            i, result = future.result()
            if result:
                df_processed.at[i, column_name] = result

#Eliminamos todas las columnas de ids y que tengan algun timestamp de _end o _start para reducir el dataframe
print("Reducing dataframe size, actual size: ", len(df_processed))
df_processed = df_processed.drop(columns=[col for col in df_processed.columns if col.endswith('_id')])
df_processed = df_processed.drop(columns=[col for col in df_processed.columns if '_start' in col or '_end' in col])
df_processed.drop_duplicates(inplace=True)
print("New size: ", len(df_processed))

# Convert processed dataframe to list of dicts
records = df_processed.to_dict(orient='records')
print("Total number of rows:", len(records))

# Tokenize and calculate chunk size
encoding = tiktoken.get_encoding("cl100k_base")
records_str = '\n'.join([str(record) for record in records])
tokens = encoding.encode(records_str)

print("Total tokens:", len(tokens))
n_chunks = len(tokens) / 64000
chunk_size = round(len(records) / n_chunks)
print("Rows per chunk:", chunk_size)

# Create chunks
chunks = chunk_list(records, chunk_size)
print("Total chunks:", len(chunks))

# Create clusters from chunks
clusters = []
for idx, chunk in enumerate(chunks):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_clusters.format(beautiful_prompt=prompt_data['prompt'])},
            {"role": "user", "content": clusters_user.format(data=chunk)}
        ],
        temperature=0,
        max_tokens=1000,
        seed=50
    )
    clusters.append(response.choices[0].message.content)
    print(f"Cluster {idx} appended")

# Merge all clusters and finalize
merged_clusters = '\n\n-------- NEXT CHUNK -------\n\n'.join(clusters)
final_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_clusters_tot.format(beautiful_prompt=prompt_data['prompt'])},
        {"role": "user", "content": clusters_tot_user.format(clusters=merged_clusters)}],
    temperature=0,
    max_tokens=2000,
    seed=50
)

# Print final clustering output
final_clusters = final_response.choices[0].message.content
print(final_clusters)
