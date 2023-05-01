import os
import openai
import requests
import json
import streamlit as st
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html2text

from collections import namedtuple
import altair as alt
import math
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image

# Set up OpenAI API credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up Pubmed API endpoint and query parameters
pubmed_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 5,
    "api_key": "5cd7903972b3a715e29b76f1a15001ce9a08"
}

# Define function to generate text using OpenAI API
def generate_text(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=2024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response["choices"][0]["message"]["content"].strip()

# Define function to search for articles using Pubmed API
def search_pubmed(query):
    params["term"] = query
    response = requests.get(pubmed_endpoint, params=params)
    data = response.json()
    article_ids = data["esearchresult"]["idlist"]
    articles = [{"id": article_id, "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"} for article_id in article_ids]
    return articles

# Define function to scrape article abstracts
def scrape_abstract(articles):
    abstracts = []
    for article in articles:
        url = article["url"]
        html_page = urlopen(url)
        soup = BeautifulSoup(html_page, features="html.parser")
        abstract = soup.find("div", {"class": "abstract-content selected"}).text
        abstracts.append({"id": article["id"], "url": url, "abstract": abstract})
    return abstracts

# Define function to convert html abstracts to text
def convert_to_text(abstracts):
    text_abstracts = []
    for abstract_info in abstracts:
        h = html2text.HTML2Text()
        h.ignore_links = True
        text_abstract = h.handle(abstract_info["abstract"])
        text_abstracts.append({"id": abstract_info["id"], "url": abstract_info["url"], "abstract": text_abstract})
    return text_abstracts

# Get user input
user_input = st.text_input("Hi there, I am EBPcharlie. What is your clinical question?")

# Search for articles using Pubmed API
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        articles = search_pubmed(user_input)
        st.write(f"Found {len(articles)} articles related to your clinical question.")
        abstracts = scrape_abstract(articles)
        text_abstracts = convert_to_text(abstracts)

        # Generate a list of PMIDs and URLs
        pmid_url_list = "\n".join([f"PMID: {abstract_info['id']} URL: {abstract_info['url']}" for abstract_info in text_abstracts])

        # Generate prompt for OpenAI API
        prompt = f"Using your expert knowledge, analyze the following systematic reviews related to '{user_input}' published between 2021-2023:\n{pmid_url_list}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of these articles.\n\n2. Important Outcomes (with PMID and URL):\n- List the most important outcomes in bullet points and ensure that the PMID and URL mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of these articles.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in these articles that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of these articles.\n\n6. Conclusion:\n- Sum up the main takeaways from these articles."

        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts
        st.subheader("Article Abstracts")
        for abstract_info in text_abstracts:
            st.write(f"PMID: {abstract_info['id']}")
            st.write(f"URL: {abstract_info['url']}")
            st.write(abstract_info["abstract"])
            st.write("\n\n\n")

        # Create a word cloud visualization based on the summary
        wordcloud = WordCloud(width=800, height=800, background_color='white', colormap='viridis', max_words=100).generate(summary)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        st.subheader("Word Cloud Visualization")
        st.pyplot(plt)

