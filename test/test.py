import os

from chatR.tools.store import faiss_engine
from chatR.tools.utils import pdf2vector

if __name__ == '__main__':

    directory = (os.getcwd() + '/pdf')
    file_path = "/workspace/lzy/chatR/test/pdf/Towards Spatio-Temporal Aware Traffic Time Series.pdf"
    # print(file_path)
    # pdf2vector(file_path, directory)
    vector_store = faiss_engine.load_vector_store([directory])
