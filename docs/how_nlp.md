* docs/how_nlp.md

so nlp builds using an AST

abstract syntax tree

we create a list of terms like 'find', 'open', 'get' and alias them to a point in a table

we then use the structure of the sentence and the type of word to determine word role

so, give me a sentence requesting a file


open my last download

get_command('open') = open_file()
# yep
result_scope('last')

get_filetypes('download') = 'any' (codes to ['image', 'video', 'audio', 'text', 'other'])

so this is used in both -- at least with text files

with video transcripts, we use a summary which then is NLP'd as if it were a text file
we also, if the v ;transcript is short enough, can bypass descriptions straight to tagging

here, let me show you the program as i have it no


yeah, exactly -- thats a step i havent added yet
once we add that, people will have far more flexability
