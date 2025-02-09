from os import getenv
from phi.playground import Playground

from agents.example import get_example_agent
from agents.grammar_generator import GrammarGenerator
from agents.flascard_generator import FlashcardGenerator
######################################################
## Router for the agent playground
######################################################

example_agent = get_example_agent(debug_mode=True)
grammar_generator_agent = (GrammarGenerator(debug_mode=True)).grammar_agent
flashcard_generator_agent = (FlashcardGenerator(debug_mode=True)).related_sentence_agent

# Create a playground instance
playground = Playground(agents=[example_agent, grammar_generator_agent, flashcard_generator_agent])

# Log the playground endpoint with phidata.app
if getenv("RUNTIME_ENV") == "dev":
    playground.create_endpoint("http://localhost:8000")

playground_router = playground.get_router()
