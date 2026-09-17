Objective:
 Develop a chatbot that can maintain context across conversations by storing and retrieving relevant information from previous interactions.
Activities:
Understand the chatbot architecture and conversation flow.
Design the memory architecture for storing user and conversation information.
Implement short-term memory for maintaining context within a conversation.
Implement long-term memory for retaining important information across sessions.
Integrate the memory layer with the chatbot/LLM.
Implement memory retrieval so relevant past information is provided to the model when required.
Handle memory updates, duplicate information, and irrelevant/expired memories.
Test the chatbot across multiple conversations and verify that the correct information is recalled.
Evaluate the chatbot for response accuracy, context retention, and memory reliability.
Document the overall architecture, implementation, and findings.

1. Keeping track of the previous conversation $\rightarrow$ Episodic MemoryWhy you need it: If your customer wants the chatbot to remember what was discussed in a past session (cross-session memory), this is Episodic Memory45.How it works: Instead of naively dumping massive transcripts of old chats into the system—which quickly overloads the chatbot4—you should use distilled experience5. The chatbot writes high-level, persistent summary notes to itself about the customer's previous issues, preferences, or decisions, and stores them to retrieve during the next session4more_horiz.

2. Accessing persistent customer data $\rightarrow$ Semantic Memory (via RAG)Why you need it: Your chatbot needs a way to look up specific, factual details from customer profiles or databases that don't change every minute but are too large to fit in a single prompt3.How it works: This is the chatbot's Semantic Memory (its permanent knowledge base)3. To pull data from this efficiently, you should use Retrieval-Augmented Generation (RAG)78. RAG converts the customer database into mathematical vector embeddings9. When the customer asks a question, RAG finds and retrieves the semantically matching records and feeds them to the chatbot810.

3. Handling uploaded files and the active session $\rightarrow$ Working MemoryWhy you need it: The files the customer uploads right now in the current chat, along with the immediate messages being typed back and forth, need a temporary workspace2.How it works: This is the chatbot's Working Memory (its context window)2. It functions like RAM—it is fast and holds the active conversation and newly uploaded documents, but it is completely wiped once the session ends2.

user story:

The main goal of this chatbot should be customer support, where the bot helps customers or the users to find the correct location of the feature or where the feature is. It also has to be able to tell what, if any, specific tasks a user asks for, like if he is in some particular feature and he wants to know what this feature will do. It should be able to explain that.

The main application is for which we want text. The chatbot is the developer control tower. It is built for developers to manage their repos and get to know what is happening in the projects. There are multiple AI agents which help do this. It's an overall summary of the entire project: what is happening inside a project ? 

