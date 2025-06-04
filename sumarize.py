# from transformers import pipeline

# # Load a pre-trained summarization model
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# # Input text
# text = """
# The Taj Mahal is a white marble mausoleum in Agra, India. It was built by Mughal Emperor Shah Jahan
# in memory of his wife Mumtaz Mahal. Construction began in 1632 and was completed in 1648. It is one of the
# most famous monuments in the world and a UNESCO World Heritage Site.
# """

# # Add a bullet-point prompt
# prompt = "Summarize the following in bullet points:\n" + text

# # Generate summary
# summary = summarizer(prompt, max_length=100, min_length=30, do_sample=False)[0]['summary_text']

# # Post-process into bullets (optional)
# bullets = summary.replace("•", "\n•") if "•" in summary else "\n• " + summary.replace(". ", ".\n• ")

# print("Bullet Point Summary:", bullets)

from transformers import pipeline

# Load the question generation pipeline
question_generator = pipeline("text2text-generation", model="valhalla/t5-small-qg-prepend")

# Input context from which to generate questions
context = "Mahatma Gandhi led the Indian independence movement with a non-violent resistance approach."

# Format input (model expects "generate question: <context>")
input_text = "generate question: " + context

# Generate question
questions = question_generator(input_text, max_length=64, do_sample=False)
print(questions)
# Print generated question
# print(questions[0]['generated_text'])
