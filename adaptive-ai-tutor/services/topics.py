"""
Small, hardcoded set of AI/ML topic notes used for OFFLINE mode
(no API key entered, or the API call failed). No CSV / external
files required -- this is intentionally simple and can't crash
on a missing dependency.
"""

TOPIC_NOTES = {
    "python": "Python is the base language for AI/ML. Focus on data types, functions, loops, list comprehensions, and the NumPy/Pandas basics.",
    "statistics": "Statistics summarizes data and measures uncertainty. Learn mean, variance, distributions, hypothesis testing, and confidence intervals.",
    "probability": "Probability is the math of uncertainty. Learn conditional probability, Bayes' theorem, random variables, and common distributions.",
    "linear regression": "Linear regression predicts continuous values. It's the cleanest intro to supervised learning: fitting a line, coefficients, and loss.",
    "classification": "Classification predicts categories (spam/not spam). Learn logistic regression, precision/recall, and threshold tuning.",
    "decision trees": "Decision trees split data into interpretable rules. Learn entropy, information gain, pruning, and random forests as the ensemble version.",
    "clustering": "Clustering groups unlabeled data by similarity. Learn K-means, hierarchical clustering, and silhouette score.",
    "neural networks": "Neural networks learn layered representations. Learn perceptrons, activations, backpropagation, and overfitting/regularization.",
    "nlp": "NLP handles text: tokenization, embeddings, sentiment analysis, and retrieval-based question answering.",
    "transformers": "Transformers use attention to model long-range dependencies. They're the backbone of modern NLP and LLMs.",
    "llm": "Large language models are pretrained on huge text corpora, then adapted via prompting, retrieval, or fine-tuning.",
    "rag": "Retrieval-Augmented Generation grounds an LLM's answers in retrieved documents instead of relying purely on memorized knowledge -- exactly what this app does with your uploaded PDFs.",
    "model evaluation": "Model evaluation checks if a model is trustworthy: train/val/test splits, cross-validation, precision, recall, F1, and ROC-AUC.",
    "prompt engineering": "Prompt engineering structures instructions, context, and examples so a language model answers more reliably.",
    "deployment": "Model deployment makes a model usable in a real system: an API endpoint, monitoring, and a plan for retraining.",
}


def best_topic_note(question: str) -> str:
    """Very small keyword match against the notes above. No ranking model, no dependency."""
    q = question.lower()
    for topic, note in TOPIC_NOTES.items():
        if topic in q:
            return note
    # loose fallback: match on any individual word overlap
    q_words = set(q.split())
    best_topic, best_overlap = None, 0
    for topic, note in TOPIC_NOTES.items():
        overlap = len(q_words & set(topic.split()))
        if overlap > best_overlap:
            best_topic, best_overlap = topic, overlap
    if best_topic:
        return TOPIC_NOTES[best_topic]
    return (
        "I don't have a canned note for that topic yet. Add your OpenRouter key above for "
        "full answers, or upload a PDF and I can answer straight from it, even offline."
    )
