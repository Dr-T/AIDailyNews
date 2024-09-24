import json
import os

import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

from workflow.gpt.prompt import multi_content_prompt


def evaluate_article_with_gpt(articles):
    load_dotenv()

    article_links = [article.link for article in articles]
    logger.info(f"start summary: {article_links}")

    prompt = multi_content_prompt

    gpt_input = ""
    for idx, item in enumerate(articles):
        gpt_input += f"```link: {item.link}, content:{item.summary}```.\n"

    ai_provider = os.environ.get("AI_PROVIDER")
    if ai_provider == "openai":
        response = request_openai(prompt=prompt, content=gpt_input)
    else:
        response = request_gemini(prompt=prompt, content=gpt_input)
    response_list = transform2json(response)
    # check format
    if not response_list:
        return []
    if not isinstance(response_list, list):
        # 有时单个内容未按数组格式输出
        response_list = [response_list]

    evaluate_list = [item for item in response_list if item.get("title") and item.get("link")]
    return evaluate_list


def request_gemini(prompt, content):
    input_text = f"{prompt}: {content}"

    api_key = os.environ.get("GPT_API_KEY")
    if not api_key:
        raise ValueError("gemini key is empty")

    genai.configure(api_key=api_key)
    # Set up the model
    generation_config = genai.GenerationConfig(temperature=0.2)

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]
    model = genai.GenerativeModel(model_name='gemini-pro',
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

    try:
        response = model.generate_content([input_text])
        logger.info(response.text)
        return response.text
    except Exception as e:
        logger.error(f"request gemini failed: {e}, skip")
        return None


def request_openai(prompt, content):
    try:
        client = OpenAI(api_key=os.environ["GPT_API_KEY"],
                        base_url=os.environ.get("GPT_BASE_URL", "https://api.openai.com"))

        chat_completion = client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": content
            }
        ], model=os.environ.get("GPT_MODEL_NAME", "gpt-3.5-turbo"))
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"request openai failed: {e}")


def transform2json(result):
    if not result:
        return None
    format_json = None
    # 去掉首尾两行就是完整json内容
    text = result.removeprefix("```json")
    text = text.removesuffix("```")
    # 有时输出格式可能不完全符合json
    try:
        json_obj = json.loads(text)
        # 关键信息校验
        format_json = json_obj
    except Exception as e:
        logger.exception(f"{e}")
    finally:
        return format_json
