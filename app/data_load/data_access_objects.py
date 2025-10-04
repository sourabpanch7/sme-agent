import json
import logging
from langchain_community.document_loaders import PyPDFLoader
from app.data_load.data_load_interface import GenericDAO


class JsonDAO(GenericDAO):
    def __init__(self):
        super().__init__()

    def read_data(self, **kwargs):
        with open(kwargs["json_path"], "r") as file:
            data = json.load(file)
        return data


class PdfDAO(GenericDAO):
    def __init__(self):
        super().__init__()

    def read_data(self, **kwargs):
        loader = PyPDFLoader(kwargs["pdf_path"])
        pages = loader.load()
        logging.info("Loaded PDF")
        return pages


