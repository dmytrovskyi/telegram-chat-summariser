#!./venv/bin/python

import json
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.documents.base import Blob
from dotenv import load_dotenv
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
import prompts


from telegram.constants import ChatType

from prompts import (
    summarize_template_with_links,
    summarize_template,
    retell_template,
    identify_params_template,
)

load_dotenv()

model_t9 = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)
model_t0 = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
whisper_parser = OpenAIWhisperParser()

parser = StrOutputParser()

chain_t9 = model_t9 | parser
chain_t0 = model_t0 | parser

def ai_summarize_basic(messages: str, template: str):
    jjj = json.dumps(messages, sort_keys=True, default=str, ensure_ascii=False)
    request = [SystemMessage(content=template), HumanMessage(content=jjj)]

    return chain_t9.invoke(request)


def ai_retell(messages, params):
    template = PromptTemplate.from_template(retell_template).format(
        language=params["language"], tone=params["tone"]
    )
    return ai_summarize_basic(messages, template)


def ai_summarize(messages, params, chat_type):
    template = summarize_template
    chat_id = params["chat_id"]

    if chat_type == ChatType.SUPERGROUP:
        template = summarize_template_with_links
        chat_id = str(chat_id)[4:]

    template = PromptTemplate.from_template(template).format(
        language=params["language"], tone=params["tone"], chat_id=chat_id
    )
    return ai_summarize_basic(messages, template)


def ai_identify_parameters(message):
    result = chain_t0.invoke(
        [SystemMessage(content=identify_params_template), HumanMessage(content=message)]
    )
    result = json.loads(result)
    return result


def ai_request_with_params(message):
    params = ai_identify_parameters(message)
    return params

def ai_describe_image(base64_data):
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe what in the image image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
            },
        ],
    )
    response = chain_t9.invoke([message])
    return response

def ai_transcript_audio(path: Path) -> str:
    blob = Blob.from_path(path)
    documents = whisper_parser.parse(blob)
    result = ''
    for doc in documents:
        if doc.page_content:
            result += doc.page_content
    return result

def ai_summarize_page_content(page_content: str):
    messages = [
        SystemMessage(content=prompts.summarize_web_content),
        HumanMessage(content=page_content),
    ]
    response = chain_t9.invoke(messages)
    return response
 