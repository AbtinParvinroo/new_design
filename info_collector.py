import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class Info_collector:
    def __init__(self):
        model_name = "nimendraai/NuExtract-tiny-Resume-Data-Extractor"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, trust_remote_code=True
        ).eval().cuda()

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.TEMPLATE = json.dumps({
            "name": "", "email": "", "phone": "", "website": "",
            "skills": [""],
            "experience": [{"title": "", "company": "", "duration": ""}],
            "education":  [{"degree": "", "institution": "", "year": ""}],
            "other_details": [""],
        }, indent=4)

    def extract_first_json(self, text):
        depth, start = 0, None
        for i, ch in enumerate(text):
            if ch == "{":
                if start is None: start = i
                depth += 1

            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i+1]

        return text

    def extract(self, resume_text: str) -> dict:
        prompt = (
            "<|input|>\n"
            f"### Template:\n{self.TEMPLATE}\n"
            f"### Text:\n{resume_text}\n\n"
            "<|output|>"
        )

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        ).to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=512, do_sample=False
            )

        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        raw = decoded.split("<|output|>")[-1].strip()
        return json.loads(self.extract_first_json(raw))
