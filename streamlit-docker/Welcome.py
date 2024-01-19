import streamlit as st

st.set_page_config(
    page_title="Journalism Assisstant",
    page_icon="✍️",
)

st.markdown("""\
# Journalism Assisstant

このサイトは記者向けの生成 AI のユーズケースのデモです。

- **[アイデアアシスタント](/IdeaAssistant)**: 与えられたトピックに関してヒットしそうな記事のアイデアを作成します
- **[記事執筆アシスタント](/WritingAssistant)**: 与えられたトピックについて調査し、記事の草稿を作成します。
- **[インタビューアシスタント](/InterviewAssistant)**: 与えられた記事の草稿を分析し、必要に応じてインタビュー先を提案しアポイントメールとインタビューガイドを作成します。
- **[編集アシスタント](EditorialAssistant)**: 与えられた記事に対してフィードバックを行います。またヒットしそうなタイトルとサムネイルを複数案考えます。
""")