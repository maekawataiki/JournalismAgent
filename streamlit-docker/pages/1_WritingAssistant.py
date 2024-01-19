from typing import Dict, Any

import re
import streamlit as st
from langchain.callbacks.base import BaseCallbackHandler

from agent.agent import getWritingAssistant, process_result, translate

st.set_page_config(
    page_title="記事執筆アシスタント",
    page_icon="✍️",
)
st.header('記事執筆アシスタント')
st.markdown("""
与えられたお題に対して調査、記事の執筆、ファクトチェックを行います。
""")
if 'article' not in st.session_state:
    st.session_state['article'] = None
if 'sources' not in st.session_state:
    st.session_state['sources'] = None


topic = st.text_input('何についての記事を執筆欲しいですか？')


# LangChain の中間ステップを Streamlit に出力するためのハンドラー
class ToolStartHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        if serialized["name"] == "search":
            st.write("検索: " + input_str)


agent = getWritingAssistant([ToolStartHandler()])

if topic:
    st.write("実行中...")
    result = agent.invoke(topic)

    if re.search(r'[^\x00-\x7f]', result['output']):
        # ASCII でない文字が含まれる（日本語だと推定）
        style, highlighted, sources_html, sources = process_result(
            result, split_by_word=False)

        st.write(style, unsafe_allow_html=True)
        st.subheader("生成された記事")
        st.write(highlighted, unsafe_allow_html=True)
        article = result["output"]
    else:
        # ASCII のみ（英語だと推定）
        style, highlighted, sources_html, sources = process_result(result, split_by_word=True)

        st.write(style, unsafe_allow_html=True)
        st.subheader("生成された英語記事")
        st.write(highlighted, unsafe_allow_html=True)

        st.subheader("生成された日本語記事")
        translated = translate(result["output"])
        st.write(translated, unsafe_allow_html=True)
        article = translated

    st.header('出典')
    st.write(sources_html, unsafe_allow_html=True)

    st.session_state.article = article
    st.session_state.sources = sources
