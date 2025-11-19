line = '1 Adam a, b c Seth, Enosh,'
words = line.split()[1:]
print('Words:', words)

# Check which are letters
is_letter = []
common_words = {'a', 'i', 'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 
               'he', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of', 'on', 
               'or', 'so', 'to', 'up', 'us', 'we'}

for i, word in enumerate(words):
    word_clean = word.strip(',.;:!?\'"')
    is_crossref = (len(word_clean) <= 2 and word_clean.isalpha() and 
                  word_clean.islower() and word_clean not in common_words)
    is_letter.append(is_crossref)
    print(f'{i}: {repr(word)} -> clean:{repr(word_clean)} -> is_letter:{is_crossref}')

print('\nFor letter "b" at index 2:')
i = 2
prev_word_idx = i - 1
print(f'  Initial prev_word_idx: {prev_word_idx}')
while prev_word_idx >= 0 and is_letter[prev_word_idx]:
    print(f'  Skipping {prev_word_idx} (is_letter={is_letter[prev_word_idx]})')
    prev_word_idx -= 1
print(f'  Final prev_word_idx: {prev_word_idx}')
if prev_word_idx >= 0:
    print(f'  Previous real word: {words[prev_word_idx]}')
