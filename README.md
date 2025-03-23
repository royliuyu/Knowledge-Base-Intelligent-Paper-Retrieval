## Knowledge Base: Intelligent Paper Retrieval, Powered by LLM-Qwen, RAG-LangChain

### No need to use Mendeley to manage your papers any longer !
 - This repository contains the source code for a knowledge base, using RAG (Retrieval-Augmented Generation)
 - The LLM (Large Language Model) engine used is Qwen, which can easily be replaced with DeepSeek, Llama, or Gemini through minor modifications
 - You can use it to interact with files, such as papers, as demo below
 - The website is built using FastAPI
 - The RAG framework is LangChain
 - Support multiple users
 - It uses an API for inference with the LLM. If you wish to deploy the LLM locally, refer to [my repository](https://github.com/royliuyu/Image-to-text-by-locally-deployed-DeepSeek) repository

### Demo:
![Demo](demo.gif)

### Prerequisites:
 - Python 3.10,  anaconda
 - PyTorch 2.5.1
 - Ubuntu 22.04/20.04
 - Your own API key of Qwen (minor change in infer.py to support DeepSeek/Gemini/Llama)

### Installation:
- Clone this repository and enter to this repository name 
- Create conda environment (optional), e.g. name of web
- Install dependencies in your prefered environment: 

  ```
  cd knowledge_base
  conda create --name web python=3.10
  conda activate web
  pip install -r requirements.txt
 
- For embedding model,you canset in config.yaml
  - call huggingface's directly  
    ```
     embedding_model : "all-MiniLM-L6-v2" 
    ```
  
   - or, download and deploy locally, via [huggingface: all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/main)

    ``` 
     embedding_model : "/you_local_path/all-MiniLM-L6-v2"
      ```
### LLM API setting
 - Qwen:
   ```
   echo 'export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
   echo 'export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"' >> ~/.bashrc
   source ~/.bashrc

     ```
   replace xxxxxxxxxxxxxx with your own
 - Gemini: TODO
 - Llama: TODO
 - Note:  If run in PyCharm, need set API with QWEN_API_KEY and QWEN_BASE_URL via: 
     - Run -> Edit Configurations -> Environment Varialbles 

### Config path
- setup BASE_DIR in config.yaml, it shall be be the folder where this applicaiton locates

### Implement
- Enter to this repository folder, enter to app foler
  ```
  cd app
  ```
- Under img_chat folder, start server:
  ```
  uvicorn main:app --reload
   ```
- visit 127.0.0.1:8000 in browser
