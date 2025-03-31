def most_similar(embeddings):
    """
    Find the pair of phrases in the embeddings dictionary that have the highest cosine similarity.
    
    Args:
        embeddings (dict): Dictionary with phrases as keys and their embeddings as values
        
    Returns:
        tuple: A tuple containing the two most similar phrases
    """
    import numpy as np
    from numpy.linalg import norm
    
    # Extract phrases and their embeddings
    phrases = list(embeddings.keys())
    
    # Calculate cosine similarity between all pairs
    max_similarity = -1
    most_similar_pair = None
    
    # Compare each pair
    for i in range(len(phrases)):
        for j in range(i + 1, len(phrases)):
            phrase1 = phrases[i]
            phrase2 = phrases[j]
            
            # Get embeddings
            embedding1 = np.array(embeddings[phrase1])
            embedding2 = np.array(embeddings[phrase2])
            
            # Calculate cosine similarity: cos(θ) = (A·B) / (||A||×||B||)
            similarity = np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
            
            # Update most similar pair if necessary
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_pair = (phrase1, phrase2)
    
    return most_similar_pair