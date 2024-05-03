import asyncio
from collections import defaultdict
from typing import List

from langchain import FAISS
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.schema import Document

from chatR.config.config import config
from chatR.tools.llm import llm


async def _get_relevant_documents(
        query,
        vector_store: FAISS,
        retrieval_k=5
):
    docs_with_score = vector_store.similarity_search_with_score(query, k=retrieval_k)
    docs = [doc[0] for doc in docs_with_score]
    docs_id = await llm.aselect_docs(docs, query)
    relevant_docs_with_score = [docs_with_score[i] for i in docs_id]
    sorted_relevant_docs_with_score = sorted(relevant_docs_with_score, key=lambda x: x[1], reverse=True)
    sorted_relevant_docs = [doc[0] for doc in sorted_relevant_docs_with_score]
    return sorted_relevant_docs


class Retriever:

    def __init__(self):

        self._first_retrieval_k = config.first_retrieval_k
        self._second_retrieval_k = config.second_retrieval_k
        self._metadata_field_info = [
            AttributeInfo(
                name="source",
                description="The source file name of the content.",
                type="string"
            ),
            AttributeInfo(
                name="page",
                description="Page number of the source file for the content.",
                type="integer"
            )
        ]

    def _reciprocal_rank_fusion(self, sorted_relevant_docs_lists, k=60) -> List[Document]:
        class DocumentWrapper:
            def __init__(self, doc: Document):
                self.document = doc

            def __hash__(self):
                return hash(self.document.page_content)

            def __eq__(self, other):
                return self.document.page_content == other.document.page_content

        fusion_scores = defaultdict(float)

        for i, ranked_list in enumerate(sorted_relevant_docs_lists):
            for rank, document in enumerate(ranked_list, start=1):
                temp = DocumentWrapper(document)
                fusion_scores[temp] += 1.0 / (rank + k)

        sorted_document_wrappers = sorted(fusion_scores.keys(), key=lambda x: fusion_scores[x], reverse=True)
        sorted_documents = [wrapper.document for wrapper in sorted_document_wrappers]
        return sorted_documents

    async def arrf_get_relevant_documents(
            self,
            queries,
            vector_store: FAISS,
            retrieval_k=None,
    ) -> List[Document]:

        tasks = [_get_relevant_documents(query, vector_store, self._first_retrieval_k) for query in queries]
        sorted_relevant_docs_lists = await asyncio.gather(*tasks)
        sorted_documents = self._reciprocal_rank_fusion(sorted_relevant_docs_lists)
        if retrieval_k is None:
            retrieval_k = self._second_retrieval_k
        return sorted_documents[:retrieval_k]


retriever = Retriever()
