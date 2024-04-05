import os
import json
from itertools import groupby

import boto3

from langchain.llms.bedrock import Bedrock
from langchain.tools.render import render_text_description
from langchain.agents import Tool, AgentExecutor
from langchain import hub
from langchain.tools import BraveSearch

from agent.agent_util import ClaudeReActSingleInputOutputParser, format_log_to_str  #, DuckDuckGoSearchResults, DuckDuckGoSearchAPIWrapper
from agent.util import colors, highlight, find_matches
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

brave_api_key = os.environ.get("BRAVE_API_KEY")

bedrock_client = boto3.client(
    "bedrock-runtime", region_name="us-west-2")
llm = Bedrock(
    model_id="anthropic.claude-instant-v1",
    client=bedrock_client,
    model_kwargs={'max_tokens_to_sample': 1024}
)
claude2 = Bedrock(
    model_id="anthropic.claude-v2",
    client=bedrock_client,
    model_kwargs={'max_tokens_to_sample': 2048}
)

# Agent


def geIdeaAssistant(callbacks):
    prompt_template = """\
Human: 経験豊富なジャーナリストとして、<topic></topic> について一度だけ検索を行い、得た情報をもとに
ヒットしそうな記事のアイデアを考え複数作成してください。
topic が誰に向けてのものか、その層のエンゲージメントが高まるかなどに注視してください。

You can use following tools.

<Tools>
{tools}
</Tools>

Use following format:

<output-format>
<Thought>Plan what is required to complete task</Thought>
<Action>The action to take, should be one of {tool_names}</Action>
<Action Input>the input to the action</Action Input>
<Observation>the result of the action</Observation>
<Thought>State I've got enough information</Thought>
<Summary>Summary of research result</Summary>
<Final Answer>List of ideas in format [{{ "idea": "..." }}]</Final Answer>
</output-format>

Begin!

<Topic>
{input}
</Topic>

Assistant:
<Thought>{agent_scratchpad}
"""
    return WriterAgent(prompt_template, callbacks, 6)


def getWritingAssistant(callbacks):
    prompt_template = """\
Human: As an expert journalist, conduct deep researh on provided <topic></topic> and write an news article about the topic.
The final article should explain background, benefits, painpoints, and target audience who will get impact.
Write in English if data sources are English. Otherwise write in Japanese.
You can use following tools.

<Tools>
{tools}
</Tools>

Use following format:

<output-format>
<Thought>Plan what is required to complete task</Thought>
<Action>The action to take, should be one of {tool_names}</Action>
<Action Input>the input to the action</Action Input>
<Observation>the result of the action</Observation>
... (repeat Thought/Action/Action Input/Observation for N times)
<Thought>State I now know the final answer</Thought>
<Summary>Summary of research result</Summary>
<Final Answer>Final Article in HTML body</Final Answer>
</output-format>

Begin!

<Topic>
{input}
</Topic>

Assistant:
<Thought>{agent_scratchpad}
"""
    return WriterAgent(prompt_template, callbacks)


class WriterAgent:

    def __init__(self, prompt_template, callbacks, max_results=5) -> None:
        # Initialize Tool
        # wrapper = DuckDuckGoSearchAPIWrapper(
        #     region="jp-jp", safesearch="strict", max_results=max_results)
        # search = DuckDuckGoSearchResults(api_wrapper=wrapper)
        search = BraveSearch.from_api_key(
            api_key=brave_api_key,
            search_kwargs={"count": 3, "text_decorations": 0}
        )

        tools = [
            Tool(
                name="search",
                func=search.run,
                description="日本語もしくは英語でウェブ検索が可能",
                callbacks=callbacks,
            )
        ]

        prompt = hub.pull("hwchase17/react")
        tool_names = ", ".join([t.name for t in tools])
        prompt = prompt.partial(
            tools=render_text_description(tools),
            tool_names=tool_names,
        )
        prompt.template = prompt_template

        # Stop Generation on stop token (passed to Bedrock)
        llm_with_stop = llm.bind(stop=["\n<Observation>"])

        # Create Agent
        agent = {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(x['intermediate_steps'])
        } | prompt | llm_with_stop | ClaudeReActSingleInputOutputParser()

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            return_intermediate_steps=True,
            verbose=True,
        )

    def invoke(self, topic):
        result = self.agent_executor.invoke({
            "input": topic
        })
        return result


def translate(text):
    return llm(f"""\
Human: 敏腕ITエンジニア記者として、<input></input>の xml タグで囲われた文章を日経クロステック風の日本語の記事に翻訳してください。

<ルール>
特に、できるようになったこと、メリット、影響を受ける対象層、それ以前の課題にフォーカスを当てて解説してください。
プロフェッショナルな文体にしつつ平易な文章で書いてください。
固有名詞は最初は正式名称（英語の場合はアルファベット）を括弧で添えてください。
出力は HTML 形式にしてください。
</ルール>

翻訳した文章だけを出力してください。それ以外の文章は一切出力してはいけません。

<input>
{text}
</input>

出力は翻訳結果だけを <output></output> の xml タグで囲って出力してください。
それ以外の文章は一切出力してはいけません。例外はありません。

Assistant: 
""")


def process_result(result, split_by_word=True):
    """
    Agent から出力された結果の後処理。出力とデータソースをマッチングしてハイライトする。
    """
    # 出力のクリーニング
    output = result["output"].replace("<output>", "").replace("</output>", "").replace(
        "<Title>", "").replace("</Title>", "").replace("<Body>", "").replace("</Body>", "")
    # データソースの取得
    print(result)
    search_results = [search_result for x in result["intermediate_steps"]
                      for search_result in json.loads(x[1])]
    # print(output)
    # 同じソースを JOIN
    search_results = [list(v) for _, v in groupby(
        sorted(search_results, key=lambda x: x['link']), key=lambda x: x['link'])]
    search_results = [{
        "title": v[0]["title"],
        "link": v[0]["link"],
        "snippet": "\n".join([x["snippet"] for x in v])
    } for v in search_results]
    # print(search_results)

    # 分割
    if split_by_word:
        # Word ごとにトークンとして分割
        output_tokens = list(output.split())
        search_tokens = [list(search_result['snippet'].split())
                         for search_result in search_results]
    else:
        # 一文字ごとにトークンとして分割
        output_tokens = list(output)
        search_tokens = [list(search_result['snippet'])
                         for search_result in search_results]

    # ハイライト
    # print(output_tokens, search_tokens)
    html, used_source = find_matches(
        output_tokens, search_tokens, split_by_word)
    # print(html)

    html = html.replace("\n", "<br/>")
    style = "<style>" + "\n".join([
        f".c{source} " + "{ color: " + colors[idx % len(colors)] + " !important; }" for idx, source in enumerate(used_source)
    ]) + "</style>"
    sources = [search_results[source]
               for _, source in enumerate(used_source)]
    sources_html = "\n".join([
        f"""<div>{highlight(search_results[source]['snippet'], source)}</div><a href="{search_results[source]['link']}">{search_results[source]['title']}</a>"""
        for _, source in enumerate(used_source)])

    return style, html, sources_html, sources
