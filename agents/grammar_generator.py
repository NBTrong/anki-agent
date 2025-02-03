import json
import os
from typing import Optional
from pydantic import Field

from phi.agent import Agent, RunResponse
from phi.utils.pprint import pprint_run_response
from phi.model.openai import OpenAIChat
from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url
from pydantic import BaseModel, Field
import pandas as pd
from phi.tools.crawl4ai_tools import Crawl4aiTools
from phi.tools.duckduckgo import DuckDuckGo
import urllib.parse
from bs4 import BeautifulSoup
import lxml
from tools.search_image import get_images_for_word
from typing import Iterator


class Grammar(BaseModel):
  grammar: str = Field(..., description="Grammar to be learned")
  meaning: str = Field(..., description="Meaning of the grammar")
  example_sentences_1: str = Field(..., description="Example sentence 1 for the grammar")
  meaning_example_sentences_1: str = Field(..., description="Meaning of example sentence 1")
  example_sentences_2: str = Field(..., description="Example sentence 2 for the grammar")
  meaning_example_sentences_2: str = Field(..., description="Meaning of example sentence 2")
  image_url: Optional[str] = Field(None, description="URL of the image illustrating the grammar")

class GrammarList(BaseModel):
  grammars: list[Grammar] = Field(..., description="List of grammars")

class GrammarGenerator(Agent):
    target_language: str = Field(default="English")
    native_language: str = Field(default="Vietnamese")
    related_sentence_agent: Agent = Field(default=None)

    def __init__(self, target_language: str = "English", native_language: str = "Vietnamese"):
      super().__init__()
      self.target_language = target_language
      self.native_language = native_language
      self.related_sentence_agent = Agent(
        name="Related Sentence generator Agent",
        agent_id="related_sentence_generator",
        model=OpenAIChat(
          id=agent_settings.gpt_4,
          max_tokens=agent_settings.default_max_completion_tokens,
          temperature=agent_settings.default_temperature,
        ),
        description=f"""An AI assistant specialized in generating contextually relevant and natural example sentences 
          for grammar rules in {self.target_language}, helping {self.native_language} native speakers learn the language.""",
        instructions=[
          f"You are a helpful assistant that generates example sentences for {self.target_language} grammar rules.",
          f"Your target audience are native {self.native_language} speakers learning {self.target_language}.",
          "For each grammar rule provided:",
          "0. Create all meanings of the grammar rule, rewrite the grammar rule in the native language",
          "1. Create 2-3 natural, contextually appropriate example sentences",
          "2. Ensure sentences are clear, concise, and demonstrate proper word usage",
          "3. Use common scenarios and situations that learners can relate to",
          "4. Avoid complex grammar or rare vocabulary in the examples",
          "5. Make sentences memorable and meaningful",
          "6. Include different forms of the word if applicable (verb tenses, plural/singular, etc.)",
          "7. For each example sentence, provide its translation in the native language on the next line",
          "8. Return only the example sentences and their translations, without any additional explanations",
        ],
        debug=True,
        response_model=GrammarList,
        structured_outputs=True,
      )

    def run(self, word: str):
        return self.related_sentence_agent.run(word, stream=True)
        # self.related_sentence_agent.print_response(word, stream=True)
    

if __name__ == "__main__":
    grammar_generator = GrammarGenerator(target_language="Japanese", native_language="Vietnamese")
    # Read words from csv file
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/../data/grammars_input.csv", "r") as file:
        grammars = file.read().splitlines()
        grammars = [grammar.split(",") for grammar in grammars]
        grammars = [{"grammar": grammar[0], "meaning": grammar[1]} for grammar in grammars]

    # Split words into chunks of 10
    chunks = [grammars[i:i+10] for i in range(0, len(grammars), 10)]
    
    # Create DataFrame to store all flashcards
    output_path = f"{os.path.dirname(os.path.abspath(__file__))}/../data/grammars_output.csv"
    
    # Check if file exists and read existing data
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
    else:
        existing_df = pd.DataFrame()

    for i, chunk in enumerate(chunks):
        try:
            chunk_grammars: list[Grammar] = []
            prompt = ""
            for j, grammar in enumerate(chunk):
                prompt += f"{i*10 + j + 1}. Grammar: {grammar['grammar']}, Meaning need to rewrite: {grammar['meaning']}\n"
            response: Iterator[RunResponse] = grammar_generator.run(prompt)
            pprint_run_response(response, markdown=True, show_time=True)

            # Add grammars from response to the chunk list
            if hasattr(response.content, 'grammars'):
                chunk_grammars.extend(response.content.grammars)

            # Convert chunk to DataFrame
            chunk_df = pd.DataFrame([{
                'grammar': f.grammar,
                'meaning': f.meaning,
                'example_sentences_1': f.example_sentences_1,
                'meaning_example_sentences_1': f.meaning_example_sentences_1,
                'example_sentences_2': f.example_sentences_2,
                'meaning_example_sentences_2': f.meaning_example_sentences_2,
                'image_url': f.image_url
            } for f in chunk_grammars])
            
            # Concatenate with existing data and save
            if existing_df.empty:
                chunk_df.to_csv(output_path, index=False)
                existing_df = chunk_df
            else:
                updated_df = pd.concat([existing_df, chunk_df], ignore_index=True)
                updated_df.to_csv(output_path, index=False)
                existing_df = updated_df
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")