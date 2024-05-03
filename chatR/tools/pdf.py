from langchain.document_loaders import PyPDFLoader


class PdfEngine:

    def __init__(self, pdf):
        self.pdf = pdf

    # 获取pdf文件内容
    def get_pdf_document(self):
        loader = PyPDFLoader(file_path=self.pdf)
        return loader.load()
