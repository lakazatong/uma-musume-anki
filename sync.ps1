uv pip compile .\requirements.txt -o .resolved-requirements.txt --index-url https://pypi.org/simple --strip-extras 
uv pip sync .\.resolved-requirements.txt
