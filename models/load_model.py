import subprocess

model_list = [
    "Isotonic/distilbert_finetuned_ai4privacy_v2",
    "MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33",
    "unitary/unbiased-toxic-roberta",
    "philomath-1209/programming-language-identification",
    "madhurjindal/autonlp-Gibberish-Detector-492513457",
    "protectai/deberta-v3-base-prompt-injection-v2",
    "papluca/xlm-roberta-base-language-detection"
]

url = "https://huggingface.co/"

for model_name in model_list:
    git_url = f"{url}{model_name}"
    subprocess.run(["git", "clone", git_url], check=True)
    print(f"Successfully cloned {model_name} to your local directory.")

