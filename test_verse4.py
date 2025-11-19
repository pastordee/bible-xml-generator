verse_text = '4 d Noah, Shem, Ham, and Japheth.'
words = verse_text.split()[1:]  # Skip verse number
expected_letters = ['c']  # From crossref section

print('Words:', words)
print('Expected letters:', expected_letters)
print()

for i, word in enumerate(words):
    word_clean = word.strip(',.;:!?\'"')
    print(f'{i}: {repr(word)} -> clean:{repr(word_clean)}')
    if word_clean in expected_letters:
        print(f'   ^ This is a crossref letter!')
