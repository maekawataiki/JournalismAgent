import json

import streamlit as st
from agent.agent import llm

st.set_page_config(
    page_title="インタビューアシスタント",
    page_icon="✉️",
)
st.header('インタビューアシスタント')
st.markdown("""
与えられた記事のお題や草稿から裏付けに必要なインタビューを提案し、アポイントのメールとインタビューガイドを作成します。
""")

if 'article' not in st.session_state:
    st.session_state['article'] = None
if 'sources' not in st.session_state:
    st.session_state['sources'] = None
article = st.session_state.article
sources = st.session_state.sources

default_value = ""
if article and sources:
    default_value = f"草稿:\n{article}\nソース:\n{sources}"

article = st.text_area('記事のアイデア/草稿', default_value)

if article:
    comment = llm(f"""\
Human:
Article の内容を精査し、誰にどのようなインタビューを行えば、事実の裏付けが取れるか、
またはより記事の内容をよくできるようなコメントを入手できるか考え、アポイントメールとインタビューガイドを作成してください。
ニュースサイトの記者としてアポイントメールは who で示した人物に対する敬語を使った丁寧なメールを執筆してください。
出力のみを <output> タグで囲み output-format に従ってください。
<article>
{article}
</article>
<output-format>
[{{ "who": "...", "email_message": "...", "interview_guide": "..."}}]
</output-format>
Assistant: <output>""").replace("</output>", "")
    print(comment)
    st.write(json.loads(comment))

