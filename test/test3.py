from chatR.tools.prompt import PromptTemplates

if __name__ == '__main__':
    prompt = PromptTemplates().get_retrieval_qa_template()
    res = prompt.format(file_names= '1',chat_history= '1', context='1', question='1')
    print(type(res))
