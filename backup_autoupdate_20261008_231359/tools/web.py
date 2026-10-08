import os

import requests

from bs4 import BeautifulSoup


def search(
    query,
    max_results=6
):

    # ==================================
    # Tavily ถ้ามี API Key
    # ==================================

    api_key = os.getenv(
        "TAVILY_API_KEY",
        ""
    )


    if api_key:

        try:

            response = requests.post(

                "https://api.tavily.com/search",

                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results
                },

                timeout=15

            )

            response.raise_for_status()

            data = response.json()


            return [

                {
                    "title":
                    item.get(
                        "title",
                        ""
                    ),

                    "url":
                    item.get(
                        "url",
                        ""
                    ),

                    "snippet":
                    item.get(
                        "content",
                        ""
                    )

                }

                for item
                in data.get(
                    "results",
                    []
                )

            ]

        except Exception:

            pass


    # ==================================
    # DuckDuckGo fallback
    # ==================================

    response = requests.get(

        "https://html.duckduckgo.com/html/",

        params={
            "q": query
        },

        headers={
            "User-Agent":
            "Mozilla/5.0"
        },

        timeout=15

    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    results = []


    for link in soup.select(
        ".result__a"
    )[:max_results]:

        parent = link.find_parent(
            ".result"
        )

        snippet = ""


        if parent:

            element = parent.select_one(
                ".result__snippet"
            )

            if element:

                snippet = element.get_text(
                    " ",
                    strip=True
                )


        results.append({

            "title":
            link.get_text(
                " ",
                strip=True
            ),

            "url":
            link.get(
                "href",
                ""
            ),

            "snippet":
            snippet

        })


    return results


def format_results(results):

    output = []


    for index, result in enumerate(
        results,
        1
    ):

        output.append(

            f"{index}. "
            f"{result['title']}\n"
            f"URL: {result['url']}\n"
            f"{result['snippet']}"

        )


    return "\n\n".join(
        output
    )