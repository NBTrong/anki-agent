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


class Flashcard(BaseModel):
  word: str = Field(..., description="Word to be learned")
  meaning: str = Field(..., description="Meaning of the word")
  example_sentences_1: str = Field(..., description="Example sentence 1 for the word")
  meaning_example_sentences_1: str = Field(..., description="Meaning of example sentence 1")
  example_sentences_2: str = Field(..., description="Example sentence 2 for the word")
  meaning_example_sentences_2: str = Field(..., description="Meaning of example sentence 2")
  image_url: Optional[str] = Field(None, description="URL of the image illustrating the word")

class FlashcardList(BaseModel):
  flashcards: list[Flashcard] = Field(..., description="List of flashcards")

class FlashcardGenerator(Agent):
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
          id=agent_settings.gpt_4o_mini,
          max_tokens=agent_settings.default_max_completion_tokens,
          temperature=agent_settings.default_temperature,
        ),
        description=f"""An AI assistant specialized in generating contextually relevant and natural example sentences 
          for vocabulary words in {self.target_language}, helping {self.native_language} native speakers learn the language.""",
        instructions=[
          f"You are a helpful assistant that generates example sentences for {self.target_language} vocabulary words.",
          f"Your target audience are native {self.native_language} speakers learning {self.target_language}.",
          "For each word provided:",
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
        response_model=FlashcardList,
        structured_outputs=True,
      )

    def run(self, word: str):
        # self.related_sentence_agent.print_response(word, stream=True)
        return self.related_sentence_agent.run(word, stream=True)
    

if __name__ == "__main__":
    try:
        flashcard_generator = FlashcardGenerator(target_language="Japanese", native_language="Vietnamese")
        # Read words from csv file
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/../data/full_25_50.csv", "r") as file:
            words = file.read().splitlines()
            words = [word.split(",") for word in words]
            words = [{"word": word[0], "meaning": word[1]} for word in words]

        # Split words into chunks of 10
        chunks = [words[i:i+10] for i in range(0, len(words), 10)]
        
        # Create DataFrame to store all flashcards
        output_path = f"{os.path.dirname(os.path.abspath(__file__))}/../data/flashcards.xlsx"
        
        # Check if file exists and read existing data
        if os.path.exists(output_path):
            existing_df = pd.read_excel(output_path)
        else:
            existing_df = pd.DataFrame()

        for i, chunk in enumerate(chunks):
            try:
                chunk_flashcards: list[Flashcard] = []
                prompt = ""
                for j, word in enumerate(chunk):
                    prompt += f"{i*10 + j + 1}. Word: {word['word']}, Meaning: {word['meaning']}\n"
                response: Iterator[RunResponse] = flashcard_generator.run(prompt)
                pprint_run_response(response, markdown=True, show_time=True)
                
                # Add flashcards from response to the chunk list
                if hasattr(response.content, 'flashcards'):
                    chunk_flashcards.extend(response.content.flashcards)
                
                # Get image for each flashcard in the chunk
                for flashcard in chunk_flashcards:
                    flashcard.image_url = get_images_for_word(flashcard.word)[0]
                    print(flashcard.image_url)

                # Convert chunk to DataFrame
                chunk_df = pd.DataFrame([{
                    'word': f.word,
                    'meaning': f.meaning,
                    'example_sentences_1': f.example_sentences_1,
                    'meaning_example_sentences_1': f.meaning_example_sentences_1,
                    'example_sentences_2': f.example_sentences_2,
                    'meaning_example_sentences_2': f.meaning_example_sentences_2,
                    'image_url': f.image_url
                } for f in chunk_flashcards])
                
                # Concatenate with existing data and save
                if existing_df.empty:
                    chunk_df.to_excel(output_path, index=False)
                else:
                    updated_df = pd.concat([existing_df, chunk_df], ignore_index=True)
                    updated_df.to_excel(output_path, index=False)
                
                # Update existing_df for next iteration
                existing_df = pd.read_excel(output_path)
                print(f"Chunk {i+1} saved to {output_path}")

            except Exception as e:
                print(f"Error processing chunk {i+1}: {str(e)}")
                # Đóng file Excel nếu có lỗi xảy ra trong quá trình xử lý chunk
                if 'updated_df' in locals():
                    del updated_df
                if 'existing_df' in locals():
                    del existing_df
                raise  # Ném lại lỗi để dừng chương trình

        print(f"All flashcards saved to {output_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Đảm bảo giải phóng tất cả tài nguyên Excel
        if 'updated_df' in locals():
            del updated_df
        if 'existing_df' in locals():
            del existing_df
