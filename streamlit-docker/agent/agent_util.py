import re
import json
import time
import subprocess
from typing import Union, List, Tuple, Optional, Type, Dict

from langchain.agents.agent import AgentOutputParser
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from langchain.schema import AgentAction, AgentFinish, OutputParserException

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field, Extra, root_validator
from langchain.tools import BaseTool

FINAL_ANSWER_ACTION = "<Final Answer>"
MISSING_ACTION_AFTER_THOUGHT_ERROR_MESSAGE = (
    "Invalid Format: Missing 'Action' after 'Thought"
)
MISSING_ACTION_INPUT_AFTER_ACTION_ERROR_MESSAGE = (
    "Invalid Format: Missing 'Action Input' after 'Action'"
)
FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE = (
    "Parsing LLM output produced both a final answer and a parse-able action:"
)


class ClaudeReActSingleInputOutputParser(AgentOutputParser):

    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        includes_answer = FINAL_ANSWER_ACTION in text
        regex = (
            r"<Action>[\s]*(.*?)[\s]*</Action>[\s]*<Action Input>[\s]*(.*)[\s]*</Action Input>"
        )
        action_match = re.search(regex, text, re.DOTALL)
        if action_match:
            if includes_answer:
                raise OutputParserException(
                    f"{FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE}: {text}"
                )
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            tool_input = tool_input.strip('"')

            return AgentAction(action, tool_input, text)

        elif includes_answer:
            return AgentFinish(
                {"output": text.split(
                    FINAL_ANSWER_ACTION)[-1].replace("</Final Answer>", "").strip()}, text
            )

        if not re.search(r"<Action>[\s]*(.*?)[\s]*</Action>", text, re.DOTALL):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation=MISSING_ACTION_AFTER_THOUGHT_ERROR_MESSAGE,
                llm_output=text,
                send_to_llm=True,
            )
        elif not re.search(
            r"[\s]<Action Input>[\s]*(.*)[\s]*</Action Input>", text, re.DOTALL
        ):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation=MISSING_ACTION_INPUT_AFTER_ACTION_ERROR_MESSAGE,
                llm_output=text,
                send_to_llm=True,
            )
        else:
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`")

    @property
    def _type(self) -> str:
        return "react-single-input"


def format_log_to_str(
    intermediate_steps: List[Tuple[AgentAction, str]],
    observation_prefix: str = "<Observation>",
    observation_suffix: str = "</Observation>",
    llm_prefix: str = "<Thought>",
) -> str:
    """Construct the scratchpad that lets the agent continue its thought process."""
    thoughts = ""
    for action, observation in intermediate_steps:
        thoughts += action.log
        thoughts += f"\n{observation_prefix}{observation}{observation_suffix}\n{llm_prefix}"
    return thoughts


class DuckDuckGoSearchAPIWrapper(BaseModel):
    """Wrapper for DuckDuckGo Search API.

    Free and does not require any setup.
    """

    region: Optional[str] = "wt-wt"
    safesearch: str = "moderate"
    time: Optional[str] = "y"
    max_results: int = 5

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that python package exists in environment."""
        try:
            from duckduckgo_search import DDGS  # noqa: F401
        except ImportError:
            raise ImportError(
                "Could not import duckduckgo-search python package. "
                "Please install it with `pip install duckduckgo-search`."
            )
        return values

    def get_snippets(self, query: str) -> List[str]:
        """Run query through DuckDuckGo and return concatenated results."""
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = ddgs.text(
                query,
                region=self.region,
                safesearch=self.safesearch,
                timelimit=self.time,
            )
            if results is None:
                return ["No good DuckDuckGo Search Result was found"]
            snippets = []
            for i, res in enumerate(results, 1):
                if res is not None:
                    snippets.append(res["body"])
                if len(snippets) == self.max_results:
                    break
        return snippets

    def run(self, query: str) -> str:
        snippets = self.get_snippets(query)
        return " ".join(snippets)

    def results(
        self, query: str, num_results: int, backend: str = "api"
    ) -> List[Dict[str, str]]:
        """Run query through DuckDuckGo and return metadata.

        Args:
            query: The query to search for.
            num_results: The number of results to return.

        Returns:
            A list of dictionaries with the following keys:
                snippet - The description of the result.
                title - The title of the result.
                link - The link to the result.
        """
        from duckduckgo_search import DDGS

        with DDGS(proxies="socks5://localhost:9050", timeout=20) as ddgs:
            results = ddgs.text(
                query,
                region=self.region,
                safesearch=self.safesearch,
                timelimit=self.time,
                backend=backend,
            )
            if results is None:
                return [{"Result": "No good DuckDuckGo Search Result was found"}]

            def to_metadata(result: Dict) -> Dict[str, str]:
                if backend == "news":
                    return {
                        "date": result["date"],
                        "title": result["title"],
                        "snippet": result["body"],
                        "source": result["source"],
                        "link": result["url"],
                    }
                return {
                    "snippet": result["body"],
                    "title": result["title"],
                    "link": result["href"],
                }

            formatted_results = []
            for i, res in enumerate(results, 1):
                if res is not None:
                    formatted_results.append(to_metadata(res))
                if len(formatted_results) == num_results:
                    break
        return formatted_results


class DDGInput(BaseModel):
    """Input for the DuckDuckGo search tool."""

    query: str = Field(description="search query to look up")


class DuckDuckGoSearchResults(BaseTool):
    """Tool that queries the DuckDuckGo search API and gets back json."""

    name: str = "DuckDuckGo Results JSON"
    description: str = (
        "A wrapper around Duck Duck Go Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. Output is a JSON array of the query results"
    )
    num_results: int = 4
    api_wrapper: DuckDuckGoSearchAPIWrapper = Field(
        default_factory=DuckDuckGoSearchAPIWrapper
    )
    backend: str = "api"
    args_schema: Type[BaseModel] = DDGInput
    DUCKDUCKGO_MAX_ATTEMPTS = 3

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        attempts = 0

        res = None
        while attempts < self.DUCKDUCKGO_MAX_ATTEMPTS:
            try:
                res = self.api_wrapper.results(
                    query, self.num_results, backend=self.backend)
                if res:
                    break
            except Exception as e:
                restart_tor()
                time.sleep(1)
                attempts += 1
                print("attempts", attempts)

        return json.dumps(res, ensure_ascii=False)


def restart_tor():
    subprocess.run(["killall -HUP tor"], shell=True)
    subprocess.run(["/etc/init.d/tor restart"], shell=True)

restart_tor()
