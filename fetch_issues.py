import urllib.request, json
try:
    req = urllib.request.urlopen('https://api.github.com/repos/jarek108/gemini-cli-headless/issues?state=all')
    issues = json.loads(req.read())
    for i in issues:
        print(f"Issue #{i['number']}: {i['title']}")
        body = i.get('body', '')
        if body:
            print(body)
        print("-" * 40)
except Exception as e:
    print(f"Error: {e}")
