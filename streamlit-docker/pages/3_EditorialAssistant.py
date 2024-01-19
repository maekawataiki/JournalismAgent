import json
import base64
from io import BytesIO

import streamlit as st
from agent.agent import llm, bedrock_client

st.set_page_config(
    page_title="編集アシスタント",
    page_icon="📝",
)
st.header('編集アシスタント')
st.markdown("""
与えられた記事に対してフィードバックを行います。またヒットしそうなタイトルとサムネイルを複数案考えます。
""")

if 'article' not in st.session_state:
    st.session_state['article'] = None
if 'sources' not in st.session_state:
    st.session_state['sources'] = None
article = st.session_state.article
sources = st.session_state.sources

article = st.text_area('記事のアイデア/草稿', article)
sources = st.text_area('データソース（追加のものがあれば末尾にペースト）', sources)

if article:
    comment = llm(f"""\
Human:
経験豊富なニュース編集長として、Article の内容を精読し、記事の事実性、記事に含まれるバイアス/偏向、記事を読むことで新たな発見が得られるか
より深い洞察ができないかなどの観点から厳しく複数のフィードバックを与えてください。
可能な限り改善点を示してください。
出典は sources に示します。
出力のみを <output> タグで囲み output-format に従ってください。
<article>
{article}
</article>
<sources>
{sources}
<sources>
<output-format>
[{{ "excerpt": "article から抜粋", "feedback": "フィードバック" }}]
</output-format>
Assistant: <output>""").replace("</output>", "")
    print(comment)
    st.subheader("フィードバック")
    st.write(json.loads(comment))

    # タイトル案
    titles = llm(f"""\
Human:
経験豊富なニュース編集長として、Article の内容を精読し、クリック率が高い記事のタイトルを複数案考えてください。
出力のみを <output> タグで囲み output-format に従ってください。
<article>
{article}
</article>
<output-format>
[{{ "title": "タイトル" }}]
</output-format>
Assistant: <output>""").replace("</output>", "")
    st.subheader("タイトル案")
    st.write("ここにクリック率予測モデルなどを統合することでタイトルを定量的に評価できるようになります。")
    st.write(json.loads(titles))

    # サムネイル案
    prompt = titles = llm(f"""\
Human: あなたは Stable Diffusion のプロンプトを生成する AI アシスタントです。
<rules>
* article の特徴を描いたプロンプトを生成してください
* プロンプトは output の xml タグに囲われた通りに出力してください。
* プロンプトは単語単位で、カンマ区切りで出力してください。長文で出力しないでください。プロンプトは必ず英語で出力してください。
* プロンプトには以下の要素を含めてください。
 * 画像のクオリティ、被写体の情報、衣装・ヘアスタイル・表情・アクセサリーなどの情報、画風に関する情報、背景に関する情報、構図に関する情報、ライティングやフィルタに関する情報
* フィルタリング対象になる不適切な要素は出力しないでください。
</rules>
<article>
{article}
</article>
Assistant: <output>""").replace("</output>", "")
    st.subheader("サムネイル案")
    st.write("このサンプルでは生成していますが、ストック画像から適切なものを自動で提案したり、クリック率予測モデルなどを統合することで適したサムネイルの選択をサポートすることも可能です。")
    st.write(prompt)

    numImage = 3
    body = json.dumps(
        {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt,   # Required
                #  "negativeText": ""  # Optional
            },
            "imageGenerationConfig": {
                "numberOfImages": numImage,   # Range: 1 to 5 
                "quality": "standard",  # Options: standard or premium
                "height": 768,         # Supported height list in the docs 
                "width": 1280,         # Supported width list in the docs
                "cfgScale": 7.5,       # Range: 1.0 (exclusive) to 10.0
            }
        }
    )
    response = bedrock_client.invoke_model(
        body=body,
        modelId="amazon.titan-image-generator-v1",
        accept="application/json", 
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())

    cols = st.columns(numImage)
    for col, base64_image in zip(cols, response_body.get("images")):
        with col:
            st.image(BytesIO(base64.b64decode(base64_image)), use_column_width=True)
