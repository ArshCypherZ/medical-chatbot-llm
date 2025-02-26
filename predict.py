from cog import BasePredictor, Input
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

class Predictor(BasePredictor):
    def setup(self):
        """Load the model and tokenizer into memory to make running multiple predictions efficient"""
        model_name = "ruslanmv/Medical-Llama3-8B"
        device_map = 'auto'
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            trust_remote_code=True,
            use_cache=False,
            device_map=device_map
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def predict(self,
                question: str = Input(description="A health-related question for the AI to answer")
    ) -> str:
        """Run a single prediction on the model"""
        sys_message = ''' 
        You are an AI Medical Assistant trained on a vast dataset of health and mental health information. Please be thorough and
        provide an informative answer. If you don't know the answer to a specific medical inquiry, advise seeking professional help. Do not be much creative.
        '''   
        # Create messages structured for the chat template
        messages = [{"role": "system", "content": sys_message}, {"role": "user", "content": question}]
        
        # Applying chat template
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=1000, use_cache=True)
        
        # Extract and return the generated text, removing the prompt
        response_text = self.tokenizer.batch_decode(outputs)[0].strip()
        answer = response_text.split('assistant')[-1].strip()
        return answer
