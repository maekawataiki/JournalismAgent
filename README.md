# Generative AI Journalism Assistant

This is a demo application of Journalism Assistant Agent based on Anthropic Claude on Amazon Bedrock.

自動で文献を調査し記事を作成してくれる Agent のデモアプリケーションです。Amazon Bedrock の Anthropic Claude を利用しています。

## Demo

![](images/agent_light.gif)

## Run Locally

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

