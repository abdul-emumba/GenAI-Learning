import json
from sentence_transformers import SentenceTransformer, util

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load evaluation results
with open('evaluation_results.json', 'r') as f:
    results = json.load(f)

# Initialize counters
total_questions = len(results)
wins_A = 0
wins_B = 0
ties = 0

comparison_results = []

print("Semantic Comparison of Answers A and B with Ground Truth\n")
print("=" * 60)

for i, result in enumerate(results, 1):
    question = result['question']
    ground_truth = result['ground_truth']
    answer_A = result['answer_A']
    answer_B = result['answer_B']

    # Compute similarities
    embeddings = model.encode([answer_A, answer_B, ground_truth])
    sim_A = util.cos_sim(embeddings[0], embeddings[2]).item()
    sim_B = util.cos_sim(embeddings[1], embeddings[2]).item()

    # Determine winner
    if sim_A > sim_B:
        winner = 'A'
        wins_A += 1
    elif sim_B > sim_A:
        winner = 'B'
        wins_B += 1
    else:
        winner = 'Tie'
        ties += 1

    # Store in results
    comparison_results.append({
        'question': question,
        'ground_truth': ground_truth,
        'answer_A': answer_A,
        'answer_B': answer_B,
        'similarity_A': sim_A,
        'similarity_B': sim_B,
        'winner': winner
    })

    print(f"Question {i}: {question[:50]}...")
    print(".3f")
    print(".3f")
    print(f"Winner: {winner}\n")

print("=" * 60)
print("Summary:")
print(f"Total Questions: {total_questions}")
print(f"Wins A: {wins_A} ({wins_A/total_questions*100:.1f}%)")
print(f"Wins B: {wins_B} ({wins_B/total_questions*100:.1f}%)")
print(f"Ties: {ties} ({ties/total_questions*100:.1f}%)")

if wins_A > wins_B:
    overall_winner = "Model A"
elif wins_B > wins_A:
    overall_winner = "Model B"
else:
    overall_winner = "Tie"

print(f"Overall Winner: {overall_winner}")

# Save to JSON
with open('comparison_results.json', 'w') as f:
    json.dump(comparison_results, f, indent=2)

print("\nResults saved to comparison_results.json")