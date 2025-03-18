import requests
import json
import os
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

load_dotenv()

async def serper_web_search(query: str) -> str:
    """
    Perform a web search using the Serper API and return the results.
    """
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query,
        "gl": "in"
    })
    headers = {
    'X-API-KEY': os.getenv("SERPER_API_KEY"),
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    return response.text
    

async def scrape_website(url: str) -> str:
    """
    Scrape a web page and return its content in markdown format.
    """
    prune_filter = PruningContentFilter(
        threshold_type="dynamic",
        threshold=0.45,
        min_word_threshold=5
    )
    md_generator = DefaultMarkdownGenerator(
        content_filter=prune_filter,
        options={
            "ignore_links": True,
            "escape_html": False,
            "skip_internal_links": True,
        }
    )
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
        exclude_external_links=True,
        remove_overlay_elements=True,
        markdown_generator=md_generator
    )  

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )

    if not result.success:
        raise Exception(f"Failed to scrape {url}: Status Code {result.status_code} | {result.error_message}")
    
    return result.markdown.fit_markdown

def get_eval_criteria() -> str:
    """
    Load the pre-defined criteria for evaluating the argumnts presented by agents
    """
    with open("evaluation-criteria.md", 'r') as f:
        criteria = f.read()
    return criteria