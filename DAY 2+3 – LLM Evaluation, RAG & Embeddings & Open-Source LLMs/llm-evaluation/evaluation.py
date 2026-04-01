import json
from PyPDF2 import PdfReader
from groq import Groq
import time

TPM_LIMIT = 6000
tokens_used = 0
window_start = time.time()

def wait_if_needed(request_tokens):
    global tokens_used, window_start

    now = time.time()

    # reset every minute
    if now - window_start >= 60:
        tokens_used = 0
        window_start = now

    if tokens_used + request_tokens > TPM_LIMIT:
        sleep_time = 60 - (now - window_start)
        print(f"Sleeping {sleep_time:.2f}s to reset TPM...")
        time.sleep(sleep_time)
        tokens_used = 0
        window_start = time.time()

    tokens_used += request_tokens

MODEL_A = "llama-3.1-8b-instant" 
MODEL_B = "llama-3.3-70b-versatile" 

PDF_FILES = [
    "pdfs/djangobook.pdf",
    "pdfs/pythonprogramming.pdf"
]

GOLDEN_DATASET_PATH = "data/golden_dataset.json"
OUTPUT_RESULTS = "evaluation_results.json"

TEMPERATURE = 0  # deterministic next-token prediction
MAX_TOKENS = 1024  # respect context window limits
CHUNK_SIZE = 1000  # words per chunk
CHUNK_OVERLAP = 100  # for splitting large text

client = Groq()
print("Groq client initialized successfully.")

def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        p_text = page.extract_text()
        if p_text:
            text += p_text
    return text


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_all_pdfs(pdf_files):
    all_chunks = []
    for pdf in pdf_files:
        print(f"Reading PDF: {pdf}")
        text = read_pdf(pdf)
        chunks = chunk_text(text)
        all_chunks.extend(chunks)
    return all_chunks


def load_dataset(path):
    with open(path, 'r') as f:
        dataset = json.load(f)
    return dataset

def run_groq_model(model_name, prompt, answer_type=None, system_prompt='You are a helpful assistant.', max_retries=5):
    # Adjust developer instruction based on answer type
    if answer_type == 'factual':
        dev_inst = "Answer factually based on the context."
    elif answer_type == 'reasoning':
        dev_inst = "Provide a reasoned explanation based on the context."
    elif answer_type == 'negative':
        dev_inst = "If the information is not mentioned in the context, state 'Not mentioned in the document.' Otherwise, answer based on the context."
    else:
        dev_inst = "Always answer based on the context."
    
    full_prompt = f"""
                System: {system_prompt}
                Developer Instruction: {dev_inst}
                User Prompt: {prompt}
                """


    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                temperature=TEMPERATURE,  # deterministic
                max_tokens=MAX_TOKENS,
                messages=[{'role':'user','content':full_prompt}]
                )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e):
                wait = 1 + attempt * 2  # exponential backoff
                print(f"Rate limited. Sleeping {wait}s...")
                print(f"Error details: {e}")
                time.sleep(wait)
            else:
                raise e
    raise Exception("Max retries exceeded")

def summarize_chunk(chunk):
    prompt = f"""Summarize the following text in under 50 words while preserving the most important key points, concepts, and intent.
            Rules:
            - Maximum 50 words
            - Keep only essential information (no fluff)
            - Do not add new information
            - Maintain clarity and meaning
            - Prefer concise, information-dense sentences

            Text:{chunk}"""
    summary = run_groq_model(MODEL_A, prompt)
    return summary


def reduce_summaries(summaries):
    combined_prompt = f"Combine these summaries into a single coherent summary:\n{summaries}" 
    final_summary = run_groq_model(MODEL_A, combined_prompt)
    return final_summary

def is_correct(answer, ground_truth):
    if ground_truth.lower() in answer.lower():
        return True
    if 'not mentioned' in ground_truth.lower() and 'not mentioned' in answer.lower():
        return True
    return False

def main():
    chunks = load_all_pdfs(PDF_FILES)

    print(f"Total chunks created from PDFs: {len(chunks)}")
    
    # MAP step: summarize each chunk
    print("Summarizing each chunk (MAP step)...")
    chunk_summaries = []
    count = 0
    for c in chunks:
        print(f"Summarizing chunk {count+1}/{len(chunks)}...")

        estimated_tokens = 1500
        wait_if_needed(estimated_tokens)

        summary = summarize_chunk(c)
        chunk_summaries.append(summary)
        count += 1

        # append summary to txt file after each chunk to avoid data loss
        with open("chunk_summaries.txt", "a", encoding="utf-8") as f:
            f.write(summary + "\n\n")

    # sleep to refersh token window before step
    print("Sleeping 60s before step to reset token limits...")
    time.sleep(60)
    # combine chunk to larger summaries after every 50 chunks to manage token limits in REDUCE step
    combined_summaries = []
    for i in range(0, len(chunk_summaries), 50):
        batch = chunk_summaries[i:i+50]
        combined = reduce_summaries(batch)
        combined_summaries.append(combined)


    # sleep to refersh token window before REDUCE step
    print("Sleeping 60s before REDUCE step to reset token limits...")
    time.sleep(60)
    # REDUCE step: combine all summaries into one context
    print("Combining summaries (REDUCE step)...")
    context = reduce_summaries(combined_summaries)

    # summary of all summaries is the context for evaluation
    with open("final_context.txt", "w", encoding="utf-8") as f:
        f.write(context)

    dataset = load_dataset(GOLDEN_DATASET_PATH)
    results = []

    for row in dataset:
        question = row['question']
        ground_truth = row['ground_truth']

        print(f"Question: {question}")

        answer_a = run_groq_model(MODEL_A, f"Answer the question based on the summary context:\n{context}\nQuestion: {question}", row['answer_type'])
        answer_b = run_groq_model(MODEL_B, f"Answer the question based on the summary context:\n{context}\nQuestion: {question}", row['answer_type'])

        correct_a = is_correct(answer_a, ground_truth)
        correct_b = is_correct(answer_b, ground_truth)

        result = {
            'question': question,
            'ground_truth': ground_truth,
            'answer_A': answer_a,
            'answer_B': answer_b,
            'correct_A': correct_a,
            'correct_B': correct_b,
            'status_A': 'PASS' if correct_a else 'FAIL',
            'status_B': 'PASS' if correct_b else 'FAIL'
        }

        results.append(result)

    with open(OUTPUT_RESULTS, 'w') as f:
        json.dump(results, f, indent=2)

    pass_rate_A = sum(r['correct_A'] for r in results) / len(results)
    pass_rate_B = sum(r['correct_B'] for r in results) / len(results)

    print(f"Model A pass rate: {pass_rate_A:.2%}")
    print(f"Model B pass rate: {pass_rate_B:.2%}")

    if pass_rate_A > pass_rate_B:
        print("Winner: MODEL A")
    elif pass_rate_B > pass_rate_A:
        print("Winner: MODEL B")
    else:
        print("Result: TIE")


if __name__ == '__main__':
    main()
