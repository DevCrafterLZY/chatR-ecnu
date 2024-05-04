import os

from chatR.tools.store import faiss_engine
from chatR.tools.utils import pdf2vector

if __name__ == '__main__':

    file_name = 'Towards Spatio-Temporal Aware Traffic Time Series.pdf'
    directory = ("/workspace/lzy/chatR/chatR/static/ppdf/1/Towards Spatio-Temporal Aware Traffic Time Series/")
    file_path = directory + file_name
    pdf2vector(file_path, directory)
