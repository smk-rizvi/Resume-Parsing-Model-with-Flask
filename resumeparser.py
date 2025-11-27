# import libraries
from openai import OpenAI
import os
import httpx

def ats_extractor(resume_data, groq_api_key):
    try:
        prompt = '''
        You are an AI bot designed to act as a professional for parsing resumes. You are given with resume and your job is to extract the following information from the resume:
        1. Full name
        2. Email ID
        3. Github portfolio
        4. Linkedin ID
        5. Employment Details
        6. Technical Skills
        7. Soft Skills
        Give the extracted information in json format only
        '''

        # Clear proxy environment variables that might interfere
        for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            if proxy_var in os.environ:
                del os.environ[proxy_var]
        
        # Create a custom HTTP client without proxy
        http_client = httpx.Client(proxy=None)
        
        openai_client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client
        )    

        messages=[
            {"role": "system", 
            "content": prompt}
            ]
        
        user_content = resume_data
        
        messages.append({"role": "user", "content": user_content})

        response = openai_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.0,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
            
        data = response.choices[0].message.content

        print(f"API Response: {data}")
        return data
    
    except Exception as e:
        print(f"Error in ats_extractor: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a valid JSON error message
        return '{"error": "' + str(e).replace('"', '\\"') + '"}'