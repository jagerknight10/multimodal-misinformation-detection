
import os
#os.environ["HF_ENDPOINT"] = "https://huggingface.co"
from datasets import load_dataset

def inspect_generic_image_instructions(cache_dir, limit=100):
    dataset = load_dataset(
        "NUSryan/TRUST-Instruct",
        split="train",
        cache_dir=cache_dir,
        streaming=True,
    )

    count = 0
    for row in dataset:
        if not row["image"].startswith("LLaVA-Pretrain/"):
            continue

        print(f"--- Example {count + 1} ---")
        print(f"ID: {row['id']}")
        print(f"Image: {row['image']}")
        for message in row["conversations"]:
            print(f"{message['from']}: {message['value']}")
        print()

        count += 1
        if count >= limit:
            break

    print(f"Displayed {count} generic image-instruction examples.")

if __name__ == "__main__":
    # Using a local cache directory within the project's temp folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(script_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    print(f"Using cache directory: {cache_dir}")
    inspect_generic_image_instructions(cache_dir, limit=100)
