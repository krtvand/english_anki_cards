I learn english with anki flash cards. 
Collection name in anki is "Sentenses"
before creating new cards in anki I write sentences to google sheets - https://docs.google.com/spreadsheets/d/1KcPd38XtYt-wWv0CqnBkP8H5nF3lrn-yjNBzGl1lWpo/edit?usp=sharing
google sheets is a user interface to add new notes from any device.
I need to create a cli application like I have for greek interview cards - /Users/krtvand/Greek/Greek/citizenship_interview

The first use case for such app:
I run skill make_anki_notes in claude code
app parses rows in google sheet. finds first row with empty column "anki".
each row has english sentence, russian and comment.
russian sentence optionally has some part embraced in asterisks *some words*. It means I want to remember how to translate this part of the sentence. So this is the main and most interesting part of the note.
for column with english sentence we need to find the most common and usual english variant. If row already has english column, ensure it follows the mentioned rule. If there are other way to translate this marked part of the sentence, we need to mention it in the comments column. If there is already content in the comments column, do not drop it and try to combine all the information.
Suggest the translation and comments.
after approving from me update collection in anki and google sheet and mark the row in google sheet as done by adding number one "1" in column "anki"
suggest to parse next row

add nessessery tools to work with anki and google sheets. 