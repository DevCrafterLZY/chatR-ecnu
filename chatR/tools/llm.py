import ast
import json
import re
from typing import List

from langchain.chains import RetrievalQA, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from chatR.config.config import config
from chatR.tools.local_llm import LocalLlmEngine
from chatR.tools.prompt import PromptTemplates
from chatR.tools.utils import get_standalone_questions_list, history_list2str


class LlmEngine:

    def __init__(
            self,
            model_name: str = config.model_name,
            streaming: bool = False
    ):
        self.model_name = model_name
        self.streaming = streaming
        self.prompt_templates = PromptTemplates()
        self.openai = ChatOpenAI(
            model_name=self.model_name,
            streaming=self.streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=config.openai_api_key
        )

    def get_questions(
            self,
            file_names,
            chat_history,
            question
    ) -> List[str]:
        prompt = self.prompt_templates.get_refine_question_template()
        chain = LLMChain(
            llm=self.openai,
            verbose=True,
            prompt=prompt
        )
        chat_history = history_list2str(chat_history)
        answer = chain({"file_names": file_names, "chat_history": chat_history, "question": question})
        questions_list = get_standalone_questions_list(answer["text"], question)
        return questions_list

    def get_a(
            self,
            file_names,
            history,
            context,
            question
    ) -> str:
        prompt = self.prompt_templates.get_retrieval_qa_template()

        chain = LLMChain(
            llm=self.openai,
            verbose=True,
            prompt=prompt
        )
        history = history_list2str(history)
        answer = chain({"file_names": file_names, "chat_history": history, "context": context, "question": question})
        return answer["text"]

    async def get_introduce(
            self,
            vector_store,
    ) -> str:
        chain = RetrievalQA.from_llm(
            llm=self.openai,
            verbose=True,
            retriever=vector_store.as_retriever(),
            prompt=self.prompt_templates.get_introduce_template()
        )
        return await chain.arun("What problem does this paper study?")

    def get_classification(
            self,
            context,
            f_ids
    ):
        chain = LLMChain(
            llm=self.openai,
            verbose=True,
            prompt=self.prompt_templates.get_classify_template()
        )
        res = chain.run(context)
        pattern = re.compile(r'```json\s*([\s\S]+?)\s*```')
        match = pattern.search(res)
        classification = [
            {
                "name": "文献",
                "children": f_ids
            }
        ]
        if match:
            json_content = match.group(1)
            classification = json.loads(json_content)
            print(classification)
        else:
            print("未找到JSON内容")
        return classification

    async def select_docs(
            self,
            docs: List[Document],
            question
    ) -> List[int]:
        chain = LLMChain(
            llm=self.openai,
            verbose=True,
            prompt=self.prompt_templates.get_select_docs_template()
        )
        context = "\n\n".join(
            [
                f"Context {i}:\n{{{doc.page_content}}}. "
                f"{{source: {doc.metadata['source']},page: {doc.metadata['page'] + 1}}}"
                for i, doc in enumerate(docs)
            ]
        )
        ids = await chain.arun(context=context, question=question)
        pattern = r"\[\s*\d+\s*(?:,\s*\d+\s*)*\]"
        print("ids", ids)
        match = re.search(pattern, ids)
        if match:
            return ast.literal_eval(match.group(0))
        else:
            return []


llm = None
if config.model_name == "gpt-3.5-turbo":
    llm = LlmEngine()
else:
    llm = LocalLlmEngine(config.model_name)
