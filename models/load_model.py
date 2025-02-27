from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_list = [
    "Isotonic/distilbert_finetuned_ai4privacy_v2",
    "MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33",
    "unitary/unbiased-toxic-roberta",
    "philomath-1209/programming-language-identification",
    "madhurjindal/autonlp-Gibberish-Detector-492513457",
    "protectai/deberta-v3-base-prompt-injection-v2",
    "papluca/xlm-roberta-base-language-detection"
]

model_names = [
    "distilbert_finetuned_ai4privacy_v2",
    "deberta-v3-base-zeroshot-v1.1-all-33",
    "unbiased-toxic-roberta",
    "programming-language-identification",
    "autonlp-Gibberish-Detector-492513457",
    "deberta-v3-base-prompt-injection-v2",
    "xlm-roberta-base-language-detection"
]

# Download and save each model and tokenizer to a dynamically named cache directory
for model_name, model_path in zip(model_names, model_list):
    model = AutoModelForSequenceClassification.from_pretrained(
        model_path, 
        cache_dir=model_name
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, 
        cache_dir=model_name
    )
    print(f"Model and tokenizer for '{model_name}' are saved to the '{model_name}' folder.")
