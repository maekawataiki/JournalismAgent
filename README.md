# Generative AI Journalism Assistant

This is a demo application of Journalism Assistant Agent based on Anthropic Claude on Amazon Bedrock.

自動で文献を調査し記事を作成してくれる Agent のデモアプリケーションです。Amazon Bedrock の Anthropic Claude を利用しています。

## Demo

![](images/agent_light.gif)

## Run Locally

Amazon Bedrock への権限が付与された AWS プロファイルが必要です。また、利用しているリージョンの Anthropic Claude Instant モデルを有効化する必要があります。

```
make local-streamlit
```

## Deploy to AWS

Run this command to initialize cdk project.

```
make prepare-deploy-streamlit
```

Run this command to deploy application afterwards.

```
make deploy-streamlit
```

## License

[MIT](./LICENSE)

