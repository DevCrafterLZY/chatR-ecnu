from langchain import PromptTemplate
from typing import List, Dict

REFINE_QUESTION_TEMPLATE = """Break down or rephrase the follow up input into fewer than 3 heterogeneous one-hop queries 
to be the input of a retrieval tool, if the follow up inout is multi-hop, multi-step, complex or comparative queries and 
relevant to Chat History and Document Names. Otherwise keep the follow up input as it is.

The output format should strictly follow the following, and each query can only contain 1 document name:
```
1. One-hop standalone query
...
3. One-hop standalone query
...
```


Document Names in the knowledge base:
```
{file_names}
```

Chat History(The first one is the latest):
```
{chat_history}
```

Begin:

Follow Up Input: {question}

One-hop standalone query(s):
"""

RETRIEVAL_QA_TEMPLATE = """You are a helpful research assistant. If you think the below below information are relevant 
to the human input, please respond to the human based on the relevant retrieved sources; 
otherwise, respond in your own words only about the human input.The output should be provided in Chinese.
File Names in the knowledge base:
```
{file_names}
```


Chat History:
```
{chat_history}
```


Verified Sources:
```
{context}
```


User: {question}
"""

INTRODUCE_SYS = """
You are a helpful research assistant.The following context are some parts of an academic paper. 
Based on the following known content, provide a concise and professional answer to the user's question.
The output should be provided in Chinese. Answer in approximately 100 Chinese characters.
You can begin like this: 本篇文章主要研究了...
"""

INTRODUCE_TEMPLATE = """

Context:
```
{context}
```

Question:
```
{question}
```
"""

CLASSIFY_SYS = """
以下是几篇文献的概述，请根据其研究主题分为不同的类别，如：推荐系统研究，城市交通预测等类别。
类别名在8个字以内，一篇文献不能出现在多个类别中：
"""

CLASSIFY_TEMPLATE = """
文献概述：
```
{summary}
```
输出要求:
请不要做额外的解释，只返回如下的json格式，包括前导和尾随的“```json”和“```”，注意文献id为数字,不带引号:
```json
[
    {{
        "name": 类别名1,
        "children":[文献id1,文献id2,...]
    }},
    {{
        "name": 类别名2,
        "children":[文献id3,文献id4,...]
    }},
    ...
]
```
"""

DOCS_SELECTION_TEMPLATE = """Below are some verified sources and a human input. 
If you think any of them are relevant to the human input, then list all possible context numbers.

```
{context}
```

The output format must be like the following, nothing else. If not, you will output []:
[0, ..., n]

Human Input: {question}
"""


class PromptTemplates:

    def __init__(self):
        self.refine_question_template = REFINE_QUESTION_TEMPLATE
        self.introduce_sys = INTRODUCE_SYS
        self.introduce_template = INTRODUCE_TEMPLATE
        self.classify_sys = CLASSIFY_SYS
        self.classify_template = CLASSIFY_TEMPLATE
        self.select_docs_template = DOCS_SELECTION_TEMPLATE
        self.retrieval_qa_template = RETRIEVAL_QA_TEMPLATE

    def get_refine_question_template(self):
        temp = self.refine_question_template
        return PromptTemplate(
            template=temp,
            input_variables=["file_names", "chat_history", "question"]
        )

    def get_retrieval_qa_template(self):
        temp = self.retrieval_qa_template
        return PromptTemplate(
            template=temp,
            input_variables=["file_names", "context", "question", "chat_history"]
        )

    def get_introduce_template(self):
        temp = self.introduce_sys + self.introduce_template
        return PromptTemplate(
            template=temp,
            input_variables=["context", "question"]
        )

    def get_classify_template(self):
        temp = self.classify_sys + self.classify_template
        return PromptTemplate(
            template=temp,
            input_variables=["summary"]
        )

    def get_select_docs_template(self):
        temp = self.select_docs_template
        return PromptTemplate(
            template=temp,
            input_variables=["context", "question"]
        )

    def get_llama3_introduce_messages(self, context, question) -> List[Dict[str, str]]:
        prompt_template = PromptTemplate(
            template=self.introduce_template,
            input_variables=["context", "question"]
        )
        message = prompt_template.format(context=context, question=question)
        messages = [
            {"role": "system", "content": self.introduce_sys},
            {"role": "user", "content": message},
        ]
        return messages

    def get_llama3_classify_messages(self, context) -> List[Dict[str, str]]:
        prompt_template = PromptTemplate(
            template=self.classify_template,
            input_variables=["summary"]
        )
        message = prompt_template.format(summary=context)
        messages = [
            {"role": "system", "content": self.classify_sys},
            {"role": "user", "content": message},
        ]

        return messages
