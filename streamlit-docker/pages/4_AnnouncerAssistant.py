import datetime

import streamlit as st
from agent.agent import claude2
from agent.util import find_matches, colors

st.set_page_config(
    page_title="AnnouncerAssistant",
    page_icon="✉️",
    layout="wide",
)
st.header('アナウンサーアシスタント')
st.markdown("""
与えられた記事からアナウンサー向けの放送原稿を作成します
""")

date = st.text_input('日付')
#datetime.datetime.now().strftime('%Y年%m月%d日')

title = st.text_input('タイトル')
article = st.text_area('記事')

if article:
    col1, col2 = st.columns(2)

    with col1:
        st.header("原文")
        st.write(f"タイトル: {title}")
        st.write(article.replace("。", "。<br/><br/>"), unsafe_allow_html=True)

    
    # # 分割
    # output_tokens = list(output)
    # search_tokens = [list(article)]

    # # ハイライト
    # # print(output_tokens, search_tokens)
    # html, used_source = find_matches(output_tokens, search_tokens, False)
    # # print(html)

    # html = html.replace("\n", "<br/>")
    # style = "<style>" + "\n".join([
    #     f".c{source} " + "{ color: " + colors[idx % len(colors)] + " !important; }" for idx, source in enumerate(used_source)
    # ]) + "</style>"

    # st.write(style, unsafe_allow_html=True)
    # st.write(html, unsafe_allow_html=True)
    with col2:
        st.header("放送原稿")
        title_output = claude2(f"""\
Human:
記事タイトルをニュース番組に表示するために短く要点がわかるように変換してください。
出力のみを <output> タグで囲んでください。
<title>
{title}
</title>
<article>
{article}
</article>
<rule>
- 20文字以内にしてください
- 要点について一目で伝わるように要約してください
</rule>
Assistant: <output>""").replace("</output>", "")
        st.write(f"タイトル: {title_output}", unsafe_allow_html=True)
        output = claude2(f"""\
Human:
article を元に rule に従いアナウンサー用の放送原稿を作成してください。
出力のみを <output> タグで囲んでください。
<article>
{article}
</article>
<rule>
- 文章をアナウンサーが話しやすいように流暢に繋げる
- 語尾を「です。ます。した。」にする
- 文字数を400字くらいに要約する
- 日付を可能であれば今日（{date}）に対して相対表記にする (例: 一昨日、昨日、今日、明日、今月、来月)
- 難読地名、氏名には html でルビをつける (例: <ruby>東京都<rt>とうきょうと</rt></ruby>)
- 省略語はフルにする (例: 公取委→公正取引委員会）
- 簡潔な文で要点を伝える
- 数字は算用数字を用いる
- 専門用語は平易な言葉に置き換える
- 固有名詞はフルネームで紹介する
- 人物の肩書きや役割を明確にする
- 時間や日付を明示する
</rule>
Assistant: <output>""").replace("</output>", "")
        st.write(output.replace("。", "。<br/><br/>"), unsafe_allow_html=True)

# 
