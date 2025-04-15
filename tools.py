describe_tools= [
    {
      "type": "function",
      "function": {
        "name": "read_columns",
        "description": "Lee las columnas del DataFrame y devuelve una lista de nombres de columna",
        "parameters": {
          "type": "object",
          "properties": {},
          "required": []
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "read_column_values",
        "description": "Lee los valores de una columna específica en el DataFrame y los devuelve como una lista",
        "parameters": {
          "type": "object",
          "properties": {
            "column": {
              "type": "string",
              "description": "Nombre de la columna que se quiere leer"
            }
          },
          "required": ["column"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "ask_info",
        "description": "Pregunta al usuario por más información sobre negocio sobre una columna o valor",
        "parameters": {
          "type": "object",
          "properties": {
            "question": {
              "type": "string",
              "description": "Pregunta para realizarle al usuario por más información de negocio sobre una columna o valor"
            }
          },
          "required": ["question"]
        }
      }
    }
  ]


retrieve_dataframe= [
    {
      "type": "function",
      "function": {
        "name": "get_dataframe",
        "description": "Lee el dataframe que el usuario quiere usar para crear los clusters. Necesitas explicar de qué se trata el dataframe al llamar a la herramienta.",
        "parameters": {
          "type": "object",
          "properties": {
              "petition": {
              "type": "string",
              "description": "Explicacion de que queres obtener el schema del dataframe y de que trata el mismo."
            }},
          "required": []
        }
      }
    }
]