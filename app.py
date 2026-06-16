import streamlit as st
import tempfile
import random
import json
import os

from extractor import extract_text
from chunker import create_chunks
from retriever import VectorStore
from generator import generate_answer, generate_flashcards, generate_study_guide

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StudyBuddy AI", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Clean up the main padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Style the flashcard */
    .flashcard-front {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #334155;
        text-align: center;
        font-size: 26px;
        font-weight: 600;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f8fafc;
    }
    .flashcard-back {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #059669;
        text-align: center;
        font-size: 22px;
        margin-top: 10px;
        margin-bottom: 20px;
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ecfdf5;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    /* Hide Streamlit default branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
@st.cache_resource
def get_vector_store():
    return VectorStore()

store = get_vector_store()

if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "current_card" not in st.session_state:
    st.session_state.current_card = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "difficult_cards" not in st.session_state:
    st.session_state.difficult_cards = []

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("🎓 StudyBuddy AI")
    st.markdown("Your personal academic knowledge base.")
    st.divider()
    
    st.header("📂 Knowledge Base")
    st.metric("Stored Chunks", store.get_document_count(), help="Total text fragments saved permanently.")
    
    uploaded_files = st.file_uploader("Add to your brain:", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Process & Save Documents", use_container_width=True, type="primary"):
            with st.spinner("Analyzing and storing..."):
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        pdf_path = tmp.name
                    
                    pages_data = extract_text(pdf_path, uploaded_file.name)
                    chunks = create_chunks(pages_data)
                    store.build(chunks)
                    os.unlink(pdf_path)
                    
            st.success("✅ Added to knowledge base!")
            st.rerun()

# --- MAIN UI ---
if store.get_document_count() == 0:
    # 🌟 EMPTY STATE / HERO SECTION 🌟
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #6366f1;'>Welcome to StudyBuddy AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94a3b8;'>Your intelligent study assistant. Upload your lectures, syllabi, or textbook chapters in the sidebar to get started.</p>", unsafe_allow_html=True)
        st.info("👈 Please upload at least one PDF in the sidebar to begin studying.")
        
else:
    # 🌟 ACTIVE STATE: TABBED INTERFACE 🌟
    st.header("🧠 Study Workspace")
    
    # Create main navigation tabs
    tab_chat, tab_flashcards, tab_guide = st.tabs([
        "💬 Ask Questions", 
        "🃏 Flashcards", 
        "📘 Study Guide"
    ])

    # --- TAB 1: CHAT ---
    with tab_chat:
        st.markdown("### Ask your Knowledge Base")
        question = st.text_input("What do you want to learn today?", placeholder="e.g., Explain the concept of recursion...")
        
        if question:
            with st.spinner("Searching documents..."):
                context = store.search(question)
                
                if not context:
                    st.warning("No relevant information found.")
                else:
                    answer = generate_answer(question, context)
                    
                    st.info("💡 **AI Answer**")
                    st.markdown(answer)
                    
                    with st.expander("📚 View Sources & Citations"):
                        for i, item in enumerate(context, start=1):
                            st.markdown(f"**Source:** `{item['metadata']['source']}` (Page {item['metadata']['page']})")
                            st.caption(item['text'])
                            st.divider()

    # --- TAB 2: FLASHCARDS ---
    with tab_flashcards:
        col_gen, col_space = st.columns([1, 3])
        with col_gen:
            if st.button("Generate New Deck", type="primary", use_container_width=True):
                with st.spinner("Creating 10 intelligent flashcards..."):
                    # We grab a broad context by searching a general query, or you can implement a full-doc summarizer later
                    general_context = store.search("Summarize the key concepts", k=10) 
                    st.session_state.flashcards = generate_flashcards(general_context)
                    st.session_state.current_card = 0
                    st.session_state.show_answer = False
                st.rerun()

        if len(st.session_state.flashcards) > 0:
            st.divider()
            cards = st.session_state.flashcards
            current = st.session_state.current_card
            card = cards[current]

            # Header & Controls
            col_title, col_actions = st.columns([1, 1])
            with col_title:
                st.markdown(f"### Card {current + 1} of {len(cards)}")
            with col_actions:
                a1, a2 = st.columns(2)
                with a1:
                    if st.button("🔀 Shuffle", use_container_width=True):
                        random.shuffle(st.session_state.flashcards)
                        st.session_state.current_card = 0
                        st.session_state.show_answer = False
                        st.rerun()
                with a2:
                    # Safely handle Anki JSON export
                    anki_data = [
                        {"front": c.get("question", c.get("front", "Unknown")), 
                         "back": c.get("answer", c.get("back", "Unknown"))} 
                        for c in cards
                    ]
                    st.download_button(
                        label="📥 Export Anki",
                        data=json.dumps(anki_data, indent=2),
                        file_name="anki_deck.json",
                        mime="application/json",
                        use_container_width=True
                    )

            st.progress((current + 1) / len(cards))

            # Display Front
            front_text = card.get('question', card.get('front', 'Error reading card format.'))
            st.markdown(f"<div class='flashcard-front'>{front_text}</div>", unsafe_allow_html=True)

            # Display Back (Answer)
            if not st.session_state.show_answer:
                if st.button("👁️ Show Answer", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                back_text = card.get('answer', card.get('back', 'Error reading card format.'))
                st.markdown(f"<div class='flashcard-back'>{back_text}</div>", unsafe_allow_html=True)
                
                if st.button("⭐ Mark as Difficult", use_container_width=True):
                    if card not in st.session_state.difficult_cards:
                        st.session_state.difficult_cards.append(card)
                        st.toast("Saved to difficult pile!")

            # Navigation
            st.write("") 
            prev_col, next_col = st.columns(2)
            with prev_col:
                if st.button("⬅ Previous Card", use_container_width=True, disabled=(current == 0)):
                    st.session_state.current_card -= 1
                    st.session_state.show_answer = False
                    st.rerun()
            with next_col:
                if st.button("Next Card ➡", use_container_width=True, disabled=(current == len(cards) - 1)):
                    st.session_state.current_card += 1
                    st.session_state.show_answer = False
                    st.rerun()

    # --- TAB 3: STUDY GUIDE ---
    with tab_guide:
        col_gen, _ = st.columns([1, 3])
        with col_gen:
            if st.button("Generate Master Study Guide", type="primary", use_container_width=True):
                with st.spinner("Synthesizing study guide..."):
                    general_context = store.search("What are the most important concepts?", k=10)
                    guide = generate_study_guide(general_context)
                    st.session_state.study_guide = guide
                
        if "study_guide" in st.session_state:
            st.divider()
            with st.container(border=True):
                st.markdown(st.session_state.study_guide)