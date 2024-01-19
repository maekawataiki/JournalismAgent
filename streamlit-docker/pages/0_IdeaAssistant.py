from typing import Dict, Any

import json

import streamlit as st

from agent.agent import llm
from langchain.callbacks.base import BaseCallbackHandler

from agent.agent import geIdeaAssistant

st.set_page_config(
    page_title="アイデアアシスタント",
    page_icon="💬",
)
st.header('アイデアアシスタント')
st.markdown("""
与えられたお題に対してヒットしそうな記事のアイデアを考えます。
""")

topic = st.text_input('何についてのアイデアを出して欲しいですか？')

# LangChain の中間ステップを Streamlit に出力するためのハンドラー
class ToolStartHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        if serialized["name"] == "search":
            st.write("検索: " + input_str)


agent = geIdeaAssistant([ToolStartHandler()])

if topic:
    st.write("実行中...")
    result = agent.invoke(topic)

    st.subheader("生成されたアイデア")
    st.write(json.loads(result["output"]))
