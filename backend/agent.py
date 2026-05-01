import os
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Ensure you have OPENAI_API_KEY set in your environment
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="openai/gpt-3.5-turbo",
    temperature=0.2
)

class BotResponse(BaseModel):
    response_text: str = Field(description="The response to the user")
    detected_intent: Optional[str] = Field(description="The detected intent of the user. Options: 'greeting', 'provide_revenue', 'provide_loan_amount', 'ask_question', 'chitchat', 'unknown'")
    user_sentiment: float = Field(description="A sentiment score of the user's message from -1.0 (very negative) to 1.0 (very positive)")
    extracted_revenue: Optional[float] = Field(description="The extracted revenue of the company, if provided, in millions")
    extracted_loan_amount: Optional[float] = Field(description="The extracted requested loan amount, if provided, in millions")
    recommended_product: Optional[str] = Field(description="If enough info is gathered, recommend a product: 'Term Loan' or 'Supply Chain Finance'")

system_prompt = """You are a professional B2B Debt Discovery Assistant.
Your goal is to help corporate borrowers discover debt products based on their financial metrics.

Follow this flow:
1. Greet the user and ask for their company's annual revenue.
2. Once revenue is provided, ask for the required loan amount.
3. If both revenue and loan amount are provided, recommend a product:
   - If loan amount > 50% of revenue, recommend "Structured Debt".
   - If loan amount <= 50% of revenue, recommend "Term Loan" or "Supply Chain Finance".
4. Answer any questions they have about debt financing politely.

Keep responses concise and professional.
"""

def generate_response(user_input: str, history: List[dict]):
    """
    history is a list of dicts: [{'role': 'user', 'content': 'hi'}, ...]
    """
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in history:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        else:
            messages.append(AIMessage(content=msg['content']))
            
    messages.append(HumanMessage(content=user_input))
    
    # Use function calling / structured output
    structured_llm = llm.with_structured_output(BotResponse)
    
    try:
        result = structured_llm.invoke(messages)
        if not result or not result.response_text:
            raise ValueError("Empty structured response")
        return result
    except Exception as e:
        print(f"Structured output failed: {e}")
        # Fallback to standard text generation if structured output fails
        raw_result = llm.invoke(messages)
        return BotResponse(
            response_text=raw_result.content if raw_result else "I apologize, but I am having trouble processing that right now. Could you please rephrase?",
            detected_intent="unknown",
            user_sentiment=0.0,
            extracted_revenue=None,
            extracted_loan_amount=None,
            recommended_product=None
        )
