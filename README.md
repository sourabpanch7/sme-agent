# SME AGENT

## Steps to run 

1.Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
2.Run server 
   ```bash
   uvicorn Home:app --reload 
   ```
3.Run RAG chat interface
    ```bash
    streamlit run Home_2.py
    ```
4.Run quiz generator
    ```bash
    python Home.py
    ```

## Local Host Swagger
    http://localhost:8000/docs