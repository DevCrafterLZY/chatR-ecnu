import transformers
import torch
import re
from langchain import HuggingFacePipeline, FAISS
import json

from chatR.tools.prompt import PromptTemplates, INTRODUCE_SYS
from chatR.tools.utils import process_raw_docs


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

    def _get_output(self, prompt) -> str:
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
        prompt_template = self.prompt_templates.get_introduce_template()
        message = prompt_template.format(context=context, question=question)
        messages = [
            {"role": "system", "content": INTRODUCE_SYS},
            {"role": "user", "content": message},
        ]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        output = self._get_output(prompt)
        return output

    def get_classification(
            self,
            context
    ):
        prompt_template = self.prompt_templates.get_classify_template()
        message = prompt_template.format(summary=context)
        messages = [
            {"role": "system", "content": INTRODUCE_SYS},
            {"role": "user", "content": message},
        ]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        output = self._get_output(prompt)
        print(output)
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
