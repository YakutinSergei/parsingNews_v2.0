from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

model_name = "facebook/m2m100_418M"
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

def translate_to_ru(text: str) -> str:
    tokenizer.src_lang = "en"
    encoded = tokenizer(text, return_tensors="pt")
    generated_tokens = model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id("ru"))
    return tokenizer.decode(generated_tokens[0], skip_special_tokens=True)

english_text = "Armed man opened fire at an ICE facility in Dallas."
print(translate_to_ru(english_text))
