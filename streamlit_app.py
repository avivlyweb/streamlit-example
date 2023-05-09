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
import pdfkit
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
        messages=[{"role": "system", "content": "You are an AI-powered research assistant."},
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

# Define functions to export content to PDF and TXT
def export_to_pdf(filename, content):
    pdfkit.from_string(content, filename)

def export_to_txt(filename, content):
    with open(filename, "w") as f:
        f.write(content)

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

        # Generate a list of
PMIDs and URLs
pmid_url_list = "\n".join([f"PMID: {abstract_info['id']} URL: {abstract_info['url']}" for abstract_info in text_abstracts])

    # Generate prompt for OpenAI API
    prompt = f"Based on your expertise, please analyze the following systematic reviews related to '{user_input}', published between 2019 and 2023. The reviews are accessible via the following PMIDs and URLs: {pmid_url_list}.\n\nYour analysis should be structured and include the following sections:\n\n1. Summary of Findings: Provide a concise summary of the main findings from the articles.\n\n2. Important Outcomes (with PMID and URL): Identify the most significant outcomes, and ensure that each outcome is appropriately linked to the correct article via PMID and URL.\n\n3. Comparisons and Contrasts: Highlight any significant similarities or differences between the findings of the articles.\n\n4. Innovative Treatments or Methodologies: Identify any innovative treatments or methodologies discussed in the articles that could have a significant impact on the field.\n\n5. Future Research and Unanswered Questions: Discuss potential future research directions or unanswered questions based on the articles' findings.\n\n6. Conclusion: Summarize the primary takeaways from the articles.\n\nPlease provide a detailed analysis in accordance with the above guidelines."

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

    # Add export functionality
    export_format = st.selectbox("Choose an export format:", ["", "PDF", "TXT"])

    if st.button("Export Summary and Abstracts"):
        if not export_format:
            st.error("Please select an export format.")
        else:
            # Combine the summary and abstracts into a single string
            combined_content = f"Summary of Findings:\n{summary}\n\nArticle Abstracts:\n"
            for abstract_info in text_abstracts:
                combined_content += f"\nPMID: {abstract_info['id']}\nURL: {abstract_info['url']}\n{abstract_info['abstract']}\n\n\n"

            # Export the content based on the selected format
            if export_format == "PDF":
                export_to_pdf("summary_and_abstracts.pdf", combined_content)
                st.success("Exported to summary_and_abstracts.pdf")
            elif export_format == "TXT":
                export_to_txt("summary_and_abstracts.txt", combined_content)
                st.success("Exported to summary_and_abstracts.txt")
