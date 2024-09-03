#!./.venv/bin/python

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
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
