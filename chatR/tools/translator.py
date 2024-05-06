from transformers import AutoModelWithLMHead, AutoTokenizer, pipeline


class Translator:
    def __init__(
            self
    ):
        self.model_name = '/home/Helsinki-NLP/opus-mt-zh-en'
        self.translator = pipeline(
            "translation_zh_to_en",
            model=AutoModelWithLMHead.from_pretrained(self.model_name),
            tokenizer=AutoTokenizer.from_pretrained(self.model_name)
        )

    def translate(
            self,
            text
    ) -> str:
        return self.translator(text, max_length=1024)[0]['translation_text']


translator = Translator()
