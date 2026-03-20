import streamlit as st
import base64
import asyncio
import json
from dotenv import load_dotenv
from wordpress import upload_image, create_product

from agents import Agent, WebSearchTool, Runner, trace
from agents.model_settings import ModelSettings

load_dotenv(override=True)

# -----------------------------
# Safe JSON Parser
# -----------------------------
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        else:
            raise ValueError("No valid JSON found in model output")

# -----------------------------
# Agent Instructions
# -----------------------------

instructions1 = """
You are a book cover recognition assistant.

Analyze the provided image of a book cover and extract:

1. Book title
2. ISBN number (10 or 13 digits if visible)

Rules:
- Carefully read visible text.
- The title is usually the largest text.
- If ISBN is not visible return null.

Return ONLY raw JSON.

Format:

{
"title": "",
"isbn": ""
}
"""

instructions2 = """
You are a Book Research Agent.

Your job is to gather accurate metadata about a book.

You have access to web search.

Input will contain a JSON with:
- title
- isbn (optional)

Search using ISBN if available otherwise use title.

Extract:

- title
- author_name
- publisher_name
- language
- cover_type
- age_group
- weight
- description

Return ONLY raw JSON.

Format:

{
"title": "",
"author_name": "",
"publisher_name": "",
"language": "",
"cover_type": "",
"age_group": "",
"weight": "",
"description": ""
}
"""

# -----------------------------
# Agents
# -----------------------------

vision_agent = Agent(
    name="vision_agent",
    instructions=instructions1,
    model="gpt-4o"
)

book_research_agent = Agent(
    name="book_research_agent",
    instructions=instructions2,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o",
    model_settings=ModelSettings(tool_choice="required")
)

# -----------------------------
# Agent Pipeline
# -----------------------------

async def process_book(image_bytes):

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Extract the book title and ISBN from this image."
                },
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image_base64}"
                }
            ]
        }
    ]

    # Vision Agent
    with trace("Vision Agent"):
        result = await Runner.run(vision_agent, message)

    vision_output = safe_json_parse(result.final_output)

    # Book Research Agent
    research_prompt = f"""
Find metadata for this book:

{json.dumps(vision_output)}
"""

    with trace("Book Research Agent"):
        result2 = await Runner.run(book_research_agent, research_prompt)

    research_output = safe_json_parse(result2.final_output)

    return vision_output, research_output


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="AutoShelf")

st.title("AutoShelf")

st.write("Upload a book cover image to automatically upload it to wordpress.")

uploaded_file = st.file_uploader(
    "Upload Book Cover Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    # Read image bytes here so both buttons can access it
    image_bytes = uploaded_file.read()

    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    if st.button("Extract Book Details"):
        with st.spinner("Running AI agents..."):
            vision_output, research_output = asyncio.run(
                process_book(image_bytes)
            )

        # Save to session state so Upload button can access
        st.session_state["vision_output"] = vision_output
        st.session_state["research_output"] = research_output
        st.session_state["image_bytes"] = image_bytes
        st.session_state["filename"] = uploaded_file.name

    # Show results if they exist in session state
    if "vision_output" in st.session_state:
        st.subheader("Vision Agent Output")
        st.json(st.session_state["vision_output"])

        st.subheader("Book Research Agent Output")
        st.json(st.session_state["research_output"])

        if st.button("Upload to WordPress"):
            with st.spinner("Uploading to WooCommerce..."):
                image_id = upload_image(
                    st.session_state["image_bytes"],
                    st.session_state["filename"]
                )
                product_id = create_product(
                    st.session_state["research_output"],
                    image_id
                )
            st.success(f"✅ Product created successfully! Product ID: {product_id}")
