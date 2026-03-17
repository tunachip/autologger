# docs/key_features.md


## Find & Launch Files
Using NLP-Processed strings, run commands from a pre-agent query line

### Sentence Structure
1. single-command, specified-single-filetype, single-description
'show me files of dogs'
  #command: 'show me' -> command = show_files(files=find_files())
  #filetypes: 'files' -> filetypes = 'image(plural)' , 'audio(plural)' , 'video(plural)', 'text(plural)'
  #post-filetype-specifier: 'of' -> filtered_filetypes = 'image(plural)' , 'audio(plural)' , 'video(plural)'
  #description: 'dogs' -> description = 'dog(plural)'
result: return a list of files (photo, video, audio) containing multiple dogs

basically, the 'of' here filters to a default assumption

2. multi-command, multi-filetype, specified-multi-description
'find and delete pictures and videos of dogs and cats'
  #commands: 'find', 'delete' -> command = delete_files(files=find_files())
  #filetypes: 'pictures', 'videos' -> filetypes = 'image(plural)', 'video(plural)'
  #post-filetype-specifier: 'of' -> filtered_filetypes = image, video
  #descriptions: 'dogs', 'cats' -> description = 'dog(plural) && cat(plural)'
result: delete all images & videos containing both dogs and cats

3. single-command, specified-single-filetype, specified-single-description
'show me my most recent photo with a dog'
  #command: 'show me' -> command = show_files(files=find_files())
  #pre-filetype-specifier: 'most recent' -> command = open_file(files=sort_files(files=find_files(), by='time', order='ASC'))
  #filetypes: 'photo' -> filetypes = 'image(singular)'
  #post-filetype-specifier: 'with' -> filtered_filetypes = 'image(singular)'
  #description: 'a dog' -> description = 'dog(singular)'
result: open an image of a dog with the most recent datetime metadata

4. terse example
'picture of dog'
  #command: None -> command = None
  #filetypes: 'picture' -> filetypes = 'image(singular)'
  #post-filetype-specifier: 'of' -> filtered_filetypes = 'image(singular)'
  #post-filetype-command-assumption: command = command_by_filetypes('image') = open_file()
  #description: 'dog' -> description = 'dog(singular)'
result: open an image of a dog

the assumption is used here

### Acting on Tokenized Structures
After Tokenization, we follow this workflow
1. parse_functions
  - find one or more functions
  - if failed: 
    1. offer user a list of commands
    2. fallback to AI & API for command choice
2. parse_filetypes
  - choose filetypes from immediate flags
  - for each filetype:
    1. key as plural / singular
    2. if plural: establish quantity
  - check for 'broader' context
    1. 
3. parse_description
