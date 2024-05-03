import re
from typing import List
import json
import ast

import transformers
import torch
from langchain import FAISS
from langchain.schema import Document

from chatR.tools.prompt import PromptTemplates
from chatR.tools.utils import process_raw_docs, get_standalone_questions_list


class LocalLlmEngine:
    def __init__(
            self,
            model_name
    ):
        self.model_name = model_name
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=model_name,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device_map="auto",
        )
        self.prompt_templates = PromptTemplates()

    def _get_output(self, messages) -> str:
        prompt = self.pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        outputs = self.pipeline(
            prompt,
            max_new_tokens=1024,
            eos_token_id=[
                self.pipeline.tokenizer.eos_token_id,
                self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
            ],
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )
        return outputs[0]["generated_text"][len(prompt):]

    def get_introduce(
            self,
            vector_store: FAISS
    ) -> str:
        question = "What problem does this paper study?"
        docs_with_score = vector_store.similarity_search_with_score(question)
        docs = [doc[0] for doc in docs_with_score]
        context, _, _ = process_raw_docs(docs)
        messages = self.prompt_templates.get_llama3_introduce_messages(context, question)
        output = self._get_output(messages)
        return output

    def get_classification(
            self,
            context
    ):
        messages = self.prompt_templates.get_llama3_classify_messages(context)
        output = self._get_output(messages)
        pattern = re.compile(r'```json\s*([\s\S]+?)\s*```')
        match = pattern.search(output)
        classification = {}
        if match:
            json_content = match.group(1)
            classification = json.loads(json_content)
            print(classification)
        else:
            print("未找到JSON内容")
        return classification

    def select_docs(
            self,
            docs: List[Document],
            question
    ) -> List[int]:
        context = "\n\n".join(
            [
                f"Context {i}:\n{{{doc.page_content}}}. "
                f"{{source: {doc.metadata['source']},page: {doc.metadata['page'] + 1}}}"
                for i, doc in enumerate(docs)
            ]
        )
        messages = self.prompt_templates.get_llama3_select_docs_messages(context, question)
        ids = self._get_output(messages)
        pattern = r"\[\s*\d+\s*(?:,\s*\d+\s*)*\]"
        print("ids", ids)
        match = re.search(pattern, ids)
        if match:
            return ast.literal_eval(match.group(0))
        else:
            return []

    def get_questions(
            self,
            file_names,
            chat_history,
            question
    ) -> List[str]:
        messages = self.prompt_templates.get_llama3_refine_question_messages(file_names, chat_history, question)
        questions = self._get_output(messages)
        questions_list = get_standalone_questions_list(questions, question)
        return questions_list

    def get_a(
            self,
            file_names,
            history,
            context,
            question
    ) -> str:
        messages = self.prompt_templates.get_llama3_retrieval_qa_messages(file_names, history, context, question)
        output = self._get_output(messages)
        print(output)
        return output
