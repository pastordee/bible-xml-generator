#!/usr/bin/env python3
import re

def parse_nkjv_raw_text(text):
    verse_letters = {}
    
    for line in text.split('\n'):
        match = re.match(r'^(\d+)\s+(.+)$', line.strip())
        if not match:
            continue
        
        verse_num = int(match.group(1))
        verse_text = match.group(2)
        
        positions = []
        words = verse_text.split()
        
        # First pass: identify which positions are letters
        is_letter = []
        for word in words:
            word_clean = word.strip(',.;:!?\'"')
            common_words = {'a', 'i', 'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 
                           'he', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of', 'on', 
                           'or', 'so', 'to', 'up', 'us', 'we'}
            
            is_crossref = (len(word_clean) <= 2 and word_clean.isalpha() and 
                          word_clean.islower() and word_clean not in common_words)
            is_letter.append(is_crossref)
        
        # Second pass: for each letter, find its position relative to real words
        for i, word in enumerate(words):
            if not is_letter[i]:
                continue
            
            word_clean = word.strip(',.;:!?\'"')
            letter = word_clean
            
            # Find previous real word (skip other letters)
            prev_word_idx = i - 1
            while prev_word_idx >= 0 and is_letter[prev_word_idx]:
                prev_word_idx -= 1
            
            # Find next real word (skip other letters)  
            next_word_idx = i + 1
            while next_word_idx < len(words) and is_letter[next_word_idx]:
                next_word_idx += 1
            
            # Determine position: if this letter or previous word has comma, it's "after"
            # Otherwise it's "before" the next word
            if ',' in word or (prev_word_idx >= 0 and ',' in words[prev_word_idx]):
                # Letter is after the previous real word
                if prev_word_idx >= 0:
                    prev_word = words[prev_word_idx].strip(',.;:!?\'"')
                    positions.append((letter, 'after', prev_word))
            else:
                # Letter is before the next real word
                if next_word_idx < len(words):
                    next_word = words[next_word_idx].strip(',.;:!?\'"')
                    positions.append((letter, 'before', next_word))
        
        if positions:
            verse_letters[verse_num] = positions
    
    return verse_letters

with open('raw/nkjv_crossrefs_ot/1_chronicles_1.txt', 'r') as f:
    content = f.read()

result = parse_nkjv_raw_text(content)
print('Verse 1:', result.get(1))
print('Verse 4:', result.get(4))
print('Verse 5:', result.get(5))
print('Verse 28:', result.get(28))
print('\nTotal verses with letters:', len(result))
