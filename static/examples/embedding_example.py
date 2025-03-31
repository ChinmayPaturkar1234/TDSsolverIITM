def most_similar(embeddings):
    """
    Find the pair of phrases in the embeddings dictionary that have the highest cosine similarity.
    
    Args:
        embeddings (dict): Dictionary with phrases as keys and their embeddings as values
        
    Returns:
        tuple: A tuple containing the two most similar phrases
    """
    import numpy as np
    from itertools import combinations
    
    phrase_keys = list(embeddings.keys())
    phrase_vectors = [np.array(embeddings[key]) for key in phrase_keys]
    
    max_similarity = -1  # Minimum possible cosine similarity
    most_similar_pair = None
    
    for (i, j) in combinations(range(len(phrase_keys)), 2):
        # Compute cosine similarity
        sim = np.dot(phrase_vectors[i], phrase_vectors[j]) / (np.linalg.norm(phrase_vectors[i]) * np.linalg.norm(phrase_vectors[j]))
        
        # Check if it's the highest similarity found
        if sim > max_similarity:
            max_similarity = sim
            most_similar_pair = (phrase_keys[i], phrase_keys[j])
    
    return most_similar_pair